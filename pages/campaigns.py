import streamlit as st
import pandas as pd

from data.google_sheets import read_sheet

from audience_segmentation import (
    get_segment_counts,
)

from campaign_manager import (
    create_campaign,
    get_campaigns,
    get_campaign_audience,
    get_campaign_summary,
    CAMPAIGN_TYPES,
    CAMPAIGN_CHANNELS,
)


def show_campaigns():

    # =====================================================
    # PAGE HEADER
    # =====================================================

    st.title(
        "📣 Campaigns"
    )

    st.caption(
        "Turn your audience segments into targeted campaigns."
    )

    # =====================================================
    # LOAD DATA
    # =====================================================

    try:

        fans = read_sheet(
            "Fans"
        )

    except Exception as e:

        st.error(
            f"Could not load fans: {e}"
        )

        return

    # =====================================================
    # CAMPAIGN SUMMARY
    # =====================================================

    summary = get_campaign_summary()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Campaigns",
        summary["campaigns"],
    )

    col2.metric(
        "Active",
        summary["active"],
    )

    col3.metric(
        "Conversions",
        summary["conversions"],
    )

    col4.metric(
        "Campaign Revenue",
        f"R{summary['revenue']:,.2f}",
    )

    st.divider()

    # =====================================================
    # CREATE CAMPAIGN
    # =====================================================

    st.subheader(
        "➕ Create Campaign"
    )

    if fans.empty:

        st.warning(
            "You need fans before creating a targeted campaign."
        )

        return

    segment_counts = get_segment_counts(
        fans
    )

    segment_names = (
        segment_counts[
            "Segment"
        ].tolist()
    )

    with st.expander(
        "Create a new campaign",
        expanded=True,
    ):

        campaign_name = st.text_input(
            "Campaign Name",
            placeholder=(
                "Example: WHOLENESS Merch Drop"
            ),
        )

        col1, col2 = st.columns(2)

        with col1:

            campaign_type = st.selectbox(
                "Campaign Type",
                CAMPAIGN_TYPES,
            )

        with col2:

            channel = st.selectbox(
                "Channel",
                CAMPAIGN_CHANNELS,
            )

        audience_segment = st.selectbox(
            "Target Audience",
            segment_names,
        )

        # -------------------------------------------------
        # Calculate audience
        # -------------------------------------------------

        target_audience = (
            get_campaign_audience(
                fans,
                audience_segment,
            )
        )

        st.info(
            f"🎯 This campaign will target "
            f"**{len(target_audience)} fans** "
            f"in the **{audience_segment}** segment."
        )

        # -------------------------------------------------
        # Message
        # -------------------------------------------------

        message = st.text_area(
            "Campaign Message",
            height=150,
            placeholder=(
                "Example:\n\n"
                "WHOLENESS FAMILY ❤️\n\n"
                "The new limited WHOLENESS "
                "collection is now available..."
            ),
        )

        budget = st.number_input(
            "Campaign Budget",
            min_value=0.0,
            step=100.0,
            value=0.0,
        )

        if st.button(
            "🚀 Create Campaign",
            use_container_width=True,
        ):

            try:

                campaign = create_campaign(

                    name=campaign_name,

                    campaign_type=(
                        campaign_type
                    ),

                    audience_segment=(
                        audience_segment
                    ),

                    channel=channel,

                    message=message,

                    budget=budget,
                )

                st.success(
                    "Campaign created successfully!"
                )

                st.info(
                    f"Campaign ID: "
                    f"{campaign['campaign_id']}"
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Could not create campaign: {e}"
                )

    st.divider()

    # =====================================================
    # CAMPAIGN AUDIENCE PREVIEW
    # =====================================================

    st.subheader(
        "🎯 Audience Preview"
    )

    preview_segment = st.selectbox(
        "Preview audience",
        segment_names,
        key="campaign_preview_segment",
    )

    preview = get_campaign_audience(
        fans,
        preview_segment,
    )

    st.metric(
        "Audience Size",
        len(preview),
    )

    if not preview.empty:

        preferred_columns = [
            "fan_id",
            "name",
            "email",
            "phone",
            "location",
            "favorite_song",
            "favorite_brand",
            "engagement_score",
            "total_spend",
        ]

        available_columns = [
            column
            for column in preferred_columns
            if column in preview.columns
        ]

        st.dataframe(
            preview[
                available_columns
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # =====================================================
    # EXISTING CAMPAIGNS
    # =====================================================

    st.subheader(
        "📋 Campaign History"
    )

    campaigns = get_campaigns()

    if campaigns.empty:

        st.info(
            "No campaigns have been created yet."
        )

    else:

        display_columns = [
            "campaign_id",
            "campaign_name",
            "campaign_type",
            "audience_segment",
            "channel",
            "budget",
            "status",
            "created_at",
            "sent",
            "responses",
            "conversions",
            "revenue",
        ]

        available_columns = [
            column
            for column in display_columns
            if column in campaigns.columns
        ]

        st.dataframe(
            campaigns[
                available_columns
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # =====================================================
    # CAMPAIGN IDEA
    # =====================================================

    st.subheader(
        "💡 Campaign Strategy"
    )

    st.write(
        """
        Don't send the same message to everyone.

        Use your CRM to target specific groups:

        • 💎 VIP Fans → exclusive access

        • 🔥 Superfans → early releases

        • 🛍 Potential Buyers → merchandise offers

        • 👟 Fashion Audience → fashion collaborations

        • 🎵 WHOLENESS Fans → WHOLENESS campaigns

        • 📍 Event Fans → local event invitations

        • 💤 Cold Fans → re-engagement campaigns
        """
    )