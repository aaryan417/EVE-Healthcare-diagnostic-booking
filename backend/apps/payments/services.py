import logging
import uuid
from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound

from apps.bookings.models import Booking
from apps.payments.models import Payment, WebhookEvent

logger = logging.getLogger(__name__)


@transaction.atomic
def process_payment(user, booking_id: int, simulate_result: str = "SUCCESS") -> Payment:
    """
    Processes a simulated payment in an atomic transaction:
    1. Locks Booking row via select_for_update().
    2. Validates user owns the booking.
    3. Validates Booking status is PENDING.
    4. Snapshots amount from booking.amount (NOT CentreTest.price).
    5. Generates unique transaction_id (PAY_<uuid>).
    6. Updates Payment and Booking statuses atomically.
       - SUCCESS: Payment.status = SUCCESS, Booking.status = CONFIRMED
       - FAILED: Payment.status = FAILED, Booking.status = FAILED (releases capacity)
    """
    if simulate_result not in ["SUCCESS", "FAILED"]:
        raise ValidationError({"simulate_result": "Invalid simulate_result. Must be 'SUCCESS' or 'FAILED'."})

    try:
        booking = Booking.objects.select_for_update().select_related(
            'user', 'centre_test', 'slot'
        ).get(id=booking_id)
    except (Booking.DoesNotExist, ValueError, TypeError):
        raise ValidationError({"booking": "Invalid booking ID."})

    if booking.user != user:
        raise ValidationError({"booking": "You can only initiate payment for your own booking."})

    if booking.status != Booking.Status.PENDING:
        raise ValidationError({"booking": f"Payment can only be initiated for PENDING bookings. Current status is '{booking.status}'."})

    transaction_id = f"PAY_{uuid.uuid4().hex.upper()}"
    payment_amount = booking.amount

    if simulate_result == "SUCCESS":
        payment_status = Payment.Status.SUCCESS
        booking.status = Booking.Status.CONFIRMED
    else:
        payment_status = Payment.Status.FAILED
        booking.status = Booking.Status.FAILED

    payment = Payment.objects.create(
        booking=booking,
        transaction_id=transaction_id,
        amount=payment_amount,
        status=payment_status
    )
    booking.save(update_fields=['status', 'updated_at'])

    return payment


@transaction.atomic
def process_payment_webhook(
    event_id: str,
    event_type: str,
    transaction_id: str,
    status_str: str,
    payload: dict
) -> dict:
    """
    Processes incoming payment gateway webhook events with database-enforced race safety and state machine rules.
    """
    logger.info(
        f"Webhook received: event_id='{event_id}', event_type='{event_type}', "
        f"transaction_id='{transaction_id}', status='{status_str}'"
    )

    # 1. Idempotency check: if event_id already exists in DB, return immediately
    existing_event = WebhookEvent.objects.filter(event_id=event_id).first()
    if existing_event:
        logger.info(f"Duplicate webhook ignored: event_id='{event_id}' already processed.")
        return {
            "status": "already_processed",
            "already_processed": True,
            "event_id": event_id,
            "message": "Webhook event already processed."
        }

    # 2. Lock Payment and associated Booking
    try:
        payment = Payment.objects.select_for_update().get(transaction_id=transaction_id)
    except Payment.DoesNotExist:
        logger.warning(f"Unknown transaction: transaction_id='{transaction_id}'")
        raise NotFound({"transaction_id": f"Payment with transaction_id '{transaction_id}' not found."})

    booking = Booking.objects.select_for_update().get(id=payment.booking_id)

    # 3. Create WebhookEvent safely using a savepoint (nested atomic) to handle race conditions
    try:
        with transaction.atomic():
            webhook_event = WebhookEvent.objects.create(
                event_id=event_id,
                event_type=event_type,
                transaction_id=transaction_id,
                payload=payload if isinstance(payload, dict) else {},
            )
    except IntegrityError:
        logger.info(f"Duplicate webhook ignored (race condition IntegrityError): event_id='{event_id}'")
        return {
            "status": "already_processed",
            "already_processed": True,
            "event_id": event_id,
            "message": "Webhook event already processed."
        }

    # 4. State Machine Validation: CANCELLED bookings can never be revived
    if booking.status == Booking.Status.CANCELLED:
        logger.warning(f"Conflicting transition: Cannot process webhook for CANCELLED booking_id={booking.id}")
        raise ValidationError({"booking": "Cannot process payment webhook for a CANCELLED booking."})

    # 5. State Machine Validation: Payment and Booking transition rules
    if payment.status == Payment.Status.SUCCESS:
        if status_str == "FAILED":
            logger.warning(f"Conflicting transition: Payment {transaction_id} is SUCCESS but received FAILED webhook.")
            raise ValidationError({"status": "Cannot mark a SUCCESS payment as FAILED."})
        if booking.status == Booking.Status.FAILED:
            logger.warning(f"Conflicting transition: Booking {booking.id} is FAILED and cannot become CONFIRMED.")
            raise ValidationError({"booking": "Booking is FAILED and cannot become CONFIRMED."})

    elif payment.status == Payment.Status.FAILED:
        if status_str == "SUCCESS":
            logger.warning(f"Conflicting transition: Payment {transaction_id} is FAILED but received SUCCESS webhook.")
            raise ValidationError({"status": "Cannot mark a FAILED payment as SUCCESS."})
        if booking.status == Booking.Status.CONFIRMED:
            logger.warning(f"Conflicting transition: Booking {booking.id} is CONFIRMED and cannot become FAILED.")
            raise ValidationError({"booking": "Booking is CONFIRMED and cannot become FAILED."})

    elif payment.status == Payment.Status.PENDING:
        if status_str == "SUCCESS":
            payment.status = Payment.Status.SUCCESS
            booking.status = Booking.Status.CONFIRMED
        elif status_str == "FAILED":
            payment.status = Payment.Status.FAILED
            booking.status = Booking.Status.FAILED

        payment.save(update_fields=['status', 'updated_at'])
        booking.save(update_fields=['status', 'updated_at'])

    # 6. Mark webhook event processed_at timestamp
    webhook_event.processed_at = timezone.now()
    webhook_event.save(update_fields=['processed_at'])

    logger.info(f"Webhook processed successfully: event_id='{event_id}' for transaction_id='{transaction_id}'")
    return {
        "status": "success",
        "already_processed": False,
        "event_id": event_id,
        "message": "Webhook event processed successfully."
    }


def process_webhook_event(event_id: str, event_type: str, data: dict) -> dict:
    transaction_id = data.get('transaction_id', '') if isinstance(data, dict) else ''
    status_str = data.get('status', 'SUCCESS') if isinstance(data, dict) else 'SUCCESS'
    return process_payment_webhook(event_id, event_type, transaction_id, status_str, data)

