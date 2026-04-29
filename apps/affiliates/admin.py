from django.contrib import admin
from .models import AffiliateNode, Commission


@admin.register(AffiliateNode)
class AffiliateNodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'parent', 'depth', 'is_active', 'created_at']
    list_filter = ['is_active', 'depth']
    search_fields = ['user__email', 'user__username']
    ordering = ['depth', '-created_at']
    readonly_fields = ['user', 'parent', 'depth']


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_code', 'recipient', 'from_user', 'plan',
        'level_depth', 'amount_usd', 'status', 'paid_at',
    ]
    list_filter = ['status', 'level_depth', 'plan__category']
    search_fields = ['transaction_code', 'recipient__email', 'from_user__email']
    ordering = ['-created_at']
    readonly_fields = [
        'recipient', 'from_user', 'plan', 'level_depth', 'rate',
        'amount_kes', 'amount_usd', 'transaction_code', 'plan_purchase_txn',
    ]
