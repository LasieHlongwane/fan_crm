# pages/campaign_execution.py

import uuid
from datetime import datetime

import pandas as pd
import streamlit as st

from data.google_sheets import (
    read_sheet,
    add_row,
    get_spreadsheet,
    get_worksheet,
    update_row,
)


# =========================================================
# CONFIGURATION
# =========================================================

CAMPAIGNS_SHEET = "Campaigns"
FANS_SHEET = "Fans"
QUEUE_SHEET = "Campaign Queue"

STATUS_PENDING = "Pending"
STATUS_SENT = "Sent"
STATUS_FAILED = "Failed"

QUEUE_HEADERS = [
    "queue_id",
    "campaign_id",
    "fan_id",
    "fan_name",
    "phone",
    "email",
    "channel",
    "message",
    "status",
    "created_at",
    "sent_at",
    "error",
]


# =========================================================
# SAFE HELPERS
# =========================================================

def safe_text(value):

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def generate_queue_id():

    return (
        "QUE-"
        + uuid.uuid4().hex[:10].upper()
    )


def now_string():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# =========================================================
# LOAD CAMPAIGNS
# =========================================================

def load_campaigns():

    try:

        return read_sheet(
            CAMPAIGNS_SHEET
        )

    except Exception:

        return pd.DataFrame()


# =========================================================
# LOAD FANS
# =========================================================

def load_fans():

    try:

        return read_sheet(
            FANS_SHEET
        )

    except Exception:

        return pd.DataFrame()


# =========================================================
# LOAD QUEUE
# =========================================================

def load_queue():

    try:

        return read_sheet(
            QUEUE_SHEET
        )

    except Exception:

        return pd.DataFrame()


# =========================================================
# ENSURE QUEUE SHEET
# =========================================================

def ensure_queue_sheet():

    try:

        worksheet = get_worksheet(
            QUEUE_SHEET
        )

        return worksheet

    except Exception:
        pass

    spreadsheet = get_spreadsheet()

    worksheet = spreadsheet.add_worksheet(
        title=QUEUE_SHEET,
        rows=1000,
        cols=len(QUEUE_HEADERS),
    )

    worksheet.append_row(
        QUEUE_HEADERS,
        value_input_option="USER_ENTERED",
    )

    return worksheet


# =========================================================
# FIND CAMPAIGN
# =========================================================

def get_campaign(
    campaign_id,
):

    campaigns = load_campaigns()

    if campaigns.empty:
        return None

    if "campaign_id" not in campaigns.columns:
        return None

    matches = campaigns[
        campaigns["campaign_id"]
        .astype(str)
        .str.strip()
        ==
        str(campaign_id).strip()
    ]

    if matches.empty:
        return None

    return (
        matches
        .iloc[0]
        .to_dict()
    )


# =========================================================
# GET CAMPAIGN AUDIENCE
# =========================================================

def get_campaign_audience(
    campaign,
):

    fans = load_fans()

    if fans.empty:
        return pd.DataFrame()

    segment_name = safe_text(
        campaign.get(
            "audience_segment",
            "",
        )
    )

    if not segment_name:
        return pd.DataFrame()

    try:

        from audience_segmentation import (
            get_segment,
        )

        audience = get_segment(
            fans,
            segment_name,
        )

        if audience is None:
            return pd.DataFrame()

        return audience.copy()

    except Exception:

        return pd.DataFrame()


# =========================================================
# FIND FAN FIELD
# =========================================================

def get_fan_value(
    fan,
    columns,
):

    for column in columns:

        if column not in fan:
            continue

        value = safe_text(
            fan.get(column)
        )

        if value:
            return value

    return ""


# =========================================================
# CREATE DELIVERY QUEUE
# =========================================================

