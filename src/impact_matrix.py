"""
impact_matrix.py
================
Environmental Aspects & Impacts Assessment.

Implements two methodologies:
  1. Conesa Matrix (1997) — ISO 14001 standard, 180+ countries
     I = ± [3i + 2EX + MO + PE + RV + SI + AC + EF + PR + MC]

  2. Leopold Matrix (1971) — US federal standard / NEPA
     Magnitude (-10 to +10) × Importance (1 to 10)

Both integrated with Life Cycle Assessment (6 stages)
per ISO 14001:2015 Clause 8.1

USAGE:
  python src/impact_matrix.py
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from schema import (CONESA_CRITERIA, CONESA_CLASSIFICATION,
                    LEOPOLD_ACTIONS, LEOPOLD_FACTORS,
                    LIFE_CYCLE_STAGES, ISO_14001_CLAUSES)

PROC_DIR = PROJECT_ROOT / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)


# ── Conesa Matrix ─────────────────────────────────────────────────────────────

def calculate_conesa(i, EX, MO, PE, RV, SI, AC, EF, PR, MC, nature="+"):
    """
    Calculate Conesa Importance Index.
    I = ± [3i + 2EX + MO + PE + RV + SI + AC + EF + PR + MC]

    nature: "+" = positive impact, "-" = negative impact

    Returns: importance score and classification
    """
    score = (3*i + 2*EX + MO + PE + RV + SI + AC + EF + PR + MC)
    signed = score if nature == "+" else -score

    # Classify
    classification = "Compatible"
    for label, limits in CONESA_CLASSIFICATION.items():
        if limits["min"] <= score < limits["max"]:
            classification = label
            break
    if score >= 75:
        classification = "Critical"

    return {
        "conesa_score":       round(score, 1),
        "conesa_signed":      round(signed, 1),
        "classification":     classification,
        "color":              CONESA_CLASSIFICATION[classification]["color"],
        "significant":        score >= 25,
    }


def build_conesa_matrix(aspects):
    """
    Build complete Conesa matrix from list of aspects.

    Each aspect dict must contain:
      - aspect_id, aspect_description, impact_description
      - life_cycle_stage, aspect_type (Direct/Indirect)
      - nature (+/-), i, EX, MO, PE, RV, SI, AC, EF, PR, MC
    """
    records = []
    for a in aspects:
        result = calculate_conesa(
            i   = a["i"],
            EX  = a["EX"],
            MO  = a["MO"],
            PE  = a["PE"],
            RV  = a["RV"],
            SI  = a["SI"],
            AC  = a["AC"],
            EF  = a["EF"],
            PR  = a["PR"],
            MC  = a["MC"],
            nature = a.get("nature", "-"),
        )
        record = {
            "aspect_id":          a["aspect_id"],
            "aspect_description": a["aspect_description"],
            "impact_description": a["impact_description"],
            "life_cycle_stage":   LIFE_CYCLE_STAGES.get(a["life_cycle_stage"],
                                                         a["life_cycle_stage"]),
            "aspect_type":        a.get("aspect_type", "Direct"),
            "nature":             a.get("nature", "-"),
            "i_intensity":        a["i"],
            "EX_extension":       a["EX"],
            "MO_moment":          a["MO"],
            "PE_persistence":     a["PE"],
            "RV_reversibility":   a["RV"],
            "SI_synergy":         a["SI"],
            "AC_accumulation":    a["AC"],
            "EF_effect":          a["EF"],
            "PR_periodicity":     a["PR"],
            "MC_recoverability":  a["MC"],
            **result,
        }
        records.append(record)

    df = pd.DataFrame(records)
    return df


# ── Leopold Matrix ────────────────────────────────────────────────────────────

def build_leopold_matrix(facility_name="Demo Facility"):
    """
    Build Leopold Matrix with random realistic values.
    In production: user inputs magnitude and importance per cell.

    Magnitude: -10 (severe negative) to +10 (highly positive)
    Importance: 1 (low) to 10 (high)
    """
    import numpy as np
    rng = np.random.default_rng(42)

    records = []
    for action in LEOPOLD_ACTIONS:
        for factor in LEOPOLD_FACTORS:
            # Most cells are blank (no interaction)
            has_interaction = rng.random() > 0.6
            if has_interaction:
                magnitude  = int(rng.choice([-8,-6,-4,-3,-2,-1,1,2,3]))
                importance = int(rng.integers(1, 10))
                records.append({
                    "action":      action,
                    "factor":      factor,
                    "magnitude":   magnitude,
                    "importance":  importance,
                    "score":       magnitude * importance,
                    "significant": abs(magnitude * importance) >= 20,
                })
            else:
                records.append({
                    "action":      action,
                    "factor":      factor,
                    "magnitude":   0,
                    "importance":  0,
                    "score":       0,
                    "significant": False,
                })

    df = pd.DataFrame(records)
    pivot = df.pivot_table(
        index="action", columns="factor",
        values="score", aggfunc="sum"
    ).fillna(0)

    return df, pivot


# ── Life Cycle Assessment Integration ────────────────────────────────────────

def build_lifecycle_matrix(conesa_df):
    """
    Aggregate Conesa scores by life cycle stage.
    Shows which stages have the highest environmental impact.
    """
    if conesa_df.empty:
        return pd.DataFrame()

    lifecycle = (
        conesa_df.groupby("life_cycle_stage")
        .agg(
            aspects_count  = ("aspect_id",     "count"),
            avg_score      = ("conesa_score",   "mean"),
            max_score      = ("conesa_score",   "max"),
            significant    = ("significant",    "sum"),
            critical_count = ("classification", lambda x: (x == "Critical").sum()),
            severe_count   = ("classification", lambda x: (x == "Severe").sum()),
        )
        .round(2)
        .reset_index()
        .sort_values("avg_score", ascending=False)
    )
    return lifecycle


# ── Demo data ─────────────────────────────────────────────────────────────────

def generate_demo_aspects():
    """
    Generate realistic aspects for a Houston chemical facility.
    Based on typical ISO 14001 implementation for NAICS 325.
    """
    return [
        # Production / Operation stage
        {
            "aspect_id": "A001", "nature": "-",
            "aspect_description": "Chemical emissions to air (VOCs)",
            "impact_description": "Air quality degradation — human health",
            "life_cycle_stage": "PRODUCTION", "aspect_type": "Direct",
            "i":8,"EX":4,"MO":4,"PE":4,"RV":4,"SI":4,"AC":4,"EF":4,"PR":4,"MC":4,
        },
        {
            "aspect_id": "A002", "nature": "-",
            "aspect_description": "Wastewater discharge",
            "impact_description": "Surface water contamination",
            "life_cycle_stage": "PRODUCTION", "aspect_type": "Direct",
            "i":4,"EX":4,"MO":2,"PE":4,"RV":2,"SI":2,"AC":4,"EF":4,"PR":4,"MC":2,
        },
        {
            "aspect_id": "A003", "nature": "-",
            "aspect_description": "Hazardous waste generation",
            "impact_description": "Soil and groundwater contamination",
            "life_cycle_stage": "PRODUCTION", "aspect_type": "Direct",
            "i":4,"EX":2,"MO":2,"PE":8,"RV":4,"SI":2,"AC":4,"EF":4,"PR":2,"MC":4,
        },
        {
            "aspect_id": "A004", "nature": "-",
            "aspect_description": "Energy consumption — electricity",
            "impact_description": "Greenhouse gas emissions — climate change",
            "life_cycle_stage": "PRODUCTION", "aspect_type": "Indirect",
            "i":2,"EX":8,"MO":2,"PE":8,"RV":1,"SI":4,"AC":4,"EF":1,"PR":4,"MC":1,
        },
        {
            "aspect_id": "A005", "nature": "-",
            "aspect_description": "Water consumption",
            "impact_description": "Depletion of water resources",
            "life_cycle_stage": "PRODUCTION", "aspect_type": "Direct",
            "i":2,"EX":4,"MO":1,"PE":4,"RV":2,"SI":2,"AC":4,"EF":1,"PR":4,"MC":2,
        },
        # Raw material acquisition
        {
            "aspect_id": "A006", "nature": "-",
            "aspect_description": "Raw material extraction",
            "impact_description": "Habitat disruption — resource depletion",
            "life_cycle_stage": "RAW_MATERIAL", "aspect_type": "Indirect",
            "i":4,"EX":8,"MO":1,"PE":8,"RV":4,"SI":2,"AC":4,"EF":1,"PR":2,"MC":4,
        },
        {
            "aspect_id": "A007", "nature": "-",
            "aspect_description": "Transportation of raw materials",
            "impact_description": "Air emissions — traffic accidents risk",
            "life_cycle_stage": "RAW_MATERIAL", "aspect_type": "Indirect",
            "i":2,"EX":4,"MO":1,"PE":2,"RV":2,"SI":2,"AC":4,"EF":4,"PR":4,"MC":2,
        },
        # Distribution
        {
            "aspect_id": "A008", "nature": "-",
            "aspect_description": "Product transportation — trucks/rail",
            "impact_description": "Air emissions — spill risk",
            "life_cycle_stage": "DISTRIBUTION", "aspect_type": "Indirect",
            "i":4,"EX":4,"MO":1,"PE":2,"RV":2,"SI":1,"AC":4,"EF":4,"PR":4,"MC":2,
        },
        # End of life
        {
            "aspect_id": "A009", "nature": "-",
            "aspect_description": "Product disposal — chemical waste",
            "impact_description": "Soil and water contamination at disposal site",
            "life_cycle_stage": "END_OF_LIFE", "aspect_type": "Indirect",
            "i":4,"EX":4,"MO":2,"PE":8,"RV":2,"SI":2,"AC":4,"EF":4,"PR":2,"MC":4,
        },
        # Positive impact
        {
            "aspect_id": "A010", "nature": "+",
            "aspect_description": "Waste recycling program",
            "impact_description": "Reduction of landfill waste — resource recovery",
            "life_cycle_stage": "PRODUCTION", "aspect_type": "Direct",
            "i":4,"EX":4,"MO":1,"PE":4,"RV":4,"SI":2,"AC":4,"EF":4,"PR":4,"MC":4,
        },
    ]


if __name__ == "__main__":
    print("=" * 65)
    print("  Environmental Impact Assessment")
    print("  Conesa Matrix + Leopold Matrix + Life Cycle Analysis")
    print("=" * 65)

    # Conesa Matrix
    print("\n  [1/3] Building Conesa Matrix...")
    aspects    = generate_demo_aspects()
    conesa_df  = build_conesa_matrix(aspects)

    out_conesa = PROC_DIR / "conesa_matrix.csv"
    conesa_df.to_csv(out_conesa, index=False)

    print(f"\n  Conesa Results ({len(conesa_df)} aspects):")
    print(f"  {'ID':<6} {'Aspect':<35} {'Score':<8} {'Classification':<12} {'Significant'}")
    print(f"  {'-'*75}")
    for _, row in conesa_df.iterrows():
        sig = "✅" if row["significant"] else "—"
        print(f"  {row['aspect_id']:<6} {row['aspect_description'][:33]:<35} "
              f"{row['conesa_score']:<8} {row['classification']:<12} {sig}")

    dist = conesa_df["classification"].value_counts().to_dict()
    print(f"\n  Distribution: {dist}")
    print(f"  Significant aspects: {conesa_df['significant'].sum()}/{len(conesa_df)}")

    # Life Cycle
    print("\n  [2/3] Life Cycle Analysis...")
    lifecycle = build_lifecycle_matrix(conesa_df)
    print(f"\n  {'Life Cycle Stage':<35} {'Aspects':<8} {'Avg Score':<10} {'Significant'}")
    print(f"  {'-'*65}")
    for _, row in lifecycle.iterrows():
        print(f"  {row['life_cycle_stage']:<35} {int(row['aspects_count']):<8} "
              f"{row['avg_score']:<10} {int(row['significant'])}")

    # Leopold Matrix
    print("\n  [3/3] Building Leopold Matrix...")
    leopold_df, pivot = build_leopold_matrix()
    out_leopold = PROC_DIR / "leopold_matrix.csv"
    pivot.to_csv(out_leopold)
    sig_count = leopold_df[leopold_df["significant"]].shape[0]
    print(f"  {len(LEOPOLD_ACTIONS)} actions × {len(LEOPOLD_FACTORS)} factors")
    print(f"  Significant interactions: {sig_count}")

    print(f"\n  Saved → {out_conesa.name}")
    print(f"  Saved → {out_leopold.name}")
    print("\n  Assessment complete!")
