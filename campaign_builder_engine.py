import pandas as pd

from data.google_sheets import (
    read_sheet,
    add_row,
)


# =========================================================
# CONFIGURATION
# =========================================================

CAMPAIGNS_SHEET = "Campaigns"


# =========================================================
# HELPERS
# =========================================================

def safe_text(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def safe_number(value, default=0):
    try:
        if value is None:
            return default

        if pd.isna(value):
            return default

        return float(value)

    except Exception:
        return default


# =========================================================
# LOAD FANS
# =========================================================

def load_fans():

    try:
        return read_sheet("Fans")

    except Exception:
        return pd.DataFrame()


# =========================================================
# GET UNIQUE FILTER OPTIONS
# =========================================================

def get_filter_options(fans, column):

    if fans.empty:
        return []

    if column not in fans.columns:
        return []

    values = (
        fans[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    values = values[values != ""]

    return sorted(
        values.unique().tolist()
    )


# =========================================================
# FILTER AUDIENCE
# =========================================================

def filter_audience(
    fans,
    city="All",
    age_group="All",
    favorite_song="All",
    favorite_brand="All",
    source="All",
    min_engagement=0,
    min_spend=0,
):
    """
    Build a campaign audience using fan attributes.
    """

    if fans.empty:
        return pd.DataFrame()

    audience = fans.copy()

    # -----------------------------------------------------
    # CITY
    # -----------------------------------------------------

    if (
        city != "All"
        and "location" in audience.columns
    ):

        audience = audience[
            audience["location"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            ==
            city.lower()
        ]

    # -----------------------------------------------------
    # AGE
    # -----------------------------------------------------

    if (
        age_group != "All"
        and "age_group" in audience.columns
    ):

        audience = audience[
            audience["age_group"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            ==
            age_group.lower()
        ]

    # -----------------------------------------------------
    # FAVORITE SONG
    # -----------------------------------------------------

    if (
        favorite_song != "All"
        and "favorite_song" in audience.columns
    ):

        audience = audience[
            audience["favorite_song"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            ==
            favorite_song.lower()
        ]

    # -----------------------------------------------------
    # FAVORITE BRAND
    # -----------------------------------------------------

    if (
        favorite_brand != "All"
        and "favorite_brand" in audience.columns
    ):

        audience = audience[
            audience["favorite_brand"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            ==
            favorite_brand.lower()
        ]

    # -----------------------------------------------------
    # SOURCE
    # -----------------------------------------------------

    if (
        source != "All"
        and "source" in audience.columns
    ):

        audience = audience[
            audience["source"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            ==
            source.lower()
        ]

    # -----------------------------------------------------
    # ENGAGEMENT
    # -----------------------------------------------------

    if "engagement_score" in audience.columns:

        scores = pd.to_numeric(
            audience["engagement_score"],
            errors="coerce",
        ).fillna(0)

        audience = audience[
            scores >= min_engagement
        ]

    # -----------------------------------------------------
    # SPEND
    # -----------------------------------------------------

    if "total_spend" in audience.columns:

        spend = pd.to_numeric(
            audience["total_spend"],
            errors="coerce",
        ).fillna(0)

        audience = audience[
            spend >= min_spend
        ]

    return audience


# =========================================================
# CAMPAIGN ID
# =========================================================

def generate_campaign_id():

    try:

        campaigns = read_sheet(
            CAMPAIGNS_SHEET
        )

    except Exception:

        campaigns = pd.DataFrame()

    if campaigns.empty:
        return "CAM-0001"

    if "campaign_id" not in campaigns.columns:
        return "CAM-0001"

    ids = (
        campaigns["campaign_id"]
        .fillna("")
        .astype(str)
    )

    numbers = []

    for campaign_id in ids:

        try:

            number = int(
                campaign_id
                .replace("CAM-", "")
            )

            numbers.append(number)

        except Exception:
            continue

    if not numbers:
        return "CAM-0001"

    next_number = max(numbers) + 1

    return f"CAM-{next_number:04d}"


# =========================================================
# CREATE CAMPAIGN
# =========================================================

def create_campaign(
    campaign_name,
    campaign_type,
    audience_segment,
    channel,
    message,
    budget=0,
    target_count=0,
):
    """
    Create a campaign record in Google Sheets.
    """

    campaign_id = generate_campaign_id()

    campaign = {

        "campaign_id":
            campaign_id,

        "campaign_name":
            campaign_name,

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

        "target_count":
            target_count,

        "sent":
            0,

        "responses":
            0,

        "conversions":
            0,

        "revenue":
            0,

        "status":
            "Draft",

        "created_at":
            pd.Timestamp.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
    }

    add_row(
        CAMPAIGNS_SHEET,
        campaign,
    )

    return campaign


# =========================================================
# ESTIMATE CAMPAIGN OPPORTUNITY
# =========================================================

def estimate_opportunity(
    audience,
    conversion_rate=0.10,
    average_order_value=500,
):
    """
    Estimate potential campaign revenue.

    Example:
    20 fans × 10% conversion × R500
    = R1,000 estimated revenue.
    """

    audience_size = len(audience)

    estimated_conversions = (
        audience_size
        * conversion_rate
    )

    estimated_revenue = (
        estimated_conversions
        * average_order_value
    )

    return {

        "audience_size":
            audience_size,

        "estimated_conversions":
            round(
                estimated_conversions,
                1,
            ),

        "estimated_revenue":
            round(
                estimated_revenue,
                2,
            ),
    }


# =========================================================
# CAMPAIGN SUMMARY
# =========================================================

def audience_summary(audience):

    if audience.empty:

        return {

            "fans": 0,

            "average_engagement": 0,

            "average_spend": 0,

            "top_city": "—",

            "top_brand": "—",

            "top_song": "—",
        }

    engagement = 0

    if "engagement_score" in audience.columns:

        engagement = pd.to_numeric(
            audience[
                "engagement_score"
            ],
            errors="coerce",
        ).fillna(0).mean()

    spend = 0

    if "total_spend" in audience.columns:

        spend = pd.to_numeric(
            audience[
                "total_spend"
            ],
            errors="coerce",
        ).fillna(0).mean()

    def most_common(column):

        if column not in audience.columns:
            return "—"

        values = (
            audience[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        values = values[
            values != ""
        ]

        if values.empty:
            return "—"

        return str(
            values.value_counts().idxmax()
        )

    return {

        "fans":
            len(audience),

        "average_engagement":
            round(
                engagement,
                1,
            ),

        "average_spend":
            round(
                spend,
                2,
            ),

        "top_city":
            most_common(
                "location"
            ),

        "top_brand":
            most_common(
                "favorite_brand"
            ),

        "top_song":
            most_common(
                "favorite_song"
            ),
    }