import streamlit as st
from optimizer import optimize_portfolio, get_frontier_data
import plotly.graph_objects as go
import pandas as pd

# ── PAGE CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="Q-STRAT Terminal",
    layout="wide"
)

# ── PROFESSIONAL DARK THEME ─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body {
    background-color: #0B0F14;
    color: #E5E7EB;
    font-family: 'Inter', sans-serif;
}

.block-container {
    padding: 1.5rem 2.5rem;
}

/* HEADER */
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #1F2937;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

.logo {
    font-weight: 600;
    font-size: 1rem;
    letter-spacing: 0.1em;
}

.subtle {
    color: #6B7280;
    font-size: 0.75rem;
}

/* CONTROL PANEL */
.control-box {
    background: #111827;
    border: 1px solid #1F2937;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 20px;
}

/* METRICS */
.metric {
    background: #111827;
    border: 1px solid #1F2937;
    padding: 1rem;
    border-radius: 8px;
}

.metric-label {
    font-size: 0.7rem;
    color: #6B7280;
}

.metric-value {
    font-size: 1.4rem;
    font-weight: 600;
}

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid #1F2937;
}

.stTabs [data-baseweb="tab"] {
    font-size: 0.8rem;
}

/* BUTTON */
button[kind="primary"] {
    background-color: #3B82F6 !important;
}

/* REMOVE STREAMLIT DEFAULT UI */
#MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── HEADER WITH SVG LOGO ────────────────────────────────
st.markdown("""
<div class="header">
    <div class="logo">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="#3B82F6" style="vertical-align:middle;margin-right:8px;">
            <path d="M3 3h18v2H3V3zm2 4h14v14H5V7zm4 4v6h2v-6H9zm4-2v8h2V9h-2z"/>
        </svg>
        Q-STRAT TERMINAL
    </div>
    <div class="subtle">
        ENV: PROD | SOLVER: SLSQP
    </div>
</div>
""", unsafe_allow_html=True)

# ── CONTROL PANEL ───────────────────────────────────────
with st.container():
    st.markdown('<div class="control-box">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([2,1,1,1])

    with col1:
        tickers_input = st.text_input("Assets", "AAPL, MSFT, NVDA, TSLA")

    with col2:
        period = st.selectbox("Horizon", ["6mo","1y","2y","5y"])

    with col3:
        objective = st.selectbox("Objective", ["max_sharpe","min_volatility"])

    with col4:
        run = st.button("Run Optimization")

    st.markdown('</div>', unsafe_allow_html=True)

# ── PROCESS INPUT ───────────────────────────────────────
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

if run:
    try:
        result = optimize_portfolio(tickers, period, objective)
        weights = result["weights"]

        # ── METRICS ───────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)

        metrics = [
            ("Expected Return", f"{result['return']}%"),
            ("Volatility", f"{result['volatility']}%"),
            ("Sharpe Ratio", result['sharpe']),
            ("Assets Used", len([v for v in weights.values() if v > 0.01]))
        ]

        for i, (label, val) in enumerate(metrics):
            with [m1, m2, m3, m4][i]:
                st.markdown(f"""
                <div class="metric">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{val}</div>
                </div>
                """, unsafe_allow_html=True)

        # ── TABS ──────────────────────────────────────────
        tab1, tab2 = st.tabs(["Portfolio", "Analytics"])

        # ── TAB 1: PORTFOLIO ──────────────────────────────
        with tab1:
            col_left, col_right = st.columns([1, 1.5])

            df = pd.DataFrame(weights.items(), columns=["Asset", "Weight"])
            df = df.sort_values(by="Weight", ascending=False)

            # Allocation Donut
            with col_left:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=df["Asset"],
                    values=df["Weight"],
                    hole=0.6
                )])

                fig_pie.update_layout(
                    paper_bgcolor="#0B0F14",
                    font=dict(color="white"),
                    showlegend=True,
                    title="Allocation"
                )

                st.plotly_chart(fig_pie, use_container_width=True)

            # Efficient Frontier
            with col_right:
                vols, rets = get_frontier_data(tickers, period)

                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=vols,
                    y=rets,
                    mode="lines",
                    name="Efficient Frontier",
                    line=dict(color="#3B82F6", width=3)
                ))

                fig.add_trace(go.Scatter(
                    x=[result["volatility"]],
                    y=[result["return"]],
                    mode="markers",
                    marker=dict(size=12, color="#22C55E"),
                    name="Optimal Portfolio"
                ))

                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#0B0F14",
                    plot_bgcolor="#0B0F14",
                    xaxis=dict(title="Volatility", gridcolor="#1F2937"),
                    yaxis=dict(title="Expected Return", gridcolor="#1F2937"),
                    font=dict(color="#D1D5DB")
                )

                st.plotly_chart(fig, use_container_width=True)

        # ── TAB 2: ANALYTICS ──────────────────────────────
        with tab2:
            st.subheader("Portfolio Weights Table")
            st.dataframe(df, use_container_width=True)

            # Bar chart
            fig_bar = go.Figure(go.Bar(
                x=df["Weight"],
                y=df["Asset"],
                orientation='h',
                marker_color="#3B82F6"
            ))

            fig_bar.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0B0F14",
                plot_bgcolor="#0B0F14",
                title="Weight Distribution"
            )

            st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.markdown("""
    <div style="text-align:center; margin-top:100px; color:#6B7280;">
        System Idle — Awaiting Input
    </div>
    """, unsafe_allow_html=True)

# ── FOOTER ─────────────────────────────────────────────
st.markdown("""
<div style="margin-top: 60px; text-align:center; font-size:0.6rem; color:#374151;">
Q-STRAT TERMINAL | Developed by M. Owais Qureshi
</div>
""", unsafe_allow_html=True)
