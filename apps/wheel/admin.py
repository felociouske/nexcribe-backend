from django.contrib import admin
from .models import WheelConfig, WheelSlice, SpinResult


class WheelSliceInline(admin.TabularInline):
    model = WheelSlice
    extra = 1
    fields = ['label', 'reward_type', 'reward_value_kes', 'reward_spins', 'probability', 'color_hex', 'display_order']


@admin.register(WheelConfig)
class WheelConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    inlines = [WheelSliceInline]


@admin.register(WheelSlice)
class WheelSliceAdmin(admin.ModelAdmin):
    list_display = ['label', 'wheel', 'reward_type', 'reward_value_kes', 'probability', 'display_order']
    list_filter = ['reward_type', 'wheel']
    ordering = ['wheel', 'display_order']


@admin.register(SpinResult)
class SpinResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'slice_won', 'reward_type', 'reward_usd', 'credited', 'created_at']
    list_filter = ['reward_type', 'credited']
    search_fields = ['user__email', 'transaction_code']
    ordering = ['-created_at']
    readonly_fields = ['user', 'wheel', 'slice_won', 'transaction_code', 'credited']
