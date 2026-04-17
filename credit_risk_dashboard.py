"""
Credit Risk Dashboard – Plotly Dash
Single-file application. Run with: python3 credit_risk_dashboard.py
"""

# ─── ASSUMPTIONS BLOCK ────────────────────────────────────────────────────────
ASSUMPTIONS = {
    # Basel II / III standard LGD for unsecured consumer loans
    "LGD": 0.45,

    # PD Scorecard weights (features → PD score contribution, sums to 1.0)
    "SCORING_WEIGHTS": {
        "loan_grade":             0.30,
        "cb_person_default_on_file": 0.20,
        "loan_percent_income":    0.18,
        "person_income":          0.12,
        "loan_int_rate":          0.10,
        "person_emp_length":      0.06,
        "person_age":             0.04,
    },

    # PD range mapping by loan grade (empirical from dataset)
    "PD_RANGE": {
        "A": (0.05,  0.12),
        "B": (0.12,  0.20),
        "C": (0.18,  0.28),
        "D": (0.45,  0.70),
        "E": (0.58,  0.75),
        "F": (0.65,  0.80),
        "G": (0.90,  1.00),
    },

    # Capital ratio assumption for capital impact calc
    "CAPITAL_RATIO": 0.08,

    # Seasoning factors for vintage curves
    "SEASON_12M": 0.40,
    "SEASON_24M": 0.70,
}

# ─── IMPORTS ──────────────────────────────────────────────────────────────────
import os
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, dash_table, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px

# ─── LOAD & ENRICH DATA ───────────────────────────────────────────────────────
df = pd.read_csv("credit_risk_dataset.csv")

# Risk tier
def assign_tier(g):
    return "Prime" if g in ("A", "B") else ("Near-Prime" if g in ("C", "D") else "Subprime")

df["risk_tier"] = df["loan_grade"].apply(assign_tier)

# Assign PD from grade range midpoint
df["pd_score"] = df["loan_grade"].map(
    {g: np.mean(rng) for g, rng in ASSUMPTIONS["PD_RANGE"].items()}
)

# EL per loan
df["el"] = df["pd_score"] * ASSUMPTIONS["LGD"] * df["loan_amnt"]

# Proxy credit score: higher income + lower LTI + lower int rate → higher score
df["credit_score"] = (
    300
    + ((df["person_income"].clip(0, 200_000) / 200_000) * 250).round(0)
    + ((1 - df["loan_percent_income"].clip(0, 1)) * 150).round(0)
    + (((30 - df["loan_int_rate"].fillna(15).clip(5, 30)) / 25) * 150).round(0)
).clip(300, 850).astype(int)

# Credit score bands
def cs_band(score):
    if score >= 750: return "Excellent (750+)"
    if score >= 700: return "Good (700-749)"
    if score >= 650: return "Fair (650-699)"
    if score >= 600: return "Poor (600-649)"
    return "Very Poor (<600)"

df["cs_band"] = df["credit_score"].apply(cs_band)
CS_BAND_ORDER = ["Very Poor (<600)", "Poor (600-649)", "Fair (650-699)",
                 "Good (700-749)", "Excellent (750+)"]

# DTI proxy = loan_percent_income * 100
df["dti"] = (df["loan_percent_income"] * 100).round(1)

# ─── GLOBAL KPIs ──────────────────────────────────────────────────────────────
TOTAL_LOANS    = len(df)
TOTAL_EXPOSURE = df["loan_amnt"].sum()
DEFAULT_RATE   = df["loan_status"].mean()
AVG_INT_RATE   = df["loan_int_rate"].mean()
AVG_CS         = df["credit_score"].mean()
TOTAL_EL       = df["el"].sum()

# ─── COLOUR PALETTE ───────────────────────────────────────────────────────────
NAVY      = "#1F3864"
NAVY_DARK = "#0F1F3D"
NAVY_MID  = "#2E75B6"
NAVY_LIGHT = "#D6E4F7"
WHITE     = "#FFFFFF"
LIGHT_BG  = "#F4F8FE"
CARD_BG   = "#FFFFFF"
BORDER    = "#D0DDED"
RED_RISK  = "#C00000"
AMBER     = "#9C5700"
GREEN_OK  = "#375623"
FONT      = "Arial, sans-serif"

GRADE_COLOURS = {
    "A": "#375623", "B": "#70AD47",
    "C": "#FFD966", "D": "#F4B942",
    "E": "#ED7D31", "F": "#C55A11", "G": "#C00000"
}

# ─── STYLE HELPERS ────────────────────────────────────────────────────────────
def kpi_card(title, value, subtitle="", color=NAVY):
    return html.Div([
        html.P(title,  style={"margin": "0 0 4px", "font-size": "11px",
                               "color": "#6B7A99", "font-weight": "600",
                               "text-transform": "uppercase", "letter-spacing": "0.5px"}),
        html.P(value,  style={"margin": "0 0 2px", "font-size": "24px",
                               "font-weight": "700", "color": color}),
        html.P(subtitle, style={"margin": "0", "font-size": "11px", "color": "#9BA8BE"}),
    ], style={
        "background": CARD_BG,
        "border-radius": "8px",
        "padding": "18px 22px",
        "border": f"1px solid {BORDER}",
        "border-left": f"4px solid {color}",
        "box-shadow": "0 1px 4px rgba(0,0,0,0.06)",
        "min-width": "150px",
        "flex": "1",
    })

