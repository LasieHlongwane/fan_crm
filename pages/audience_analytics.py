# pages/analytics.py

import streamlit as st
import pandas as pd

from data.google_sheets import read_sheet

from audience_segmentation import (
    get_segments,
    get_brand_segments,
    get_song_segments,
    get_city_segments,
)


# =========================================================
# NAVIGATION HELPER
# =========================================================

def go_to_audience_actions(
    segment_name,
    action="View Audience",
):

    st.session_state["selected_segment"] = segment_name
    st.session_state["audience_action"] = action

    # Tell app.py which page should be opened
    st.session_state["navigation_target"] = "Audience Actions"

    st.rerun()


# =========================================================
# PAGE
# =========================================================

def show_analytics():

    st.title("📊 Audience Analytics")

    st.caption(
        "Turn fan data into decisions, audiences and actions."
    )

    # =====================================================
    # LOAD FANS
    # =====================================================

    try:

        fans = read_sheet("Fans")

    except Exception as error:

        st.error(
            f"Unable to load fan data: {error}"
        )

        return

    if fans.empty:

        st.info(
            "Analytics will appear once fans start joining."
        )

        return

    # =====================================================
    # SEGMENTS
    # =====================================================

    segments = get_segments(fans)

    # =====================================================
    # AUDIENCE OVERVIEW
    # =====================================================

    st.subheader("👥 Audience Overview")

    total_fans = len(fans)

    if "engagement_score" in fans.columns:

        engagement = pd.to_numeric(
            fans["engagement_score"],
            errors="coerce",
        ).fillna(0)

        avg_engagement = engagement.mean()

    else:

        avg_engagement = 0

    if "total_spend" in fans.columns:

        spend = pd.to_numeric(
            fans["total_spend"],
            errors="coerce",
        ).fillna(0)

        buyers = int(
            (spend > 0).sum()
        )

        fan_revenue = float(
            spend.sum()
        )

    else:

        buyers = 0
        fan_revenue = 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Fans",
            total_fans,
        )

    with col2:

        st.metric(
            "Avg Engagement",
            f"{avg_engagement:.1f}",
        )

    with col3:

        st.metric(
            "Buyers",
            buyers,
        )

    with col4:

        st.metric(
            "Fan Revenue",
            f"R{fan_revenue:,.2f}",
        )

    st.divider()

    # =====================================================
    # AUDIENCE INTELLIGENCE
    # =====================================================

    st.subheader("🧠 Audience Intelligence")

    st.caption(
        "Identify audiences that deserve attention right now."
    )

    intelligence = [

        (
            "🔥",
            "Superfans",
            "Highly engaged fans who are strong candidates for exclusive access, early releases and special experiences.",
        ),

        (
            "💰",
            "Potential Buyers",
            "Highly engaged fans who have not purchased yet. This is one of your strongest conversion audiences.",
        ),

        (
            "⭐",
            "VIP Fans",
            "Highly engaged fans who have already spent money. Protect and reward this audience.",
        ),

        (
            "❤️",
            "WHOLENESS Fans",
            "Fans whose favourite song is WHOLENESS.",
        ),

        (
            "🎟️",
            "Event Fans",
            "Fans interested in events and live experiences.",
        ),

        (
            "👕",
            "Fashion Audience",
            "Fans who have identified a favourite brand.",
        ),

        (
            "🆕",
            "New Fans",
            "Fans who recently joined.",
        ),

        (
            "😴",
            "Cold Fans",
            "Fans with low engagement who may need re-engagement.",
        ),
    ]

    for icon, segment_name, description in intelligence:

        audience = segments.get(
            segment_name,
            pd.DataFrame(),
        )

        count = len(audience)

        col1, col2, col3, col4 = st.columns(
            [0.5, 2.2, 1, 3.3]
        )

        with col1:

            st.write(icon)

        with col2:

            st.markdown(
                f"**{segment_name}**"
            )

        with col3:

            st.metric(
                "Fans",
                count,
            )

        with col4:

            st.caption(
                description
            )

        button_col1, button_col2, button_col3 = st.columns(
            [1, 1, 1]
        )

        with button_col1:

            if st.button(
                "👥 View Audience",
                key=f"view_{segment_name}",
                use_container_width=True,
            ):

                go_to_audience_actions(
                    segment_name,
                    "View Audience",
                )

        with button_col2:

            if st.button(
                "🎯 Take Action",
                key=f"action_{segment_name}",
                use_container_width=True,
            ):

                go_to_audience_actions(
                    segment_name,
                    "Take Action",
                )

        with button_col3:

            if st.button(
                "📢 Create Campaign",
                key=f"campaign_{segment_name}",
                use_container_width=True,
            ):

                go_to_audience_actions(
                    segment_name,
                    "Create Campaign",
                )

        st.divider()

    # =====================================================
    # HIGH VALUE AUDIENCE
    # =====================================================

    st.subheader("💎 High-Value Audience")

    high_value = segments.get(
        "High Value Fans",
        pd.DataFrame(),
    )

    high_value_count = len(
        high_value
    )

    audience_share = (
        high_value_count
        / total_fans
        * 100
        if total_fans > 0
        else 0
    )

    high_value_spend = 0

    if not high_value.empty:

        if "total_spend" in high_value.columns:

            high_value_spend = pd.to_numeric(
                high_value["total_spend"],
                errors="coerce",
            ).fillna(0).sum()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "High Value Fans",
            high_value_count,
        )

    with col2:

        st.metric(
            "Audience Share",
            f"{audience_share:.1f}%",
        )

    with col3:

        st.metric(
            "High-Value Revenue",
            f"R{high_value_spend:,.2f}",
        )

    st.info(
        "Your high-value fans are an important retention audience. "
        "Consider exclusive experiences, early access and personalised offers."
    )

    # -----------------------------------------------------
    # HIGH VALUE ACTION
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "👥 View High-Value Fans",
            use_container_width=True,
        ):

            go_to_audience_actions(
                "High Value Fans",
                "View Audience",
            )

    with col2:

        if st.button(
            "🎯 Take Action",
            key="high_value_action",
            use_container_width=True,
        ):

            go_to_audience_actions(
                "High Value Fans",
                "Take Action",
            )

    with col3:

        if st.button(
            "📢 Create Campaign",
            key="high_value_campaign",
            use_container_width=True,
        ):

            go_to_audience_actions(
                "High Value Fans",
                "Create Campaign",
            )

    # =====================================================
    # RECOMMENDED ACTIONS
    # =====================================================

    st.subheader("🎯 Recommended Actions")

    superfans_count = len(
        segments.get(
            "Superfans",
            pd.DataFrame(),
        )
    )

    new_fans_count = len(
        segments.get(
            "New Fans",
            pd.DataFrame(),
        )
    )

    potential_buyers_count = len(
        segments.get(
            "Potential Buyers",
            pd.DataFrame(),
        )
    )

    if superfans_count > 0:

        st.success(
            f"🔥 You have {superfans_count} superfans. "
            "Consider giving them early access or exclusive content."
        )

    if new_fans_count > 0:

        st.info(
            f"🆕 You have {new_fans_count} new fans. "
            "Consider welcoming them before making a sales offer."
        )

    if potential_buyers_count > 0:

        st.warning(
            f"💰 You have {potential_buyers_count} potential buyers. "
            "Consider a targeted offer or product campaign."
        )

    # =====================================================
    # ENGAGEMENT DISTRIBUTION
    # =====================================================

    st.divider()

    st.subheader("🔥 Engagement Distribution")

    if "engagement_score" in fans.columns:

        scores = pd.to_numeric(
            fans["engagement_score"],
            errors="coerce",
        ).fillna(0)

        engagement_distribution = pd.DataFrame(
            {
                "Engagement Level": [
                    "Cold",
                    "Regular",
                    "Highly Engaged",
                    "Superfan",
                ],
                "Score Range": [
                    "0–29",
                    "30–59",
                    "60–79",
                    "80–100",
                ],
                "Fans": [
                    int(
                        (scores < 30).sum()
                    ),
                    int(
                        (
                            (scores >= 30)
                            & (scores < 60)
                        ).sum()
                    ),
                    int(
                        (
                            (scores >= 60)
                            & (scores < 80)
                        ).sum()
                    ),
                    int(
                        (scores >= 80).sum()
                    ),
                ],
            }
        )

        st.dataframe(
            engagement_distribution,
            use_container_width=True,
            hide_index=True,
        )

    # =====================================================
    # CITIES
    # =====================================================

    st.subheader("📍 Where Are Your Fans?")

    cities = get_city_segments(
        fans
    )

    if not cities.empty:

        cities = cities.copy()

        cities.insert(
            0,
            "Rank",
            range(
                1,
                len(cities) + 1,
            ),
        )

        st.dataframe(
            cities,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No location data available yet."
        )

    # =====================================================
    # SONGS
    # =====================================================

    st.subheader("🎵 Favourite Songs")

    songs = get_song_segments(
        fans
    )

    if not songs.empty:

        songs = songs.copy()

        songs.insert(
            0,
            "Rank",
            range(
                1,
                len(songs) + 1,
            ),
        )

        st.dataframe(
            songs,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No favourite song data available yet."
        )

    # =====================================================
    # BRANDS
    # =====================================================

    st.subheader("👕 Favourite Brands")

    brands = get_brand_segments(
        fans
    )

    if not brands.empty:

        brands = brands.copy()

        brands.insert(
            0,
            "Rank",
            range(
                1,
                len(brands) + 1,
            ),
        )

        st.dataframe(
            brands,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No favourite brand data available yet."
        )

    # =====================================================
    # FOOTER
    # =====================================================

    st.divider()

    st.caption(
        "🔎 Audience analytics are generated from your current Fans data."
    )