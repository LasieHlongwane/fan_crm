import pandas as pd


# =========================================================
# SEGMENT DEFINITIONS
# =========================================================

SEGMENTS = {
    "VIP Fans": "High engagement + has purchased",

    "Superfans": "Very high engagement",

    "Potential Buyers": "Highly engaged but has not purchased",

    "Merch Buyers": "Fans who have purchased merchandise",

    "Event Fans": "Fans interested in events",

    "Fashion Audience": "Fans with a favorite brand",

    "WHOLENESS Fans": "Fans whose favorite song is WHOLENESS",

    "New Fans": "Recently added fans",

    "Cold Fans": "Fans with low engagement",

    "High Value Fans": "Fans with significant lifetime spend",
}


# =========================================================
# SAFE NUMERIC CONVERSION
# =========================================================

def numeric_series(
    dataframe,
    column,
    default=0,
):

    if column not in dataframe.columns:

        return pd.Series(
            default,
            index=dataframe.index,
        )

    return pd.to_numeric(
        dataframe[column],
        errors="coerce",
    ).fillna(default)


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text_series(
    dataframe,
    column,
):

    if column not in dataframe.columns:

        return pd.Series(
            "",
            index=dataframe.index,
        )

    return (
        dataframe[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )


# =========================================================
# VIP FANS
# =========================================================

def get_vip_fans(
    fans,
):

    if fans.empty:

        return fans.copy()

    score = numeric_series(
        fans,
        "engagement_score",
    )

    spend = numeric_series(
        fans,
        "total_spend",
    )

    return fans[
        (score >= 80)
        & (spend > 0)
    ].copy()


# =========================================================
# SUPERFANS
# =========================================================

def get_superfans(
    fans,
):

    if fans.empty:

        return fans.copy()

    score = numeric_series(
        fans,
        "engagement_score",
    )

    return fans[
        score >= 80
    ].copy()


# =========================================================
# POTENTIAL BUYERS
# =========================================================

def get_potential_buyers(
    fans,
):

    if fans.empty:

        return fans.copy()

    score = numeric_series(
        fans,
        "engagement_score",
    )

    spend = numeric_series(
        fans,
        "total_spend",
    )

    return fans[
        (score >= 60)
        & (spend <= 0)
    ].copy()


# =========================================================
# MERCH BUYERS
# =========================================================

def get_merch_buyers(
    fans,
):

    if fans.empty:

        return fans.copy()

    spend = numeric_series(
        fans,
        "total_spend",
    )

    return fans[
        spend > 0
    ].copy()


# =========================================================
# EVENT FANS
# =========================================================

def get_event_fans(
    fans,
):

    if fans.empty:

        return fans.copy()

    # -----------------------------------------------------
    # Check common possible column names
    # -----------------------------------------------------

    possible_columns = [
        "event_interest",
        "event_interested",
        "interested_in_events",
        "events",
        "would_you_like_notification_about",
    ]

    for column in possible_columns:

        if column in fans.columns:

            values = clean_text_series(
                fans,
                column,
            ).str.lower()

            mask = values.str.contains(
                "event",
                na=False,
            )

            return fans[mask].copy()

    return fans.iloc[0:0].copy()


# =========================================================
# FASHION AUDIENCE
# =========================================================

def get_fashion_audience(
    fans,
):

    if fans.empty:

        return fans.copy()

    brands = clean_text_series(
        fans,
        "favorite_brand",
    )

    return fans[
        brands != ""
    ].copy()


# =========================================================
# WHOLENESS FANS
# =========================================================

def get_wholeness_fans(
    fans,
):

    if fans.empty:

        return fans.copy()

    songs = clean_text_series(
        fans,
        "favorite_song",
    )

    return fans[
        songs.str.lower()
        == "wholeness"
    ].copy()


# =========================================================
# NEW FANS
# =========================================================

def get_new_fans(
    fans,
    days=30,
):

    if fans.empty:

        return fans.copy()

    if "created_at" not in fans.columns:

        return fans.iloc[0:0].copy()

    dates = pd.to_datetime(
        fans["created_at"],
        errors="coerce",
    )

    cutoff = (
        pd.Timestamp.now()
        - pd.Timedelta(
            days=days
        )
    )

    return fans[
        dates >= cutoff
    ].copy()


# =========================================================
# COLD FANS
# =========================================================

def get_cold_fans(
    fans,
):

    if fans.empty:

        return fans.copy()

    score = numeric_series(
        fans,
        "engagement_score",
    )

    return fans[
        score < 30
    ].copy()


# =========================================================
# HIGH VALUE FANS
# =========================================================

def get_high_value_fans(
    fans,
    minimum_spend=500,
):

    if fans.empty:

        return fans.copy()

    spend = numeric_series(
        fans,
        "total_spend",
    )

    return fans[
        spend >= minimum_spend
    ].copy()


# =========================================================
# GET ALL SEGMENTS
# =========================================================

def get_segments(
    fans,
):

    return {

        "VIP Fans":
            get_vip_fans(fans),

        "Superfans":
            get_superfans(fans),

        "Potential Buyers":
            get_potential_buyers(fans),

        "Merch Buyers":
            get_merch_buyers(fans),

        "Event Fans":
            get_event_fans(fans),

        "Fashion Audience":
            get_fashion_audience(fans),

        "WHOLENESS Fans":
            get_wholeness_fans(fans),

        "New Fans":
            get_new_fans(fans),

        "Cold Fans":
            get_cold_fans(fans),

        "High Value Fans":
            get_high_value_fans(fans),
    }


# =========================================================
# SEGMENT COUNTS
# =========================================================

def get_segment_counts(
    fans,
):

    segments = get_segments(
        fans
    )

    data = []

    for name, dataframe in segments.items():

        data.append(
            {
                "Segment": name,
                "Fans": len(dataframe),
                "Description": SEGMENTS.get(
                    name,
                    "",
                ),
            }
        )

    return pd.DataFrame(
        data
    )


# =========================================================
# GET SEGMENT
# =========================================================

def get_segment(
    fans,
    segment_name,
):

    segments = get_segments(
        fans
    )

    return segments.get(
        segment_name,
        pd.DataFrame(),
    )


# =========================================================
# BRAND SEGMENTS
# =========================================================

def get_brand_segments(
    fans,
):

    if fans.empty:

        return pd.DataFrame()

    if "favorite_brand" not in fans.columns:

        return pd.DataFrame(
            columns=[
                "Brand",
                "Fans",
            ]
        )

    brands = (
        fans["favorite_brand"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    brands = brands[
        brands != ""
    ]

    if brands.empty:

        return pd.DataFrame(
            columns=[
                "Brand",
                "Fans",
            ]
        )

    result = (
        brands
        .value_counts()
        .rename_axis("Brand")
        .reset_index(
            name="Fans"
        )
    )

    return result


# =========================================================
# SONG SEGMENTS
# =========================================================

def get_song_segments(
    fans,
):

    if fans.empty:

        return pd.DataFrame()

    if "favorite_song" not in fans.columns:

        return pd.DataFrame(
            columns=[
                "Song",
                "Fans",
            ]
        )

    songs = (
        fans["favorite_song"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    songs = songs[
        songs != ""
    ]

    if songs.empty:

        return pd.DataFrame(
            columns=[
                "Song",
                "Fans",
            ]
        )

    result = (
        songs
        .value_counts()
        .rename_axis("Song")
        .reset_index(
            name="Fans"
        )
    )

    return result


# =========================================================
# CITY SEGMENTS
# =========================================================

def get_city_segments(
    fans,
):

    if fans.empty:

        return pd.DataFrame()

    if "location" not in fans.columns:

        return pd.DataFrame(
            columns=[
                "City",
                "Fans",
            ]
        )

    cities = (
        fans["location"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    cities = cities[
        cities != ""
    ]

    if cities.empty:

        return pd.DataFrame(
            columns=[
                "City",
                "Fans",
            ]
        )

    result = (
        cities
        .value_counts()
        .rename_axis("City")
        .reset_index(
            name="Fans"
        )
    )

    return result


# =========================================================
# FAN SEGMENT LABELS
# =========================================================

def get_fan_segments(
    fan,
):

    """
    Determine all applicable segments
    for one individual fan.

    Returns a list such as:

        [
            "Superfans",
            "Potential Buyers",
            "Fashion Audience",
            "WHOLENESS Fans"
        ]
    """

    segments = []

    # -----------------------------------------------------
    # Score
    # -----------------------------------------------------

    try:

        score = float(
            fan.get(
                "engagement_score",
                0,
            )
        )

    except Exception:

        score = 0

    # -----------------------------------------------------
    # Spend
    # -----------------------------------------------------

    try:

        spend = float(
            fan.get(
                "total_spend",
                0,
            )
        )

    except Exception:

        spend = 0

    # -----------------------------------------------------
    # Superfan
    # -----------------------------------------------------

    if score >= 80:

        segments.append(
            "Superfans"
        )

    # -----------------------------------------------------
    # VIP
    # -----------------------------------------------------

    if (
        score >= 80
        and spend > 0
    ):

        segments.append(
            "VIP Fans"
        )

    # -----------------------------------------------------
    # Potential buyer
    # -----------------------------------------------------

    if (
        score >= 60
        and spend <= 0
    ):

        segments.append(
            "Potential Buyers"
        )

    # -----------------------------------------------------
    # Merch buyer
    # -----------------------------------------------------

    if spend > 0:

        segments.append(
            "Merch Buyers"
        )

    # -----------------------------------------------------
    # High value
    # -----------------------------------------------------

    if spend >= 500:

        segments.append(
            "High Value Fans"
        )

    # -----------------------------------------------------
    # Fashion
    # -----------------------------------------------------

    brand = str(
        fan.get(
            "favorite_brand",
            "",
        )
    ).strip()

    if brand:

        segments.append(
            "Fashion Audience"
        )

    # -----------------------------------------------------
    # WHOLENESS
    # -----------------------------------------------------

    favorite_song = str(
        fan.get(
            "favorite_song",
            "",
        )
    ).strip()

    if (
        favorite_song.lower()
        == "wholeness"
    ):

        segments.append(
            "WHOLENESS Fans"
        )

    # -----------------------------------------------------
    # Event interest
    # -----------------------------------------------------

    event_values = [
        fan.get(
            "event_interest",
            "",
        ),
        fan.get(
            "event_interested",
            "",
        ),
        fan.get(
            "interested_in_events",
            "",
        ),
        fan.get(
            "events",
            "",
        ),
    ]

    for value in event_values:

        if (
            "event"
            in str(value).lower()
        ):

            segments.append(
                "Event Fans"
            )

            break

    # -----------------------------------------------------
    # Cold
    # -----------------------------------------------------

    if score < 30:

        segments.append(
            "Cold Fans"
        )

    return segments


# =========================================================
# ADD SEGMENTS COLUMN
# =========================================================

def add_segment_labels(
    fans,
):

    if fans.empty:

        result = fans.copy()

        result["segments"] = []

        return result

    result = fans.copy()

    result["segments"] = result.apply(
        lambda row: ", ".join(
            get_fan_segments(
                row.to_dict()
            )
        ),
        axis=1,
    )

    return result