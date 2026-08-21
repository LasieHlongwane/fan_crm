# pages/campaign_builder.py

import streamlit as st
import pandas as pd

from data.google_sheets import read_sheet

from campaign_manager import (
    create_campaign,
    CAMPAIGN_TYPES,
    CAMPAIGN_CHANNELS,
)

from audience_segmentation import (
    get_segment,
)

from campaign_delivery import (
    create_delivery_queue,
)


# =========================================================
# LOAD FANS
# =========================================================

def load_fans():

    try:

        return read_sheet("Fans")

    except Exception:

        return pd.DataFrame()


# =========================================================
# SAFE FAN VALUE
# =========================================================

def get_fan_value(
    fan,
    columns,
):

    for column in columns:

        if column not in fan.index:
            continue

        value = fan.get(
            column,
            "",
        )

        if pd.notna(value):

            value = str(value).strip()

            if value:
                return value

    return ""


# =========================================================
# PERSONALIZE MESSAGE
# =========================================================

def personalize_message(
    message,
    fan,
):

    name = get_fan_value(
        fan,
        [
            "name",
            "full_name",
            "fan_name",
        ],
    )

    fan_id = get_fan_value(
        fan,
        [
            "fan_id",
        ],
    )

    phone = get_fan_value(
        fan,
        [
            "phone",
            "phone_number",
            "whatsapp_number",
            "mobile",
        ],
    )

    first_name = ""

    if name:

        first_name = (
            name.split()[0]
        )

    replacements = {

        "{name}":
            name,

        "{first_name}":
            first_name,

        "{fan_id}":
            fan_id,

        "{phone}":
            phone,
    }

    result = str(
        message
    )

    for placeholder, value in replacements.items():

        result = result.replace(
            placeholder,
            value,
        )

    return result


# =========================================================
# CREATE DELIVERY QUEUE
# =========================================================

def build_delivery_queue(
    campaign,
    audience,
):

    created = 0
    skipped = 0
    errors = []

    for _, fan in audience.iterrows():

        # -------------------------------------------------
        # Fan ID
        # -------------------------------------------------

        fan_id = get_fan_value(
            fan,
            [
                "fan_id",
            ],
        )

        # -------------------------------------------------
        # Phone
        # -------------------------------------------------

        phone = get_fan_value(
            fan,
            [
                "whatsapp_number",
                "phone",
                "phone_number",
                "mobile",
            ],
        )

        # -------------------------------------------------
        # Required fields
        # -------------------------------------------------

        if not fan_id:

            skipped += 1

            errors.append(
                "Fan skipped: missing fan_id"
            )

            continue

        if not phone:

            skipped += 1

            errors.append(
                f"{fan_id}: missing phone number"
            )

            continue

        # -------------------------------------------------
        # Personalized message
        # -------------------------------------------------

        message = personalize_message(
            campaign["message"],
            fan,
        )

        # -------------------------------------------------
        # Create queue record
        # -------------------------------------------------

        try:

            create_delivery_queue(
                campaign_id=(
                    campaign[
                        "campaign_id"
                    ]
                ),

                fan_id=fan_id,

                channel=(
                    campaign[
                        "channel"
                    ]
                ),

                phone_number=phone,

                message=message,
            )

            created += 1

        except Exception as error:

            skipped += 1

            errors.append(
                f"{fan_id}: {error}"
            )

    return (
        created,
        skipped,
        errors,
    )


# =========================================================
# SHOW CAMPAIGN BUILDER
# =========================================================

