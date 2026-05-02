from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Profile, AccountWallet, YieldsWallet, Transaction, DepositWallet, CashbackWallet


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    referral_code = serializers.CharField(
        write_only=True, required=False, allow_blank=True, allow_null=True, default=''
    )
    first_name = serializers.CharField(required=False, allow_blank=True, default='')
    last_name = serializers.CharField(required=False, allow_blank=True, default='')
    phone = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'phone', 'password', 'password2', 'referral_code',
        ]

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def validate_referral_code(self, value):
        if value and value.strip():
            try:
                profile = Profile.objects.get(referral_code=value.strip())
                return profile.user
            except Profile.DoesNotExist:
                raise serializers.ValidationError('Invalid referral code.')
        return None

    def create(self, validated_data):
        validated_data.pop('password2')
        referrer = validated_data.pop('referral_code', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        if referrer:
            user.profile.referred_by = referrer
            user.profile.save()
            referrer.profile.total_referrals += 1
            referrer.profile.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):
    referral_code = serializers.ReadOnlyField()
    total_referrals = serializers.ReadOnlyField()

    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'country', 'referral_code', 'total_referrals']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'phone',
            'is_verified', 'date_joined', 'full_name', 'profile',
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'date_joined']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_code', 'wallet_type', 'type',
            'amount_usd', 'amount_kes', 'source', 'description',
            'status', 'reference', 'balance_after_usd', 'created_at',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password2 = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs