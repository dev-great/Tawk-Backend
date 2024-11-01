import uuid
import secrets
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
# Create your models here.


class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    email = models.EmailField(_('email address'), unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    first_name = models.CharField(
        max_length=50, null=True, blank=True)
    last_name = models.CharField(
        max_length=50, null=True, blank=True)
    account_type = models.CharField(
        max_length=200, null=True, blank=True)
   
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        related_name='customuser_set',
        related_query_name='user'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        related_name='customuser_set',
        related_query_name='user'
    )
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    PASSWORD_FIELD = 'password'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'account_type', ]

    def __str__(self):
        return str(self.email)

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def get_full_name(self):
        """
        Returns the full name for the user.
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.username


class ReferralCode(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=154, unique=True)

    def generate_code(self):
        CustomUser = self.user.email
        useremail = CustomUser.split("@")
        splited_mail = useremail[:1]
        key = "".join(useremail)
        gen = list(key)[:3]
        ref_code = "".join(gen)
        random_code = secrets.token_hex(4)
        return ref_code + random_code

    def save(self, *args, **kwargs):
        self.code = self.generate_code()

        return super(ReferralCode, self).save(*args, **kwargs)


class Referral(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    referred_by = models.ForeignKey(
        CustomUser, unique=False, on_delete=models.CASCADE, related_query_name='my_referral')
    referred_to = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_query_name='has_referred')


class ReferralPointModel(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    user_id = models.ForeignKey(
        'CustomUser', on_delete=models.CASCADE, default=None)
    point = models.FloatField(default=0.0)

    def __str__(self):
        return self.user_id.email

