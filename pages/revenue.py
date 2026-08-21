import streamlit as st

from data.google_sheets import read_sheet
from analytics.metrics import (
    total_revenue,
    revenue_by_category,
    purchasing_fans,
)


def show_revenue():

    st.title("💰 Revenue")

    try:

        purchases = read_sheet("Purchases")

    except Exception as e:

        st.error(
            f"Unable to load purchases: {e}"
        )

        return

    if purchases.empty:

        st.info(
            "No purchases recorded yet."
        )

        return

    revenue = total_revenue(
        purchases
    )

    buyers = purchasing_fans(
        purchases
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Total Revenue",
        f"R{revenue:,.2f}",
    )

    col2.metric(
        "Paying Fans",
        buyers,
    )

    st.divider()

    st.subheader(
        "Revenue by Category"
    )

    category_revenue = revenue_by_category(
        purchases
    )

    if not category_revenue.empty:

        st.bar_chart(
            category_revenue
        )

    st.divider()

    st.subheader(
        "Transactions"
    )

    st.dataframe(
        purchases,
        use_container_width=True,
        hide_index=True,
    )