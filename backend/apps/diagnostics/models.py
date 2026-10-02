from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models.functions import Lower


class DiagnosticCentre(models.Model):
    """
    Diagnostic Centre model representing a physical healthcare facility.
    """
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'diagnostic centre'
        verbose_name_plural = 'diagnostic centres'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['city', 'is_active']),
        ]

    def __str__(self):
        return self.name


class CentreMembership(models.Model):
    """
    Relationship model granting centre-level roles (e.g. ADMIN) to users.
    A user can have only one membership per diagnostic centre.
    """
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='centre_memberships'
    )
    centre = models.ForeignKey(
        DiagnosticCentre,
        on_delete=models.CASCADE,
        related_name='user_memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'centre membership'
        verbose_name_plural = 'centre memberships'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'centre'],
                name='unique_user_centre_membership'
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.centre.name} ({self.role})"


class DiagnosticTest(models.Model):
    """
    Global Diagnostic Test catalog (e.g. Complete Blood Count, Lipid Profile).
    Represents WHAT the test is. Price is NOT stored here.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'diagnostic test'
        verbose_name_plural = 'diagnostic tests'
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                name='unique_lower_diagnostic_test_name'
            )
        ]

    def __str__(self):
        return self.name


class CentreTest(models.Model):
    """
    Diagnostic Test offered by a specific Diagnostic Centre, including centre-specific
    price and availability status.
    """
    centre = models.ForeignKey(
        DiagnosticCentre,
        on_delete=models.CASCADE,
        related_name='centre_tests'
    )
    test = models.ForeignKey(
        DiagnosticTest,
        on_delete=models.CASCADE,
        related_name='offered_in_centres'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'centre test'
        verbose_name_plural = 'centre tests'
        ordering = ['centre', 'test']
        constraints = [
            models.UniqueConstraint(
                fields=['centre', 'test'],
                name='unique_centre_diagnostic_test'
            )
        ]
        indexes = [
            models.Index(fields=['centre', 'is_available']),
            models.Index(fields=['test', 'is_available']),
        ]

    def __str__(self):
        return f"{self.centre.name} - {self.test.name} (₹{self.price})"


class AppointmentSlot(models.Model):
    """
    Appointment Slot for a specific CentreTest offering, defining calendar date, time window,
    and capacity.
    """
    centre_test = models.ForeignKey(
        CentreTest,
        on_delete=models.CASCADE,
        related_name='slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'appointment slot'
        verbose_name_plural = 'appointment slots'
        ordering = ['date', 'start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['centre_test', 'date', 'start_time', 'end_time'],
                name='unique_centre_test_slot'
            ),
            models.CheckConstraint(
                check=models.Q(capacity__gte=1),
                name='chk_slot_capacity_gte_1'
            )
        ]
        indexes = [
            models.Index(fields=['centre_test', 'date']),
            models.Index(fields=['date', 'start_time']),
        ]

    def __str__(self):
        return (
            f"{self.centre_test.centre.name} - {self.centre_test.test.name} "
            f"({self.date} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"
        )
