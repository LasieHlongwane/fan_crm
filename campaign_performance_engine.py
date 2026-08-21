import pandas as pd

from data.google_sheets import (
    read_sheet,
    add_row,
)


# =========================================================
# CONFIGURATION
# =========================================================

CAMPAIGNS_SHEET = "Campaigns"
PURCHASES_SHEET = "Purchases"


# =========================================================
# SAFE NUMBER
# =========================================================

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
# LOAD CAMPAIGNS
# =========================================================

def load_campaigns():

    try:

        return read_sheet(
            CAMPAIGNS_SHEET
        )

    except Exception:

        return pd.DataFrame()


# =========================================================
# LOAD PURCHASES
# =========================================================

def load_purchases():

    try:

        return read_sheet(
            PURCHASES_SHEET
        )

    except Exception:

        return pd.DataFrame()


# =========================================================
# CALCULATE CAMPAIGN PERFORMANCE
# =========================================================

def calculate_campaign_performance(
    campaign,
):

    sent = safe_number(
        campaign.get(
            "sent",
            0,
        )
    )

    responses = safe_number(
        campaign.get(
            "responses",
            0,
        )
    )

    conversions = safe_number(
        campaign.get(
            "conversions",
            0,
        )
    )

    revenue = safe_number(
        campaign.get(
            "revenue",
            0,
        )
    )

    budget = safe_number(
        campaign.get(
            "budget",
            0,
        )
    )

    # -----------------------------------------------------
    # Response rate
    # -----------------------------------------------------

    if sent > 0:

        response_rate = (
            responses / sent
        ) * 100

    else:

        response_rate = 0

    # -----------------------------------------------------
    # Conversion rate
    # -----------------------------------------------------

    if sent > 0:

        conversion_rate = (
            conversions / sent
        ) * 100

    else:

        conversion_rate = 0

    # -----------------------------------------------------
    # Revenue per fan
    # -----------------------------------------------------

    if sent > 0:

        revenue_per_fan = (
            revenue / sent
        )

    else:

        revenue_per_fan = 0

    # -----------------------------------------------------
    # ROI
    # -----------------------------------------------------

    if budget > 0:

        roi = (
            (revenue - budget)
            / budget
        ) * 100

    else:

        roi = 0

    return {

        "sent": int(sent),

        "responses": int(
            responses
        ),

        "conversions": int(
            conversions
        ),

        "revenue": revenue,

        "budget": budget,

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
# BUILD PERFORMANCE TABLE
# =========================================================

def build_performance_table():

    campaigns = load_campaigns()

    if campaigns.empty:

        return pd.DataFrame()

    records = []

    for _, campaign in campaigns.iterrows():

        campaign_data = (
            campaign.to_dict()
        )

        metrics = (
            calculate_campaign_performance(
                campaign_data
            )
        )

        record = {

            "Campaign ID":
                campaign.get(
                    "campaign_id",
                    "",
                ),

            "Campaign":
                campaign.get(
                    "campaign_name",
                    "",
                ),

            "Type":
                campaign.get(
                    "campaign_type",
                    "",
                ),

            "Audience":
                campaign.get(
                    "audience_segment",
                    "",
                ),

            "Channel":
                campaign.get(
                    "channel",
                    "",
                ),

            "Status":
                campaign.get(
                    "status",
                    "",
                ),

            "Sent":
                metrics["sent"],

            "Responses":
                metrics["responses"],

            "Conversions":
                metrics["conversions"],

            "Revenue":
                metrics["revenue"],

            "Budget":
                metrics["budget"],

            "Response Rate":
                metrics[
                    "response_rate"
                ],

            "Conversion Rate":
                metrics[
                    "conversion_rate"
                ],

            "Revenue / Fan":
                metrics[
                    "revenue_per_fan"
                ],

            "ROI":
                metrics["roi"],
        }

        records.append(
            record
        )

    return pd.DataFrame(
        records
    )


# =========================================================
# TOTAL PERFORMANCE
# =========================================================

def get_total_performance():

    performance = (
        build_performance_table()
    )

    if performance.empty:

        return {

            "campaigns": 0,

            "sent": 0,

            "responses": 0,

            "conversions": 0,

            "revenue": 0.0,

            "budget": 0.0,

            "roi": 0.0,
        }

    sent = safe_number(
        performance["Sent"].sum()
    )

    responses = safe_number(
        performance["Responses"].sum()
    )

    conversions = safe_number(
        performance["Conversions"].sum()
    )

    revenue = safe_number(
        performance["Revenue"].sum()
    )

    budget = safe_number(
        performance["Budget"].sum()
    )

    if budget > 0:

        roi = (
            (revenue - budget)
            / budget
        ) * 100

    else:

        roi = 0

    return {

        "campaigns":
            len(performance),

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

        "roi":
            roi,
    }


# =========================================================
# BEST CAMPAIGN
# =========================================================

def get_best_campaign():

    performance = (
        build_performance_table()
    )

    if performance.empty:

        return None

    performance = performance.copy()

    performance["Revenue"] = (
        pd.to_numeric(
            performance["Revenue"],
            errors="coerce",
        )
        .fillna(0)
    )

    best_index = (
        performance[
            "Revenue"
        ].idxmax()
    )

    return (
        performance
        .loc[best_index]
        .to_dict()
    )


# =========================================================
# REVENUE BY CAMPAIGN
# =========================================================

def revenue_by_campaign():

    performance = (
        build_performance_table()
    )

    if performance.empty:

        return pd.DataFrame()

    result = performance[
        [
            "Campaign",
            "Revenue",
        ]
    ].copy()

    result["Revenue"] = pd.to_numeric(
        result["Revenue"],
        errors="coerce",
    ).fillna(0)

    result = (
        result
        .groupby(
            "Campaign",
            as_index=False,
        )
        .sum()
    )

    result = result.sort_values(
        "Revenue",
        ascending=False,
    )

    return result


# =========================================================
# REVENUE BY AUDIENCE
# =========================================================

def revenue_by_audience():

    performance = (
        build_performance_table()
    )

    if performance.empty:

        return pd.DataFrame()

    result = performance[
        [
            "Audience",
            "Revenue",
            "Conversions",
        ]
    ].copy()

    result["Revenue"] = pd.to_numeric(
        result["Revenue"],
        errors="coerce",
    ).fillna(0)

    result["Conversions"] = pd.to_numeric(
        result["Conversions"],
        errors="coerce",
    ).fillna(0)

    result = (
        result
        .groupby(
            "Audience",
            as_index=False,
        )
        .sum()
    )

    result = result.sort_values(
        "Revenue",
        ascending=False,
    )

    return result


# =========================================================
# REVENUE BY CHANNEL
# =========================================================

def revenue_by_channel():

    performance = (
        build_performance_table()
    )

    if performance.empty:

        return pd.DataFrame()

    result = performance[
        [
            "Channel",
            "Revenue",
            "Conversions",
        ]
    ].copy()

    result["Revenue"] = pd.to_numeric(
        result["Revenue"],
        errors="coerce",
    ).fillna(0)

    result["Conversions"] = pd.to_numeric(
        result["Conversions"],
        errors="coerce",
    ).fillna(0)

    result = (
        result
        .groupby(
            "Channel",
            as_index=False,
        )
        .sum()
    )

    result = result.sort_values(
        "Revenue",
        ascending=False,
    )

    return result


# =========================================================
# CAMPAIGN FUNNEL
# =========================================================

def campaign_funnel():

    performance = (
        build_performance_table()
    )

    if performance.empty:

        return {

            "sent": 0,

            "responses": 0,

            "conversions": 0,

            "revenue": 0.0,
        }

    return {

        "sent":
            int(
                safe_number(
                    performance[
                        "Sent"
                    ].sum()
                )
            ),

        "responses":
            int(
                safe_number(
                    performance[
                        "Responses"
                    ].sum()
                )
            ),

        "conversions":
            int(
                safe_number(
                    performance[
                        "Conversions"
                    ].sum()
                )
            ),

        "revenue":
            safe_number(
                performance[
                    "Revenue"
                ].sum()
            ),
    }


# =========================================================
# PURCHASE ATTRIBUTION
# =========================================================

def calculate_purchase_attribution():

    purchases = load_purchases()

    if purchases.empty:

        return pd.DataFrame()

    if "campaign_id" not in purchases.columns:

        return pd.DataFrame()

    if "amount" not in purchases.columns:

        return pd.DataFrame()

    purchases = purchases.copy()

    purchases["amount"] = pd.to_numeric(
        purchases["amount"],
        errors="coerce",
    ).fillna(0)

    result = (
        purchases
        .groupby(
            "campaign_id",
            as_index=False,
        )["amount"]
        .sum()
    )

    result = result.rename(
        columns={
            "amount": "Revenue"
        }
    )

    return result


# =========================================================
# RECORD ATTRIBUTED PURCHASE
# =========================================================

def attribute_purchase_to_campaign(
    campaign_id,
    fan_id,
    amount,
    product="",
):

    purchase_id = (
        "PUR-"
        + pd.Timestamp.now().strftime(
            "%Y%m%d%H%M%S%f"
        )
    )

    purchase = {

        "purchase_id":
            purchase_id,

        "fan_id":
            fan_id,

        "campaign_id":
            campaign_id,

        "amount":
            amount,

        "product":
            product,

        "purchase_date":
            pd.Timestamp.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
    }

    add_row(
        PURCHASES_SHEET,
        purchase,
    )

    return purchase


# =========================================================
# TEST
# =========================================================

def test_campaign_performance():

    print(
        "Campaign performance module loaded."
    )

    print(
        "build_performance_table:",
        build_performance_table,
    )

    print(
        "get_total_performance:",
        get_total_performance,
    )

    print(
        "get_best_campaign:",
        get_best_campaign,
    )