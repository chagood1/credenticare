# backend/api/payments.py

import os
import json
from fastapi import APIRouter, Request, HTTPException
from stripe import Webhook, error
import stripe
from ..services.supabase_client import supabase

router = APIRouter(prefix="/payments", tags=["payments"])

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = Webhook.construct_event(payload, sig_header, endpoint_secret)
    except error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")
    except Exception:
        raise HTTPException(400, "Malformed webhook")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Mark user as Pro by email
        user_res = await supabase.from_("users") \
            .select("id") \
            .eq("email", session.get("customer_email")) \
            .single() \
            .execute()
        if user_res.data:
            await supabase.from_("users") \
                .update({"is_pro": True}) \
                .eq("id", user_res.data["id"]) \
                .execute()

    return {"status": "success"}
