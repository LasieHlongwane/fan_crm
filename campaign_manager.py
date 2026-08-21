import uuid
from datetime import datetime

import pandas as pd

from data.google_sheets import (
    read_sheet,
    add_row,
)


# =========================================================
# CONFIGURATION
# =========================================================

CAMPAIGNS_SHEET = "Campaigns"

CAMPAIGN_TYPES = [
    "Music Release",
    "Merchandise",
    "Event",
    "Exclusive Content",
    "Fan Appreciation",
    "General Promotion",
]

CAMPAIGN_CHANNELS = [
    "Instagram",
    "TikTok",
    "WhatsApp",
    "Email",
    "SMS",
    "Multiple Channels",
]

CAMPAIGN_STATUSES = [
    "Draft",
    "Ready",
    "Active",
    "Completed",
    "Cancelled",
]


# =========================================================
# GENERATE CAMPAIGN ID
# =========================================================

def generate_campaign_id():

    return (
        "CMP-"
        + uuid.uuid4().hex[:8].upper()
    )


# =========================================================
# GET CAMPAIGNS
# =========================================================

def get_campaigns():

    try:

        return read_sheet(
            CAMPAIGNS_SHEET
        )

    except Exception:

        return pd.DataFrame()


# =========================================================
# CREATE CAMPAIGN
# =========================================================

def create_campaign(
    name,
    campaign_type,
    audience_segment,
    channel,
    message,
    budget=0,
):

    # -----------------------------------------------------
    # Validate name
    # -----------------------------------------------------

    name = str(
        name or ""
    ).strip()

    if not name:

        raise ValueError(
            "Campaign name is required."
        )

    # -----------------------------------------------------
    # Validate message
    # -----------------------------------------------------

    message = str(
        message or ""
    ).strip()

    if not message:

        raise ValueError(
            "Campaign message is required."
        )

    # -----------------------------------------------------
    # Budget
    # -----------------------------------------------------

    try:

        budget = float(
            budget
        )

    except Exception:

        budget = 0.0

    # -----------------------------------------------------
    # Generate ID
    # -----------------------------------------------------

    campaign_id = (
        generate_campaign_id()
    )

    # -----------------------------------------------------
    # Campaign record
    # -----------------------------------------------------

    campaign = {

        "campaign_id":
            campaign_id,

        "campaign_name":
            name,

        "campaign_type":
            campaign_type,

        "audience_segment":
            audience_segment,

        "channel":
            channel,

        "message":
            message,

        "budget":
            budget,

        "status":
            "Draft",

        "created_at":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "sent":
            0,

        "responses":
            0,

        "conversions":
            0,

        "revenue":
            0,

    }

    # -----------------------------------------------------
    # Save to Google Sheets
    # -----------------------------------------------------

    add_row(
        CAMPAIGNS_SHEET,
        campaign,
    )

    return campaign


# =========================================================
# GET CAMPAIGN AUDIENCE
# =========================================================

def get_campaign_audience(
    fans,
    segment_name,
):

    # Import here to avoid circular imports
    from audience_segmentation import (
        get_segments,
    )

    segments = get_segments(
        fans
    )

    return segments.get(
        segment_name,
        pd.DataFrame(),
    )


# =========================================================
# CAMPAIGN PERFORMANCE
# =========================================================

def calculate_campaign_metrics(
    campaign,
):

    def number(
        value,
    ):

        try:

            return float(
                value
            )

        except Exception:

            return 0.0

    sent = number(
        campaign.get(
            "sent",
            0,
        )
    )

    responses = number(
        campaign.get(
            "responses",
            0,
        )
    )

    conversions = number(
        campaign.get(
            "conversions",
            0,
        )
    )

    revenue = number(
        campaign.get(
            "revenue",
            0,
        )
    )

    budget = number(
        campaign.get(
            "budget",
            0,
        )
    )

    response_rate = (
        responses / sent * 100
        if sent > 0
        else 0
    )

    conversion_rate = (
        conversions / sent * 100
        if sent > 0
        else 0
    )

    revenue_per_fan = (
        revenue / sent
        if sent > 0
        else 0
    )

    roi = (
        ((revenue - budget) / budget) * 100
        if budget > 0
        else 0
    )

    return {

        "sent":
            int(sent),

        "responses":
            int(responses),

        "conversions":
            int(conversions),

        "revenue":
            revenue,

        "budget":
            budget,

        "response_rate":
            response_rate,

        "conversion_rate":
            conversion_rate,

        "revenue_per_fan":
            revenue_per_fan,

        "roi":
            roi,
    }


# =========================================================
# CAMPAIGN SUMMARY
# =========================================================

def get_campaign_summary():

    campaigns = get_campaigns()

    if campaigns.empty:

        return {

            "campaigns": 0,

            "active": 0,

            "revenue": 0,

            "conversions": 0,
        }

    # -----------------------------------------------------
    # Active campaigns
    # -----------------------------------------------------

    if "status" in campaigns.columns:

        active = (
            campaigns["status"]
            .astype(str)
            .str.lower()
            .eq("active")
            .sum()
        )

    else:

        active = 0

    # -----------------------------------------------------
    # Revenue
    # -----------------------------------------------------

    if "revenue" in campaigns.columns:

        revenue = pd.to_numeric(
            campaigns["revenue"],
            errors="coerce",
        ).fillna(0).sum()

    else:

        revenue = 0

    # -----------------------------------------------------
    # Conversions
    # -----------------------------------------------------

    if "conversions" in campaigns.columns:

        conversions = pd.to_numeric(
            campaigns["conversions"],
            errors="coerce",
        ).fillna(0).sum()

    else:

        conversions = 0

    return {

        "campaigns":
            len(campaigns),

        "active":
            int(active),

        "revenue":
            float(revenue),

        "conversions":
            int(conversions),
    }


# =========================================================
# TEST FUNCTION
# =========================================================

def test_campaign_manager():

    print(
        "Campaign manager loaded successfully."
    )

    print(
        "create_campaign:",
        create_campaign,
    )

    print(
        "get_campaigns:",
        get_campaigns,
    )

    print(
        "get_campaign_audience:",
        get_campaign_audience,
    )