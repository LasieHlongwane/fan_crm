# pages/artist_leads.py

import json
import os
import time

import gspread
import pandas as pd
import streamlit as st

from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession


# =========================================================
# CONFIGURATION
# =========================================================

ARTIST_LEADS_SHEET = "Artist Leads"

ARTIST_LEADS_SPREADSHEET_ID = (
    "1vpdgj31_RLFuFN0TVS9-uhJaP7h1lAC4hxs-eQlKoxQ"
)

CREDENTIALS_FILE = "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

LEAD_STATUSES = [
    "New",
    "Contacted",
    "Interested",
    "Demo Scheduled",
    "Pilot",
    "Converted",
    "Not Interested",
    "No Response",
]


# =========================================================
# GOOGLE CREDENTIALS
# =========================================================

def get_artist_leads_credentials():

    service_account_info = None

    # -----------------------------------------------------
    # Streamlit secrets
    # -----------------------------------------------------

    try:
        if "gcp_service_account" in st.secrets:
            service_account_info = dict(
                st.secrets["gcp_service_account"]
            )
    except Exception:
        pass

    # -----------------------------------------------------
    # Optional nested Artist Leads credentials
    # -----------------------------------------------------

    if service_account_info is None:

        try:
            if "artist_leads" in st.secrets:

                section = st.secrets[
                    "artist_leads"
                ]

                if "service_account" in section:

                    service_account_info = dict(
                        section["service_account"]
                    )

        except Exception:
            pass

    # -----------------------------------------------------
    # Local credentials.json
    # -----------------------------------------------------

    if (
        service_account_info is None
        and os.path.exists(
            CREDENTIALS_FILE
        )
    ):

        with open(
            CREDENTIALS_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            service_account_info = json.load(
                file
            )

    if not service_account_info:

        raise FileNotFoundError(
            "Google service-account credentials were not found."
        )

    if (
        service_account_info.get("type")
        != "service_account"
    ):

        raise ValueError(
            "Google credentials are not a service-account file."
        )

    return Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES,
    )


# =========================================================
# GOOGLE CLIENT
# =========================================================

@st.cache_resource(
    show_spinner=False
)
def get_artist_leads_client():

    credentials = (
        get_artist_leads_credentials()
    )

    session = AuthorizedSession(
        credentials
    )

    session.headers.update(
        {
            "Connection": "keep-alive",
        }
    )

    return gspread.Client(
        auth=credentials,
        session=session,
    )


# =========================================================
# OPEN SPREADSHEET
# =========================================================

@st.cache_resource(
    show_spinner=False
)
def get_artist_leads_spreadsheet():

    spreadsheet_id = os.getenv(
        "ARTIST_LEADS_SPREADSHEET_ID",
        "",
    ).strip()

    if not spreadsheet_id:

        try:

            if "artist_leads" in st.secrets:

                spreadsheet_id = str(
                    st.secrets[
                        "artist_leads"
                    ].get(
                        "spreadsheet_id",
                        "",
                    )
                ).strip()

        except Exception:
            pass

    if not spreadsheet_id:

        spreadsheet_id = (
            ARTIST_LEADS_SPREADSHEET_ID
        )

    last_error = None

    for attempt in range(3):

        try:

            client = (
                get_artist_leads_client()
            )

            return client.open_by_key(
                spreadsheet_id
            )

        except gspread.SpreadsheetNotFound as error:

            raise Exception(
                "Artist Leads spreadsheet could not be accessed. "
                "Check that the service account has Editor access."
            ) from error

        except Exception as error:

            last_error = error

            if attempt < 2:

                time.sleep(
                    1.5 * (
                        attempt + 1
                    )
                )

    raise Exception(
        "Unable to connect to Artist Leads Google Sheet: "
        f"{last_error}"
    )


# =========================================================
# WORKSHEET
# =========================================================

def get_artist_leads_worksheet():

    spreadsheet = (
        get_artist_leads_spreadsheet()
    )

    try:

        return spreadsheet.worksheet(
            ARTIST_LEADS_SHEET
        )

    except gspread.WorksheetNotFound as error:

        raise ValueError(
            "Worksheet 'Artist Leads' was not found."
        ) from error


