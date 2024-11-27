from django.contrib import admin
from .models import Card, SubscriptionPlan, Subscription, Billing

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'currency', 'gateway', 'created_on')
    search_fields = ('name', 'gateway')
    list_filter = ('currency', 'gateway', 'created_on')
    readonly_fields = ('created_on',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'expiration_date', 'is_active', 'auto_renew', 'created_on')
    search_fields = ('user__username', 'plan__name', 'tx_ref')
    list_filter = ('is_active', 'auto_renew', 'created_on')
    readonly_fields = ('start_date', 'expiration_date', 'created_on')
    actions = ['renew_selected_subscriptions', 'cancel_selected_subscriptions']

    def renew_selected_subscriptions(self, request, queryset):
        for subscription in queryset:
            subscription.renew_subscription()
    renew_selected_subscriptions.short_description = "Renew selected subscriptions"

    def cancel_selected_subscriptions(self, request, queryset):
        queryset.update(is_active=False)
    cancel_selected_subscriptions.short_description = "Cancel selected subscriptions"

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'payment_date', 'plan_name', 'gateway')
    search_fields = ('user__username', 'tx_ref', 'plan_name')
    list_filter = ('currency', 'gateway', 'payment_date')
    readonly_fields = ('payment_date',)



@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'issuer', 'country', 'card_type', 'expiry_date', 'created_at')
    list_filter = ('issuer', 'country', 'card_type', 'created_at')
    search_fields = ('issuer', 'first_6digits', 'last_4digits', 'user__email')
    
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at')