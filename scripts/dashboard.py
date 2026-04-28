"""
Semantic Extraction — Interactive Accuracy Dashboard
Run: .venv/bin/python3.13 -m streamlit run scripts/dashboard.py
"""

import json
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Extraction Accuracy Dashboard",
    page_icon="📊",
    layout="wide",
)

ROOT           = Path(__file__).resolve().parent.parent
CANDIDATES_DIR = ROOT / "downloads/candidates"
COMPARISON_CSV = ROOT / "reports/field_comparison.csv"

SECTION_LABELS = {
    "GeneralInformation":    "General Information",
    "CoverageDetails":       "Coverage Details",
    "RiskAssessment":        "Risk Assessment",
    "EmployeeCategory":      "Employee Category",
    "EPLISpecificQuestions": "EPLI Specific Questions",
}

RESULT_COLORS = {
    "CORRECT":     "#22c55e",
    "MISMATCH":    "#f97316",
    "MISSING":     "#ef4444",
    "NOT_ON_FORM": "#94a3b8",
    "SKIP":        "#cbd5e1",
}

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_comparison():
    df = pd.read_csv(COMPARISON_CSV)
    df["Section_Label"] = df["Section"].map(SECTION_LABELS).fillna(df["Section"])
    df["DocShort"] = df["Document"].apply(
        lambda x: re.sub(r"\.(pdf|PDF)$", "", str(x))[:50]
    )
    return df

@st.cache_data
def load_candidates():
    out = {}
    for f in CANDIDATES_DIR.glob("*.json"):
        name = re.sub(r"^[0-9a-f\-]+__", "", f.name).replace(".candidates.json", "")
        out[name] = json.loads(f.read_text())
    return out

df  = load_comparison()
_candidates = load_candidates()

# ── Derived stats ─────────────────────────────────────────────────────────────
SCORED = {"CORRECT", "MISMATCH", "MISSING"}

total_candidates = 20
total_golden     = 18
matched          = 18
no_golden_docs   = ["chubb_application_do_epl_etc_2025.pdf", "25-26_EPL_CRIME_-_Chubb_Supp_App.pdf"]

scored_df  = df[df["Result"].isin(SCORED)]
overall_c  = (scored_df["Result"] == "CORRECT").sum()
overall_t  = len(scored_df)
overall_pct = round(overall_c / overall_t * 100, 1) if overall_t else 0

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Semantic Extraction — Accuracy Dashboard")
st.caption("Comparing system-extracted candidates against the manually created Golden Set.")

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Candidate Files", total_candidates)
k2.metric("Golden Set Docs", total_golden)
k3.metric("Matched Pairs", matched)
k4.metric("Overall Accuracy", f"{overall_pct}%", f"{overall_c}/{overall_t} fields")
k5.metric("Not Scored", len(no_golden_docs), "no golden entry")

st.divider()

# ── Row 1: Section accuracy  +  Result breakdown ──────────────────────────────
col_sec, col_pie = st.columns([3, 2])

with col_sec:
    st.subheader("Accuracy by Section")
    sec_rows = []
    for sec, label in SECTION_LABELS.items():
        sub  = df[(df["Section"] == sec) & df["Result"].isin(SCORED)]
        c    = (sub["Result"] == "CORRECT").sum()
        t    = len(sub)
        notf = (df[df["Section"] == sec]["Result"] == "NOT_ON_FORM").sum()
        sec_rows.append({
            "Section":           label,
            "Correct":           c,
            "Total Scored":      t,
            "Accuracy %":        round(c / t * 100, 1) if t else 0,
            "Correctly Absent":  notf,
        })
    sec_df = pd.DataFrame(sec_rows).sort_values("Accuracy %")

    fig_sec = px.bar(
        sec_df,
        x="Accuracy %",
        y="Section",
        orientation="h",
        text="Accuracy %",
        color="Accuracy %",
        color_continuous_scale=["#ef4444", "#f97316", "#eab308", "#22c55e"],
        range_color=[0, 100],
        custom_data=["Correct", "Total Scored", "Correctly Absent"],
    )
    fig_sec.update_traces(
        texttemplate="%{x}%",
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Correct: %{customdata[0]}/%{customdata[1]}<br>"
            "Correctly absent: %{customdata[2]}<extra></extra>"
        ),
    )
    fig_sec.update_layout(
        height=280,
        margin=dict(l=0, r=60, t=10, b=10),
        coloraxis_showscale=False,
        xaxis=dict(range=[0, 115]),
        yaxis_title=None,
    )
    st.plotly_chart(fig_sec, use_container_width=True, config={"displayModeBar": False})

