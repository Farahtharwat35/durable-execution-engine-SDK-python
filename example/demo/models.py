from typing import List, Optional

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    id: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)


class OrderInput(BaseModel):
    order_id: str
    customer_email: str
    items: List[OrderItem]
    total_amount: float = Field(gt=0)


class PaymentInput(BaseModel):
    amount: float = Field(gt=0)
    payment_method: str = "credit_card"


class PaymentResult(BaseModel):
    payment_id: str
    amount: float
    status: str


class InventoryInput(BaseModel):
    item_id: str
    quantity: int = Field(gt=0)


class InventoryResult(BaseModel):
    reservation_id: str
    item_id: str
    quantity: int
    status: str


class NotificationInput(BaseModel):
    recipient: str
    message: str
    type: str = "email"


class NotificationResult(BaseModel):
    notification_id: str
    recipient: str
    status: str


class UserInput(BaseModel):
    email: str
    username: str = Field(min_length=3)
    password: str = Field(min_length=6)


class UserResult(BaseModel):
    user_id: str
    email: str
    status: str


class OrderStatusInput(BaseModel):
    order_id: str


class OrderStatusResult(BaseModel):
    order_id: str
    status: str
    tracking_number: Optional[str] = None


class RefundInput(BaseModel):
    order_id: str
    amount: float = Field(gt=0)
    reason: str = "Customer request"


class RefundResult(BaseModel):
    refund_id: str
    amount: float
    status: str
