from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.diagnostics.models import (
    DiagnosticCentre,
    CentreMembership,
    DiagnosticTest,
    CentreTest,
    AppointmentSlot,
)

User = get_user_model()


class DiagnosticCentreSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticCentre
        fields = (
            'id',
            'name',
            'address',
            'city',
            'state',
            'pincode',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Name is required.")
        return value.strip()

    def validate_address(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Address is required.")
        return value.strip()

    def validate_city(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("City is required.")
        return value.strip()

    def validate_state(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("State is required.")
        return value.strip()

    def validate_pincode(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Pincode is required.")
        return value.strip()

    def validate_is_active(self, value):
        request = self.context.get('request')
        if self.instance and self.instance.is_active != value:
            if not (request and request.user and request.user.is_superuser):
                raise serializers.ValidationError("Only platform admins can activate or deactivate centres.")
        return value


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email')
        read_only_fields = ('id', 'name', 'email')


class CentreMembershipSerializer(serializers.ModelSerializer):
    user_detail = UserMinimalSerializer(source='user', read_only=True)
    centre_detail = DiagnosticCentreSerializer(source='centre', read_only=True)

    class Meta:
        model = CentreMembership
        fields = (
            'id',
            'user',
            'centre',
            'role',
            'created_at',
            'user_detail',
            'centre_detail',
        )
        read_only_fields = ('id', 'created_at')

    def validate_role(self, value):
        if value not in CentreMembership.Role.values:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of {list(CentreMembership.Role.values)}."
            )
        return value

    def validate(self, attrs):
        user = attrs.get('user')
        centre = attrs.get('centre')

        if not self.instance:
            if CentreMembership.objects.filter(user=user, centre=centre).exists():
                raise serializers.ValidationError(
                    {"non_field_errors": ["User already has a membership for this centre."]}
                )

        return attrs


class DiagnosticTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticTest
        fields = (
            'id',
            'name',
            'description',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Test name is required.")
        cleaned_name = value.strip()

        query = DiagnosticTest.objects.filter(name__iexact=cleaned_name)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError("A diagnostic test with this name already exists.")

        return cleaned_name


class DiagnosticCentreMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticCentre
        fields = ('id', 'name', 'address', 'city', 'state', 'pincode')
        read_only_fields = ('id', 'name', 'address', 'city', 'state', 'pincode')


class DiagnosticTestMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticTest
        fields = ('id', 'name', 'description')
        read_only_fields = ('id', 'name', 'description')


class CentreTestReadSerializer(serializers.ModelSerializer):
    centre = DiagnosticCentreMinimalSerializer(read_only=True)
    test = DiagnosticTestMinimalSerializer(read_only=True)

    class Meta:
        model = CentreTest
        fields = (
            'id',
            'centre',
            'test',
            'price',
            'is_available',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class CentreTestWriteSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')
    )

    class Meta:
        model = CentreTest
        fields = (
            'id',
            'centre',
            'test',
            'price',
            'is_available',
        )
        read_only_fields = ('id',)

    def validate_price(self, value):
        if value is None or value <= Decimal('0.00'):
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate(self, attrs):
        centre = attrs.get('centre')
        test = attrs.get('test')

        if not self.instance:
            if centre and test:
                if CentreTest.objects.filter(centre=centre, test=test).exists():
                    raise serializers.ValidationError(
                        {"non_field_errors": ["This diagnostic test is already offered by the selected centre."]}
                    )
        else:
            if 'centre' in attrs and attrs['centre'] != self.instance.centre:
                raise serializers.ValidationError({"centre": "Centre cannot be changed after creation."})
            if 'test' in attrs and attrs['test'] != self.instance.test:
                raise serializers.ValidationError({"test": "Diagnostic test cannot be changed after creation."})

        return attrs


class AppointmentSlotSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(default=1, min_value=1)
    remaining_capacity = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AppointmentSlot
        fields = (
            'id',
            'centre_test',
            'date',
            'start_time',
            'end_time',
            'capacity',
            'remaining_capacity',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'remaining_capacity', 'created_at', 'updated_at')

    def get_remaining_capacity(self, obj):
        active_count = obj.bookings.filter(status__in=['PENDING', 'CONFIRMED']).count()
        return max(0, obj.capacity - active_count)

    def validate_capacity(self, value):
        if value < 1:
            raise serializers.ValidationError("Capacity must be at least 1.")
        return value

    def validate(self, attrs):
        instance = self.instance

        centre_test = attrs.get('centre_test', getattr(instance, 'centre_test', None))
        slot_date = attrs.get('date', getattr(instance, 'date', None))
        start_time = attrs.get('start_time', getattr(instance, 'start_time', None))
        end_time = attrs.get('end_time', getattr(instance, 'end_time', None))

        if instance and 'centre_test' in attrs and attrs['centre_test'] != instance.centre_test:
            raise serializers.ValidationError({"centre_test": "centre_test cannot be changed after creation."})

        if start_time and end_time:
            if end_time <= start_time:
                raise serializers.ValidationError({"end_time": "end_time must be after start_time."})

        now = timezone.now()
        current_date = now.date()
        current_time = now.time()

        if slot_date:
            if slot_date < current_date:
                raise serializers.ValidationError({"date": "Cannot create or update slot for a past date."})
            if slot_date == current_date and start_time and start_time <= current_time:
                raise serializers.ValidationError({"start_time": "Start time must be in the future."})

        if centre_test and slot_date and start_time and end_time:
            query = AppointmentSlot.objects.filter(
                centre_test=centre_test,
                date=slot_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if instance:
                query = query.exclude(pk=instance.pk)

            if query.exists():
                raise serializers.ValidationError(
                    {"non_field_errors": ["An overlapping slot already exists for this centre test on this date."]}
                )

        return attrs


class BulkGenerateSlotsSerializer(serializers.Serializer):
    centre_test = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    slot_duration_minutes = serializers.IntegerField(min_value=1)
    capacity = serializers.IntegerField(min_value=1)

    def validate_slot_duration_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError("Slot duration must be greater than 0 minutes.")
        return value

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be at least 1.")
        return value

    def validate(self, attrs):
        from apps.diagnostics.services import user_can_manage_centre
        import datetime as dt_module

        request = self.context.get('request')
        user = request.user if request else None

        centre_test_id = attrs.get('centre_test')
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        slot_duration = attrs.get('slot_duration_minutes')

        # 1. Check centre_test exists
        try:
            centre_test = CentreTest.objects.select_related('centre', 'test').get(pk=centre_test_id)
        except (CentreTest.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError({'centre_test': 'Centre test offering not found.'})

        # 2. Authorization / Tenant security check
        if user and not user_can_manage_centre(user, centre_test.centre):
            raise serializers.ValidationError({'centre_test': 'You do not have permission to manage slots for this centre.'})

        # 3. Check active & available status
        if not (centre_test.is_available and centre_test.centre.is_active and centre_test.test.is_active):
            raise serializers.ValidationError({'centre_test': 'Centre test offering is inactive or unavailable.'})

        # 4. Dates validation
        now = timezone.now()
        today = now.date()

        if start_date < today:
            raise serializers.ValidationError({'start_date': 'Start date cannot be in the past.'})

        if end_date < start_date:
            raise serializers.ValidationError({'end_date': 'End date must be on or after start date.'})

        date_count = (end_date - start_date).days + 1
        if date_count > 31:
            raise serializers.ValidationError({'end_date': 'Date range cannot exceed 31 days.'})

        # 5. Times validation
        if end_time <= start_time:
            raise serializers.ValidationError({'end_time': 'End time must be after start time.'})

        # 6. Upper bounds limit check
        duration_delta = dt_module.timedelta(minutes=slot_duration)
        dummy_date = dt_module.date(2000, 1, 1)
        start_dt = dt_module.datetime.combine(dummy_date, start_time)
        end_dt = dt_module.datetime.combine(dummy_date, end_time)

        slots_per_day = 0
        curr_dt = start_dt
        while curr_dt + duration_delta <= end_dt:
            slots_per_day += 1
            curr_dt += duration_delta

        if slots_per_day == 0:
            raise serializers.ValidationError({'slot_duration_minutes': 'Slot duration exceeds working hours window.'})

        total_slots = slots_per_day * date_count
        if total_slots > 1000:
            raise serializers.ValidationError({'non_field_errors': ['Bulk generation count exceeds maximum limit of 1000 slots per request.']})

        attrs['centre_test_obj'] = centre_test
        return attrs

