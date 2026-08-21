import uuid
from datetime import datetime

import pandas as pd

from data.google_sheets import (
    read_sheet,
    add_row,
)


# =========================================================
# GOOGLE SHEET NAMES
# =========================================================

FORM_SHEET = "Form responses 1"
FANS_SHEET = "Fans"


# =========================================================
# FAN ID
# =========================================================

def generate_fan_id(existing_ids=None):

    """
    Generate a unique FAN-ID.

    Example:

        FAN-7A83F21C
    """

    existing_ids = set(
        str(x).strip().upper()
        for x in (existing_ids or [])
        if str(x).strip()
    )

    while True:

        fan_id = (
            "FAN-"
            + uuid.uuid4().hex[:8].upper()
        )

        if fan_id not in existing_ids:

            return fan_id


# =========================================================
# CLEAN VALUES
# =========================================================

def clean(value):

    """
    Convert Google Sheet values into
    clean strings.
    """

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip()


# =========================================================
# NORMALIZE EMAIL
# =========================================================

def normalize_email(email):

    return clean(email).lower()


# =========================================================
# NORMALIZE PHONE
# =========================================================

def normalize_phone(phone):

    phone = clean(phone)

    if not phone:
        return ""

    # Remove spaces
    phone = phone.replace(" ", "")

    # Remove common formatting
    phone = phone.replace("-", "")
    phone = phone.replace("(", "")
    phone = phone.replace(")", "")

    return phone


# =========================================================
# DUPLICATE CHECK
# =========================================================

def build_duplicate_sets(fans):

    """
    Create sets containing existing
    emails and phone numbers.

    This makes duplicate detection
    much faster.
    """

    emails = set()
    phones = set()

    if fans.empty:

        return emails, phones

    if "email" in fans.columns:

        for value in fans["email"]:

            email = normalize_email(value)

            if email:

                emails.add(email)

    if "phone" in fans.columns:

        for value in fans["phone"]:

            phone = normalize_phone(value)

            if phone:

                phones.add(phone)

    return emails, phones


# =========================================================
# ENGAGEMENT SCORE
# =========================================================

def calculate_initial_score(row):

    """
    Calculate an initial fan engagement score.

    This is intentionally simple for the MVP.
    """

    score = 10

    email = normalize_email(
        row.get("Email", "")
    )

    phone = normalize_phone(
        row.get("WhatsApp Number", "")
    )

    notifications = clean(
        row.get(
            "Would you like notification about",
            "",
        )
    )

    brand = clean(
        row.get(
            "Fashion Brands Interested In",
            "",
        )
    )

    source = clean(
        row.get(
            "How did you discover my music",
            "",
        )
    )

    # Email
    if email:

        score += 5

    # WhatsApp
    if phone:

        score += 5

    # Notification preference
    if notifications:

        score += 10

    # Brand interest
    if brand:

        score += 5

    # Discovery source
    if source:

        score += 5

    return min(score, 100)


# =========================================================
# FAN STATUS
# =========================================================

def determine_fan_status(score):

    if score >= 76:

        return "VIP"

    if score >= 51:

        return "Loyal"

    if score >= 21:

        return "Engaged"

    return "New"


# =========================================================
# BUILD FAN RECORD
# =========================================================

def build_fan_record(
    form_row,
    fan_id,
):

    score = calculate_initial_score(
        form_row
    )

    status = determine_fan_status(
        score
    )

    timestamp = clean(
        form_row.get(
            "Timestamp",
            "",
        )
    )

    if not timestamp:

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    fan = {

        "fan_id": fan_id,

        "name": clean(
            form_row.get(
                "Name",
                "",
            )
        ),

        "email": normalize_email(
            form_row.get(
                "Email",
                "",
            )
        ),

        "phone": normalize_phone(
            form_row.get(
                "WhatsApp Number",
                "",
            )
        ),

        "location": clean(
            form_row.get(
                "City",
                "",
            )
        ),

        "age_group": clean(
            form_row.get(
                "Age Range",
                "",
            )
        ),

        # These are not currently
        # collected by the form.

        "favorite_song": "",

        "favorite_artist": "",

        "favorite_brand": clean(
            form_row.get(
                "Fashion Brands Interested In",
                "",
            )
        ),

        "source": clean(
            form_row.get(
                "How did you discover my music",
                "",
            )
        ),

        "consent": "Yes",

        "fan_status": status,

        "engagement_score": score,

        "total_spend": 0,

        "last_interaction": "",

        "created_at": timestamp,

        "notification_preferences": clean(
            form_row.get(
                "Would you like notification about",
                "",
            )
        ),
    }

    return fan


