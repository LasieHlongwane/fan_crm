# pages/audience_actions.py

import streamlit as st
import pandas as pd

from data.google_sheets import read_sheet
from audience_segmentation import (
    get_segments,
    get_segment,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

PAGE_TITLE = "🎯 Audience Actions"


# =========================================================
# SEGMENT DESCRIPTIONS
# =========================================================

SEGMENT_DESCRIPTIONS = {

    "VIP Fans":
        "Highly engaged fans who have already purchased. Protect and reward this audience.",

    "Superfans":
        "Very highly engaged fans. Strong candidates for exclusive access, early releases and special experiences.",

    "Potential Buyers":
        "Highly engaged fans who have not purchased yet. This is a strong conversion audience.",

    "Merch Buyers":
        "Fans who have already purchased. Use this audience for retention and repeat purchases.",

    "Event Fans":
        "Fans interested in events. Useful for event announcements, ticket campaigns and invitations.",

    "Fashion Audience":
        "Fans with a favourite brand. Useful for partnership and collaboration opportunities.",

    "WHOLENESS Fans":
        "Fans whose favourite song is WHOLENESS. They may strongly identify with your deeper brand message.",

    "New Fans":
        "Recently joined fans. Give them a reason to become active before they become passive followers.",

    "Cold Fans":
        "Fans with low engagement. Focus on re-engagement rather than immediately selling.",

    "High Value Fans":
        "Fans with significant lifetime spend. Focus on retention, exclusivity and personalised offers.",
}


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
# LOAD FANS
# =========================================================

def load_fans():

    try:

        fans = read_sheet("Fans")

        if fans is None:
            return pd.DataFrame()

        return fans

    except Exception as error:

        st.error(
            f"Unable to load fan data: {error}"
        )

        return pd.DataFrame()


# =========================================================
# FORMAT FAN TABLE
# =========================================================

def prepare_fan_table(fans):

    if fans.empty:
        return fans

    data = fans.copy()

    # -----------------------------------------------------
    # Add useful display columns if available
    # -----------------------------------------------------

    if "engagement_score" in data.columns:

        data["engagement_score"] = pd.to_numeric(
            data["engagement_score"],
            errors="coerce",
        ).fillna(0)

    if "total_spend" in data.columns:

        data["total_spend"] = pd.to_numeric(
            data["total_spend"],
            errors="coerce",
        ).fillna(0)

    # -----------------------------------------------------
    # Select useful columns
    # -----------------------------------------------------

    preferred_columns = [

        "fan_id",

        "name",

        "first_name",

        "last_name",

        "email",

        "phone",

        "whatsapp_number",

        "location",

        "favorite_song",

        "favorite_brand",

        "engagement_score",

        "total_spend",

        "consent",

        "created_at",
    ]

    available = [
        column
        for column in preferred_columns
        if column in data.columns
    ]

    if available:

        return data[available]

    return data


# =========================================================
# FAN NAME
# =========================================================

def get_fan_name(row):

    name = str(
        row.get(
            "name",
            "",
        )
    ).strip()

    if name:
        return name

    first_name = str(
        row.get(
            "first_name",
            "",
        )
    ).strip()

    last_name = str(
        row.get(
            "last_name",
            "",
        )
    ).strip()

    full_name = (
        f"{first_name} {last_name}"
    ).strip()

    if full_name:
        return full_name

    return "Fan"


# =========================================================
# AUDIENCE SUMMARY
# =========================================================

def audience_summary(
    audience,
):

    total = len(audience)

    if total == 0:

        return {
            "fans": 0,
            "engagement": 0,
            "spend": 0,
        }

    if "engagement_score" in audience.columns:

        engagement = pd.to_numeric(
            audience["engagement_score"],
            errors="coerce",
        ).fillna(0).mean()

    else:

        engagement = 0

    if "total_spend" in audience.columns:

        spend = pd.to_numeric(
            audience["total_spend"],
            errors="coerce",
        ).fillna(0).sum()

    else:

        spend = 0

    return {

        "fans":
            total,

        "engagement":
            engagement,

        "spend":
            spend,
    }


# =========================================================
# ACTION RECOMMENDATIONS
# =========================================================

def get_recommended_action(
    segment_name,
):

    recommendations = {

        "VIP Fans":
            "Reward this audience with exclusive access, VIP experiences, private content or early releases.",

        "Superfans":
            "Give these fans early access, exclusive content or opportunities to become your strongest advocates.",

        "Potential Buyers":
            "Create a low-friction offer such as merchandise, a digital product, exclusive content or event access.",

        "Merch Buyers":
            "Focus on repeat purchases, new merchandise and loyalty offers.",

        "Event Fans":
            "Send event announcements, ticket offers and reminders.",

        "Fashion Audience":
            "Explore brand collaborations, sponsored campaigns and fashion-related content.",

        "WHOLENESS Fans":
            "Create content and offers connected to the WHOLENESS message and your deeper artistic identity.",

        "New Fans":
            "Welcome them first. Introduce your story, music and community before making a strong sales offer.",

        "Cold Fans":
            "Run a re-engagement campaign with music, storytelling or community content before attempting a sale.",

        "High Value Fans":
            "Prioritise retention. Offer personalised experiences, early access and premium opportunities.",
    }

    return recommendations.get(
        segment_name,
        "Create a campaign specifically designed for this audience.",
    )


# =========================================================
# CREATE CAMPAIGN NAVIGATION
# =========================================================

def go_to_campaign_builder(
    segment_name,
):

    st.session_state[
        "campaign_audience_segment"
    ] = segment_name

    st.session_state[
        "selected_audience_segment"
    ] = segment_name

    st.session_state[
        "open_campaign_builder"
    ] = True

    st.info(
        "Audience selected. Open Campaign Builder from the sidebar to create the campaign."
    )


# =========================================================
# SHOW AUDIENCE
# =========================================================

def show_audience_table(
    audience,
):

    if audience.empty:

        st.info(
            "There are currently no fans in this audience."
        )

        return

    display_data = prepare_fan_table(
        audience
    )

    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# TAKE ACTION
# =========================================================

def show_take_action(
    audience,
    segment_name,
):

    st.subheader(
        "⚡ Take Action"
    )

    st.write(
        get_recommended_action(
            segment_name
        )
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "💬 WhatsApp Audience",
            use_container_width=True,
            key=f"whatsapp_{segment_name}",
        ):

            st.session_state[
                "action_audience"
            ] = segment_name

            st.success(
                f"{segment_name} selected for WhatsApp action."
            )

    with col2:

        if st.button(
            "📧 Email Audience",
            use_container_width=True,
            key=f"email_{segment_name}",
        ):

            st.session_state[
                "action_audience"
            ] = segment_name

            st.success(
                f"{segment_name} selected for email action."
            )

    with col3:

        if st.button(
            "📱 SMS Audience",
            use_container_width=True,
            key=f"sms_{segment_name}",
        ):

            st.session_state[
                "action_audience"
            ] = segment_name

            st.success(
                f"{segment_name} selected for SMS action."
            )


# =========================================================
# CREATE CAMPAIGN
# =========================================================

def show_create_campaign(
    audience,
    segment_name,
):

    st.subheader(
        "🚀 Create Campaign"
    )

    st.write(
        f"Build a campaign specifically for **{segment_name}**."
    )

    st.metric(
        "Audience Size",
        len(audience),
    )

    if st.button(
        "🚀 Create Campaign for This Audience",
        type="primary",
        use_container_width=True,
        key=f"create_campaign_{segment_name}",
    ):

        go_to_campaign_builder(
            segment_name
        )


# =========================================================
# MAIN PAGE
# =========================================================

def show_audience_actions():

    st.title(
        PAGE_TITLE
    )

    st.caption(
        "Turn audience insights into targeted actions."
    )

    # -----------------------------------------------------
    # Load fans
    # -----------------------------------------------------

    fans = load_fans()

    if fans.empty:

        st.info(
            "No fan data is available yet."
        )

        return

    # -----------------------------------------------------
    # Get segments
    # -----------------------------------------------------

    segments = get_segments(
        fans
    )

    available_segments = [
        name
        for name, dataframe
        in segments.items()
        if dataframe is not None
    ]

    # -----------------------------------------------------
    # Check navigation from Analytics
    # -----------------------------------------------------

    analytics_segment = (
        st.session_state.get(
            "selected_audience_segment"
        )
    )

    # -----------------------------------------------------
    # Segment selector
    # -----------------------------------------------------

    st.subheader(
        "🎯 Select Audience"
    )

    default_index = 0

    if (
        analytics_segment
        and analytics_segment
        in available_segments
    ):

        default_index = (
            available_segments.index(
                analytics_segment
            )
        )

    selected_segment = st.selectbox(
        "Audience Segment",
        available_segments,
        index=default_index,
        key="audience_actions_segment",
    )

    # Keep selected audience available
    # to other pages.

    st.session_state[
        "selected_audience_segment"
    ] = selected_segment

    # -----------------------------------------------------
    # Get audience
    # -----------------------------------------------------

    audience = segments.get(
        selected_segment,
        pd.DataFrame(),
    )

    if audience is None:

        audience = pd.DataFrame()

    # -----------------------------------------------------
    # Audience header
    # -----------------------------------------------------

    st.divider()

    st.header(
        f"🎯 {selected_segment}"
    )

    description = (
        SEGMENT_DESCRIPTIONS.get(
            selected_segment,
            "",
        )
    )

    if description:

        st.write(
            description
        )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    summary = audience_summary(
        audience
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Audience Size",
            summary["fans"],
        )

    with col2:

        st.metric(
            "Avg Engagement",
            f"{summary['engagement']:.1f}",
        )

    with col3:

        st.metric(
            "Total Spend",
            f"R{summary['spend']:,.2f}",
        )

    # -----------------------------------------------------
    # Main action tabs
    # -----------------------------------------------------

    tab_view, tab_action, tab_campaign = st.tabs(
        [
            "👥 View Audience",
            "⚡ Take Action",
            "🚀 Create Campaign",
        ]
    )

    # -----------------------------------------------------
    # VIEW AUDIENCE
    # -----------------------------------------------------

    with tab_view:

        st.subheader(
            "👥 Fans in This Audience"
        )

        show_audience_table(
            audience
        )

    # -----------------------------------------------------
    # TAKE ACTION
    # -----------------------------------------------------

    with tab_action:

        show_take_action(
            audience,
            selected_segment,
        )

    # -----------------------------------------------------
    # CREATE CAMPAIGN
    # -----------------------------------------------------

    with tab_campaign:

        show_create_campaign(
            audience,
            selected_segment,
        )

    # -----------------------------------------------------
    # Audience insight
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "🧠 Audience Insight"
    )

    st.info(
        get_recommended_action(
            selected_segment
        )
    )


# =========================================================
# STREAMLIT ENTRY POINT
# =========================================================

if __name__ == "__main__":

    show_audience_actions()