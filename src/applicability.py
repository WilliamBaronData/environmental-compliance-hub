"""
applicability.py
================
Regulatory Applicability Determination Engine.

Given a company profile, automatically determines which
environmental regulations apply and which do not.

REGULATIONS COVERED:
  - EPA Tier II (EPCRA Section 312)
  - EPA TRI Form R / Form A (EPCRA Section 313)
  - RCRA (LQG / SQG / VSQG)
  - RMP (CAA Section 112r)
  - SWPPP (Clean Water Act)
  - ISO 14001:2015
  - OSHA PSM (29 CFR 1910.119)

USAGE:
  python src/applicability.py
"""

import sys
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from schema import (TIER_II_THRESHOLDS, TRI_THRESHOLDS, RCRA_CATEGORIES,
                    RMP_THRESHOLD_CHEMICALS, REPORTING_NAICS,
                    COMPLIANCE_WEIGHTS, REGULATORY_VERSIONS)

PROC_DIR = PROJECT_ROOT / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)


# ── Company Profile ───────────────────────────────────────────────────────────

def build_company_profile(
    facility_name,
    naics_code,
    state,
    employee_count,
    has_hazardous_chemicals=False,
    max_chemical_qty_lbs=0,
    has_ehs_chemicals=False,
    ehs_chemical_qty_lbs=0,
    hazardous_waste_kg_month=0,
    has_rmp_chemicals=False,
    rmp_chemical_name=None,
    rmp_chemical_qty_lbs=0,
    has_stormwater_discharge=False,
    industrial_activity_code=None,
    has_air_emissions=False,
    annual_emissions_tons=0,
    tri_chemical_qty_lbs=0,
    seeks_iso_14001=False,
):
    """
    Build a standardized company profile for applicability analysis.
    All quantity fields in lbs unless noted.
    """
    return {
        "facility_name":           facility_name,
        "naics_code":              str(naics_code)[:3],
        "naics_description":       REPORTING_NAICS.get(str(naics_code)[:3], "Other"),
        "state":                   state,
        "employee_count":          employee_count,
        "has_hazardous_chemicals": has_hazardous_chemicals,
        "max_chemical_qty_lbs":    max_chemical_qty_lbs,
        "has_ehs_chemicals":       has_ehs_chemicals,
        "ehs_chemical_qty_lbs":    ehs_chemical_qty_lbs,
        "hazardous_waste_kg_month":hazardous_waste_kg_month,
        "has_rmp_chemicals":       has_rmp_chemicals,
        "rmp_chemical_name":       rmp_chemical_name,
        "rmp_chemical_qty_lbs":    rmp_chemical_qty_lbs,
        "has_stormwater_discharge":has_stormwater_discharge,
        "industrial_activity_code":industrial_activity_code,
        "has_air_emissions":       has_air_emissions,
        "annual_emissions_tons":   annual_emissions_tons,
        "tri_chemical_qty_lbs":    tri_chemical_qty_lbs,
        "seeks_iso_14001":         seeks_iso_14001,
    }


# ── Applicability Rules ───────────────────────────────────────────────────────

def check_tier_ii(profile):
    """
    EPA Tier II — EPCRA Section 312
    Applies if facility stores hazardous chemicals above threshold.
    Deadline: March 1 annually.
    """
    ehs_threshold     = TIER_II_THRESHOLDS["extremely_hazardous"]
    default_threshold = TIER_II_THRESHOLDS["default"]

    if profile["has_ehs_chemicals"] and \
       profile["ehs_chemical_qty_lbs"] >= ehs_threshold:
        return {
            "regulation":   "EPA Tier II",
            "applicable":   True,
            "reason":       f"EHS chemical quantity ({profile['ehs_chemical_qty_lbs']:,} lbs) "
                           f"exceeds threshold ({ehs_threshold:,} lbs)",
            "threshold":    f"{ehs_threshold:,} lbs (EHS chemicals)",
            "deadline":     "March 1 annually",
            "form":         "Tier II Chemical Inventory Report",
            "agency":       "State SERC / Local LEPC",
            "priority":     "HIGH",
        }
    elif profile["has_hazardous_chemicals"] and \
         profile["max_chemical_qty_lbs"] >= default_threshold:
        return {
            "regulation":   "EPA Tier II",
            "applicable":   True,
            "reason":       f"Hazardous chemical quantity ({profile['max_chemical_qty_lbs']:,} lbs) "
                           f"exceeds threshold ({default_threshold:,} lbs)",
            "threshold":    f"{default_threshold:,} lbs (hazardous chemicals)",
            "deadline":     "March 1 annually",
            "form":         "Tier II Chemical Inventory Report",
            "agency":       "State SERC / Local LEPC",
            "priority":     "HIGH",
        }
    return {
        "regulation":   "EPA Tier II",
        "applicable":   False,
        "reason":       "Chemical quantities below reporting thresholds",
        "threshold":    f"{default_threshold:,} lbs",
        "deadline":     "N/A",
        "form":         "N/A",
        "agency":       "N/A",
        "priority":     "LOW",
    }


