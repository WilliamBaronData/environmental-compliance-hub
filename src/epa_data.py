"""
epa_data.py
===========
EPA Data Integration Module.

Downloads real facility data from:
  - EPA ECHO (Enforcement and Compliance History Online)
  - EPA TRI (Toxic Release Inventory)
  - Synthetic fallback if API unavailable

USAGE:
  python src/epa_data.py
"""

import sys
import time
import requests
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from schema import REPORTING_NAICS, CANONICAL_COLS

RAW_DIR  = PROJECT_ROOT / "data" / "raw"
PROC_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)

EPA_ECHO_URL = "https://echo.epa.gov/rest/services/CWA_REST_Services/get_facilities"
EPA_TRI_URL  = "https://data.epa.gov/efservice/tri_facility/state_abbr/TX/JSON"


# ── EPA ECHO ──────────────────────────────────────────────────────────────────

def fetch_echo_facilities(state="TX", naics_prefix="325", limit=100):
    """
    Fetch facility compliance data from EPA ECHO API.
    Returns facilities with violation history in Texas.
    """
    print(f"  Fetching EPA ECHO facilities — State: {state}, NAICS: {naics_prefix}...")
    try:
        params = {
            "output":       "JSON",
            "p_st":         state,
            "p_ncs":        naics_prefix,
            "p_act":        "Y",
            "responseset":  limit,
        }
        resp = requests.get(EPA_ECHO_URL, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            facilities = data.get("Results", {}).get("Facilities", [])
            if facilities:
                df = pd.DataFrame(facilities)
                print(f"  ✅ EPA ECHO: {len(df)} facilities retrieved")
                return df
    except Exception as e:
        print(f"  ⚠️  EPA ECHO unavailable: {e}")
    return None


# ── Synthetic EPA Data ────────────────────────────────────────────────────────

def generate_synthetic_facilities(n=50, state="TX"):
    """
    Generate realistic synthetic EPA facility data.
    Used as fallback when EPA API is unavailable.
    Modeled after actual Houston Ship Channel facilities.
    """
    rng = np.random.default_rng(42)

    facility_types = [
        "Chemical Manufacturing", "Petroleum Refinery",
        "Petrochemical Plant", "Terminal/Storage",
        "Plastics Manufacturing", "Industrial Gas",
        "Pharmaceutical Manufacturing", "Food Processing",
        "Metal Fabrication", "Power Generation",
    ]

    naics_options = list(REPORTING_NAICS.keys())

    houston_coords = {
        "lat_center": 29.7604, "lon_center": -95.3698,
        "lat_std":    0.25,    "lon_std":    0.30,
    }

    cities = ["Houston","Baytown","Deer Park","Pasadena",
              "La Porte","Texas City","Galveston","Beaumont"]

    facilities = []
    for i in range(n):
        naics    = rng.choice(naics_options)
        fac_type = rng.choice(facility_types)
        city     = rng.choice(cities)
        employees = int(rng.integers(10, 2000))

        # Violation history — industrial facilities have realistic rates
        violations_3yr  = int(rng.negative_binomial(2, 0.4))
        penalties_3yr   = float(rng.exponential(15000)) if violations_3yr > 0 else 0
        inspections_3yr = int(rng.integers(0, 8))

        # Chemical quantities
        chem_qty_lbs    = float(rng.exponential(20000))
        waste_kg_month  = float(rng.exponential(300))
        tri_qty_lbs     = float(rng.exponential(30000)) if naics in [str(n) for n in range(311,340)] else 0

        # Compliance score — lower if more violations
        base_score = 100 - (violations_3yr * 12) - rng.uniform(0, 15)
        comp_score = max(10, min(100, base_score))

        facilities.append({
            "facility_id":          f"TX{i+1:04d}",
            "facility_name":        f"{city} {fac_type} {i+1:03d}",
            "facility_type":        fac_type,
            "naics_code":           naics,
            "naics_description":    REPORTING_NAICS.get(naics, "Other"),
            "state":                state,
            "city":                 city,
            "zip_code":             f"7{rng.integers(7000,7999):04d}",
            "latitude":             round(float(rng.normal(
                                        houston_coords["lat_center"],
                                        houston_coords["lat_std"])), 4),
            "longitude":            round(float(rng.normal(
                                        houston_coords["lon_center"],
                                        houston_coords["lon_std"])), 4),
            "employee_count":       employees,
            "violations_3yr":       violations_3yr,
            "penalties_3yr_usd":    round(penalties_3yr, 2),
            "inspections_3yr":      inspections_3yr,
            "chemical_qty_lbs":     round(chem_qty_lbs, 1),
            "waste_kg_month":       round(waste_kg_month, 1),
            "tri_qty_lbs":          round(tri_qty_lbs, 1),
            "has_rmp":              bool(rng.choice([True, False], p=[0.3, 0.7])),
            "has_swppp":            bool(rng.choice([True, False], p=[0.6, 0.4])),
            "iso_14001_certified":  bool(rng.choice([True, False], p=[0.25, 0.75])),
            "compliance_score":     round(comp_score, 1),
            "compliance_status":    "Compliant" if comp_score >= 70 else
                                    "At Risk" if comp_score >= 40 else "Non-Compliant",
            "last_inspection_year": int(rng.integers(2021, 2025)),
            "year":                 2024,
        })

    df = pd.DataFrame(facilities)
    print(f"  ✅ Synthetic: {len(df)} facilities generated")
    return df


def load_facilities(force_synthetic=False):
    """
    Load facility data — real EPA ECHO or synthetic fallback.
    """
    print("\n" + "="*58)
    print("  EPA Facility Data Pipeline")
    print("="*58)

    # Try real EPA data first
    if not force_synthetic:
        df = fetch_echo_facilities()
        if df is not None and len(df) > 0:
            out = PROC_DIR / "facilities_echo.csv"
            df.to_csv(out, index=False)
            print(f"  Saved → {out.name}")
            return df

    # Synthetic fallback
    print("  Using synthetic data (EPA API unavailable)")
    df = generate_synthetic_facilities(n=75)

    out = PROC_DIR / "facilities.csv"
    df.to_csv(out, index=False)

    # Summary
    print(f"\n  Facilities loaded    : {len(df)}")
    print(f"  Cities covered       : {df['city'].nunique()}")
    print(f"  NAICS sectors        : {df['naics_code'].nunique()}")
    print(f"  Avg compliance score : {df['compliance_score'].mean():.1f}")
    print(f"  Non-compliant        : {(df['compliance_status']=='Non-Compliant').sum()}")
    print(f"  Total violations     : {df['violations_3yr'].sum()}")
    print(f"  Total penalties      : ${df['penalties_3yr_usd'].sum():,.0f}")
    print(f"  ISO 14001 certified  : {df['iso_14001_certified'].sum()} facilities")
    print(f"\n  Saved → {out.name}")
    return df


if __name__ == "__main__":
    df = load_facilities()
