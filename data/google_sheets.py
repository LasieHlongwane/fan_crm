import json
import os
import time

import gspread
import pandas as pd

from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession


# =========================================================
# CONFIGURATION
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = (
    "1nlElm-0N6jVrFj3klk8CKLL1GcONILakhU1cPVSn-zw"
)

CREDENTIALS_FILE = "credentials.json"

# Google API request timeout.
#
# Tuple:
#   connect timeout
#   read timeout
#
REQUEST_TIMEOUT = (
    15,
    60,
)

MAX_RETRIES = 4


# =========================================================
# OPTIONAL STREAMLIT CACHE
# =========================================================
#
# Streamlit reruns the script frequently.
#
# Without caching, every interaction can potentially create
# another Google API client/session.
#
# We cache the client when Streamlit is available.
#


try:

    import streamlit as st

    CACHE_AVAILABLE = True

except Exception:

    st = None

    CACHE_AVAILABLE = False


# =========================================================
# LOAD CREDENTIALS
# =========================================================

def load_credentials_data():

    # -----------------------------------------------------
    # Local development
    # -----------------------------------------------------

    if os.path.exists(
        CREDENTIALS_FILE
    ):

        with open(
            CREDENTIALS_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    # -----------------------------------------------------
    # Streamlit Cloud
    # -----------------------------------------------------
    #
    # If credentials are stored in Streamlit secrets,
    # support:
    #
    # [gcp_service_account]
    #
    # This avoids requiring credentials.json on Cloud.
    #

    if CACHE_AVAILABLE:

        try:

            if "gcp_service_account" in st.secrets:

                return dict(
                    st.secrets[
                        "gcp_service_account"
                    ]
                )

        except Exception:

            pass

    raise FileNotFoundError(
        "Google service-account credentials were not found. "
        "For local development, place credentials.json in "
        "the project root. For Streamlit Cloud, configure "
        "the [gcp_service_account] secret."
    )


# =========================================================
# CREATE GOOGLE CLIENT
# =========================================================

def _create_google_client():

    credentials_data = (
        load_credentials_data()
    )

    if credentials_data.get(
        "type"
    ) != "service_account":

        raise ValueError(
            "Google credentials must be a "
            "service-account credentials file."
        )

    credentials = (
        Credentials.from_service_account_info(
            credentials_data,
            scopes=SCOPES,
        )
    )

    # -----------------------------------------------------
    # Create authorized HTTP session
    # -----------------------------------------------------

    session = AuthorizedSession(
        credentials
    )

    # -----------------------------------------------------
    # Do NOT force Connection: keep-alive
    #
    # Google/requests handles connection pooling itself.
    # Leaving this header out avoids forcing reuse of a
    # connection that may have already been closed.
    # -----------------------------------------------------

    client = gspread.Client(
        auth=credentials,
        session=session,
    )

    # -----------------------------------------------------
    # Configure gspread timeout
    # -----------------------------------------------------

    try:

        client.set_timeout(
            REQUEST_TIMEOUT
        )

    except Exception:

        # Older gspread versions may not support
        # tuple timeouts in the same way.
        #
        # Continue using the default behaviour.
        pass

    return client


# =========================================================
# GET GOOGLE CLIENT
# =========================================================

if CACHE_AVAILABLE:

    @st.cache_resource(
        show_spinner=False
    )
    def get_google_client():

        return _create_google_client()

else:

    def get_google_client():

        return _create_google_client()


# =========================================================
# TRANSIENT ERROR DETECTION
# =========================================================

def is_transient_error(error):

    """
    Determine whether an error is likely temporary.

    Examples:

    - SSL EOF
    - Connection reset
    - Connection aborted
    - Timeout
    - Temporary network failure
    - 429 rate limiting
    - 5xx Google server errors
    """

    error_text = str(
        error
    ).lower()

    transient_messages = [

        "ssleoferror",

        "sslzero",

        "unexpected_eof",

        "connection reset",

        "connection aborted",

        "connection broken",

        "remote disconnected",

        "max retries exceeded",

        "timed out",

        "timeout",

        "temporarily unavailable",

        "service unavailable",

        "bad gateway",

        "gateway timeout",

        "internal server error",

        "too many requests",

        "429",

        "500",

        "502",

        "503",

        "504",
    ]

    return any(
        message in error_text
        for message in transient_messages
    )


# =========================================================
# RETRY DELAY
# =========================================================

def retry_delay(
    attempt
):

    # 1.5
    # 3
    # 6
    # 12

    return min(
        1.5 * (2 ** attempt),
        12,
    )


# =========================================================
# OPEN SPREADSHEET
# =========================================================

def get_spreadsheet():

    last_error = None

    for attempt in range(
        MAX_RETRIES
    ):

        try:

            client = (
                get_google_client()
            )

            spreadsheet = (
                client.open_by_key(
                    SPREADSHEET_ID
                )
            )

            return spreadsheet

        except gspread.SpreadsheetNotFound as e:

            raise Exception(
                "Could not access the Artist Fan CRM "
                "Google Sheet.\n\n"
                "Check that:\n"
                "1. The spreadsheet ID is correct.\n"
                "2. The service-account email has Editor "
                "access to the spreadsheet.\n"
                "3. Google Sheets API and Google Drive API "
                "are enabled."
            ) from e

        except Exception as e:

            last_error = e

            # -------------------------------------------------
            # If this isn't a transient error, don't keep
            # hammering Google.
            # -------------------------------------------------

            if not is_transient_error(e):

                break

            # -------------------------------------------------
            # Clear cached client after network failure.
            #
            # This forces the next attempt to create a fresh
            # HTTP session rather than potentially reusing a
            # broken connection.
            # -------------------------------------------------

            if CACHE_AVAILABLE:

                try:

                    get_google_client.clear()

                except Exception:

                    pass

            if attempt < (
                MAX_RETRIES - 1
            ):

                time.sleep(
                    retry_delay(
                        attempt
                    )
                )

    raise Exception(
        "Unable to connect to Google Sheets "
        f"after {MAX_RETRIES} attempts: "
        f"{last_error}"
    )


# =========================================================
# GET WORKSHEET
# =========================================================

def get_worksheet(
    sheet_name: str,
):

    spreadsheet = (
        get_spreadsheet()
    )

    try:

        return spreadsheet.worksheet(
            sheet_name
        )

    except gspread.WorksheetNotFound as e:

        raise Exception(
            f"Worksheet '{sheet_name}' was not found "
            "inside the Artist Fan CRM spreadsheet."
        ) from e


# =========================================================
# CONVERT VALUES TO DATAFRAME
# =========================================================

def values_to_dataframe(
    values
):

    if not values:

        return pd.DataFrame()

    # -----------------------------------------------------
    # First row = headers
    # -----------------------------------------------------

    headers = [
        str(header).strip()
        for header in values[0]
    ]

    if not any(headers):

        return pd.DataFrame()

    data_rows = values[1:]

    # -----------------------------------------------------
    # Google Sheets rows may have different lengths.
    # Normalize them to the header length.
    # -----------------------------------------------------

    normalized_rows = []

    for row in data_rows:

        row = list(row)

        if len(row) < len(headers):

            row.extend(
                [""] *
                (
                    len(headers)
                    - len(row)
                )
            )

        elif len(row) > len(headers):

            row = row[
                :len(headers)
            ]

        normalized_rows.append(
            row
        )

    return pd.DataFrame(
        normalized_rows,
        columns=headers,
    )


# =========================================================
# READ SHEET
# =========================================================

def read_sheet(
    sheet_name: str,
) -> pd.DataFrame:

    last_error = None

    for attempt in range(
        MAX_RETRIES
    ):

        try:

            worksheet = (
                get_worksheet(
                    sheet_name
                )
            )

            # -------------------------------------------------
            # Read the sheet values directly.
            #
            # This avoids get_all_records()'s additional
            # header/record processing.
            # -------------------------------------------------

            values = (
                worksheet.get_all_values()
            )

            return values_to_dataframe(
                values
            )

        except Exception as e:

            last_error = e

            if not is_transient_error(e):

                break

            if CACHE_AVAILABLE:

                try:

                    get_google_client.clear()

                except Exception:

                    pass

            if attempt < (
                MAX_RETRIES - 1
            ):

                time.sleep(
                    retry_delay(
                        attempt
                    )
                )

    raise Exception(
        f"Unable to read worksheet "
        f"'{sheet_name}': "
        f"{last_error}"
    )


# =========================================================
# ADD ROW
# =========================================================

def add_row(
    sheet_name: str,
    row_data: dict,
):

    last_error = None

    for attempt in range(
        MAX_RETRIES
    ):

        try:

            worksheet = (
                get_worksheet(
                    sheet_name
                )
            )

            headers = (
                worksheet.row_values(1)
            )

            row = []

            for header in headers:

                row.append(
                    row_data.get(
                        header,
                        "",
                    )
                )

            worksheet.append_row(
                row,
                value_input_option=(
                    "USER_ENTERED"
                ),
            )

            return

        except Exception as e:

            last_error = e

            if not is_transient_error(e):

                break

            if CACHE_AVAILABLE:

                try:

                    get_google_client.clear()

                except Exception:

                    pass

            if attempt < (
                MAX_RETRIES - 1
            ):

                time.sleep(
                    retry_delay(
                        attempt
                    )
                )

    raise Exception(
        f"Unable to add row to "
        f"'{sheet_name}': "
        f"{last_error}"
    )


# =========================================================
# UPDATE ROW
# =========================================================

def update_row(
    sheet_name: str,
    row_number: int,
    row_data: dict,
):

    last_error = None

    for attempt in range(
        MAX_RETRIES
    ):

        try:

            worksheet = (
                get_worksheet(
                    sheet_name
                )
            )

            headers = (
                worksheet.row_values(1)
            )

            row = []

            for header in headers:

                row.append(
                    row_data.get(
                        header,
                        "",
                    )
                )

            worksheet.update(
                f"A{row_number}",
                [row],
                value_input_option=(
                    "USER_ENTERED"
                ),
            )

            return

        except Exception as e:

            last_error = e

            if not is_transient_error(e):

                break

            if CACHE_AVAILABLE:

                try:

                    get_google_client.clear()

                except Exception:

                    pass

            if attempt < (
                MAX_RETRIES - 1
            ):

                time.sleep(
                    retry_delay(
                        attempt
                    )
                )

    raise Exception(
        f"Unable to update row "
        f"{row_number} in "
        f"'{sheet_name}': "
        f"{last_error}"
    )


# =========================================================
# GET FAN BY ID
# =========================================================

def get_fan_by_id(
    fan_id: str,
):

    fans = read_sheet(
        "Fans"
    )

    if fans.empty:

        return None

    if "fan_id" not in fans.columns:

        return None

    matches = fans[
        fans["fan_id"]
        .astype(str)
        .str.lower()
        ==
        str(fan_id)
        .lower()
    ]

    if matches.empty:

        return None

    return (
        matches
        .iloc[0]
        .to_dict()
    )


# =========================================================
# GET FAN INTERACTIONS
# =========================================================

def get_fan_interactions(
    fan_id: str,
) -> pd.DataFrame:

    interactions = read_sheet(
        "Interactions"
    )

    if interactions.empty:

        return pd.DataFrame()

    if "fan_id" not in interactions.columns:

        return pd.DataFrame()

    return interactions[
        interactions["fan_id"]
        .astype(str)
        .str.lower()
        ==
        str(fan_id)
        .lower()
    ]


# =========================================================
# GET FAN PURCHASES
# =========================================================

def get_fan_purchases(
    fan_id: str,
) -> pd.DataFrame:

    purchases = read_sheet(
        "Purchases"
    )

    if purchases.empty:

        return pd.DataFrame()

    if "fan_id" not in purchases.columns:

        return pd.DataFrame()

    return purchases[
        purchases["fan_id"]
        .astype(str)
        .str.lower()
        ==
        str(fan_id)
        .lower()
    ]