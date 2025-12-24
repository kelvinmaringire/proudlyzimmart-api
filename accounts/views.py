"""
API views for authentication endpoints.
Handles registration, login, logout, password management, and social authentication.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)
from .services import (
    get_tokens_for_user,
    send_verification_email,
    send_password_reset_email,
)

User = get_user_model()


def _build_auth_response(user, message):
    """Build standardized authentication response with user data and tokens."""
    tokens = get_tokens_for_user(user)
    user_serializer = UserSerializer(user)
    return {
        'user': user_serializer.data,
        'access_token': tokens['access'],
        'refresh_token': tokens['refresh'],
        'access': tokens['access'],
        'refresh': tokens['refresh'],
        'tokens': tokens,
        'message': message
    }


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    
    POST /api/accounts/register/
    Creates a new user account.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(request)
        return Response(
            _build_auth_response(user, 'Registration successful.'),
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """
    User login endpoint.
    
    POST /api/accounts/login/
    Authenticates user with email/username and password, returns JWT tokens.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response(
            _build_auth_response(user, 'Login successful.'),
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    """
    User logout endpoint.
    
    POST /api/accounts/logout/
    Blacklists the refresh token to invalidate user session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({
                    'message': 'Successfully logged out.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Refresh token is required.'
                }, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({
                'error': 'Invalid token.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Change password endpoint.
    
    PUT /api/accounts/change-password/
    PATCH /api/accounts/change-password/
    Allows authenticated users to change their password.
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, *args, **kwargs):
        """Handle PUT request for password change."""
        return self._change_password(request)

    def patch(self, request, *args, **kwargs):
        """Handle PATCH request for password change."""
        return self._change_password(request)

    def _change_password(self, request):
        """Common logic for password change."""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)


class PasswordResetView(APIView):
    """
    Request password reset endpoint.
    
    POST /api/accounts/password-reset/
    Sends password reset email to user.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(request, user)
            return Response({
                'message': 'Password reset email has been sent.'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'message': 'If an account exists with this email, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset endpoint.
    
    POST /api/accounts/password-reset-confirm/
    POST /api/accounts/password-reset-confirm/<uidb64>-<token>/
    Resets password using token from email.
    
    Accepts token in two formats:
    1. URL path: /api/accounts/password-reset-confirm/{uidb64}-{token}/
    2. Request body: {"token_key": "uidb64-token", "new_password1": "...", "new_password2": "..."}
    3. Request body: {"uid": "uidb64", "token": "token", "new_password1": "...", "new_password2": "..."}
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, token_key=None):
        data = request.data.copy()
        
        if token_key:
            data['token_key'] = token_key
        
        serializer = PasswordResetConfirmSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        uid, token = serializer.get_uid_and_token()
        new_password = serializer.validated_data['new_password1']
        
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({
                    'message': 'Password has been reset successfully.'
                }, status=status.HTTP_200_OK)
            return Response({
                'error': 'Invalid or expired token.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid user ID or token.'
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetTokenValidateView(APIView):
    """
    Validate password reset token endpoint.
    
    GET /api/accounts/password-reset/validate/<uidb64>-<token>/
    Validates if a password reset token is valid without resetting the password.
    Useful for frontend to check if the token is valid before showing the reset form.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token_key):
        if '-' not in token_key:
            return Response({
                'valid': False,
                'error': 'Invalid token format. Expected: uidb64-token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            uid, token = token_key.rsplit('-', 1)
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                return Response({
                    'valid': True,
                    'message': 'Token is valid.'
                }, status=status.HTTP_200_OK)
            return Response({
                'valid': False,
                'error': 'Invalid or expired token.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'valid': False,
                'error': 'Invalid user ID or token.'
            }, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """
    Email verification endpoint.
    
    POST /api/accounts/verify-email/
    Verifies user email using confirmation key from email.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        key = request.data.get('key')
        if not key:
            return Response({
                'error': 'Verification key is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            email_confirmation = EmailConfirmationHMAC.from_key(key)
            if email_confirmation is None:
                email_confirmation = EmailConfirmation.objects.filter(key=key).first()
            
            if email_confirmation:
                email_confirmation.confirm(request)
                return Response({
                    'message': 'Email verified successfully.'
                }, status=status.HTTP_200_OK)
            return Response({
                'error': 'Invalid or expired verification key.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    """
    Resend verification email endpoint.
    
    POST /api/accounts/resend-verification/
    Resends email verification to user.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'error': 'Email is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                return Response({
                    'message': 'Email is already verified.'
                }, status=status.HTTP_200_OK)
            
            send_verification_email(request, user)
            return Response({
                'message': 'Verification email has been sent.'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'error': 'No user found with this email address.'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    User profile endpoint.
    
    GET /api/accounts/profile/
    PUT /api/accounts/profile/
    Retrieve or update authenticated user profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class GoogleLoginView(SocialLoginView):
    """
    Google OAuth2 login endpoint.
    
    POST /api/accounts/google/
    Authenticates user with Google OAuth2 token.
    Returns user data and JWT tokens.
    """
    adapter_class = GoogleOAuth2Adapter


class FacebookLoginView(SocialLoginView):
    """
    Facebook OAuth2 login endpoint.
    
    POST /api/accounts/facebook/
    Authenticates user with Facebook OAuth2 token.
    Returns user data and JWT tokens.
    """
    adapter_class = FacebookOAuth2Adapter
