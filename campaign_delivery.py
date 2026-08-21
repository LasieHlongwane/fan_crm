#"""
#campaign_delivery.py

#Campaign Delivery / Execution layer.

#Flow:

 #   Campaig      ↓
 #   Audience
  #      ↓
   # Delivery Queue
   #     ↓
   # Pending
#        ↓
#    WhatsApp Provider
#        ↓
#    Sent / Failed

#Google Sheets structure is preserved. The module works with the existing
#Delivery Queue / Notifications sheet and adds only fields that already
#exist in the row headers.

#Expected queue columns (the code safely handles missing optional columns):

#    delivery_id
#    campaign_id
#    fan_id
#    fan_name
#    phone_number
#    channel
#    message
#    status
#    created_at
#    sent_at
#    failed_at
#    provider_message_id
#   provider_status
#    error

#If your existing sheet uses "Notifications" instead of "Delivery Queue",
#set DELIVERY_QUEUE_SHEET accordingly.


import os
import uuid
from datetime import datetime
from typing import Any, Dict

import pandas as pd

from data.google_sheets import (
    read_sheet,
    add_row,
    update_row,
)

from whatsapp import send_whatsapp_message


# =========================================================
# CONFIGURATION
# =========================================================

DELIVERY_QUEUE_SHEET = os.getenv(
    "DELIVERY_QUEUE_SHEET",
    "Delivery Queue",
)

PENDING_STATUS = "Pending"
SENT_STATUS = "Sent"
FAILED_STATUS = "Failed"


# =========================================================
# HELPERS
# =========================================================

def now_string() -> str:
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def generate_delivery_id() -> str:
    return (
        "DEL-"
        + uuid.uuid4().hex[:10].upper()
    )