with col_pie:
    st.subheader("Result Breakdown")
    counts = df["Result"].value_counts().reset_index()
    counts.columns = ["Result", "Count"]
    counts = counts[counts["Result"] != "SKIP"]
    fig_pie = px.pie(
        counts,
        names="Result",
        values="Count",
        color="Result",
        color_discrete_map=RESULT_COLORS,
        hole=0.45,
    )
    fig_pie.update_traces(
        textposition="outside",
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value} fields<extra></extra>",
    )
    fig_pie.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=10, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

st.divider()

# ── Row 2: Per-field accuracy chart ──────────────────────────────────────────
st.subheader("Per-Field Accuracy")

field_rows = []
for field, grp in df.groupby("Field"):
    sc   = grp[grp["Result"].isin(SCORED)]
    c    = (sc["Result"] == "CORRECT").sum()
    mm   = (sc["Result"] == "MISMATCH").sum()
    ms   = (sc["Result"] == "MISSING").sum()
    notf = (grp["Result"] == "NOT_ON_FORM").sum()
    t    = len(sc)
    sec  = grp["Section_Label"].iloc[0] if len(grp) else ""
    field_rows.append({
        "Field":            field,
        "Section":          sec,
        "Correct":          int(c),
        "Mismatch":         int(mm),
        "Missing":          int(ms),
        "Correctly Absent": int(notf),
        "Total Scored":     int(t),
        "Accuracy %":       round(c / t * 100, 1) if t else None,
    })

field_df = pd.DataFrame(field_rows)

# Filters
fc1, fc2, fc3 = st.columns([2, 2, 2])
with fc1:
    sec_filter = st.multiselect(
        "Filter by section",
        options=list(SECTION_LABELS.values()),
        default=list(SECTION_LABELS.values()),
    )
with fc2:
    show_no_data = st.checkbox("Include fields with no golden data", value=False)
with fc3:
    sort_by = st.selectbox("Sort by", ["Accuracy % (asc)", "Accuracy % (desc)", "Field name"])

filt = field_df[field_df["Section"].isin(sec_filter)].copy()
if not show_no_data:
    filt = filt[filt["Total Scored"] > 0]

if sort_by == "Accuracy % (asc)":
    filt = filt.sort_values("Accuracy %", ascending=True, na_position="first")
elif sort_by == "Accuracy % (desc)":
    filt = filt.sort_values("Accuracy %", ascending=False, na_position="last")
else:
    filt = filt.sort_values("Field")

fig_field = go.Figure()

# Store customdata: [field_name, result_type] for click handling
for result_type, color in [
    ("Correct",          RESULT_COLORS["CORRECT"]),
    ("Mismatch",         RESULT_COLORS["MISMATCH"]),
    ("Missing",          RESULT_COLORS["MISSING"]),
    ("Correctly Absent", RESULT_COLORS["NOT_ON_FORM"]),
]:
    result_key = result_type.upper().replace(" ", "_")
    fig_field.add_trace(go.Bar(
        y=filt["Field"],
        x=filt[result_type],
        name=result_type,
        orientation="h",
        marker_color=color,
        customdata=[[f, result_type] for f in filt["Field"]],
        hovertemplate=f"<b>%{{y}}</b><br>{result_type}: %{{x}}<br><i>Click to inspect documents</i><extra></extra>",
    ))

fig_field.update_layout(
    barmode="stack",
    height=max(350, len(filt) * 26),
    margin=dict(l=0, r=20, t=10, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
    xaxis_title="Number of documents",
    yaxis_title=None,
    yaxis=dict(autorange="reversed"),
    clickmode="event+select",
)

event = st.plotly_chart(
    fig_field,
    use_container_width=True,
    config={"displayModeBar": False},
    on_select="rerun",
    selection_mode="points",
    key="field_chart",
)

# ── Detail panel: shown when user clicks a bar segment ────────────────────────
selected_points = (event.selection or {}).get("points", [])
if selected_points:
    pt          = selected_points[0]
    clicked_field  = pt.get("y") or (pt.get("customdata") or [None])[0]
    clicked_result = (pt.get("customdata") or [None, None])[1]

    if clicked_field and clicked_result and clicked_result != "Correctly Absent":
        # Map display name back to CSV Result value
        result_map = {
            "Correct":  "CORRECT",
            "Mismatch": "MISMATCH",
            "Missing":  "MISSING",
        }
        csv_result = result_map.get(clicked_result, clicked_result)

        detail = df[
            (df["Field"] == clicked_field) & (df["Result"] == csv_result)
        ][["DocShort", "Golden", "System", "Result"]].copy()
        detail.columns = ["Document", "Expected (Golden)", "Got (System)", "Result"]

        emoji = {"CORRECT": "✅", "MISMATCH": "⚠️", "MISSING": "❌"}.get(csv_result, "")
        st.markdown(
            f"### {emoji} `{clicked_field}` — {clicked_result} in {len(detail)} document(s)"
        )

        def row_style(row):
            bg = {
                "CORRECT":  "background-color: #166534; color: #ffffff",
                "MISMATCH": "background-color: #92400e; color: #ffffff",
                "MISSING":  "background-color: #991b1b; color: #ffffff",
            }.get(row["Result"], "")
            return [bg] * len(row)

        st.dataframe(
            detail.style.apply(row_style, axis=1),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Document":         st.column_config.TextColumn(width="large"),
                "Expected (Golden)":st.column_config.TextColumn(width="large"),
                "Got (System)":     st.column_config.TextColumn(width="large"),
                "Result":           st.column_config.TextColumn(width="small"),
            },
        )
        st.caption("Click another bar segment to switch view, or click elsewhere to dismiss.")

