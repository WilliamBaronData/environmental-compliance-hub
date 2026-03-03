"""
report_generator.py
===================
Generates regulatory compliance reports ready for signature.

REPORTS GENERATED:
  - Tier II Chemical Inventory Report (Excel + PDF)
  - TRI Form R Summary (Excel)
  - RCRA Hazardous Waste Summary (Excel)
  - SWPPP Inspection Checklist (Excel)
  - ISO 14001 Internal Audit Report (Excel)
  - Executive Compliance Summary (Excel)

USAGE:
  from report_generator import generate_all_reports
  generate_all_reports(company_profile, facility_data)
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from schema import (TIER_II_THRESHOLDS, TRI_THRESHOLDS, RCRA_CATEGORIES,
                    ISO_14001_CLAUSES, CONESA_CRITERIA, REGULATORY_VERSIONS)

EXPORTS_DIR = PROJECT_ROOT / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_report_date():
    return datetime.now().strftime("%B %d, %Y")


# ── Tier II Report ────────────────────────────────────────────────────────────

def generate_tier_ii(profile, chemicals):
    """
    Generate EPA Tier II Chemical Inventory Report.
    Ready for submission to State SERC / Local LEPC.
    Deadline: March 1 annually.
    """
    filename = EXPORTS_DIR / f"Tier_II_Report_{profile['facility_name'].replace(' ','_')}_{datetime.now().year}.xlsx"

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:

        # Tab 1 — Facility Information
        facility_info = pd.DataFrame([
            ["FACILITY NAME",        profile["facility_name"]],
            ["FACILITY ADDRESS",     profile.get("address", "")],
            ["CITY",                 profile.get("city", "")],
            ["STATE",                profile["state"]],
            ["ZIP CODE",             profile.get("zip_code", "")],
            ["NAICS CODE",           profile["naics_code"]],
            ["EMPLOYEE COUNT",       profile["employee_count"]],
            ["EMERGENCY CONTACT",    profile.get("emergency_contact", "")],
            ["EMERGENCY PHONE",      profile.get("emergency_phone", "")],
            ["REPORT YEAR",          datetime.now().year],
            ["REPORT DATE",          get_report_date()],
            ["REGULATORY VERSION",   f"EPCRA Section 312 — {REGULATORY_VERSIONS['tier_ii']}"],
        ], columns=["FIELD", "VALUE"])
        facility_info.to_excel(writer, sheet_name="Facility Information", index=False)

        # Tab 2 — Chemical Inventory
        chem_df = pd.DataFrame(chemicals)
        chem_df.to_excel(writer, sheet_name="Chemical Inventory", index=False)

        # Tab 3 — Certification
        cert = pd.DataFrame([
            ["I certify under penalty of law that I have personally examined "
             "and am familiar with the information submitted and that based on "
             "my inquiry of those individuals responsible for obtaining the "
             "information, I believe that the submitted information is true, "
             "accurate, and complete.", ""],
            ["", ""],
            ["AUTHORIZED OFFICIAL NAME", ""],
            ["TITLE",                    ""],
            ["SIGNATURE",                "___________________________"],
            ["DATE",                     ""],
            ["PHONE",                    ""],
        ], columns=["CERTIFICATION STATEMENT", "RESPONSE"])
        cert.to_excel(writer, sheet_name="Certification", index=False)

    print(f"  ✅ Tier II Report → {filename.name}")
    return filename


# ── TRI Form R Summary ────────────────────────────────────────────────────────

def generate_tri_form_r(profile, chemical_releases):
    """
    Generate TRI Form R Summary.
    Deadline: July 1 annually.
    """
    filename = EXPORTS_DIR / f"TRI_FormR_{profile['facility_name'].replace(' ','_')}_{datetime.now().year}.xlsx"

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:

        # Tab 1 — Facility Info
        info = pd.DataFrame([
            ["FACILITY NAME",         profile["facility_name"]],
            ["STATE",                 profile["state"]],
            ["NAICS CODE",            profile["naics_code"]],
            ["PARENT COMPANY",        profile.get("parent_company", "")],
            ["DUNS NUMBER",           profile.get("duns", "")],
            ["REPORT YEAR",           datetime.now().year],
            ["SUBMISSION DEADLINE",   "July 1"],
            ["FORM TYPE",             "Form R (Section 313)"],
            ["REGULATORY VERSION",    REGULATORY_VERSIONS["tri"]],
        ], columns=["FIELD", "VALUE"])
        info.to_excel(writer, sheet_name="Facility Information", index=False)

        # Tab 2 — Chemical Releases
        releases_df = pd.DataFrame(chemical_releases)
        releases_df.to_excel(writer, sheet_name="Chemical Releases", index=False)

        # Tab 3 — Release Summary
        if chemical_releases:
            summary = pd.DataFrame([{
                "Total Chemicals Reported": len(chemical_releases),
                "Total Air Releases (lbs)": sum(c.get("air_releases_lbs", 0)
                                                for c in chemical_releases),
                "Total Water Releases (lbs)": sum(c.get("water_releases_lbs", 0)
                                                  for c in chemical_releases),
                "Total Land Releases (lbs)": sum(c.get("land_releases_lbs", 0)
                                                 for c in chemical_releases),
                "Total Off-site Transfers (lbs)": sum(c.get("offsite_transfers_lbs", 0)
                                                      for c in chemical_releases),
            }])
            summary.to_excel(writer, sheet_name="Release Summary", index=False)

        # Tab 4 — Certification
        cert = pd.DataFrame([
            ["CERTIFICATION", "I hereby certify that I have reviewed the attached "
             "documents and, to the best of my knowledge and belief, the submitted "
             "information is true and complete."],
            ["AUTHORIZED OFFICIAL", ""],
            ["TITLE", ""],
            ["SIGNATURE", "___________________________"],
            ["DATE", ""],
        ], columns=["FIELD", "VALUE"])
        cert.to_excel(writer, sheet_name="Certification", index=False)

    print(f"  ✅ TRI Form R → {filename.name}")
    return filename


# ── RCRA Hazardous Waste Summary ──────────────────────────────────────────────

def generate_rcra_summary(profile, waste_data):
    """
    Generate RCRA Hazardous Waste Generator Summary.
    Includes generator category determination.
    """
    filename = EXPORTS_DIR / f"RCRA_Waste_Summary_{profile['facility_name'].replace(' ','_')}_{datetime.now().year}.xlsx"

    # Determine generator category
    kg_month = profile.get("hazardous_waste_kg_month", 0)
    if kg_month >= 1000:
        category = "LQG — Large Quantity Generator"
        requirements = RCRA_CATEGORIES["LQG"]["requirements"]
    elif kg_month >= 100:
        category = "SQG — Small Quantity Generator"
        requirements = RCRA_CATEGORIES["SQG"]["requirements"]
    elif kg_month > 0:
        category = "VSQG — Very Small Quantity Generator"
        requirements = RCRA_CATEGORIES["VSQG"]["requirements"]
    else:
        category = "Not a Generator"
        requirements = []

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:

        # Tab 1 — Generator Profile
        profile_data = pd.DataFrame([
            ["FACILITY NAME",              profile["facility_name"]],
            ["EPA ID NUMBER",              profile.get("epa_id", "")],
            ["STATE",                      profile["state"]],
            ["NAICS CODE",                 profile["naics_code"]],
            ["GENERATOR CATEGORY",         category],
            ["MONTHLY GENERATION (kg)",    kg_month],
            ["REPORT PERIOD",              f"Q{((datetime.now().month-1)//3)+1} {datetime.now().year}"],
            ["REGULATORY VERSION",         REGULATORY_VERSIONS["rcra"]],
        ], columns=["FIELD", "VALUE"])
        profile_data.to_excel(writer, sheet_name="Generator Profile", index=False)

        # Tab 2 — Waste Inventory
        if waste_data:
            waste_df = pd.DataFrame(waste_data)
            waste_df.to_excel(writer, sheet_name="Waste Inventory", index=False)

        # Tab 3 — Requirements Checklist
        checklist = pd.DataFrame([
            {"Requirement": req, "Compliant": "", "Notes": ""}
            for req in requirements
        ])
        checklist.to_excel(writer, sheet_name="Requirements Checklist", index=False)

        # Tab 4 — Manifest Log
        manifest_cols = ["Manifest Number", "Date", "Waste Code",
                         "Quantity (kg)", "Transporter", "Disposal Facility",
                         "Signature", "Status"]
        pd.DataFrame(columns=manifest_cols).to_excel(
            writer, sheet_name="Manifest Log", index=False)

    print(f"  ✅ RCRA Summary → {filename.name}")
    return filename


# ── SWPPP Inspection Checklist ────────────────────────────────────────────────

def generate_swppp_checklist(profile):
    """
    Generate SWPPP Annual Inspection Checklist.
    Required for NPDES permit compliance.
    """
    filename = EXPORTS_DIR / f"SWPPP_Inspection_{profile['facility_name'].replace(' ','_')}_{get_timestamp()}.xlsx"

    inspection_items = [
        # Site conditions
        ("SITE CONDITIONS", "Are all stormwater discharge points identified?", ""),
        ("SITE CONDITIONS", "Are drainage pathways clear of debris?", ""),
        ("SITE CONDITIONS", "Are spill containment structures intact?", ""),
        ("SITE CONDITIONS", "Are berms and dikes in good condition?", ""),
        # BMPs
        ("BMPs", "Are all Best Management Practices (BMPs) in place?", ""),
        ("BMPs", "Are sediment controls installed and functional?", ""),
        ("BMPs", "Are vehicle tracking controls maintained?", ""),
        ("BMPs", "Are dust controls adequate?", ""),
        # Chemical storage
        ("CHEMICAL STORAGE", "Are chemical storage areas covered?", ""),
        ("CHEMICAL STORAGE", "Are secondary containment structures functional?", ""),
        ("CHEMICAL STORAGE", "Are spill kits available and stocked?", ""),
        ("CHEMICAL STORAGE", "Are SDS accessible for all chemicals?", ""),
        # Monitoring
        ("MONITORING", "Have benchmark monitoring samples been collected?", ""),
        ("MONITORING", "Are monitoring records current?", ""),
        ("MONITORING", "Are discharge samples within benchmark values?", ""),
        # Training
        ("TRAINING", "Are all personnel trained on SWPPP procedures?", ""),
        ("TRAINING", "Are training records current and documented?", ""),
        # Documentation
        ("DOCUMENTATION", "Is SWPPP document current and up to date?", ""),
        ("DOCUMENTATION", "Are all amendments documented?", ""),
        ("DOCUMENTATION", "Are inspection records filed for 3 years?", ""),
    ]

    checklist_df = pd.DataFrame(inspection_items,
        columns=["CATEGORY", "INSPECTION ITEM", "STATUS (Pass/Fail/N/A)"])
    checklist_df["CORRECTIVE ACTION"] = ""
    checklist_df["DUE DATE"] = ""
    checklist_df["RESPONSIBLE PARTY"] = ""

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        # Header info
        header = pd.DataFrame([
            ["FACILITY NAME",    profile["facility_name"]],
            ["STATE",            profile["state"]],
            ["INSPECTION DATE",  ""],
            ["INSPECTOR NAME",   ""],
            ["INSPECTOR TITLE",  ""],
            ["WEATHER",          ""],
            ["PERMIT NUMBER",    profile.get("npdes_permit", "")],
            ["NEXT INSPECTION",  ""],
        ], columns=["FIELD", "VALUE"])
        header.to_excel(writer, sheet_name="Inspection Header", index=False)
        checklist_df.to_excel(writer, sheet_name="Inspection Checklist", index=False)

        # Corrective actions tracker
        ca_cols = ["Item", "Finding", "Corrective Action",
                   "Priority", "Responsible Party", "Due Date",
                   "Completion Date", "Verified By"]
        pd.DataFrame(columns=ca_cols).to_excel(
            writer, sheet_name="Corrective Actions", index=False)

        # Certification
        cert = pd.DataFrame([
            ["I certify that this facility has been inspected in accordance "
             "with the requirements of the SWPPP and applicable permit.", ""],
            ["INSPECTOR SIGNATURE", "___________________________"],
            ["DATE", ""],
            ["TITLE", ""],
        ], columns=["CERTIFICATION", "RESPONSE"])
        cert.to_excel(writer, sheet_name="Certification", index=False)

    print(f"  ✅ SWPPP Checklist → {filename.name}")
    return filename


# ── ISO 14001 Audit Report ────────────────────────────────────────────────────

def generate_iso_audit_report(profile, aspects_data=None):
    """
    Generate ISO 14001:2015 Internal Audit Report.
    Covers all major clauses with findings and corrective actions.
    """
    filename = EXPORTS_DIR / f"ISO14001_Audit_Report_{profile['facility_name'].replace(' ','_')}_{get_timestamp()}.xlsx"

    audit_items = []
    for clause, description in ISO_14001_CLAUSES.items():
        audit_items.append({
            "Clause":       clause,
            "Requirement":  description,
            "Conformance":  "",
            "Finding":      "",
            "Evidence":     "",
            "Risk Level":   "",
            "Corrective Action": "",
            "Due Date":     "",
            "Status":       "",
        })

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:

        # Tab 1 — Audit Header
        header = pd.DataFrame([
            ["ORGANIZATION",         profile["facility_name"]],
            ["AUDIT DATE",           ""],
            ["LEAD AUDITOR",         ""],
            ["AUDIT TEAM",           ""],
            ["STANDARD",             "ISO 14001:2015"],
            ["SCOPE",                profile.get("ems_scope", "")],
            ["AUDIT TYPE",           "Internal Audit"],
            ["PREVIOUS AUDIT DATE",  ""],
            ["NEXT AUDIT DATE",      ""],
            ["REPORT DATE",          get_report_date()],
        ], columns=["FIELD", "VALUE"])
        header.to_excel(writer, sheet_name="Audit Header", index=False)

        # Tab 2 — Clause Checklist
        pd.DataFrame(audit_items).to_excel(
            writer, sheet_name="Clause Checklist", index=False)

        # Tab 3 — Aspects & Impacts
        if aspects_data is not None:
            aspects_data.to_excel(
                writer, sheet_name="Aspects & Impacts Matrix", index=False)
        else:
            conesa_cols = [
                "Aspect ID", "Aspect Description", "Impact Description",
                "Life Cycle Stage", "Type", "Nature",
                "i", "EX", "MO", "PE", "RV", "SI", "AC", "EF", "PR", "MC",
                "Conesa Score", "Classification", "Significant",
                "Objective", "PDCA Action", "Responsible", "Due Date"
            ]
            pd.DataFrame(columns=conesa_cols).to_excel(
                writer, sheet_name="Aspects & Impacts Matrix", index=False)

        # Tab 4 — Nonconformities
        nc_cols = ["NC Number", "Clause", "Description",
                   "Type (Major/Minor/OFI)", "Root Cause",
                   "Corrective Action", "Responsible Party",
                   "Due Date", "Verification Date", "Status"]
        pd.DataFrame(columns=nc_cols).to_excel(
            writer, sheet_name="Nonconformities", index=False)

        # Tab 5 — Audit Summary
        summary = pd.DataFrame([
            ["Total Clauses Audited",   len(ISO_14001_CLAUSES)],
            ["Conformances",            ""],
            ["Minor Nonconformities",   ""],
            ["Major Nonconformities",   ""],
            ["Opportunities for Improvement", ""],
            ["Overall Assessment",      ""],
            ["Recommendation",          ""],
        ], columns=["FIELD", "VALUE"])
        summary.to_excel(writer, sheet_name="Audit Summary", index=False)

        # Tab 6 — Certification
        cert = pd.DataFrame([
            ["Lead Auditor Signature",  "___________________________"],
            ["Date",                    ""],
            ["Management Representative", "___________________________"],
            ["Date",                    ""],
            ["Top Management Approval", "___________________________"],
            ["Date",                    ""],
        ], columns=["ROLE", "SIGNATURE / DATE"])
        cert.to_excel(writer, sheet_name="Signatures", index=False)

    print(f"  ✅ ISO 14001 Audit Report → {filename.name}")
    return filename


# ── Executive Compliance Summary ──────────────────────────────────────────────

def generate_executive_summary(profile, applicability_df, kpis):
    """
    Generate Executive Compliance Summary.
    One-page summary for management review.
    """
    filename = EXPORTS_DIR / f"Executive_Compliance_Summary_{profile['facility_name'].replace(' ','_')}_{get_timestamp()}.xlsx"

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:

        # Executive Summary
        summary_data = [
            ["ENVIRONMENTAL COMPLIANCE EXECUTIVE SUMMARY", ""],
            ["", ""],
            ["Facility",             profile["facility_name"]],
            ["Report Date",          get_report_date()],
            ["Reporting Period",      str(datetime.now().year)],
            ["NAICS Code",           profile["naics_code"]],
            ["State",                profile["state"]],
            ["", ""],
            ["COMPLIANCE METRICS", ""],
            ["Overall Compliance Score", f"{kpis.get('avg_score', 'N/A')}"],
            ["Total Facilities",     kpis.get("total_facilities", "N/A")],
            ["Compliant",            kpis.get("compliant", "N/A")],
            ["At Risk",              kpis.get("at_risk", "N/A")],
            ["Non-Compliant",        kpis.get("non_compliant", "N/A")],
            ["Total Violations (3yr)", kpis.get("total_violations", "N/A")],
            ["Total Penalties (3yr)", kpis.get("total_penalties", "N/A")],
            ["ISO 14001 Certified",  kpis.get("iso_certified", "N/A")],
            ["", ""],
            ["REGULATORY STATUS", ""],
        ]

        if applicability_df is not None:
            for _, row in applicability_df.iterrows():
                status = "REQUIRED" if row["applicable"] else "NOT REQUIRED"
                summary_data.append([row["regulation"], status])

        summary_data.extend([
            ["", ""],
            ["PREPARED BY",          ""],
            ["TITLE",                ""],
            ["DATE",                 ""],
            ["SIGNATURE",            "___________________________"],
            ["APPROVED BY",          ""],
            ["TITLE",                ""],
            ["DATE",                 ""],
            ["SIGNATURE",            "___________________________"],
        ])

        pd.DataFrame(summary_data, columns=["FIELD", "VALUE"]).to_excel(
            writer, sheet_name="Executive Summary", index=False)

        # Regulatory Calendar
        calendar_data = [
            {"Regulation": "EPA Tier II",    "Deadline": "March 1",   "Status": "", "Responsible": "", "Notes": ""},
            {"Regulation": "EPA TRI Form R", "Deadline": "July 1",    "Status": "", "Responsible": "", "Notes": ""},
            {"Regulation": "RCRA Manifest",  "Deadline": "Per shipment","Status": "","Responsible": "","Notes": ""},
            {"Regulation": "RMP Update",     "Deadline": "Every 5 yrs","Status": "","Responsible": "","Notes": ""},
            {"Regulation": "SWPPP Cert.",    "Deadline": "Annual",     "Status": "", "Responsible": "", "Notes": ""},
            {"Regulation": "ISO 14001 Audit","Deadline": "Annual",     "Status": "", "Responsible": "", "Notes": ""},
        ]
        pd.DataFrame(calendar_data).to_excel(
            writer, sheet_name="Regulatory Calendar", index=False)

    print(f"  ✅ Executive Summary → {filename.name}")
    return filename


# ── Generate All Reports ──────────────────────────────────────────────────────

def generate_all_reports(profile, chemicals=None, releases=None,
                         waste_data=None, aspects_df=None,
                         applicability_df=None, kpis=None):
    """
    Generate all compliance reports for a facility.
    Returns list of generated file paths.
    """
    print("\n" + "="*58)
    print(f"  Generating Compliance Reports")
    print(f"  Facility: {profile['facility_name']}")
    print(f"  Date: {get_report_date()}")
    print("="*58 + "\n")

    generated = []

    generated.append(generate_tier_ii(profile, chemicals or []))
    generated.append(generate_tri_form_r(profile, releases or []))
    generated.append(generate_rcra_summary(profile, waste_data or []))
    generated.append(generate_swppp_checklist(profile))
    generated.append(generate_iso_audit_report(profile, aspects_df))
    generated.append(generate_executive_summary(profile, applicability_df, kpis or {}))

    print(f"\n  {len(generated)} reports generated in exports/")
    return generated


if __name__ == "__main__":
    from applicability import build_company_profile

    profile = build_company_profile(
        facility_name           = "Houston Chemical Plant Demo",
        naics_code              = "325",
        state                   = "TX",
        employee_count          = 150,
        has_hazardous_chemicals = True,
        max_chemical_qty_lbs    = 15000,
        has_ehs_chemicals       = True,
        ehs_chemical_qty_lbs    = 800,
        hazardous_waste_kg_month= 250,
        has_rmp_chemicals       = True,
        rmp_chemical_name       = "Chlorine",
        rmp_chemical_qty_lbs    = 3000,
        has_stormwater_discharge= True,
        tri_chemical_qty_lbs    = 28000,
        seeks_iso_14001         = True,
    )

    chemicals = [
        {"Chemical Name": "Chlorine", "CAS Number": "7782-50-5",
         "Max Qty (lbs)": 3000, "Avg Qty (lbs)": 2000,
         "Physical State": "Gas", "Hazard Type": "EHS",
         "Storage Location": "Building A", "Container Type": "Cylinder"},
        {"Chemical Name": "Sulfuric Acid", "CAS Number": "7664-93-9",
         "Max Qty (lbs)": 15000, "Avg Qty (lbs)": 10000,
         "Physical State": "Liquid", "Hazard Type": "Hazardous",
         "Storage Location": "Tank Farm", "Container Type": "Tank"},
    ]

    generate_all_reports(profile, chemicals=chemicals)