# =========================================================
# LOAD LEADS
# =========================================================

def load_artist_leads():

    worksheet = (
        get_artist_leads_worksheet()
    )

    records = (
        worksheet.get_all_records()
    )

    if not records:

        return pd.DataFrame()

    leads = pd.DataFrame(
        records
    )

    # -----------------------------------------------------
    # Make sure expected columns exist
    # -----------------------------------------------------

    defaults = {
        "lead_id": "",
        "artist_name": "",
        "email": "",
        "whatsapp": "",
        "genre": "",
        "audience_size": "",
        "status": "New",
        "source": "",
        "created_at": "",
        "notes": "",
    }

    for column, default in defaults.items():

        if column not in leads.columns:

            leads[column] = default

    return leads


# =========================================================
# FIND SHEET ROW
# =========================================================

def find_lead_row(
    lead_id,
):

    worksheet = (
        get_artist_leads_worksheet()
    )

    headers = [
        str(header).strip()
        for header
        in worksheet.row_values(1)
    ]

    if "lead_id" not in headers:

        raise ValueError(
            "Artist Leads sheet is missing the 'lead_id' header."
        )

    lead_id_column = (
        headers.index(
            "lead_id"
        )
        + 1
    )

    values = worksheet.col_values(
        lead_id_column
    )

    for row_number, value in enumerate(
        values,
        start=1,
    ):

        if (
            str(value).strip()
            == str(lead_id).strip()
        ):

            return row_number

    return None


# =========================================================
# UPDATE LEAD
# =========================================================

def update_artist_lead(
    lead_id,
    status,
    notes,
):

    worksheet = (
        get_artist_leads_worksheet()
    )

    row_number = find_lead_row(
        lead_id
    )

    if not row_number:

        raise ValueError(
            f"Lead '{lead_id}' could not be found."
        )

    headers = [
        str(header).strip()
        for header
        in worksheet.row_values(1)
    ]

    row_values = worksheet.row_values(
        row_number
    )

    # Expand row so it matches number of headers.
    if len(row_values) < len(headers):

        row_values.extend(
            [""] * (
                len(headers)
                - len(row_values)
            )
        )

    row_data = dict(
        zip(
            headers,
            row_values,
        )
    )

    row_data["status"] = status
    row_data["notes"] = notes

    # -----------------------------------------------------
    # Optional tracking field
    # -----------------------------------------------------

    if (
        status == "Contacted"
        and "last_contacted_at"
        in headers
    ):

        row_data[
            "last_contacted_at"
        ] = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    updated_row = [
        row_data.get(
            header,
            "",
        )
        for header in headers
    ]

    worksheet.update(
        f"A{row_number}",
        [updated_row],
        value_input_option=(
            "USER_ENTERED"
        ),
    )


# =========================================================
# LEAD COUNTS
# =========================================================

def get_status_count(
    leads,
    status,
):

    if leads.empty:

        return 0

    if "status" not in leads.columns:

        return 0

    return int(
        leads[
            "status"
        ]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .eq(
            status.lower()
        )
        .sum()
    )


# =========================================================
# MAIN PAGE
# =========================================================

