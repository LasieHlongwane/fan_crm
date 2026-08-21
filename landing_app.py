import time

import gspread
import pandas as pd
import streamlit as st

from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession

st.set_page_config(
    page_title="LAC Artist CRM | Turn Fans Into Relationships",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ARTIST_LEADS_SHEET = "Artist Leads"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_artist_leads_credentials():
    try:
        service_account_info = dict(
            st.secrets["gcp_service_account"]
        )
    except Exception as error:
        raise ValueError(
            "Google service-account credentials are not configured "
            "in Streamlit Secrets under [gcp_service_account]."
        ) from error

    if not service_account_info:
        raise ValueError(
            "Google service-account credentials in Streamlit Secrets are empty."
        )

    if service_account_info.get("type") != "service_account":
        raise ValueError(
            "The configured Google credentials are not service-account credentials."
        )

    return Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES,
    )


@st.cache_resource(show_spinner=False)
def get_artist_leads_client():
    credentials = get_artist_leads_credentials()
    session = AuthorizedSession(credentials)
    session.headers.update({"Connection": "keep-alive"})

    return gspread.Client(
        auth=credentials,
        session=session,
    )


@st.cache_resource(show_spinner=False)
def get_artist_leads_spreadsheet():
    try:
        spreadsheet_id = str(
            st.secrets["artist_leads"]["spreadsheet_id"]
        ).strip()
    except Exception as error:
        raise ValueError(
            "Artist Leads spreadsheet ID is not configured. "
            "Add [artist_leads] spreadsheet_id to Streamlit Secrets."
        ) from error

    if not spreadsheet_id:
        raise ValueError(
            "Artist Leads spreadsheet ID in Streamlit Secrets is empty."
        )

    last_error = None

    for attempt in range(3):
        try:
            client = get_artist_leads_client()
            return client.open_by_key(spreadsheet_id)

        except gspread.SpreadsheetNotFound as error:
            raise Exception(
                "The Artist Leads Google Sheet could not be accessed. "
                "Check the spreadsheet ID and make sure the service account "
                "has Editor access."
            ) from error

        except Exception as error:
            last_error = error
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))

    raise Exception(
        "Unable to connect to the Artist Leads Google Sheet "
        f"after 3 attempts: {last_error}"
    )


def save_artist_lead(
    artist_name,
    email,
    whatsapp,
    genre,
    fan_size,
):
    spreadsheet = get_artist_leads_spreadsheet()

    try:
        worksheet = spreadsheet.worksheet(
            ARTIST_LEADS_SHEET
        )
    except gspread.WorksheetNotFound as error:
        raise ValueError(
            "Worksheet 'Artist Leads' was not found. "
            "Create a worksheet with that exact name."
        ) from error

    headers = [
        str(header).strip()
        for header in worksheet.row_values(1)
    ]

    if not headers:
        raise ValueError(
            "The 'Artist Leads' worksheet has no header row."
        )

    required_headers = {
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
    }

    missing_headers = required_headers - set(headers)

    if missing_headers:
        raise ValueError(
            "Artist Leads sheet is missing required header(s): "
            + ", ".join(sorted(missing_headers))
        )

    lead_id = (
        "LEAD-"
        + pd.Timestamp.now().strftime("%Y%m%d%H%M%S%f")
    )

    lead = {
        "lead_id": lead_id,
        "artist_name": str(artist_name or "").strip(),
        "email": str(email or "").strip(),
        "whatsapp": str(whatsapp or "").strip(),
        "genre": str(genre or "").strip(),
        "audience_size": str(fan_size or "").strip(),
        "status": "New",
        "source": "Artist CRM Landing Page",
        "created_at": pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "notes": "",
    }

    row = [
        lead.get(header, "")
        for header in headers
    ]

    worksheet.append_row(
        row,
        value_input_option="USER_ENTERED",
    )

    return lead


