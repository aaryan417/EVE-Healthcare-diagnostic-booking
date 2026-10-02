from django.contrib import admin
from apps.payments.models import Payment, WebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'transaction_id',
        'booking',
        'get_user',
        'amount',
        'status',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = (
        'transaction_id',
        'booking__id',
        'booking__user__email',
        'booking__centre_test__centre__name',
    )
    raw_id_fields = ('booking',)
    readonly_fields = ('transaction_id', 'amount', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'booking',
            'booking__user',
            'booking__centre_test__centre'
        )

    def get_user(self, obj):
        return obj.booking.user.email
    get_user.short_description = 'User'


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_id', 'event_type', 'transaction_id', 'processed_at', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('event_id', 'event_type', 'transaction_id')
    readonly_fields = ('event_id', 'event_type', 'transaction_id', 'payload', 'processed_at', 'created_at')

