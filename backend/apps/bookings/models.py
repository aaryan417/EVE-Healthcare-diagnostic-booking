from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from apps.diagnostics.models import CentreTest, AppointmentSlot


class Booking(models.Model):
    """
    Booking model representing an appointment reservation made by a patient for a diagnostic test slot.
    Contains point-in-time price snapshot (amount).
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    centre_test = models.ForeignKey(
        CentreTest,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    slot = models.ForeignKey(
        AppointmentSlot,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'booking'
        verbose_name_plural = 'bookings'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'slot'],
                condition=models.Q(status__in=['PENDING', 'CONFIRMED']),
                name='unique_active_user_slot_booking'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['slot', 'status']),
            models.Index(fields=['status']),
        ]

    def clean(self):
        super().clean()
        if self.slot_id and self.centre_test_id:
            if self.slot.centre_test_id != self.centre_test_id:
                raise ValidationError({"centre_test": "Booking centre_test must match slot centre_test."})

    def __str__(self):
        return f"Booking #{self.id} ({self.user.email} - {self.centre_test.test.name} - {self.status})"
