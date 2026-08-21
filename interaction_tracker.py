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

INTERACTIONS_SHEET = "Interactions"
FANS_SHEET = "Fans"


# =========================================================
# INTERACTION TYPES
# =========================================================

INTERACTION_TYPES = [
    "Instagram",
    "TikTok",
    "WhatsApp",
    "Music",
    "Event",
    "Campaign",
    "Merchandise",
    "Direct",
]


# =========================================================
# INTERACTION POINTS
# =========================================================

INTERACTION_POINTS = {
    "Instagram": 2,
    "TikTok": 2,
    "WhatsApp": 5,
    "Music": 2,
    "Event": 10,
    "Campaign": 5,
    "Merchandise": 10,
    "Direct": 5,
}


# =========================================================
# GENERATE INTERACTION ID
# =========================================================

def generate_interaction_id(
    existing_ids=None,
):

    """
    Generate a unique interaction ID.

    Example:

        INT-7A83F21C
    """

    existing_ids = set(
        str(value).strip().upper()
        for value in (existing_ids or [])
        if str(value).strip()
    )

    while True:

        interaction_id = (
            "INT-"
            + uuid.uuid4().hex[:8].upper()
        )

        if interaction_id not in existing_ids:

            return interaction_id


# =========================================================
# CLEAN VALUE
# =========================================================

def clean(value):

    if value is None:

        return ""

    try:

        if pd.isna(value):

            return ""

    except Exception:

        pass

    return str(value).strip()


# =========================================================
# GET EXISTING INTERACTION IDS
# =========================================================

def get_existing_interaction_ids():

    try:

        interactions = read_sheet(
            INTERACTIONS_SHEET
        )

    except Exception:

        return set()

    if interactions.empty:

        return set()

    if "interaction_id" not in interactions.columns:

        return set()

    return set(
        str(value).strip().upper()
        for value in interactions[
            "interaction_id"
        ]
        if str(value).strip()
    )


# =========================================================
# GET POINTS FOR INTERACTION
# =========================================================

def get_interaction_points(
    interaction_type,
):

    interaction_type = clean(
        interaction_type
    )

    return INTERACTION_POINTS.get(
        interaction_type,
        1,
    )


# =========================================================
# VALIDATE INTERACTION
# =========================================================

def validate_interaction(
    fan_id,
    interaction_type,
    description,
):

    errors = []

    if not clean(fan_id):

        errors.append(
            "Fan ID is required."
        )

    if not clean(interaction_type):

        errors.append(
            "Interaction type is required."
        )

    elif interaction_type not in INTERACTION_TYPES:

        errors.append(
            "Invalid interaction type."
        )

    if not clean(description):

        errors.append(
            "Description is required."
        )

    return errors


# =========================================================
# CREATE INTERACTION
# =========================================================

def create_interaction(
    fan_id,
    interaction_type,
    description,
    channel="",
    campaign="",
    value=0,
    interaction_date=None,
):

    """
    Create and save a new fan interaction.
    """

    # -----------------------------------------------------
    # Clean values
    # -----------------------------------------------------

    fan_id = clean(fan_id)

    interaction_type = clean(
        interaction_type
    )

    description = clean(
        description
    )

    channel = clean(
        channel
    )

    campaign = clean(
        campaign
    )

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    errors = validate_interaction(
        fan_id=fan_id,
        interaction_type=interaction_type,
        description=description,
    )

    if errors:

        raise ValueError(
            " ".join(errors)
        )

    # -----------------------------------------------------
    # Date
    # -----------------------------------------------------

    if interaction_date:

        interaction_date = clean(
            interaction_date
        )

    else:

        interaction_date = (
            datetime.now()
            .strftime(
                "%Y-%m-%d"
            )
        )

    # -----------------------------------------------------
    # Value
    # -----------------------------------------------------

    try:

        value = float(value)

    except Exception:

        value = 0

    # -----------------------------------------------------
    # Engagement points
    # -----------------------------------------------------

    points = get_interaction_points(
        interaction_type
    )

    # -----------------------------------------------------
    # ID
    # -----------------------------------------------------

    existing_ids = (
        get_existing_interaction_ids()
    )

    interaction_id = (
        generate_interaction_id(
            existing_ids
        )
    )

    # -----------------------------------------------------
    # Build record
    # -----------------------------------------------------

    interaction = {

        "interaction_id":
            interaction_id,

        "fan_id":
            fan_id,

        "date":
            interaction_date,

        "interaction_type":
            interaction_type,

        "description":
            description,

        "channel":
            channel,

        "campaign":
            campaign,

        "value":
            value,

        "engagement_points":
            points,

    }

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    add_row(
        INTERACTIONS_SHEET,
        interaction,
    )

    return interaction


