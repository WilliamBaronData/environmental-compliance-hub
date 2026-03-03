"""
analysis.py
===========
Analysis and KPI functions for Environmental Compliance Hub.

USAGE:
  from analysis import load_facilities, get_kpis
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from schema import COMPLIANCE_WEIGHTS, CONESA_CLASSIFICATION

PROC_DIR = PROJECT_ROOT / "data" / "processed"


def load_facilities():
    path = PROC_DIR / "facilities.csv"
    if not path.exists():
        raise FileNotFoundError("Run python src/epa_data.py first")
    return pd.read_csv(path, low_memory=False)


def load_conesa():
    path = PROC_DIR / "conesa_matrix.csv"
    if not path.exists():
        raise FileNotFoundError("Run python src/impact_matrix.py first")
    return pd.read_csv(path, low_memory=False)


def load_applicability():
    path = PROC_DIR / "applicability_matrix.csv"
    if not path.exists():
        raise FileNotFoundError("Run python src/applicability.py first")
    return pd.read_csv(path, low_memory=False)


def get_kpis(df):
    """Compute executive KPI cards."""
    total_facilities    = len(df)
    compliant           = int((df["compliance_status"] == "Compliant").sum())
    at_risk             = int((df["compliance_status"] == "At Risk").sum())
    non_compliant       = int((df["compliance_status"] == "Non-Compliant").sum())
    avg_score           = round(df["compliance_score"].mean(), 1)
    total_violations    = int(df["violations_3yr"].sum())
    total_penalties     = df["penalties_3yr_usd"].sum()
    iso_certified       = int(df["iso_14001_certified"].sum())
    rmp_facilities      = int(df["has_rmp"].sum()) if "has_rmp" in df.columns else 0
    worst_facility      = df.loc[df["compliance_score"].idxmin(), "facility_name"]
    best_facility       = df.loc[df["compliance_score"].idxmax(), "facility_name"]
    avg_waste_kg        = round(df["waste_kg_month"].mean(), 1)

    return {
        "total_facilities":  total_facilities,
        "compliant":         compliant,
        "at_risk":           at_risk,
        "non_compliant":     non_compliant,
        "avg_score":         avg_score,
        "total_violations":  total_violations,
        "total_penalties":   f"${total_penalties:,.0f}",
        "iso_certified":     iso_certified,
        "rmp_facilities":    rmp_facilities,
        "worst_facility":    worst_facility[:25] if len(worst_facility) > 25 else worst_facility,
        "best_facility":     best_facility[:25]  if len(best_facility) > 25  else best_facility,
        "avg_waste_kg":      avg_waste_kg,
        "compliance_rate":   f"{compliant/total_facilities*100:.1f}%",
    }


def get_compliance_by_naics(df):
    """Compliance score by industry sector."""
    return (
        df.groupby("naics_description")
          .agg(
              facilities      = ("facility_id",       "count"),
              avg_score       = ("compliance_score",   "mean"),
              total_violations= ("violations_3yr",     "sum"),
              total_penalties = ("penalties_3yr_usd",  "sum"),
              non_compliant   = ("compliance_status",
                                 lambda x: (x == "Non-Compliant").sum()),
          )
          .round(2)
          .reset_index()
          .sort_values("avg_score")
    )


def get_compliance_by_city(df):
    """Compliance by city — for map visualization."""
    return (
        df.groupby("city")
          .agg(
              facilities    = ("facility_id",      "count"),
              avg_score     = ("compliance_score",  "mean"),
              violations    = ("violations_3yr",    "sum"),
              penalties     = ("penalties_3yr_usd", "sum"),
              lat           = ("latitude",          "mean"),
              lon           = ("longitude",         "mean"),
          )
          .round(2)
          .reset_index()
          .sort_values("avg_score")
    )


def get_violation_analysis(df):
    """Violation and penalty trends."""
    return (
        df[df["violations_3yr"] > 0]
          .sort_values("violations_3yr", ascending=False)
          .head(20)
          [[
              "facility_name","city","naics_description",
              "violations_3yr","penalties_3yr_usd",
              "compliance_score","compliance_status"
          ]]
    )


def get_compliance_distribution(df):
    """Distribution of compliance scores."""
    bins   = [0, 25, 50, 70, 85, 100]
    labels = ["Critical (0-25)", "Poor (25-50)",
              "At Risk (50-70)", "Good (70-85)", "Excellent (85-100)"]
    df = df.copy()
    df["score_band"] = pd.cut(df["compliance_score"],
                               bins=bins, labels=labels, include_lowest=True)
    return df["score_band"].value_counts().reset_index()


def get_iso_vs_non_iso(df):
    """Compare compliance: ISO 14001 certified vs non-certified."""
    return (
        df.groupby("iso_14001_certified")
          .agg(
              facilities      = ("facility_id",       "count"),
              avg_score       = ("compliance_score",   "mean"),
              avg_violations  = ("violations_3yr",     "mean"),
              avg_penalties   = ("penalties_3yr_usd",  "mean"),
              avg_waste       = ("waste_kg_month",     "mean"),
          )
          .round(2)
          .reset_index()
    )


def get_top_risk_facilities(df, n=10):
    """Top N highest risk facilities."""
    return (
        df.sort_values("compliance_score")
          .head(n)
          [[
              "facility_name","city","naics_description",
              "compliance_score","compliance_status",
              "violations_3yr","penalties_3yr_usd",
              "has_rmp","iso_14001_certified",
              "latitude","longitude"
          ]]
    )


def get_conesa_summary(conesa_df):
    """Summary of Conesa matrix results."""
    return (
        conesa_df.groupby("classification")
                 .agg(count=("aspect_id","count"),
                      avg_score=("conesa_score","mean"))
                 .round(2)
                 .reset_index()
    )


def get_pdca_status(df):
    """
    PDCA compliance status overview.
    Maps regulatory compliance to PDCA phases.
    """
    compliant     = (df["compliance_status"] == "Compliant").sum()
    at_risk       = (df["compliance_status"] == "At Risk").sum()
    non_compliant = (df["compliance_status"] == "Non-Compliant").sum()
    total         = len(df)

    return {
        "PLAN":  {"score": round(compliant/total*100, 1),
                  "status": "Regulatory calendar established",
                  "items":  total},
        "DO":    {"score": round((compliant+at_risk)/total*100, 1),
                  "status": "Active compliance programs",
                  "items":  compliant + at_risk},
        "CHECK": {"score": round(compliant/total*100, 1),
                  "status": "Compliance audits completed",
                  "items":  compliant},
        "ACT":   {"score": round(non_compliant/total*100, 1),
                  "status": "Corrective actions needed",
                  "items":  non_compliant},
    }


if __name__ == "__main__":
    df  = load_facilities()
    kpi = get_kpis(df)
    print("\n  Environmental Compliance KPIs:")
    for k, v in kpi.items():
        print(f"    {k:<25}: {v}")
