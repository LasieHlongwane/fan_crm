import json
import os
import time
import uuid
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession


# =========================================================
# CONFIGURATION
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ---------------------------------------------------------
# IMPORTANT
#
# Set your Artist Leads spreadsheet ID here.
#
# Example:
#
# https://docs.google.com/spreadsheets/d/ABC123XYZ/edit
#
# Spreadsheet ID:
#
# ABC123XYZ
# ---------------------------------------------------------

ARTIST_LEADS_SPREADSHEET_ID = os.getenv(
    "ARTIST_LEADS_SPREADSHEET_ID",
    "",
)

CREDENTIALS_FILE = "credentials.json"

LEADS_SHEET = "Artist Leads"


# =========================================================
# GET CREDENTIALS
# =========================================================

def get_artist_leads_credentials():

    if not os.path.exists(
        CREDENTIALS_FILE
    ):

        raise FileNotFoundError(
            "credentials.json was not found."
        )

    with open(
        CREDENTIALS_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        credentials_data = json.load(file)

    if (
        credentials_data.get("type")
        != "service_account"
    ):

        raise ValueError(
            "credentials.json is not a "
            "service-account file."
        )

    return Credentials.from_service_account_info(
        credentials_data,
        scopes=SCOPES,
    )


# =========================================================
# GET GOOGLE CLIENT
# =========================================================

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
# GET SPREADSHEET
# =========================================================

def get_artist_leads_spreadsheet():

    if not ARTIST_LEADS_SPREADSHEET_ID:

        raise ValueError(
            "ARTIST_LEADS_SPREADSHEET_ID is not configured."
        )

    last_error = None

    for attempt in range(3):

        try:

            client = (
                get_artist_leads_client()
            )

            return client.open_by_key(
                ARTIST_LEADS_SPREADSHEET_ID
            )

        except (
            gspread.SpreadsheetNotFound,
        ) as error:

            raise Exception(
                "Could not access the Artist Leads "
                "Google Spreadsheet. Make sure the "
                "spreadsheet ID is correct and that "
                "the service account has Editor access."
            ) from error

        except Exception as error:

            last_error = error

            if attempt < 2:

                time.sleep(
                    1.5 * (attempt + 1)
                )

    raise Exception(
        "Unable to connect to Artist Leads "
        f"Google Sheets after 3 attempts: "
        f"{last_error}"
    )


# =========================================================
# GET ARTIST LEADS WORKSHEET
# =========================================================

def get_artist_leads_worksheet():

    spreadsheet = (
        get_artist_leads_spreadsheet()
    )

    try:

        return spreadsheet.worksheet(
            LEADS_SHEET
        )

    except gspread.WorksheetNotFound as error:

        raise Exception(
            "The 'Artist Leads' worksheet was "
            "not found. Create a worksheet named "
            "'Artist Leads'."
        ) from error


# =========================================================
# GENERATE LEAD ID
# =========================================================

def generate_lead_id():

    return (
        "LEAD-"
        + uuid.uuid4()
        .hex[:8]
        .upper()
    )


# =========================================================
# CREATE ARTIST LEAD
# =========================================================

def create_artist_lead(
    artist_name,
    email,
    whatsapp_number,
    music_genre,
    audience_size,
):

    artist_name = str(
        artist_name or ""
    ).strip()

    email = str(
        email or ""
    ).strip()

    whatsapp_number = str(
        whatsapp_number or ""
    ).strip()

    music_genre = str(
        music_genre or ""
    ).strip()

    audience_size = str(
        audience_size or ""
    ).strip()

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    if not artist_name:

        raise ValueError(
            "Artist / Stage Name is required."
        )

    if (
        not email
        and not whatsapp_number
    ):

        raise ValueError(
            "An email address or WhatsApp "
            "number is required."
        )

    # -----------------------------------------------------
    # Create lead
    # -----------------------------------------------------

    lead = {

        "lead_id":
            generate_lead_id(),

        "artist_name":
            artist_name,

        "email":
            email,

        "whatsapp_number":
            whatsapp_number,

        "music_genre":
            music_genre,

        "audience_size":
            audience_size,

        "source":
            "Landing Page",

        "status":
            "New",

        "created_at":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "last_contacted_at":
            "",

        "notes":
            "",
    }

    # -----------------------------------------------------
    # Get worksheet
    # -----------------------------------------------------

    worksheet = (
        get_artist_leads_worksheet()
    )

    # -----------------------------------------------------
    # Read headers
    # -----------------------------------------------------

    headers = (
        worksheet.row_values(1)
    )

    if not headers:

        raise Exception(
            "The 'Artist Leads' worksheet "
            "does not contain headers in row 1."
        )

    # -----------------------------------------------------
    # Build row according to sheet headers
    # -----------------------------------------------------

    row = []

    for header in headers:

        row.append(
            lead.get(
                header,
                "",
            )
        )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    worksheet.append_row(
        row,
        value_input_option="USER_ENTERED",
    )

    return lead