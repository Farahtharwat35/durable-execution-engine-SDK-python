import random
import time
import asyncio
from .models import *


def validate_payment(input_data: PaymentInput) -> PaymentResult:
    time.sleep(2.0)
    
    if random.random() < 0.2:
        raise Exception("Payment validation failed")
    
    return PaymentResult(
        payment_id=f"pay_{random.randint(1000, 9999)}",
        amount=input_data.amount,
        status="validated"
    )


def reserve_inventory(input_data: InventoryInput) -> InventoryResult:
    time.sleep(1.5)
    
    if random.random() < 0.15:
        raise Exception(f"Insufficient inventory for {input_data.item_id}")
    
    return InventoryResult(
        reservation_id=f"res_{random.randint(1000, 9999)}",
        item_id=input_data.item_id,
        quantity=input_data.quantity,
        status="reserved"
    )


async def send_notification(input_data: NotificationInput) -> NotificationResult:
    await asyncio.sleep(1.0)
    
    if random.random() < 0.1:
        raise Exception(f"Failed to send {input_data.type}")
    
    return NotificationResult(
        notification_id=f"notif_{random.randint(1000, 9999)}",
        recipient=input_data.recipient,
        status="sent"
    )


def create_user(input_data: UserInput) -> UserResult:
    time.sleep(1.5)
    
    if random.random() < 0.1:
        raise Exception("User creation failed")
    
    return UserResult(
        user_id=f"user_{random.randint(1000, 9999)}",
        email=input_data.email,
        status="active"
    )


def process_refund(input_data: RefundInput) -> RefundResult:
    time.sleep(3.0)
    
    if random.random() < 0.05:
        raise Exception("Refund processing failed")
    
    return RefundResult(
        refund_id=f"ref_{random.randint(1000, 9999)}",
        amount=input_data.amount,
        status="processed"
    )


def check_order_status(order_id: str) -> dict:
    time.sleep(0.5)
    
    return {
        "order_id": order_id,
        "status": random.choice(["pending", "processing", "shipped", "delivered"]),
        "tracking_number": f"TRK{random.randint(100000, 999999)}"
    }
