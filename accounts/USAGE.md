# Accounts App - Usage Guide

This guide provides setup instructions, testing examples, and frontend integration guides for the accounts authentication system.

## Table of Contents

- [Setup Instructions](#setup-instructions)
- [Testing](#testing)
- [Frontend Integration](#frontend-integration)
- [Troubleshooting](#troubleshooting)
- [Production Considerations](#production-considerations)

## Setup Instructions

### 1. Install Dependencies

Make sure all required packages are installed:

```bash
pip install -r requirements.txt
```

Required packages:
- `djangorestframework-simplejwt==5.3.1` - JWT authentication
- `django-allauth==65.1.0` - Authentication and social auth
- `dj-rest-auth==6.0.0` - REST API support for allauth

### 2. Database Migrations

Create and apply migrations for the accounts app:

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

**Important:** The `email_verified` field was added to CustomUser. If you have existing users, you may need a data migration.

### 3. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 4. Configure Site Object

Django-allauth requires a Site object. Run:

```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'localhost:8000'  # Change for production
site.name = 'ProudlyZimMart'
site.save()
```

Or create it via admin panel at `/django-admin/sites/site/`

### 5. Environment Variables

Create a `.env` file in the project root with the required variables (see [README.md](./README.md#environment-variables) for complete list).

### 6. Run Server

```bash
python manage.py runserver
```

## Testing

### Example: Register User

```bash
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password1": "SecurePass123!",
    "password2": "SecurePass123!"
  }'
```

### Example: Login

```bash
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "login": "test@example.com",
    "password": "SecurePass123!"
  }'
```

### Example: Get Profile (with token)

```bash
curl -X GET http://localhost:8000/api/accounts/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Example: Change Password

```bash
curl -X PUT http://localhost:8000/api/accounts/change-password/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "OldPassword123!",
    "new_password1": "NewPassword123!",
    "new_password2": "NewPassword123!"
  }'
```

### Example: Request Password Reset

```bash
curl -X POST http://localhost:8000/api/accounts/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### Example: Validate Password Reset Token

```bash
curl http://localhost:8000/api/accounts/password-reset/validate/MQ-d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf/
```

### Example: Confirm Password Reset

**Using URL token:**
```bash
curl -X POST http://localhost:8000/api/accounts/password-reset-confirm/MQ-d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf/ \
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
    "token_key": "MQ-d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf",
    "new_password1": "NewPassword123!",
    "new_password2": "NewPassword123!"
  }'
```

## Frontend Integration

### Password Reset Flow

The password reset flow is designed to work entirely through the frontend. Users click a link in their email that takes them to your frontend application.

#### Email Link Format

When a user requests a password reset, they receive an email with a link like:

```
http://localhost:9000/password/reset/key/1-d1b4o1-9e4d96fb02b86b5edb66171e08d58dc4/
```

**Format:** `{FRONTEND_URL}/password/reset/key/{uidb64}-{token}/`

#### Frontend Flow

1. **User Clicks Email Link** → Route to `/password/reset/key/:tokenKey`

2. **Validate Token (Optional but Recommended)**
   ```javascript
   async function validatePasswordResetToken(tokenKey) {
     const response = await fetch(
       `http://localhost:8000/api/accounts/password-reset/validate/${tokenKey}/`
     );
     const data = await response.json();
     return data.valid; // true or false
   }
   ```

3. **Reset Password**
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

#### Complete React Example

See [Password Reset Frontend Guide](#password-reset-frontend-guide) section below.

### Change Password Integration

#### Backend Requirements

- **URL**: `/api/accounts/change-password/`
- **Methods**: `PUT` or `PATCH` (both supported)
- **Authentication**: **REQUIRED** - JWT Bearer token

#### Request Format

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

#### JavaScript Example

```javascript
async function changePassword(oldPassword, newPassword, confirmPassword) {
  const accessToken = localStorage.getItem('access_token');
  
  if (!accessToken) {
    throw new Error('No access token found. Please login again.');
  }

  try {
    const response = await fetch('http://localhost:8000/api/accounts/change-password/', {
      method: 'PUT',
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
      if (response.status === 400) {
        throw new Error(JSON.stringify(data));
      }
      if (response.status === 401) {
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

### Password Reset Frontend Guide

#### Complete React Example

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

## Troubleshooting

### Email Not Sending

**Symptoms:**
- Password reset emails not received
- Verification emails not received

**Solutions:**
- Check `EMAIL_BACKEND` in settings
- For Gmail, use App Password (not regular password)
- Check `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS` settings
- In development, use `django.core.mail.backends.console.EmailBackend` to see emails in console
- Verify email credentials in `.env` file

### Social Auth Not Working

**Symptoms:**
- Google/Facebook login fails
- OAuth redirect errors

**Solutions:**
- Verify OAuth credentials in `.env`
- Check redirect URIs match exactly
- Ensure Site ID is set correctly
- Check that social account providers are enabled in admin
- Verify OAuth consent screen is configured

### Token Issues

**Symptoms:**
- 401 Unauthorized errors
- Token refresh fails
- Logout doesn't work

**Solutions:**
- Verify `SECRET_KEY` is set correctly
- Check token expiration times
- Ensure token blacklist app is installed and migrated
- Verify JWT authentication is configured in REST_FRAMEWORK settings
- Check that access token (not refresh token) is used for authenticated requests

### Password Reset Issues

**Symptoms:**
- Token validation fails
- Password reset fails
- "Invalid or expired token" error

**Solutions:**
- Ensure token format is correct: `uidb64-token`
- Check that token hasn't expired (tokens expire after use or after 3 days)
- Verify token hasn't been used already (one-time use)
- Ensure passwords match (`new_password1` === `new_password2`)
- Verify password meets Django validation requirements

### Change Password Issues

**Symptoms:**
- 401 Unauthorized error
- 405 Method Not Allowed
- Validation errors

**Solutions:**
- Ensure JWT access token is included in Authorization header: `Bearer <token>`
- Use `PUT` or `PATCH` method (not `POST`)
- Use exact field names: `old_password`, `new_password1`, `new_password2`
- Verify token is still valid (not expired)
- Check CORS settings if request is blocked

### Migration Issues

**Symptoms:**
- Migration errors
- `email_verified` field issues

**Solutions:**
- If `email_verified` field causes issues, create a data migration
- Ensure CustomUser model is properly configured
- Check that `AUTH_USER_MODEL` is set correctly
- Run `python manage.py makemigrations accounts` and `python manage.py migrate`

### CORS Issues

**Symptoms:**
- Request blocked by CORS policy
- Frontend can't connect to API

**Solutions:**
- Ensure `django-cors-headers` is installed and configured
- Check `CORS_ALLOWED_ORIGINS` in Django settings
- Verify the frontend URL matches the allowed origins
- Add frontend domain to `CORS_ALLOWED_ORIGINS`

## Production Considerations

### Security

1. Set `DEBUG = False` in production settings
2. Use secure `SECRET_KEY` from environment
3. Configure `ALLOWED_HOSTS` correctly
4. Use HTTPS for all endpoints
5. Configure CORS properly
6. Set up proper logging
7. Use environment variables for all secrets
8. Configure proper database backups

### Email

1. Configure production SMTP server
2. Set proper `DEFAULT_FROM_EMAIL`
3. Update `FRONTEND_URL` to production domain
4. Use secure email backend

### Social Auth

1. Update OAuth redirect URIs for production
2. Use production OAuth credentials
3. Configure proper app domains
4. Update OAuth consent screen for production

### Database

1. Ensure PostgreSQL is properly configured
2. Set up database backups
3. Run migrations in production
4. Monitor database performance

### Monitoring

1. Set up error tracking (Sentry, etc.)
2. Configure logging
3. Monitor API performance
4. Set up alerts for critical errors

## Configuration Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Migrations run (`python manage.py migrate`)
- [ ] Site object created (ID=1)
- [ ] Email backend configured in `.env`
- [ ] Frontend URL set in `.env`
- [ ] Google OAuth credentials added (if using social auth)
- [ ] Facebook OAuth credentials added (if using social auth)
- [ ] Test registration endpoint
- [ ] Test login endpoint
- [ ] Test email verification flow
- [ ] Test password reset flow
- [ ] Test change password endpoint
- [ ] CORS configured for frontend domains

---

For complete API documentation, see [README.md](./README.md).