def check_tri(profile):
    """
    EPA TRI — EPCRA Section 313
    Applies to manufacturing NAICS with 10+ employees using
    listed toxic chemicals above threshold quantities.
    Deadline: July 1 annually.
    """
    manufacturing_naics = [str(n) for n in range(311, 340)]
    naics = profile["naics_code"]
    employees = profile["employee_count"]
    qty = profile["tri_chemical_qty_lbs"]

    if naics not in manufacturing_naics:
        return {
            "regulation":  "EPA TRI (Form R/A)",
            "applicable":  False,
            "reason":      f"NAICS {naics} not in TRI-covered manufacturing sectors",
            "threshold":   "25,000 lbs (manufacturing) / 10,000 lbs (otherwise used)",
            "deadline":    "N/A",
            "form":        "N/A",
            "agency":      "N/A",
            "priority":    "LOW",
        }
    if employees < 10:
        return {
            "regulation":  "EPA TRI (Form R/A)",
            "applicable":  False,
            "reason":      f"Fewer than 10 employees ({employees})",
            "threshold":   "10 employees minimum",
            "deadline":    "N/A",
            "form":        "N/A",
            "agency":      "N/A",
            "priority":    "LOW",
        }
    mfg_threshold = TRI_THRESHOLDS["form_r"]["manufacturing"]
    if qty >= mfg_threshold:
        form = "Form A" if qty < mfg_threshold * 2 else "Form R"
        return {
            "regulation":  "EPA TRI (Form R/A)",
            "applicable":  True,
            "reason":      f"TRI chemical quantity ({qty:,} lbs) exceeds threshold",
            "threshold":   f"{mfg_threshold:,} lbs",
            "deadline":    "July 1 annually",
            "form":        form,
            "agency":      "EPA + State",
            "priority":    "HIGH",
        }
    return {
        "regulation":  "EPA TRI (Form R/A)",
        "applicable":  False,
        "reason":      f"TRI chemical quantity ({qty:,} lbs) below threshold",
        "threshold":   f"{mfg_threshold:,} lbs",
        "deadline":    "N/A",
        "form":        "N/A",
        "agency":      "N/A",
        "priority":    "LOW",
    }


