import razorpay
from fastapi import APIRouter, Request
from app.core.config import settings

router = APIRouter()

# Razorpay client
razorpay_client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID, 
        settings.RAZORPAY_KEY_SECRET
    )
)

@router.post("/create-order")
async def create_order(request: Request):
    body = await request.json()
    amount = body.get("amount", 100) * 100  # convert to paise (₹100 → 10000)

    order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    return order


@router.post("/verify-payment")
async def verify_payment(request: Request):
    body = await request.json()
    try:
        razorpay_client.utility.verify_payment_signature(body)
        return {"status": "success"}
    except:
        return {"status": "failure"}
