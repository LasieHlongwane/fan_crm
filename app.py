# app.py

import importlib
import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Artist CRM",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🎵 Artist CRM")

st.sidebar.caption(
    "Audience → Relationships → Revenue"
)

st.sidebar.divider()


# =========================================================
# NAVIGATION OPTIONS
# =========================================================

NAVIGATION_OPTIONS = [
    "Dashboard",
    "Fans",
    "Fan Profile",
    "Audience Actions",
    "Segmentation",
    "Campaign Builder",
    "Campaigns",
    "Campaign Execution",
    "Campaign Performance",
    "Revenue",
    "Analytics",
    "Artist Leads",
]


# =========================================================
# HANDLE PROGRAMMATIC NAVIGATION
# =========================================================

if "navigation_target" not in st.session_state:

    st.session_state[
        "navigation_target"
    ] = None


navigation_target = st.session_state.get(
    "navigation_target"
)


# =========================================================
# SIDEBAR RADIO
# =========================================================

default_index = 0

if navigation_target in NAVIGATION_OPTIONS:

    default_index = NAVIGATION_OPTIONS.index(
        navigation_target
    )

    # Clear target after consuming it

    st.session_state[
        "navigation_target"
    ] = None


page = st.sidebar.radio(
    "Navigation",
    NAVIGATION_OPTIONS,
    index=default_index,
)


# =========================================================
# PAGE HANDLERS
# =========================================================

PAGE_HANDLERS = {

    "Dashboard":
        (
            "pages.dashboard",
            "show_dashboard",
        ),

    "Fans":
        (
            "pages.fans",
            "show_fans",
        ),

    "Fan Profile":
        (
            "pages.fan_profile",
            "show_fan_profile",
        ),

    "Audience Actions":
        (
            "pages.audience_actions",
            "show_audience_actions",
        ),

    "Segmentation":
        (
            "pages.segmentation",
            "show_segmentation",
        ),

    "Campaign Builder":
        (
            "pages.campaign_builder",
            "show_campaign_builder",
        ),

    "Campaigns":
        (
            "pages.campaigns",
            "show_campaigns",
        ),

    "Campaign Execution":
        (
            "pages.campaign_execution",
            "show_campaign_execution",
        ),

    "Campaign Performance":
        (
            "pages.campaign_performance",
            "show_campaign_performance",
        ),

    "Revenue":
        (
            "pages.revenue",
            "show_revenue",
        ),

    "Analytics":
        (
            "pages.audience_analytics",
            "show_analytics",
        ),

    "Artist Leads": 
        (
            "pages.artist_leads",
            "show_artist_leads",
        ),
}


# =========================================================
# LOAD PAGE
# =========================================================

def load_page_handler(
    page_name,
):

    module_name, function_name = (
        PAGE_HANDLERS[
            page_name
        ]
    )

    module = importlib.import_module(
        module_name
    )

    handler = getattr(
        module,
        function_name,
    )

    if not callable(handler):

        raise TypeError(
            f"{function_name} in "
            f"{module_name} is not callable."
        )

    return handler


# =========================================================
# RUN PAGE
# =========================================================

try:

    handler = load_page_handler(
        page
    )

    handler()

except Exception as error:

    st.error(
        f"Unable to load the {page} page."
    )

    st.exception(
        error
    )