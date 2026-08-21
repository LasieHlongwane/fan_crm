#providers/whatsapp.py

#WhatsApp delivery provider using Twilio's WhatsApp API.

#Environment variables required:
#    TWILIO_ACCOUNT_SID
#    TWILIO_AUTH_TOKEN
#    TWILIO_WHATSAPP_FROM

#Example:
#    TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

#For production, replace the Twilio Sandbox sender with an approved
#WhatsApp sender and use approved templates where required.


import os
from typing import Any, Dict

import requests


class WhatsAppDeliveryError(Exception):
    """Raised when WhatsApp delivery cannot be completed."""


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise WhatsAppDeliveryError(
            f"Missing required environment variable: {name}"
        )

    return value


def normalize_whatsapp_number(phone: Any) -> str:
    """
    Normalize a stored phone number for Twilio WhatsApp.

    Accepts:
        +27821234567
        27821234567
        whatsapp:+27821234567

    This intentionally does not attempt to guess a country code.
    Store South African numbers with +27 for reliable delivery.
    """
    value = str(phone or "").strip()

    if not value:
        raise WhatsAppDeliveryError(
            "Fan does not have a WhatsApp phone number."
        )

    if value.lower().startswith("whatsapp:"):
        value = value.split(":", 1)[1].strip()

    value = value.replace(" ", "").replace("-", "")

    if not value.startswith("+"):
        raise WhatsAppDeliveryError(
            "Phone number must include an international country code, "
            "for example +27821234567."
        )

    return f"whatsapp:{value}"


def send_whatsapp_message(
    to: Any,
    message: str,
) -> Dict[str, Any]:
    """
    Send one WhatsApp message through Twilio.

    Returns:
        {
            "success": True,
            "message_sid": "...",
            "status": "...",
        }

    On failure:
        {
            "success": False,
            "error": "...",
        }
    """
    account_sid = _required_env("TWILIO_ACCOUNT_SID")
    auth_token = _required_env("TWILIO_AUTH_TOKEN")
    sender = _required_env("TWILIO_WHATSAPP_FROM")

    if not sender.lower().startswith("whatsapp:"):
        sender = f"whatsapp:{sender}"

    recipient = normalize_whatsapp_number(to)

    message = str(message or "").strip()

    if not message:
        raise WhatsAppDeliveryError(
            "Cannot send an empty WhatsApp message."
        )

    url = (
        f"https://api.twilio.com/2010-04-01/"
        f"Accounts/{account_sid}/Messages.json"
    )

    try:
        response = requests.post(
            url,
            auth=(account_sid, auth_token),
            data={
                "From": sender,
                "To": recipient,
                "Body": message,
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        return {
            "success": False,
            "error": f"Network error: {exc}",
            "message_sid": "",
            "status": "failed",
        }

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if 200 <= response.status_code < 300:
        return {
            "success": True,
            "message_sid": payload.get("sid", ""),
            "status": payload.get("status", "queued"),
            "error": "",
        }

    error_message = (
        payload.get("message")
        or payload.get("error_message")
        or response.text
        or f"HTTP {response.status_code}"
    )

    return {
        "success": False,
        "message_sid": payload.get("sid", ""),
        "status": "failed",
        "error": str(error_message),
    }
