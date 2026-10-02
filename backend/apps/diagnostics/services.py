import datetime
from django.db import models, transaction
from django.utils import timezone
from apps.diagnostics.models import (
    DiagnosticCentre,
    CentreMembership,
    DiagnosticTest,
    CentreTest,
    AppointmentSlot,
)


def get_centres_visible_to_user(user):
    """
    Returns queryset of DiagnosticCentre objects visible to the given user:
    - Platform Admin (superuser): All centres (active and inactive).
    - Clinic Admin: Active centres plus inactive centres where they hold an ADMIN membership.
    - Patient / Anonymous / Normal user: Only active centres.
    """
    if not user or user.is_anonymous or not user.is_authenticated:
        return DiagnosticCentre.objects.filter(is_active=True)

    if user.is_superuser:
        return DiagnosticCentre.objects.all()

    admin_centre_ids = CentreMembership.objects.filter(
        user=user,
        role=CentreMembership.Role.ADMIN
    ).values_list('centre_id', flat=True)

    return DiagnosticCentre.objects.filter(
        models.Q(is_active=True) | models.Q(id__in=admin_centre_ids)
    ).distinct()


def user_can_manage_centre(user, centre) -> bool:
    """
    Returns True if user has authorization to update/manage the specified centre:
    - Platform Admin (superuser): True for all centres.
    - Clinic Admin: True if user holds an ADMIN CentreMembership for this centre.
    - Patient / is_staff without membership: False.
    """
    if not user or user.is_anonymous or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return CentreMembership.objects.filter(
        user=user,
        centre=centre,
        role=CentreMembership.Role.ADMIN
    ).exists()


def get_diagnostic_tests_visible_to_user(user):
    """
    Returns queryset of DiagnosticTest objects visible to the given user:
    - Platform Admin (superuser): All global tests (active and inactive).
    - Patients / Anonymous / Clinic Admins: Only active tests (is_active=True).
    """
    if not user or user.is_anonymous or not user.is_authenticated:
        return DiagnosticTest.objects.filter(is_active=True)

    if user.is_superuser:
        return DiagnosticTest.objects.all()

    return DiagnosticTest.objects.filter(is_active=True)


def get_centre_tests_visible_to_user(user):
    """
    Returns queryset of CentreTest objects visible to the given user:
    - Platform Admin (superuser): All centre test offerings.
    - Clinic Admin: Active & available offerings OR offerings belonging to a centre they manage.
    - Patient / Anonymous / Normal user: Only offerings where centre is active, test is active, AND is_available is True.
    """
    base_qs = CentreTest.objects.select_related('centre', 'test')

    if not user or user.is_anonymous or not user.is_authenticated:
        return base_qs.filter(
            centre__is_active=True,
            test__is_active=True,
            is_available=True
        )

    if user.is_superuser:
        return base_qs.all()

    admin_centre_ids = CentreMembership.objects.filter(
        user=user,
        role=CentreMembership.Role.ADMIN
    ).values_list('centre_id', flat=True)

    return base_qs.filter(
        models.Q(
            centre__is_active=True,
            test__is_active=True,
            is_available=True
        ) | models.Q(centre_id__in=admin_centre_ids)
    ).distinct()


def get_slots_visible_to_user(user):
    """
    Returns queryset of AppointmentSlot objects visible to the given user:
    - Platform Admin (superuser): All appointment slots.
    - Clinic Admin: Active slots OR slots for centres they manage.
    - Patient / Anonymous / Normal user: Slots for active centres, active tests, available CentreTests, future time, AND remaining capacity > 0.
    """
    base_qs = AppointmentSlot.objects.select_related('centre_test', 'centre_test__centre', 'centre_test__test')

    if user and user.is_authenticated and user.is_superuser:
        return base_qs.all()

    now = timezone.now()
    current_date = now.date()
    current_time = now.time()

    future_slot_condition = models.Q(date__gt=current_date) | (
        models.Q(date=current_date) & models.Q(start_time__gt=current_time)
    )

    active_booking_filter = models.Q(bookings__status__in=['PENDING', 'CONFIRMED'])
    annotated_qs = base_qs.annotate(
        active_bookings_count=models.Count('bookings', filter=active_booking_filter)
    )

    patient_condition = (
        models.Q(centre_test__centre__is_active=True) &
        models.Q(centre_test__test__is_active=True) &
        models.Q(centre_test__is_available=True) &
        future_slot_condition &
        models.Q(active_bookings_count__lt=models.F('capacity'))
    )

    if not user or user.is_anonymous or not user.is_authenticated:
        return annotated_qs.filter(patient_condition).distinct()

    admin_centre_ids = CentreMembership.objects.filter(
        user=user,
        role=CentreMembership.Role.ADMIN
    ).values_list('centre_id', flat=True)

    if admin_centre_ids.exists():
        return annotated_qs.filter(
            patient_condition | models.Q(centre_test__centre_id__in=admin_centre_ids)
        ).distinct()

    return annotated_qs.filter(patient_condition).distinct()



