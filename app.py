from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
# ----------------------------- Page setup -----------------------------------
st.set_page_config(
    page_title="PlayScope | Store Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
IST = ZoneInfo("Asia/Kolkata")
DATA_DIR = Path(__file__).parent / "data"
PLAY_STORE_FILE = DATA_DIR / "Play Store Data.csv"

# ----------------------------- Premium styling ------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#edf2ff; --muted:#9aa8c7; --panel:#111a2d; --line:rgba(161,181,220,.14); }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp {
  background:
    radial-gradient(ellipse at 12% 0%, rgba(58,105,190,.22), transparent 34%),
    radial-gradient(ellipse at 92% 8%, rgba(119,77,190,.16), transparent 28%),
    #080e1b;
  color:var(--ink);
}
[data-testid="stHeader"] { background:rgba(8,14,27,.75); }
[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#101a2d 0%,#0b1322 100%);
  border-right:1px solid var(--line);
}
.block-container { padding-top:2rem; padding-bottom:3rem; max-width:1500px; }
.hero { padding:1.35rem 1.55rem; border:1px solid var(--line); border-radius:22px;
  background:linear-gradient(120deg,rgba(28,46,79,.88),rgba(19,25,48,.78));
  box-shadow:0 18px 55px rgba(0,0,0,.20); margin-bottom:1.2rem; }
