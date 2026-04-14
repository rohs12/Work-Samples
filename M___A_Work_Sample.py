# =============================================================================
# ALPHABET × WIZ  —  M&A SENIOR ANALYST DASHBOARD  (DYNAMIC)
# =============================================================================
# FILE:         M_&_A_Work_Sample.py
# DEPENDENCIES: pip install dash plotly pandas numpy
# RUN:          python "M_&_A_Work_Sample.py"   →  http://127.0.0.1:8050
#
# DATA SOURCES
# ─────────────────────────────────────────────────────────────────────────────
#  Alphabet P&L / Balance / Cash Flow  Alphabet 10-K FY2020-FY2024  SEC EDGAR
#  Alphabet Segments                   Alphabet 8-K Q4 press releases FY2020-FY2024
#  Wiz Funding Rounds                  Wikipedia / TechCrunch / Crunchbase / Pitchbook
#  Wiz ARR Milestones                  Wikipedia / Contrary Research / TechCrunch
#  Deal Terms & Regulatory             Alphabet/SEC filings / Wikipedia
#  Trading Comps                       Public filings / Bloomberg (approx. FY2024)
#  M&A Transaction Comps               SEC filings / press releases / Qatalyst
#
# KEY ASSUMPTIONS
# ─────────────────────────────────────────────────────────────────────────────
#  Wiz ARR at close (Mar 2026)         $500M base  |  $650M bull  |  $380M bear
#  Price / ARR multiple (base)         $32,000M / $500M = 64.0x
#  Acquisition premium                 $32,000M / $12,000M (Series E) = 2.67x
#  Cash coverage                       $32,000M / $110,174M (YE2024) = 29.1%
#  Alphabet diluted shares             12,450M  (NI $100,118M / EPS $8.04)
#  Lost interest on $32B               5.0% yield → $1,600M pre-tax / $1,338M after-tax
#  Wiz gross margin                    70%  (cloud-native CNAPP, infra-efficient)
#  Wiz Year-1 EBIT margin              -20% (pre-profitability; heavy S&M + R&D)
#  Wiz fair-value intangibles          $9,000M (tech $5B + customers $3B + brand $1B)
#  Goodwill                            $32,000M - $9,000M - $1,000M = $22,000M
#  Google Cloud enterprise customers   ~10,000 est.  avg Wiz ACV $500K
#  DCF: WACC default                   10%   (adjustable 8-16%)
#  DCF: terminal EV/Revenue multiple   12x   (adjustable 6-25x)
#  DCF: explicit forecast period       5 years (2026-2030)
#  DCF: growth rates (base)            55% → 40% → 33% → 27% → 20%
#  DCF: EBIT margin ramp (base)        -20% → -8% → +6% → +17% → +26%
# =============================================================================

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ── COLOURS ──────────────────────────────────────────────────────────────────
C_ALPHA  = "#4285F4"
C_WIZ    = "#00C853"
C_YELLOW = "#FBBC04"
C_RED    = "#EA4335"
C_PURPLE = "#AB47BC"
C_BULL   = "#00e676"
BG       = "#0d1117"
CARD     = "#161b22"
CARD2    = "#1c2128"
BORDER   = "#30363d"
TXT      = "#e6edf3"
MUTED    = "#8b949e"

# ── BASE LAYOUT  (no margin key — each chart sets its own) ───────────────────
PL = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter,-apple-system,sans-serif", color=TXT, size=11),
)
M = dict(l=52, r=18, t=38, b=46)      # default margin shortcut

def _ax(**kw):
    return dict(gridcolor=BORDER, linecolor=BORDER, zeroline=False, **kw)

def _leg(**kw):
    return dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, **kw)

# =============================================================================
# HARDCODED DATA
# =============================================================================

YEARS = [2020, 2021, 2022, 2023, 2024]

APL = {
    "total_rev":     [182527, 257637, 282836, 307394, 350018],
    "net_income":    [40269,  76033,  59972,  73795,  100118],
    "op_income":     [41224,  78714,  74842,  84293,  112390],
    "gross_margin":  [55.6,   56.9,   55.3,   56.6,   58.1],
    "op_margin":     [22.6,   30.6,   26.5,   27.4,   32.1],
    "net_margin":    [22.1,   29.5,   21.2,   24.0,   28.6],
    "ebitda_margin": [29.0,   35.5,   32.5,   32.2,   37.0],
    "fcf":           [42843,  67012,  60010,  69495,  72764],
    "fcf_margin":    [23.5,   26.0,   21.2,   22.6,   20.8],
    "cloud_rev":     [13059,  19206,  26280,  33088,  43228],
    "cloud_op_mgn":  [-42.9, -16.1,  -2.7,    5.2,   21.8],
    "rd_exp":        [27573,  31562,  39500,  45427,  49316],
    "sm_exp":        [17946,  22912,  26567,  27917,  27573],
    "cogs":          [84732, 110939, 126203, 133332, 146306],
}

ABS = {
    "cash_sec":    [131174, 139649, 113762, 110916, 110174],
    "total_assets":[319616, 359268, 365264, 402392, 450256],
    "lt_debt":     [13932,  14817,  14701,  13253,  10818],
    "total_liab":  [97071,  107633, 109120, 119013, 125172],
    "total_equity":[222545, 251635, 256144, 283379, 325084],
    "goodwill":    [21175,  22956,  28960,  29198,  32838],
    "market_cap":  [1185000,1921000,1140000,1756000,2030000],
}

ACF = {
    "op_cf":  [65124, 91652, 91495, 101746, 125333],
    "capex":  [22461, 24273, 31485,  32251,  52535],
    "buybacks":[31149,50274, 59296,  61504,  61778],
}

RATIOS = {
    "pe":          [29.4, 25.3, 19.0, 23.8, 20.3],
    "ev_rev":      [5.9,  7.0,  3.7,  5.4,  5.5],
    "ev_ebitda":   [20.4, 24.7, 11.5, 16.8, 14.9],
    "roe":         [18.1, 30.2, 23.4, 26.0, 30.8],
    "roa":         [12.6, 21.2, 16.4, 18.3, 22.2],
}

DEAL = {
    "ev": 32000, "wiz_arr_base": 500, "wiz_arr_bull": 650, "wiz_arr_bear": 380,
    "last_val": 12000, "alphabet_cash": 110174, "breakup_fee": 3200,
    "announced": "Mar 18, 2025", "closed": "Mar 11, 2026",
    "shares_diluted": 12450, "eps_2024": 8.04,
}

WIZ_FUNDING = {
    "rounds": ["Ser A","Ser B1","Ser B2","Ser C","Secondary","Ser D","Ser E","Acquisition"],
    "dates":  ["Dec-20","Apr-21","May-21","Oct-21","2022","Feb-23","May-24","Mar-25"],
    "raised": [100, 130, 120, 250, 100, 300, 1000, 32000],
    "val":    [None, 1700, 1700, 6000, None, 10000, 12000, 32000],
    "ev_arr": [None, None, None, None, None, 28.5, 24.0, 64.0],
}

WIZ_ARR = {
    "labels":   ["Feb-21","Jul-22","May-23","Feb-24","May-24","Close"],
    "arr":      [1,       100,     200,     350,     500,     500],
    "ftune100": [None,    25,      35,      40,      45,      45],
}

COMPS_TRADING = {
    "co":     ["Palo Alto","CrowdStrike","Zscaler","Fortinet","SentinelOne","Cloudflare","Okta"],
    "rev":    [8027,  3806,  2168,  5305,  1065,  1625,  2597],
    "growth": [16,    29,    34,    10,    33,    28,    19],
    "ev_rev": [16.4,  23.6,  12.9,  10.4,  8.5,   24.6,  5.4],
    "op_mgn": [19.5,  0.3,   4.5,  27.8,  -6.2,  -1.6,  1.4],
}

COMPS_MA = {
    "deal":  ["Alphabet×Wiz","PANW×CyberArk","Cisco×Splunk","Alphabet×Mandiant","Broadcom×Symantec"],
    "year":  [2025, 2025, 2024, 2022, 2019],
    "ev":    [32000, 25000, 28000, 5400, 9000],
    "ev_rev":[64.0,  17.8,  7.4,  8.2,  5.2],
    "note":  ["$500M ARR; CNAPP leader; record deal",
              "Identity sec; $1.4B rev",
              "SIEM; $3.7B rev",
              "Threat intel; $660M rev",
              "Ent. security portfolio"],
}

RISK = {
    "cat":   ["Regulatory / Antitrust","Integration Execution","Key Person Retention",
              "Competitive Response","Valuation / Multiple Risk",
              "Cloud Market Saturation","Geo / Data Sovereignty"],
    "sev":   [4, 4, 3, 4, 5, 3, 3],
    "like":  [2, 4, 4, 3, 3, 3, 2],
    "score": [8, 16, 12, 12, 15, 9, 6],
    "notes": [
        "DOJ + EC cleared no conditions. Trump-era M&A-friendly env. lowers tail risk.",
        "Standalone unit structure preserves velocity. Alphabet/Mandiant integration was slow.",
        "Co-founder retention pkg expected. Historically 2-3yr post-acq tenure.",
        "MSFT Defender / PANW CNAPP / AWS Security Hub accelerating. Moat must widen fast.",
        "64x ARR is a record. ARR miss of 20% wipes ~$6B NPV. Path to profitability critical.",
        "Hyperscaler security spend growth decelerating post-2024. CISO budget scrutiny.",
        "EU data-residency laws. Non-US cloud sovereignty legislation evolving.",
    ],
}

PROJ = {
    "years": [2024, 2025, 2026, 2027, 2028, 2029, 2030],
    "bull":  [500,  825,  1320, 1980, 2770, 3740, 4800],
    "base":  [500,  750,  1050, 1400, 1800, 2200, 2650],
    "bear":  [500,  640,   820, 1000, 1180, 1380, 1580],
}

# =============================================================================
# TABLE BUILDER
# =============================================================================

def make_table(headers, rows, highlight_rows=None, note=None):
    TH = {"padding":"7px 12px","fontSize":"10px","fontWeight":"700",
          "letterSpacing":"0.06em","color":MUTED,"background":CARD2,
          "borderBottom":f"2px solid {BORDER}","whiteSpace":"nowrap"}
    TD_BASE = {"padding":"6px 12px","fontSize":"11px",
               "borderBottom":f"1px solid {BORDER}","color":TXT,
               "fontVariantNumeric":"tabular-nums"}

    thead = html.Thead(html.Tr([
        html.Th(h, style={**TH,"textAlign":"left" if i==0 else "right"})
        for i,h in enumerate(headers)
    ]))

    tbody_rows = []
    for ri, row in enumerate(rows):
        is_sep = isinstance(row[0], str) and row[0].startswith("──")
        if is_sep:
            tbody_rows.append(html.Tr([html.Td(
                row[0].replace("──","").strip(),
                colSpan=len(headers),
                style={**TD_BASE,"background":CARD2,"color":MUTED,
                       "fontSize":"9px","fontWeight":"700",
                       "letterSpacing":"0.1em","textTransform":"uppercase"}
            )]))
            continue
        bold = highlight_rows and ri in highlight_rows
        cells = []
        for ci, v in enumerate(row):
            st = {**TD_BASE, "textAlign": "left" if ci == 0 else "right"}
            if bold:
                st = {**st, "fontWeight":"700", "color": C_ALPHA}
            val = "—" if v is None else (str(v) if not isinstance(v, str) else v)
            cells.append(html.Td(val, style=st))
        tbody_rows.append(html.Tr(cells))

    tbl = html.Table([thead, html.Tbody(tbody_rows)],
                     style={"width":"100%","borderCollapse":"collapse"})
    if note:
        return html.Div([tbl, html.Div(note, style={
            "fontSize":"9px","color":MUTED,"marginTop":"8px","fontStyle":"italic"
        })])
    return tbl


def section_header(title, sub=""):
    return html.Div([
        html.Span(title, style={"fontWeight":"700","color":TXT,"fontSize":"13px"}),
        html.Span(f"  —  {sub}" if sub else "",
                  style={"color":MUTED,"fontSize":"11px"}),
    ], style={"borderBottom":f"2px solid {BORDER}","paddingBottom":"10px",
              "marginBottom":"16px","marginTop":"8px"})


