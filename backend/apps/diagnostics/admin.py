from django.contrib import admin
from apps.diagnostics.models import (
    DiagnosticCentre,
    CentreMembership,
    DiagnosticTest,
    CentreTest,
    AppointmentSlot,
)


@admin.register(DiagnosticCentre)
class DiagnosticCentreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city', 'state', 'pincode', 'is_active', 'created_at')
    list_filter = ('is_active', 'city', 'state')
    search_fields = ('name', 'city', 'address', 'pincode')
    ordering = ('-created_at',)


@admin.register(CentreMembership)
class CentreMembershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'centre', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__email', 'user__name', 'centre__name')
    raw_id_fields = ('user', 'centre')
    ordering = ('-created_at',)


@admin.register(DiagnosticTest)
class DiagnosticTestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(CentreTest)
class CentreTestAdmin(admin.ModelAdmin):
    list_display = ('id', 'centre', 'test', 'price', 'is_available', 'created_at')
    list_filter = ('is_available', 'centre', 'test')
    search_fields = ('centre__name', 'test__name')
    raw_id_fields = ('centre', 'test')
    ordering = ('centre', 'test')


@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'centre_test', 'date', 'start_time', 'end_time', 'capacity', 'created_at')
    list_filter = ('date', 'centre_test__centre')
    search_fields = ('centre_test__centre__name', 'centre_test__test__name')
    raw_id_fields = ('centre_test',)
    ordering = ('date', 'start_time')