def create_delivery_queue(
    campaign,
):

    ensure_queue_sheet()

    campaign_id = safe_text(
        campaign.get(
            "campaign_id",
            "",
        )
    )

    if not campaign_id:
        raise ValueError(
            "Campaign does not have a campaign_id."
        )

    audience = get_campaign_audience(
        campaign
    )

    if audience.empty:
        return {
            "created": 0,
            "skipped": 0,
        }

    existing_queue = load_queue()

    existing_keys = set()

    if not existing_queue.empty:

        if (
            "campaign_id"
            in existing_queue.columns
            and
            "fan_id"
            in existing_queue.columns
        ):

            for _, row in (
                existing_queue.iterrows()
            ):

                existing_keys.add(
                    (
                        safe_text(
                            row.get(
                                "campaign_id"
                            )
                        ),
                        safe_text(
                            row.get(
                                "fan_id"
                            )
                        ),
                    )
                )

    channel = safe_text(
        campaign.get(
            "channel",
            "",
        )
    )

    message = safe_text(
        campaign.get(
            "message",
            "",
        )
    )

    created = 0
    skipped = 0

    for _, fan in audience.iterrows():

        fan_id = get_fan_value(
            fan,
            [
                "fan_id",
                "id",
                "email",
                "phone",
            ],
        )

        if not fan_id:

            skipped += 1
            continue

        key = (
            campaign_id,
            fan_id,
        )

        # Prevent duplicate queue entries
        if key in existing_keys:

            skipped += 1
            continue

        fan_name = get_fan_value(
            fan,
            [
                "name",
                "full_name",
                "fan_name",
            ],
        )

        phone = get_fan_value(
            fan,
            [
                "phone",
                "phone_number",
                "whatsapp_number",
            ],
        )

        email = get_fan_value(
            fan,
            [
                "email",
                "email_address",
            ],
        )

        # -------------------------------------------------
        # Validate contact
        # -------------------------------------------------

        if not phone and not email:

            status = STATUS_FAILED

            error = (
                "No phone number or email address."
            )

        else:

            status = STATUS_PENDING
            error = ""

        queue_record = {

            "queue_id":
                generate_queue_id(),

            "campaign_id":
                campaign_id,

            "fan_id":
                fan_id,

            "fan_name":
                fan_name,

            "phone":
                phone,

            "email":
                email,

            "channel":
                channel,

            "message":
                message,

            "status":
                status,

            "created_at":
                now_string(),

            "sent_at":
                "",

            "error":
                error,
        }

        add_row(
            QUEUE_SHEET,
            queue_record,
        )

        existing_keys.add(
            key
        )

        created += 1

    return {
        "created": created,
        "skipped": skipped,
    }


# =========================================================
# QUEUE STATUS COUNTS
# =========================================================