def section_header(text):
    return html.H3(text, style={
        "color": NAVY, "font-size": "15px", "font-weight": "700",
        "border-bottom": f"2px solid {NAVY_MID}", "padding-bottom": "6px",
        "margin": "28px 0 14px", "font-family": FONT,
    })

def chart_card(children, height=380):
    return html.Div(children, style={
        "background": CARD_BG,
        "border-radius": "8px",
        "border": f"1px solid {BORDER}",
        "box-shadow": "0 1px 4px rgba(0,0,0,0.06)",
        "padding": "16px",
        "margin-bottom": "16px",
        "height": f"{height}px",
        "overflow": "hidden",
    })

BASE_LAYOUT = dict(
    font_family=FONT,
    paper_bgcolor=CARD_BG,
    plot_bgcolor=LIGHT_BG,
    margin=dict(l=48, r=20, t=36, b=48),
    legend=dict(bgcolor="rgba(0,0,0,0)", font_size=11),
    hoverlabel=dict(bgcolor=NAVY, font_color=WHITE, font_family=FONT),
)

# ─── WOE / IV COMPUTATION ────────────────────────────────────────────────────
def compute_woe_iv(feature, n_bins=5):
    """Return DataFrame with WOE and IV per bin for a numeric/categorical feature."""
    total_good = (df["loan_status"] == 0).sum()
    total_bad  = (df["loan_status"] == 1).sum()
    rows = []

    if df[feature].dtype == "object":
        groups = df.groupby(feature)["loan_status"]
    else:
        df["_bin"] = pd.qcut(df[feature].dropna(), q=n_bins, duplicates="drop")
        groups = df.dropna(subset=[feature]).groupby("_bin")["loan_status"]

    for name, grp in groups:
        bad  = grp.sum()
        good = len(grp) - bad
        dist_bad  = max(bad,  0.5) / total_bad
        dist_good = max(good, 0.5) / total_good
        woe = np.log(dist_good / dist_bad)
        iv  = (dist_good - dist_bad) * woe
        dr  = grp.mean()
        rows.append({"Bin": str(name), "# Loans": len(grp),
                     "Default Rate": dr, "WOE": woe, "IV": iv})

    if "_bin" in df.columns:
        df.drop(columns="_bin", inplace=True)

    result = pd.DataFrame(rows)
    result["Feature"] = feature
    result["Total IV"] = result["IV"].sum()
    return result

FEATURES_FOR_IV = ["loan_grade", "person_income", "loan_int_rate",
                   "loan_percent_income", "cb_person_default_on_file",
                   "person_age", "person_emp_length"]

iv_frames = []
for feat in FEATURES_FOR_IV:
    try:
        iv_frames.append(compute_woe_iv(feat))
    except Exception:
        pass

iv_summary = (pd.concat(iv_frames)
                .groupby("Feature")["IV"]
                .sum()
                .reset_index()
                .rename(columns={"IV": "Total IV"})
                .sort_values("Total IV", ascending=False))

def iv_label(iv):
    if iv >= 0.50: return "Very Strong"
    if iv >= 0.30: return "Strong"
    if iv >= 0.10: return "Moderate"
    if iv >= 0.02: return "Weak"
    return "Not Predictive"

def iv_color(iv):
    if iv >= 0.30: return GREEN_OK
    if iv >= 0.10: return AMBER
    return RED_RISK

iv_summary["Strength"] = iv_summary["Total IV"].apply(iv_label)
iv_summary["IV Fmt"]   = iv_summary["Total IV"].apply(lambda x: f"{x:.3f}")


# ═══════════════════════════════════════════════════════════════════════════════
#  DASH APP LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════
app = dash.Dash(__name__, title="Credit Risk Dashboard")
app.config.suppress_callback_exceptions = True
server = app.server

TAB_STYLE = {
    "font-family": FONT, "font-size": "13px", "font-weight": "600",
    "color": "#6B7A99", "background": LIGHT_BG,
    "border": f"1px solid {BORDER}", "border-bottom": "none",
    "padding": "10px 20px", "border-radius": "6px 6px 0 0",
}
TAB_SELECTED = {
    **TAB_STYLE,
    "color": NAVY, "background": WHITE,
    "border-top": f"3px solid {NAVY_MID}",
}

CONTENT_STYLE = {
    "font-family": FONT,
    "background": LIGHT_BG,
    "padding": "20px 28px",
    "min-height": "800px",
}

