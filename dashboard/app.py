"""
app.py — Environmental Compliance Hub Dashboard
===============================================
Interactive dashboard covering:
  - EPA Tier II, TRI, RCRA, RMP, SWPPP
  - ISO 14001:2015 compliance
  - Conesa Matrix + Leopold Matrix
  - Life Cycle Assessment
  - PDCA tracker

USAGE:
  python dashboard/app.py
  Open: http://127.0.0.1:8053
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, Input, Output, dcc, html, dash_table
import dash_bootstrap_components as dbc
from report_generator import generate_all_reports
from applicability import build_company_profile, determine_applicability
from analysis import (load_facilities, load_conesa, load_applicability,
                      get_kpis, get_compliance_by_naics, get_compliance_by_city,
                      get_violation_analysis, get_compliance_distribution,
                      get_iso_vs_non_iso, get_top_risk_facilities,
                      get_conesa_summary, get_pdca_status)
from schema import CONESA_CLASSIFICATION, PDCA_PHASES, LIFE_CYCLE_STAGES

# ── Load data ─────────────────────────────────────────────────────────────────
df_master  = load_facilities()
conesa_df  = load_conesa()
applic_df  = load_applicability()
print(f"  Loaded {len(df_master):,} facilities")

# ── Design system ─────────────────────────────────────────────────────────────
C = {
    "bg":"#0A0E1A","panel":"#111827","panel2":"#1A2035","border":"#1F2D45",
    "primary":"#3B82F6","danger":"#EF4444","warning":"#F59E0B",
    "success":"#10B981","purple":"#8B5CF6","cyan":"#06B6D4",
    "text":"#F1F5F9","muted":"#64748B","high":"#F97316","subtle":"#94A3B8",
}
STATUS_COLORS = {
    "Compliant":"#10B981","At Risk":"#F59E0B","Non-Compliant":"#EF4444"
}
PLOT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
    font_color=C["text"],font_family="monospace",
    margin=dict(l=10,r=10,t=35,b=10))

# ── Helpers ───────────────────────────────────────────────────────────────────
def kpi_card(icon, label, value, color, card_id):
    return html.Div([
        html.Div(f"{icon}  {label}",style={"fontSize":"9px","color":C["muted"],
            "letterSpacing":"2px","textTransform":"uppercase","marginBottom":"5px"}),
        html.Div(str(value),id=card_id,style={"fontSize":"22px",
            "fontWeight":"700","color":color}),
    ],style={"background":C["panel"],"border":f"1px solid {C['border']}",
             "borderLeft":f"3px solid {color}","borderRadius":"8px",
             "padding":"14px 16px","flex":"1","minWidth":"120px"})

def chart_card(title, graph_id, height="260px", flex="1", subtitle=""):
    return html.Div([
        html.Div([
            html.Span(title,style={"fontSize":"9px","color":C["muted"],
                "letterSpacing":"2px","textTransform":"uppercase"}),
            html.Span(f" — {subtitle}",
                style={"fontSize":"8px","color":C["primary"]}) if subtitle else html.Span(),
        ],style={"marginBottom":"8px"}),
        dcc.Graph(id=graph_id,config={"displayModeBar":False},
                  style={"height":height}),
    ],style={"flex":flex,"background":C["panel"],"border":f"1px solid {C['border']}",
             "borderRadius":"8px","padding":"16px"})

# ── App ───────────────────────────────────────────────────────────────────────
app = Dash(__name__,
    external_stylesheets=[dbc.themes.DARKLY,
        "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap"],
    title="Environmental Compliance Hub | Houston MSA",
    suppress_callback_exceptions=True)

# Tabs
TAB_STYLE = {"fontSize":"10px","letterSpacing":"2px","padding":"8px 16px",
             "color":C["muted"],"background":C["panel2"],
             "border":f"1px solid {C['border']}","borderRadius":"4px 4px 0 0"}
TAB_SELECTED = {**TAB_STYLE,"color":C["cyan"],"borderBottom":f"2px solid {C['cyan']}"}

app.layout = html.Div([

    # Header
    html.Div([
        html.Div([
            html.Span("ENVIRONMENTAL",style={"color":C["success"],
                "fontSize":"28px","fontWeight":"900"}),
            html.Span(" COMPLIANCE HUB",style={"color":C["text"],
                "fontSize":"28px","fontWeight":"900"}),
        ]),
        html.Div("EPA Tier II · TRI · RCRA · RMP · SWPPP · ISO 14001:2015 — Houston MSA",
                 style={"color":C["muted"],"fontSize":"10px",
                        "letterSpacing":"3px","textTransform":"uppercase"}),
    ],style={"background":C["panel"],"borderBottom":f"1px solid {C['border']}",
             "padding":"16px 28px 12px"}),

    # KPIs
    html.Div([
        kpi_card("🏭","Facilities",       "—",C["primary"],  "kpi-total"),
        kpi_card("✅","Compliant",         "—",C["success"],  "kpi-compliant"),
        kpi_card("⚠️","At Risk",           "—",C["warning"],  "kpi-risk"),
        kpi_card("🚨","Non-Compliant",     "—",C["danger"],   "kpi-noncompliant"),
        kpi_card("📊","Avg Score",         "—",C["cyan"],     "kpi-score"),
        kpi_card("⚖️","Total Violations",  "—",C["high"],     "kpi-violations"),
        kpi_card("💰","Total Penalties",   "—",C["danger"],   "kpi-penalties"),
        kpi_card("🌿","ISO 14001 Cert.",   "—",C["success"],  "kpi-iso"),
    ],style={"display":"flex","gap":"10px","flexWrap":"wrap","padding":"14px 28px"}),

    # Tabs
    dcc.Download(id="download-report"),
    dcc.Tabs(id="tabs",value="overview",
        children=[
            dcc.Tab(label="OVERVIEW",        value="overview",
                    style=TAB_STYLE,selected_style=TAB_SELECTED),
            dcc.Tab(label="EPA COMPLIANCE",  value="epa",
                    style=TAB_STYLE,selected_style=TAB_SELECTED),
            dcc.Tab(label="ISO 14001",       value="iso",
                    style=TAB_STYLE,selected_style=TAB_SELECTED),
            dcc.Tab(label="IMPACT MATRIX",   value="matrix",
                    style=TAB_STYLE,selected_style=TAB_SELECTED),
            dcc.Tab(label="PDCA TRACKER",    value="pdca",
                    style=TAB_STYLE,selected_style=TAB_SELECTED),
            dcc.Tab(label="COMPANY PROFILE", value="profile",
                    style=TAB_STYLE,selected_style=TAB_SELECTED),
        ],
        style={"padding":"0 28px","background":C["panel2"]}),

    html.Div(id="tab-content",style={"padding":"16px 28px 28px"}),

    # Footer
    html.Div("HSE Data Science Portfolio — Project 4/5  |  Environmental Compliance Hub  |  EPA + ISO 14001:2015",
             style={"textAlign":"center","padding":"12px",
                    "borderTop":f"1px solid {C['border']}","background":C["panel"],
                    "color":C["muted"],"fontSize":"9px","letterSpacing":"1px"}),

],style={"background":C["bg"],"minHeight":"100vh","color":C["text"]})


# ── KPI Callback ──────────────────────────────────────────────────────────────
@app.callback(
    Output("kpi-total","children"),Output("kpi-compliant","children"),
    Output("kpi-risk","children"),Output("kpi-noncompliant","children"),
    Output("kpi-score","children"),Output("kpi-violations","children"),
    Output("kpi-penalties","children"),Output("kpi-iso","children"),
    Input("tabs","value"))
def cb_kpis(tab):
    kpi = get_kpis(df_master)
    return (
        str(kpi["total_facilities"]),str(kpi["compliant"]),
        str(kpi["at_risk"]),str(kpi["non_compliant"]),
        str(kpi["avg_score"]),str(kpi["total_violations"]),
        kpi["total_penalties"],str(kpi["iso_certified"]),
    )


# ── Company Profile Tab ───────────────────────────────────────────────────────

def render_profile_tab():
    """Company Profile Input + Report Generator."""
    return html.Div([

        html.Div([
            html.Div("COMPANY PROFILE — REGULATORY APPLICABILITY DETERMINATION",
                     style={"fontSize":"9px","color":C["muted"],"letterSpacing":"2px",
                            "marginBottom":"16px","textTransform":"uppercase"}),
            html.Div("Enter your facility information to determine which EPA regulations apply and generate compliance reports.",
                     style={"color":C["subtle"],"fontSize":"11px","marginBottom":"20px"}),

            # Row 1 — Basic Info
            html.Div([
                html.Div([
                    html.Label("Facility Name",style={"color":C["muted"],"fontSize":"10px","letterSpacing":"1px"}),
                    dcc.Input(id="inp-facility-name",type="text",
                              placeholder="Houston Chemical Plant",
                              style={"width":"100%","background":C["panel2"],
                                     "border":f"1px solid {C['border']}",
                                     "color":C["text"],"padding":"8px",
                                     "borderRadius":"4px","fontSize":"11px"}),
                ],style={"flex":"2"}),
                html.Div([
                    html.Label("NAICS Code",style={"color":C["muted"],"fontSize":"10px","letterSpacing":"1px"}),
                    dcc.Dropdown(id="inp-naics",
                        options=[{"label":f"{k} — {v}","value":k}
                                 for k,v in {
                                     "211":"Oil & Gas Extraction",
                                     "221":"Utilities",
                                     "236":"Construction",
                                     "324":"Petroleum & Coal",
                                     "325":"Chemical Manufacturing",
                                     "326":"Plastics & Rubber",
                                     "331":"Primary Metal",
                                     "332":"Fabricated Metal",
                                     "334":"Electronics",
                                     "336":"Transportation Equipment",
                                     "486":"Pipeline Transport",
                                     "562":"Waste Management",
                                     "622":"Hospitals",
                                 }.items()],
                        placeholder="Select NAICS...",
                        style={"fontSize":"11px","color":"#111827"}),
                ],style={"flex":"1"}),
                html.Div([
                    html.Label("State",style={"color":C["muted"],"fontSize":"10px","letterSpacing":"1px"}),
                    dcc.Dropdown(id="inp-state",
                        options=[{"label":s,"value":s} for s in
                                 ["TX","CA","LA","OH","PA","IL","NY","FL","GA","NC"]],
                        placeholder="State...",
                        style={"fontSize":"11px","color":"#111827"}),
                ],style={"flex":"0.5"}),
                html.Div([
                    html.Label("Employees",style={"color":C["muted"],"fontSize":"10px","letterSpacing":"1px"}),
                    dcc.Input(id="inp-employees",type="number",
                              placeholder="150",min=1,
                              style={"width":"100%","background":C["panel2"],
                                     "border":f"1px solid {C['border']}",
                                     "color":C["text"],"padding":"8px",
                                     "borderRadius":"4px","fontSize":"11px"}),
                ],style={"flex":"0.5"}),
            ],style={"display":"flex","gap":"12px","marginBottom":"16px","alignItems":"flex-end"}),

            # Row 2 — Chemical quantities
            html.Div([
                html.Div([
                    html.Label("Max Chemical Qty (lbs)",style={"color":C["muted"],"fontSize":"10px"}),
                    dcc.Input(id="inp-chem-qty",type="number",placeholder="15000",min=0,
                              style={"width":"100%","background":C["panel2"],
                                     "border":f"1px solid {C['border']}",
                                     "color":C["text"],"padding":"8px",
                                     "borderRadius":"4px","fontSize":"11px"}),
                ],style={"flex":"1"}),
                html.Div([
                    html.Label("EHS Chemical Qty (lbs)",style={"color":C["muted"],"fontSize":"10px"}),
                    dcc.Input(id="inp-ehs-qty",type="number",placeholder="800",min=0,
                              style={"width":"100%","background":C["panel2"],
                                     "border":f"1px solid {C['border']}",
                                     "color":C["text"],"padding":"8px",
                                     "borderRadius":"4px","fontSize":"11px"}),
                ],style={"flex":"1"}),
                html.Div([
                    html.Label("Hazardous Waste (kg/month)",style={"color":C["muted"],"fontSize":"10px"}),
                    dcc.Input(id="inp-waste-kg",type="number",placeholder="250",min=0,
                              style={"width":"100%","background":C["panel2"],
                                     "border":f"1px solid {C['border']}",
                                     "color":C["text"],"padding":"8px",
                                     "borderRadius":"4px","fontSize":"11px"}),
                ],style={"flex":"1"}),
                html.Div([
                    html.Label("TRI Chemical Qty (lbs)",style={"color":C["muted"],"fontSize":"10px"}),
                    dcc.Input(id="inp-tri-qty",type="number",placeholder="28000",min=0,
                              style={"width":"100%","background":C["panel2"],
                                     "border":f"1px solid {C['border']}",
                                     "color":C["text"],"padding":"8px",
                                     "borderRadius":"4px","fontSize":"11px"}),
                ],style={"flex":"1"}),
            ],style={"display":"flex","gap":"12px","marginBottom":"16px"}),

            # Row 3 — Checkboxes
            html.Div([
                html.Div([
                    dcc.Checklist(id="inp-checks",
                        options=[
                            {"label":"  Has Hazardous Chemicals",    "value":"has_haz"},
                            {"label":"  Has EHS Chemicals",          "value":"has_ehs"},
                            {"label":"  Has RMP Chemicals",          "value":"has_rmp"},
                            {"label":"  Has Stormwater Discharge",   "value":"has_swppp"},
                            {"label":"  Has Air Emissions",          "value":"has_air"},
                            {"label":"  Seeks ISO 14001 Certification","value":"seeks_iso"},
                        ],
                        value=["has_haz","has_ehs","has_rmp","has_swppp","seeks_iso"],
                        inline=True,
                        style={"color":C["subtle"],"fontSize":"11px","gap":"16px"},
                        inputStyle={"marginRight":"6px"},
                    ),
                ]),
            ],style={"marginBottom":"20px"}),

            # Analyze button
            html.Div([
                html.Button("🔍  ANALYZE REGULATORY REQUIREMENTS",
                    id="btn-analyze",n_clicks=0,
                    style={"background":C["primary"],"color":"white",
                           "border":"none","padding":"10px 24px",
                           "borderRadius":"6px","fontSize":"11px",
                           "fontWeight":"700","letterSpacing":"2px",
                           "cursor":"pointer","marginRight":"12px"}),
            ],style={"marginBottom":"20px"}),

            # Results
            html.Div(id="profile-results"),

        ],style={"background":C["panel"],"border":f"1px solid {C['border']}",
                 "borderRadius":"8px","padding":"24px","marginBottom":"12px"}),

        # Download buttons
        html.Div([
            html.Div("GENERATE COMPLIANCE REPORTS — READY FOR SIGNATURE",
                     style={"fontSize":"9px","color":C["muted"],"letterSpacing":"2px",
                            "marginBottom":"16px","textTransform":"uppercase"}),
            html.Div([
                html.Button("📥  Tier II Report",
                    id="btn-tier2",n_clicks=0,
                    style={"background":C["panel2"],"color":C["cyan"],
                           "border":f"1px solid {C['cyan']}","padding":"8px 16px",
                           "borderRadius":"6px","fontSize":"10px","cursor":"pointer",
                           "fontWeight":"600","letterSpacing":"1px"}),
                html.Button("📥  TRI Form R",
                    id="btn-tri",n_clicks=0,
                    style={"background":C["panel2"],"color":C["warning"],
                           "border":f"1px solid {C['warning']}","padding":"8px 16px",
                           "borderRadius":"6px","fontSize":"10px","cursor":"pointer",
                           "fontWeight":"600","letterSpacing":"1px"}),
                html.Button("📥  RCRA Summary",
                    id="btn-rcra",n_clicks=0,
                    style={"background":C["panel2"],"color":C["high"],
                           "border":f"1px solid {C['high']}","padding":"8px 16px",
                           "borderRadius":"6px","fontSize":"10px","cursor":"pointer",
                           "fontWeight":"600","letterSpacing":"1px"}),
                html.Button("📥  SWPPP Checklist",
                    id="btn-swppp",n_clicks=0,
                    style={"background":C["panel2"],"color":C["success"],
                           "border":f"1px solid {C['success']}","padding":"8px 16px",
                           "borderRadius":"6px","fontSize":"10px","cursor":"pointer",
                           "fontWeight":"600","letterSpacing":"1px"}),
                html.Button("📥  ISO 14001 Audit",
                    id="btn-iso",n_clicks=0,
                    style={"background":C["panel2"],"color":C["purple"],
                           "border":f"1px solid {C['purple']}","padding":"8px 16px",
                           "borderRadius":"6px","fontSize":"10px","cursor":"pointer",
                           "fontWeight":"600","letterSpacing":"1px"}),
                html.Button("📥  Executive Summary",
                    id="btn-exec",n_clicks=0,
                    style={"background":C["primary"],"color":"white",
                           "border":"none","padding":"8px 16px",
                           "borderRadius":"6px","fontSize":"10px","cursor":"pointer",
                           "fontWeight":"700","letterSpacing":"1px"}),
            ],style={"display":"flex","gap":"12px","flexWrap":"wrap"}),
            html.Div(id="download-status",
                     style={"color":C["success"],"fontSize":"11px","marginTop":"12px"}),
        ],style={"background":C["panel"],"border":f"1px solid {C['border']}",
                 "borderRadius":"8px","padding":"24px"}),
    ])


# ── Tab Content ───────────────────────────────────────────────────────────────
@app.callback(Output("tab-content","children"),Input("tabs","value"))
def render_tab(tab):

    # ── OVERVIEW ──────────────────────────────────────────────────────────────
    if tab == "overview":
        return html.Div([
            html.Div([
                chart_card("COMPLIANCE BY CITY — HOUSTON MSA",
                           "g-city","320px","1.3",
                           "ANSWERS: Where are the risks?"),
                chart_card("COMPLIANCE STATUS DISTRIBUTION",
                           "g-status","320px","0.7"),
                chart_card("VIOLATIONS BY SECTOR",
                           "g-naics","320px","1",
                           "ANSWERS: Which industry has most violations?"),
            ],style={"display":"flex","gap":"12px"}),
            html.Div([
                chart_card("ISO 14001 CERTIFIED vs NON-CERTIFIED",
                           "g-iso-compare","260px","1",
                           "ANSWERS: Does ISO 14001 reduce violations?"),
                chart_card("COMPLIANCE SCORE DISTRIBUTION",
                           "g-score-dist","260px","1"),
                chart_card("TOP RISK FACILITIES",
                           "g-top-risk","260px","1.3",
                           "ANSWERS: Which facilities need attention?"),
            ],style={"display":"flex","gap":"12px","marginTop":"12px"}),
        ])

    # ── EPA COMPLIANCE ─────────────────────────────────────────────────────────
    elif tab == "epa":
        applic = load_applicability()
        rows   = []
        for _, row in applic.iterrows():
            status = "✅ REQUIRED" if row["applicable"] else "❌ NOT REQUIRED"
            color  = C["danger"] if row["applicable"] else C["success"]
            rows.append(html.Tr([
                html.Td(str(row["regulation"]),
                    style={"color":C["text"],"padding":"8px 12px","fontSize":"11px",
                           "fontWeight":"600"}),
                html.Td(html.Span(status,style={"color":color,"fontSize":"10px",
                    "fontWeight":"700"}),style={"padding":"8px 12px"}),
                html.Td(str(row.get("form","N/A")),
                    style={"color":C["subtle"],"padding":"8px 12px","fontSize":"10px"}),
                html.Td(str(row.get("deadline","N/A")),
                    style={"color":C["warning"],"padding":"8px 12px","fontSize":"10px"}),
                html.Td(str(row.get("agency","N/A")),
                    style={"color":C["muted"],"padding":"8px 12px","fontSize":"9px"}),
                html.Td(html.Span(str(row.get("priority","—")),style={
                    "color":"white","background":
                        C["danger"] if row.get("priority")=="CRITICAL" else
                        C["high"]   if row.get("priority")=="HIGH" else
                        C["warning"]if row.get("priority")=="MODERATE" else C["muted"],
                    "padding":"2px 8px","borderRadius":"3px","fontSize":"9px"}),
                    style={"padding":"8px 12px"}),
            ],style={"borderBottom":f"1px solid {C['border']}"}))

        return html.Div([
            html.Div([
                html.Div("REGULATORY APPLICABILITY MATRIX — Houston Chemical Plant Demo",
                    style={"fontSize":"9px","color":C["muted"],"letterSpacing":"2px",
                           "marginBottom":"12px","textTransform":"uppercase"}),
                html.Div([
                    html.Span("NAICS 325 — Chemical Manufacturing  |  State: TX  |  ",
                        style={"color":C["muted"],"fontSize":"10px"}),
                    html.Span("EPA Version 2024  |  ISO 14001:2015",
                        style={"color":C["cyan"],"fontSize":"10px"}),
                ],style={"marginBottom":"16px"}),
                html.Table([
                    html.Thead(html.Tr([
                        html.Th(h,style={"color":C["muted"],"fontSize":"8px",
                            "letterSpacing":"2px","padding":"8px 12px",
                            "textTransform":"uppercase","fontWeight":"500",
                            "borderBottom":f"1px solid {C['border']}"})
                        for h in ["Regulation","Status","Required Form",
                                  "Deadline","Agency","Priority"]
                    ])),
                    html.Tbody(rows),
                ],style={"width":"100%","borderCollapse":"collapse"}),
            ],style={"background":C["panel"],"border":f"1px solid {C['border']}",
                     "borderRadius":"8px","padding":"20px","marginBottom":"12px"}),

            html.Div([
                chart_card("VIOLATIONS BY CITY","g-epa-city","260px","1"),
                chart_card("PENALTIES BY SECTOR","g-epa-penalties","260px","1.2",
                           "ANSWERS: Which sector pays most penalties?"),
                chart_card("RMP FACILITIES","g-epa-rmp","260px","0.8",
                           "ANSWERS: High hazard chemical sites"),
            ],style={"display":"flex","gap":"12px"}),
        ])

    # ── ISO 14001 ──────────────────────────────────────────────────────────────
    elif tab == "iso":
        return html.Div([
            html.Div([
                chart_card("ISO 14001 CERTIFICATION RATE BY SECTOR",
                           "g-iso-sector","300px","1.3",
                           "ANSWERS: Which sectors are certified?"),
                html.Div([
                    html.Div("ISO 14001:2015 — CLAUSE COVERAGE",
                        style={"fontSize":"9px","color":C["muted"],"letterSpacing":"2px",
                               "marginBottom":"12px","textTransform":"uppercase"}),
                    html.Div([
                        html.Div([
                            html.Div(clause,style={"color":C["cyan"],"fontSize":"10px",
                                "fontWeight":"700","marginBottom":"2px"}),
                            html.Div(desc,style={"color":C["muted"],"fontSize":"9px"}),
                        ],style={"padding":"8px","borderBottom":f"1px solid {C['border']}"})
                        for clause, desc in [
                            ("6.1.2","Aspects & Impacts ✅ Conesa + Leopold"),
                            ("6.1.3","Compliance Obligations ✅ EPA Regulations"),
                            ("6.2",  "Environmental Objectives ✅ PDCA Tracker"),
                            ("8.1",  "Life Cycle Perspective ✅ 6 Stages"),
                            ("9.1",  "Monitoring & Measurement ✅ KPI Dashboard"),
                            ("10.2", "Corrective Actions ✅ Non-compliance Tracker"),
                        ]
                    ]),
                ],style={"flex":"1","background":C["panel"],
                         "border":f"1px solid {C['border']}",
                         "borderRadius":"8px","padding":"16px"}),
            ],style={"display":"flex","gap":"12px"}),

            html.Div([
                chart_card("ISO 14001 vs NON-CERTIFIED — COMPLIANCE COMPARISON",
                           "g-iso-detail","260px","1.5",
                           "ANSWERS: Business case for certification"),
                chart_card("CERTIFICATION BY CITY","g-iso-city","260px","1"),
            ],style={"display":"flex","gap":"12px","marginTop":"12px"}),
        ])

    # ── IMPACT MATRIX ──────────────────────────────────────────────────────────
    elif tab == "matrix":
        return html.Div([
            html.Div([
                chart_card("CONESA MATRIX — ENVIRONMENTAL IMPACT SCORES",
                           "g-conesa","320px","1.5",
                           "I = ±[3i + 2EX + MO + PE + RV + SI + AC + EF + PR + MC]"),
                chart_card("LIFE CYCLE ASSESSMENT — IMPACT BY STAGE",
                           "g-lifecycle","320px","1",
                           "ISO 14001:2015 Clause 8.1"),
            ],style={"display":"flex","gap":"12px"}),
            html.Div([
                chart_card("CLASSIFICATION DISTRIBUTION",
                           "g-conesa-dist","260px","0.7"),
                chart_card("LEOPOLD MATRIX — TOP SIGNIFICANT INTERACTIONS",
                           "g-leopold","260px","1.5",
                           "NEPA / US Federal Standard"),
                chart_card("ASPECTS BY TYPE — DIRECT vs INDIRECT",
                           "g-aspect-type","260px","0.8"),
            ],style={"display":"flex","gap":"12px","marginTop":"12px"}),
        ])

    # ── PDCA TRACKER ──────────────────────────────────────────────────────────
    elif tab == "pdca":
        pdca = get_pdca_status(df_master)
        pdca_cards = []
        for phase, data in pdca.items():
            color = PDCA_PHASES[phase]["color"]
            pdca_cards.append(html.Div([
                html.Div(phase,style={"fontSize":"24px","fontWeight":"900",
                    "color":color,"letterSpacing":"3px"}),
                html.Div(PDCA_PHASES[phase]["description"],
                    style={"color":C["muted"],"fontSize":"9px",
                           "letterSpacing":"1px","marginBottom":"12px"}),
                html.Div(f"{data['score']}%",style={"fontSize":"36px",
                    "fontWeight":"700","color":color}),
                html.Div(f"{data['items']} facilities",
                    style={"color":C["muted"],"fontSize":"11px"}),
                html.Div(data["status"],
                    style={"color":C["subtle"],"fontSize":"10px","marginTop":"8px"}),
            ],style={"flex":"1","background":C["panel"],
                     "border":f"1px solid {C['border']}",
                     "borderLeft":f"4px solid {color}",
                     "borderRadius":"8px","padding":"20px"}))

        return html.Div([
            html.Div(pdca_cards,
                     style={"display":"flex","gap":"12px","marginBottom":"12px"}),
            html.Div([
                chart_card("COMPLIANCE TREND — PDCA CYCLE",
                           "g-pdca-trend","280px","1.3",
                           "ANSWERS: Is performance improving?"),
                chart_card("CORRECTIVE ACTIONS BY PRIORITY",
                           "g-pdca-actions","280px","1",
                           "ANSWERS: What needs immediate attention?"),
            ],style={"display":"flex","gap":"12px"}),
        ])

    elif tab == "profile":
        return render_profile_tab()
    return html.Div("Select a tab")


# ── Overview Charts ───────────────────────────────────────────────────────────
@app.callback(Output("g-city","figure"),Input("tabs","value"))
def cb_city(tab):
    if False: return go.Figure()
    data = get_compliance_by_city(df_master)
    fig  = go.Figure(go.Bar(
        x=data["avg_score"], y=data["city"], orientation="h",
        marker=dict(color=data["avg_score"],
            colorscale=[[0,C["danger"]],[0.5,C["warning"]],[1,C["success"]]]),
        text=data["avg_score"].round(1),textposition="outside",
        textfont=dict(color=C["muted"],size=10)))
    fig.add_vline(x=70,line_dash="dot",line_color=C["warning"],
                  annotation_text="Compliant Threshold",
                  annotation_font_color=C["warning"],annotation_font_size=9)
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["muted"],range=[0,110]),
        yaxis=dict(showgrid=False,color=C["text"],tickfont=dict(size=10)))
    return fig


@app.callback(Output("g-status","figure"),Input("tabs","value"))
def cb_status(tab):
    if False: return go.Figure()
    kpi  = get_kpis(df_master)
    data = pd.DataFrame({
        "status": ["Compliant","At Risk","Non-Compliant"],
        "count":  [kpi["compliant"],kpi["at_risk"],kpi["non_compliant"]],
    })
    fig = go.Figure(go.Pie(
        labels=data["status"],values=data["count"],hole=0.55,
        marker=dict(colors=[C["success"],C["warning"],C["danger"]]),
        textfont=dict(size=10,color=C["text"]),textinfo="label+percent"))
    fig.update_layout(**PLOT_BASE,showlegend=False,
        annotations=[dict(text="Status",x=0.5,y=0.5,
            font_size=11,font_color=C["muted"],showarrow=False)])
    return fig


@app.callback(Output("g-naics","figure"),Input("tabs","value"))
def cb_naics(tab):
    if False: return go.Figure()
    data = get_compliance_by_naics(df_master).head(10)
    fig  = go.Figure(go.Bar(
        x=data["total_violations"],y=data["naics_description"],
        orientation="h",
        marker_color=C["danger"],
        text=data["total_violations"],textposition="outside",
        textfont=dict(color=C["muted"],size=9)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["muted"]),
        yaxis=dict(showgrid=False,color=C["text"],tickfont=dict(size=8)))
    return fig


@app.callback(Output("g-iso-compare","figure"),Input("tabs","value"))
def cb_iso_compare(tab):
    if False: return go.Figure()
    data = get_iso_vs_non_iso(df_master)
    data["label"] = data["iso_14001_certified"].map({True:"ISO 14001",False:"Non-Certified"})
    fig  = go.Figure()
    for col, name, color in [
        ("avg_score","Avg Score",C["cyan"]),
        ("avg_violations","Avg Violations",C["danger"]),
    ]:
        fig.add_trace(go.Bar(name=name,x=data["label"],y=data[col].round(1),
            marker_color=color,text=data[col].round(1),
            textposition="outside",textfont=dict(size=10)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["text"]),
        yaxis=dict(showgrid=False,visible=False),
        barmode="group",bargap=0.2,
        legend=dict(bgcolor="rgba(0,0,0,0)",font_color=C["muted"],font_size=9))
    return fig


@app.callback(Output("g-score-dist","figure"),Input("tabs","value"))
def cb_score_dist(tab):
    if False: return go.Figure()
    data = get_compliance_distribution(df_master)
    data.columns = ["band","count"]
    fig  = go.Figure(go.Bar(
        x=data["count"],y=data["band"],orientation="h",
        marker_color=[C["danger"],C["high"],C["warning"],C["primary"],C["success"]],
        text=data["count"],textposition="outside",
        textfont=dict(color=C["muted"],size=10)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["muted"]),
        yaxis=dict(showgrid=False,color=C["text"],tickfont=dict(size=9)))
    return fig


@app.callback(Output("g-top-risk","figure"),Input("tabs","value"))
def cb_top_risk(tab):
    if False: return go.Figure()
    data = get_top_risk_facilities(df_master, n=8)
    fig  = go.Figure(go.Bar(
        x=data["compliance_score"],
        y=data["facility_name"].str[:20],
        orientation="h",
        marker=dict(color=data["compliance_score"],
            colorscale=[[0,C["danger"]],[0.5,C["warning"]],[1,C["success"]]]),
        text=data["compliance_score"].round(1),textposition="outside",
        textfont=dict(color=C["muted"],size=9)))
    fig.add_vline(x=70,line_dash="dot",line_color=C["warning"])
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["muted"],range=[0,110]),
        yaxis=dict(showgrid=False,color=C["text"],tickfont=dict(size=8)))
    return fig


# ── EPA Charts ────────────────────────────────────────────────────────────────
@app.callback(Output("g-epa-city","figure"),Input("tabs","value"))
def cb_epa_city(tab):
    if False: return go.Figure()
    data = get_compliance_by_city(df_master)
    fig  = go.Figure(go.Bar(
        x=data["city"],y=data["violations"],
        marker_color=C["danger"],
        text=data["violations"],textposition="outside",
        textfont=dict(color=C["muted"],size=10)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["text"],tickangle=15),
        yaxis=dict(showgrid=True,gridcolor=C["border"],color=C["muted"]))
    return fig


@app.callback(Output("g-epa-penalties","figure"),Input("tabs","value"))
def cb_epa_penalties(tab):
    if False: return go.Figure()
    data = get_compliance_by_naics(df_master).nlargest(8,"total_penalties")
    fig  = go.Figure(go.Bar(
        x=data["total_penalties"]/1000,
        y=data["naics_description"].str[:25],
        orientation="h",
        marker_color=C["warning"],
        text=(data["total_penalties"]/1000).round(0).astype(int).astype(str)+"K",
        textposition="outside",textfont=dict(color=C["muted"],size=9)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["muted"],title="Penalties ($K)"),
        yaxis=dict(showgrid=False,color=C["text"],tickfont=dict(size=8)))
    return fig


@app.callback(Output("g-epa-rmp","figure"),Input("tabs","value"))
def cb_epa_rmp(tab):
    if False: return go.Figure()
    data = df_master.groupby("city")["has_rmp"].sum().reset_index()
    data.columns = ["city","rmp_count"]
    data = data.sort_values("rmp_count",ascending=False)
    fig  = go.Figure(go.Bar(
        x=data["city"],y=data["rmp_count"],
        marker_color=C["purple"],
        text=data["rmp_count"],textposition="outside",
        textfont=dict(color=C["muted"],size=11)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["text"],tickangle=15),
        yaxis=dict(showgrid=False,visible=False),bargap=0.3)
    return fig


# ── ISO 14001 Charts ──────────────────────────────────────────────────────────
@app.callback(Output("g-iso-sector","figure"),Input("tabs","value"))
def cb_iso_sector(tab):
    if False: return go.Figure()
    data = (df_master.groupby("naics_description")
            .agg(total=("facility_id","count"),
                 certified=("iso_14001_certified","sum"))
            .reset_index())
    data["rate"] = (data["certified"]/data["total"]*100).round(1)
    data = data.sort_values("rate",ascending=False).head(10)
    fig  = go.Figure(go.Bar(
        x=data["rate"],y=data["naics_description"].str[:30],
        orientation="h",
        marker=dict(color=data["rate"],
            colorscale=[[0,C["danger"]],[0.5,C["warning"]],[1,C["success"]]]),
        text=data["rate"].astype(str)+"%",textposition="outside",
        textfont=dict(color=C["muted"],size=9)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["muted"],range=[0,110]),
        yaxis=dict(showgrid=False,color=C["text"],tickfont=dict(size=8)))
    return fig


@app.callback(Output("g-iso-detail","figure"),Input("tabs","value"))
def cb_iso_detail(tab):
    if False: return go.Figure()
    data = get_iso_vs_non_iso(df_master)
    data["label"] = data["iso_14001_certified"].map({True:"ISO 14001",False:"Non-Certified"})
    fig  = go.Figure()
    for col, name, color in [
        ("avg_score","Avg Compliance Score",C["success"]),
        ("avg_violations","Avg Violations (3yr)",C["danger"]),
        ("avg_penalties","Avg Penalties ($)",C["warning"]),
    ]:
        fig.add_trace(go.Bar(name=name,x=data["label"],y=data[col].round(1),
            marker_color=color,text=data[col].round(0),
            textposition="outside",textfont=dict(size=9)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["text"]),
        yaxis=dict(showgrid=False,visible=False),
        barmode="group",bargap=0.2,
        legend=dict(bgcolor="rgba(0,0,0,0)",font_color=C["muted"],font_size=9))
    return fig


@app.callback(Output("g-iso-city","figure"),Input("tabs","value"))
def cb_iso_city(tab):
    if False: return go.Figure()
    data = (df_master.groupby("city")["iso_14001_certified"]
            .mean().mul(100).round(1).reset_index())
    data.columns = ["city","cert_rate"]
    data = data.sort_values("cert_rate",ascending=False)
    fig  = go.Figure(go.Bar(
        x=data["city"],y=data["cert_rate"],
        marker_color=C["success"],
        text=data["cert_rate"].astype(str)+"%",textposition="outside",
        textfont=dict(color=C["muted"],size=10)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["text"],tickangle=15),
        yaxis=dict(showgrid=False,visible=False,range=[0,60]),bargap=0.3)
    return fig


# ── Impact Matrix Charts ──────────────────────────────────────────────────────
@app.callback(Output("g-conesa","figure"),Input("tabs","value"))
def cb_conesa(tab):
    if False: return go.Figure()
    df  = conesa_df.copy()
    colors = [CONESA_CLASSIFICATION.get(c,{}).get("color",C["muted"])
              for c in df["classification"]]
    fig = go.Figure(go.Bar(
        x=df["conesa_score"],
        y=df["aspect_description"].str[:35],
        orientation="h",
        marker_color=colors,
        text=df["conesa_score"],textposition="outside",
        textfont=dict(color=C["muted"],size=9),
        customdata=df["classification"],
        hovertemplate="<b>%{y}</b><br>Score: %{x}<br>Class: %{customdata}<extra></extra>"))
    fig.add_vline(x=25,line_dash="dot",line_color=C["warning"],
                  annotation_text="Significant threshold",
                  annotation_font_color=C["warning"],annotation_font_size=8)
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["muted"],range=[0,100]),
        yaxis=dict(showgrid=False,color=C["text"],tickfont=dict(size=8)))
    return fig


@app.callback(Output("g-lifecycle","figure"),Input("tabs","value"))
def cb_lifecycle(tab):
    if False: return go.Figure()
    from impact_matrix import build_lifecycle_matrix
    data = build_lifecycle_matrix(conesa_df)
    if data.empty: return go.Figure()
    fig  = go.Figure(go.Bar(
        x=data["avg_score"],y=data["life_cycle_stage"],
        orientation="h",
        marker=dict(color=data["avg_score"],
            colorscale=[[0,C["success"]],[0.5,C["warning"]],[1,C["danger"]]]),
        text=data["avg_score"].round(1),textposition="outside",
        textfont=dict(color=C["muted"],size=10)))
    fig.add_vline(x=25,line_dash="dot",line_color=C["warning"])
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["muted"],range=[0,80]),
        yaxis=dict(showgrid=False,color=C["text"],tickfont=dict(size=9)))
    return fig


@app.callback(Output("g-conesa-dist","figure"),Input("tabs","value"))
def cb_conesa_dist(tab):
    if False: return go.Figure()
    data  = get_conesa_summary(conesa_df)
    colors = [CONESA_CLASSIFICATION.get(c,{}).get("color",C["muted"])
              for c in data["classification"]]
    fig   = go.Figure(go.Pie(
        labels=data["classification"],values=data["count"],hole=0.5,
        marker=dict(colors=colors),
        textfont=dict(size=10,color=C["text"]),textinfo="label+percent"))
    fig.update_layout(**PLOT_BASE,showlegend=False)
    return fig


@app.callback(Output("g-leopold","figure"),Input("tabs","value"))
def cb_leopold(tab):
    if False: return go.Figure()
    from impact_matrix import build_leopold_matrix
    df_l, pivot = build_leopold_matrix()
    sig = df_l[df_l["significant"]].nlargest(10,"score")
    if sig.empty: return go.Figure()
    sig["label"] = sig["action"].str[:15] + " / " + sig["factor"].str[:15]
    fig = go.Figure(go.Bar(
        x=sig["score"],y=sig["label"],orientation="h",
        marker_color=[C["danger"] if s < 0 else C["success"] for s in sig["score"]],
        text=sig["score"],textposition="outside",
        textfont=dict(color=C["muted"],size=9)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["muted"],
                   title="Magnitude × Importance"),
        yaxis=dict(showgrid=False,color=C["text"],tickfont=dict(size=8)))
    return fig


@app.callback(Output("g-aspect-type","figure"),Input("tabs","value"))
def cb_aspect_type(tab):
    if False: return go.Figure()
    data = conesa_df.groupby("aspect_type").agg(
        count=("aspect_id","count"),
        avg_score=("conesa_score","mean")).reset_index()
    fig  = go.Figure(go.Bar(
        x=data["aspect_type"],y=data["avg_score"],
        marker_color=[C["danger"],C["warning"]][:len(data)],
        text=data["avg_score"].round(1),textposition="outside",
        textfont=dict(color=C["muted"],size=11)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["text"]),
        yaxis=dict(showgrid=False,visible=False),bargap=0.3)
    return fig


# ── PDCA Charts ───────────────────────────────────────────────────────────────
@app.callback(Output("g-pdca-trend","figure"),Input("tabs","value"))
def cb_pdca_trend(tab):
    if False: return go.Figure()
    # Simulate quarterly trend
    quarters = ["Q1 2022","Q2 2022","Q3 2022","Q4 2022",
                "Q1 2023","Q2 2023","Q3 2023","Q4 2023",
                "Q1 2024","Q2 2024"]
    import numpy as np
    rng = np.random.default_rng(42)
    scores = 45 + np.cumsum(rng.normal(2, 1.5, len(quarters)))
    scores = np.clip(scores, 0, 100)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=quarters,y=scores.round(1),name="Avg Compliance Score",
        mode="lines+markers",line=dict(color=C["success"],width=2.5),
        marker=dict(size=6),fill="tozeroy",
        fillcolor="rgba(16,185,129,0.08)"))
    fig.add_hline(y=70,line_dash="dot",line_color=C["warning"],
                  annotation_text="Compliance Target",
                  annotation_font_color=C["warning"],annotation_font_size=9)
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["muted"],tickangle=30,
                   tickfont=dict(size=8)),
        yaxis=dict(showgrid=True,gridcolor=C["border"],
                   color=C["muted"],range=[0,110]),
        legend=dict(bgcolor="rgba(0,0,0,0)",font_color=C["muted"],font_size=9))
    return fig


@app.callback(Output("g-pdca-actions","figure"),Input("tabs","value"))
def cb_pdca_actions(tab):
    if False: return go.Figure()
    data = pd.DataFrame({
        "action":   ["Update RMP filing","Tier II submission","RCRA manifest review",
                     "SWPPP annual cert.","ISO 14001 audit","TRI Form R deadline",
                     "Air permit renewal","Corrective actions"],
        "priority": ["Critical","High","High","Moderate",
                     "High","High","Moderate","Critical"],
        "days_due": [15, 45, 30, 60, 90, 120, 180, 7],
    })
    colors = [C["danger"] if p=="Critical" else
              C["high"]   if p=="High" else C["warning"]
              for p in data["priority"]]
    fig = go.Figure(go.Bar(
        x=data["days_due"],y=data["action"],orientation="h",
        marker_color=colors,
        text=data["days_due"].astype(str)+" days",
        textposition="outside",textfont=dict(color=C["muted"],size=9)))
    fig.update_layout(**PLOT_BASE,
        xaxis=dict(showgrid=False,color=C["muted"],title="Days Until Due"),
        yaxis=dict(showgrid=False,color=C["text"],tickfont=dict(size=9)))
    return fig




@app.callback(
    Output("profile-results","children"),
    Input("btn-analyze","n_clicks"),
    [
        __import__('dash').dependencies.State("inp-facility-name","value"),
        __import__('dash').dependencies.State("inp-naics","value"),
        __import__('dash').dependencies.State("inp-state","value"),
        __import__('dash').dependencies.State("inp-employees","value"),
        __import__('dash').dependencies.State("inp-chem-qty","value"),
        __import__('dash').dependencies.State("inp-ehs-qty","value"),
        __import__('dash').dependencies.State("inp-waste-kg","value"),
        __import__('dash').dependencies.State("inp-tri-qty","value"),
        __import__('dash').dependencies.State("inp-checks","value"),
    ],
    prevent_initial_call=True)
def cb_analyze(n_clicks, facility_name, naics, state, employees,
               chem_qty, ehs_qty, waste_kg, tri_qty, checks):
    if not facility_name or not naics or not state:
        return html.Div("Please fill in Facility Name, NAICS Code and State.",
                        style={"color":C["warning"],"fontSize":"11px"})
    checks = checks or []
    profile = build_company_profile(
        facility_name           = facility_name or "Demo Facility",
        naics_code              = naics or "325",
        state                   = state or "TX",
        employee_count          = int(employees or 50),
        has_hazardous_chemicals = "has_haz"   in checks,
        max_chemical_qty_lbs    = float(chem_qty or 0),
        has_ehs_chemicals       = "has_ehs"   in checks,
        ehs_chemical_qty_lbs    = float(ehs_qty or 0),
        hazardous_waste_kg_month= float(waste_kg or 0),
        has_rmp_chemicals       = "has_rmp"   in checks,
        has_stormwater_discharge= "has_swppp" in checks,
        has_air_emissions       = "has_air"   in checks,
        tri_chemical_qty_lbs    = float(tri_qty or 0),
        seeks_iso_14001         = "seeks_iso" in checks,
    )
    df = determine_applicability(profile)

    rows = []
    for _, row in df.iterrows():
        applicable = row["applicable"]
        color  = C["danger"] if applicable else C["success"]
        status = "✅ REQUIRED" if applicable else "❌ NOT REQUIRED"
        priority = row.get("priority","")
        rows.append(html.Tr([
            html.Td(str(row["regulation"]),
                    style={"color":C["text"],"padding":"8px 12px",
                           "fontSize":"11px","fontWeight":"600"}),
            html.Td(html.Span(status,style={"color":color,"fontSize":"10px",
                    "fontWeight":"700"}),style={"padding":"8px 12px"}),
            html.Td(str(row.get("form","N/A")),
                    style={"color":C["subtle"],"padding":"8px 12px","fontSize":"10px"}),
            html.Td(str(row.get("deadline","N/A")),
                    style={"color":C["warning"],"padding":"8px 12px","fontSize":"10px"}),
            html.Td(html.Span(str(priority),style={
                "color":"white",
                "background": C["danger"]  if priority=="CRITICAL" else
                              C["high"]    if priority=="HIGH"     else
                              C["warning"] if priority=="MODERATE" else C["muted"],
                "padding":"2px 8px","borderRadius":"3px","fontSize":"9px"}),
                style={"padding":"8px 12px"}),
        ],style={"borderBottom":f"1px solid {C['border']}"}))

    required = df[df["applicable"]==True].shape[0]
    return html.Div([
        html.Div([
            html.Span(f"✅ Analysis complete for {facility_name}  |  ",
                      style={"color":C["success"],"fontSize":"11px"}),
            html.Span(f"{required} regulations apply  |  ",
                      style={"color":C["warning"],"fontSize":"11px","fontWeight":"700"}),
            html.Span(f"NAICS {naics} — {state}",
                      style={"color":C["muted"],"fontSize":"11px"}),
        ],style={"marginBottom":"12px"}),
        html.Table([
            html.Thead(html.Tr([
                html.Th(h,style={"color":C["muted"],"fontSize":"8px",
                    "letterSpacing":"2px","padding":"8px 12px",
                    "textTransform":"uppercase","fontWeight":"500",
                    "borderBottom":f"1px solid {C['border']}"})
                for h in ["Regulation","Status","Required Form","Deadline","Priority"]
            ])),
            html.Tbody(rows),
        ],style={"width":"100%","borderCollapse":"collapse"}),
    ])


@app.callback(
    Output("download-report","data"),
    Output("download-status","children"),
    Input("btn-tier2","n_clicks"),
    Input("btn-tri","n_clicks"),
    Input("btn-rcra","n_clicks"),
    Input("btn-swppp","n_clicks"),
    Input("btn-iso","n_clicks"),
    Input("btn-exec","n_clicks"),
    prevent_initial_call=True)
def cb_download(n1,n2,n3,n4,n5,n6):
    from dash import ctx
    import base64
    triggered = ctx.triggered_id
    profile = build_company_profile(
        facility_name="Houston Chemical Plant Demo",
        naics_code="325", state="TX", employee_count=150,
        has_hazardous_chemicals=True, max_chemical_qty_lbs=15000,
        has_ehs_chemicals=True, ehs_chemical_qty_lbs=800,
        hazardous_waste_kg_month=250, has_rmp_chemicals=True,
        rmp_chemical_name="Chlorine", rmp_chemical_qty_lbs=3000,
        has_stormwater_discharge=True, tri_chemical_qty_lbs=28000,
        seeks_iso_14001=True,
    )
    from report_generator import (generate_tier_ii, generate_tri_form_r,
                                   generate_rcra_summary, generate_swppp_checklist,
                                   generate_iso_audit_report, generate_executive_summary)
    from analysis import get_kpis
    kpis = get_kpis(df_master)

    btn_map = {
        "btn-tier2": (generate_tier_ii,    [profile, []],       "Tier II Report"),
        "btn-tri":   (generate_tri_form_r,  [profile, []],       "TRI Form R"),
        "btn-rcra":  (generate_rcra_summary,[profile, []],       "RCRA Summary"),
        "btn-swppp": (generate_swppp_checklist,[profile],        "SWPPP Checklist"),
        "btn-iso":   (generate_iso_audit_report,[profile],       "ISO 14001 Audit"),
        "btn-exec":  (generate_executive_summary,[profile,None,kpis],"Executive Summary"),
    }
    if triggered not in btn_map:
        return None, ""

    func, args, label = btn_map[triggered]
    filepath = func(*args)
    with open(filepath,"rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return (
        {"content": encoded, "filename": filepath.name,
         "base64": True, "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        f"✅ {label} downloaded — {filepath.name}"
    )


# Profile tab integrated directly in render_tab above
# Profile tab integrated directly in render_tab aboveif __name__ == "__main__":
    print(f"\n{'='*52}")
    print(f"  Environmental Compliance Hub")
    print(f"  {len(df_master):,} facilities loaded")
    print(f"  EPA + ISO 14001:2015 + Conesa + Leopold")
    print(f"  Open: http://127.0.0.1:8053")
    print(f"{'='*52}\n")
    app.run(debug=True, host="127.0.0.1", port=8053)


if __name__ == "__main__":
    print(f"\n{'='*52}")
    print(f"  Environmental Compliance Hub")
    print(f"  {len(df_master):,} facilities loaded")
    print(f"  EPA + ISO 14001:2015 + Conesa + Leopold")
    print(f"  Open: http://127.0.0.1:8053")
    print(f"{'='*52}\n")
    app.run(debug=True, host="127.0.0.1", port=8053)
