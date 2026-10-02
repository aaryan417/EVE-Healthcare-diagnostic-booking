from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator

from apps.bookings.models import Booking


class Payment(models.Model):
    """
    Payment model representing financial transaction attempts associated with a Booking.
    Amount is a snapshot derived from Booking.amount.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'

    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True
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

    class Meta:
        verbose_name = 'payment'
        verbose_name_plural = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['booking', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Payment #{self.id} - {self.transaction_id} ({self.status})"


class WebhookEvent(models.Model):
    """
    Model representing received payment webhook events for idempotency and audit logging.
    """
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    transaction_id = models.CharField(max_length=100, default='')
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'webhook event'
        verbose_name_plural = 'webhook events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_id']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['event_type']),
        ]

    def __str__(self):
        return f"WebhookEvent {self.event_id} ({self.event_type})"