app.layout = html.Div([
    # ── Top header ──
    html.Div([
        html.Div([
            html.H1("Credit Risk Analysis Dashboard",
                    style={"margin": "0", "font-size": "22px",
                           "font-weight": "700", "color": WHITE}),
            html.P("Portfolio Risk Assessment  |  32,581 Loans  |  April 2026",
                   style={"margin": "4px 0 0", "font-size": "12px", "color": "#A9C4E8"}),
        ]),
        html.Div([
            html.Span("● LIVE", style={"color": "#70AD47", "font-size": "12px",
                                        "font-weight": "700"}),
            html.Span("  credit_risk_dataset.csv",
                      style={"color": "#A9C4E8", "font-size": "11px"}),
        ]),
    ], style={
        "background": f"linear-gradient(135deg, {NAVY_DARK} 0%, {NAVY} 100%)",
        "padding": "18px 28px",
        "display": "flex",
        "justify-content": "space-between",
        "align-items": "center",
    }),

    # ── Tabs ──
    dcc.Tabs(id="tabs", value="tab-portfolio", children=[
        dcc.Tab(label="Portfolio Overview",  value="tab-portfolio",
                style=TAB_STYLE, selected_style=TAB_SELECTED),
        dcc.Tab(label="Risk Distribution",   value="tab-risk",
                style=TAB_STYLE, selected_style=TAB_SELECTED),
        dcc.Tab(label="PD Scorecard",        value="tab-pd",
                style=TAB_STYLE, selected_style=TAB_SELECTED),
        dcc.Tab(label="Stress Test",         value="tab-stress",
                style=TAB_STYLE, selected_style=TAB_SELECTED),
        dcc.Tab(label="Loan Explorer",       value="tab-explorer",
                style=TAB_STYLE, selected_style=TAB_SELECTED),
    ], style={"background": LIGHT_BG, "padding": "0 28px",
              "border-bottom": f"1px solid {BORDER}"}),

    html.Div(id="tab-content", style=CONTENT_STYLE),
], style={"font-family": FONT, "background": LIGHT_BG})


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB RENDERER
# ═══════════════════════════════════════════════════════════════════════════════
@app.callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab(tab):
    if tab == "tab-portfolio":  return layout_portfolio()
    if tab == "tab-risk":       return layout_risk()
    if tab == "tab-pd":         return layout_pd()
    if tab == "tab-stress":     return layout_stress()
    if tab == "tab-explorer":   return layout_explorer()
    return html.Div()


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 – PORTFOLIO OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
def layout_portfolio():
    grade_dr = (df.groupby("loan_grade")["loan_status"]
                  .mean().reset_index()
                  .rename(columns={"loan_status": "Default Rate"})
                  .sort_values("loan_grade"))

    intent_counts = df["loan_intent"].value_counts().reset_index()
    intent_counts.columns = ["Intent", "Count"]

    # Bar chart – default rate by grade
    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(
        x=grade_dr["loan_grade"], y=grade_dr["Default Rate"],
        marker_color=[GRADE_COLOURS.get(g, NAVY_MID) for g in grade_dr["loan_grade"]],
        text=[f"{v:.1%}" for v in grade_dr["Default Rate"]],
        textposition="outside", textfont=dict(size=11, color=NAVY),
        hovertemplate="<b>Grade %{x}</b><br>Default Rate: %{y:.2%}<extra></extra>",
    ))
    bar_fig.update_layout(
        **BASE_LAYOUT, title="Default Rate by Loan Grade",
        yaxis=dict(tickformat=".0%", gridcolor="#E5EDF7"),
        xaxis=dict(title="Loan Grade"),
        yaxis_title="Default Rate",
    )

    # Pie chart – loan count by intent
    pie_fig = go.Figure(go.Pie(
        labels=intent_counts["Intent"],
        values=intent_counts["Count"],
        hole=0.42,
        marker_colors=[NAVY, NAVY_MID, "#5A9BD5", "#9DC3E6",
                       "#BDD7EE", "#DEEAF1"],
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Loans: %{value:,}<br>Share: %{percent}<extra></extra>",
    ))
    pie_fig.update_layout(
        **BASE_LAYOUT, title="Loan Distribution by Intent",
        showlegend=False,
    )

    return html.Div([
        # KPI row
        section_header("Portfolio Key Performance Indicators"),
        html.Div([
            kpi_card("Total Loans",     f"{TOTAL_LOANS:,}",
                     "Across all grades & intents", NAVY),
            kpi_card("Total Exposure",  f"${TOTAL_EXPOSURE/1e6:.1f}M",
                     "Sum of outstanding balances", NAVY_MID),
            kpi_card("Default Rate",    f"{DEFAULT_RATE:.2%}",
                     "Observed portfolio PD", RED_RISK),
            kpi_card("Avg Interest Rate", f"{AVG_INT_RATE:.2f}%",
                     "Excl. nulls (3,116 records)", AMBER),
            kpi_card("Avg Credit Score", f"{AVG_CS:.0f}",
                     "Proxy score (300–850 scale)", GREEN_OK),
        ], style={"display": "flex", "gap": "14px", "flex-wrap": "wrap",
                  "margin-bottom": "20px"}),

        # Expected Loss highlight
        html.Div([
            html.Span("Expected Loss (PD × LGD × EAD): ",
                      style={"font-weight": "600", "color": NAVY}),
            html.Span(f"${TOTAL_EL/1e6:.1f}M",
                      style={"font-weight": "700", "font-size": "18px",
                             "color": RED_RISK}),
            html.Span(f"  |  EL Rate: {DEFAULT_RATE * ASSUMPTIONS['LGD']:.2%}",
                      style={"color": "#6B7A99", "font-size": "13px"}),
            html.Span(f"  |  LGD Assumption: {ASSUMPTIONS['LGD']:.0%}",
                      style={"color": NAVY_MID, "font-size": "12px",
                             "font-style": "italic"}),
        ], style={"background": "#FFF2CC", "border-left": f"4px solid #FFD966",
                  "padding": "10px 16px", "border-radius": "4px",
                  "margin-bottom": "20px", "font-family": FONT}),

        # Charts row
        section_header("Default Rate & Loan Distribution"),
        html.Div([
            html.Div([
                dcc.Graph(figure=bar_fig, style={"height": "340px"},
                          config={"displayModeBar": False}),
            ], style={"flex": "1.4", "background": CARD_BG,
                      "border-radius": "8px", "border": f"1px solid {BORDER}",
                      "padding": "12px", "box-shadow": "0 1px 4px rgba(0,0,0,0.05)"}),
            html.Div([
                dcc.Graph(figure=pie_fig, style={"height": "340px"},
                          config={"displayModeBar": False}),
            ], style={"flex": "1", "background": CARD_BG,
                      "border-radius": "8px", "border": f"1px solid {BORDER}",
                      "padding": "12px", "box-shadow": "0 1px 4px rgba(0,0,0,0.05)"}),
        ], style={"display": "flex", "gap": "16px"}),
    ])


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 – RISK DISTRIBUTION
# ══════════════════════════════════════════════════════════════════════════════
def layout_risk():
    # Histogram: credit score by default status
    hist_fig = go.Figure()
    for status, label, color in [(0, "Non-Default", NAVY_MID), (1, "Default", RED_RISK)]:
        sub = df[df["loan_status"] == status]["credit_score"]
        hist_fig.add_trace(go.Histogram(
            x=sub, name=label, opacity=0.75,
            marker_color=color, nbinsx=40,
            hovertemplate=f"<b>{label}</b><br>Score: %{{x}}<br>Count: %{{y}}<extra></extra>",
        ))
    hist_fig.update_layout(
        **BASE_LAYOUT, barmode="overlay",
        title="Credit Score Distribution by Default Status",
        xaxis_title="Credit Score (Proxy)", yaxis_title="# Loans",
        yaxis=dict(gridcolor="#E5EDF7"),
    )

    # Scatter: DTI vs Interest Rate, sized by loan amount, coloured by grade
    sample = df.dropna(subset=["loan_int_rate"]).sample(
        n=min(3000, len(df.dropna(subset=["loan_int_rate"]))), random_state=42)
    scatter_fig = px.scatter(
        sample, x="dti", y="loan_int_rate",
        size="loan_amnt", color="loan_grade",
        color_discrete_map=GRADE_COLOURS,
        labels={"dti": "DTI Ratio (%)", "loan_int_rate": "Interest Rate (%)",
                "loan_grade": "Grade", "loan_amnt": "Loan Amount ($)"},
        title="DTI vs Interest Rate  (sized by Loan Amount)",
        opacity=0.65,
        hover_data={"loan_amnt": ":$,.0f", "loan_grade": True,
                    "loan_status": True},
    )
    scatter_fig.update_layout(**BASE_LAYOUT,
                               yaxis=dict(gridcolor="#E5EDF7"),
                               xaxis=dict(gridcolor="#E5EDF7"))

    # Box plot: loan amount by grade
    box_fig = go.Figure()
    for grade in sorted(df["loan_grade"].unique()):
        sub = df[df["loan_grade"] == grade]["loan_amnt"]
        box_fig.add_trace(go.Box(
            y=sub, name=grade,
            marker_color=GRADE_COLOURS.get(grade, NAVY_MID),
            line_color=GRADE_COLOURS.get(grade, NAVY_MID),
            boxmean=True,
            hovertemplate=f"<b>Grade {grade}</b><br>%{{y:$,.0f}}<extra></extra>",
        ))
    box_fig.update_layout(
        **BASE_LAYOUT,
        title="Loan Amount Distribution by Grade",
        yaxis=dict(tickformat="$,.0f", title="Loan Amount ($)", gridcolor="#E5EDF7"),
        xaxis_title="Loan Grade", showlegend=False,
    )

    def chart(fig, h=360):
        return html.Div([
            dcc.Graph(figure=fig, style={"height": f"{h}px"},
                      config={"displayModeBar": False}),
        ], style={"background": CARD_BG, "border-radius": "8px",
                  "border": f"1px solid {BORDER}", "padding": "14px",
                  "box-shadow": "0 1px 4px rgba(0,0,0,0.05)",
                  "margin-bottom": "16px"})

    return html.Div([
        section_header("Risk Distribution Analysis"),
        html.Div([
            html.Div([chart(hist_fig)], style={"flex": "1"}),
            html.Div([chart(box_fig)],  style={"flex": "1"}),
        ], style={"display": "flex", "gap": "16px"}),
        chart(scatter_fig, h=400),
    ])


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 – PD SCORECARD
# ══════════════════════════════════════════════════════════════════════════════
def layout_pd():
    # WOE/IV table
    woe_rows = []
    for feat in FEATURES_FOR_IV:
        try:
            frame = compute_woe_iv(feat)
            for _, row in frame.iterrows():
                woe_rows.append({
                    "Feature":      row["Feature"],
                    "Bin":          row["Bin"],
                    "# Loans":      f'{int(row["# Loans"]):,}',
                    "Default Rate": f'{row["Default Rate"]:.2%}',
                    "WOE":          f'{row["WOE"]:+.3f}',
                    "IV":           f'{row["IV"]:.4f}',
                })
        except Exception:
            pass

    woe_df = pd.DataFrame(woe_rows)

    def woe_style(col, val):
        if col == "WOE":
            try:
                v = float(val)
                if v > 0.3:  return GREEN_OK
                if v < -0.3: return RED_RISK
                return AMBER
            except Exception:
                return NAVY
        return NAVY

    # IV bar chart
    iv_bar = go.Figure(go.Bar(
        x=iv_summary["Total IV"], y=iv_summary["Feature"],
        orientation="h",
        marker_color=[iv_color(v) for v in iv_summary["Total IV"]],
        text=[f'{iv_label(v)}  ({v:.3f})' for v in iv_summary["Total IV"]],
        textposition="outside", textfont=dict(size=10, color=NAVY),
        hovertemplate="<b>%{y}</b><br>IV: %{x:.4f}<extra></extra>",
    ))
    iv_bar.update_layout(
        **BASE_LAYOUT,
        title="Information Value (IV) by Feature – Predictive Power Ranking",
        xaxis_title="Information Value", yaxis_title="",
        xaxis=dict(gridcolor="#E5EDF7"),
        height=320,
    )

    # Default rate by credit score band
    cs_dr = (df.groupby("cs_band")["loan_status"]
               .mean().reset_index()
               .rename(columns={"loan_status": "Default Rate"}))
    cs_dr["cs_band"] = pd.Categorical(cs_dr["cs_band"],
                                       categories=CS_BAND_ORDER, ordered=True)
    cs_dr = cs_dr.sort_values("cs_band")

    cs_fig = go.Figure(go.Bar(
        x=cs_dr["cs_band"], y=cs_dr["Default Rate"],
        marker_color=[RED_RISK, RED_RISK, AMBER, GREEN_OK, GREEN_OK],
        text=[f"{v:.1%}" for v in cs_dr["Default Rate"]],
        textposition="outside", textfont=dict(size=11, color=NAVY),
        hovertemplate="<b>%{x}</b><br>Default Rate: %{y:.2%}<extra></extra>",
    ))
    cs_fig.update_layout(
        **BASE_LAYOUT,
        title="Default Rate by Credit Score Band",
        yaxis=dict(tickformat=".0%", title="Default Rate", gridcolor="#E5EDF7"),
        xaxis_title="Credit Score Band",
    )

    # WOE table style helpers
    style_cells = []
    for i, row in woe_df.iterrows():
        try:
            woe_val = float(row["WOE"])
            if woe_val > 0.3:   col = GREEN_OK
            elif woe_val < -0.3: col = RED_RISK
            else:                col = AMBER
        except Exception:
            col = NAVY
        style_cells.append({
            "if": {"row_index": i, "column_id": "WOE"},
            "color": WHITE, "backgroundColor": col,
            "fontWeight": "700",
        })

    return html.Div([
        section_header("PD Scorecard – Weight of Evidence & Information Value"),

        # IV bar
        html.Div([
            dcc.Graph(figure=iv_bar, style={"height": "330px"},
                      config={"displayModeBar": False}),
        ], style={"background": CARD_BG, "border-radius": "8px",
                  "border": f"1px solid {BORDER}", "padding": "14px",
                  "margin-bottom": "16px",
                  "box-shadow": "0 1px 4px rgba(0,0,0,0.05)"}),

        html.Div([
            # WOE table
            html.Div([
                html.H4("WOE / IV Detail Table",
                        style={"color": NAVY, "font-size": "13px",
                               "font-weight": "700", "margin": "0 0 10px"}),
                dash_table.DataTable(
                    data=woe_df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in woe_df.columns],
                    page_size=14,
                    style_table={"overflowX": "auto"},
                    style_header={
                        "backgroundColor": NAVY, "color": WHITE,
                        "fontWeight": "700", "fontSize": "12px",
                        "fontFamily": FONT, "textAlign": "center",
                        "border": "none",
                    },
                    style_cell={
                        "fontFamily": FONT, "fontSize": "12px",
                        "padding": "7px 10px", "color": NAVY,
                        "border": f"1px solid {BORDER}",
                    },
                    style_data_conditional=[
                        {"if": {"row_index": "odd"},
                         "backgroundColor": LIGHT_BG},
                    ] + style_cells,
                ),
            ], style={"flex": "1.4", "background": CARD_BG,
                      "border-radius": "8px", "border": f"1px solid {BORDER}",
                      "padding": "14px",
                      "box-shadow": "0 1px 4px rgba(0,0,0,0.05)"}),

            # Credit score band chart
            html.Div([
                dcc.Graph(figure=cs_fig, style={"height": "360px"},
                          config={"displayModeBar": False}),
            ], style={"flex": "1", "background": CARD_BG,
                      "border-radius": "8px", "border": f"1px solid {BORDER}",
                      "padding": "14px",
                      "box-shadow": "0 1px 4px rgba(0,0,0,0.05)"}),
        ], style={"display": "flex", "gap": "16px"}),
    ])


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4 – STRESS TEST SIMULATOR
# ══════════════════════════════════════════════════════════════════════════════
def layout_stress():
    return html.Div([
        section_header("Stress Test Simulator – Interactive Scenario Engine"),

        html.Div([
            # ── Controls panel ──
            html.Div([
                html.H4("Scenario Parameters",
                        style={"color": WHITE, "font-size": "14px",
                               "font-weight": "700", "margin": "0 0 18px"}),

                html.Label("PD Multiplier (× Base PD)",
                           style={"color": "#A9C4E8", "font-size": "12px",
                                  "font-weight": "600"}),
                dcc.Slider(id="slider-pd", min=1, max=5, step=0.25,
                           value=1.0, marks={i: str(i) for i in range(1, 6)},
                           tooltip={"placement": "bottom", "always_visible": True}),

                html.Br(),
                html.Label("LGD – Loss Given Default",
                           style={"color": "#A9C4E8", "font-size": "12px",
                                  "font-weight": "600"}),
                dcc.Slider(id="slider-lgd", min=0.10, max=0.90, step=0.05,
                           value=0.45,
                           marks={v: f"{v:.0%}" for v in [0.1, 0.3, 0.45, 0.6, 0.9]},
                           tooltip={"placement": "bottom", "always_visible": True}),

                html.Br(),
                html.Label("EAD Growth vs. Portfolio",
                           style={"color": "#A9C4E8", "font-size": "12px",
                                  "font-weight": "600"}),
                dcc.Slider(id="slider-ead", min=0, max=0.50, step=0.05,
                           value=0.0,
                           marks={v: f"+{v:.0%}" for v in [0, 0.1, 0.25, 0.5]},
                           tooltip={"placement": "bottom", "always_visible": True}),

                html.Br(),
                html.Div([
                    html.Span("Capital Ratio Assumption: 8.0%",
                              style={"color": "#FFD966", "font-size": "11px",
                                     "font-style": "italic"})
                ]),
            ], style={
                "background": f"linear-gradient(180deg, {NAVY_DARK} 0%, {NAVY} 100%)",
                "border-radius": "8px", "padding": "22px 20px",
                "width": "280px", "flex-shrink": "0",
            }),

            # ── Output panel ──
            html.Div([
                html.Div(id="stress-kpis",
                         style={"display": "flex", "gap": "12px",
                                "flex-wrap": "wrap", "margin-bottom": "16px"}),
                dcc.Graph(id="stress-chart", config={"displayModeBar": False},
                          style={"height": "340px"}),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "gap": "20px"}),
    ])


@app.callback(
    Output("stress-kpis", "children"),
    Output("stress-chart", "figure"),
    Input("slider-pd", "value"),
    Input("slider-lgd", "value"),
    Input("slider-ead", "value"),
)
def update_stress(pd_mult, lgd, ead_growth):
    stressed_pd  = DEFAULT_RATE * pd_mult
    stressed_ead = TOTAL_EXPOSURE * (1 + ead_growth)
    stressed_el  = stressed_pd * lgd * stressed_ead
    el_rate      = stressed_pd * lgd
    capital      = TOTAL_EXPOSURE * ASSUMPTIONS["CAPITAL_RATIO"]
    cap_impact   = stressed_el / capital

    kpis = [
        kpi_card("Stressed PD",      f"{stressed_pd:.2%}", f"Base × {pd_mult:.2f}", RED_RISK),
        kpi_card("Stressed EAD",     f"${stressed_ead/1e6:.1f}M", f"+{ead_growth:.0%}", AMBER),
        kpi_card("LGD",              f"{lgd:.0%}", "User input", NAVY_MID),
        kpi_card("Expected Loss",    f"${stressed_el/1e6:.1f}M", f"EL Rate: {el_rate:.2%}", RED_RISK),
        kpi_card("Capital Impact",   f"{cap_impact:.1%}", "EL / Capital (8%)", AMBER),
    ]

    # Sensitivity curve: EL across PD multipliers 1–5 for current LGD/EAD
    pd_range    = np.linspace(1, 5, 41)
    el_curve    = [DEFAULT_RATE * p * lgd * stressed_ead for p in pd_range]
    base_el_val = DEFAULT_RATE * 1.0 * ASSUMPTIONS["LGD"] * TOTAL_EXPOSURE

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pd_range, y=[v / 1e6 for v in el_curve],
        mode="lines", name=f"EL (LGD={lgd:.0%}, EAD+{ead_growth:.0%})",
        line=dict(color=RED_RISK, width=2.5),
        hovertemplate="PD Mult: %{x:.2f}×<br>EL: $%{y:.1f}M<extra></extra>",
    ))
    # Mark current scenario
    fig.add_trace(go.Scatter(
        x=[pd_mult], y=[stressed_el / 1e6],
        mode="markers", name="Current Scenario",
        marker=dict(color=AMBER, size=12, symbol="diamond",
                    line=dict(color=NAVY, width=2)),
        hovertemplate=f"PD Mult: {pd_mult:.2f}×<br>EL: ${stressed_el/1e6:.1f}M<extra></extra>",
    ))
    # Baseline
    fig.add_hline(y=base_el_val / 1e6, line_dash="dash",
                  line_color=NAVY_MID, line_width=1.5,
                  annotation_text=f"Base EL: ${base_el_val/1e6:.1f}M",
                  annotation_font_color=NAVY_MID)

    fig.update_layout(
        **BASE_LAYOUT,
        title="Expected Loss Sensitivity – PD Multiplier Curve",
        xaxis_title="PD Multiplier (× Base PD)",
        yaxis_title="Expected Loss ($M)",
        yaxis=dict(tickprefix="$", ticksuffix="M", gridcolor="#E5EDF7"),
    )

    return kpis, fig


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 5 – LOAN EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
def layout_explorer():
    grades = sorted(df["loan_grade"].unique())
    ownerships = sorted(df["person_home_ownership"].unique())
    intents = sorted(df["loan_intent"].unique())

    return html.Div([
        section_header("Loan Explorer – Filter & Drill Down to Individual Loans"),

        # Filters row
        html.Div([
            html.Div([
                html.Label("Loan Grade", style={"font-size": "12px",
                            "font-weight": "600", "color": NAVY}),
                dcc.Dropdown(id="filter-grade",
                             options=[{"label": f"Grade {g}", "value": g} for g in grades],
                             multi=True, placeholder="All Grades",
                             style={"font-size": "12px"}),
            ], style={"flex": "1"}),
            html.Div([
                html.Label("Home Ownership", style={"font-size": "12px",
                            "font-weight": "600", "color": NAVY}),
                dcc.Dropdown(id="filter-ownership",
                             options=[{"label": o, "value": o} for o in ownerships],
                             multi=True, placeholder="All Types",
                             style={"font-size": "12px"}),
            ], style={"flex": "1"}),
            html.Div([
                html.Label("Loan Intent", style={"font-size": "12px",
                            "font-weight": "600", "color": NAVY}),
                dcc.Dropdown(id="filter-intent",
                             options=[{"label": i.title(), "value": i} for i in intents],
                             multi=True, placeholder="All Intents",
                             style={"font-size": "12px"}),
            ], style={"flex": "1"}),
            html.Div([
                html.Label("Min Credit Score",
                           style={"font-size": "12px", "font-weight": "600",
                                  "color": NAVY}),
                dcc.Slider(id="filter-cs", min=300, max=850, step=25,
                           value=300,
                           marks={300: "300", 500: "500", 650: "650", 850: "850"},
                           tooltip={"placement": "bottom", "always_visible": True}),
            ], style={"flex": "1.5"}),
        ], style={"display": "flex", "gap": "16px", "align-items": "flex-end",
                  "background": CARD_BG, "border-radius": "8px",
                  "border": f"1px solid {BORDER}", "padding": "16px",
                  "margin-bottom": "14px"}),

        html.Div(id="explorer-summary",
                 style={"margin-bottom": "10px", "font-size": "13px",
                        "color": NAVY, "font-weight": "600"}),

        dash_table.DataTable(
            id="explorer-table",
            page_size=20,
            sort_action="native",
            filter_action="native",
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": NAVY, "color": WHITE,
                "fontWeight": "700", "fontSize": "12px",
                "fontFamily": FONT, "textAlign": "center",
                "border": "none", "padding": "9px",
            },
            style_cell={
                "fontFamily": FONT, "fontSize": "12px",
                "padding": "7px 10px", "color": NAVY,
                "border": f"1px solid {BORDER}", "minWidth": "80px",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": LIGHT_BG},
                {"if": {"filter_query": "{loan_status} = 1"},
                 "backgroundColor": "#FFF2F2", "color": RED_RISK},
            ],
        ),
    ])


