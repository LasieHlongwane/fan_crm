import streamlit as st
import pandas as pd

from data.google_sheets import (
    get_fan_by_id,
    get_fan_purchases,
)

from interaction_tracker import (
    create_interaction,
    get_interactions_for_fan,
    get_fan_interaction_summary,
    INTERACTION_TYPES,
)


def show_fan_profile():

    # =====================================================
    # PAGE HEADER
    # =====================================================

    st.title("👤 Fan Profile")

    # =====================================================
    # GET SELECTED FAN
    # =====================================================

    fan_id = st.session_state.get(
        "selected_fan_id"
    )

    # -----------------------------------------------------
    # No fan selected
    # -----------------------------------------------------

    if not fan_id:

        st.info(
            "Select a fan from the Fans page "
            "to view their profile."
        )

        if st.button(
            "← Back to Fans"
        ):

            st.switch_page(
                "pages/fans.py"
            )

        return

    # =====================================================
    # LOAD FAN
    # =====================================================

    try:

        fan = get_fan_by_id(
            fan_id
        )

        if not fan:

            st.error(
                "Fan could not be found."
            )

            return

        interactions = (
            get_interactions_for_fan(
                fan_id
            )
        )

        purchases = (
            get_fan_purchases(
                fan_id
            )
        )

        interaction_summary = (
            get_fan_interaction_summary(
                fan_id
            )
        )

    except Exception as e:

        st.error(
            f"Unable to load fan profile: {e}"
        )

        return

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    name = fan.get(
        "name",
        "Unnamed Fan",
    )

    email = fan.get(
        "email",
        "",
    )

    phone = fan.get(
        "phone",
        "",
    )

    location = fan.get(
        "location",
        "",
    )

    age_group = fan.get(
        "age_group",
        "",
    )

    brand = fan.get(
        "favorite_brand",
        "",
    )

    source = fan.get(
        "source",
        "",
    )

    favorite_song = fan.get(
        "favorite_song",
        "",
    )

    status = fan.get(
        "fan_status",
        fan.get(
            "fan status",
            "New",
        ),
    )

    # -----------------------------------------------------
    # Existing fan score
    # -----------------------------------------------------

    existing_score = fan.get(
        "engagement_score",
        0,
    )

    try:

        existing_score = float(
            existing_score
        )

    except Exception:

        existing_score = 0

    # -----------------------------------------------------
    # Interaction-derived score
    # -----------------------------------------------------

    interaction_score = interaction_summary.get(
        "engagement_score",
        0,
    )

    try:

        interaction_score = float(
            interaction_score
        )

    except Exception:

        interaction_score = 0

    # -----------------------------------------------------
    # Use interaction score when interactions exist
    # -----------------------------------------------------

    if len(interactions) > 0:

        score = interaction_score

    else:

        score = existing_score

    # -----------------------------------------------------
    # Total spend
    # -----------------------------------------------------

    total_spend = fan.get(
        "total_spend",
        0,
    )

    try:

        total_spend = float(
            total_spend
        )

    except Exception:

        total_spend = 0

    # =====================================================
    # PROFILE HEADER
    # =====================================================

    st.subheader(
        f"🎵 {name}"
    )

    st.caption(
        f"Fan ID: {fan_id}"
    )

    # =====================================================
    # STATUS
    # =====================================================

    status_text = str(
        status or "New"
    ).strip().lower()

    relationship_level = (
        interaction_summary.get(
            "engagement_level",
            "New",
        )
    )

    if (
        status_text == "vip"
        or relationship_level == "VIP"
    ):

        st.success(
            "💎 VIP FAN"
        )

    elif (
        status_text == "loyal"
        or relationship_level
        == "Highly Engaged"
    ):

        st.info(
            "⭐ LOYAL FAN"
        )

    elif (
        status_text == "engaged"
        or relationship_level
        == "Engaged"
    ):

        st.warning(
            "🔥 ENGAGED FAN"
        )

    else:

        st.caption(
            "🌱 NEW FAN"
        )

    # =====================================================
    # CORE METRICS
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Engagement Score",
        f"{score:.0f}",
    )

    col2.metric(
        "Lifetime Spend",
        f"R{total_spend:,.2f}",
    )

    col3.metric(
        "Interactions",
        len(interactions),
    )

    col4.metric(
        "Purchases",
        len(purchases),
    )

    st.divider()

    # =====================================================
    # FAN INFORMATION
    # =====================================================

    st.subheader(
        "📋 Fan Information"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**📧 Email:** "
            f"{email or '—'}"
        )

        st.write(
            f"**📱 WhatsApp:** "
            f"{phone or '—'}"
        )

        st.write(
            f"**📍 City:** "
            f"{location or '—'}"
        )

        st.write(
            f"**🎂 Age Range:** "
            f"{age_group or '—'}"
        )

    with col2:

        st.write(
            f"**👟 Favorite Brand:** "
            f"{brand or '—'}"
        )

        st.write(
            f"**🎵 Favorite Song:** "
            f"{favorite_song or '—'}"
        )

        st.write(
            f"**📱 Discovered Through:** "
            f"{source or '—'}"
        )

        st.write(
            f"**⭐ Status:** "
            f"{status or '—'}"
        )

    st.divider()

    # =====================================================
    # AUDIENCE INTEREST
    # =====================================================

    st.subheader(
        "🎯 Audience Interests"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            "### 👟 Fashion"
        )

        st.write(
            brand
            or "No brand preference recorded."
        )

    with col2:

        st.markdown(
            "### 🎵 Music"
        )

        st.write(
            favorite_song
            or "No favorite song recorded."
        )

    st.divider()

    # =====================================================
    # RELATIONSHIP STRENGTH
    # =====================================================

    st.subheader(
        "📈 Relationship Strength"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Interactions",
        interaction_summary.get(
            "total_interactions",
            0,
        ),
    )

    col2.metric(
        "Engagement Score",
        f"{score:.0f}",
    )

    col3.metric(
        "Relationship",
        relationship_level,
    )

    st.divider()

    # =====================================================
    # RECORD INTERACTION
    # =====================================================

    st.subheader(
        "➕ Record Interaction"
    )

    with st.expander(
        "Add a new fan interaction"
    ):

        interaction_type = st.selectbox(
            "Interaction Type",
            INTERACTION_TYPES,
            key=(
                f"interaction_type_"
                f"{fan_id}"
            ),
        )

        description = st.text_area(
            "What happened?",
            placeholder=(
                "Example: Commented on "
                "the WHOLENESS TikTok video"
            ),
            key=(
                f"interaction_description_"
                f"{fan_id}"
            ),
        )

        col1, col2 = st.columns(2)

        with col1:

            channel = st.selectbox(
                "Channel",
                [
                    "",
                    "Instagram",
                    "TikTok",
                    "WhatsApp",
                    "YouTube",
                    "Spotify",
                    "Live Event",
                    "Email",
                    "Other",
                ],
                key=(
                    f"interaction_channel_"
                    f"{fan_id}"
                ),
            )

        with col2:

            campaign = st.text_input(
                "Campaign",
                placeholder=(
                    "Example: WHOLENESS Launch"
                ),
                key=(
                    f"interaction_campaign_"
                    f"{fan_id}"
                ),
            )

        value = st.number_input(
            "Value",
            min_value=0.0,
            step=1.0,
            help=(
                "Optional monetary or campaign "
                "value associated with this interaction."
            ),
            key=(
                f"interaction_value_"
                f"{fan_id}"
            ),
        )

        if st.button(
            "💾 Save Interaction",
            use_container_width=True,
            key=(
                f"save_interaction_"
                f"{fan_id}"
            ),
        ):

            if not description.strip():

                st.warning(
                    "Please describe the interaction."
                )

            else:

                try:

                    interaction = create_interaction(

                        fan_id=fan_id,

                        interaction_type=(
                            interaction_type
                        ),

                        description=(
                            description
                        ),

                        channel=channel,

                        campaign=campaign,

                        value=value,
                    )

                    st.success(
                        "Interaction recorded successfully!"
                    )

                    st.info(
                        "Interaction ID: "
                        f"{interaction['interaction_id']} "
                        "| "
                        "Engagement Points: "
                        f"+{interaction['engagement_points']}"
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Could not save interaction: "
                        f"{e}"
                    )

    st.divider()

    # =====================================================
    # INTERACTIONS
    # =====================================================

    st.subheader(
        "💬 Interaction History"
    )

    if interactions.empty:

        st.info(
            "No interactions recorded yet."
        )

    else:

        interaction_display = (
            interactions.copy()
        )

        # -------------------------------------------------
        # Select useful columns
        # -------------------------------------------------

        preferred_columns = [
            "date",
            "interaction_type",
            "description",
            "channel",
            "campaign",
            "value",
            "engagement_points",
        ]

        available_columns = [
            column
            for column in preferred_columns
            if column
            in interaction_display.columns
        ]

        if available_columns:

            interaction_display = (
                interaction_display[
                    available_columns
                ]
            )

        st.dataframe(
            interaction_display,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # =====================================================
    # INTERACTION TYPES
    # =====================================================

    if not interactions.empty:

        st.subheader(
            "📊 Interaction Breakdown"
        )

        if (
            "interaction_type"
            in interactions.columns
        ):

            interaction_counts = (
                interactions[
                    "interaction_type"
                ]
                .value_counts()
                .rename(
                    "Interactions"
                )
            )

            st.bar_chart(
                interaction_counts
            )

    st.divider()

    # =====================================================
    # PURCHASES
    # =====================================================

    st.subheader(
        "🛍 Purchases"
    )

    if purchases.empty:

        st.info(
            "This fan has not made any purchases yet."
        )

    else:

        purchase_display = (
            purchases.copy()
        )

        st.dataframe(
            purchase_display,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # =====================================================
    # RECOMMENDED ACTION
    # =====================================================

    st.subheader(
        "💡 Recommended Action"
    )

    if (
        total_spend > 0
        and score >= 76
    ):

        st.success(
            "💎 This is a high-value fan. "
            "Consider giving them early access, "
            "exclusive merchandise or VIP event access."
        )

    elif score >= 76:

        st.info(
            "🔥 Highly engaged but has not purchased yet. "
            "Consider a targeted merchandise or event offer."
        )

    elif brand:

        st.info(
            f"👟 This fan is interested in {brand}. "
            "Consider using relevant brand/fashion content "
            "in future campaigns."
        )

    elif len(interactions) == 0:

        st.info(
            "Start recording interactions with this fan "
            "to understand their relationship with your music."
        )

    else:

        st.info(
            "Continue engaging this fan and learn more "
            "about their interests."
        )

    # =====================================================
    # BACK BUTTON
    # =====================================================

    st.divider()

    if st.button(
        "← Back to Fans",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/fans.py"
        )