# =========================================================
# VALIDATE FORM RESPONSE
# =========================================================

def validate_form_response(row):

    """
    Basic validation before importing.
    """

    name = clean(
        row.get("Name", "")
    )

    email = normalize_email(
        row.get("Email", "")
    )

    phone = normalize_phone(
        row.get("WhatsApp Number", "")
    )

    if not name:

        return False, "Name is missing."

    if not email and not phone:

        return (
            False,
            "Email or WhatsApp number is required.",
        )

    return True, ""


# =========================================================
# IMPORT ALL FANS
# =========================================================

def import_all_fans():

    """
    Import new Google Form responses
    into the Fans worksheet.
    """

    # -----------------------------------------------------
    # Read Google Form responses
    # -----------------------------------------------------

    form_responses = read_sheet(
        FORM_SHEET
    )

    # -----------------------------------------------------
    # Read existing fans
    # -----------------------------------------------------

    fans = read_sheet(
        FANS_SHEET
    )

    # -----------------------------------------------------
    # Empty form
    # -----------------------------------------------------

    if form_responses.empty:

        return {

            "imported": 0,

            "duplicates": 0,

            "errors": 0,

            "messages": [
                "No Google Form responses found."
            ],
        }

    # -----------------------------------------------------
    # Existing identifiers
    # -----------------------------------------------------

    existing_emails, existing_phones = (
        build_duplicate_sets(fans)
    )

    existing_ids = set()

    if (
        not fans.empty
        and "fan_id" in fans.columns
    ):

        existing_ids = set(
            str(value).strip().upper()
            for value in fans["fan_id"]
            if str(value).strip()
        )

    # -----------------------------------------------------
    # Counters
    # -----------------------------------------------------

    imported = 0

    duplicates = 0

    errors = 0

    messages = []

    # -----------------------------------------------------
    # Process each Google Form row
    # -----------------------------------------------------

    for index, row in form_responses.iterrows():

        try:

            row_data = row.to_dict()

            # ---------------------------------------------
            # Validate
            # ---------------------------------------------

            valid, error_message = (
                validate_form_response(
                    row_data
                )
            )

            if not valid:

                errors += 1

                messages.append(
                    f"Row {index + 2}: "
                    f"{error_message}"
                )

                continue

            # ---------------------------------------------
            # Normalize identifiers
            # ---------------------------------------------

            email = normalize_email(
                row_data.get(
                    "Email",
                    "",
                )
            )

            phone = normalize_phone(
                row_data.get(
                    "WhatsApp Number",
                    "",
                )
            )

            # ---------------------------------------------
            # Duplicate check - EMAIL
            # ---------------------------------------------

            email_duplicate = (
                email
                and email in existing_emails
            )

            # ---------------------------------------------
            # Duplicate check - PHONE
            # ---------------------------------------------

            phone_duplicate = (
                phone
                and phone in existing_phones
            )

            if (
                email_duplicate
                or phone_duplicate
            ):

                duplicates += 1

                name = clean(
                    row_data.get(
                        "Name",
                        "",
                    )
                )

                messages.append(
                    f"Skipped duplicate: {name}"
                )

                continue

            # ---------------------------------------------
            # Generate ID
            # ---------------------------------------------

            fan_id = generate_fan_id(
                existing_ids
            )

            existing_ids.add(
                fan_id
            )

            # ---------------------------------------------
            # Build fan
            # ---------------------------------------------

            fan = build_fan_record(
                row_data,
                fan_id,
            )

            # ---------------------------------------------
            # Save fan
            # ---------------------------------------------

            add_row(
                FANS_SHEET,
                fan,
            )

            imported += 1

            # ---------------------------------------------
            # Update duplicate indexes
            #
            # This is important:
            #
            # If two identical new form submissions
            # exist in the SAME import run, the second
            # one will now be detected.
            # ---------------------------------------------

            if email:

                existing_emails.add(
                    email
                )

            if phone:

                existing_phones.add(
                    phone
                )

            messages.append(
                f"Imported: {fan['name']} "
                f"({fan_id})"
            )

        except Exception as e:

            errors += 1

            messages.append(
                f"Row {index + 2} failed: {e}"
            )

    # -----------------------------------------------------
    # Result
    # -----------------------------------------------------

    return {

        "imported": imported,

        "duplicates": duplicates,

        "errors": errors,

        "messages": messages,
    }