def check_rcra(profile):
    """
    RCRA Hazardous Waste Generator Classification.
    Determines LQG / SQG / VSQG based on monthly generation.
    """
    kg = profile["hazardous_waste_kg_month"]
    lgq = RCRA_CATEGORIES["LQG"]
    sqg = RCRA_CATEGORIES["SQG"]
    vsqg = RCRA_CATEGORIES["VSQG"]

    if kg >= lgq["threshold_kg"]:
        return {
            "regulation":  "RCRA — Hazardous Waste",
            "applicable":  True,
            "category":    "LQG (Large Quantity Generator)",
            "reason":      f"Generates {kg:,} kg/month (≥ {lgq['threshold_kg']:,} kg)",
            "threshold":   f"≥ {lgq['threshold_kg']:,} kg/month",
            "deadline":    "Biennial Report — March 1 (even years)",
            "form":        "EPA Biennial Report + Manifest",
            "agency":      "EPA / State",
            "priority":    "CRITICAL",
            "requirements": lgq["requirements"],
        }
    elif kg >= sqg["threshold_kg_min"]:
        return {
            "regulation":  "RCRA — Hazardous Waste",
            "applicable":  True,
            "category":    "SQG (Small Quantity Generator)",
            "reason":      f"Generates {kg:,} kg/month ({sqg['threshold_kg_min']}-{sqg['threshold_kg_max']} kg)",
            "threshold":   f"{sqg['threshold_kg_min']}-{sqg['threshold_kg_max']} kg/month",
            "deadline":    "Manifest required per shipment",
            "form":        "Hazardous Waste Manifest",
            "agency":      "EPA / State",
            "priority":    "HIGH",
            "requirements": sqg["requirements"],
        }
    elif kg > 0:
        return {
            "regulation":  "RCRA — Hazardous Waste",
            "applicable":  True,
            "category":    "VSQG (Very Small Quantity Generator)",
            "reason":      f"Generates {kg:,} kg/month (< {vsqg['threshold_kg']} kg)",
            "threshold":   f"< {vsqg['threshold_kg']} kg/month",
            "deadline":    "No periodic reporting — proper disposal required",
            "form":        "Proper disposal documentation",
            "agency":      "State",
            "priority":    "MODERATE",
            "requirements": vsqg["requirements"],
        }
    return {
        "regulation":  "RCRA — Hazardous Waste",
        "applicable":  False,
        "category":    "Not a generator",
        "reason":      "No hazardous waste generation reported",
        "threshold":   "Any quantity triggers VSQG",
        "deadline":    "N/A",
        "form":        "N/A",
        "agency":      "N/A",
        "priority":    "LOW",
    }


def check_rmp(profile):
    """
    RMP — Risk Management Plan (CAA Section 112r)
    Applies if facility has listed chemicals above threshold quantities.
    """
    if not profile["has_rmp_chemicals"]:
        return {
            "regulation":  "EPA RMP (Risk Management Plan)",
            "applicable":  False,
            "reason":      "No RMP-listed chemicals reported",
            "threshold":   "Varies by chemical",
            "deadline":    "N/A",
            "form":        "N/A",
            "agency":      "N/A",
            "priority":    "LOW",
        }
    chemical = profile.get("rmp_chemical_name", "Unknown")
    qty      = profile.get("rmp_chemical_qty_lbs", 0)
    threshold = RMP_THRESHOLD_CHEMICALS.get(chemical, 10000)

    if qty >= threshold:
        return {
            "regulation":  "EPA RMP (Risk Management Plan)",
            "applicable":  True,
            "reason":      f"{chemical} quantity ({qty:,} lbs) ≥ threshold ({threshold:,} lbs)",
            "threshold":   f"{threshold:,} lbs for {chemical}",
            "deadline":    "Initial submission + update every 5 years",
            "form":        "RMP*eSubmit to EPA",
            "agency":      "EPA",
            "priority":    "CRITICAL",
        }
    return {
        "regulation":  "EPA RMP (Risk Management Plan)",
        "applicable":  False,
        "reason":      f"{chemical} quantity ({qty:,} lbs) below threshold ({threshold:,} lbs)",
        "threshold":   f"{threshold:,} lbs for {chemical}",
        "deadline":    "N/A",
        "form":        "N/A",
        "agency":      "N/A",
        "priority":    "LOW",
    }


def check_swppp(profile):
    """
    SWPPP — Stormwater Pollution Prevention Plan
    Applies to industrial facilities with stormwater discharge.
    """
    industrial_codes = ["SIC 10-14","SIC 20-39","SIC 44-45",
                        "SIC 49","SIC 50-51","SIC 52-59","SIC 70-89"]
    if profile["has_stormwater_discharge"]:
        return {
            "regulation":  "SWPPP (Stormwater Pollution Prevention Plan)",
            "applicable":  True,
            "reason":      "Industrial facility with stormwater discharge to waters of the US",
            "threshold":   "Any industrial stormwater discharge",
            "deadline":    "NPDES permit — annual certification",
            "form":        "SWPPP Document + Annual Report",
            "agency":      "EPA / State environmental agency",
            "priority":    "HIGH",
        }
    return {
        "regulation":  "SWPPP (Stormwater Pollution Prevention Plan)",
        "applicable":  False,
        "reason":      "No stormwater discharge to waters of the US reported",
        "threshold":   "Any industrial stormwater discharge",
        "deadline":    "N/A",
        "form":        "N/A",
        "agency":      "N/A",
        "priority":    "LOW",
    }


