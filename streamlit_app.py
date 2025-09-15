# CloseoutSoft • WAMI Progress Dashboard (COMPACT • CLEAN HEADER • SIDEBAR FILTERS)
# Visual/layout/theme changes only. Functionality unchanged for existing sections.
# Adds a drill-down Submittals view driven by Reports.json / Reports.xlsx (Discipline → System → Subsystem).

import base64
from pathlib import Path
import json as _json

import altair as alt
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# -------------------- Page / Theme --------------------
st.set_page_config(
    page_title="CloseoutSoft – WAMI Progress",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Altair look (doesn't affect Plotly tabs)
try:
    alt.themes.enable("none")
except Exception:
    pass

# Allow large datasets in Altair (fixes Submittals charts not rendering on Cloud)
try:
    alt.data_transformers.enable("default", max_rows=None)
except Exception:
    try:
        alt.data_transformers.disable_max_rows()
    except Exception:
        pass

# Plotly defaults (avoid old Plotly template crash)
px.defaults.template = None
px.defaults.color_discrete_sequence = px.colors.qualitative.Pastel

# Brand accents & colors
STATUS_COLORS = {
    "Approved": "#A3E4D7",
    "ApprovedWithComments": "#C9E4FF",
    "Rejected": "#FADBD8",
    "UR": "#FDEBD0",
    "Open": "#F9E79F",
    "Closed": "#D7BDE2",
}
SOURCE_COLORS = {"AG": "#AED6F1", "CloseoutSoft": "#F5CBA7"}


# ---------- Styling helpers ----------
def style_fig(fig, *, height=220, showlegend=True, legend_title=" "):
    fig.update_layout(
        title=None,
        legend_title_text="",
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=height,
        font=dict(color="#0F172A", size=12),
        title_font=dict(color="#0B1220", size=15),
        legend=dict(
            font=dict(size=10),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
        ),
        margin=dict(l=8, r=8, t=32, b=6),
        showlegend=showlegend,
    )
    fig.update_xaxes(
        showgrid=False,
        tickfont=dict(size=11, color="#0F172A"),
        title_font=dict(size=12, color="#0F172A"),
        showline=True, linewidth=1, linecolor="#CBD5E1", zeroline=False,
    )
    fig.update_yaxes(
        gridcolor="#EEF2F7",
        tickfont=dict(size=11, color="#0F172A"),
        title_font=dict(size=12, color="#0F172A"),
        showline=True, linewidth=1, linecolor="#CBD5E1", zeroline=False,
    )
    return fig


# ---- Global CSS (compact layout, visible dropdowns, CLEAN WHITE HEADER) ----
st.markdown(
    """
<style>
  :root, * { color-scheme: light !important; }
  html, body, .stApp { background:#FFFFFF !important; color:#0F172A !important; overflow-x:hidden !important; }

  :root {
    --rebus-bg:#FFFFFF;
    --rebus-fg:#0F172A;
    --rebus-purple-100:#E6E0F8;
    --rebus-purple-200:#DDD7F6;
  }

  .block-container { padding-top: 1.6rem !important; padding-bottom: 1rem; max-width: 1200px; margin: 0 auto; }

  header[data-testid="stHeader"] { background:#FFFFFF !important; }
  div[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display:none !important; }

  [data-testid="stSidebar"]{ background:#FFFFFF !important; border-right:1px solid #E6ECF4; }
  section[data-testid="stSidebar"] > div:first-child { background:transparent !important; }

  .stSelectbox > div, .stMultiSelect > div, .stDateInput > div, [data-baseweb="select"] > div {
    background:#FFFFFF !important; border:1px solid #E6ECF4 !important; border-radius:10px !important;
    box-shadow:none !important; min-height:38px;
  }
  .stSelectbox label, .stMultiSelect label, .stDateInput label {
    color:#42526E !important; font-weight:700 !important; font-size:11px !important;
    letter-spacing:.2px; text-transform:uppercase; margin-bottom:4px !important;
  }
  .stApp input, .stApp textarea { background:#FFFFFF !important; color:#0F172A !important; -webkit-text-fill-color:#0F172A !important; }
  .stApp [data-baseweb="select"] svg { color:#0F172A !important; fill:#0F172A !important; }
  .stApp [data-baseweb="tag"] { background:#F1F5F9 !important; color:#0B1220 !important; border:1px solid #E6ECF4 !important; border-radius:8px !important; }

  .card-kpi{
    background: var(--rebus-purple-100) !important;
    border:1px solid var(--rebus-purple-200) !important;
    border-radius:16px; padding:12px; box-shadow:0 1px 2px rgba(16,24,40,.04), 0 8px 16px rgba(16,24,40,.06);
  }
  .kpi-tiles{ display:grid; grid-template-columns: repeat(5, minmax(0,1fr)); gap: 12px; }
  @media (max-width:1100px){ .kpi-tiles{ grid-template-columns: repeat(2, minmax(0,1fr)); } }
  .kpi-tile{
    background:#FFFFFF; border:1px solid #E6ECF4; border-radius:14px; padding:12px 14px;
    box-shadow:0 1px 2px rgba(16,24,40,.04), 0 8px 16px rgba(16,24,40,.06);
  }
  /* KPI banner: pill + bold value */
  .pill{
    display:inline-flex; align-items:center; gap:6px;
    padding:4px 12px; border-radius:9999px; font-weight:800; font-size:12px;
    border:1px solid transparent;
  }
  .pill.ok{   background:rgba(16,185,129,.12);  color:#047857; border-color:#A7F3D0; }
  .pill.warn{ background:rgba(245,158,11,.12);  color:#B45309; border-color:#FDE68A; }
  .pill.risk{ background:rgba(239,68,68,.12);   color:#B91C1C; border-color:#FCA5A5; }

  .kpi-head{ display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
  .kpi-label{ color:#334155; font-weight:900; font-size:11px; letter-spacing:.08em; text-transform:uppercase; }
  .kpi-val{ font-size:22px; font-weight:900; color:#0B1220; line-height:1.05; }

  .card{ background:#FFF; border:1px solid #E6ECF4; border-radius:12px; padding:12px; box-shadow:0 1px 2px rgba(16,24,40,.04); }

  [data-testid="stTabs"] [role="tablist"]{ gap:6px; border-bottom:none; flex-wrap:wrap; }
  [data-testid="stTabs"] [role="tab"]{
     background:#F8FAFC; color:#0F172A !important; padding:8px 12px; border-radius:10px 10px 0 0;
     font-weight:700; border:1px solid #E6ECF4; border-bottom:none; font-size:13px;
  }
  [data-testid="stTabs"] [role="tab"][aria-selected="true"]{
     background:#FFFFFF; color:#0B1220 !important; box-shadow:0 -2px 8px rgba(16,24,40,.05);
  }

  div[data-testid="stDataFrame"]{ border:1px solid #E6ECF4; border-radius:12px; overflow:hidden; background:#FFFFFF !important; }

  .js-plotly-plot .g-gtitle { display: none !important; }
  .js-plotly-plot .legend .legendtext { fill:#0F172A !important; color:#0F172A !important; opacity:1 !important; font-size:12px !important; }

  .brand-bar { margin: 8px 0 12px 0; padding: 4px 0; }
  .brand-row { display:flex; align-items:center; justify-content:space-between; min-height:52px; }

  /* NEW: smaller logo size */
  .rebus-logo {
    height:44px;
    width:auto;
    display:block;
  }

  /* NEW: larger, crisp circular avatar */
  .avatar {
    width:44px;
    height:44px;
    border-radius:9999px;
    object-fit:cover;
    border:1px solid #E6ECF4;
    box-shadow:0 1px 2px rgba(16,24,40,.04);
    background:#F1F5F9;
  }

  .avatar-fallback { display:none !important; } /* no longer used */
</style>
""",
    unsafe_allow_html=True,
)


# -------------------- Simple Header --------------------
def _img_to_data_uri(path: Path) -> str | None:
    if not path or not path.exists():
        return None
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _logo_data_uri() -> str | None:
    here = Path(__file__).parent if "__file__" in globals() else Path(".")
    for name in ("rebus_logo.png", "rebus.png", "rebus.jpg", "rebus.jpeg"):
        uri = _img_to_data_uri(here / name)
        if uri:
            return uri
    return None


def _profile_data_uri() -> str | None:
    here = Path(__file__).parent if "__file__" in globals() else Path(".")
    # Prioritize profile.jpg first (your case), then other common names
    for name in ("profile.jpg", "profile.png", "avatar.png", "user.png", "avatar.jpg"):
        uri = _img_to_data_uri(here / name)
        if uri:
            return uri
    return None


def _actor_svg_data_uri() -> str:
    # Default actor-style avatar if no local profile image exists
    svg = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>
      <defs>
        <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
          <stop offset='0%' stop-color='#60A5FA'/>
          <stop offset='100%' stop-color='#22D3EE'/>
        </linearGradient>
      </defs>
      <circle cx='32' cy='32' r='32' fill='url(#g)'/>
      <circle cx='32' cy='26' r='10' fill='white' opacity='0.95'/>
      <path d='M16 52c0-8.837 7.163-16 16-16s16 7.163 16 16' fill='white' opacity='0.95'/>
    </svg>"""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


_logo = _logo_data_uri()
_avatar = _profile_data_uri()
_actor = _actor_svg_data_uri()

st.markdown(
    f"""
    <div class="brand-bar">
      <div class="brand-row">
        <div class="brand-left">
          {f'<img class="rebus-logo" src="{_logo}" alt="CloseoutSoft">' if _logo else ''}
        </div>
        <div class="brand-right">
          <img class="avatar" src="{_avatar or _actor}" alt="Profile">
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------- Helpers --------------------
def pct(num, den):
    return float(num) / float(den) * 100 if den else 0.0


def safe_sum(df, col):
    return int(df[col].sum()) if isinstance(df, pd.DataFrame) and col in df.columns else 0


# ---- Altair interactive donuts (click to filter) + improved table ----
def build_submittals_drilldown(df: pd.DataFrame) -> alt.Chart:
    """
    Three linked donuts (Discipline → System → Subsystem)
    + white-themed, bordered table with fallback filtering:
      - if Subsystem selected → use Subsystem
      - elif System selected → use System
      - elif Discipline selected → use Discipline
      - else show all
    """
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame({"x": []})).mark_text(text="No data")

    df = df.copy()

    # Ensure expected columns present
    for col, fill in [
        ("Discipline","—"),("System","—"),("Subsystem","—"),
        ("Status","—"),("Activity","—"),("InternalRefNumber","—"),
        ("Company","—"),("Building","—"),("Level","—"),("Room","—"),
        ("SubmittalDate", pd.NaT),
    ]:
        if col not in df.columns:
            df[col] = fill

    # Dates
    df["SubmittalDate"] = pd.to_datetime(df["SubmittalDate"], errors="coerce")
    df["SubmittalDateStr"] = df["SubmittalDate"].dt.strftime("%Y-%m-%d").fillna("—")

    # --- Named Selections (Altair v4/v5) ---
    def _sel(fields, name):
        if hasattr(alt, "selection_point"):
            # single-select; dblclick to clear
            return alt.selection_point(name=name, fields=fields, empty=True, clear="dblclick", toggle=False)
        return alt.selection_single(fields=fields, empty="all", name=name)

    disc_sel = _sel(["Discipline"], name="disc_sel")
    sys_sel  = _sel(["System"],     name="sys_sel")
    sub_sel  = _sel(["Subsystem"],  name="sub_sel")

    base = alt.Chart(df).properties(width=280, height=280)
    donut_kwargs = dict(innerRadius=75, outerRadius=120)

    disc = (
        base.transform_aggregate(group_count="count()", groupby=["Discipline"])
            .transform_joinaggregate(total="sum(group_count)")
            .transform_calculate(pct="datum.group_count / datum.total")
            .mark_arc(**donut_kwargs)
            .encode(
                theta="group_count:Q",
                color=alt.Color("Discipline:N", legend=None, scale=alt.Scale(scheme="category20")),
                tooltip=[
                    alt.Tooltip("Discipline:N", title="Discipline"),
                    alt.Tooltip("group_count:Q", title="Count"),
                    alt.Tooltip("pct:Q", title="Percent", format=".1%"),
                ],
            )
            .add_params(disc_sel)
            .properties(title="Discipline")
    )

    sys = (
        base.transform_filter(disc_sel)
            .transform_aggregate(group_count="count()", groupby=["System"])
            .transform_joinaggregate(total="sum(group_count)")
            .transform_calculate(pct="datum.group_count / datum.total")
            .mark_arc(**donut_kwargs)
            .encode(
                theta="group_count:Q",
                color=alt.Color("System:N", legend=None, scale=alt.Scale(scheme="category20")),
                tooltip=[
                    alt.Tooltip("System:N", title="System"),
                    alt.Tooltip("group_count:Q", title="Count"),
                    alt.Tooltip("pct:Q", title="Percent", format=".1%"),
                ],
            )
            .add_params(sys_sel)
            .properties(title="System")
    )

    sub = (
        base.transform_filter(disc_sel)
            .transform_filter(sys_sel)
            .transform_aggregate(group_count="count()", groupby=["Subsystem"])
            .transform_joinaggregate(total="sum(group_count)")
            .transform_calculate(pct="datum.group_count / datum.total")
            .mark_arc(**donut_kwargs)
            .encode(
                theta="group_count:Q",
                color=alt.Color("Subsystem:N", legend=None, scale=alt.Scale(scheme="category20")),
                tooltip=[
                    alt.Tooltip("Subsystem:N", title="Subsystem"),
                    alt.Tooltip("group_count:Q", title="Count"),
                    alt.Tooltip("pct:Q", title="Percent", format=".1%"),
                ],
            )
            .add_params(sub_sel)
            .properties(title="Subsystem")
    )

    # ===== Table (fallback layers) =====
    cols_pref = [
        "Discipline", "System", "Subsystem", "Status", "SubmittalDateStr",
        "InternalRefNumber", "Company", "Building",
    ]
    present_cols = [c for c in cols_pref if c in df.columns]

    table_width = max(720, 150 * max(1, len(present_cols)))
    row_step = 26
    page_limit = 15

    # Visibility conditions (use Vega selection stores)
    cond_sub_active  = "length(data('sub_sel_store')) > 0"
    cond_sys_active  = "(length(data('sub_sel_store')) == 0) && (length(data('sys_sel_store')) > 0)"
    cond_disc_active = "(length(data('sub_sel_store')) == 0) && (length(data('sys_sel_store')) == 0) && (length(data('disc_sel_store')) > 0)"
    cond_none        = "(length(data('sub_sel_store')) == 0) && (length(data('sys_sel_store')) == 0) && (length(data('disc_sel_store')) == 0)"

    def _table_layer(row_filter, visible_when_expr):
        # Base rows
        base_tbl = alt.Chart(df)
        # Only apply a row filter if one is provided (None means "show all")
        if row_filter is not None:
            base_tbl = base_tbl.transform_filter(row_filter)

        base_tbl = (
            base_tbl
              .transform_filter(visible_when_expr)  # show this layer only in its mode
              .transform_window(
                  row_number="row_number()",
                  sort=[{"field": "SubmittalDate", "order": "descending"}] if "SubmittalDate" in df.columns else []
              )
              .transform_filter(f"datum.row_number <= {page_limit}")
              .transform_fold(present_cols, as_=["Column", "Value"])
              .transform_calculate(
                  ValueStr="isValid(datum.Value) ? (length(toString(datum.Value)) > 38 ? slice(toString(datum.Value), 0, 38) + '…' : toString(datum.Value)) : ''"
              )
        )
        grid = (
            base_tbl
              .mark_rect(stroke="#E6ECF4", strokeWidth=1)
              .encode(
                  x=alt.X("Column:N", sort=present_cols, axis=alt.Axis(labels=False, ticks=False, domain=False, title=None)),
                  y=alt.Y("row_number:O", axis=alt.Axis(labels=False, ticks=False, domain=False, title=None)),
                  color=alt.condition("datum.row_number % 2 === 1", alt.value("#FAFAFA"), alt.value("#FFFFFF")),
              )
              .properties(width=table_width, height={"step": row_step})
        )
        cells = (
            base_tbl.mark_text(baseline="middle", fontSize=12, dx=6)
              .encode(
                  x=alt.X("Column:N", sort=present_cols, axis=alt.Axis(labels=False, ticks=False, domain=False, title=None)),
                  y=alt.Y("row_number:O", axis=alt.Axis(labels=False, ticks=False, domain=False, title=None)),
                  text=alt.Text("ValueStr:N"),
                  tooltip=[alt.Tooltip("Value:N", title="Value")],
              )
              .properties(width=table_width, height={"step": row_step})
        )
        return grid + cells

    # Header band (common)
    header_df = pd.DataFrame({"Column": present_cols, "Label": present_cols})
    header_bg = (
        alt.Chart(header_df)
           .mark_rect(fill="#F9FAFB", stroke="#E6ECF4", strokeWidth=1)
           .encode(x=alt.X("Column:N", sort=present_cols, axis=None))
           .properties(width=table_width, height=32)
    )
    header_text = (
        alt.Chart(header_df)
          .mark_text(fontWeight="bold", fontSize=12, baseline="middle", dx=6)
          .encode(x=alt.X("Column:N", sort=present_cols, axis=None), y=alt.value(16), text="Label:N")
          .properties(width=table_width, height=32)
    )

    # Build the 4 fallback layers
    layer_sub  = _table_layer(sub_sel,  cond_sub_active)
    layer_sys  = _table_layer(sys_sel,  cond_sys_active)
    layer_disc = _table_layer(disc_sel, cond_disc_active)
    layer_all  = _table_layer(None,     cond_none)  # no selection → show all

    table = alt.vconcat(header_bg + header_text,
                        layer_sub + layer_sys + layer_disc + layer_all,
                        spacing=0)

    return (
        alt.vconcat(
            alt.hconcat(disc, sys, sub).resolve_scale(color="independent"),
            table,
            spacing=12
        )
        .configure_view(stroke=None)
        .configure(background="white", padding=0)
        .configure_title(fontSize=14, color="#0B1220", fontWeight="bold", anchor="middle")
    )


# -------------------- Demo Mock Data (unchanged sections) --------------------
def mock_materials(seed=1):
    np.random.seed(seed)
    rng = pd.date_range("2025-02-01", periods=45, freq="2D")
    discs = ["Architectural", "Civil", "Controls", "ELV", "Electrical"]
    rows = []
    for d in discs:
        for dt in rng:
            total = np.random.randint(2, 16)
            ap = max(0, total - np.random.randint(0, 4))
            rj = np.random.randint(0, min(3, total - ap) + 1)
            ur = max(0, total - ap - rj)
            rows.append(
                dict(
                    Date=dt,
                    Discipline=d,
                    Submitted=total,
                    Approved=ap,
                    Rejected=rj,
                    UR=ur,
                    Source=np.random.choice(["AG", "CloseoutSoft"]),
                )
            )
    return pd.DataFrame(rows)


def mock_drawings(seed=2):
    np.random.seed(seed)
    rng = pd.date_range("2025-02-01", periods=40, freq="3D")
    discs = ["Architectural", "Civil", "Controls", "ELV", "Electrical"]
    rows = []
    for d in discs:
        for dt in rng:
            total = np.random.randint(1, 12)
            ap = max(0, total - np.random.randint(0, 3))
            ac = np.random.randint(0, min(3, total - ap) + 1)
            rj = np.random.randint(0, min(2, total - ap - ac) + 1)
            ur = max(0, total - ap - ac - rj)
            rows.append(
                dict(
                    Date=dt,
                    Discipline=d,
                    Submitted=total,
                    Approved=ap,
                    ApprovedWithComments=ac,
                    Rejected=rj,
                    UR=ur,
                    Source=np.random.choice(["AG", "CloseoutSoft"]),
                )
            )
    return pd.DataFrame(rows)


def mock_ncr(seed=3):
    np.random.seed(seed)
    rng = pd.date_range("2025-02-01", periods=70, freq="D")
    return pd.DataFrame(
        {
            "Date": np.random.choice(rng, 150),
            "Discipline": np.random.choice(
                ["Architectural", "Civil", "Controls", "ELV", "Electrical"], 150
            ),
            "Status": np.random.choice(["Open", "Closed"], 150, p=[0.45, 0.55]),
            "Severity": np.random.choice(["Low", "Medium", "High"], 150, p=[0.4, 0.45, 0.15]),
            "Source": np.random.choice(["AG", "CloseoutSoft"], 150),
        }
    )


def mock_wir(seed=4):
    np.random.seed(seed)
    rng = pd.date_range("2025-02-01", periods=90, freq="D")
    return pd.DataFrame(
        {
            "Date": np.random.choice(rng, 160),
            "Discipline": np.random.choice(
                ["Architectural", "Civil", "Controls", "ELV", "Electrical"], 160
            ),
            "Approved": np.random.choice([0, 1], 160, p=[0.1, 0.9]),
            "Source": np.random.choice(["AG", "CloseoutSoft"], 160),
        }
    )


def mock_ms(seed=5):
    np.random.seed(seed)
    rng = pd.date_range("2025-02-01", periods=60, freq="2D")
    return pd.DataFrame(
        {
            "Date": np.random.choice(rng, 120),
            "Discipline": np.random.choice(
                ["Architectural", "Civil", "Controls", "ELV", "Electrical"], 120
            ),
            "Submitted": np.random.randint(0, 6, 120),
            "Approved": np.random.randint(0, 6, 120),
            "Rejected": np.random.randint(0, 3, 120),
            "UR": np.random.randint(0, 3, 120),
            "Source": np.random.choice(["AG", "CloseoutSoft"], 120),
        }
    )


def mock_milestones():
    return pd.DataFrame(
        [
            {"Milestone": "Chilled Water", "TargetDate": "2025-04-30", "Status": "At Risk"},
            {"Milestone": "Project Handover", "TargetDate": "2025-08-31", "Status": "On Track"},
        ]
    )


def mock_site_visits():
    return pd.DataFrame(
        [
            {"Date": "2025-02-20", "Stakeholders": "Rebus, AGE, Consultant", "Notes": "Kickoff at RAK site"},
            {"Date": "2025-03-12", "Stakeholders": "Rebus, AGE", "Notes": "Register review & mapping"},
            {"Date": "2025-04-22", "Stakeholders": "Rebus", "Notes": "Monthly progress snapshot"},
        ]
    )


# -------------------- Load Demo Data --------------------
materials = mock_materials()
drawings = mock_drawings()
ncrs = mock_ncr()
wir = mock_wir()
ms = mock_ms()
milestones = mock_milestones()
sitevisits = mock_site_visits()


# -------------------- Sidebar Filters --------------------
def multiselect_with_all(label: str, options: list[str], *, default_all=True, key: str = "ms"):
    all_tag = "All"
    opts = [all_tag] + options
    widget_key = f"{key}_raw"
    prev_key = f"{key}_prev"

    if widget_key not in st.session_state:
        st.session_state[widget_key] = [all_tag] if default_all else []
    if prev_key not in st.session_state:
        st.session_state[prev_key] = st.session_state[widget_key][:]

    def _on_change():
        sel = st.session_state.get(widget_key, [])
        prev = st.session_state.get(prev_key, [])
        if "All" in sel and len(sel) > 1:
            all_added_now = ("All" in sel) and ("All" not in prev)
            if all_added_now:
                st.session_state[widget_key] = ["All"]
            else:
                st.session_state[widget_key] = [v for v in sel if v != "All"]
        elif len(sel) == 0 and default_all:
            st.session_state[widget_key] = ["All"]
        st.session_state[prev_key] = st.session_state[widget_key][:]

    sel = st.sidebar.multiselect(label, [all_tag] + options, key=widget_key, on_change=_on_change)
    return options if ("All" in sel or not sel) else [x for x in sel if x != "All"]


def selectbox_with_all(label: str, options: list[str], *, default="All", key=None) -> list[str]:
    all_tag = "All"
    opts = [all_tag] + options
    choice = st.sidebar.selectbox(label, opts, index=opts.index(default) if default in opts else 0, key=key)
    return options if choice == all_tag else [choice]


discipline_choices = sorted(
    list(
        {
            *materials.get("Discipline", pd.Series(dtype=str)).dropna().unique().tolist(),
            *drawings.get("Discipline", pd.Series(dtype=str)).dropna().unique().tolist(),
            *ncrs.get("Discipline", pd.Series(dtype=str)).dropna().unique().tolist(),
            *wir.get("Discipline", pd.Series(dtype=str)).dropna().unique().tolist(),
            *ms.get("Discipline", pd.Series(dtype=str)).dropna().unique().tolist(),
        }
    )
)
source_choices = ["AG", "CloseoutSoft"]

src_filter = selectbox_with_all("Source", source_choices, default="All", key="src_all")
sel_disc = multiselect_with_all("Discipline", discipline_choices, default_all=True, key="disc_all")

frames = [
    df for df in [materials, drawings, ncrs, wir, ms]
    if isinstance(df, pd.DataFrame) and not df.empty and "Date" in df.columns
]
if frames:
    min_date = min(df["Date"].min() for df in frames)
    max_date = max(df["Date"].max() for df in frames)
    start_date, end_date = st.sidebar.date_input("Date Range", (min_date.date(), max_date.date()), disabled=True)
else:
    today = pd.Timestamp.today().date()
    start_date, end_date = st.sidebar.date_input("Date Range", (today, today), disabled=True)


# -------------------- Apply filters --------------------
def apply_filters(df):
    if df is None or df.empty:
        return df
    out = df.copy()
    if "Source" in out.columns and src_filter:
        out = out[out["Source"].isin(src_filter)]
    if "Date" in out.columns:
        out = out[(out["Date"] >= pd.to_datetime(start_date)) & (out["Date"] <= pd.to_datetime(end_date))]
    if sel_disc and "Discipline" in out.columns:
        out = out[out["Discipline"].isin(sel_disc)]
    return out


f_mats = apply_filters(materials)
f_dwgs = apply_filters(drawings)
f_ncrs = apply_filters(ncrs)
f_wir = apply_filters(wir)
f_ms = apply_filters(ms)


# -------------------- KPI CARDS --------------------
m_total, m_approved = safe_sum(f_mats, "Submitted"), safe_sum(f_mats, "Approved")
d_total, d_approved = safe_sum(f_dwgs, "Submitted"), safe_sum(f_dwgs, "Approved")
n_total = int(len(f_ncrs)) if isinstance(f_ncrs, pd.DataFrame) else 0
n_closed = int((f_ncrs["Status"] == "Closed").sum()) if isinstance(f_ncrs, pd.DataFrame) and "Status" in f_ncrs else 0
ms_total, ms_approved = safe_sum(f_ms, "Submitted"), safe_sum(f_ms, "Approved")
hri = (
    0.4 * pct(m_approved, m_total)
    + 0.3 * pct(d_approved, d_total)
    + 0.2 * pct(ms_approved, ms_total)
    + 0.1 * pct(n_closed, n_total)
)


def render_kpi_cards():
    def s_pct(a, b):
        val = pct(a, b)
        return val, ("OK" if val >= 90 else ("WARN" if val >= 70 else "RISK"))

    m_pct, m_status = s_pct(m_approved, m_total)
    d_pct, _ = s_pct(d_approved, d_total)
    n_pct, n_status = s_pct(n_closed, n_total)
    ms_pct, _ = s_pct(ms_approved, ms_total)
    h_status = "OK" if hri >= 85 else ("WARN" if hri >= 70 else "RISK")

    cards = [
        {"label": "Material Approval %", "value": f"{m_pct:.1f}", "suffix": "%", "status": m_status},
        {"label": "Drawing Approval %", "value": f"{d_pct:.1f}", "suffix": "%", "status": None},
        {"label": "NCR Closure %", "value": f"{n_pct:.1f}", "suffix": "%", "status": n_status},
        {"label": "Method Statements %", "value": f"{ms_pct:.1f}", "suffix": "%", "status": None},
        {"label": "Handover Readiness", "value": f"{hri:.0f}", "suffix": "/100", "status": h_status},
    ]

    tiles = []
    for c in cards:
        status = c.get("status")
        badge = ""
        if status:
            cls = "ok" if status.upper() == "OK" else ("warn" if status.upper() == "WARN" else "risk")
            badge = f'<span class="pill {cls}">{status}</span>'
        tiles.append(
            f"""
            <div class="kpi-tile">
              <div class="kpi-head"><span class="kpi-label">{c['label']}</span>{badge}</div>
              <div class="kpi-val">{c['value']}{c.get('suffix','')}</div>
            </div>
            """.strip()
        )
    st.markdown('<div class="card-kpi"><div class="kpi-tiles">' + "\n".join(tiles) + "</div></div>", unsafe_allow_html=True)


render_kpi_cards()


# -------------------- Tabs --------------------
tabs = st.tabs(
    [
        "Overview",
        "Project Details",
        "Milestones",
        "Constraints",
        "Achievements",
        "Recommendations",
        "AG Summary",
        "CloseoutSoft Summary",
        "AG vs CloseoutSoft",
        "General Notes",
        "Handover Strategy",
        "Addendum: Site Visits",
        "Submittals",
    ]
)

# =============== Overview ===============
with tabs[0]:
    t1, t2 = st.columns(2)
    b1, b2 = st.columns(2)

    with t1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Materials – Status by Discipline**")
        if isinstance(f_mats, pd.DataFrame) and not f_mats.empty:
            df = f_mats.groupby("Discipline")[["Approved", "Rejected", "UR"]].sum().reset_index()
            long = df.melt(
                id_vars="Discipline",
                value_vars=["Approved", "Rejected", "UR"],
                var_name="Status",
                value_name="Count",
            )
            long["Status"] = long["Status"].fillna("(Blank)")
            long["Discipline"] = long["Discipline"].fillna("(Blank)")
            fig = px.bar(
                long, x="Discipline", y="Count", color="Status", barmode="stack",
                color_discrete_map=STATUS_COLORS, template=None
            )
            st.plotly_chart(style_fig(fig, height=240), use_container_width=True)
        else:
            st.caption("No material data in the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)

    with t2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**NCR Status**")
        if isinstance(f_ncrs, pd.DataFrame) and not f_ncrs.empty and "Status" in f_ncrs.columns:
            tmp = f_ncrs.copy()
            tmp["Status"] = tmp["Status"].fillna("(Blank)")
            fig = px.pie(
                tmp, names="Status", hole=0.55, color="Status",
                color_discrete_map=STATUS_COLORS, template=None
            )
            fig.update_traces(textinfo="percent", textposition="inside")
            fig.update_layout(margin=dict(l=8, r=8, t=16, b=16), showlegend=True)
            st.plotly_chart(style_fig(fig, height=240, showlegend=True), use_container_width=True)
        else:
            st.caption("No NCR data in the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)

    with b1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Shop Drawings – Status by Discipline**")
        if isinstance(f_dwgs, pd.DataFrame) and not f_dwgs.empty:
            df = (
                f_dwgs.groupby("Discipline")[["Approved", "ApprovedWithComments", "Rejected", "UR"]]
                .sum()
                .reset_index()
            )
            long = df.melt(
                id_vars="Discipline",
                value_vars=["Approved", "ApprovedWithComments", "Rejected", "UR"],
                var_name="Status",
                value_name="Count",
            )
            long["Status"] = long["Status"].fillna("(Blank)")
            long["Discipline"] = long["Discipline"].fillna("(Blank)")
            fig = px.bar(
                long, x="Discipline", y="Count", color="Status", barmode="stack",
                color_discrete_map=STATUS_COLORS, template=None
            )
            st.plotly_chart(style_fig(fig, height=240), use_container_width=True)
        else:
            st.caption("No drawings data in the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)

    with b2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**CloseoutSoft – Material Inspections**")
        if isinstance(f_ms, pd.DataFrame) and not f_ms.empty:
            grp = f_ms.groupby("Discipline")[["Approved", "Rejected", "UR"]].sum().reset_index()
            long = grp.melt(
                id_vars="Discipline",
                value_vars=["Approved", "Rejected", "UR"],
                var_name="Status",
                value_name="Count",
            )
            long["Status"] = long["Status"].fillna("(Blank)")
            long["Discipline"] = long["Discipline"].fillna("(Blank)")
            fig = px.bar(
                long, x="Discipline", y="Count", color="Status", barmode="stack",
                color_discrete_map=STATUS_COLORS, template=None,
            )
            st.plotly_chart(style_fig(fig, height=240), use_container_width=True)
        else:
            st.caption("No MIR data in the selected filters.")
        st.markdown('</div>', unsafe_allow_html=True)


# =============== Project Details ===============
with tabs[1]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Project Details")
    details = pd.DataFrame(
        [
            ["Project Name", "Wynn Al Marjan Island – District Cooling Plant 4 (WAMI)"],
            ["Project Goal", "DCP"],
            ["Client", "Wynn Al Marjan Island"],
            ["Main Contractor", "Al Ghurair Engineering & Power Contracting"],
            ["Consultant", "DC Pro Engineering"],
            ["Project Start", "2024-10-01"],
        ],
        columns=["Field", "Value"],
    )
    st.dataframe(details, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =============== Milestones ===============
with tabs[2]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.dataframe(milestones, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =============== Constraints ===============
with tabs[3]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        """
- **Restricted DMS Access** (ACONEX & DomeConnect).  
- **Site Access Limitations** for documentation activities.  
- **No Dedicated Documentation Team.**  
- **Duplication of Effort** across registers.  
- **Lack of Standardization** in mapping & formats.
"""
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =============== Achievements ===============
with tabs[4]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        """
- Work Activity Logs (weekly & on-demand).  
        - Terminology mapping matrix (AG ↔ CloseoutSoft).  
- Reporting templates aligned with AG formats.  
- Reusable report structures for future projects.
"""
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =============== Recommendations ===============
with tabs[5]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        """
- Improve system visibility in handover reports.  
- Refine classification between systems & deliverables.  
- Adopt standardized, CloseoutSoft-compatible templates.  
- Lock consultant cadence & expectations early.
"""
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =============== AG vs CloseoutSoft ===============
with tabs[6]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Material Submissions Summary**")
        if isinstance(f_mats, pd.DataFrame) and not f_mats.empty:
            grp = f_mats.groupby("Discipline")[["Submitted", "Approved", "Rejected", "UR"]].sum().reset_index()
            st.dataframe(grp, use_container_width=True, hide_index=True)
        else:
            st.caption("No data.")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Shop Drawings Summary**")
        if isinstance(f_dwgs, pd.DataFrame) and not f_dwgs.empty:
            grp = (
                f_dwgs.groupby("Discipline")[["Submitted", "Approved", "ApprovedWithComments", "Rejected", "UR"]]
                .sum()
                .reset_index()
            )
            st.dataframe(grp, use_container_width=True, hide_index=True)
        else:
            st.caption("No data.")
        st.markdown("</div>", unsafe_allow_html=True)

# =============== CloseoutSoft Summary ===============
with tabs[7]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Material Inspection Requests**")
        if isinstance(f_ms, pd.DataFrame) and not f_ms.empty:
            mir = f_ms.groupby("Discipline")[["Submitted", "Approved", "Rejected", "UR"]].sum().reset_index()
            st.dataframe(mir, use_container_width=True, hide_index=True)
        else:
            st.caption("No data.")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Material Submissions**")
        if isinstance(f_mats, pd.DataFrame) and not f_mats.empty:
            grp = f_mats.groupby("Discipline")[["Submitted", "Approved", "Rejected", "UR"]].sum().reset_index()
            st.dataframe(grp, use_container_width=True, hide_index=True)
        else:
            st.caption("No data.")
        st.markdown("</div>", unsafe_allow_html=True)

# =============== AG vs CloseoutSoft ===============
with tabs[8]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### AG vs CloseoutSoft – Comparison")
    st.markdown(
        """
- Scope & taxonomy mismatches observed across Materials/Drawings  
- CloseoutSoft can generate unified statistical reports for weekly/monthly meetings  
- Missing in AG: **WIR**, **Progress S-Curve**, **O&M Manuals**, **Spares**, **Snag/Punch List**
"""
    )
    if (
        isinstance(f_mats, pd.DataFrame)
        and isinstance(f_dwgs, pd.DataFrame)
        and not f_mats.empty
        and not f_dwgs.empty
        and "Source" in f_mats.columns
        and "Source" in f_dwgs.columns
        and "Submitted" in f_mats.columns
        and "Submitted" in f_dwgs.columns
    ):
        agg_a = f_mats.groupby(["Source"]).agg({"Submitted": "sum"}).reset_index()
        agg_b = f_dwgs.groupby(["Source"]).agg({"Submitted": "sum"}).reset_index()
        agg_a["Register"] = "Materials"
        agg_b["Register"] = "Drawings"
        comp = pd.concat([agg_a, agg_b], ignore_index=True)
        fig = px.bar(comp, x="Register", y="Submitted", color="Source", barmode="group",
                     color_discrete_map=SOURCE_COLORS, template=None)
        st.plotly_chart(style_fig(fig, height=230), use_container_width=True)
    else:
        st.caption("Not enough data to compare.")
    st.markdown("</div>", unsafe_allow_html=True)

# =============== General Notes ===============
with tabs[9]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        """
- Misclassification of sub-systems in several registers.  
- Incomplete documentation for some MEP services; As-Built record gaps.  
- Inconsistent discipline mapping (Shop Drawings vs WIR).  
- Recommend consistent **Trade / Discipline / System** taxonomy.
"""
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =============== Handover Strategy ===============
with tabs[10]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Handover Strategy")
    st.markdown(
        """
- Implement system-wise handover with standardized templates.  
- Establish consultant coordination cadence.  
- Use integrated submittal/comment tracking to surface unresolved items.  
"""
    )
    st.progress(min(100, int(hri)))
    st.markdown("</div>", unsafe_allow_html=True)

# =============== Site Visits ===============
with tabs[11]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Site Visit Details")
    st.dataframe(sitevisits, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =============== Submittals Drill-down (Discipline → System → Subsystem) ===============
def load_reports_df() -> "pd.DataFrame | None":
    """
    Load Reports.json / Reports.xlsx from the app folder OR from a user upload.
    """
    import re

    def _norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

    def _auto_map_columns(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        norm_to_real = {_norm(c): c for c in df.columns}
        wants = {
            "Discipline": ["discipline", "trade", "division", "disciplinename"],
            "System": ["system", "systemname", "systems"],
            "Subsystem": ["subsystem", "subsystemname", "sub_system", "sub-system", "subsystemdesc", "subsystemdescription", "subsystemtype"],
            "Status": ["status", "submittalstatus", "state", "stage", "approvalstatus"],
            "Activity": ["activity", "activitytype", "register", "category"],
            "SubmittalDate": ["submittaldate", "date", "submittedon"],
            "InternalRefNumber": ["internalrefnumber", "refno", "internalref", "reference", "referenceid"],
            "Company": ["createdcompanyname", "company", "createdbycompany", "originatorcompany"],
            "Building": ["building", "buildingname"],
            "Level": ["level", "floor", "storey"],
            "Room": ["room", "roomname"],
        }
        rename = {}
        for target, cands in wants.items():
            found = None
            for cand in cands:
                for norm_col, real_col in norm_to_real.items():
                    if norm_col == cand or cand in norm_col:
                        found = real_col
                        break
                if found:
                    break
            if found:
                rename[found] = target
        if rename:
            df = df.rename(columns=rename)
        keep = [
            "Discipline","System","Subsystem","Status","Activity",
            "SubmittalDate","InternalRefNumber","Company","Building","Level","Room",
        ]
        df = df[[c for c in keep if c in df.columns]].copy()
        return df

    # 1) Try local files
    here = Path(__file__).parent if "__file__" in globals() else Path(".")
    discovered, found_name = None, None
    for name in ("Reports.json", "Reports.xlsx"):
        p = here / name
        if p.exists():
            try:
                if p.suffix.lower() == ".json":
                    with p.open("r", encoding="utf-8") as f:
                        j = _json.load(f)
                    if isinstance(j, list):
                        discovered = pd.DataFrame(j)
                    elif isinstance(j, dict):
                        list_key = next((k for k, v in j.items() if isinstance(v, list)), None)
                        discovered = pd.DataFrame(j[list_key]) if list_key else pd.json_normalize(j)
                    else:
                        discovered = pd.read_json(p)
                else:
                    discovered = pd.read_excel(p, sheet_name=0)
                found_name = name
            except Exception as e:
                st.warning(f"Found {name} but failed to read it: {e}")
                discovered = None
            break

    # 2) Uploader (always visible)
    uploaded = st.file_uploader(
        "Report Inputs",
        type=["json", "xlsx"],
        key="reports_uploader",
        accept_multiple_files=False,
        help="Upload Reports.json or Reports.xlsx. If present locally next to the app, it will be picked up automatically.",
    )

    df, src = None, None
    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".json"):
                j = _json.loads(uploaded.read().decode("utf-8"))
                if isinstance(j, list):
                    df = pd.DataFrame(j)
                elif isinstance(j, dict):
                    list_key = next((k for k, v in j.items() if isinstance(v, list)), None)
                    df = pd.DataFrame(j[list_key]) if list_key else pd.json_normalize(j)
                else:
                    df = pd.read_json(uploaded)
                src = f"uploaded file ({uploaded.name})"
            else:
                df = pd.read_excel(uploaded)
                src = f"uploaded file ({uploaded.name})"
        except Exception as e:
            st.error(f"Could not read uploaded file: {e}")
            df = None

    if df is None:
        df = discovered
        if discovered is not None:
            src = f"local file ({found_name})"

    if df is None or df.empty:
        st.info("Place **Reports.json** or **Reports.xlsx** next to `streamlit_app.py`, or use the **Report Inputs** control above.")
        return None

    # Auto-map & validate
    df = _auto_map_columns(df)
    if df is None or df.empty or "Discipline" not in df.columns or "System" not in df.columns:
        st.error("Reports file loaded, but required columns not found. Expect **Discipline, System** (plus Subsystem/Status/Activity if available).")
        return None

    with st.expander("REPORTS DATA", expanded=False):
        st.write(f"Source: **{src or 'unknown'}**")
        st.write("Columns:", list(df.columns))
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

    return df


with tabs[12]:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    reports_df = load_reports_df()

    if reports_df is not None and not reports_df.empty:
        # Only ACTIVITY dropdown (no Discipline/System widgets)
        if "Activity" in reports_df.columns:
            acts_raw = sorted(reports_df["Activity"].dropna().astype(str).unique().tolist())
            preferred = "MS" if "MS" in acts_raw else (acts_raw[0] if acts_raw else "(All)")
            acts = ["(All)"] + acts_raw
            if "activity_select" not in st.session_state:
                st.session_state["activity_select"] = preferred
            sel_act = st.selectbox("ACTIVITY", acts, key="activity_select")
            df_act = reports_df if sel_act == "(All)" else reports_df[reports_df["Activity"] == sel_act]
        else:
            df_act = reports_df

        chart = build_submittals_drilldown(df_act)
        st.altair_chart(chart, use_container_width=True)
        st.caption("Tip: Click to drill; double-click a donut to clear that level. The table automatically prefers Subsystem > System > Discipline.")

    st.markdown("</div>", unsafe_allow_html=True)

# NOTE: The details table is rendered inside build_submittals_drilldown with fallback logic (Subsystem → System → Discipline).
