# pages/segmentation.py

import streamlit as st
import pandas as pd

from data.google_sheets import read_sheet

from audience_segmentation import (
    get_segments,
    get_segment_counts,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

PAGE_TITLE = "🎯 Audience Segmentation"


# =========================================================
# LOAD FANS
# =========================================================

def load_fans():

    try:

        return read_sheet("Fans")

    except Exception as error:

        st.error(
            f"Unable to load fan data: {error}"
        )

        return pd.DataFrame()


# =========================================================
# GET ANALYTICS SELECTED SEGMENT
# =========================================================

def get_selected_segment():

    return st.session_state.get(
        "selected_segment"
    )


# =========================================================
# CLEAR SELECTED SEGMENT
# =========================================================

def clear_selected_segment():

    if (
        "selected_segment"
        in st.session_state
    ):

        del st.session_state[
            "selected_segment"
        ]

    if (
        "analytics_selected_segment"
        in st.session_state
    ):

        del st.session_state[
            "analytics_selected_segment"
        ]


# =========================================================
# DISPLAY SELECTED AUDIENCE
# =========================================================

def render_selected_audience(
    fans,
    selected_segment,
):

    if not selected_segment:

        return

    segments = get_segments(
        fans
    )

    selected_data = segments.get(
        selected_segment,
        pd.DataFrame(),
    )

    st.success(
        f"🎯 Analytics selected audience: **{selected_segment}**"
    )

    col1, col2 = st.columns(
        [4, 1]
    )

    with col1:

        st.write(
            f"**{len(selected_data)} fans** belong to this audience."
        )

    with col2:

        if st.button(
            "Clear",
            key="clear_analytics_segment",
            use_container_width=True,
        ):

            clear_selected_segment()

            st.rerun()

    st.divider()

    if selected_data.empty:

        st.warning(
            f"No fans currently belong to **{selected_segment}**."
        )

        return

    st.subheader(
        f"👥 {selected_segment}"
    )

    st.dataframe(
        selected_data,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()


# =========================================================
# MAIN SEGMENTATION PAGE
# =========================================================

def show_segmentation():

    st.title(
        PAGE_TITLE
    )

    st.caption(
        "Understand who your fans are and group them into actionable audiences."
    )

    # -----------------------------------------------------
    # Load fans
    # -----------------------------------------------------

    fans = load_fans()

    if fans.empty:

        st.info(
            "No fans are available yet."
        )

        return

    # -----------------------------------------------------
    # Analytics-selected audience
    # -----------------------------------------------------

    selected_segment = (
        get_selected_segment()
    )

    render_selected_audience(
        fans,
        selected_segment,
    )

    # -----------------------------------------------------
    # Segment selector
    # -----------------------------------------------------

    segments = get_segments(
        fans
    )

    available_segments = list(
        segments.keys()
    )

    default_index = 0

    if selected_segment in available_segments:

        default_index = (
            available_segments.index(
                selected_segment
            )
        )

    selected = st.selectbox(
        "Select Audience Segment",
        available_segments,
        index=default_index,
        key="segmentation_selector",
    )

    audience = segments.get(
        selected,
        pd.DataFrame(),
    )

    # -----------------------------------------------------
    # Audience summary
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Audience Size",
            len(audience),
        )

    with col2:

        percentage = (
            len(audience)
            / len(fans)
            * 100
            if len(fans) > 0
            else 0
        )

        st.metric(
            "Audience Share",
            f"{percentage:.1f}%",
        )

    with col3:

        if "total_spend" in audience.columns:

            spend = pd.to_numeric(
                audience[
                    "total_spend"
                ],
                errors="coerce",
            ).fillna(0).sum()

        else:

            spend = 0

        st.metric(
            "Audience Revenue",
            f"R{spend:,.2f}",
        )

    st.divider()

    # -----------------------------------------------------
    # Audience table
    # -----------------------------------------------------

    st.subheader(
        f"👥 {selected}"
    )

    if audience.empty:

        st.info(
            "No fans currently belong to this segment."
        )

    else:

        st.dataframe(
            audience,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # -----------------------------------------------------
    # Segment overview
    # -----------------------------------------------------

    st.subheader(
        "📊 Segment Overview"
    )

    counts = get_segment_counts(
        fans
    )

    if not counts.empty:

        st.dataframe(
            counts,
            use_container_width=True,
            hide_index=True,
        )