def show_artist_leads():

    st.title(
        "🎤 Artist Leads"
    )

    st.caption(
        "Manage artists who request access to the LAC Artist CRM."
    )

    # =====================================================
    # LOAD DATA
    # =====================================================

    try:

        with st.spinner(
            "Loading artist leads..."
        ):

            leads = (
                load_artist_leads()
            )

    except Exception as error:

        st.error(
            "Unable to load Artist Leads."
        )

        st.exception(
            error
        )

        return

    # =====================================================
    # EMPTY STATE
    # =====================================================

    if leads.empty:

        st.info(
            "No artist leads have been captured yet."
        )

        return

    # =====================================================
    # CLEAN DATA
    # =====================================================

    leads = leads.copy()

    text_columns = [
        "lead_id",
        "artist_name",
        "email",
        "whatsapp",
        "genre",
        "audience_size",
        "status",
        "source",
        "created_at",
        "notes",
    ]

    for column in text_columns:

        if column in leads.columns:

            leads[column] = (
                leads[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    leads["status"] = (
        leads["status"]
        .replace(
            "",
            "New",
        )
    )

    # =====================================================
    # KPI OVERVIEW
    # =====================================================

    st.subheader(
        "📊 Lead Pipeline"
    )

    c1, c2, c3, c4, c5 = (
        st.columns(5)
    )

    with c1:

        st.metric(
            "Total Leads",
            len(leads),
        )

    with c2:

        st.metric(
            "New",
            get_status_count(
                leads,
                "New",
            ),
        )

    with c3:

        st.metric(
            "Contacted",
            get_status_count(
                leads,
                "Contacted",
            ),
        )

    with c4:

        st.metric(
            "Demo Scheduled",
            get_status_count(
                leads,
                "Demo Scheduled",
            ),
        )

    with c5:

        st.metric(
            "Converted",
            get_status_count(
                leads,
                "Converted",
            ),
        )

    st.divider()

    # =====================================================
    # FILTERS
    # =====================================================

    st.subheader(
        "🔎 Find Artist Leads"
    )

    col1, col2, col3 = (
        st.columns(3)
    )

    search = col1.text_input(
        "Search",
        placeholder=(
            "Artist, email, WhatsApp..."
        ),
    )

    statuses = [
        "All Statuses"
    ] + LEAD_STATUSES

    selected_status = (
        col2.selectbox(
            "Status",
            statuses,
        )
    )

    genres = sorted(
        [
            value
            for value
            in leads[
                "genre"
            ].unique()
            if value
        ]
    )

    selected_genre = (
        col3.selectbox(
            "Genre",
            [
                "All Genres"
            ] + genres,
        )
    )

    # =====================================================
    # APPLY FILTERS
    # =====================================================

    filtered = (
        leads.copy()
    )

    if search:

        value = (
            search
            .strip()
            .lower()
        )

        mask = (
            filtered[
                "artist_name"
            ]
            .str.lower()
            .str.contains(
                value,
                na=False,
            )
            |
            filtered[
                "email"
            ]
            .str.lower()
            .str.contains(
                value,
                na=False,
            )
            |
            filtered[
                "whatsapp"
            ]
            .str.lower()
            .str.contains(
                value,
                na=False,
            )
        )

        filtered = filtered[
            mask
        ]

    if (
        selected_status
        != "All Statuses"
    ):

        filtered = filtered[
            filtered[
                "status"
            ]
            == selected_status
        ]

    if (
        selected_genre
        != "All Genres"
    ):

        filtered = filtered[
            filtered[
                "genre"
            ]
            == selected_genre
        ]

    # =====================================================
    # LEAD TABLE
    # =====================================================

    st.divider()

    st.subheader(
        f"🎵 Leads ({len(filtered)})"
    )

    if filtered.empty:

        st.info(
            "No artist leads match the current filters."
        )

    else:

        display_columns = [
            "artist_name",
            "genre",
            "audience_size",
            "email",
            "whatsapp",
            "status",
            "source",
            "created_at",
        ]

        available_columns = [
            column
            for column
            in display_columns
            if column
            in filtered.columns
        ]

        display = filtered[
            available_columns
        ].copy()

        rename_map = {
            "artist_name":
                "Artist",
            "genre":
                "Genre",
            "audience_size":
                "Audience Size",
            "email":
                "Email",
            "whatsapp":
                "WhatsApp",
            "status":
                "Status",
            "source":
                "Source",
            "created_at":
                "Created",
        }

        display = display.rename(
            columns=rename_map
        )

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
        )

    # =====================================================
    # LEAD MANAGEMENT
    # =====================================================

    if filtered.empty:

        return

    st.divider()

    st.subheader(
        "⚙️ Manage Lead"
    )

    lead_options = {}

    for _, row in (
        filtered.iterrows()
    ):

        lead_id = str(
            row.get(
                "lead_id",
                "",
            )
        ).strip()

        artist_name = str(
            row.get(
                "artist_name",
                "Unknown Artist",
            )
        ).strip()

        if not lead_id:

            continue

        label = (
            f"{artist_name} — {lead_id}"
        )

        lead_options[
            label
        ] = lead_id

    if not lead_options:

        st.info(
            "No leads with valid lead IDs are available."
        )

        return

    selected_label = (
        st.selectbox(
            "Select Artist Lead",
            list(
                lead_options.keys()
            ),
        )
    )

    selected_lead_id = (
        lead_options[
            selected_label
        ]
    )

    selected_rows = filtered[
        filtered[
            "lead_id"
        ]
        == selected_lead_id
    ]

    if selected_rows.empty:

        return

    lead = (
        selected_rows
        .iloc[0]
        .to_dict()
    )

    # =====================================================
    # LEAD DETAILS
    # =====================================================

    st.markdown(
        f"### 🎤 {lead.get('artist_name') or 'Artist'}"
    )

    detail1, detail2 = (
        st.columns(2)
    )

    with detail1:

        st.write(
            f"**Email:** "
            f"{lead.get('email') or '—'}"
        )

        st.write(
            f"**WhatsApp:** "
            f"{lead.get('whatsapp') or '—'}"
        )

        st.write(
            f"**Genre:** "
            f"{lead.get('genre') or '—'}"
        )

    with detail2:

        st.write(
            f"**Audience Size:** "
            f"{lead.get('audience_size') or '—'}"
        )

        st.write(
            f"**Status:** "
            f"{lead.get('status') or 'New'}"
        )

        st.write(
            f"**Created:** "
            f"{lead.get('created_at') or '—'}"
        )

    # =====================================================
    # UPDATE FORM
    # =====================================================

    current_status = (
        lead.get(
            "status",
            "New",
        )
        or "New"
    )

    if (
        current_status
        in LEAD_STATUSES
    ):

        status_index = (
            LEAD_STATUSES.index(
                current_status
            )
        )

    else:

        status_index = 0

    with st.form(
        "lead_management_form"
    ):

        new_status = (
            st.selectbox(
                "Update Status",
                LEAD_STATUSES,
                index=status_index,
            )
        )

        notes = st.text_area(
            "Notes",
            value=str(
                lead.get(
                    "notes",
                    "",
                )
            ),
            height=130,
            placeholder=(
                "Example: Interested in pilot. "
                "Call again on Monday."
            ),
        )

        save_changes = (
            st.form_submit_button(
                "💾 Save Changes",
                type="primary",
                use_container_width=True,
            )
        )

    if save_changes:

        try:

            with st.spinner(
                "Updating lead..."
            ):

                update_artist_lead(
                    lead_id=(
                        selected_lead_id
                    ),
                    status=new_status,
                    notes=notes,
                )

            st.success(
                "Artist lead updated successfully."
            )

            st.cache_resource.clear()

            st.rerun()

        except Exception as error:

            st.error(
                "Unable to update the artist lead."
            )

            st.exception(
                error
            )

    # =====================================================
    # OUTREACH HELP
    # =====================================================

    st.divider()

    st.subheader(
        "📲 Outreach"
    )

    artist_name = (
        lead.get(
            "artist_name",
            "Artist",
        )
        or "Artist"
    )

    whatsapp = (
        lead.get(
            "whatsapp",
            "",
        )
        or ""
    )

    email = (
        lead.get(
            "email",
            "",
        )
        or ""
    )

    message = (
        f"Hi {artist_name} 👋🏾\\n\\n"
        "Thank you for your interest in LAC Artist CRM. "
        "I'd love to show you how the platform helps artists "
        "understand their fans, build targeted audiences and "
        "turn fan relationships into revenue.\\n\\n"
        "Would you be available for a short demo?"
    )

    st.text_area(
        "Suggested WhatsApp Message",
        value=message,
        height=180,
    )

    if whatsapp:

        st.caption(
            f"WhatsApp contact: {whatsapp}"
        )

    if email:

        st.caption(
            f"Email contact: {email}"
        )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    show_artist_leads()