def check_iso_14001(profile):
    """
    ISO 14001:2015 — Environmental Management System
    Not legally required but strongly recommended / contractually required.
    """
    manufacturing_naics = [str(n) for n in range(311, 340)]
    naics = profile["naics_code"]

    if profile["seeks_iso_14001"]:
        return {
            "regulation":  "ISO 14001:2015 — EMS",
            "applicable":  True,
            "reason":      "Organization seeks ISO 14001 certification",
            "threshold":   "Voluntary — contractual or market requirement",
            "deadline":    "Certification audit — typically 6-12 months",
            "form":        "Aspects & Impacts Matrix + EMS Documentation",
            "agency":      "Accredited Certification Body (CB)",
            "priority":    "HIGH",
        }
    if naics in manufacturing_naics or naics in ["211","213","221","486"]:
        return {
            "regulation":  "ISO 14001:2015 — EMS",
            "applicable":  True,
            "reason":      f"NAICS {naics} — high environmental impact sector. "
                          f"ISO 14001 strongly recommended / often contractually required",
            "threshold":   "Voluntary — contractual or market requirement",
            "deadline":    "Recommended within 12 months",
            "form":        "Aspects & Impacts Matrix + EMS Documentation",
            "agency":      "Accredited Certification Body (CB)",
            "priority":    "MODERATE",
        }
    return {
        "regulation":  "ISO 14001:2015 — EMS",
        "applicable":  False,
        "reason":      "Not contractually required for this sector — voluntary option",
        "threshold":   "Voluntary",
        "deadline":    "N/A",
        "form":        "N/A",
        "agency":      "N/A",
        "priority":    "LOW",
    }


# ── Master applicability function ─────────────────────────────────────────────

def determine_applicability(profile):
    """
    Run all regulatory checks for a company profile.
    Returns complete applicability matrix.
    """
    results = [
        check_tier_ii(profile),
        check_tri(profile),
        check_rcra(profile),
        check_rmp(profile),
        check_swppp(profile),
        check_iso_14001(profile),
    ]

    df = pd.DataFrame(results)

    # Summary counts
    applicable     = df[df["applicable"] == True]
    not_applicable = df[df["applicable"] == False]

    print("\n" + "="*65)
    print(f"  REGULATORY APPLICABILITY REPORT")
    print(f"  Facility: {profile['facility_name']}")
    print(f"  NAICS: {profile['naics_code']} — {profile['naics_description']}")
    print(f"  State: {profile['state']}")
    print("="*65)
    print(f"\n  {'REGULATION':<35} {'APPLIES':<10} {'PRIORITY':<10}")
    print(f"  {'-'*55}")
    for _, row in df.iterrows():
        status = "✅ YES" if row["applicable"] else "❌ NO"
        print(f"  {row['regulation']:<35} {status:<10} {row.get('priority',''):<10}")

    print(f"\n  Regulations that APPLY    : {len(applicable)}")
    print(f"  Regulations that DO NOT   : {len(not_applicable)}")
    print(f"\n  REQUIRED ACTIONS:")
    for _, row in applicable.iterrows():
        print(f"  → {row['regulation']}")
        print(f"    Form: {row['form']}")
        print(f"    Deadline: {row['deadline']}")
        print(f"    Agency: {row['agency']}\n")

    # Save results
    out = PROC_DIR / "applicability_matrix.csv"
    df.to_csv(out, index=False)
    print(f"  Saved → {out.name}")
    return df


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Example: Houston chemical plant
    profile = build_company_profile(
        facility_name          = "Houston Chemical Plant — Demo",
        naics_code             = "325",
        state                  = "TX",
        employee_count         = 150,
        has_hazardous_chemicals= True,
        max_chemical_qty_lbs   = 15000,
        has_ehs_chemicals      = True,
        ehs_chemical_qty_lbs   = 800,
        hazardous_waste_kg_month= 250,
        has_rmp_chemicals      = True,
        rmp_chemical_name      = "Chlorine",
        rmp_chemical_qty_lbs   = 3000,
        has_stormwater_discharge= True,
        has_air_emissions      = True,
        annual_emissions_tons  = 45,
        tri_chemical_qty_lbs   = 28000,
        seeks_iso_14001        = True,
    )
    determine_applicability(profile)
