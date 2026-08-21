import streamlit as st
import pandas as pd

from campaign_performance_engine import (
    build_performance_table,
    get_total_performance,
)

from campaign_delivery import (
    execute_pending_deliveries,
    get_delivery_summary,
    get_delivery_queue,
)


def show_campaign_performance():

    st.title(
        "📈 Campaign Performance"
    )

    st.caption(
        "Measure campaign results and execute audience deliveries."
    )


    # =====================================================
    # PERFORMANCE OVERVIEW
    # =====================================================

    summary = get_total_performance()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Campaigns",
            summary.get("campaigns", 0),
        )

    with c2:
        st.metric(
            "Messages Sent",
            summary.get("sent", 0),
        )

    with c3:
        st.metric(
            "Conversions",
            summary.get("conversions", 0),
        )

    with c4:
        st.metric(
            "Revenue",
            f"R{summary.get('revenue', 0):,.2f}",
        )


    st.divider()


    # =====================================================
    # DELIVERY CONTROL CENTER
    # =====================================================

    st.header(
        "🚀 Campaign Delivery Execution"
    )

    delivery_summary = get_delivery_summary()

    d1, d2, d3, d4 = st.columns(4)

    with d1:
        st.metric(
            "Queue Total",
            delivery_summary["total"],
        )

    with d2:
        st.metric(
            "Pending",
            delivery_summary["pending"],
        )

    with d3:
        st.metric(
            "Sent",
            delivery_summary["sent"],
        )

    with d4:
        st.metric(
            "Failed",
            delivery_summary["failed"],
        )


    st.write(
        "Pending messages are delivered through the configured WhatsApp provider."
    )


    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "📨 Send Pending Messages",
            use_container_width=True,
        ):

            with st.spinner(
                "Sending pending messages..."
            ):

                result = execute_pending_deliveries(
                    limit=50
                )

            if result.get("sent", 0) > 0:

                st.success(
                    f"{result['sent']} messages sent successfully."
                )

            if result.get("failed", 0) > 0:

                st.warning(
                    f"{result['failed']} messages failed."
                )

            st.json(
                result
            )


    with col2:

        if st.button(
            "▶ Execute Campaign Queue",
            use_container_width=True,
        ):

            with st.spinner(
                "Executing campaign delivery queue..."
            ):

                result = execute_pending_deliveries(
                    limit=500
                )

            st.success(
                "Campaign execution completed."
            )

            st.json(
                result
            )


    st.divider()


    # =====================================================
    # DELIVERY QUEUE TABLE
    # =====================================================

    st.header(
        "📋 Delivery Queue"
    )

    queue = get_delivery_queue()

    if queue.empty:

        st.info(
            "No delivery queue records found."
        )

    else:

        st.dataframe(
            queue,
            use_container_width=True,
        )


    st.divider()


    # =====================================================
    # CAMPAIGN PERFORMANCE TABLE
    # =====================================================

    st.header(
        "📊 Campaign Results"
    )

    performance = build_performance_table()

    if performance.empty:

        st.info(
            "No campaign performance data available."
        )

    else:

        st.dataframe(
            performance,
            use_container_width=True,
        )