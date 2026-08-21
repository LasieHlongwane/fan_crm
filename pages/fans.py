import streamlit as st
import pandas as pd

from data.google_sheets import read_sheet


def show_fans():

    # =====================================================
    # PAGE HEADER
    # =====================================================

    st.title("🎵 Fans")

    st.caption(
        "Your audience database — understand who your fans are "
        "and how to build stronger relationships with them."
    )

    # =====================================================
    # LOAD DATA
    # =====================================================

    try:

        fans = read_sheet("Fans")

    except Exception as e:

        st.error(
            f"Unable to load fans: {e}"
        )

        return

    # =====================================================
    # EMPTY STATE
    # =====================================================

    if fans.empty:

        st.info(
            "No fans have been added yet."
        )

        st.write(
            "Submit a fan through your Google Form, "
            "then use the Import New Fans button "
            "on the Artist Dashboard."
        )

        return

    # =====================================================
    # NORMALIZE COLUMNS
    # =====================================================

    fans = fans.copy()

    # Support the older "fan status" column
    # if it still exists in Google Sheets.

    if (
        "fan_status" not in fans.columns
        and "fan status" in fans.columns
    ):

        fans["fan_status"] = fans[
            "fan status"
        ]

    # Make sure important columns exist.

    default_columns = {

        "name": "",

        "email": "",

        "phone": "",

        "location": "",

        "favorite_brand": "",

        "source": "",

        "fan_status": "New",

        "engagement_score": 0,

        "total_spend": 0,

    }

    for column, default in default_columns.items():

        if column not in fans.columns:

            fans[column] = default

    # =====================================================
    # CLEAN DATA
    # =====================================================

    fans["name"] = (
        fans["name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    fans["email"] = (
        fans["email"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    fans["phone"] = (
        fans["phone"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    fans["location"] = (
        fans["location"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    fans["favorite_brand"] = (
        fans["favorite_brand"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    fans["source"] = (
        fans["source"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    fans["fan_status"] = (
        fans["fan_status"]
        .fillna("New")
        .astype(str)
        .str.strip()
    )

    fans["engagement_score"] = pd.to_numeric(
        fans["engagement_score"],
        errors="coerce",
    ).fillna(0)

    fans["total_spend"] = pd.to_numeric(
        fans["total_spend"],
        errors="coerce",
    ).fillna(0)

    # =====================================================
    # SUMMARY
    # =====================================================

    total = len(fans)

    vip_count = len(
        fans[
            fans["fan_status"]
            .str.lower()
            == "vip"
        ]
    )

    buyers = len(
        fans[
            fans["total_spend"] > 0
        ]
    )

    average_score = (
        fans["engagement_score"].mean()
        if total
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Fans",
        total,
    )

    col2.metric(
        "VIP Fans",
        vip_count,
    )

    col3.metric(
        "Paying Fans",
        buyers,
    )

    col4.metric(
        "Avg Engagement",
        f"{average_score:.0f}",
    )

    st.divider()

    # =====================================================
    # SEARCH
    # =====================================================

    st.subheader("🔎 Find Fans")

    search = st.text_input(
        "Search by name, email or phone",
        placeholder="e.g. Thabo, gmail.com, 082...",
    )

    # =====================================================
    # FILTERS
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)

    # -----------------------------------------------------
    # City
    # -----------------------------------------------------

    cities = sorted(
        [
            value
            for value in fans["location"].unique()
            if value
        ]
    )

    city_options = [
        "All Cities"
    ] + cities

    selected_city = col1.selectbox(
        "📍 City",
        city_options,
    )

    # -----------------------------------------------------
    # Brand
    # -----------------------------------------------------

    brands = sorted(
        [
            value
            for value in fans["favorite_brand"].unique()
            if value
        ]
    )

    brand_options = [
        "All Brands"
    ] + brands

    selected_brand = col2.selectbox(
        "👟 Brand",
        brand_options,
    )

    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------

    statuses = sorted(
        [
            value
            for value in fans["fan_status"].unique()
            if value
        ]
    )

    status_options = [
        "All Statuses"
    ] + statuses

    selected_status = col3.selectbox(
        "⭐ Status",
        status_options,
    )

    # -----------------------------------------------------
    # Source
    # -----------------------------------------------------

    sources = sorted(
        [
            value
            for value in fans["source"].unique()
            if value
        ]
    )

    source_options = [
        "All Sources"
    ] + sources

    selected_source = col4.selectbox(
        "📱 Source",
        source_options,
    )

    # =====================================================
    # APPLY FILTERS
    # =====================================================

    filtered = fans.copy()

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    if search:

        search_value = (
            search
            .strip()
            .lower()
        )

        filtered = filtered[
            filtered["name"]
            .str.lower()
            .str.contains(
                search_value,
                na=False,
            )
            |
            filtered["email"]
            .str.lower()
            .str.contains(
                search_value,
                na=False,
            )
            |
            filtered["phone"]
            .str.lower()
            .str.contains(
                search_value,
                na=False,
            )
        ]

    # -----------------------------------------------------
    # City
    # -----------------------------------------------------

    if selected_city != "All Cities":

        filtered = filtered[
            filtered["location"]
            == selected_city
        ]

    # -----------------------------------------------------
    # Brand
    # -----------------------------------------------------

    if selected_brand != "All Brands":

        filtered = filtered[
            filtered["favorite_brand"]
            == selected_brand
        ]

    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------

    if selected_status != "All Statuses":

        filtered = filtered[
            filtered["fan_status"]
            == selected_status
        ]

    # -----------------------------------------------------
    # Source
    # -----------------------------------------------------

    if selected_source != "All Sources":

        filtered = filtered[
            filtered["source"]
            == selected_source
        ]

    # =====================================================
    # RESULTS
    # =====================================================

    st.divider()

    st.subheader(
        f"👥 Fans ({len(filtered)})"
    )

    if filtered.empty:

        st.info(
            "No fans match your filters."
        )

        return

    # =====================================================
    # FAN TABLE
    # =====================================================

    display = filtered[
        [
            "name",
            "location",
            "favorite_brand",
            "engagement_score",
            "fan_status",
            "total_spend",
        ]
    ].copy()

    display.columns = [
        "Fan",
        "City",
        "Brand",
        "Engagement",
        "Status",
        "Spend",
    ]

    display["Spend"] = display[
        "Spend"
    ].apply(
        lambda value:
        f"R{value:,.2f}"
    )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )

    # =====================================================
    # FAN PROFILE SELECTOR
    # =====================================================

    st.divider()

    st.subheader(
        "👤 View Fan Profile"
    )

    fan_options = {}

    for index, row in filtered.iterrows():

        fan_id = str(
            row.get(
                "fan_id",
                index,
            )
        )

        name = row["name"]

        if not name:

            name = "Unnamed Fan"

        fan_options[
            f"{name} — {fan_id}"
        ] = fan_id

    selected_fan_label = st.selectbox(
        "Select a fan",
        list(fan_options.keys()),
    )

    selected_fan_id = fan_options[
        selected_fan_label
    ]

    if st.button(
        "👤 Open Fan Profile",
        use_container_width=True,
    ):

        st.session_state[
            "selected_fan_id"
        ] = selected_fan_id

        st.switch_page(
            "pages/fan_profile.py"
        )