def kpi(label, val, sub=None, color=TXT):
    return html.Div([
        html.Div(val, style={"fontSize":"26px","fontWeight":"800",
                             "color":color,"lineHeight":"1"}),
        html.Div(label, style={"fontSize":"10px","color":MUTED,"marginTop":"5px",
                               "fontWeight":"600","textTransform":"uppercase",
                               "letterSpacing":"0.07em"}),
        html.Div(sub, style={"fontSize":"10px","color":MUTED,"marginTop":"2px"}) if sub else None,
    ], style={"padding":"16px 20px","background":CARD2,
              "border":f"1px solid {BORDER}","borderRadius":"6px"})


def card(children, col=1, pad="18px 20px"):
    return html.Div(children, style={
        "background":CARD,"border":f"1px solid {BORDER}",
        "borderRadius":"8px","padding":pad,"gridColumn":f"span {col}",
    })


def grid(*children, cols="repeat(4,1fr)", gap="12px"):
    return html.Div(list(children), style={
        "display":"grid","gridTemplateColumns":cols,
        "gap":gap,"alignItems":"start",
    })

SL = {"fontSize":"11px","color":MUTED,"marginBottom":"4px"}

# =============================================================================
# STATIC FIGURES
# =============================================================================

def fig_alphabet_bars(metric_a="total_rev", metric_b="net_income"):
    LABELS = {"total_rev":"Total Revenue","net_income":"Net Income",
              "op_income":"Operating Income","fcf":"Free Cash Flow",
              "cloud_rev":"Google Cloud Rev"}
    fig = go.Figure()
    for key, color in [(metric_a, C_ALPHA),(metric_b, C_WIZ)]:
        fig.add_trace(go.Bar(x=YEARS, y=APL[key], name=LABELS.get(key,key),
            marker_color=color,
            text=[f"${v/1000:.0f}B" for v in APL[key]],
            textposition="outside", textfont_size=9))
    fig.update_layout(**PL, margin=M, barmode="group", height=300,
        yaxis=_ax(tickprefix="$",tickformat=",.0f"), xaxis=_ax(),
        legend=_leg(orientation="h",y=1.12,x=0))
    return fig


def fig_margins():
    fig = go.Figure()
    for label, key, color, lstyle in [
        ("Gross Margin",     "gross_margin",  "#90CAF9", "solid"),
        ("Operating Margin", "op_margin",     C_ALPHA,   "dot"),
        ("Net Margin",       "net_margin",    C_WIZ,     "dash"),
        ("EBITDA Margin",    "ebitda_margin", C_YELLOW,  "dashdot"),
        ("FCF Margin",       "fcf_margin",    C_PURPLE,  "longdash"),
    ]:
        fig.add_trace(go.Scatter(x=YEARS, y=APL[key], name=label,
            mode="lines+markers",
            line=dict(color=color,dash=lstyle,width=2),
            marker=dict(size=5)))
    fig.update_layout(**PL, margin=M, height=290,
        yaxis=_ax(ticksuffix="%"), xaxis=_ax(),
        legend=_leg(orientation="h",y=1.15,x=0,font_size=9))
    return fig


def fig_valuation_ratios():
    fig = make_subplots(rows=1, cols=3,
        subplot_titles=["P/E Trailing (x)","EV/Revenue (x)","EV/EBITDA (x)"])
    for col,(label,key,color) in enumerate([
        ("P/E","pe",C_ALPHA),("EV/Rev","ev_rev",C_WIZ),("EV/EBITDA","ev_ebitda",C_YELLOW)
    ],1):
        fig.add_trace(go.Scatter(x=YEARS,y=RATIOS[key],name=label,
            mode="lines+markers",
            line=dict(color=color,width=2.5),
            marker=dict(size=6),showlegend=False),row=1,col=col)
    fig.update_layout(**PL, margin=M, height=250)
    for i in range(1,4):
        fig.update_xaxes(gridcolor=BORDER,linecolor=BORDER,row=1,col=i)
        fig.update_yaxes(gridcolor=BORDER,linecolor=BORDER,row=1,col=i)
    return fig


def fig_cash_bridge():
    fig = go.Figure()
    fig.add_trace(go.Bar(x=YEARS,y=ABS["cash_sec"],name="Cash + Mkt Sec",
        marker_color=C_WIZ,opacity=0.85))
    fig.add_trace(go.Bar(x=YEARS,y=ABS["lt_debt"],name="Long-Term Debt",
        marker_color=C_RED,opacity=0.85))
    fig.add_shape(type="line",x0=2019.4,x1=2024.6,y0=32000,y1=32000,
        line=dict(color=C_YELLOW,width=1.5,dash="dash"))
    fig.add_annotation(x=2023.5,y=36000,text="Deal Cost: $32B",
        showarrow=False,font=dict(size=9,color=C_YELLOW))
    fig.update_layout(**PL, margin=M, barmode="group", height=270,
        yaxis=_ax(tickprefix="$",tickformat=",.0f"), xaxis=_ax(),
        legend=_leg(orientation="h",y=1.12,x=0))
    return fig


def fig_cloud_growth():
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Bar(x=YEARS,y=APL["cloud_rev"],name="Cloud Revenue ($M)",
        marker_color=C_ALPHA,opacity=0.8),secondary_y=False)
    fig.add_trace(go.Scatter(x=YEARS,y=APL["cloud_op_mgn"],name="Cloud Op Margin %",
        mode="lines+markers",
        line=dict(color=C_YELLOW,width=2),marker=dict(size=6)),secondary_y=True)
    fig.update_layout(**PL, margin=M, height=270,
        legend=_leg(orientation="h",y=1.12,x=0))
    fig.update_yaxes(gridcolor=BORDER,linecolor=BORDER,secondary_y=False)
    fig.update_yaxes(ticksuffix="%",gridcolor=BORDER,linecolor=BORDER,secondary_y=True)
    fig.update_xaxes(gridcolor=BORDER,linecolor=BORDER)
    return fig


def fig_wiz_arr():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=WIZ_ARR["labels"],y=WIZ_ARR["arr"],
        mode="lines+markers+text",
        text=[f"${v}M" for v in WIZ_ARR["arr"]],
        textposition="top center",textfont=dict(size=9),
        line=dict(color=C_WIZ,width=3),
        marker=dict(size=10,color=C_WIZ,line=dict(width=2,color=BG)),
        fill="tozeroy",fillcolor="rgba(0,200,83,0.07)",name="ARR"))
    fig.add_annotation(x="Jul-22",y=100,
        text="Fastest SaaS ever<br>to $100M ARR (18 mo)",
        showarrow=True,arrowhead=2,arrowcolor=MUTED,ax=80,ay=-55,
        font=dict(size=9,color=MUTED),bgcolor=CARD2,bordercolor=BORDER,borderwidth=1)
    fig.update_layout(**PL, margin=M, height=300,
        yaxis=_ax(tickprefix="$",ticksuffix="M"),xaxis=_ax())
    return fig


def fig_wiz_funding():
    rounds = [r for r,v in zip(WIZ_FUNDING["rounds"],WIZ_FUNDING["val"]) if v]
    vals   = [v for v in WIZ_FUNDING["val"] if v]
    colors = [C_RED if r=="Acquisition" else C_ALPHA for r in rounds]
    fig = go.Figure(go.Bar(x=rounds,y=vals,marker_color=colors,opacity=0.9,
        text=[f"${v/1000:.1f}B" for v in vals],
        textposition="outside",textfont_size=10))
    fig.add_shape(type="line",x0=-0.5,x1=len(rounds)-0.5,y0=12000,y1=12000,
        line=dict(color=C_WIZ,width=1.5,dash="dash"))
    fig.add_annotation(x=len(rounds)-1.5,y=13800,text="Last Private: $12B",
        showarrow=False,font=dict(size=9,color=C_WIZ))
    fig.update_layout(**PL, margin=M, height=290,
        yaxis=_ax(tickprefix="$",tickformat=",.0f",range=[0,38000]),
        xaxis=_ax())
    return fig


def fig_wiz_peers():
    fig = go.Figure()
    for i,co in enumerate(COMPS_TRADING["co"]):
        fig.add_trace(go.Scatter(
            x=[COMPS_TRADING["growth"][i]],y=[COMPS_TRADING["ev_rev"][i]],
            mode="markers+text",text=[co],
            textposition="top center",textfont=dict(size=8,color=MUTED),
            marker=dict(size=max(10,int(np.sqrt(COMPS_TRADING["rev"][i])/2.5)),
                        color=C_ALPHA,opacity=0.8,line=dict(width=1,color="white")),
            showlegend=False))
    fig.add_trace(go.Scatter(
        x=[80],y=[64],mode="markers+text",text=["Wiz (Deal)"],
        textposition="top center",textfont=dict(size=9,color=C_RED),
        marker=dict(size=22,color=C_RED,symbol="star",opacity=0.95,
                    line=dict(width=1.5,color="white")),showlegend=False))
    fig.update_layout(**PL, margin=M, height=310,
        xaxis=_ax(title="Revenue Growth YoY (%)",ticksuffix="%"),
        yaxis=_ax(title="EV / Revenue (x)",ticksuffix="x"))
    return fig


def fig_ma_comps():
    fig = go.Figure()
    for i,deal in enumerate(COMPS_MA["deal"]):
        is_wiz = (i == 0)
        fig.add_trace(go.Scatter(
            x=[COMPS_MA["ev"][i]],y=[COMPS_MA["ev_rev"][i]],
            mode="markers+text",text=[deal],
            textposition="top left" if is_wiz else "top right",
            textfont=dict(size=9,color=C_RED if is_wiz else MUTED),
            marker=dict(size=22 if is_wiz else 13,
                        color=C_RED if is_wiz else C_ALPHA,
                        symbol="star" if is_wiz else "circle",
                        opacity=0.9,line=dict(width=1.5,color="white")),
            name=deal,showlegend=False,
            customdata=[COMPS_MA["note"][i]],
            hovertemplate=(f"<b>{deal}</b> ({COMPS_MA['year'][i]})<br>"
                           f"EV: ${COMPS_MA['ev'][i]/1000:.1f}B<br>"
                           f"EV/Rev: {COMPS_MA['ev_rev'][i]}x<br>"
                           "%{customdata[0]}<extra></extra>")))
    fig.update_layout(**PL, margin=M, height=340,
        xaxis=_ax(title="Enterprise Value ($M)",tickprefix="$",tickformat=",.0f"),
        yaxis=_ax(title="EV / Revenue (x)",ticksuffix="x"))
    return fig


def fig_risk_matrix():
    fig = go.Figure()
    for (x0,x1,y0,y1,col) in [
        (0.5,3,0.5,3,"rgba(0,200,83,0.05)"),
        (3,5.5,0.5,3,"rgba(251,188,4,0.07)"),
        (0.5,3,3,5.5,"rgba(251,188,4,0.07)"),
        (3,5.5,3,5.5,"rgba(234,67,53,0.10)"),
    ]:
        fig.add_shape(type="rect",x0=x0,x1=x1,y0=y0,y1=y1,
            fillcolor=col,line_width=0,layer="below")
    for i,cat in enumerate(RISK["cat"]):
        sc = RISK["score"][i]
        fig.add_trace(go.Scatter(
            x=[RISK["sev"][i]],y=[RISK["like"][i]],
            mode="markers+text",text=[cat],
            textposition="middle right",textfont=dict(size=8.5,color=TXT),
            marker=dict(size=sc*2.8,opacity=0.85,
                color=sc,colorscale=[[0,"#3a1a1a"],[0.5,"#b83a3a"],[1,"#f44336"]],
                cmin=0,cmax=20,showscale=False,
                line=dict(width=1,color="white")),
            name=cat,showlegend=False,
            customdata=[RISK["notes"][i]],
            hovertemplate=(f"<b>{cat}</b><br>"
                           f"Severity {RISK['sev'][i]}/5  Likelihood {RISK['like'][i]}/5  Score {sc}/25<br>"
                           "<i>%{customdata[0]}</i><extra></extra>")))
    fig.update_layout(**PL, margin=M, height=370,
        xaxis=_ax(title="Severity (1=Low → 5=High)",range=[0.2,7.8],tickvals=[1,2,3,4,5]),
        yaxis=_ax(title="Likelihood (1=Low → 5=High)",range=[0.2,5.8],tickvals=[1,2,3,4,5]))
    return fig