st.markdown(
    '''
    <style>
    .stApp { background: #0b0b0b; color: white; }
    .block-container { max-width: 1200px; padding-top: 2rem; padding-bottom: 4rem; }
    .hero { text-align: center; padding: 70px 20px 60px; }
    .hero-label { font-size: 16px; font-weight: 600; margin-bottom: 20px; color: #c7c7c7; letter-spacing: 1px; }
    .hero h1 { font-size: 64px; line-height: 1.05; font-weight: 800; margin: 0 0 25px; }
    .hero h1 span { color: #ff4b4b; }
    .hero p { font-size: 21px; line-height: 1.6; color: #bdbdbd; max-width: 760px; margin: auto; }
    .section { padding: 70px 10px; }
    .section-title { text-align: center; font-size: 38px; font-weight: 750; margin-bottom: 15px; }
    .section-subtitle { text-align: center; color: #a8a8a8; font-size: 18px; margin-bottom: 45px; }
    .card { background: #151515; border: 1px solid #292929; border-radius: 16px; padding: 28px; min-height: 190px; margin-bottom: 15px; }
    .card-icon { font-size: 34px; margin-bottom: 12px; }
    .card-title { font-size: 21px; font-weight: 700; margin-bottom: 10px; }
    .card-text { color: #a9a9a9; line-height: 1.6; }
    .workflow { background: #151515; border: 1px solid #292929; border-radius: 20px; padding: 40px; text-align: center; }
    .workflow-step { font-size: 18px; font-weight: 600; padding: 15px; }
    .workflow-arrow { color: #777; font-size: 25px; }
    .cta { background: #151515; border: 1px solid #292929; border-radius: 24px; padding: 60px 30px; text-align: center; margin-top: 40px; }
    .cta h2 { font-size: 42px; margin: 0 0 15px; }
    .cta p { color: #aaa; font-size: 18px; max-width: 700px; margin: auto; }
    .footer { text-align: center; color: #777; padding: 50px 10px 20px; border-top: 1px solid #242424; margin-top: 60px; }
    @media (max-width: 768px) {
        .hero h1 { font-size: 42px; }
        .section-title { font-size: 30px; }
        .cta h2 { font-size: 32px; }
    }
    </style>
    ''',
    unsafe_allow_html=True,
)


