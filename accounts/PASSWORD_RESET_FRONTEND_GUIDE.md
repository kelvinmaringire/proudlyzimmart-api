# Password Reset - Frontend Integration Guide

## Overview

The password reset flow is designed to work entirely through the frontend. Users click a link in their email that takes them to your frontend application, where they can reset their password.

## Email Link Format

When a user requests a password reset, they receive an email with a link like:

```
http://localhost:9000/password/reset/key/1-d1b4o1-9e4d96fb02b86b5edb66171e08d58dc4/
```

**Format:** `{FRONTEND_URL}/password/reset/key/{uidb64}-{token}/`

- **Development:** `http://localhost:9000/password/reset/key/{uidb64}-{token}/`
- **Production:** `https://proudlyzimmart.com/password/reset/key/{uidb64}-{token}/`

## Frontend Flow

### Step 1: User Clicks Email Link

When the user clicks the link in their email, they should be taken to your frontend password reset page:

```
Route: /password/reset/key/:tokenKey
```

Example React Router route:
```javascript
<Route path="/password/reset/key/:tokenKey" element={<PasswordResetPage />} />
```

### Step 2: Validate Token (Optional but Recommended)

Before showing the password reset form, validate that the token is still valid:

**Endpoint:** `GET /api/accounts/password-reset/validate/<uidb64>-<token>/`

**Example:**
```javascript
async function validatePasswordResetToken(tokenKey) {
  const response = await fetch(
    `http://localhost:8000/api/accounts/password-reset/validate/${tokenKey}/`
  );
  const data = await response.json();
  return data.valid; // true or false
}
```

**Response (200 OK):**
```json
{
  "valid": true,
  "message": "Token is valid."
}
```

**Response (400 Bad Request):**
```json
{
  "valid": false,
  "error": "Invalid or expired token."
}
```

### Step 3: Reset Password

Once validated, show the password reset form and submit the new password:

**Endpoint:** `POST /api/accounts/password-reset-confirm/<uidb64>-<token>/`

**Request Body:**
```json
{
  "new_password1": "NewSecurePassword123!",
  "new_password2": "NewSecurePassword123!"
}
```

**Example:**
```javascript
async function resetPassword(tokenKey, newPassword, confirmPassword) {
  const response = await fetch(
    `http://localhost:8000/api/accounts/password-reset-confirm/${tokenKey}/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        new_password1: newPassword,
        new_password2: confirmPassword,
      }),
    }
  );
  
  const data = await response.json();
  return data;
}
```

**Response (200 OK):**
```json
{
  "message": "Password has been reset successfully."
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Invalid or expired token."
}
```

or

```json
{
  "new_password2": ["The two password fields didn't match."]
}
```

## Complete React Example

```javascript
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function PasswordResetPage() {
  const { tokenKey } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [valid, setValid] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    // Validate token on mount
    validateToken();
  }, [tokenKey]);

  async function validateToken() {
    try {
      const response = await fetch(
        `http://localhost:8000/api/accounts/password-reset/validate/${tokenKey}/`
      );
      const data = await response.json();
      setValid(data.valid);
      if (!data.valid) {
        setError(data.error || 'Invalid or expired token.');
      }
    } catch (err) {
      setError('Failed to validate token.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/accounts/password-reset-confirm/${tokenKey}/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            new_password1: newPassword,
            new_password2: confirmPassword,
          }),
        }
      );

      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        setError(data.error || JSON.stringify(data));
      }
    } catch (err) {
      setError('Failed to reset password. Please try again.');
    }
  }

  if (loading) {
    return <div>Validating token...</div>;
  }

  if (!valid) {
    return (
      <div>
        <h1>Invalid Token</h1>
        <p>{error}</p>
        <p>The password reset link is invalid or has expired.</p>
        <button onClick={() => navigate('/password-reset')}>
          Request New Reset Link
        </button>
      </div>
    );
  }

  if (success) {
    return (
      <div>
        <h1>Password Reset Successful</h1>
        <p>Your password has been reset successfully. Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div>
      <h1>Reset Password</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label>New Password:</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Confirm Password:</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>
        {error && <div style={{ color: 'red' }}>{error}</div>}
        <button type="submit">Reset Password</button>
      </form>
    </div>
  );
}

export default PasswordResetPage;
```

## Alternative: Using Request Body Instead of URL

You can also send the token in the request body instead of the URL:

**Endpoint:** `POST /api/accounts/password-reset-confirm/`

**Request Body:**
```json
{
  "token_key": "1-d1b4o1-9e4d96fb02b86b5edb66171e08d58dc4",
  "new_password1": "NewSecurePassword123!",
  "new_password2": "NewSecurePassword123!"
}
```

This is useful if you want to extract the token from the URL and send it in the body instead.

## Request Password Reset

To request a password reset email:

**Endpoint:** `POST /api/accounts/password-reset/`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Example:**
```javascript
async function requestPasswordReset(email) {
  const response = await fetch('http://localhost:8000/api/accounts/password-reset/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });
  
  const data = await response.json();
  return data;
}
```

## Environment Configuration

Make sure your backend has the correct `FRONTEND_URL` set:

**Development (.env):**
```
FRONTEND_URL=http://localhost:9000
```

**Production (.env):**
```
FRONTEND_URL=https://proudlyzimmart.com
```

## API Endpoints Summary

1. **Request Password Reset**
   - `POST /api/accounts/password-reset/`
   - Body: `{ "email": "..." }`

2. **Validate Token** (Optional)
   - `GET /api/accounts/password-reset/validate/<tokenKey>/`
   - Returns: `{ "valid": true/false }`

3. **Reset Password**
   - `POST /api/accounts/password-reset-confirm/<tokenKey>/`
   - Body: `{ "new_password1": "...", "new_password2": "..." }`
   - OR: `POST /api/accounts/password-reset-confirm/` with `{ "token_key": "...", "new_password1": "...", "new_password2": "..." }`

## Error Handling

Common errors:

- **400 Bad Request**: Invalid token format, passwords don't match, or validation errors
- **401 Unauthorized**: Token expired or invalid
- **404 Not Found**: Invalid endpoint

Always check the response status and handle errors appropriately in your frontend.