# ── DCF ENGINE ────────────────────────────────────────────────────────────────

def run_dcf(wacc_pct=10.0, terminal_mult=12.0, starting_arr=500):
    """
    5-year unlevered FCF DCF.
    FCF = NOPAT + D&A - CapEx - ΔNWC
    NOPAT = EBIT × (1 - tax_rate)
    TV = Revenue_2030 × terminal_multiple
    NPV = Σ PV(FCF) + PV(TV)
    """
    w            = wacc_pct / 100
    growth_rates = [0.55, 0.40, 0.33, 0.27, 0.20]   # ARR YoY growth 2026-2030
    ebit_margins = [-0.20,-0.08, 0.06, 0.17, 0.26]   # EBIT margin 2026-2030
    da_pct       = 0.05   # D&A as % of revenue
    capex_pct    = 0.08   # CapEx as % of revenue
    tax          = 0.164  # Alphabet effective tax rate
    nwc_pct      = 0.02   # Δ NWC as % of revenue

    revs=[]; ebits=[]; nopats=[]; das=[]; capexs=[]; nwcs=[]; fcfs=[]; pvs=[]
    arr = starting_arr
    for i,(g,em) in enumerate(zip(growth_rates,ebit_margins)):
        arr   *= (1+g)
        rev    = arr
        ebit   = rev * em
        nopat  = ebit * (1-tax)
        da     = rev * da_pct
        capex  = rev * capex_pct
        nwc    = rev * nwc_pct
        fcf    = nopat + da - capex - nwc
        pv     = fcf / (1+w)**(i+1)
        revs.append(rev);  ebits.append(ebit);  nopats.append(nopat)
        das.append(da);    capexs.append(capex); nwcs.append(nwc)
        fcfs.append(fcf);  pvs.append(pv)

    tv    = revs[-1] * terminal_mult
    pv_tv = tv / (1+w)**5
    npv   = sum(pvs) + pv_tv
    return {
        "years":PROJ["years"][2:], "revs":revs, "ebits":ebits, "nopats":nopats,
        "das":das, "capexs":capexs, "nwcs":nwcs, "fcfs":fcfs, "pvs":pvs,
        "tv":tv, "pv_tv":pv_tv, "npv":npv,
        "ebit_margins":ebit_margins, "growth":growth_rates,
    }


def _solve_wacc(term_mult, arr, target=32000, lo=0.01, hi=0.35, itr=50):
    for _ in range(itr):
        mid = (lo+hi)/2
        npv = run_dcf(mid*100, term_mult, arr)["npv"]
        if npv > target: lo = mid
        else: hi = mid
    return mid*100


def _solve_mult(wacc_pct, arr, target=32000, lo=1.0, hi=120.0, itr=50):
    for _ in range(itr):
        mid = (lo+hi)/2
        npv = run_dcf(wacc_pct, mid, arr)["npv"]
        if npv < target: lo = mid
        else: hi = mid
    return mid


def fig_dcf_waterfall(dcf):
    labels  = [f"PV FCF {y}" for y in range(2026,2031)] + ["PV Terminal Value","Enterprise Value"]
    values  = list(dcf["pvs"]) + [dcf["pv_tv"], dcf["npv"]]
    measures = ["relative"]*5 + ["relative","total"]
    fig = go.Figure(go.Waterfall(
        orientation="v", measure=measures, x=labels, y=values,
        connector=dict(line=dict(color=BORDER,width=1)),
        increasing=dict(marker_color=C_ALPHA),
        decreasing=dict(marker_color=C_RED),
        totals=dict(marker_color=C_WIZ),
        text=[f"${v:,.0f}M" for v in values],
        textposition="outside",textfont_size=9))
    fig.add_shape(type="line",x0=-0.5,x1=len(labels)-0.5,y0=32000,y1=32000,
        line=dict(color=C_RED,width=1.5,dash="dash"))
    fig.add_annotation(x=3,y=35000,text="Deal Price: $32,000M",
        showarrow=False,font=dict(size=9,color=C_RED))
    fig.update_layout(**PL, margin=M, height=380,
        yaxis=_ax(tickprefix="$",tickformat=",.0f"),xaxis=_ax())
    return fig


def build_dcf_output(dcf, wacc_pct, terminal_mult, starting_arr):
    """
    Returns two properly structured tables:
      1. Assumptions + Valuation Bridge  (2 columns)
      2. Full DCF model grid             (6 columns: label + 5 years)
    """
    f  = lambda v: f"${v:,.0f}M"
    fp = lambda v: f"{v*100:.1f}%"

    req_wacc = _solve_wacc(terminal_mult, starting_arr)
    req_mult = _solve_mult(wacc_pct, starting_arr)

    # ── Table A: Assumptions + Bridge ─────────────────────────────────────────
    bridge = [
        ["──ASSUMPTIONS (inputs)"],
        ["Starting Wiz ARR (2026E)",            f"${starting_arr}M"],
        ["WACC",                                 f"{wacc_pct:.1f}%"],
        ["Terminal EV / Revenue Multiple",       f"{terminal_mult:.0f}x"],
        ["Explicit Forecast Period",             "5 years  (2026 – 2030)"],
        ["Tax Rate",                             "16.4%  (Alphabet effective)"],
        ["D&A as % of Revenue",                  "5.0%"],
        ["CapEx as % of Revenue",                "8.0%"],
        ["Δ NWC as % of Revenue",               "2.0%"],
        ["──VALUATION BRIDGE (outputs)"],
        ["Sum of PV (FCFs yr 1–5)",              f(sum(dcf["pvs"]))],
        ["Terminal Revenue (2030E)",             f(dcf["revs"][-1])],
        ["Terminal Value  (Rev × {:.0f}x)".format(terminal_mult), f(dcf["tv"])],
        ["PV of Terminal Value",                 f(dcf["pv_tv"])],
        ["Enterprise Value (NPV)",               f(dcf["npv"])],
        ["Deal Price",                           "$32,000M"],
        ["Over / (Under) Valued vs $32B",        f(dcf["npv"]-32000)],
        ["──SENSITIVITY SOLVERS"],
        ["WACC needed to justify $32B",          f"{req_wacc:.1f}%"],
        ["Terminal Multiple needed to justify $32B", f"{req_mult:.1f}x"],
        ["──FORMULAS"],
        ["FCF",         "= NOPAT + D&A − CapEx − ΔNWC"],
        ["NOPAT",       "= EBIT × (1 − 16.4%)"],
        ["Terminal Val","= Revenue₂₀₃₀ × Terminal Multiple"],
        ["NPV",         "= Σ [ FCFₜ / (1+WACC)ᵗ ]  +  TV / (1+WACC)⁵"],
    ]
    tbl_a = make_table(
        ["Parameter","Value / Formula"], bridge,
        highlight_rows={14,15,16,18,19},
        note=("Red = value destroyed vs $32B price  |  "
              "Green = value created  |  "
              "Solvers use binary search (50 iterations)")
    )

    # ── Table B: DCF model grid ────────────────────────────────────────────────
    yrs = list(range(2026,2031))
    model_rows = [
        ["ARR / Revenue ($M)"]    + [f(v) for v in dcf["revs"]],
        ["YoY Growth"]             + [fp(g) for g in dcf["growth"]],
        ["EBIT ($M)"]              + [f(v) for v in dcf["ebits"]],
        ["EBIT Margin"]            + [fp(m) for m in dcf["ebit_margins"]],
        ["NOPAT  (after tax)"]     + [f(v) for v in dcf["nopats"]],
        ["(+) D&A"]                + [f(v) for v in dcf["das"]],
        ["(−) CapEx"]              + [f(-v) for v in dcf["capexs"]],
        ["(−) Δ NWC"]             + [f(-v) for v in dcf["nwcs"]],
        ["Unlevered FCF"]          + [f(v) for v in dcf["fcfs"]],
        ["PV of FCF"]              + [f(v) for v in dcf["pvs"]],
    ]
    tbl_b = make_table(
        ["Metric","2026E","2027E","2028E","2029E","2030E"],
        model_rows,
        highlight_rows={8,9},
        note="FCF = NOPAT + D&A − CapEx − ΔNWC  |  Parentheses = outflow (subtracted)"
    )

    return html.Div([
        html.Div([
            html.Div("ASSUMPTIONS & VALUATION BRIDGE",
                style={"fontSize":"10px","color":MUTED,"fontWeight":"700",
                       "letterSpacing":"0.08em","marginBottom":"12px"}),
            tbl_a,
        ], style={"marginBottom":"20px"}),
        html.Div([
            html.Div("DCF MODEL — EXPLICIT FORECAST (2026–2030)",
                style={"fontSize":"10px","color":MUTED,"fontWeight":"700",
                       "letterSpacing":"0.08em","marginBottom":"12px"}),
            tbl_b,
        ]),
    ])


# ── SYNERGY ENGINE ────────────────────────────────────────────────────────────

def build_synergy(cross_pct=15, cost_pct=5, wacc_pct=10):
    """
    Revenue synergies: GCP enterprise customers × penetration % × avg ACV
    Cost synergies:   % of Alphabet R&D base (infra + R&D consolidation + G&A)
    NPV: 3-year ramp PV + perpetuity beyond year 3
    Breakeven ARR: (Deal − NPV synergies) × (1+WACC)^5 / terminal multiple
    """
    gcp, acv  = 10000, 0.5           # 10k enterprise GCP customers, $500K ACV
    w         = wacc_pct / 100
    alpha_rd  = APL["rd_exp"][-1]    # $49,316M

    rev_ss  = gcp * (cross_pct/100) * acv
    cost_ss = alpha_rd * (cost_pct/100)

    rev_yr  = [rev_ss*0.20,  rev_ss*0.60,  rev_ss*1.00]
    cost_yr = [cost_ss*0.30, cost_ss*0.70, cost_ss*1.00]
    total_yr= [r+c for r,c in zip(rev_yr,cost_yr)]

    pv_ramp = sum(s/(1+w)**i for i,s in enumerate(total_yr,1))
    perp_pv = (total_yr[-1]/w) / (1+w)**3
    total_pv= pv_ramp + perp_pv

    adjusted_ev  = 32000 - total_pv
    req_arr_5yr  = adjusted_ev * (1+w)**5 / 12  # 12x terminal

    rows = [
        ["──REVENUE SYNERGIES  (Cross-sell Wiz into GCP customer base)"],
        ["Formula","= GCP Customers × Penetration% × Avg ACV"],
        ["GCP Enterprise Customers (est.)","10,000"],
        ["Cross-sell Penetration",f"{cross_pct}%"],
        ["Average Wiz ACV","$500K"],
        ["Steady-State Annual Rev Synergy",f"${rev_ss:,.0f}M"],
        ["Year 1 Rev Synergy  (20% ramp)",f"${rev_yr[0]:,.0f}M"],
        ["Year 2 Rev Synergy  (60% ramp)",f"${rev_yr[1]:,.0f}M"],
        ["Year 3 Rev Synergy  (100%)",     f"${rev_yr[2]:,.0f}M"],
        ["──COST SYNERGIES  (Infrastructure + R&D consolidation + G&A)"],
        ["Formula","= Alphabet R&D Base × Cost Synergy %"],
        ["Alphabet R&D Base (FY2024)","$49,316M"],
        ["Synergy % of R&D Base",f"{cost_pct}%"],
        ["Steady-State Annual Cost Savings",f"${cost_ss:,.0f}M"],
        ["Year 1 Cost Savings  (30% ramp)",f"${cost_yr[0]:,.0f}M"],
        ["Year 2 Cost Savings  (70% ramp)",f"${cost_yr[1]:,.0f}M"],
        ["Year 3 Cost Savings  (100%)",     f"${cost_yr[2]:,.0f}M"],
        ["──NPV OF SYNERGIES  (@10% WACC)"],
        ["Formula","PV = Σ Syn_yr/(1+w)^yr  +  Perp/((1+w)^3)"],
        ["PV of 3-year Synergy Ramp",       f"${pv_ramp:,.0f}M"],
        ["PV of Perpetuity (yr 3 onwards)", f"${perp_pv:,.0f}M"],
        ["TOTAL NPV of Synergies",          f"${total_pv:,.0f}M"],
        ["──BREAKEVEN ANALYSIS"],
        ["Deal Price",                      "$32,000M"],
        ["Less: PV of Synergies",           f"(${total_pv:,.0f}M)"],
        ["Synergy-Adjusted Deal Cost",       f"${adjusted_ev:,.0f}M"],
        ["Required Wiz ARR in 2030 (12x terminal, adj.)",f"${req_arr_5yr:,.0f}M"],
        ["Required Wiz ARR in 2030 (12x terminal, no syn.)",
         f"${32000*(1+w)**5/12:,.0f}M"],
    ]
    tbl = make_table(
        ["Metric","Value"],rows,
        highlight_rows={21,25,26,27},
        note=(f"Revenue synergy: 10,000 GCP ent. customers × {cross_pct}% penetration × $500K ACV  |  "
              f"Cost synergy: {cost_pct}% of $49,316M R&D base  |  WACC {wacc_pct}%  |  "
              f"12x terminal multiple on 2030 Wiz ARR")
    )

    fig_syn = go.Figure()
    yrs_s = ["Year 1","Year 2","Year 3"]
    fig_syn.add_trace(go.Bar(x=yrs_s,y=rev_yr,name="Revenue Synergies",marker_color=C_WIZ))
    fig_syn.add_trace(go.Bar(x=yrs_s,y=cost_yr,name="Cost Synergies",marker_color=C_ALPHA))
    fig_syn.update_layout(**PL, margin=M, barmode="stack",height=270,
        yaxis=_ax(title="$M",tickprefix="$",tickformat=",.0f"),xaxis=_ax(),
        legend=_leg(orientation="h",y=1.12,x=0))

    return tbl, fig_syn, total_pv


