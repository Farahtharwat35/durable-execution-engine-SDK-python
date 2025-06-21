# Durable Execution Engine SDK - Demo Workflows

This document provides a comprehensive overview of all workflows in the demo application, including their failure characteristics, retry configurations, and expected behavior.

## Overview

The demo showcases three main services with multiple workflows that demonstrate durable execution patterns, retry mechanisms, and error handling:

- **Orders Service**: Complex multi-step workflows with dependent actions
- **Users Service**: User management with notifications  
- **Payments Service**: Payment processing and refund handling

## Services and Workflows

### 🛒 Orders Service (`orders`)

#### 1. Process Order (`process_order`)
**Endpoint**: `POST /execute/orders/process_order`

A complex multi-step workflow demonstrating sequential action execution with different retry strategies.

**Input**: `OrderInput`
```json
{
  "order_id": "string",
  "customer_email": "string", 
  "items": [
    {
      "id": "string",
      "quantity": number,
      "price": number
    }
  ],
  "total_amount": number
}
```

**Workflow Steps**:
1. **Payment Validation** (8s processing time)
   - Action: `validate_payment`
   - Failure Rate: **50%** 
   - Max Retries: 3
   - Retry Mechanism: Exponential
   - Error: "Payment validation failed"

2. **Inventory Reservation** (10s processing time per item)
   - Action: `reserve_inventory` (executed for each item)
   - Failure Rate: **50%**
   - Max Retries: 2
   - Retry Mechanism: Linear
   - Error: "Insufficient inventory for {item_id}"
   - Custom Action Names: `reserve_inventory_0`, `reserve_inventory_1`, etc.

3. **Order Confirmation Notification** (6s processing time)
   - Action: `send_notification`
   - Failure Rate: **0%** (Always succeeds)
   - Max Retries: 2
   - Retry Mechanism: Constant
   - Recipient: Customer email

**Expected Behavior**: Due to high failure rates in payment and inventory steps, this workflow frequently requires retries and may fail entirely if retries are exhausted.

#### 2. Get Order Status (`get_order_status`)
**Endpoint**: `POST /execute/orders/get_order_status`

A simple status check workflow that always succeeds.

**Input**: `OrderStatusInput`
```json
{
  "order_id": "string"
}
```

**Workflow Steps**:
1. **Status Check** (5s processing time)
   - Action: `check_order_status`
   - Failure Rate: **0%** (Always succeeds)
   - Max Retries: 1
   - Retry Mechanism: Constant
   - Returns random status: "pending", "processing", "shipped", or "delivered"

**Expected Behavior**: Reliable workflow that demonstrates successful action execution.

### 👤 Users Service (`users`)

#### 1. Register User (`register_user`)
**Endpoint**: `POST /execute/users/register_user`

User registration workflow with welcome notification.

**Input**: `UserInput`
```json
{
  "email": "string",
  "username": "string",
  "password": "string"
}
```

**Workflow Steps**:
1. **User Creation** (7s processing time)
   - Action: `create_user`
   - Failure Rate: **0%** (Always succeeds)
   - Max Retries: 2
   - Retry Mechanism: Exponential

2. **Welcome Notification** (6s processing time)
   - Action: `send_notification`
   - Failure Rate: **0%** (Always succeeds)
   - Max Retries: 1
   - Retry Mechanism: Constant
   - Message: "Welcome {username}!"

**Expected Behavior**: Highly reliable workflow that consistently succeeds.

### 💳 Payments Service (`payments`)

#### 1. Process Refund (`process_refund`)
**Endpoint**: `POST /execute/payments/process_refund`

Complex refund processing with order verification and notifications.

**Input**: `RefundInput`
```json
{
  "order_id": "string",
  "amount": number,
  "reason": "string"
}
```

**Workflow Steps**:
1. **Pre-Refund Order Check** (5s processing time)
   - Action: `check_order_status`
   - Failure Rate: **0%** (Always succeeds)
   - Max Retries: 2
   - Retry Mechanism: Constant
   - Custom Action Name: `pre_refund_order_check`

2. **Refund Processing** (9s processing time)
   - Action: `process_refund`
   - Failure Rate: **90%** (Very high failure rate)
   - Max Retries: 3
   - Retry Mechanism: Exponential
   - Error: "Refund processing failed"

3. **Finance Notification** (6s processing time)
   - Action: `send_notification`
   - Failure Rate: **0%** (Always succeeds)
   - Max Retries: 2
   - Retry Mechanism: Linear
   - Recipient: "finance@company.com"

**Expected Behavior**: This workflow has the highest failure rate and will frequently exhaust retries due to the 90% failure rate in refund processing.

#### 2. Verify Payment and Notify (`verify_payment_and_notify`)
**Endpoint**: `POST /execute/payments/verify_payment_and_notify`

Payment verification with admin notification.

**Input**: `PaymentInput`
```json
{
  "amount": number,
  "payment_method": "string"
}
```

**Workflow Steps**:
1. **Payment Validation** (8s processing time)
   - Action: `validate_payment`
   - Failure Rate: **50%**
   - Max Retries: 3
   - Retry Mechanism: Exponential
   - Custom Action Name: `primary_payment_validation`

2. **Admin Notification** (6s processing time)
   - Action: `send_notification`
   - Failure Rate: **0%** (Always succeeds)
   - Max Retries: 2
   - Retry Mechanism: Linear
   - Recipient: "admin@company.com"

**Expected Behavior**: Moderate failure rate due to payment validation step.

## Action Failure Summary

| Action | Processing Time | Failure Rate | Typical Error |
|--------|----------------|--------------|---------------|
| `validate_payment` | 8 seconds | **50%** | "Payment validation failed" |
| `reserve_inventory` | 10 seconds | **50%** | "Insufficient inventory for {item_id}" |
| `process_refund` | 9 seconds | **90%** | "Refund processing failed" |
| `send_notification` | 6 seconds | **0%** | Never fails |
| `create_user` | 7 seconds | **0%** | Never fails |
| `check_order_status` | 5 seconds | **0%** | Never fails |

## Retry Mechanisms

The demo showcases three different retry mechanisms:

1. **Exponential**: Exponentially increasing delays between retries
2. **Linear**: Fixed incremental delays between retries  
3. **Constant**: Fixed delay between retries

## Testing the Demo

### High Success Rate Workflows
- `users/register_user` - Should consistently succeed
- `orders/get_order_status` - Always succeeds

### Moderate Failure Rate Workflows
- `orders/process_order` - 50% failure rate on payment and inventory
- `payments/verify_payment_and_notify` - 50% failure rate on payment

### High Failure Rate Workflows
- `payments/process_refund` - 90% failure rate on refund processing

### Recommended Test Scenarios

1. **Success Path**: Call `register_user` or `get_order_status`
2. **Retry Demonstration**: Call `process_order` or `verify_payment_and_notify` multiple times
3. **Failure Demonstration**: Call `process_refund` to see retry exhaustion
4. **Complex Workflow**: Call `process_order` with multiple items to see parallel inventory reservations
