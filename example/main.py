import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import DurableApp, Service, WorkflowContext
from app.types import RetryMechanism
from fastapi import FastAPI
from demo.models import *
from demo.actions import *
import uvicorn
import asyncio


def main():
    app = FastAPI(title="Durable Execution Demo", version="1.0.0")
    
    order_service = Service("orders")
    user_service = Service("users")
    payment_service = Service("payments")

    @order_service.workflow()
    async def process_order(ctx: WorkflowContext, input: OrderInput) -> dict:
            await asyncio.sleep(0.5)

            payment_result = await ctx.execute_action(
                action=validate_payment,
                input_data=PaymentInput(
                    amount=input.total_amount,
                    payment_method="credit_card"
                ),
                max_retries=3,
                retry_mechanism=RetryMechanism.EXPONENTIAL
            )
            
            await asyncio.sleep(0.3)
            
            reservations = []
            for idx, item in enumerate(input.items):
                reservation = await ctx.execute_action(
                    action=reserve_inventory,
                    input_data=InventoryInput(
                        item_id=item.id,
                        quantity=item.quantity
                    ),
                    max_retries=2,
                    retry_mechanism=RetryMechanism.LINEAR,
                    action_name=f"reserve_inventory_{idx}"
                )
                reservations.append(reservation)
            
            await asyncio.sleep(0.2)
            
            notification_result = await ctx.execute_action(
                action=send_notification,
                input_data=NotificationInput(
                    recipient=input.customer_email,
                    message=f"Order {input.order_id} confirmed",
                    type="email"
                ),
                max_retries=2,
                retry_mechanism=RetryMechanism.CONSTANT
            )
            
            return {
                "order_id": input.order_id,
                "status": "completed",
                "payment": payment_result,
                "reservations": reservations,
                "notification": notification_result
            }


    @order_service.workflow()
    def get_order_status(ctx: WorkflowContext, input: OrderStatusInput) -> OrderStatusResult:
        result = ctx.execute_action(
            action=check_order_status,
            input_data=input.order_id,
            max_retries=1,
            retry_mechanism=RetryMechanism.CONSTANT
        )
        
        return OrderStatusResult(
            order_id=result["order_id"],
            status=result["status"],
            tracking_number=result.get("tracking_number")
        )

    @user_service.workflow()
    async def register_user(ctx: WorkflowContext, input: UserInput) -> dict:
        await asyncio.sleep(0.5)
        
        user_result = await ctx.execute_action(
            action=create_user,
            input_data=input,
            max_retries=2,
            retry_mechanism=RetryMechanism.EXPONENTIAL
        )
        
        notification_result = await ctx.execute_action(
            action=send_notification,
            input_data=NotificationInput(
                recipient=input.email,
                message=f"Welcome {input.username}!",
                type="email"
            ),
            max_retries=1,
            retry_mechanism=RetryMechanism.CONSTANT
        )
        
        return {
            "success": True,
            "user": user_result,
            "notification": notification_result
        }

    @payment_service.workflow()
    async def process_refund(ctx: WorkflowContext, input: RefundInput) -> dict:
        refund_result = await ctx.execute_action(
            action=process_refund,
            input_data=input,
            max_retries=3,
            retry_mechanism=RetryMechanism.EXPONENTIAL
        )
        
        return {
            "order_id": input.order_id,
            "refund": refund_result,
            "status": "completed"
        }

    durable_app = DurableApp(app)

    return app


if __name__ == "__main__":
    app = main()
    print("🚀 Demo Server Starting...")
    print("Services: orders, users, payments")
    uvicorn.run(app, host="0.0.0.0", port=8000)