def fig_payback(cross_pct=15, cost_pct=5):
    w      = 0.10
    gcp    = 10000
    rev_ss = gcp * (cross_pct/100) * 0.5
    cost_ss= APL["rd_exp"][-1] * (cost_pct/100)
    balance= -32000
    cumulative=[]
    for yr in range(1,16):
        ramp  = min(1.0, yr/3)
        ann   = (rev_ss+cost_ss)*ramp
        wiz_contrib = PROJ["base"][min(yr,6)] * 0.10 if yr>3 else 0
        balance += ann + wiz_contrib
        cumulative.append(balance)
    colors = [C_WIZ if v>=0 else C_RED for v in cumulative]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(range(1,16)),y=cumulative,
        marker_color=colors,name="Cumulative Net Return ($M)"))
    fig.add_shape(type="line",x0=0,x1=16,y0=0,y1=0,
        line=dict(color=TXT,width=1,dash="dot"))
    fig.update_layout(**PL, margin=M, height=270,
        xaxis=_ax(title="Year Post-Close",tickvals=list(range(1,16))),
        yaxis=_ax(title="Cumulative Net Return ($M)",tickprefix="$",tickformat=",.0f"))
    return fig


# ── PRO FORMA TABLES ──────────────────────────────────────────────────────────

def build_is_table(wiz_arr=500, integration_cost=200):
    wiz_rev   = wiz_arr
    wiz_cogs  = round(wiz_arr * 0.30)
    wiz_gp    = wiz_rev - wiz_cogs
    wiz_rd    = round(wiz_arr * 0.40)
    wiz_sm    = round(wiz_arr * 0.40)
    wiz_ga    = round(wiz_arr * 0.10)
    wiz_ebit  = wiz_gp - wiz_rd - wiz_sm - wiz_ga
    lost_int  = -1600
    adj_ni    = round((lost_int - integration_cost) * (1-0.164))
    wiz_ni    = round(wiz_ebit * (1-0.164))
    pf_ni     = 100118 + wiz_ni + adj_ni
    pf_eps    = round(pf_ni / DEAL["shares_diluted"], 2)
    eps_chg   = round(pf_eps - DEAL["eps_2024"], 2)

    rows=[
        ["──INCOME STATEMENT ($M)"],
        ["Revenue",          "$350,018", f"${wiz_rev:,}",  "—",
         f"${350018+wiz_rev:,}"],
        ["Cost of Revenue",  "$146,306", f"${wiz_cogs:,}", "—",
         f"${146306+wiz_cogs:,}"],
        ["Gross Profit",     "$203,712", f"${wiz_gp:,}",   "—",
         f"${203712+wiz_gp:,}"],
        ["  Gross Margin",   "58.1%",    f"{wiz_gp/wiz_rev*100:.1f}%","—",
         f"{(203712+wiz_gp)/(350018+wiz_rev)*100:.1f}%"],
        ["R&D",              "$ 49,316", f"${wiz_rd:,}",   "—",
         f"${49316+wiz_rd:,}"],
        ["Sales & Marketing","$ 27,573", f"${wiz_sm:,}",   "—",
         f"${27573+wiz_sm:,}"],
        ["G&A",              "$ 15,846", f"${wiz_ga:,}",   "—",
         f"${15846+wiz_ga:,}"],
        ["Operating Income", "$112,390", f"${wiz_ebit:,}", f"(${integration_cost}M one-time)",
         f"${112390+wiz_ebit-integration_cost:,}"],
        ["  Operating Margin","32.1%",   f"{wiz_ebit/wiz_rev*100:.1f}%","—",
         f"{(112390+wiz_ebit-integration_cost)/(350018+wiz_rev)*100:.1f}%"],
        ["Other Inc/(Exp)",  "$  7,425", "—",  f"${lost_int:,}M (lost interest on $32B @ 5%)",
         f"${7425+lost_int:,}"],
        ["Pre-Tax Income",   "$119,815", f"${wiz_ebit:,}", f"${lost_int-integration_cost:,}",
         f"${119815+wiz_ebit+lost_int-integration_cost:,}"],
        ["Income Taxes",     "$ 19,697", f"${round(wiz_ebit*0.164):,}",
         f"${round((lost_int-integration_cost)*0.164):,}",
         f"${19697+round(wiz_ebit*0.164)+round((lost_int-integration_cost)*0.164):,}"],
        ["Net Income",       "$100,118", f"${wiz_ni:,}", f"${adj_ni:,}", f"${pf_ni:,}"],
        ["──EPS ANALYSIS"],
        ["Diluted Shares (M)","12,450",  "—","—","12,450  (no new shares; all-cash deal)"],
        ["Diluted EPS",       "$8.04",   "—","—",f"${pf_eps:.2f}"],
        ["EPS Impact",        "—",       "—","—",
         f"{eps_chg:+.2f}/share  ({eps_chg/DEAL['eps_2024']*100:+.1f}%)"],
    ]
    return make_table(
        ["Line Item ($M)","Alphabet FY2024","Wiz (Est.)","Adjustments","Pro Forma"],
        rows, highlight_rows={13,16,17},
        note=(f"Wiz ARR ${wiz_arr}M  |  Gross margin 70%  |  "
              f"EBIT margin {wiz_ebit/wiz_rev*100:.1f}%  |  "
              f"Integration cost ${integration_cost}M one-time  |  "
              f"Lost interest: $32B × 5% = $1,600M pre-tax  |  Tax rate 16.4%")
    )


def build_bs_table():
    rows=[
        ["──ASSETS"],
        ["Cash & Equivalents",        "$26,450M", "($26,450M → $0)",       "$0M"],
        ["Marketable Securities",     "$83,724M", "($5,724M used for deal)","$78,000M"],
        ["Total Cash + Securities",   "$110,174M","($32,000M)",             "$78,174M"],
        ["Accounts Receivable",       "$54,410M", "+$300M",                 "$54,710M"],
        ["Other Current Assets",      "$14,640M", "+$200M",                 "$14,840M"],
        ["Total Current Assets",      "$184,962M","($31,500M)",             "$153,462M"],
        ["PP&E",                      "$177,532M","+$500M",                 "$178,032M"],
        ["Goodwill",                  "$32,838M", "+$22,000M ←(1)",         "$54,838M"],
        ["Identified Intangibles",    "$2,093M",  "+$9,000M ←(2)",          "$11,093M"],
        ["Other Long-Term Assets",    "$52,869M", "+$500M",                 "$53,369M"],
        ["TOTAL ASSETS",              "$450,256M","≈ flat ←(3)",            "$450,759M"],
        ["──LIABILITIES & EQUITY"],
        ["Total Current Liabilities", "$81,671M", "+$200M",                 "$81,871M"],
        ["Long-Term Debt",            "$10,818M", "—",                      "$10,818M"],
        ["Other LT Liabilities",      "$32,683M", "+$300M",                 "$32,983M"],
        ["Total Liabilities",         "$125,172M","+$500M",                 "$125,672M"],
        ["Total Equity",              "$325,084M","($500M)",                 "$324,584M"],
        ["──PURCHASE PRICE ALLOCATION"],
        ["Purchase Price",            "$32,000M", "—","—"],
        ["(−) Wiz Tangible Assets",   "—","($1,000M)","—"],
        ["(−) Identified Intangibles","—","($9,000M)","Tech $5B + Cust $3B + Brand $1B"],
        ["= Goodwill",                "—","$22,000M","Residual; not amortized; tested annually"],
    ]
    return make_table(
        ["Line Item","Pre-Deal (YE2024)","Transaction Impact","Post-Deal (Est.)"],
        rows, highlight_rows={11,17},
        note=("(1) Goodwill = $32B purchase price − $9B intangibles − $1B net tangible assets = $22B  |  "
              "(2) Tech IP $5B + Customer relationships $3B + Brand/Trademark $1B  |  "
              "(3) Cash outflow offset by goodwill + intangibles booked — total assets roughly neutral")
    )


def build_cf_table(wiz_arr=500):
    wiz_op_cf = round(-wiz_arr * 0.16)
    rows=[
        ["──OPERATING ACTIVITIES"],
        ["Net Income",             "$100,118M", f"${wiz_op_cf+80:,}M  (Wiz net loss)",  f"${100118+wiz_op_cf+80:,}M"],
        ["(+) D&A / Amortization", "$ 17,214M", "+$900M  (intangible amort. ~10yr)",    "$ 18,114M"],
        ["(+) Stock-Based Comp",   "$ 24,515M", "+$300M  (Wiz SBC est.)",               "$ 24,815M"],
        ["(+/−) Working Capital",  "($3,429M)", "($200M)",                              "($3,629M)"],
        ["Net Operating CF",       "$125,333M", f"${wiz_op_cf:,}M",                     f"${125333+wiz_op_cf:,}M"],
        ["──INVESTING ACTIVITIES"],
        ["Capital Expenditures",   "($52,535M)","($150M)",                              "($52,685M)"],
        ["Acquisition of Wiz",     "—",         "($32,000M)  ← deal outflow",           "($32,000M)"],
        ["Mkt Sec Net",            "$ 7,839M",  "—",                                    "$ 7,839M"],
        ["Net Investing CF",       "($49,740M)","($32,150M)",                           "($81,890M)"],
        ["──FINANCING ACTIVITIES"],
        ["Share Repurchases",      "($61,778M)","—  (program suspended yr 1)",          "($61,778M)"],
        ["Dividends Paid",         "($4,889M)", "—",                                    "($4,889M)"],
        ["Net Financing CF",       "($69,134M)","—",                                    "($69,134M)"],
        ["──SUMMARY"],
        ["NET CHANGE IN CASH",     "$  2,402M", f"${wiz_op_cf-32150:,}M",              f"${2402+wiz_op_cf-32150:,}M"],
        ["FREE CASH FLOW",         "$ 72,764M", f"${wiz_op_cf-150:,}M",               f"${72764+wiz_op_cf-150:,}M"],
        ["FCF Margin",             "20.8%","—",f"{(72764+wiz_op_cf-150)/(350018+wiz_arr)*100:.1f}%"],
    ]
    return make_table(
        ["Line Item ($M)","Alphabet FY2024","Wiz / Deal Impact","Combined (Est.)"],
        rows, highlight_rows={15,16},
        note=(f"Wiz operating cash burn est. ~16% of ARR at ${wiz_arr}M scale  |  "
              "Intangible amortization $9B over 10 years = $900M/yr  |  "
              "Investing CF includes full $32B deal outflow; largest line item")
    )


