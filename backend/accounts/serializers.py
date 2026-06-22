from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth.models import User


class UserCreateSerializer(BaseUserCreateSerializer):
    """
    Custom user registration serializer.
    Accepts email, username, password, re_password.
    Sets is_active = False so user must verify email before logging in.
    """

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'password')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def perform_create(self, validated_data):
        user = super().perform_create(validated_data)
        user.is_active = False
        user.save()
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that authenticates by email instead of username.
    Looks up the User by email, then authenticates with the found username.
    """

    email = serializers.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the default 'username' field that simplejwt adds
        # based on User.USERNAME_FIELD, since we use 'email' instead
        if self.username_field in self.fields and self.username_field != 'email':
            del self.fields[self.username_field]

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = User.objects.filter(email=email).first()
            if not user:
                raise serializers.ValidationError(
                    'No active account found with the given credentials'
                )

            # Inject username so super().validate() can authenticate
            attrs[self.username_field] = user.username

        return super().validate(attrs)