def get_available_dates_for_centre_test(user, centre_test_id):
    """
    Returns a sorted list of unique future date strings (YYYY-MM-DD) having available slots with remaining capacity for a given CentreTest.
    """
    slots = get_slots_visible_to_user(user).filter(centre_test_id=centre_test_id)

    now = timezone.now()
    current_date = now.date()
    current_time = now.time()

    slots = slots.filter(
        models.Q(date__gt=current_date) | (
            models.Q(date=current_date) & models.Q(start_time__gt=current_time)
        )
    )

    dates = list(slots.values_list('date', flat=True).distinct().order_by('date'))
    return [d.strftime('%Y-%m-%d') for d in dates]


def bulk_generate_slots(
    centre_test: CentreTest,
    start_date: datetime.date,
    end_date: datetime.date,
    start_time: datetime.time,
    end_time: datetime.time,
    slot_duration_minutes: int,
    capacity: int
) -> dict:
    """
    Bulk generates appointment slots for a given CentreTest over a date range and working hours window.
    Skips any slot that overlaps with existing AppointmentSlot records for the same CentreTest and date.
    Returns a dictionary summarizing the result: created_count, skipped_count, date_count, etc.
    """
    import collections
    import datetime as dt_module

    duration = dt_module.timedelta(minutes=slot_duration_minutes)
    dummy_date = dt_module.date(2000, 1, 1)

    # 1. Generate daily time intervals
    daily_intervals = []
    curr_start_dt = dt_module.datetime.combine(dummy_date, start_time)
    end_dt = dt_module.datetime.combine(dummy_date, end_time)

    while curr_start_dt + duration <= end_dt:
        curr_end_dt = curr_start_dt + duration
        daily_intervals.append((curr_start_dt.time(), curr_end_dt.time()))
        curr_start_dt = curr_end_dt

    # 2. Build list of target dates
    target_dates = []
    curr_date = start_date
    while curr_date <= end_date:
        target_dates.append(curr_date)
        curr_date += dt_module.timedelta(days=1)

    date_count = len(target_dates)

    if not daily_intervals or not target_dates:
        return {
            "message": "No new slots were created. Slot duration exceeds working hours window or date range is empty.",
            "created_count": 0,
            "skipped_count": 0,
            "date_count": date_count,
            "centre_test": centre_test.id,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
        }

    # 3. Fetch existing slots for this centre_test across the date range to avoid N+1 queries
    existing_slots = AppointmentSlot.objects.filter(
        centre_test=centre_test,
        date__range=(start_date, end_date)
    ).values('date', 'start_time', 'end_time')

    existing_by_date = collections.defaultdict(list)
    for s in existing_slots:
        existing_by_date[s['date']].append((s['start_time'], s['end_time']))

    slots_to_create = []
    skipped_count = 0

    # 4. Check candidate slots for each date
    for d in target_dates:
        existing_intervals = existing_by_date[d]
        for cand_start, cand_end in daily_intervals:
            # Overlap rule: existing.start_time < new_end_time AND existing.end_time > new_start_time
            is_overlapping = any(
                ex_start < cand_end and ex_end > cand_start
                for ex_start, ex_end in existing_intervals
            )
            if is_overlapping:
                skipped_count += 1
            else:
                existing_intervals.append((cand_start, cand_end))
                slots_to_create.append(
                    AppointmentSlot(
                        centre_test=centre_test,
                        date=d,
                        start_time=cand_start,
                        end_time=cand_end,
                        capacity=capacity
                    )
                )

    # 5. Atomic bulk create
    with transaction.atomic():
        if slots_to_create:
            AppointmentSlot.objects.bulk_create(slots_to_create)

    created_count = len(slots_to_create)

    if created_count > 0:
        message = "Slots generated successfully."
    else:
        message = "No new slots were created. All requested slots already exist or overlap with existing slots."

    return {
        "message": message,
        "created_count": created_count,
        "skipped_count": skipped_count,
        "date_count": date_count,
        "centre_test": centre_test.id,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
    }