# ── VERDICT FIGURES ───────────────────────────────────────────────────────────

def fig_projections(scenario="all"):
    """Always shows all 3 scenarios. Dims non-selected when a specific one is chosen."""
    cfg = [
        ("Bull Case", "bull", C_BULL,  "dot",   0.55),
        ("Base Case", "base", C_WIZ,   "solid", 0.55),
        ("Bear Case", "bear", C_RED,   "dash",  0.55),
    ]
    fig = go.Figure()
    for label, key, color, lstyle, _ in cfg:
        opacity   = 1.0 if (scenario == "all" or scenario == key) else 0.20
        line_w    = 3.0 if (scenario == "all" or scenario == key) else 1.5
        vals      = PROJ[key]
        fill_col  = "rgba(0,200,83,0.07)" if key=="base" else None
        fig.add_trace(go.Scatter(
            x=PROJ["years"], y=vals,
            name=label,
            mode="lines+markers",
            opacity=opacity,
            line=dict(color=color, dash=lstyle, width=line_w),
            marker=dict(size=7, color=color, line=dict(width=1.5, color=BG)),
            fill="tozeroy" if key=="base" else None,
            fillcolor=fill_col,
            hovertemplate=f"<b>{label}</b>  %{{x}}: $%{{y:,.0f}}M ARR<extra></extra>",
        ))
    # 2030 terminal value annotations
    for label, key, color, _, _op in cfg:
        if scenario != "all" and scenario != key: continue
        tv = PROJ[key][-1] * 8          # rough 8x terminal
        fig.add_annotation(
            x=2030.1, y=PROJ[key][-1],
            text=f"  {label[:4]}: ${PROJ[key][-1]/1000:.1f}B ARR",
            showarrow=False,
            font=dict(size=9, color=color),
            xanchor="left",
        )
    fig.add_vline(x=2025.5, line_dash="dot", line_color=C_ALPHA, line_width=1.5)
    fig.add_annotation(x=2025.7, y=PROJ["bull"][-1]*0.9,
        text="Deal Close", showarrow=False, font=dict(size=9, color=C_ALPHA))
    fig.update_layout(**PL, margin=dict(l=52,r=100,t=38,b=46), height=340,
        xaxis=_ax(title="Year", tickvals=PROJ["years"]),
        yaxis=_ax(title="Wiz ARR ($M)", tickprefix="$", ticksuffix="M"),
        legend=_leg(orientation="h", y=1.08, x=0))
    return fig


def fig_radar(scenario="base"):
    cats   = ["Strategic Fit","Valuation Discipline","Execution Risk",
              "Financial Impact","Market Position","Synergy Potential","Regulatory"]
    scores = {
        "bull": [9, 6, 7, 8, 9, 9, 8],
        "base": [9, 5, 5, 7, 8, 8, 8],
        "bear": [8, 3, 3, 5, 7, 6, 8],
    }
    clr = {"bull": C_BULL, "base": C_ALPHA, "bear": C_RED}
    vals = scores[scenario]
    # Close the polygon
    r_vals = vals + [vals[0]]
    t_vals = cats  + [cats[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=r_vals, theta=t_vals,
        fill="toself",
        fillcolor=f"rgba(66,133,244,0.15)" if scenario=="base" else
                  (f"rgba(0,230,118,0.15)" if scenario=="bull" else "rgba(234,67,53,0.15)"),
        line=dict(color=clr[scenario], width=2.5),
        marker=dict(size=8, color=clr[scenario]),
        name=f"{scenario.capitalize()} Case",
    ))
    fig.update_layout(
        **PL,
        margin=dict(l=70, r=70, t=50, b=50),
        height=340,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[0,10],
                gridcolor=BORDER, tickcolor=MUTED,
                tickfont=dict(size=8, color=MUTED),
                tickvals=[2,4,6,8,10],
            ),
            angularaxis=dict(
                gridcolor=BORDER, linecolor=BORDER,
                tickfont=dict(size=9, color=TXT),
            ),
        ),
    )
    return fig


def build_verdict_table(scenario="base"):
    data = {
        "bull": {
            "Strategic Fit":         (9, "Best-in-class CNAPP asset; seals GCP enterprise security stack vs AWS/MSFT"),
            "Valuation Discipline":  (6, "64x ARR aggressive even in bull; requires sustained 60%+ CAGR through 2028"),
            "Execution Risk":        (7, "Standalone unit + strong mgmt team mitigates; co-founders likely stay 3+ yrs"),
            "Financial Impact":      (8, "Accretive by 2027; meaningful FCF contribution by 2028"),
            "Market Position":       (9, "Cements GCP as enterprise cloud security platform of record"),
            "Synergy Potential":     (9, "10K+ GCP enterprise customers; $750M+ rev synergy NPV realizable"),
            "Regulatory":            (8, "Cleared DOJ + EC no conditions; clean deal"),
        },
        "base": {
            "Strategic Fit":         (9, "Best-in-class CNAPP; fills critical GCP security gap that was costing deals"),
            "Valuation Discipline":  (5, "64x ARR vs median comps 12–25x; paid 267% premium over Series E"),
            "Execution Risk":        (5, "Prior Alphabet integrations (Mandiant) were slow; talent retention is key"),
            "Financial Impact":      (7, "$0.13 EPS dilution yr 1 (pro forma EPS $7.91 vs $8.04); neutral by yr 3; accretive yr 4–5"),
            "Market Position":       (8, "Strong strategic rationale; rivals will accelerate CNAPP offerings"),
            "Synergy Potential":     (8, "$400–700M NPV synergies realistic; cross-sell logic is sound"),
            "Regulatory":            (8, "Cleared; signals favorable M&A environment under current admin"),
        },
        "bear": {
            "Strategic Fit":         (8, "Strategic rationale sound even in bear; product gap is real and structural"),
            "Valuation Discipline":  (3, "At $380M ARR close, implied multiple = 84x ARR. Indefensible on its own."),
            "Execution Risk":        (3, "Integration distraction + talent loss + CrowdStrike/PANW close the gap fast"),
            "Financial Impact":      (5, "EPS dilutive through 2028+; $32B cash drag weighs on buyback capacity"),
            "Market Position":       (7, "Wiz brand intact; competitive moat erodes faster than base case"),
            "Synergy Potential":     (6, "GCP cross-sell slower if enterprise market decelerates; 30% synergy capture"),
            "Regulatory":            (8, "No regulatory risk in any scenario"),
        },
    }
    d = data[scenario]
    overall = round(sum(v[0] for v in d.values()) / len(d), 1)
    color_map = {"bull": C_BULL, "base": C_ALPHA, "bear": C_RED}
    rec = {
        "bull": "STRONG BUY (strategic + financial)",
        "base": "BUY — with conviction on ARR trajectory",
        "bear": "HOLD / MONITOR — revisit at FY2026 ARR print",
    }
    rows = [["──DIMENSION SCORES"]]
    for cat,(score,rationale) in d.items():
        rows.append([cat, f"{score} / 10", rationale])
    rows += [
        ["──COMPOSITE"],
        ["OVERALL SCORE",  f"{overall} / 10", "Simple average across 7 dimensions"],
        ["RECOMMENDATION", rec[scenario],     "Subject to scenario assumptions"],
    ]
    return make_table(
        ["Dimension","Score","Rationale"],
        rows,
        highlight_rows={len(rows)-3, len(rows)-2, len(rows)-1},
        note="Execution Risk = higher score means lower risk  |  "
             "Valuation Discipline = higher score means better price paid  |  "
             "Strategic Fit and Market Position carry most weight in thesis"
    )


# =============================================================================
# APP LAYOUT
# =============================================================================

TS  = {"padding":"10px 18px","fontSize":"11px","fontWeight":"600","color":MUTED,
       "background":CARD,"border":"none","borderBottom":f"2px solid {BORDER}",
       "cursor":"pointer","letterSpacing":"0.04em"}
TSS = {**TS,"color":TXT,"borderBottom":f"2px solid {C_ALPHA}","background":BG}

HEADER = html.Div([
    html.Div([
        html.Div([
            html.Span("ALPHABET",style={"color":C_ALPHA,"fontWeight":"800"}),
            html.Span(" × ",style={"color":MUTED,"margin":"0 8px"}),
            html.Span("WIZ",style={"color":C_WIZ,"fontWeight":"800"}),
            html.Span("   M&A Senior Analyst Dashboard",
                style={"color":TXT,"fontWeight":"300","fontSize":"18px"}),
        ],style={"fontSize":"22px","letterSpacing":"-0.02em"}),
        html.Div(
            "$32B All-Cash Acquisition  ·  Announced Mar 18 2025  ·  Closed Mar 11 2026  "
            "·  Largest cybersecurity deal in history",
            style={"fontSize":"10px","color":MUTED,"marginTop":"5px"}),
    ]),
    html.Div("SAMPLE WORK — DEAL ANALYSIS",style={
        "fontSize":"9px","color":C_RED,"letterSpacing":"0.1em",
        "background":"#2a0a0a","padding":"5px 10px",
        "borderRadius":"4px","border":f"1px solid {C_RED}"}),
],style={"display":"flex","justifyContent":"space-between","alignItems":"center",
         "padding":"20px 28px 16px","borderBottom":f"2px solid {BORDER}","background":CARD})


app = dash.Dash(
    __name__,
    title="Alphabet × Wiz | M&A",
    meta_tags=[{"name":"viewport","content":"width=device-width,initial-scale=1"}],
    suppress_callback_exceptions=True,
)

app.layout = html.Div(
    style={"background":BG,"minHeight":"100vh",
           "fontFamily":"Inter,-apple-system,BlinkMacSystemFont,sans-serif","color":TXT},
    children=[
        HEADER,
        dcc.Tabs(id="tabs", value="t1",
            style={"background":CARD,"borderBottom":f"1px solid {BORDER}"},
            children=[
                dcc.Tab(label="01 · Deal Overview",  value="t1",style=TS,selected_style=TSS),
                dcc.Tab(label="02 · Alphabet",        value="t2",style=TS,selected_style=TSS),
                dcc.Tab(label="03 · Wiz Profile",     value="t3",style=TS,selected_style=TSS),
                dcc.Tab(label="04 · Valuation",       value="t4",style=TS,selected_style=TSS),
                dcc.Tab(label="05 · Synergy",         value="t5",style=TS,selected_style=TSS),
                dcc.Tab(label="06 · Risk",            value="t6",style=TS,selected_style=TSS),
                dcc.Tab(label="07 · Pro Forma",       value="t7",style=TS,selected_style=TSS),
                dcc.Tab(label="08 · Verdict",         value="t8",style=TS,selected_style=TSS),
            ]),
        html.Div(id="tab-content"),
        html.Div([
            "Sources: Alphabet 10-K/8-K FY2020–FY2024 (SEC EDGAR) · Wikipedia · TechCrunch · "
            "Crunchbase · Bloomberg (approx.) · Qatalyst · Contrary Research · Press releases",
            html.Br(),
            "All figures $M unless noted. Wiz financials are estimates. Illustrative only.",
        ],style={"fontSize":"9px","color":MUTED,"padding":"12px 28px",
                 "borderTop":f"1px solid {BORDER}","marginTop":"4px"}),
    ])

# =============================================================================
# TAB CONTENT BUILDERS
# =============================================================================