# =========================================================
# GET FAN INTERACTIONS
# =========================================================

def get_interactions_for_fan(
    fan_id,
):

    interactions = read_sheet(
        INTERACTIONS_SHEET
    )

    if interactions.empty:

        return pd.DataFrame()

    if "fan_id" not in interactions.columns:

        return pd.DataFrame()

    result = interactions[
        interactions["fan_id"]
        .astype(str)
        .str.lower()
        ==
        str(fan_id)
        .lower()
    ].copy()

    if "date" in result.columns:

        result["_sort_date"] = pd.to_datetime(
            result["date"],
            errors="coerce",
        )

        result = result.sort_values(
            "_sort_date",
            ascending=False,
        )

        result = result.drop(
            columns=[
                "_sort_date"
            ]
        )

    return result


# =========================================================
# CALCULATE FAN ENGAGEMENT
# =========================================================

def calculate_fan_engagement(
    fan_id,
):

    interactions = (
        get_interactions_for_fan(
            fan_id
        )
    )

    if interactions.empty:

        return 0

    # -----------------------------------------------------
    # If engagement points exist
    # -----------------------------------------------------

    if (
        "engagement_points"
        in interactions.columns
    ):

        points = pd.to_numeric(
            interactions[
                "engagement_points"
            ],
            errors="coerce",
        ).fillna(0)

        total_points = points.sum()

    else:

        # -------------------------------------------------
        # Backwards compatibility
        # -------------------------------------------------

        if (
            "interaction_type"
            not in interactions.columns
        ):

            return 0

        total_points = 0

        for interaction_type in interactions[
            "interaction_type"
        ]:

            total_points += (
                get_interaction_points(
                    interaction_type
                )
            )

    # -----------------------------------------------------
    # Base score
    # -----------------------------------------------------

    base_score = 10

    score = (
        base_score
        + total_points
    )

    # -----------------------------------------------------
    # Cap score
    # -----------------------------------------------------

    return min(
        int(score),
        100,
    )


# =========================================================
# GET FAN ENGAGEMENT LEVEL
# =========================================================

def get_engagement_level(
    score,
):

    try:

        score = float(score)

    except Exception:

        score = 0

    if score >= 80:

        return "VIP"

    if score >= 60:

        return "Highly Engaged"

    if score >= 40:

        return "Engaged"

    if score >= 20:

        return "Warming Up"

    return "New"


# =========================================================
# FAN INTERACTION SUMMARY
# =========================================================

def get_fan_interaction_summary(
    fan_id,
):

    interactions = (
        get_interactions_for_fan(
            fan_id
        )
    )

    if interactions.empty:

        return {

            "total_interactions": 0,

            "engagement_score": 10,

            "engagement_level": "New",

            "total_value": 0,

        }

    # -----------------------------------------------------
    # Number of interactions
    # -----------------------------------------------------

    total_interactions = len(
        interactions
    )

    # -----------------------------------------------------
    # Engagement score
    # -----------------------------------------------------

    engagement_score = (
        calculate_fan_engagement(
            fan_id
        )
    )

    engagement_level = (
        get_engagement_level(
            engagement_score
        )
    )

    # -----------------------------------------------------
    # Interaction value
    # -----------------------------------------------------

    total_value = 0

    if "value" in interactions.columns:

        values = pd.to_numeric(
            interactions["value"],
            errors="coerce",
        ).fillna(0)

        total_value = float(
            values.sum()
        )

    return {

        "total_interactions":
            total_interactions,

        "engagement_score":
            engagement_score,

        "engagement_level":
            engagement_level,

        "total_value":
            total_value,

    }


# =========================================================
# INTERACTION TYPE SUMMARY
# =========================================================

def get_interaction_type_summary(
    fan_id,
):

    interactions = (
        get_interactions_for_fan(
            fan_id
        )
    )

    if interactions.empty:

        return pd.DataFrame()

    if (
        "interaction_type"
        not in interactions.columns
    ):

        return pd.DataFrame()

    summary = (
        interactions[
            "interaction_type"
        ]
        .value_counts()
        .rename(
            "Interactions"
        )
        .reset_index()
    )

    summary.columns = [
        "Interaction Type",
        "Interactions",
    ]

    return summary