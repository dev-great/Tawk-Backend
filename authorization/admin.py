from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .forms import *
from .models import *


class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'code',)
    search_fields = ("code", "user_id",)


admin.site.register(ReferralCode, ReferralCodeAdmin)


class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referred_by', 'referred_to',)
    list_filter = ("referred_by", 'referred_to')
    search_fields = ("referred_by", "referred_to",)


admin.site.register(Referral, ReferralAdmin)


class ReferralPointAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'point',)
    list_filter = ("user_id",)
    search_fields = ("user_id", "point",)


admin.site.register(ReferralPointModel, ReferralPointAdmin)


class CustomUserAdmin(admin.ModelAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    fieldsets = (
        (None, {'fields': ('email', 'password', )}),
        (_('Personal info'), {'fields': (
            'first_name', 'last_name', 'state', 'postal_code', 'country', 'address',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('user_info'), {'fields': ('phone_number',
                                     )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide', ),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ['email', 'first_name', 'last_name',
                    'is_staff', 'phone_number', 'state', 'postal_code', 'country', 'address',]
    search_fields = ('email', 'first_name', 'last_name',
                     'phone_number', 'state', 'postal_code', 'country', 'address',)
    ordering = ('email', )


admin.site.register(CustomUser, CustomUserAdmin)