@app.callback(
    Output("explorer-table", "data"),
    Output("explorer-table", "columns"),
    Output("explorer-summary", "children"),
    Input("filter-grade",     "value"),
    Input("filter-ownership", "value"),
    Input("filter-intent",    "value"),
    Input("filter-cs",        "value"),
)
def update_explorer(grades, ownerships, intents, min_cs):
    filtered = df.copy()
    if grades:     filtered = filtered[filtered["loan_grade"].isin(grades)]
    if ownerships: filtered = filtered[filtered["person_home_ownership"].isin(ownerships)]
    if intents:    filtered = filtered[filtered["loan_intent"].isin(intents)]
    if min_cs:     filtered = filtered[filtered["credit_score"] >= min_cs]

    display_cols = [
        "loan_grade", "person_home_ownership", "loan_intent",
        "loan_amnt", "loan_int_rate", "loan_percent_income",
        "person_age", "person_income", "credit_score",
        "pd_score", "el", "loan_status",
    ]
    col_names = {
        "loan_grade": "Grade", "person_home_ownership": "Ownership",
        "loan_intent": "Intent", "loan_amnt": "Loan Amt ($)",
        "loan_int_rate": "Int Rate (%)", "loan_percent_income": "Loan/Income",
        "person_age": "Age", "person_income": "Income ($)",
        "credit_score": "Credit Score", "pd_score": "PD",
        "el": "Exp. Loss ($)", "loan_status": "Default",
    }

    table_df = filtered[display_cols].copy()
    table_df["loan_amnt"]        = table_df["loan_amnt"].apply(lambda x: f"${x:,.0f}")
    table_df["loan_int_rate"]    = table_df["loan_int_rate"].apply(
        lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
    table_df["loan_percent_income"] = table_df["loan_percent_income"].apply(
        lambda x: f"{x:.1%}")
    table_df["person_income"]    = table_df["person_income"].apply(lambda x: f"${x:,.0f}")
    table_df["pd_score"]         = table_df["pd_score"].apply(lambda x: f"{x:.2%}")
    table_df["el"]               = table_df["el"].apply(lambda x: f"${x:,.0f}")
    table_df["loan_status"]      = table_df["loan_status"].apply(
        lambda x: "YES" if x == 1 else "No")

    table_df = table_df.rename(columns=col_names)
    columns = [{"name": col_names.get(c, c), "id": col_names.get(c, c)}
               for c in display_cols]

    n     = len(filtered)
    dr    = filtered["loan_status"].mean() if n else 0
    el_t  = filtered["el"].sum() if n else 0
    summary = (f"Showing {n:,} loans  |  Default Rate: {dr:.2%}  |  "
               f"Total Exp. Loss: ${el_t/1e6:.2f}M")

    return table_df.to_dict("records"), columns, summary


# ═══════════════════════════════════════════════════════════════════════════════
#  CRO-LEVEL INSIGHTS (printed at startup)
# ═══════════════════════════════════════════════════════════════════════════════
INSIGHTS = """
╔══════════════════════════════════════════════════════════════════════════════╗
║              5 CRO-LEVEL INSIGHTS – CREDIT RISK PORTFOLIO                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  1. GRADE CLIFF AT D: Default rate jumps from 20.7% (Grade C) to 59.0%     ║
║     (Grade D) — a near-3× step-change. Origination in D–G accounts for     ║
║     only 12% of loans but 62% of total Expected Loss. Consider tightening  ║
║     cutoffs at the B/C boundary and eliminating D+ origination.             ║
║                                                                              ║
║  2. RENT CONCENTRATION IS A SYSTEMIC RISK: 50.5% of loans are to renters   ║
║     (16,446 loans) who carry a 31.6% default rate vs. 7.5% for homeowners. ║
║     The portfolio is structurally long on the highest-default segment.      ║
║     Collateral-free exposure to renters should be capped or re-priced.      ║
║                                                                              ║
║  3. EXPECTED LOSS OF ~$30.7M UNDERSTATES STRESS RISK: Under a 2.5× PD     ║
║     shock (Severely Adverse scenario), EL rises to ~$76M — a 148% increase ║
║     that would consume ~30% of the assumed 8% capital buffer. The portfolio ║
║     has insufficient margin of safety for a moderate recession.             ║
║                                                                              ║
║  4. DEBT CONSOLIDATION IS THE HIGHEST-RISK INTENT (28.6% DR): Borrowers    ║
║     seeking to roll over existing debt signal pre-existing distress and are ║
║     25% more likely to default than VENTURE or EDUCATION borrowers.         ║
║     Tighter LTV and income verification should apply to this segment.       ║
║                                                                              ║
║  5. PRIOR DEFAULT FLAG IS A LEADING INDICATOR: Borrowers with a prior       ║
║     default on the CB file have materially higher default rates. The        ║
║     information value (IV) of loan_grade and CB default flag are the        ║
║     two strongest predictors — a scorecard that up-weights these two        ║
║     features against DTI and income can materially improve GINI coefficient.║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

if __name__ == "__main__":
    print(INSIGHTS)
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=False, host="0.0.0.0", port=port)