def tab_deal_overview():
    return html.Div([
        section_header("01  DEAL OVERVIEW","Transaction summary, structure, timeline & breakup fee"),
        grid(
            kpi("Enterprise Value",    "$32.0B",  "All-cash; Alphabet's largest deal ever",C_ALPHA),
            kpi("Price / ARR (base)",  "64.0x",   "$32,000M / $500M ARR at close est.",C_WIZ),
            kpi("Acquisition Premium", "2.67x",   "Over $12B Series E (May 2024)",C_YELLOW),
            kpi("Cash Coverage",       "29.1%",   "$32B / $110.2B cash+sec (YE2024)",C_RED),
            kpi("Mkt Cap at Ann.",      "~$2.0T",  "Deal = ~1.6% of market cap"),
            kpi("Breakup Fee",         "$3.2B",   "~10% of EV — largest in tech history"),
            kpi("Announced",           "Mar 18'25","DOJ cleared Mar 2025"),
            kpi("Closed",              "Mar 11'26","EC cleared — no conditions",C_WIZ),
            cols="repeat(4,1fr)",
        ),
        html.Div(style={"height":"16px"}),
        grid(
            card([
                html.Div("DEAL STRUCTURE",style={"fontSize":"10px","color":MUTED,"fontWeight":"700",
                         "letterSpacing":"0.08em","marginBottom":"14px"}),
                make_table(["Parameter","Detail"],[
                    ["Acquirer",              "Alphabet Inc. (GOOGL / GOOG)"],
                    ["Target",                "Wiz Inc. (private)"],
                    ["Deal Type",             "All-cash acquisition"],
                    ["Payment Form",          "100% cash; no equity consideration"],
                    ["Enterprise Value",      "$32,000M"],
                    ["Equity Value",          "$32,000M (no disclosed net debt)"],
                    ["Post-close Integration","Wiz joins Google Cloud as standalone unit"],
                    ["Shareholder Approval",  "Not required (Wiz is private)"],
                    ["Total VC Funding Raised","$1,900M across 6 rounds (2020–2024)"],
                    ["Last Private Valuation", "$12,000M (Series E, May 2024)"],
                    ["Wiz Product",           "CNAPP — cloud-native application protection platform"],
                    ["Key Differentiator",    "Agentless architecture; fastest enterprise adoption in SaaS history"],
                ]),
            ],col=2),
            card([
                html.Div("REGULATORY & DEAL TIMELINE",style={"fontSize":"10px","color":MUTED,"fontWeight":"700",
                         "letterSpacing":"0.08em","marginBottom":"14px"}),
                make_table(["Event","Date","Detail"],[
                    ["Initial Google Approach", "Mid-2024","Offered $23B; Wiz rejected to pursue IPO"],
                    ["IPO Market Weakness",     "H2 2024", "IPO window closed; deal revived at $32B"],
                    ["Deal Announced",          "Mar 18, 2025","$32B confirmed; press release"],
                    ["DOJ Clearance (US)",      "Mar 2025", "Cleared; no conditions (Trump-era M&A env.)"],
                    ["EC Clearance (EU)",       "Q4 2025",  "Cleared; no conditions imposed"],
                    ["Deal Closed",             "Mar 11, 2026","Wiz transitions into Google Cloud"],
                ]),
            ],col=2),
            card([
                html.Div("BREAKUP FEE ANALYSIS",style={"fontSize":"10px","color":MUTED,"fontWeight":"700",
                         "letterSpacing":"0.08em","marginBottom":"14px"}),
                make_table(["Metric","Value","Context"],[
                    ["Breakup Fee",             "$3,200M","~10% of EV — reflects high regulatory risk at signing"],
                    ["Fee as % of EV",          "10.0%",  "vs typical 3–4% in large-cap tech M&A"],
                    ["Fee / Alphabet Cash",     "2.9%",   "$3.2B / $110.2B YE2024 cash+sec"],
                    ["MSFT / Activision comp",  "$3,000M","8.5% of $69B — antitrust uncertainty"],
                    ["MSFT / LinkedIn comp",    "$725M",  "3.3% of $26.2B — clean deal"],
                    ["Oracle / Cerner comp",    "$1,400M","4.7% of $28.3B"],
                    ["Reverse Breakup Fee",     "Undisclosed","Standard: protects Wiz if Alphabet walks"],
                    ["Why High?",               "Regulatory risk","DOJ had active antitrust cases vs Google at signing"],
                ]),
            ],col=4),
            cols="repeat(8,1fr)",
        ),
    ],style={"padding":"20px 28px"})


