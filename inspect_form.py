import streamlit as st

from data.google_sheets import read_sheet


st.set_page_config(
    page_title="Fan CRM - Form Inspector",
    page_icon="🎵",
    layout="wide",
)


st.title("🎵 Fan CRM — Form Inspector")

st.write(
    "This page is used to inspect Google Form responses."
)


if st.button("🔄 Load Form Responses"):

    try:

        with st.spinner(
            "Connecting to Google Sheets..."
        ):

            df = read_sheet(
                "Form responses 1"
            )

        st.success(
            "Google Form responses loaded!"
        )

        st.subheader("Column names")

        for column in df.columns:

            st.code(column)

        st.subheader("Raw data")

        if df.empty:

            st.info(
                "The Form responses sheet is empty."
            )

        else:

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

    except Exception as e:

        st.error(
            "Google Sheets connection failed."
        )

        st.write(
            "Try the button again. "
            "The connection is currently experiencing "
            "an intermittent SSL/network error."
        )

        st.exception(e)