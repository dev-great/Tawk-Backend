from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import *
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from .services import *
from rest_framework.validators import ValidationError
from django.contrib.auth import get_user_model
User = get_user_model()


class ChangePasswordSerializer(serializers.Serializer):
    model = User
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


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
                    raise ValidationError(
                        "Your account has been suspended", code=404)
            else:
                raise ValidationError(
                    "Please check your credentials and try again!", code=401)
        else:
            raise ValidationError(
                "Please enter both username and password to login!", code=401)
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