def tab_alphabet():
    return html.Div([
        section_header("02  ALPHABET FINANCIAL PROFILE","FY2020–FY2024 consolidated performance"),
        html.Div([
            html.Div("Select Metrics:",style={**SL,"display":"inline-block","marginRight":"12px"}),
            dcc.Dropdown(id="alpha-a",
                options=[{"label":"Total Revenue","value":"total_rev"},
                         {"label":"Net Income","value":"net_income"},
                         {"label":"Operating Income","value":"op_income"},
                         {"label":"Free Cash Flow","value":"fcf"},
                         {"label":"Google Cloud Revenue","value":"cloud_rev"}],
                value="total_rev",clearable=False,
                style={"width":"210px","display":"inline-block","fontSize":"11px","marginRight":"10px"}),
            dcc.Dropdown(id="alpha-b",
                options=[{"label":"Net Income","value":"net_income"},
                         {"label":"Total Revenue","value":"total_rev"},
                         {"label":"Operating Income","value":"op_income"},
                         {"label":"Free Cash Flow","value":"fcf"},
                         {"label":"Google Cloud Revenue","value":"cloud_rev"}],
                value="net_income",clearable=False,
                style={"width":"210px","display":"inline-block","fontSize":"11px"}),
        ],style={"marginBottom":"14px"}),
        grid(
            card([html.Div("Revenue & Income (selectable)",style={"fontSize":"10px","color":MUTED,
                     "marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(id="alpha-bar",figure=fig_alphabet_bars(),
                            config={"displayModeBar":False})],col=3),
            card([html.Div("Margin Trends",style={"fontSize":"10px","color":MUTED,
                     "marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(figure=fig_margins(),config={"displayModeBar":False})],col=3),
            cols="repeat(6,1fr)",
        ),
        html.Div(style={"height":"12px"}),
        grid(
            card([html.Div("Cash + Mkt Securities vs Long-Term Debt",style={"fontSize":"10px",
                     "color":MUTED,"marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(figure=fig_cash_bridge(),config={"displayModeBar":False})],col=2),
            card([html.Div("Google Cloud — Revenue & Operating Margin",style={"fontSize":"10px",
                     "color":MUTED,"marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(figure=fig_cloud_growth(),config={"displayModeBar":False})],col=2),
            card([html.Div("Valuation Ratios (P/E, EV/Rev, EV/EBITDA)",style={"fontSize":"10px",
                     "color":MUTED,"marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(figure=fig_valuation_ratios(),config={"displayModeBar":False})],col=2),
            cols="repeat(6,1fr)",
        ),
        html.Div(style={"height":"12px"}),
        card([
            html.Div("FULL FINANCIAL METRICS TABLE",style={"fontSize":"10px","color":MUTED,
                     "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
            make_table(
                ["Metric","2020","2021","2022","2023","2024"],
                [
                    ["──INCOME STATEMENT"],
                    ["Total Revenue ($M)",     "$182,527","$257,637","$282,836","$307,394","$350,018"],
                    ["YoY Revenue Growth",     "—",       "41.1%",  "9.8%",   "8.7%",   "13.8%"],
                    ["Gross Profit ($M)",      "$97,795", "$146,698","$156,633","$174,062","$203,712"],
                    ["Gross Margin",           "55.6%",   "56.9%",  "55.3%",  "56.6%",  "58.1%"],
                    ["Operating Income ($M)",  "$41,224", "$78,714","$74,842", "$84,293","$112,390"],
                    ["Operating Margin",       "22.6%",   "30.6%",  "26.5%",  "27.4%",  "32.1%"],
                    ["Net Income ($M)",        "$40,269", "$76,033","$59,972", "$73,795","$100,118"],
                    ["Net Margin",             "22.1%",   "29.5%",  "21.2%",  "24.0%",  "28.6%"],
                    ["EBITDA Margin",          "29.0%",   "35.5%",  "32.5%",  "32.2%",  "37.0%"],
                    ["FCF ($M)",               "$42,843", "$67,012","$60,010", "$69,495","$72,764"],
                    ["FCF Margin",             "23.5%",   "26.0%",  "21.2%",  "22.6%",  "20.8%"],
                    ["──GOOGLE CLOUD SEGMENT"],
                    ["Cloud Revenue ($M)",     "$13,059", "$19,206","$26,280", "$33,088","$43,228"],
                    ["Cloud YoY Growth",       "—",       "47.1%",  "36.9%",  "25.8%",  "30.6%"],
                    ["Cloud Op Margin",        "(42.9%)", "(16.1%)","(2.7%)",  "5.2%",   "21.8%"],
                    ["Cloud as % of Total Rev","7.2%",    "7.5%",   "9.3%",   "10.8%",  "12.4%"],
                    ["──BALANCE SHEET"],
                    ["Cash + Mkt Securities",  "$131,174","$139,649","$113,762","$110,916","$110,174"],
                    ["Long-Term Debt",         "$13,932", "$14,817","$14,701", "$13,253","$10,818"],
                    ["Total Assets",           "$319,616","$359,268","$365,264","$402,392","$450,256"],
                    ["Total Equity",           "$222,545","$251,635","$256,144","$283,379","$325,084"],
                    ["Market Cap (EOY)",       "$1,185B", "$1,921B","$1,140B", "$1,756B","$2,030B"],
                    ["──VALUATION & RETURNS"],
                    ["P/E Trailing (x)",       "29.4x",   "25.3x",  "19.0x",  "23.8x",  "20.3x"],
                    ["EV / Revenue (x)",       "5.9x",    "7.0x",   "3.7x",   "5.4x",   "5.5x"],
                    ["EV / EBITDA (x)",        "20.4x",   "24.7x",  "11.5x",  "16.8x",  "14.9x"],
                    ["ROE",                    "18.1%",   "30.2%",  "23.4%",  "26.0%",  "30.8%"],
                    ["ROA",                    "12.6%",   "21.2%",  "16.4%",  "18.3%",  "22.2%"],
                    ["Share Buybacks ($M)",    "$31,149", "$50,274","$59,296", "$61,504","$61,778"],
                ], highlight_rows={1,7,20},
            ),
        ]),
    ],style={"padding":"20px 28px"})


def tab_wiz():
    return html.Div([
        section_header("03  WIZ FINANCIAL PROFILE","ARR trajectory, funding history, burn & valuation"),
        grid(
            card([html.Div("ARR Growth Trajectory",style={"fontSize":"10px","color":MUTED,
                     "marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(figure=fig_wiz_arr(),config={"displayModeBar":False})],col=2),
            card([html.Div("Valuation by Funding Round",style={"fontSize":"10px","color":MUTED,
                     "marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(figure=fig_wiz_funding(),config={"displayModeBar":False})],col=2),
            card([html.Div("EV/Revenue vs Cybersecurity Peers",style={"fontSize":"10px","color":MUTED,
                     "marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(figure=fig_wiz_peers(),config={"displayModeBar":False})],col=2),
            cols="repeat(6,1fr)",
        ),
        html.Div(style={"height":"12px"}),
        grid(
            card([
                html.Div("WIZ FUNDING ROUNDS",style={"fontSize":"10px","color":MUTED,
                         "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
                make_table(
                    ["Round","Date","Raised","Post-Money Val","EV/ARR","Lead Investors","Milestone"],
                    [
                        ["Series A",    "Dec 2020","$100M","N/D",    "—",  "Index, Sequoia, Insight","Emerged from stealth"],
                        ["Series B (1)","Apr 2021","$130M","$1.7B",  "—",  "Greenoaks, Index","Early enterprise traction"],
                        ["Series B (2)","May 2021","$120M","$1.7B",  "—",  "Greenoaks, Insight","Extended B; $250M total"],
                        ["Series C",    "Oct 2021","$250M","$6.0B",  "—",  "Greenoaks, Salesforce","Fastest SaaS to $100M ARR"],
                        ["Secondary",   "2022",    "$100M","N/D",    "—",  "Various","Partial investor liquidity"],
                        ["Series D",    "Feb 2023","$300M","$10.0B", "28.5x","Greenoaks (lead), Lightspeed","$350M ARR; 35% Fortune 100"],
                        ["Series E",    "May 2024","$1,000M","$12.0B","24.0x","a16z, Lightspeed, Thrive","$500M ARR; rejected $23B Google offer"],
                        ["ACQUISITION", "Mar 2025","$32,000M","$32.0B","64.0x","Alphabet Inc.","Largest cybersecurity deal ever"],
                    ], highlight_rows={7},
                ),
            ],col=3),
            card([
                html.Div("OPERATING METRICS & BURN RATE ESTIMATES",style={"fontSize":"10px","color":MUTED,
                         "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
                make_table(
                    ["Metric","Estimate","Assumption / Source"],
                    [
                        ["ARR at Close — Base",          "$500M", "Series E basis; management guidance"],
                        ["ARR at Close — Bull",          "$650M", "Continued 70%+ organic ARR growth"],
                        ["ARR at Close — Bear",          "$380M", "Competitive headwinds; execution lag"],
                        ["Implied ARR CAGR (Jul22–Mar26)","~50%", "$100M → $500M in ~44 months"],
                        ["Fortune 100 Penetration",      "~40–45%","~40 of top 100 US cos; last disclosed 45%"],
                        ["Headcount (Nov 2024)",         "~1,995","Last disclosed figure (Wikipedia)"],
                        ["Revenue / Employee",           "~$251K","$500M ARR / 1,995 HC"],
                        ["Estimated Gross Margin",       "~70%",  "Cloud-native CNAPP; infra-efficient"],
                        ["Estimated S&M",                "~$200M","~40% of ARR — high-growth SaaS benchmark"],
                        ["Estimated R&D",                "~$200M","~40% of ARR — security R&D intensive"],
                        ["Estimated EBIT Margin",        "~(20%)", "Pre-profitability; target breakeven at $1B ARR"],
                        ["Estimated Cash Burn",          "~$80–100M/yr","Op loss less non-cash SBC; ~16–20% of ARR"],
                        ["Net Revenue Retention (est.)", ">120%", "High-growth cloud security typical range"],
                        ["Avg Enterprise ACV",          "~$500K–$1M","Fortune 500 CNAPP pricing comps"],
                        ["Total VC Funding Raised",     "$1,900M","Across 6 rounds Dec 2020 – May 2024"],
                    ],
                ),
            ],col=3),
            cols="repeat(6,1fr)",
        ),
    ],style={"padding":"20px 28px"})


def tab_valuation():
    return html.Div([
        section_header("04  DEAL VALUATION ANALYSIS",
            "Price/ARR benchmarks · DCF model · M&A comps · premium analysis"),
        grid(
            html.Div([
                html.Div("DCF CONTROLS",style={"fontSize":"10px","color":MUTED,"fontWeight":"700",
                         "letterSpacing":"0.08em","marginBottom":"16px"}),
                html.Div("WACC (%)",style=SL),
                dcc.Slider(id="dcf-wacc",min=8,max=16,step=0.5,value=10,
                    marks={i:f"{i}%" for i in [8,10,12,14,16]},
                    tooltip={"placement":"bottom","always_visible":False}),
                html.Div(style={"height":"6px"}),
                html.Div("Terminal EV / Revenue Multiple (x)",style=SL),
                dcc.Slider(id="dcf-mult",min=6,max=25,step=1,value=12,
                    marks={i:f"{i}x" for i in [6,10,15,20,25]},
                    tooltip={"placement":"bottom","always_visible":False}),
                html.Div(style={"height":"6px"}),
                html.Div("Starting ARR at Close ($M)",style=SL),
                dcc.Slider(id="dcf-arr",min=300,max=700,step=50,value=500,
                    marks={i:f"${i}M" for i in [300,400,500,600,700]},
                    tooltip={"placement":"bottom","always_visible":False}),
                html.Div(style={"height":"16px"}),
                html.Div(id="dcf-implied-npv",style={"fontSize":"22px","fontWeight":"800",
                         "color":C_WIZ,"marginTop":"4px"}),
                html.Div("Implied Enterprise Value (DCF NPV)",
                         style={"fontSize":"9px","color":MUTED}),
            ],style={"background":CARD,"border":f"1px solid {BORDER}",
                     "borderRadius":"8px","padding":"20px","gridColumn":"span 1"}),
            card([html.Div("DCF Valuation Waterfall",style={"fontSize":"10px","color":MUTED,
                     "marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(id="dcf-waterfall",config={"displayModeBar":False})],col=3),
            card([html.Div("M&A Comps — Deal Size vs Revenue Multiple",style={"fontSize":"10px",
                     "color":MUTED,"marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(figure=fig_ma_comps(),config={"displayModeBar":False})],col=2),
            cols="repeat(6,1fr)",
        ),
        html.Div(style={"height":"12px"}),
        card([
            html.Div("DCF MODEL — FULL OUTPUT  (updates with slider)",style={"fontSize":"10px","color":MUTED,
                     "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
            html.Div(id="dcf-table"),
        ]),
        html.Div(style={"height":"12px"}),
        grid(
            card([
                html.Div("PRICE / ARR BENCHMARKS",style={"fontSize":"10px","color":MUTED,
                         "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
                make_table(
                    ["Benchmark","EV/ARR","Context"],
                    [
                        ["Wiz Deal  (this transaction)",       "64.0x","← $32B / $500M ARR base"],
                        ["Median: High-growth SaaS (>30% gr.)", "15–25x","Bloomberg / PitchBook comps"],
                        ["Wiz Series D (Feb 2023)",             "28.5x", "$10B / $350M ARR"],
                        ["Wiz Series E (May 2024)",             "24.0x", "$12B / $500M ARR"],
                        ["CrowdStrike NTM EV/Rev",              "17.8x", "Best-in-class security SaaS"],
                        ["Palo Alto Networks NTM EV/Rev",       "13.1x", "Diversified security platform"],
                        ["Cloudflare NTM EV/Rev",               "18.3x", "High-growth network security"],
                        ["Cisco × Splunk (2024)",               "7.4x",  "Mature SIEM; $3.7B rev"],
                        ["PANW × CyberArk (2025)",              "17.8x", "$1.4B rev"],
                        ["Alphabet × Mandiant (2022)",          "8.2x",  "$660M rev; threat intel"],
                        ["DEAL PREMIUM OVER MEDIAN",            "~3–4x", "64x vs 15–25x sector median"],
                    ], highlight_rows={0,10},
                ),
            ],col=3),
            card([
                html.Div("VALUATION PREMIUM ANALYSIS",style={"fontSize":"10px","color":MUTED,
                         "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
                make_table(
                    ["Metric","Value","Formula / Notes"],
                    [
                        ["Deal Price",                        "$32,000M", "Announced Mar 18, 2025"],
                        ["Wiz Last Private Valuation",        "$12,000M", "Series E, May 2024"],
                        ["Premium over Last Round",           "167%",     "($32,000−$12,000)/$12,000"],
                        ["Absolute Premium",                  "$20,000M", "Cash paid above Series E val"],
                        ["Wiz Series D Valuation (Feb 2023)", "$10,000M", "Prior round"],
                        ["Premium over Series D",             "220%",     "($32,000−$10,000)/$10,000"],
                        ["Rejected Initial Offer",            "$23,000M", "Mid-2024; Wiz wanted IPO"],
                        ["Delta: Final vs Rejected",          "+$9,000M", "Premium Wiz extracted from Alphabet"],
                        ["Required 2030 ARR (base DCF, 12x)","~$2.7B",   "10% WACC, 12x terminal"],
                        ["Required 2030 ARR (bull DCF, 15x)","~$1.8B",   "8% WACC, 15x terminal"],
                        ["Required 2030 ARR (bear DCF, 8x)", "~$4.1B",   "14% WACC, 8x terminal"],
                    ], highlight_rows={2,3,7},
                ),
            ],col=3),
            cols="repeat(6,1fr)",
        ),
    ],style={"padding":"20px 28px"})


def tab_synergy():
    return html.Div([
        section_header("05  SYNERGY MODEL",
            "Revenue (cross-sell) + cost (R&D/infra) synergies · breakeven ARR · payback"),
        grid(
            html.Div([
                html.Div("SYNERGY CONTROLS",style={"fontSize":"10px","color":MUTED,"fontWeight":"700",
                         "letterSpacing":"0.08em","marginBottom":"16px"}),
                html.Div("Cross-sell Penetration  (% of GCP enterprise customers adopting Wiz)",style=SL),
                dcc.Slider(id="syn-cross",min=5,max=30,step=1,value=15,
                    marks={i:f"{i}%" for i in [5,10,15,20,25,30]},
                    tooltip={"placement":"bottom","always_visible":False}),
                html.Div(style={"height":"6px"}),
                html.Div("Cost Synergies  (% of Alphabet R&D base = $49,316M)",style=SL),
                dcc.Slider(id="syn-cost",min=1,max=10,step=0.5,value=5,
                    marks={i:f"{i}%" for i in [1,3,5,7,10]},
                    tooltip={"placement":"bottom","always_visible":False}),
                html.Div(style={"height":"16px"}),
                html.Div("Total NPV of Synergies",style={**SL,"borderTop":f"1px solid {BORDER}","paddingTop":"14px"}),
                html.Div(id="syn-npv",style={"fontSize":"22px","fontWeight":"800","color":C_WIZ,"marginTop":"6px"}),
                html.Div("@ 10% WACC  |  3-yr ramp + perpetuity",style={"fontSize":"9px","color":MUTED}),
            ],style={"background":CARD,"border":f"1px solid {BORDER}",
                     "borderRadius":"8px","padding":"20px","gridColumn":"span 1"}),
            card([html.Div("Synergy Build-up by Year",style={"fontSize":"10px","color":MUTED,
                     "marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(id="syn-chart",config={"displayModeBar":False})],col=2),
            card([html.Div("Cumulative Return — Payback Period",style={"fontSize":"10px","color":MUTED,
                     "marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(id="syn-payback",config={"displayModeBar":False})],col=3),
            cols="repeat(6,1fr)",
        ),
        html.Div(style={"height":"12px"}),
        card([
            html.Div("SYNERGY MODEL — FULL OUTPUT  (updates with slider)",style={"fontSize":"10px","color":MUTED,
                     "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
            html.Div(id="syn-table"),
        ]),
    ],style={"padding":"20px 28px"})


def tab_risk():
    return html.Div([
        section_header("06  RISK ASSESSMENT","Antitrust · integration · competitive · valuation · key-person"),
        grid(
            card([html.Div("Risk Matrix — Severity × Likelihood (hover for mitigation)",
                     style={"fontSize":"10px","color":MUTED,"marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(figure=fig_risk_matrix(),config={"displayModeBar":False})],col=4),
            card([
                html.Div("RISK REGISTER  (sorted by score)",style={"fontSize":"10px","color":MUTED,
                         "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
                make_table(
                    ["Risk","Sev","Like","Score","Rating"],
                    sorted([
                        [RISK["cat"][i], f"{RISK['sev'][i]}/5",
                         f"{RISK['like'][i]}/5", str(RISK["score"][i]),
                         "HIGH" if RISK["score"][i]>=12 else
                         ("MED" if RISK["score"][i]>=8 else "LOW")]
                        for i in range(len(RISK["cat"]))
                    ], key=lambda x: -int(x[3])),
                ),
            ],col=2),
            cols="repeat(6,1fr)",
        ),
        html.Div(style={"height":"12px"}),
        card([
            html.Div("RISK DEEP-DIVE",style={"fontSize":"10px","color":MUTED,
                     "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
            make_table(
                ["Risk","Score","Key Drivers","Primary Mitigation","Residual Assessment"],
                [
                    ["Integration Execution","16/25",
                     "Bureaucracy; Mandiant was slow; culture clash; GCP layer conflicts",
                     "Standalone unit; Wiz retains CEO + brand + roadmap autonomy",
                     "MED — monitor product velocity at 12-month mark post-close"],
                    ["Valuation / Multiple Risk","15/25",
                     "64x ARR is outlier vs 12–25x sector median; NPV breakeven requires heroic assumptions",
                     "Synergy NPV ~$400–700M; strategic option value embedded; GCP positioning",
                     "HIGH — deal dilutive until Wiz reaches $800M+ ARR and margin improves"],
                    ["Key Person Retention","12/25",
                     "4 technical co-founders; ~2yr post-acq tenure typical; Series E investors cashed out",
                     "Golden handcuffs; multi-year equity vesting; GPM reporting line to CEO",
                     "MED — co-founder departure within 2 yrs likely; strong #2 layer needed"],
                    ["Competitive Response","12/25",
                     "MSFT Defender CNAPP; PANW CNAPP acquisition spree; CrowdStrike cloud expansion",
                     "Wiz agentless architecture is hard to replicate; GCP distribution advantage",
                     "MED-HIGH — 18–24mo window to entrench before competitive parity closes"],
                    ["Cloud Market Saturation","9/25",
                     "Hyperscaler security spend growth decelerating post-2024; CISO budget scrutiny",
                     "CNAPP/cloud security structural; not discretionary; driven by compliance requirements",
                     "LOW-MED — secular tailwind intact; cyclical headwinds 2025–2026 manageable"],
                    ["Regulatory / Antitrust","8/25",
                     "DOJ had active antitrust cases vs Google at time of announcement",
                     "DOJ + EC cleared with no conditions; Trump-era M&A env. favorable",
                     "LOW — cleared and closed; tail risk eliminated"],
                    ["Geo / Data Sovereignty","6/25",
                     "EU data-residency requirements; non-US cloud sovereignty legislation evolving",
                     "GCP data residency features; region-specific compliance roadmap",
                     "LOW — manageable with product investment; not deal-threatening"],
                ],
            ),
        ]),
    ],style={"padding":"20px 28px"})


def tab_proforma():
    return html.Div([
        section_header("07  PRO FORMA FINANCIALS",
            "Post-acquisition income statement · balance sheet · cash flow · EPS impact"),
        html.Div([
            html.Div("Wiz ARR at Close ($M):",style={**SL,"display":"inline-block","marginRight":"12px"}),
            dcc.Slider(id="pf-arr",min=380,max=700,step=10,value=500,
                marks={i:f"${i}M" for i in [380,500,650]},
                tooltip={"placement":"bottom","always_visible":False},
                style={"width":"320px","display":"inline-block","verticalAlign":"middle"}),
            html.Div("   Year-1 Integration Cost ($M, one-time):",style={**SL,"display":"inline-block",
                     "marginLeft":"30px","marginRight":"12px"}),
            dcc.Slider(id="pf-integ",min=0,max=500,step=50,value=200,
                marks={i:f"${i}M" for i in [0,100,200,300,500]},
                tooltip={"placement":"bottom","always_visible":False},
                style={"width":"280px","display":"inline-block","verticalAlign":"middle"}),
        ],style={"marginBottom":"16px","padding":"14px 20px",
                 "background":CARD,"border":f"1px solid {BORDER}","borderRadius":"8px"}),
        card([
            html.Div("INCOME STATEMENT IMPACT  (updates with sliders)",style={"fontSize":"10px","color":MUTED,
                     "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
            html.Div(id="pf-is"),
        ]),
        html.Div(style={"height":"12px"}),
        grid(
            card([
                html.Div("BALANCE SHEET IMPACT",style={"fontSize":"10px","color":MUTED,
                         "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
                build_bs_table(),
            ],col=3),
            card([
                html.Div("CASH FLOW STATEMENT IMPACT  (updates with sliders)",style={"fontSize":"10px","color":MUTED,
                         "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
                html.Div(id="pf-cf"),
            ],col=3),
            cols="repeat(6,1fr)",
        ),
    ],style={"padding":"20px 28px"})


def tab_verdict():
    return html.Div([
        section_header("08  VERDICT","Bull / Base / Bear  ·  Scorecard  ·  Final recommendation"),
        html.Div([
            html.Div("Scenario:",style={**SL,"display":"inline-block","marginRight":"12px"}),
            dcc.Dropdown(id="verdict-scenario",
                options=[{"label":"All Scenarios","value":"all"},
                         {"label":"Bull Case",    "value":"bull"},
                         {"label":"Base Case",    "value":"base"},
                         {"label":"Bear Case",    "value":"bear"}],
                value="all", clearable=False,
                style={"width":"180px","display":"inline-block","fontSize":"11px"}),
            html.Span("  —  Radar and scorecard update to selected scenario; projections always show all three",
                      style={"fontSize":"10px","color":MUTED,"marginLeft":"12px"}),
        ],style={"marginBottom":"16px","padding":"14px 20px",
                 "background":CARD,"border":f"1px solid {BORDER}","borderRadius":"8px"}),
        grid(
            card([html.Div("Wiz ARR Projections — Bull / Base / Bear (2024–2030)",
                     style={"fontSize":"10px","color":MUTED,"marginBottom":"8px","fontWeight":"600"}),
                  dcc.Graph(id="verdict-proj",config={"displayModeBar":False})],col=4),
            card([html.Div("Analyst Scorecard Radar",style={"fontSize":"10px","color":MUTED,
                     "marginBottom":"8px","fontWeight":"600"}),
                  html.Div("(select a specific scenario to display radar)",
                     style={"fontSize":"9px","color":MUTED,"marginBottom":"6px","fontStyle":"italic"}),
                  dcc.Graph(id="verdict-radar",config={"displayModeBar":False})],col=2),
            cols="repeat(6,1fr)",
        ),
        html.Div(style={"height":"12px"}),
        grid(
            card([
                html.Div("ANALYST SCORECARD  (updates with scenario)",style={"fontSize":"10px","color":MUTED,
                         "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
                html.Div(id="verdict-table"),
            ],col=3),
            card([
                html.Div("BULL / BASE / BEAR SUMMARY",style={"fontSize":"10px","color":MUTED,
                         "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
                make_table(
                    ["Dimension","Bull","Base","Bear"],
                    [
                        ["──OPERATING ASSUMPTIONS"],
                        ["ARR at Close",                "$650M",  "$500M",  "$380M"],
                        ["2030 ARR Target",             "$4.8B",  "$2.65B", "$1.58B"],
                        ["ARR CAGR (2024–2030)",        "~58%",   "~40%",   "~26%"],
                        ["EBIT Margin (2030E)",         "35%+",   "~26%",   "~5%"],
                        ["FCF Contribution (2030E)",   ">$960M", ">$400M", "Breakeven"],
                        ["──FINANCIAL OUTCOMES"],
                        ["Terminal EV (8x ARR, 2030)","$38.4B", "$21.2B", "$12.6B"],
                        ["Implied IRR",                 "~15%",   "~9%",    "~2%"],
                        ["NPV vs $32B Deal Price",     "+$6B",   "−$11B",  "−$19B"],
                        ["EPS Accretive By",           "2027E",  "2028E",  "2030E+"],
                        ["──STRATEGIC FACTORS"],
                        ["Market Position",            "Dominant","Strong", "Contested"],
                        ["Synergy Capture",            "80%+",   "~60%",   "~30%"],
                        ["Key People Retained",        "3–4 founders","2–3","1–2"],
                        ["Integration Speed",          "18 mo",  "30 mo",  "48+ mo"],
                    ], highlight_rows={7,8,9,10},
                ),
            ],col=3),
            cols="repeat(6,1fr)",
        ),
        html.Div(style={"height":"12px"}),
        card([
            html.Div("FINAL RECOMMENDATION",style={"fontSize":"10px","color":MUTED,
                     "fontWeight":"700","letterSpacing":"0.08em","marginBottom":"14px"}),
            make_table(
                ["Category","Assessment"],
                [
                    ["Strategic Rationale",
                     "COMPELLING — Wiz is the best available CNAPP asset. Fills a structural gap in GCP's "
                     "enterprise security stack. Without this, Google Cloud loses enterprise deals to "
                     "AWS+CrowdStrike and Azure+MSFT Defender. The acquisition is strategically sound "
                     "regardless of scenario."],
                    ["Financial Discipline",
                     "STRETCHED — 64x ARR is unprecedented. Median cybersecurity M&A comp is 7–18x. "
                     "Price requires a bull-case ARR trajectory ($4.8B by 2030) that only 2–3 SaaS "
                     "companies in history have achieved. The $20B premium over last private valuation "
                     "is the largest absolute premium in cybersecurity history."],
                    ["Execution Risk",
                     "MODERATE-HIGH — Alphabet's integration track record is mixed (Mandiant took 18+ months "
                     "to integrate; most co-founders departed). Standalone unit structure is the right "
                     "call but doesn't eliminate talent risk. Watch: product velocity and ARR trajectory "
                     "at 12-month mark post-close (Mar 2027) will be the primary thesis confirmation signal."],
                    ["Synergy Viability",
                     "REALISTIC BUT MARGINAL — $400–700M NPV synergies are achievable via GCP cross-sell "
                     "and R&D consolidation. That represents 1.3–2.2% of the deal value. Synergies help but "
                     "do not materially change the financial case. The deal must stand on Wiz's standalone ARR "
                     "trajectory to be financially justified."],
                    ["KEY WATCHPOINT",
                     "Wiz ARR at Dec 31, 2027 (18 months post-close). Base case requires ~$1.4B. "
                     "If Wiz ARR < $1.0B by end of 2027, the deal will almost certainly be viewed "
                     "as value-destructive. Bull case requires >$1.8B — achievable but not guaranteed."],
                    ["VERDICT",
                     "BASE CASE — STRATEGICALLY JUSTIFIED, FINANCIALLY AGGRESSIVE. "
                     "Score: 7.1/10. "
                     "Buy the strategic thesis; scrutinize the price. "
                     "The deal makes Alphabet a credible enterprise cloud security vendor. "
                     "Whether it creates shareholder value hinges entirely on ARR execution."],
                ], highlight_rows={5},
            ),
        ]),
    ],style={"padding":"20px 28px"})


# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(Output("tab-content","children"), Input("tabs","value"))
def render_tab(tab):
    return {
        "t1": tab_deal_overview,
        "t2": tab_alphabet,
        "t3": tab_wiz,
        "t4": tab_valuation,
        "t5": tab_synergy,
        "t6": tab_risk,
        "t7": tab_proforma,
        "t8": tab_verdict,
    }.get(tab, tab_deal_overview)()


@app.callback(Output("alpha-bar","figure"),
              Input("alpha-a","value"), Input("alpha-b","value"))
def update_alpha_bars(a, b):
    return fig_alphabet_bars(a, b)


@app.callback(
    Output("dcf-waterfall","figure"),
    Output("dcf-table","children"),
    Output("dcf-implied-npv","children"),
    Input("dcf-wacc","value"),
    Input("dcf-mult","value"),
    Input("dcf-arr","value"),
)
def update_dcf(wacc, mult, arr):
    dcf = run_dcf(wacc, mult, arr)
    label = f"${dcf['npv']:,.0f}M"
    return fig_dcf_waterfall(dcf), build_dcf_output(dcf, wacc, mult, arr), label


@app.callback(
    Output("syn-table","children"),
    Output("syn-chart","figure"),
    Output("syn-payback","figure"),
    Output("syn-npv","children"),
    Input("syn-cross","value"),
    Input("syn-cost","value"),
)
def update_synergy(cross_pct, cost_pct):
    tbl, fig, total_pv = build_synergy(cross_pct, cost_pct)
    return tbl, fig, fig_payback(cross_pct, cost_pct), f"${total_pv:,.0f}M"


@app.callback(
    Output("pf-is","children"),
    Output("pf-cf","children"),
    Input("pf-arr","value"),
    Input("pf-integ","value"),
)
def update_proforma(arr, integ):
    return build_is_table(arr, integ), build_cf_table(arr)


@app.callback(
    Output("verdict-proj","figure"),
    Output("verdict-radar","figure"),
    Output("verdict-table","children"),
    Input("verdict-scenario","value"),
)
def update_verdict(scenario):
    # For radar: default to base if "all" is selected
    radar_scenario = scenario if scenario != "all" else "base"
    return fig_projections(scenario), fig_radar(radar_scenario), build_verdict_table(radar_scenario)


# =============================================================================
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
