import pandas as pd


# ---------------------------------------------------------
# Clean dataframe
# ---------------------------------------------------------

def clean_dataframe(df):

    if df is None:
        return pd.DataFrame()

    if df.empty:
        return df

    df = df.copy()

    df.columns = [
        str(column).strip().lower()
        for column in df.columns
    ]

    return df


# ---------------------------------------------------------
# Total fans
# ---------------------------------------------------------

def total_fans(fans):

    if fans.empty:
        return 0

    return len(fans)


# ---------------------------------------------------------
# New fans this month
# ---------------------------------------------------------

def new_fans_this_month(fans):

    if fans.empty or "timestamp" not in fans.columns:
        return 0

    df = fans.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    now = pd.Timestamp.now()

    return int(
        (
            (df["timestamp"].dt.month == now.month)
            &
            (df["timestamp"].dt.year == now.year)
        ).sum()
    )


# ---------------------------------------------------------
# Consent count
# ---------------------------------------------------------

def consented_fans(fans):

    if fans.empty or "consent" not in fans.columns:
        return 0

    values = (
        fans["consent"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    return int(
        values.isin(
            ["yes", "true", "1", "y"]
        ).sum()
    )


# ---------------------------------------------------------
# Fans who want events
# ---------------------------------------------------------

def event_interested_fans(fans):

    if fans.empty or "wants_events" not in fans.columns:
        return 0

    values = (
        fans["wants_events"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    return int(
        values.isin(
            ["yes", "true", "1", "y"]
        ).sum()
    )


# ---------------------------------------------------------
# Fans interested in merchandise
# ---------------------------------------------------------

def merch_interested_fans(fans):

    if fans.empty or "wants_merch" not in fans.columns:
        return 0

    values = (
        fans["wants_merch"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    return int(
        values.isin(
            ["yes", "true", "1", "y"]
        ).sum()
    )


# ---------------------------------------------------------
# Top cities
# ---------------------------------------------------------

def top_cities(fans, limit=10):

    if fans.empty or "city" not in fans.columns:
        return pd.Series(dtype=int)

    return (
        fans["city"]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
        .head(limit)
    )


# ---------------------------------------------------------
# Top songs
# ---------------------------------------------------------

def top_songs(fans, limit=10):

    if fans.empty or "favorite_song" not in fans.columns:
        return pd.Series(dtype=int)

    return (
        fans["favorite_song"]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
        .head(limit)
    )


# ---------------------------------------------------------
# Interests
# ---------------------------------------------------------

def interest_counts(fans):

    if fans.empty or "interests" not in fans.columns:
        return pd.Series(dtype=int)

    interests = []

    for value in fans["interests"].dropna():

        parts = str(value).split(",")

        for part in parts:

            part = part.strip()

            if part:
                interests.append(part)

    if not interests:
        return pd.Series(dtype=int)

    return (
        pd.Series(interests)
        .value_counts()
    )


# ---------------------------------------------------------
# Revenue
# ---------------------------------------------------------

def total_revenue(purchases):

    if purchases.empty or "amount" not in purchases.columns:
        return 0.0

    amounts = pd.to_numeric(
        purchases["amount"],
        errors="coerce",
    ).fillna(0)

    return float(amounts.sum())


# ---------------------------------------------------------
# Revenue by category
# ---------------------------------------------------------

def revenue_by_category(purchases):

    if purchases.empty:
        return pd.Series(dtype=float)

    if "category" not in purchases.columns:
        return pd.Series(dtype=float)

    purchases = purchases.copy()

    purchases["amount"] = pd.to_numeric(
        purchases["amount"],
        errors="coerce",
    ).fillna(0)

    return (
        purchases.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )


# ---------------------------------------------------------
# Average fan value
# ---------------------------------------------------------

def average_fan_value(fans, purchases):

    if fans.empty:
        return 0.0

    if purchases.empty:
        return 0.0

    revenue = total_revenue(purchases)

    return revenue / len(fans)


# ---------------------------------------------------------
# Purchases per fan
# ---------------------------------------------------------

def purchasing_fans(purchases):

    if purchases.empty or "fan_id" not in purchases.columns:
        return 0

    return purchases["fan_id"].nunique()


# ---------------------------------------------------------
# Fan engagement score
# ---------------------------------------------------------

def engagement_score(
    fan_id,
    interactions,
    purchases,
):

    score = 0

    if not interactions.empty:

        fan_interactions = interactions[
            interactions["fan_id"].astype(str)
            == str(fan_id)
        ]

        score += len(fan_interactions) * 2

    if not purchases.empty:

        fan_purchases = purchases[
            purchases["fan_id"].astype(str)
            == str(fan_id)
        ]

        score += len(fan_purchases) * 5

    return score


# ---------------------------------------------------------
# Engagement level
# ---------------------------------------------------------

def engagement_level(score):

    if score >= 20:
        return "🔥 Superfan"

    if score >= 10:
        return "⭐ Highly Engaged"

    if score >= 5:
        return "👍 Engaged"

    return "👤 Casual"