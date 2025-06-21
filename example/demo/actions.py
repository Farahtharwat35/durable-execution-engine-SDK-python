import asyncio
import random
import time

from .models import *


def validate_payment(input_data: PaymentInput) -> PaymentResult:
    time.sleep(8)

    if random.random() < 0.5:
        raise Exception("Payment validation failed")

    return PaymentResult(
        payment_id=f"pay_{random.randint(1000, 9999)}",
        amount=input_data.amount,
        status="validated",
    )


def reserve_inventory(input_data: InventoryInput) -> InventoryResult:
    time.sleep(10)

    if random.random() < 0.50:
        raise Exception(f"Insufficient inventory for {input_data.item_id}")

    return InventoryResult(
        reservation_id=f"res_{random.randint(1000, 9999)}",
        item_id=input_data.item_id,
        quantity=input_data.quantity,
        status="reserved",
    )


async def send_notification(
    input_data: NotificationInput,
) -> NotificationResult:
    await asyncio.sleep(6)

    return NotificationResult(
        notification_id=f"notif_{random.randint(1000, 9999)}",
        recipient=input_data.recipient,
        status="sent",
    )


def create_user(input_data: UserInput) -> UserResult:
    time.sleep(7)

    return UserResult(
        user_id=f"user_{random.randint(1000, 9999)}",
        email=input_data.email,
        status="active",
    )


def process_refund(input_data: RefundInput) -> RefundResult:
    time.sleep(9)

    if random.random() < 0.9:
        raise Exception("Refund processing failed")

    return RefundResult(
        refund_id=f"ref_{random.randint(1000, 9999)}",
        amount=input_data.amount,
        status="processed",
    )


def check_order_status(order_id: str) -> dict:
    time.sleep(5)

    return {
        "order_id": order_id,
        "status": random.choice(
            ["pending", "processing", "shipped", "delivered"]
        ),
        "tracking_number": f"TRK{random.randint(100000, 999999)}",
    }