def safe_string(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


# =========================================================
# LOAD QUEUE
# =========================================================

def get_delivery_queue() -> pd.DataFrame:
    try:
        return read_sheet(
            DELIVERY_QUEUE_SHEET
        )
    except Exception:
        return pd.DataFrame()


# =========================================================
# CREATE QUEUE ITEM
# =========================================================

def create_delivery_item(
    campaign_id: str,
    fan_id: str,
    fan_name: str,
    phone_number: str,
    message: str,
    channel: str = "WhatsApp",
) -> Dict[str, Any]:

    delivery_id = generate_delivery_id()

    item = {
        "delivery_id": delivery_id,
        "campaign_id": safe_string(campaign_id),
        "fan_id": safe_string(fan_id),
        "fan_name": safe_string(fan_name),
        "phone_number": safe_string(phone_number),
        "channel": safe_string(channel) or "WhatsApp",
        "message": safe_string(message),
        "status": PENDING_STATUS,
        "created_at": now_string(),
        "sent_at": "",
        "failed_at": "",
        "provider_message_id": "",
        "provider_status": "",
        "error": "",
    }

    add_row(
        DELIVERY_QUEUE_SHEET,
        item,
    )

    return item


# =========================================================
# GET ROW NUMBER
# =========================================================

def find_delivery_row(
    delivery_id: str,
):
    queue = get_delivery_queue()

    if queue.empty:
        return None

    if "delivery_id" not in queue.columns:
        return None

    matches = queue[
        queue["delivery_id"]
        .astype(str)
        .str.strip()
        .eq(str(delivery_id).strip())
    ]

    if matches.empty:
        return None

    # Google Sheets row 1 contains headers.
    dataframe_index = matches.index[0]
    return int(dataframe_index) + 2


# =========================================================
# UPDATE DELIVERY STATUS
# =========================================================

def update_delivery_status(
    delivery_id: str,
    status: str,
    provider_message_id: str = "",
    provider_status: str = "",
    error: str = "",
):
    row_number = find_delivery_row(
        delivery_id
    )

    if row_number is None:
        raise ValueError(
            f"Delivery item '{delivery_id}' was not found."
        )

    queue = get_delivery_queue()

    # Read the existing row so we do not destroy columns that
    # exist in the user's current Google Sheet.
    row_index = row_number - 2

    if row_index < 0 or row_index >= len(queue):
        raise ValueError(
            f"Invalid queue row for '{delivery_id}'."
        )

    existing = queue.iloc[
        row_index
    ].to_dict()

    existing["status"] = status

    if provider_message_id:
        existing["provider_message_id"] = (
            provider_message_id
        )

    if provider_status:
        existing["provider_status"] = (
            provider_status
        )

    if error:
        existing["error"] = error
    elif status == SENT_STATUS:
        existing["error"] = ""

    if status == SENT_STATUS:
        existing["sent_at"] = now_string()

    if status == FAILED_STATUS:
        existing["failed_at"] = now_string()

    update_row(
        DELIVERY_QUEUE_SHEET,
        row_number,
        existing,
    )

    return existing


# =========================================================
# SEND ONE PENDING ITEM
# =========================================================

def execute_delivery_item(
    delivery_id: str,
) -> Dict[str, Any]:

    queue = get_delivery_queue()

    if queue.empty:
        return {
            "success": False,
            "status": FAILED_STATUS,
            "error": "Delivery queue is empty.",
        }

    if "delivery_id" not in queue.columns:
        return {
            "success": False,
            "status": FAILED_STATUS,
            "error": (
                "Delivery queue is missing "
                "'delivery_id' column."
            ),
        }

    matches = queue[
        queue["delivery_id"]
        .astype(str)
        .str.strip()
        .eq(str(delivery_id).strip())
    ]

    if matches.empty:
        return {
            "success": False,
            "status": FAILED_STATUS,
            "error": (
                f"Delivery item '{delivery_id}' "
                "was not found."
            ),
        }

    item = matches.iloc[0].to_dict()

    current_status = safe_string(
        item.get("status", PENDING_STATUS)
    )

    if current_status.lower() != PENDING_STATUS.lower():
        return {
            "success": False,
            "status": current_status,
            "error": (
                f"Delivery item is already "
                f"'{current_status}'."
            ),
        }

    channel = safe_string(
        item.get("channel", "WhatsApp")
    ).lower()

    phone_number = safe_string(
        item.get("phone_number")
        or item.get("whatsapp_number")
        or item.get("phone")
    )

    message = safe_string(
        item.get("message")
    )

    # -----------------------------------------------------
    # WhatsApp
    # -----------------------------------------------------

    if channel in {
        "whatsapp",
        "wa",
    }:

        result = send_whatsapp_message(
            to=phone_number,
            message=message,
        )

    else:

        result = {
            "success": False,
            "status": "failed",
            "message_sid": "",
            "error": (
                f"Unsupported delivery channel: "
                f"{item.get('channel')}"
            ),
        }

    # -----------------------------------------------------
    # Provider success
    # -----------------------------------------------------

    if result.get("success"):

        updated = update_delivery_status(
            delivery_id=delivery_id,
            status=SENT_STATUS,
            provider_message_id=result.get(
                "message_sid",
                "",
            ),
            provider_status=result.get(
                "status",
                "",
            ),
        )

        return {
            "success": True,
            "status": SENT_STATUS,
            "delivery_id": delivery_id,
            "provider_message_id": result.get(
                "message_sid",
                "",
            ),
            "provider_status": result.get(
                "status",
                "",
            ),
            "row": updated,
        }

    # -----------------------------------------------------
    # Provider failure
    # -----------------------------------------------------

    error = safe_string(
        result.get("error")
        or "WhatsApp provider rejected the message."
    )

    updated = update_delivery_status(
        delivery_id=delivery_id,
        status=FAILED_STATUS,
        provider_message_id=result.get(
            "message_sid",
            "",
        ),
        provider_status=result.get(
            "status",
            "failed",
        ),
        error=error,
    )

    return {
        "success": False,
        "status": FAILED_STATUS,
        "delivery_id": delivery_id,
        "provider_message_id": result.get(
            "message_sid",
            "",
        ),
        "provider_status": result.get(
            "status",
            "failed",
        ),
        "error": error,
        "row": updated,
    }


# =========================================================
# EXECUTE PENDING QUEUE
# =========================================================

def execute_pending_deliveries(
    campaign_id: str = "",
    limit: int = 50,
) -> Dict[str, Any]:

    queue = get_delivery_queue()

    if queue.empty:
        return {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "results": [],
        }

    if "status" not in queue.columns:
        return {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "results": [],
            "error": (
                "Delivery queue is missing "
                "'status' column."
            ),
        }

    pending = queue[
        queue["status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq(PENDING_STATUS.lower())
    ].copy()

    if campaign_id and "campaign_id" in pending.columns:
        pending = pending[
            pending["campaign_id"]
            .astype(str)
            .str.strip()
            .eq(str(campaign_id).strip())
        ]

    pending = pending.head(
        max(1, safe_int(limit, 50))
    )

    results = []
    sent = 0
    failed = 0

    for _, row in pending.iterrows():

        delivery_id = safe_string(
            row.get("delivery_id")
        )

        if not delivery_id:
            failed += 1
            results.append({
                "success": False,
                "status": FAILED_STATUS,
                "error": "Missing delivery_id.",
            })
            continue

        result = execute_delivery_item(
            delivery_id
        )

        results.append(result)

        if result.get("success"):
            sent += 1
        else:
            failed += 1

    return {
        "processed": len(pending),
        "sent": sent,
        "failed": failed,
        "skipped": max(
            0,
            len(pending) - sent - failed,
        ),
        "results": results,
    }


# =========================================================
# QUEUE SUMMARY
# =========================================================

def get_delivery_summary(
    campaign_id: str = "",
) -> Dict[str, int]:

    queue = get_delivery_queue()

    if queue.empty:
        return {
            "total": 0,
            "pending": 0,
            "sent": 0,
            "failed": 0,
        }

    if campaign_id and "campaign_id" in queue.columns:
        queue = queue[
            queue["campaign_id"]
            .astype(str)
            .str.strip()
            .eq(str(campaign_id).strip())
        ]

    if "status" not in queue.columns:
        return {
            "total": len(queue),
            "pending": 0,
            "sent": 0,
            "failed": 0,
        }

    statuses = (
        queue["status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return {
        "total": len(queue),
        "pending": int(
            statuses.eq("pending").sum()
        ),
        "sent": int(
            statuses.eq("sent").sum()
        ),
        "failed": int(
            statuses.eq("failed").sum()
        ),
    }


# =========================================================
# TEST
# =========================================================

def test_campaign_delivery():

    print(
        "Campaign delivery module loaded."
    )

    print(
        "Delivery queue sheet:",
        DELIVERY_QUEUE_SHEET,
    )

    print(
        "get_delivery_queue:",
        get_delivery_queue,
    )

    print(
        "execute_delivery_item:",
        execute_delivery_item,
    )

    print(
        "execute_pending_deliveries:",
        execute_pending_deliveries,
    )