def get_queue_counts(
    queue,
):

    if queue.empty:

        return {
            "total": 0,
            "pending": 0,
            "sent": 0,
            "failed": 0,
        }

    if "status" not in queue.columns:

        return {
            "total": len(queue),
            "pending": 0,
            "sent": 0,
            "failed": 0,
        }

    statuses = (
        queue["status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return {

        "total":
            len(queue),

        "pending":
            int(
                (
                    statuses
                    == "pending"
                ).sum()
            ),

        "sent":
            int(
                (
                    statuses
                    == "sent"
                ).sum()
            ),

        "failed":
            int(
                (
                    statuses
                    == "failed"
                ).sum()
            ),
    }


# =========================================================
# UPDATE QUEUE ROW
# =========================================================

def update_queue_status(
    dataframe_index,
    status,
    error="",
):

    queue = load_queue()

    if queue.empty:
        return False

    if dataframe_index < 0:
        return False

    if dataframe_index >= len(queue):
        return False

    row_number = (
        dataframe_index + 2
    )

    row_data = (
        queue
        .iloc[dataframe_index]
        .to_dict()
    )

    row_data["status"] = status

    row_data["error"] = error

    if status == STATUS_SENT:

        row_data["sent_at"] = (
            now_string()
        )

    elif status == STATUS_PENDING:

        row_data["sent_at"] = ""

    update_row(
        QUEUE_SHEET,
        row_number,
        row_data,
    )

    return True


# =========================================================
# MARK SENT
# =========================================================

def mark_sent(
    dataframe_index,
):

    return update_queue_status(
        dataframe_index,
        STATUS_SENT,
        "",
    )


# =========================================================
# MARK FAILED
# =========================================================

def mark_failed(
    dataframe_index,
    error="Delivery failed.",
):

    return update_queue_status(
        dataframe_index,
        STATUS_FAILED,
        error,
    )


# =========================================================
# RETRY
# =========================================================

def retry_delivery(
    dataframe_index,
):

    return update_queue_status(
        dataframe_index,
        STATUS_PENDING,
        "",
    )


# =========================================================
# SHOW PAGE
# =========================================================

def show_campaign_execution():

    st.title(
        "🚀 Campaign Execution"
    )

    st.caption(
        "Campaign → Audience → Delivery Queue → "
        "Pending → Sent / Failed"
    )

    # =====================================================
    # LOAD CAMPAIGNS
    # =====================================================

    campaigns = load_campaigns()

    if campaigns.empty:

        st.info(
            "No campaigns found. "
            "Create a campaign first."
        )

        return

    if "campaign_id" not in campaigns.columns:

        st.error(
            "The Campaigns sheet does not contain "
            "'campaign_id'."
        )

        return

    # =====================================================
    # CAMPAIGN SELECTOR
    # =====================================================

    campaign_options = {}

    for _, campaign in (
        campaigns.iterrows()
    ):

        campaign_id = safe_text(
            campaign.get(
                "campaign_id"
            )
        )

        campaign_name = safe_text(
            campaign.get(
                "campaign_name"
            )
        )

        if campaign_id:

            campaign_options[
                campaign_id
            ] = (
                campaign_name
                or campaign_id
            )

    if not campaign_options:

        st.warning(
            "No campaigns are available."
        )

        return

    selected_campaign_id = (
        st.selectbox(
            "Select Campaign",
            list(
                campaign_options.keys()
            ),
            format_func=lambda x:
                (
                    f"{campaign_options[x]} "
                    f"({x})"
                ),
        )
    )

    campaign = get_campaign(
        selected_campaign_id
    )

    if not campaign:

        st.error(
            "Unable to load campaign."
        )

        return

    # =====================================================
    # CAMPAIGN SUMMARY
    # =====================================================

    st.subheader(
        "📋 Campaign Details"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Campaign",
            safe_text(
                campaign.get(
                    "campaign_name"
                )
            )
            or "Unnamed",
        )

    with col2:

        st.metric(
            "Audience",
            safe_text(
                campaign.get(
                    "audience_segment"
                )
            )
            or "None",
        )

    with col3:

        st.metric(
            "Channel",
            safe_text(
                campaign.get(
                    "channel"
                )
            )
            or "None",
        )

    with col4:

        st.metric(
            "Status",
            safe_text(
                campaign.get(
                    "status"
                )
            )
            or "Draft",
        )

    # =====================================================
    # MESSAGE
    # =====================================================

    with st.expander(
        "💬 Campaign Message",
        expanded=False,
    ):

        st.write(
            safe_text(
                campaign.get(
                    "message"
                )
            )
            or "No message."
        )

    st.divider()

    # =====================================================
    # AUDIENCE
    # =====================================================

    audience = get_campaign_audience(
        campaign
    )

    st.subheader(
        "🎯 Campaign Audience"
    )

    st.metric(
        "Audience Members",
        len(audience),
    )

    if not audience.empty:

        preview_columns = [
            column
            for column in [
                "fan_id",
                "name",
                "full_name",
                "phone",
                "email",
                "engagement_score",
                "total_spend",
            ]
            if column in audience.columns
        ]

        if preview_columns:

            st.dataframe(
                audience[
                    preview_columns
                ],
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.dataframe(
                audience,
                use_container_width=True,
                hide_index=True,
            )

    else:

        st.warning(
            "No fans were found for this campaign's "
            "audience segment."
        )

    # =====================================================
    # CREATE QUEUE
    # =====================================================

    st.subheader(
        "📥 Delivery Queue"
    )

    st.write(
        "Create one delivery record for every fan "
        "in this campaign audience."
    )

    if st.button(
        "📥 Create Delivery Queue",
        type="primary",
        use_container_width=True,
    ):

        try:

            result = (
                create_delivery_queue(
                    campaign
                )
            )

            st.success(
                f"{result['created']} recipient(s) "
                "added to the delivery queue."
            )

            if result["skipped"]:

                st.info(
                    f"{result['skipped']} recipient(s) "
                    "were skipped because they already "
                    "exist in the queue or have no fan ID."
                )

            st.rerun()

        except Exception as error:

            st.error(
                "Unable to create delivery queue."
            )

            st.exception(
                error
            )

    st.divider()

    # =====================================================
    # LOAD QUEUE
    # =====================================================

    queue = load_queue()

    if queue.empty:

        st.info(
            "The delivery queue is empty."
        )

        return

    if "campaign_id" not in queue.columns:

        st.error(
            "Campaign Queue is missing campaign_id."
        )

        return

    campaign_queue = queue[
        queue["campaign_id"]
        .astype(str)
        .str.strip()
        ==
        selected_campaign_id
    ].copy()

    if campaign_queue.empty:

        st.info(
            "This campaign has no delivery records yet."
        )

        return

    # =====================================================
    # QUEUE METRICS
    # =====================================================

    counts = get_queue_counts(
        campaign_queue
    )

    st.subheader(
        "📊 Delivery Status"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Total",
            counts["total"],
        )

    with col2:

        st.metric(
            "Pending",
            counts["pending"],
        )

    with col3:

        st.metric(
            "Sent",
            counts["sent"],
        )

    with col4:

        st.metric(
            "Failed",
            counts["failed"],
        )

    # =====================================================
    # DELIVERY TABLE
    # =====================================================

    st.subheader(
        "📬 Recipients"
    )

    display_columns = [
        column
        for column in [
            "fan_id",
            "fan_name",
            "phone",
            "email",
            "channel",
            "status",
            "created_at",
            "sent_at",
            "error",
        ]
        if column in campaign_queue.columns
    ]

    st.dataframe(
        campaign_queue[
            display_columns
        ],
        use_container_width=True,
        hide_index=True,
    )

    # =====================================================
    # PENDING
    # =====================================================

    pending = campaign_queue[
        campaign_queue["status"]
        .fillna("")
        .astype(str)
        .str.lower()
        ==
        "pending"
    ]

    if not pending.empty:

        st.subheader(
            "⏳ Pending Deliveries"
        )

        for index, row in (
            pending.iterrows()
        ):

            fan_name = (
                safe_text(
                    row.get(
                        "fan_name"
                    )
                )
                or safe_text(
                    row.get(
                        "fan_id"
                    )
                )
            )

            contact = (
                safe_text(
                    row.get(
                        "phone"
                    )
                )
                or safe_text(
                    row.get(
                        "email"
                    )
                )
            )

            with st.container(
                border=True
            ):

                col1, col2, col3 = (
                    st.columns(
                        [5, 1, 1]
                    )
                )

                with col1:

                    st.write(
                        f"**{fan_name}**"
                    )

                    st.caption(
                        contact
                        or
                        "No contact information"
                    )

                with col2:

                    if st.button(
                        "✓ Sent",
                        key=(
                            f"sent_"
                            f"{selected_campaign_id}_"
                            f"{index}"
                        ),
                    ):

                        try:

                            mark_sent(
                                index
                            )

                            st.success(
                                "Recipient marked as Sent."
                            )

                            st.rerun()

                        except Exception as error:

                            st.error(
                                f"Unable to update recipient: "
                                f"{error}"
                            )

                with col3:

                    if st.button(
                        "✕ Failed",
                        key=(
                            f"failed_"
                            f"{selected_campaign_id}_"
                            f"{index}"
                        ),
                    ):

                        try:

                            mark_failed(
                                index,
                                "Manually marked as failed.",
                            )

                            st.warning(
                                "Recipient marked as Failed."
                            )

                            st.rerun()

                        except Exception as error:

                            st.error(
                                f"Unable to update recipient: "
                                f"{error}"
                            )

    # =====================================================
    # FAILED
    # =====================================================

    failed = campaign_queue[
        campaign_queue["status"]
        .fillna("")
        .astype(str)
        .str.lower()
        ==
        "failed"
    ]

    if not failed.empty:

        st.subheader(
            "❌ Failed Deliveries"
        )

        for index, row in (
            failed.iterrows()
        ):

            fan_name = (
                safe_text(
                    row.get(
                        "fan_name"
                    )
                )
                or safe_text(
                    row.get(
                        "fan_id"
                    )
                )
            )

            error_message = (
                safe_text(
                    row.get(
                        "error"
                    )
                )
                or
                "Delivery failed."
            )

            with st.container(
                border=True
            ):

                col1, col2 = (
                    st.columns(
                        [5, 1]
                    )
                )

                with col1:

                    st.write(
                        f"**{fan_name}**"
                    )

                    st.caption(
                        error_message
                    )

                with col2:

                    if st.button(
                        "↻ Retry",
                        key=(
                            f"retry_"
                            f"{selected_campaign_id}_"
                            f"{index}"
                        ),
                    ):

                        try:

                            retry_delivery(
                                index
                            )

                            st.success(
                                "Recipient returned to Pending."
                            )

                            st.rerun()

                        except Exception as error:

                            st.error(
                                f"Unable to retry recipient: "
                                f"{error}"
                            )

    # =====================================================
    # EXECUTION FLOW
    # =====================================================

    st.divider()

    st.subheader(
        "🔄 Campaign Execution Flow"
    )

    st.markdown(
        """
        **Campaign**
        ↓
        **Audience Segment**
        ↓
        **Delivery Queue**
        ↓
        **Pending**
        ↓
        **Sent / Failed**
        """
    )


# =========================================================
# TEST
# =========================================================

def test_campaign_execution():

    print(
        "Campaign execution module loaded."
    )

    print(
        "create_delivery_queue:",
        create_delivery_queue,
    )

    print(
        "update_queue_status:",
        update_queue_status,
    )

    print(
        "show_campaign_execution:",
        show_campaign_execution,
    )