# Password Reset Endpoints Verification

## Endpoint Overview

### 1. Request Password Reset
**Endpoint:** `POST /api/accounts/password-reset/`

**Status:** ✅ Working

**Implementation:**
- Accepts email in request body
- Finds user by email
- Sends password reset email via `send_password_reset_email()`
- Returns success message even if email doesn't exist (security best practice)

**Code Location:** `accounts/views.py:151-174`

**Test:**
```bash
curl -X POST http://localhost:8000/api/accounts/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

---

### 2. Validate Password Reset Token
**Endpoint:** `GET /api/accounts/password-reset/validate/<token_key>/`

**Status:** ✅ Working

**Implementation:**
- Accepts token in URL path format: `uidb64-token`
- Parses token using `split('-', 1)` to handle tokens with dashes
- Validates token without resetting password
- Returns `{"valid": true/false}`

**Code Location:** `accounts/views.py:226-260`

**Token Parsing Logic:**
```python
uid, token = token_key.split('-', 1)  # Splits on FIRST dash only
```

**Example:**
- Input: `MQ-d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf`
- Parsed: `uid='MQ'`, `token='d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf'`

**Test:**
```bash
curl http://localhost:8000/api/accounts/password-reset/validate/MQ-d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf/
```

---

### 3. Confirm Password Reset
**Endpoint:** `POST /api/accounts/password-reset-confirm/<token_key>/`  
**Endpoint:** `POST /api/accounts/password-reset-confirm/`

**Status:** ✅ Working (Fixed)

**Implementation:**
- Accepts token in URL path OR request body
- Supports three formats:
  1. URL path: `/api/accounts/password-reset-confirm/{token_key}/`
  2. Body with `token_key`: `{"token_key": "...", "new_password1": "...", "new_password2": "..."}`
  3. Body with separate `uid` and `token`: `{"uid": "...", "token": "...", "new_password1": "...", "new_password2": "..."}`

**Code Location:** `accounts/views.py:177-223`

**Token Parsing Logic:**
- Uses `PasswordResetConfirmSerializer.get_uid_and_token()`
- Parses using `split('-', 1)` to correctly handle tokens with dashes
- Validates token and resets password if valid

**Test:**
```bash
# Using URL path
curl -X POST http://localhost:8000/api/accounts/password-reset-confirm/MQ-d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf/ \
  -H "Content-Type: application/json" \
  -d '{
    "new_password1": "NewPassword123!",
    "new_password2": "NewPassword123!"
  }'

# Using request body
curl -X POST http://localhost:8000/api/accounts/password-reset-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "token_key": "MQ-d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf",
    "new_password1": "NewPassword123!",
    "new_password2": "NewPassword123!"
  }'
```

---

## Key Fixes Applied

### ✅ Token Parsing Fix
**Issue:** Tokens with dashes (e.g., `MQ-d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf`) were incorrectly parsed using `rsplit('-', 1)`.

**Fix:** Changed to `split('-', 1)` to split on the FIRST dash only.

**Files Changed:**
- `accounts/serializers.py:229` - `get_uid_and_token()` method
- `accounts/views.py:244` - `PasswordResetTokenValidateView.get()`

### ✅ Error Handling Improvement
**Enhancement:** Better error messages for debugging token parsing issues.

**Files Changed:**
- `accounts/views.py:216-223` - Separated error handling for different exception types

---

## URL Configuration

**File:** `accounts/urls.py`

**Routes:**
```python
path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
path('password-reset/validate/<str:token_key>/', PasswordResetTokenValidateView.as_view(), name='password_reset_validate'),
path('password-reset-confirm/<str:token_key>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm_with_token'),
path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
```

**Status:** ✅ All routes correctly configured

---

## Serializer Logic

**File:** `accounts/serializers.py`

### PasswordResetConfirmSerializer

**Fields:**
- `token_key` (optional) - Combined format: `uidb64-token`
- `uid` (optional) - Separate uidb64
- `token` (optional) - Separate token
- `new_password1` (required) - New password
- `new_password2` (required) - Confirm password

**Validation:**
- Requires either `token_key` OR both `uid` and `token`
- Validates passwords match
- Validates password strength using Django validators

**Token Parsing Method:**
```python
def get_uid_and_token(self):
    if self.validated_data.get('token_key'):
        token_key = self.validated_data['token_key']
        if '-' in token_key:
            uid, token = token_key.split('-', 1)  # Split on FIRST dash
            return uid, token
    return self.validated_data['uid'], self.validated_data['token']
```

**Status:** ✅ Working correctly

---

## Testing Checklist

- [x] Token parsing handles tokens with dashes correctly
- [x] Token validation endpoint works
- [x] Password reset confirmation endpoint works
- [x] Error handling provides clear messages
- [x] URL routes are correctly configured
- [x] Serializer validation works correctly

---

## Common Issues and Solutions

### Issue: "Invalid user ID or token"
**Cause:** Token parsing failed or token expired
**Solution:** 
- Verify token format is correct: `uidb64-token`
- Check that token hasn't expired (tokens expire after use or after 3 days)
- Ensure token hasn't been used already

### Issue: "Invalid token format"
**Cause:** Token doesn't contain a dash
**Solution:** Ensure token is in format `uidb64-token`

### Issue: "The two password fields didn't match"
**Cause:** `new_password1` and `new_password2` don't match
**Solution:** Ensure both password fields are identical

---

## Frontend Integration Notes

The frontend should:
1. Extract token from URL: `/password/reset/key/{token_key}/`
2. Optionally validate token: `GET /api/accounts/password-reset/validate/{token_key}/`
3. Submit password reset: `POST /api/accounts/password-reset-confirm/{token_key}/` with `new_password1` and `new_password2`

**Example Frontend Flow:**
```javascript
// 1. Extract token from URL
const tokenKey = route.params.tokenKey; // e.g., "MQ-d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf"

// 2. Validate token (optional)
const validateResponse = await fetch(`/api/accounts/password-reset/validate/${tokenKey}/`);
const { valid } = await validateResponse.json();

// 3. Reset password
const resetResponse = await fetch(`/api/accounts/password-reset-confirm/${tokenKey}/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    new_password1: newPassword,
    new_password2: confirmPassword,
  }),
});
```

---

## Summary

All password reset endpoints are **working correctly** after the token parsing fix. The endpoints properly handle:
- ✅ Tokens with dashes in them
- ✅ Multiple token input formats
- ✅ Proper error handling
- ✅ Token validation
- ✅ Password reset confirmation

The main fix was changing from `rsplit('-', 1)` to `split('-', 1)` to correctly parse tokens that contain dashes.

