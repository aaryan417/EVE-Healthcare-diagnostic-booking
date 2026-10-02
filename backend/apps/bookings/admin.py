from django.contrib import admin
from apps.bookings.models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'get_centre',
        'get_test',
        'get_slot_time',
        'amount',
        'status',
        'created_at',
    )
    list_filter = ('status', 'centre_test__centre', 'slot__date')
    search_fields = ('user__email', 'user__name', 'centre_test__centre__name', 'centre_test__test__name')
    raw_id_fields = ('user', 'centre_test', 'slot')
    ordering = ('-created_at',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user',
            'centre_test__centre',
            'centre_test__test',
            'slot'
        )

    def get_centre(self, obj):
        return obj.centre_test.centre.name
    get_centre.short_description = 'Centre'

    def get_test(self, obj):
        return obj.centre_test.test.name
    get_test.short_description = 'Test'

    def get_slot_time(self, obj):
        return f"{obj.slot.date} {obj.slot.start_time.strftime('%H:%M')}-{obj.slot.end_time.strftime('%H:%M')}"
    get_slot_time.short_description = 'Appointment Slot'
