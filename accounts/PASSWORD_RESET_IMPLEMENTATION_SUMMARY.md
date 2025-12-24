# Password Reset Implementation Summary

## Changes Made

### 1. Updated Password Reset Email URL Generation

**File:** `accounts/adapters.py`

Added `get_password_reset_url()` method to `CustomAccountAdapter` to generate frontend URLs:

```python
def get_password_reset_url(self, request, user):
    """Generate custom password reset URL pointing to frontend."""
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:9000')
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{frontend_url}/password/reset/key/{uidb64}-{token}/"
```

**Email Link Format:**
- Development: `http://localhost:9000/password/reset/key/{uidb64}-{token}/`
- Production: `https://proudlyzimmart.com/password/reset/key/{uidb64}-{token}/`

### 2. Updated Default FRONTEND_URL

**File:** `proudlyzimmart/settings/base.py`

Changed default `FRONTEND_URL` from `http://localhost:8080` to `http://localhost:9000`

### 3. Enhanced Password Reset Confirm Endpoint

**File:** `accounts/views.py`

Updated `PasswordResetConfirmView` to accept tokens in multiple formats:

1. **URL Path Format (Recommended for Frontend):**
   ```
   POST /api/accounts/password-reset-confirm/{uidb64}-{token}/
   ```

2. **Request Body with token_key:**
   ```
   POST /api/accounts/password-reset-confirm/
   Body: { "token_key": "uidb64-token", "new_password1": "...", "new_password2": "..." }
   ```

3. **Request Body with separate uid and token (Legacy):**
   ```
   POST /api/accounts/password-reset-confirm/
   Body: { "uid": "...", "token": "...", "new_password1": "...", "new_password2": "..." }
   ```

### 4. Added Token Validation Endpoint

**File:** `accounts/views.py`

Added `PasswordResetTokenValidateView` to validate tokens without resetting password:

```
GET /api/accounts/password-reset/validate/{uidb64}-{token}/
```

Returns:
```json
{
  "valid": true,
  "message": "Token is valid."
}
```

### 5. Updated Serializer

**File:** `accounts/serializers.py`

Updated `PasswordResetConfirmSerializer` to accept:
- `token_key` (combined format: `uidb64-token`)
- Separate `uid` and `token` (legacy format)

### 6. Updated URL Configuration

**File:** `accounts/urls.py`

Added new URL patterns:
- `password-reset/validate/<str:token_key>/` - Token validation
- `password-reset-confirm/<str:token_key>/` - Password reset with token in URL

## Testing

### 1. Test Password Reset Email

1. Request password reset:
   ```bash
   curl -X POST http://localhost:8000/api/accounts/password-reset/ \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
   ```

2. Check email - link should be:
   ```
   http://localhost:9000/password/reset/key/{uidb64}-{token}/
   ```

### 2. Test Token Validation

```bash
curl http://localhost:8000/api/accounts/password-reset/validate/1-d1b4o1-9e4d96fb02b86b5edb66171e08d58dc4/
```

Expected response:
```json
{
  "valid": true,
  "message": "Token is valid."
}
```

### 3. Test Password Reset

**Using URL token:**
```bash
curl -X POST http://localhost:8000/api/accounts/password-reset-confirm/1-d1b4o1-9e4d96fb02b86b5edb66171e08d58dc4/ \
  -H "Content-Type: application/json" \
  -d '{
    "new_password1": "NewPassword123!",
    "new_password2": "NewPassword123!"
  }'
```

**Using request body:**
```bash
curl -X POST http://localhost:8000/api/accounts/password-reset-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "token_key": "1-d1b4o1-9e4d96fb02b86b5edb66171e08d58dc4",
    "new_password1": "NewPassword123!",
    "new_password2": "NewPassword123!"
  }'
```

## Configuration

### Environment Variables

Make sure your `.env` file has:

**Development:**
```
FRONTEND_URL=http://localhost:9000
```

**Production:**
```
FRONTEND_URL=https://proudlyzimmart.com
```

## Frontend Integration

See `PASSWORD_RESET_FRONTEND_GUIDE.md` for complete frontend integration examples.

### Quick Frontend Example

1. **Route Setup:**
   ```javascript
   <Route path="/password/reset/key/:tokenKey" element={<PasswordResetPage />} />
   ```

2. **Validate Token:**
   ```javascript
   const response = await fetch(
     `http://localhost:8000/api/accounts/password-reset/validate/${tokenKey}/`
   );
   ```

3. **Reset Password:**
   ```javascript
   const response = await fetch(
     `http://localhost:8000/api/accounts/password-reset-confirm/${tokenKey}/`,
     {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         new_password1: newPassword,
         new_password2: confirmPassword,
       }),
     }
   );
   ```

## Troubleshooting

### Issue: Email still shows backend URL

**Solution:** 
1. Check that `ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'` is set in settings
2. Restart Django server after changes
3. Verify `FRONTEND_URL` is set correctly in `.env`

### Issue: Token validation fails

**Solution:**
1. Ensure token format is correct: `{uidb64}-{token}`
2. Check that token hasn't expired (tokens expire after password reset is used)
3. Verify user ID decoding works correctly

### Issue: Password reset fails

**Solution:**
1. Check token format matches email link exactly
2. Ensure passwords match (`new_password1` === `new_password2`)
3. Verify password meets Django validation requirements

## Notes

- The password reset token expires after it's used once
- Tokens also expire after a certain time (Django default: 3 days)
- The email link format matches the frontend route pattern
- All endpoints are API-only - no HTML pages are served

