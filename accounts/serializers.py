"""
Serializers for the accounts app.
Handles user registration, authentication, and profile management.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.account import app_settings as allauth_settings

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user model."""
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                  'email_verified', 'dob', 'sex', 'physical_address', 'phone_number')
        read_only_fields = ('id', 'email_verified')


class RegisterSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    Validates and creates new user accounts with email verification.
    """
    username = serializers.CharField(
        max_length=150,
        required=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Password must meet Django's password validation requirements."
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Enter the same password as before, for verification."
    )

    def validate_username(self, username):
        """Validate username uniqueness."""
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return username

    def validate_email(self, email):
        """Validate email uniqueness and format."""
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError("A user is already registered with this email address.")
        return email

    def validate_password1(self, password):
        """Validate password using Django validators."""
        return get_adapter().clean_password(password)

    def validate(self, data):
        """Validate that passwords match."""
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password2": "The two password fields didn't match."})
        return data

    def save(self, request):
        """Create and save the user."""
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.validated_data
        adapter.save_user(request, user, self)
        setup_user_email(request, user, [])
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Supports login with either email or username.
    Accepts 'login', 'username', or 'email' field.
    """
    login = serializers.CharField(required=False, help_text="Email or username")
    username = serializers.CharField(required=False, help_text="Username")
    email = serializers.CharField(required=False, help_text="Email")
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        """Validate login credentials."""
        # Get login value from any of the possible fields
        login = data.get('login') or data.get('username') or data.get('email')
        password = data.get('password')

        if not login:
            raise serializers.ValidationError("Must include 'login', 'username', or 'email' field along with 'password'.")

        if not password:
            raise serializers.ValidationError("Password is required.")

        # Try to authenticate with username
        user = authenticate(username=login, password=password)
        
        # If username fails, try email
        if user is None:
            try:
                user_obj = User.objects.get(email=login)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if user is None:
            raise serializers.ValidationError("Unable to log in with provided credentials.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        
        # Check email verification status (informative, but don't block login)
        # Note: Email verification is handled by allauth, but we allow login
        # The frontend can check email_verified status from user data
        
        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    Requires old password verification.
    """
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password1 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate_new_password1(self, value):
        """Validate new password using Django validators."""
        validate_password(value, self.context['request'].user)
        return value

    def validate(self, data):
        """Validate that new passwords match."""
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "The two password fields didn't match."})
        return data

    def save(self):
        """Update user password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password1'])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting password reset.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, email):
        """Validate email exists."""
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return email


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset with token.
    """
    token = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)
    new_password1 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate_new_password1(self, value):
        """Validate new password."""
        # We'll validate against a temporary user object
        from django.contrib.auth import get_user_model
        User = get_user_model()
        temp_user = User()
        validate_password(value, temp_user)
        return value

    def validate(self, data):
        """Validate that new passwords match."""
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "The two password fields didn't match."})
        return data