def show_campaign_builder():

    st.title(
        "🚀 Campaign Builder"
    )

    st.caption(
        "Create a campaign and automatically "
        "turn its audience into a delivery queue."
    )

    # =====================================================
    # LOAD FANS
    # =====================================================

    fans = load_fans()

    if fans.empty:

        st.warning(
            "No fans are available yet."
        )

        return

    # =====================================================
    # CAMPAIGN DETAILS
    # =====================================================

    st.subheader(
        "1. Campaign Details"
    )

    campaign_name = st.text_input(
        "Campaign Name",
        placeholder=(
            "WHOLENESS Early Access"
        ),
    )

    campaign_type = st.selectbox(
        "Campaign Type",
        CAMPAIGN_TYPES,
    )

    channel = st.selectbox(
        "Delivery Channel",
        CAMPAIGN_CHANNELS,
    )

    budget = st.number_input(
        "Campaign Budget",
        min_value=0.0,
        value=0.0,
        step=50.0,
    )

    # =====================================================
    # AUDIENCE
    # =====================================================

    st.subheader(
        "2. Select Audience"
    )

    segment_options = [

        "All Fans",

        "VIP Fans",

        "Superfans",

        "Potential Buyers",

        "Merch Buyers",

        "Event Fans",

        "Fashion Audience",

        "WHOLENESS Fans",

        "New Fans",

        "Cold Fans",

        "High Value Fans",
    ]

    selected_segment = st.selectbox(
        "Audience Segment",
        segment_options,
    )

    # =====================================================
    # GET AUDIENCE
    # =====================================================

    if selected_segment == "All Fans":

        audience = fans.copy()

    else:

        audience = get_segment(
            fans,
            selected_segment,
        )

    # =====================================================
    # AUDIENCE SUMMARY
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Audience",
            len(audience),
        )

    with col2:

        eligible = 0

        for _, fan in audience.iterrows():

            fan_id = get_fan_value(
                fan,
                ["fan_id"],
            )

            phone = get_fan_value(
                fan,
                [
                    "whatsapp_number",
                    "phone",
                    "phone_number",
                    "mobile",
                ],
            )

            if fan_id and phone:

                eligible += 1

        st.metric(
            "Queue Eligible",
            eligible,
        )

    with col3:

        st.metric(
            "Not Eligible",
            len(audience) - eligible,
        )

    # =====================================================
    # AUDIENCE PREVIEW
    # =====================================================

    with st.expander(
        "👥 Preview Selected Audience"
    ):

        if audience.empty:

            st.info(
                "No fans belong to this segment."
            )

        else:

            st.dataframe(
                audience,
                use_container_width=True,
                hide_index=True,
            )

    # =====================================================
    # MESSAGE
    # =====================================================

    st.subheader(
        "3. Campaign Message"
    )

    st.caption(
        "Available placeholders: "
        "{name}, {first_name}, {fan_id}, {phone}"
    )

    message = st.text_area(
        "Message",
        height=160,
        placeholder=(
            "Hi {first_name}, "
            "thank you for supporting my music. "
            "You have early access..."
        ),
    )

    # =====================================================
    # MESSAGE PREVIEW
    # =====================================================

    if not audience.empty and message.strip():

        st.subheader(
            "4. Message Preview"
        )

        sample_fan = audience.iloc[0]

        preview = personalize_message(
            message,
            sample_fan,
        )

        st.info(
            preview
        )

    # =====================================================
    # CREATE CAMPAIGN
    # =====================================================

    st.subheader(
        "5. Create Campaign"
    )

    st.write(
        "When you click the button below:"
    )

    st.markdown(
        """
        **Campaign**
        ↓  
        **Selected Audience**
        ↓  
        **Delivery Queue**
        ↓  
        **Pending**
        ↓  
        **WhatsApp Execution**
        """
    )

    create_button = st.button(
        "🚀 Create Campaign + Build Delivery Queue",
        type="primary",
        use_container_width=True,
    )

    if not create_button:

        return

    # =====================================================
    # VALIDATION
    # =====================================================

    if not campaign_name.strip():

        st.error(
            "Campaign name is required."
        )

        return

    if not message.strip():

        st.error(
            "Campaign message is required."
        )

        return

    if audience.empty:

        st.error(
            "The selected audience is empty."
        )

        return

    if eligible == 0:

        st.error(
            "No audience members have both "
            "fan_id and a phone number."
        )

        return

    # =====================================================
    # CREATE CAMPAIGN
    # =====================================================

    try:

        with st.spinner(
            "Creating campaign..."
        ):

            campaign = create_campaign(

                name=campaign_name,

                campaign_type=campaign_type,

                audience_segment=(
                    selected_segment
                ),

                channel=channel,

                message=message,

                budget=budget,
            )

        st.success(
            f"Campaign {campaign['campaign_id']} "
            "created successfully."
        )

        # =================================================
        # BUILD DELIVERY QUEUE
        # =================================================

        with st.spinner(
            "Building delivery queue..."
        ):

            created, skipped, errors = (
                build_delivery_queue(
                    campaign,
                    audience,
                )
            )

        # =================================================
        # RESULTS
        # =================================================

        st.divider()

        st.subheader(
            "📨 Delivery Queue Created"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Campaign",
                campaign[
                    "campaign_id"
                ],
            )

        with col2:

            st.metric(
                "Pending",
                created,
            )

        with col3:

            st.metric(
                "Skipped",
                skipped,
            )

        if created:

            st.success(
                f"{created} delivery queue records "
                "were created with Pending status."
            )

        if skipped:

            st.warning(
                f"{skipped} audience members "
                "could not be added to the queue."
            )

        # =================================================
        # ERRORS
        # =================================================

        if errors:

            with st.expander(
                "View skipped audience records"
            ):

                for error in errors:

                    st.write(
                        f"• {error}"
                    )

        # =================================================
        # NEXT STEP
        # =================================================

        st.info(
            "Campaign creation is complete. "
            "The audience is now in the Delivery Queue. "
            "Go to Campaign Performance and use "
            "'Send Pending Messages' or "
            "'Execute Campaign Queue' to deliver them."
        )

    except Exception as error:

        st.error(
            "Campaign creation failed."
        )

        st.exception(
            error
        )
