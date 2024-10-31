from .models import *
from .services import *
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework import serializers, status
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model
from exceptions.custom_apiexception_class import *
from django.utils.decorators import method_decorator
User = get_user_model()


class ChangePasswordSerializer(serializers.Serializer):
    model = User
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class TokenObtainPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        return token


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class TokenVerifyResponseSerializer(serializers.Serializer):
    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()

class UserSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(
        max_length=154, write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'referral_code',
                  'first_name', 'last_name', 'phone_number', 'state', 'postal_code', 'country', 'address',]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', None)
        password = validated_data.pop('password')

        if referral_code:
            try:
                referred_by_user = User.objects.get(
                    referralcode__code=referral_code)
            except User.DoesNotExist:
                referred_by_user = None
        else:
            referred_by_user = None

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        if referred_by_user:
            CreateReferral(referred_by=referred_by_user,
                           referred_to=user).new_referral()

        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email', "")
        password = data.get('password', "")
        if email and password:
            user = authenticate(email=email, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    return CustomAPIException(detail="Your account has been suspended", status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

            else:
                return CustomAPIException(detail="Please check your credentials and try again!", status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

        else:
            return CustomAPIException(detail="Please enter both username and password to login!", status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

        return data


class ReferralCodeSerializer(serializers.ModelSerializer):
    to_email = serializers.EmailField(write_only=True)

    class Meta:
        model = ReferralCode
        fields = ['code', 'to_email']
        extra_kwargs = {'code': {'read_only': True}}

    def create(self, validated_data):
        to_email = validated_data.get('to_email')
        current_user = self.context['request'].user
        code = ReferralCode.objects.get(user=current_user).code
        sendReferral = SendReferral(mail_id=to_email, referral_code=code)
        sendReferral.send_referral_mail()
        return validated_data


class ReferralHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = '__all__'

