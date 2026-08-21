import streamlit as st
import pandas as pd

from fan_importer import import_all_fans

from data.google_sheets import read_sheet

from analytics.metrics import (
    total_fans,
    new_fans_this_month,
    consented_fans,
    event_interested_fans,
    merch_interested_fans,
    total_revenue,
    average_fan_value,
    top_cities,
)


def show_dashboard():

    # =====================================================
    # PAGE HEADER
    # =====================================================

    st.title("🎵 Artist Dashboard")

    st.caption(
        "Turn your audience into relationships — "
        "and relationships into revenue."
    )

    # =====================================================
    # FAN IMPORT
    # =====================================================

    with st.expander(
        "👥 Fan Import",
        expanded=False,
    ):

        st.caption(
            "Import new fans from your Google Form "
            "into the CRM."
        )

        if st.button(
            "🔄 Import New Fans",
            use_container_width=True,
        ):

            try:

                with st.spinner(
                    "Importing fans from Google Forms..."
                ):

                    result = import_all_fans()

                imported = result.get(
                    "imported",
                    0,
                )

                duplicates = result.get(
                    "duplicates",
                    0,
                )

                errors = result.get(
                    "errors",
                    0,
                )

                if imported > 0:

                    st.success(
                        f"Import complete — "
                        f"{imported} new fan(s) imported."
                    )

                else:

                    st.info(
                        "No new fans were imported."
                    )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "New Fans",
                    imported,
                )

                col2.metric(
                    "Duplicates",
                    duplicates,
                )

                col3.metric(
                    "Errors",
                    errors,
                )

                messages = result.get(
                    "messages",
                    [],
                )

                if messages:

                    with st.expander(
                        "View import details"
                    ):

                        for message in messages:

                            st.write(
                                f"• {message}"
                            )

                st.cache_data.clear()

                st.rerun()

            except Exception as e:

                st.error(
                    f"Fan import failed: {e}"
                )

    # =====================================================
    # LOAD DATA
    # =====================================================

    try:

        fans = read_sheet("Fans")

        purchases = read_sheet("Purchases")

        interactions = read_sheet(
            "Interactions"
        )

        events = read_sheet(
            "Events"
        )

    except Exception as e:

        st.error(
            f"Unable to load Google Sheets: {e}"
        )

        return

    # =====================================================
    # AUDIENCE OVERVIEW
    # =====================================================

    st.subheader(
        "👥 Audience Overview"
    )

    total_fans_value = total_fans(
        fans
    )

    new_fans_value = new_fans_this_month(
        fans
    )

    consented_value = consented_fans(
        fans
    )

    potential_buyers = merch_interested_fans(
        fans
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Fans",
        f"{total_fans_value:,}",
    )

    col2.metric(
        "New This Month",
        f"{new_fans_value:,}",
    )

    col3.metric(
        "Consented Fans",
        f"{consented_value:,}",
    )

    col4.metric(
        "Potential Buyers",
        f"{potential_buyers:,}",
    )

    # =====================================================
    # AUDIENCE SUMMARY TABLE
    # =====================================================

    st.markdown(
        "### 📋 Audience Summary"
    )

    audience_summary = pd.DataFrame(
        [
            {
                "Metric": "Total Fans",
                "Value": total_fans_value,
            },
            {
                "Metric": "New Fans This Month",
                "Value": new_fans_value,
            },
            {
                "Metric": "Consented Fans",
                "Value": consented_value,
            },
            {
                "Metric": "Potential Buyers",
                "Value": potential_buyers,
            },
            {
                "Metric": "Event Interested",
                "Value": event_interested_fans(fans),
            },
            {
                "Metric": "Interactions",
                "Value": len(interactions),
            },
            {
                "Metric": "Paying Fans",
                "Value": (
                    purchases["fan_id"]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .replace("", pd.NA)
                    .dropna()
                    .nunique()
                    if (
                        not purchases.empty
                        and "fan_id" in purchases.columns
                    )
                    else 0
                ),
            },
        ]
    )

    st.dataframe(
        audience_summary,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # =====================================================
    # REVENUE OVERVIEW
    # =====================================================

    st.subheader(
        "💰 Revenue Overview"
    )

    revenue = total_revenue(
        purchases
    )

    fan_value = average_fan_value(
        fans,
        purchases,
    )

    event_interested = event_interested_fans(
        fans
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Revenue",
        f"R{revenue:,.2f}",
    )

    col2.metric(
        "Average Fan Value",
        f"R{fan_value:,.2f}",
    )

    col3.metric(
        "Event Interested",
        event_interested,
    )

    # -----------------------------------------------------
    # Revenue table
    # -----------------------------------------------------

    revenue_summary = pd.DataFrame(
        [
            {
                "Revenue Metric": "Total Revenue",
                "Amount": f"R{revenue:,.2f}",
            },
            {
                "Revenue Metric": "Average Fan Value",
                "Amount": f"R{fan_value:,.2f}",
            },
            {
                "Revenue Metric": "Paying Fans",
                "Amount": (
                    f"{purchases['fan_id'].nunique():,}"
                    if (
                        not purchases.empty
                        and "fan_id" in purchases.columns
                    )
                    else "0"
                ),
            },
        ]
    )

    st.dataframe(
        revenue_summary,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # =====================================================
    # AUDIENCE INSIGHTS
    # =====================================================

    st.subheader(
        "🎯 Audience Insights"
    )

    # -----------------------------------------------------
    # MOST POPULAR SONG
    # -----------------------------------------------------

    popular_song = "—"

    if (
        not fans.empty
        and "favorite_song" in fans.columns
    ):

        songs = (
            fans["favorite_song"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        songs = songs[
            songs != ""
        ]

        if not songs.empty:

            popular_song = (
                songs
                .value_counts()
                .idxmax()
            )

    # -----------------------------------------------------
    # TOP CITY
    # -----------------------------------------------------

    top_city = "—"

    if (
        not fans.empty
        and "location" in fans.columns
    ):

        cities = (
            fans["location"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        cities = cities[
            cities != ""
        ]

        if not cities.empty:

            top_city = (
                cities
                .value_counts()
                .idxmax()
            )

    # -----------------------------------------------------
    # FASTEST GROWING CITY
    # -----------------------------------------------------

    fastest_city = "—"

    if (
        not fans.empty
        and "location" in fans.columns
        and "created_at" in fans.columns
    ):

        temp = fans.copy()

        temp["created_at"] = pd.to_datetime(
            temp["created_at"],
            errors="coerce",
        )

        temp = temp.dropna(
            subset=["created_at"]
        )

        if not temp.empty:

            latest_date = temp[
                "created_at"
            ].max()

            recent = temp[
                temp["created_at"]
                >= latest_date
                - pd.Timedelta(days=30)
            ]

            location_counts = (
                recent["location"]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            location_counts = (
                location_counts[
                    location_counts != ""
                ]
            )

            if not location_counts.empty:

                fastest_city = (
                    location_counts
                    .value_counts()
                    .idxmax()
                )

    # -----------------------------------------------------
    # FAVORITE BRAND
    # -----------------------------------------------------

    favorite_brand = "—"

    if (
        not fans.empty
        and "favorite_brand" in fans.columns
    ):

        brands = (
            fans["favorite_brand"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        brands = brands[
            brands != ""
        ]

        if not brands.empty:

            favorite_brand = (
                brands
                .value_counts()
                .idxmax()
            )

    # =====================================================
    # INSIGHTS TABLE
    # =====================================================

    insights_table = pd.DataFrame(
        [
            {
                "Insight": "🎵 Most Popular Song",
                "Result": popular_song,
            },
            {
                "Insight": "📍 Top City",
                "Result": top_city,
            },
            {
                "Insight": "📈 Fastest Growing Audience",
                "Result": fastest_city,
            },
            {
                "Insight": "👟 Favorite Brand",
                "Result": favorite_brand,
            },
        ]
    )

    st.dataframe(
        insights_table,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # =====================================================
    # BRAND PREFERENCES
    # =====================================================

    st.subheader(
        "👟 Audience Brand Preferences"
    )

    if (
        not fans.empty
        and "favorite_brand" in fans.columns
    ):

        brands = (
            fans["favorite_brand"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        brands = brands[
            brands != ""
        ]

        if not brands.empty:

            brand_counts = (
                brands
                .value_counts()
                .reset_index()
            )

            brand_counts.columns = [
                "Brand",
                "Fans",
            ]

            total_brand_fans = (
                brand_counts["Fans"]
                .sum()
            )

            brand_counts[
                "% of Audience"
            ] = (
                brand_counts["Fans"]
                / total_brand_fans
                * 100
            ).round(1)

            brand_counts.insert(
                0,
                "Rank",
                range(
                    1,
                    len(brand_counts) + 1,
                ),
            )

            brand_counts[
                "% of Audience"
            ] = (
                brand_counts[
                    "% of Audience"
                ].astype(str)
                + "%"
            )

            st.dataframe(
                brand_counts,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No favorite brand data available yet."
            )

    else:

        st.info(
            "The Fans sheet needs a "
            "'favorite_brand' column."
        )

    st.divider()

    # =====================================================
    # FAN LOCATIONS
    # =====================================================

    st.subheader(
        "📍 Audience Location Breakdown"
    )

    if (
        not fans.empty
        and "location" in fans.columns
    ):

        location_data = (
            fans["location"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        location_data = location_data[
            location_data != ""
        ]

        if not location_data.empty:

            location_table = (
                location_data
                .value_counts()
                .reset_index()
            )

            location_table.columns = [
                "City",
                "Fans",
            ]

            total_location_fans = (
                location_table["Fans"].sum()
            )

            location_table[
                "% of Audience"
            ] = (
                location_table["Fans"]
                / total_location_fans
                * 100
            ).round(1)

            location_table.insert(
                0,
                "Rank",
                range(
                    1,
                    len(location_table) + 1,
                ),
            )

            location_table[
                "% of Audience"
            ] = (
                location_table[
                    "% of Audience"
                ].astype(str)
                + "%"
            )

            st.dataframe(
                location_table,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No audience location data available."
            )

    else:

        st.info(
            "No location column found in Fans sheet."
        )

    st.divider()

    # =====================================================
    # MUSIC PREFERENCES
    # =====================================================

    st.subheader(
        "🎵 Music Preferences"
    )

    if (
        not fans.empty
        and "favorite_song" in fans.columns
    ):

        songs = (
            fans["favorite_song"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        songs = songs[
            songs != ""
        ]

        if not songs.empty:

            song_table = (
                songs
                .value_counts()
                .reset_index()
            )

            song_table.columns = [
                "Song",
                "Fans",
            ]

            total_song_fans = (
                song_table["Fans"].sum()
            )

            song_table[
                "% of Audience"
            ] = (
                song_table["Fans"]
                / total_song_fans
                * 100
            ).round(1)

            song_table.insert(
                0,
                "Rank",
                range(
                    1,
                    len(song_table) + 1,
                ),
            )

            song_table[
                "% of Audience"
            ] = (
                song_table[
                    "% of Audience"
                ].astype(str)
                + "%"
            )

            st.dataframe(
                song_table,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No favorite song data available."
            )

    else:

        st.info(
            "No favorite_song column found."
        )

    st.divider()

    # =====================================================
    # AUDIENCE SOURCES
    # =====================================================

    st.subheader(
        "📣 How Fans Discover You"
    )

    if (
        not fans.empty
        and "source" in fans.columns
    ):

        sources = (
            fans["source"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        sources = sources[
            sources != ""
        ]

        if not sources.empty:

            source_table = (
                sources
                .value_counts()
                .reset_index()
            )

            source_table.columns = [
                "Discovery Channel",
                "Fans",
            ]

            total_source_fans = (
                source_table["Fans"].sum()
            )

            source_table[
                "% of Audience"
            ] = (
                source_table["Fans"]
                / total_source_fans
                * 100
            ).round(1)

            source_table.insert(
                0,
                "Rank",
                range(
                    1,
                    len(source_table) + 1,
                ),
            )

            source_table[
                "% of Audience"
            ] = (
                source_table[
                    "% of Audience"
                ].astype(str)
                + "%"
            )

            st.dataframe(
                source_table,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No discovery source data available."
            )

    else:

        st.info(
            "No source column found in Fans sheet."
        )

    st.divider()

    # =====================================================
    # FAN STATUS
    # =====================================================

    st.subheader(
        "⭐ Fan Status Breakdown"
    )

    status_column = None

    if "fan status" in fans.columns:
        status_column = "fan status"

    elif "fan_status" in fans.columns:
        status_column = "fan_status"

    if (
        not fans.empty
        and status_column
    ):

        statuses = (
            fans[status_column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        statuses = statuses[
            statuses != ""
        ]

        if not statuses.empty:

            status_table = (
                statuses
                .value_counts()
                .reset_index()
            )

            status_table.columns = [
                "Fan Status",
                "Fans",
            ]

            total_status_fans = (
                status_table["Fans"].sum()
            )

            status_table[
                "% of Audience"
            ] = (
                status_table["Fans"]
                / total_status_fans
                * 100
            ).round(1)

            status_table.insert(
                0,
                "Rank",
                range(
                    1,
                    len(status_table) + 1,
                ),
            )

            status_table[
                "% of Audience"
            ] = (
                status_table[
                    "% of Audience"
                ].astype(str)
                + "%"
            )

            st.dataframe(
                status_table,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No fan status data available."
            )

    else:

        st.info(
            "No fan status column found."
        )

    st.divider()

    # =====================================================
    # UPCOMING EVENTS
    # =====================================================

    st.subheader(
        "📅 Upcoming Events"
    )

    if events.empty:

        st.info(
            "No upcoming events recorded yet."
        )

    else:

        event_display = events.copy()

        preferred_columns = [
            "event_name",
            "name",
            "date",
            "event_date",
            "time",
            "event_time",
            "location",
            "venue",
            "category",
        ]

        available_columns = [
            column
            for column in preferred_columns
            if column in event_display.columns
        ]

        if available_columns:

            st.dataframe(
                event_display[
                    available_columns
                ],
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.dataframe(
                event_display,
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    # =====================================================
    # RECENT PURCHASES
    # =====================================================

    st.subheader(
        "🛍 Recent Fan Purchases"
    )

    if purchases.empty:

        st.info(
            "No purchases recorded yet."
        )

    else:

        purchase_display = purchases.copy()

        st.dataframe(
            purchase_display,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # =====================================================
    # CRM EXPLANATION
    # =====================================================

    st.subheader(
        "💡 What Your CRM Is Telling You"
    )

    explanation_table = pd.DataFrame(
        [
            {
                "Business Question": "Who are my fans?",
                "CRM Answer": (
                    "Audience size, location, age, "
                    "status and consent."
                ),
            },
            {
                "Business Question": "What do they like?",
                "CRM Answer": (
                    "Favorite songs, artists and brands."
                ),
            },
            {
                "Business Question": "Where do they come from?",
                "CRM Answer": (
                    "TikTok, Instagram, concerts, "
                    "WhatsApp and other discovery channels."
                ),
            },
            {
                "Business Question": "Who might buy?",
                "CRM Answer": (
                    "Engaged fans, merchandise-interested "
                    "fans and previous purchasers."
                ),
            },
            {
                "Business Question": "What makes money?",
                "CRM Answer": (
                    "Purchases, revenue, fan value "
                    "and campaign attribution."
                ),
            },
            {
                "Business Question": "Where should I focus?",
                "CRM Answer": (
                    "Top cities, brands, songs, channels "
                    "and high-value fan segments."
                ),
            },
        ]
    )

    st.dataframe(
        explanation_table,
        use_container_width=True,
        hide_index=True,
    )