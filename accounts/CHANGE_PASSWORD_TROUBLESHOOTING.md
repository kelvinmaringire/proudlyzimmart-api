# Change Password API - Frontend Integration Guide

## Backend Requirements

### Endpoint
- **URL**: `/api/accounts/change-password/`
- **Methods**: `PUT` or `PATCH` (both supported)
- **Authentication**: **REQUIRED** - JWT Bearer token

### Request Format

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body:**
```json
{
  "old_password": "CurrentPassword123!",
  "new_password1": "NewPassword123!",
  "new_password2": "NewPassword123!"
}
```

### Response

**Success (200 OK):**
```json
{
  "message": "Password changed successfully."
}
```

**Error (400 Bad Request):**
```json
{
  "old_password": ["Old password is incorrect."],
  "new_password2": ["The two password fields didn't match."]
}
```

**Error (401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Common Frontend Issues & Solutions

### Issue 1: Missing Authentication Token

**Symptom:** Getting 401 Unauthorized error

**Solution:** Ensure the JWT access token is included in the Authorization header:

```javascript
// Example using fetch
const response = await fetch('/api/accounts/change-password/', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${accessToken}`,  // ← CRITICAL: Must include this
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    old_password: oldPassword,
    new_password1: newPassword,
    new_password2: confirmPassword,
  }),
});
```

**Common Mistakes:**
- ❌ `Authorization: ${accessToken}` (missing "Bearer " prefix)
- ❌ `Authorization: Token ${accessToken}` (wrong prefix, should be "Bearer")
- ❌ Not including the header at all
- ❌ Using refresh token instead of access token

---

### Issue 2: Wrong HTTP Method

**Symptom:** Getting 405 Method Not Allowed error

**Solution:** Use `PUT` or `PATCH` method (both are supported):

```javascript
// ✅ Correct
method: 'PUT'
// or
method: 'PATCH'

// ❌ Wrong
method: 'POST'  // This will fail
```

---

### Issue 3: Token Expired

**Symptom:** Getting 401 Unauthorized even with token present

**Solution:** Refresh the access token before making the request:

```javascript
// Refresh token flow
const refreshResponse = await fetch('/api/token/refresh/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    refresh: refreshToken,
  }),
});

const { access } = await refreshResponse.json();

// Now use the new access token
const response = await fetch('/api/accounts/change-password/', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${access}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    old_password: oldPassword,
    new_password1: newPassword,
    new_password2: confirmPassword,
  }),
});
```

---

### Issue 4: CORS Issues

**Symptom:** Request blocked by CORS policy

**Solution:** Ensure backend CORS settings allow your frontend origin:

1. Check `CORS_ALLOWED_ORIGINS` in Django settings
2. Ensure `django-cors-headers` is installed and configured
3. Verify the frontend URL matches the allowed origins

---

### Issue 5: Wrong Field Names

**Symptom:** Getting validation errors about missing fields

**Solution:** Use exact field names as specified:

```javascript
// ✅ Correct field names
{
  old_password: "...",      // NOT "current_password" or "oldPassword"
  new_password1: "...",      // NOT "newPassword" or "password"
  new_password2: "..."      // NOT "confirmPassword" or "passwordConfirm"
}

// ❌ Wrong field names
{
  currentPassword: "...",    // Wrong
  newPassword: "...",        // Wrong
  confirmPassword: "..."     // Wrong
}
```

---

## Complete Frontend Example

### React/JavaScript Example

```javascript
async function changePassword(oldPassword, newPassword, confirmPassword) {
  // Get access token from storage (localStorage, context, etc.)
  const accessToken = localStorage.getItem('access_token');
  
  if (!accessToken) {
    throw new Error('No access token found. Please login again.');
  }

  try {
    const response = await fetch('http://localhost:8000/api/accounts/change-password/', {
      method: 'PUT',  // or 'PATCH'
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        old_password: oldPassword,
        new_password1: newPassword,
        new_password2: confirmPassword,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle validation errors
      if (response.status === 400) {
        // data will contain field-specific errors
        throw new Error(JSON.stringify(data));
      }
      if (response.status === 401) {
        // Token expired or invalid
        throw new Error('Authentication failed. Please login again.');
      }
      throw new Error('Failed to change password');
    }

    return data; // { message: "Password changed successfully." }
  } catch (error) {
    console.error('Password change error:', error);
    throw error;
  }
}
```

### Axios Example

```javascript
import axios from 'axios';

async function changePassword(oldPassword, newPassword, confirmPassword) {
  const accessToken = localStorage.getItem('access_token');
  
  try {
    const response = await axios.put(
      '/api/accounts/change-password/',
      {
        old_password: oldPassword,
        new_password1: newPassword,
        new_password2: confirmPassword,
      },
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      }
    );
    
    return response.data;
  } catch (error) {
    if (error.response?.status === 401) {
      // Token expired - refresh it
      await refreshAccessToken();
      // Retry the request
      return changePassword(oldPassword, newPassword, confirmPassword);
    }
    throw error;
  }
}
```

### Axios with Interceptor (Recommended)

```javascript
import axios from 'axios';

// Set up axios instance with base URL
const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Add token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post('/api/token/refresh/', {
            refresh: refreshToken,
          });
          localStorage.setItem('access_token', data.access);
          // Retry original request
          error.config.headers.Authorization = `Bearer ${data.access}`;
          return axios.request(error.config);
        } catch (refreshError) {
          // Refresh failed - redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Now use it simply:
async function changePassword(oldPassword, newPassword, confirmPassword) {
  const response = await api.put('/api/accounts/change-password/', {
    old_password: oldPassword,
    new_password1: newPassword,
    new_password2: confirmPassword,
  });
  return response.data;
}
```

---

## Testing with cURL

Test the endpoint directly to verify backend is working:

```bash
# Replace <access_token> with actual token from login
curl -X PUT http://localhost:8000/api/accounts/change-password/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "OldPassword123!",
    "new_password1": "NewPassword123!",
    "new_password2": "NewPassword123!"
  }'
```

Expected response:
```json
{
  "message": "Password changed successfully."
}
```

---

## Debugging Checklist

- [ ] Is the access token being sent in the Authorization header?
- [ ] Is the token format correct: `Bearer <token>` (with space after "Bearer")?
- [ ] Is the HTTP method `PUT` or `PATCH` (not `POST`)?
- [ ] Are the field names exactly: `old_password`, `new_password1`, `new_password2`?
- [ ] Is the Content-Type header set to `application/json`?
- [ ] Is the access token still valid (not expired)?
- [ ] Are CORS settings configured correctly?
- [ ] Is the backend URL correct (including trailing slash)?
- [ ] Are you using the access token (not refresh token)?

---

## Backend Verification

To verify the backend is working correctly, check:

1. **View is accessible**: `accounts/views.py` - `ChangePasswordView`
2. **URL is configured**: `accounts/urls.py` - should have `path('change-password/', ...)`
3. **Authentication is required**: View has `permission_classes = [permissions.IsAuthenticated]`
4. **JWT authentication is enabled**: Settings have `JWTAuthentication` in `REST_FRAMEWORK`

---

## Need More Help?

If the issue persists:

1. Check browser Network tab to see the actual request/response
2. Check Django server logs for errors
3. Verify token is valid by testing another authenticated endpoint (e.g., `/api/accounts/profile/`)
4. Test with Postman/Insomnia to isolate frontend vs backend issues

