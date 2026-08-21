import pandas as pd


def safe_column(df, column):

    if column in df.columns:
        return (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    return pd.Series([""] * len(df))


# =====================================
# VIP FANS
# =====================================

def get_vip_fans(fans):

    if fans.empty:
        return pd.DataFrame()


    score = pd.to_numeric(
        fans.get(
            "engagement_score",
            0
        ),
        errors="coerce"
    ).fillna(0)


    spend = pd.to_numeric(
        fans.get(
            "total_spend",
            0
        ),
        errors="coerce"
    ).fillna(0)


    vip = fans[
        (score >= 80)
        |
        (spend > 0)
    ]


    return vip



# =====================================
# POTENTIAL BUYERS
# =====================================

def get_potential_buyers(fans):

    if fans.empty:
        return pd.DataFrame()


    buyers = fans[
        (
            safe_column(
                fans,
                "consent"
            ).str.lower()
            == "yes"
        )
        &
        (
            pd.to_numeric(
                fans.get(
                    "total_spend",
                    0
                ),
                errors="coerce"
            )
            .fillna(0)
            == 0
        )
    ]


    return buyers



# =====================================
# BRAND AUDIENCE
# =====================================

def get_brand_audience(
        fans,
        brand
):

    if fans.empty:
        return pd.DataFrame()


    brands = safe_column(
        fans,
        "favorite_brand"
    )


    return fans[
        brands.str.lower()
        ==
        brand.lower()
    ]



# =====================================
# NEW FANS
# =====================================

def get_new_fans(fans):

    if fans.empty:
        return pd.DataFrame()


    if "created_at" not in fans.columns:
        return pd.DataFrame()


    data = fans.copy()


    data["created_at"] = pd.to_datetime(
        data["created_at"],
        errors="coerce"
    )


    return data[
        data["created_at"]
        >=
        (
            pd.Timestamp.now()
            -
            pd.Timedelta(days=30)
        )
    ]