st.divider()

# ── Row 3: Per-field accuracy table ──────────────────────────────────────────
st.subheader("Field Accuracy Table")

def style_acc(val):
    if pd.isna(val):
        return "color: #94a3b8"
    if val >= 80:
        return "background-color: #166534; color: #ffffff"
    if val >= 50:
        return "background-color: #854d0e; color: #ffffff"
    return "background-color: #991b1b; color: #ffffff"

display_df = filt[["Field", "Section", "Total Scored", "Correct", "Mismatch",
                    "Missing", "Correctly Absent", "Accuracy %"]].copy()
st.dataframe(
    display_df.style.map(style_acc, subset=["Accuracy %"]),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ── Row 4: Document explorer ──────────────────────────────────────────────────
st.subheader("Document Explorer")
st.caption("Select a document to see a field-by-field comparison between system output and the Golden Set.")

docs = sorted(df["DocShort"].dropna().unique())
selected_doc = st.selectbox("Select document", docs)

doc_df = df[df["DocShort"] == selected_doc].copy()

# Summary chips
d_scored = doc_df[doc_df["Result"].isin(SCORED)]
d_c  = (d_scored["Result"] == "CORRECT").sum()
d_mm = (d_scored["Result"] == "MISMATCH").sum()
d_ms = (d_scored["Result"] == "MISSING").sum()
d_t  = len(d_scored)
d_acc = round(d_c / d_t * 100, 1) if d_t else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Accuracy", f"{d_acc}%", f"{d_c}/{d_t}")
m2.metric("Correct",  d_c)
m3.metric("Mismatch", d_mm)
m4.metric("Missing",  d_ms)

# Result filter
res_filter = st.multiselect(
    "Show results",
    options=["CORRECT", "MISMATCH", "MISSING", "NOT_ON_FORM"],
    default=["MISMATCH", "MISSING"],
    key="doc_res_filter",
)

view = doc_df[doc_df["Result"].isin(res_filter)][
    ["Section_Label", "Field", "Golden", "System", "Result"]
].rename(columns={"Section_Label": "Section"})

def highlight_result(row):
    if row["Result"] == "CORRECT":
        bg = "background-color: #166534; color: #ffffff"
    elif row["Result"] == "MISMATCH":
        bg = "background-color: #92400e; color: #ffffff"
    elif row["Result"] == "MISSING":
        bg = "background-color: #991b1b; color: #ffffff"
    elif row["Result"] == "NOT_ON_FORM":
        bg = "background-color: #1e293b; color: #94a3b8"
    else:
        bg = ""
    return [bg] * len(row)

if view.empty:
    st.info("No records match the selected filters.")
else:
    st.dataframe(
        view.style.apply(highlight_result, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Section":  st.column_config.TextColumn("Section", width="medium"),
            "Field":    st.column_config.TextColumn("Field",   width="medium"),
            "Golden":   st.column_config.TextColumn("Expected (Golden)", width="large"),
            "System":   st.column_config.TextColumn("Got (System)",      width="large"),
            "Result":   st.column_config.TextColumn("Result",  width="small"),
        },
    )

st.divider()

# ── Row 5: Unscored candidates notice ────────────────────────────────────────
with st.expander("Candidates with no Golden Set entry (not scored)"):
    for n in no_golden_docs:
        st.write(f"• `{n}`")
    st.caption("These files were produced by the system but have no corresponding row in the Golden Set.")