.eyebrow { color:#8db5ff; font-size:.72rem; letter-spacing:.19em; font-weight:700; text-transform:uppercase; }
.hero h1 { font-family:Manrope,sans-serif; color:#f3f6ff; font-size:2.05rem; font-weight:800; margin:.35rem 0 .35rem; }
.hero p { color:#aab8d4; margin:0; font-size:.95rem; }
.metric-card { border:1px solid var(--line); border-radius:17px; padding:1rem 1.1rem;
  background:linear-gradient(145deg,rgba(24,37,62,.92),rgba(14,23,40,.95)); min-height:112px; }
.metric-label { color:#9baac7; font-size:.78rem; font-weight:600; letter-spacing:.04em; }
.metric-value { color:#f2f6ff; font-family:Manrope,sans-serif; font-size:1.65rem; font-weight:800; margin-top:.35rem; }
.metric-note { color:#7f91b4; font-size:.72rem; margin-top:.15rem; }
.section-title { font-family:Manrope,sans-serif; color:#eef3ff; font-size:1.1rem; font-weight:800; margin:.6rem 0 .2rem; }
.subtle { color:#9aa8c7; font-size:.84rem; }
.gate-card { border:1px solid rgba(116,151,211,.24); border-radius:18px; padding:1.5rem;
  background:linear-gradient(130deg,rgba(25,42,70,.92),rgba(17,25,44,.92)); }
.gate-title { color:#edf3ff; font-family:Manrope,sans-serif; font-weight:800; font-size:1.12rem; }
.gate-copy { color:#9eacc8; margin-top:.45rem; line-height:1.55; }
div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:14px; overflow:hidden; }
.stButton>button { border-radius:10px; border:1px solid #4869a5; background:#203b68; color:#f3f6ff; }
small, .stCaption { color:#91a0bd !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------------- Data utilities -------------------------------
def parse_installs(value):
    """Convert values such as '1,000+' to an integer."""
    if pd.isna(value):
        return 0
    digits = re.sub(r"[^0-9]", "", str(value))
    return int(digits) if digits else 0

def parse_size_mb(value):
    """Convert Play Store size strings to MB. Unknown/Varies with device -> NaN."""
    if pd.isna(value):
        return float("nan")
    value = str(value).strip().upper()
    if value in {"", "NAN", "VARIES WITH DEVICE"}:
        return float("nan")
    match = re.search(r"([0-9]*\.?[0-9]+)\s*([KMG]?)", value)
    if not match:
        return float("nan")
    amount, unit = float(match.group(1)), match.group(2)
    if unit == "K":
        return amount / 1024
    if unit == "G":
        return amount * 1024
    return amount

@st.cache_data(show_spinner=False)
def load_and_aggregate(csv_path, modified_time):
    df = pd.read_csv(csv_path)
    required = {"App", "Category", "Rating", "Reviews", "Size", "Installs", "Last Updated"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")

    df = df.copy()
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df["Reviews_num"] = pd.to_numeric(df["Reviews"], errors="coerce").fillna(0)
    df["Installs_num"] = df["Installs"].map(parse_installs)
    df["Size_MB"] = df["Size"].map(parse_size_mb)
    df["Last_Updated_dt"] = pd.to_datetime(df["Last Updated"], errors="coerce")

    # Remove duplicate app records so an app is not counted more than once.
    df = df.sort_values("Last_Updated_dt").drop_duplicates(subset=["App"], keep="last")

    # Filters are applied at app level before category aggregation.
    filtered = df[
        (df["Rating"] >= 4.0)
        & (df["Size_MB"] >= 10.0)
        & (df["Last_Updated_dt"].dt.month == 1)
    ].copy()

    summary = (
        filtered.groupby("Category", as_index=False)
        .agg(
            average_rating=("Rating", "mean"),
            total_reviews=("Reviews_num", "sum"),
            total_installs=("Installs_num", "sum"),
            app_count=("App", "nunique"),
        )
        .sort_values(["total_installs", "Category"], ascending=[False, True])
        .head(10)
    )
    return filtered, summary


def is_chart_window(now=None):
    now = now or datetime.now(IST)
    # Inclusive start, exclusive end: chart is visible from 3:00 PM to 4:59:59 PM IST.
    return now.hour == 15 or (now.hour == 16)


def format_number(value):
    return f"{value:,.0f}"


# ----------------------------- Sidebar --------------------------------------
with st.sidebar:
    st.markdown("## ◈ PlayScope")
    st.caption("APP STORE INTELLIGENCE")
    st.divider()
    st.markdown("**Analysis rules**")
    st.markdown("- Average rating ≥ **4.0**")
    st.markdown("- App size ≥ **10 MB**")
    st.markdown("- Last updated in **January**")
    st.markdown("- Top **10** categories by installs")
    st.divider()
    st.markdown("**Visibility schedule**")
    st.markdown("🕒 3:00 PM – 5:00 PM IST")
    st.caption("The chart is hidden outside this time window.")
    st.divider()
    st.caption("Dataset: Google Play Store app data")

# ----------------------------- Header ---------------------------------------
st.markdown("""
<div class="hero">
  <div class="eyebrow">STORE PERFORMANCE / ANALYTICS</div>
  <h1>Play Store Category Intelligence</h1>
  <p>A focused view of category quality and engagement, filtered by your business rules.</p>
</div>
""", unsafe_allow_html=True)

if not PLAY_STORE_FILE.exists():
    st.error("Play Store dataset not found. Place 'Play Store Data.csv' inside the project's data/ folder.")
    st.stop()

try:
    filtered_apps, category_summary = load_and_aggregate(
        str(PLAY_STORE_FILE), PLAY_STORE_FILE.stat().st_mtime
    )
except Exception as exc:
    st.error(f"Could not process the dataset: {exc}")
    st.stop()

if category_summary.empty:
    st.warning("No categories match all selected rules. Check the dataset values and filter criteria.")
    st.stop()

total_apps = len(filtered_apps)
total_installs = int(category_summary["total_installs"].sum())
total_reviews = int(category_summary["total_reviews"].sum())
overall_rating = filtered_apps["Rating"].mean() if total_apps else 0

m1, m2, m3, m4 = st.columns(4)
metrics = [
    (m1, "QUALIFYING APPS", format_number(total_apps), "After all app-level filters"),
    (m2, "CATEGORIES SHOWN", str(len(category_summary)), "Ranked by total installs"),
    (m3, "TOTAL INSTALLS", format_number(total_installs), "Across the displayed top 10"),
    (m4, "TOTAL REVIEWS", format_number(total_reviews), f"Mean app rating: {overall_rating:.2f} / 5"),
]
for col, label, value, note in metrics:
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div>'
            f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown('<div class="section-title">Category comparison</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtle">Average rating and total review volume for the 10 highest-install categories '
    'that satisfy the selected app-level filters.</div>',
    unsafe_allow_html=True,
)

# Fragment refreshes the time gate every 30 seconds without requiring a manual reload.
@st.fragment(run_every="30s")
def scheduled_chart():
    now = datetime.now(IST)
    if not is_chart_window(now):
        st.markdown(
            f"""
            <div class="gate-card">
              <div class="gate-title">◷ Analytics view is currently locked</div>
              <div class="gate-copy">
                This chart is available daily from <b>3:00 PM to 5:00 PM IST</b>.
                It will appear automatically during that window. Current India time:
                <b>{now.strftime('%I:%M:%S %p')} IST</b>.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    plot_df = category_summary.copy()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Average rating ( / 5 )",
        x=plot_df["Category"],
        y=plot_df["average_rating"].round(2),
        yaxis="y",
        offsetgroup="rating",
        marker=dict(color="#7C9CFF", line=dict(color="#A9BCFF", width=0.6)),
        hovertemplate="<b>%{x}</b><br>Average rating: %{y:.2f} / 5<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Total reviews",
        x=plot_df["Category"],
        y=plot_df["total_reviews"],
        yaxis="y2",
        offsetgroup="reviews",
        marker=dict(color="#36C9B4", line=dict(color="#78E5D4", width=0.6)),
        hovertemplate="<b>%{x}</b><br>Total reviews: %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        barmode="group",
        height=520,
        margin=dict(l=18, r=22, t=42, b=100),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#C7D2E8"),
        legend=dict(orientation="h", y=1.13, x=0, bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(title="", tickangle=-30, showgrid=False, linecolor="rgba(160,180,220,.2)"),
        yaxis=dict(title="Average rating (out of 5)", range=[0, 5], gridcolor="rgba(160,180,220,.12)", zeroline=False),
        yaxis2=dict(title="Total review count", overlaying="y", side="right", showgrid=False, rangemode="tozero"),
        bargap=0.24,
        bargroupgap=0.10,
        hoverlabel=dict(bgcolor="#17243B", font_color="#F4F7FF"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(f"Chart access window active · {now.strftime('%I:%M:%S %p')} IST · Refreshes every 30 seconds")

scheduled_chart()

with st.expander("View category data table", expanded=False):
    display_df = category_summary.rename(columns={
        "Category": "App category",
        "average_rating": "Average rating",
        "total_reviews": "Total reviews",
        "total_installs": "Total installs",
        "app_count": "Qualifying apps",
    }).copy()
    display_df["Average rating"] = display_df["Average rating"].round(2)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(
    "Method: app-level filters are applied first; duplicate app names are reduced to the latest dated record; "
    "category metrics are then aggregated. January means any January in the dataset, regardless of year. "
    "The chart uses separate left/right axes because rating and review counts have very different scales."
)