def show_card(icon, title, description):
    st.markdown(
        f'''
        <div class="card">
            <div class="card-icon">{icon}</div>
            <div class="card-title">{title}</div>
            <div class="card-text">{description}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


nav1, nav2, nav3 = st.columns([2, 1, 1])

with nav1:
    st.markdown("### 🎵 LAC Artist CRM")


st.divider()

st.html(
    '''
    <div class="hero">
        <div class="hero-label">
            AUDIENCE → RELATIONSHIPS → REVENUE
        </div>
        <h1>
            Turn your audience into
            <span>real fan relationships.</span>
        </h1>
        <p>
            Artist CRM helps independent artists understand their fans,
            build targeted audiences, launch campaigns and turn fan
            relationships into revenue.
        </p>
    </div>
    '''
)

hero1, hero2, hero3 = st.columns([1, 1, 1])


st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown(
    '<div class="section-title">Followers are not the same as fans.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '''
    <p class="section-subtitle">
        Social media tells you how many people follow you.
        Artist CRM helps you understand who they actually are.
    </p>
    ''',
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)

problem1, problem2, problem3 = st.columns(3)

with problem1:
    show_card(
        "📱",
        "Scattered Fan Data",
        "Fan information can be spread across social media, WhatsApp, "
        "events, spreadsheets and conversations.",
    )

with problem2:
    show_card(
        "👥",
        "Everyone Gets the Same Message",
        "Not every fan wants the same thing. Some want music, some want "
        "events and some want merchandise.",
    )

with problem3:
    show_card(
        "💰",
        "Missed Opportunities",
        "Without audience intelligence, valuable fans can easily be overlooked.",
    )

st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown(
    '<div class="section-title">Understand your audience.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-subtitle">'
    'Artist CRM turns fan information into actionable audiences.'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)

features = [
    ("🔥", "Superfans", "Identify your most engaged supporters."),
    ("💎", "VIP Fans", "Find fans who are both highly engaged and valuable."),
    ("💰", "Potential Buyers", "Find engaged fans who have not purchased yet."),
    ("🎵", "Song Intelligence", "Understand which songs resonate with your audience."),
    ("🎟️", "Event Audiences", "Identify fans interested in attending events."),
    ("👕", "Audience Interests", "Understand brand and fashion interests."),
]

for start in range(0, len(features), 3):
    columns = st.columns(3)
    for column, feature in zip(
        columns,
        features[start:start + 3],
    ):
        with column:
            show_card(*feature)

st.html(
    '''
    <div class="section">
        <div class="section-title">From fan data to action.</div>
        <div class="section-subtitle">
            Stop guessing who to contact. Build audiences and act on them.
        </div>
        <div class="workflow">
            <div class="workflow-step">👤 Fan Data</div>
            <div class="workflow-arrow">↓</div>
            <div class="workflow-step">🧠 Audience Intelligence</div>
            <div class="workflow-arrow">↓</div>
            <div class="workflow-step">🎯 Target Audience</div>
            <div class="workflow-arrow">↓</div>
            <div class="workflow-step">📢 Campaign</div>
            <div class="workflow-arrow">↓</div>
            <div class="workflow-step">📱 WhatsApp / Email / SMS</div>
            <div class="workflow-arrow">↓</div>
            <div class="workflow-step">💰 Results &amp; Revenue</div>
        </div>
    </div>
    '''
)

st.html(
    '''
    <div class="cta">
        <h2>Your followers are already there.</h2>
        <p>
            The next step is understanding them, building relationships
            with them and giving them a reason to support you.
        </p>
    </div>
    '''
)

st.write("")

cta1, cta2, cta3 = st.columns([1, 1, 1])

with cta2:
    if st.button(
        "🎵 Join the Artist CRM",
        use_container_width=True,
        type="primary",
        key="cta_join",
    ):
        st.session_state["show_form"] = True

if st.session_state.get("show_form", False):
    st.divider()
    st.markdown("## 🚀 Join the Artist CRM Pilot")
    st.write(
        "Tell us a little about yourself and we'll contact you."
    )

    with st.form(
        "artist_pilot_form",
        clear_on_submit=False,
    ):
        name = st.text_input("Artist / Stage Name")
        email = st.text_input("Email")
        whatsapp = st.text_input("WhatsApp Number")
        genre = st.text_input("Music Genre")

        fan_size = st.selectbox(
            "Approximate Audience Size",
            [
                "Less than 500",
                "500 – 2,000",
                "2,000 – 10,000",
                "10,000 – 50,000",
                "50,000+",
            ],
        )

        submitted = st.form_submit_button(
            "Submit Pilot Request",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        clean_name = name.strip()
        clean_email = email.strip()
        clean_whatsapp = whatsapp.strip()

        if not clean_name:
            st.error(
                "Please enter your artist/stage name."
            )

        elif not clean_email and not clean_whatsapp:
            st.error(
                "Please provide an email or WhatsApp number."
            )

        else:
            try:
                with st.spinner(
                    "Submitting your request..."
                ):
                    lead = save_artist_lead(
                        artist_name=clean_name,
                        email=clean_email,
                        whatsapp=clean_whatsapp,
                        genre=genre,
                        fan_size=fan_size,
                    )

                st.success(
                    "Thank you! Your pilot request has been received."
                )

                st.info(
                    "We will contact you to arrange a short demo."
                )

                st.caption(
                    f"Reference: {lead['lead_id']}"
                )

            except Exception as error:
                st.error(
                    "Your request could not be saved to "
                    "the Artist Leads Google Sheet."
                )
                st.exception(error)

st.markdown(
    '''
    <div class="footer">
        🎵 <strong>LAC Artist CRM</strong>
        <br><br>
        Audience → Relationships → Revenue
        <br><br>
        Built for independent artists.
    </div>
    ''',
    unsafe_allow_html=True,
)