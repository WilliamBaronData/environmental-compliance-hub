"""
schema.py
=========
Single source of truth for Environmental Compliance Hub.
All regulatory thresholds, ISO 14001 clauses, and column
definitions live here. To update for new regulations or
ISO 14001:2026, only this file needs to change.

REGULATIONS COVERED:
  USA: EPA Tier II, TRI, RCRA, RMP, SWPPP, NEPA/Leopold
  GLOBAL: ISO 14001:2015, Conesa Matrix (180+ countries)
"""

# ── Versioning ────────────────────────────────────────────────────────────────
REGULATORY_VERSIONS = {
    "iso_14001":    "2015",   # Update to "2026" when published
    "tier_ii":      "2024",
    "tri":          "2024",
    "rcra":         "2024",
    "rmp":          "2024",
    "epa_echo":     "2024",
}

# ── Canonical column names ────────────────────────────────────────────────────
CANONICAL_COLS = {
    # Facility identity
    "facility_id":          "string",
    "facility_name":        "string",
    "naics_code":           "string",
    "naics_description":    "string",
    "state":                "string",
    "city":                 "string",
    "zip_code":             "string",
    "latitude":             "float64",
    "longitude":            "float64",
    "employee_count":       "Int64",
    "facility_type":        "string",
    # Chemical inventory
    "chemical_name":        "string",
    "cas_number":           "string",
    "quantity_lbs":         "float64",
    "quantity_kg":          "float64",
    "physical_state":       "string",
    "hazard_type":          "string",
    # Compliance
    "regulation":           "string",
    "applicable":           "bool",
    "threshold_lbs":        "float64",
    "exceeds_threshold":    "bool",
    "compliance_score":     "float64",
    "compliance_status":    "string",
    "deadline":             "string",
    "year":                 "Int64",
    # Environmental aspects
    "aspect_id":            "string",
    "aspect_description":   "string",
    "impact_description":   "string",
    "life_cycle_stage":     "string",
    "aspect_type":          "string",
    "significance":         "string",
    "conesa_score":         "float64",
    "leopold_magnitude":    "float64",
    "leopold_importance":   "float64",
}

# ── EPA Tier II Thresholds ────────────────────────────────────────────────────
TIER_II_THRESHOLDS = {
    "extremely_hazardous":  500,    # lbs — EHS chemicals
    "default":              10000,  # lbs — all other hazardous
    "deadline":             "March 1",
    "reporting_period":     "calendar year",
    "agency":               "SERC / LEPC",
    "form":                 "Tier II Chemical Inventory Report",
}

# ── EPA TRI Thresholds ────────────────────────────────────────────────────────
TRI_THRESHOLDS = {
    "form_r": {
        "manufacturing":    25000,  # lbs — manufactured/processed
        "otherwise":        10000,  # lbs — otherwise used
        "deadline":         "July 1",
        "form":             "Form R",
    },
    "form_a": {
        "manufacturing":    25000,  # lbs
        "otherwise":        10000,  # lbs
        "annual_release":   500,    # lbs — must be below this for Form A
        "deadline":         "July 1",
        "form":             "Form A (Certification Statement)",
    },
    "pbt_chemicals": {
        "threshold":        100,    # lbs — Persistent Bioaccumulative Toxic
        "deadline":         "July 1",
    },
    "dioxin_furans": {
        "threshold":        0.1,    # grams
        "deadline":         "July 1",
    },
}

# ── RCRA Generator Categories ─────────────────────────────────────────────────
RCRA_CATEGORIES = {
    "LQG": {
        "name":             "Large Quantity Generator",
        "threshold_kg":     1000,   # kg/month
        "threshold_lbs":    2200,
        "accumulation_days": 90,
        "requirements":     ["EPA ID", "Manifest", "Biennial Report",
                             "Training", "Contingency Plan"],
    },
    "SQG": {
        "name":             "Small Quantity Generator",
        "threshold_kg_min": 100,
        "threshold_kg_max": 1000,
        "threshold_lbs_min": 220,
        "threshold_lbs_max": 2200,
        "accumulation_days": 270,
        "requirements":     ["EPA ID", "Manifest", "Training"],
    },
    "VSQG": {
        "name":             "Very Small Quantity Generator",
        "threshold_kg":     100,    # kg/month — below this
        "threshold_lbs":    220,
        "accumulation_days": None,  # No time limit
        "requirements":     ["Proper disposal only"],
    },
}

# ── RMP Thresholds (selected chemicals) ──────────────────────────────────────
RMP_THRESHOLD_CHEMICALS = {
    "Chlorine":             2500,   # lbs
    "Ammonia (anhydrous)":  10000,
    "Hydrogen fluoride":    1000,
    "Sulfur dioxide":       5000,
    "Hydrogen chloride":    5000,
    "Ethylene oxide":       10000,
    "Methyl isocyanate":    500,
    "Phosgene":             500,
    "Hydrogen sulfide":     10000,
    "Propane":              10000,
}

# ── NAICS Codes requiring environmental reporting ────────────────────────────
REPORTING_NAICS = {
    "211":  "Oil & Gas Extraction",
    "213":  "Support Activities for Mining",
    "221":  "Utilities",
    "311":  "Food Manufacturing",
    "312":  "Beverage & Tobacco",
    "313":  "Textile Mills",
    "322":  "Paper Manufacturing",
    "324":  "Petroleum & Coal Products",
    "325":  "Chemical Manufacturing",
    "326":  "Plastics & Rubber",
    "327":  "Nonmetallic Mineral Products",
    "331":  "Primary Metal Manufacturing",
    "332":  "Fabricated Metal Products",
    "333":  "Machinery Manufacturing",
    "334":  "Computer & Electronic Products",
    "336":  "Transportation Equipment",
    "339":  "Miscellaneous Manufacturing",
    "486":  "Pipeline Transportation",
    "562":  "Waste Management",
    "622":  "Hospitals",
    "236":  "Construction of Buildings",
    "237":  "Heavy & Civil Engineering Construction",
}

# ── ISO 14001:2015 Clauses ────────────────────────────────────────────────────
ISO_14001_CLAUSES = {
    "4.1":  "Understanding the organization and its context",
    "4.2":  "Understanding needs of interested parties",
    "4.3":  "Determining scope of EMS",
    "4.4":  "Environmental management system",
    "5.1":  "Leadership and commitment",
    "5.2":  "Environmental policy",
    "5.3":  "Roles, responsibilities and authorities",
    "6.1.1":"Actions to address risks and opportunities",
    "6.1.2":"Environmental aspects and impacts",
    "6.1.3":"Compliance obligations",
    "6.1.4":"Planning action",
    "6.2.1":"Environmental objectives",
    "6.2.2":"Planning to achieve objectives",
    "7.1":  "Resources",
    "7.2":  "Competence",
    "7.3":  "Awareness",
    "7.4":  "Communication",
    "7.5":  "Documented information",
    "8.1":  "Operational planning and control",
    "8.2":  "Emergency preparedness and response",
    "9.1":  "Monitoring, measurement, analysis and evaluation",
    "9.2":  "Internal audit",
    "9.3":  "Management review",
    "10.1": "Continual improvement",
    "10.2": "Nonconformity and corrective action",
}

# ── Conesa Matrix — 10 criteria ───────────────────────────────────────────────
CONESA_CRITERIA = {
    "i":  {"name": "Intensity",      "description": "Degree of destruction",          "scale": [1,2,4,8,12]},
    "EX": {"name": "Extension",      "description": "Area of influence",              "scale": [1,2,4,8,12]},
    "MO": {"name": "Moment",         "description": "Time between action and impact", "scale": [1,2,4,8]},
    "PE": {"name": "Persistence",    "description": "Permanence of effect",           "scale": [1,2,4,8]},
    "RV": {"name": "Reversibility",  "description": "Natural recovery capacity",      "scale": [1,2,4,8]},
    "SI": {"name": "Synergy",        "description": "Reinforcement of effects",       "scale": [1,2,4]},
    "AC": {"name": "Accumulation",   "description": "Progressive increase",           "scale": [1,4]},
    "EF": {"name": "Effect",         "description": "Direct or indirect",             "scale": [1,4]},
    "PR": {"name": "Periodicity",    "description": "Frequency of impact",            "scale": [1,2,4]},
    "MC": {"name": "Recoverability", "description": "Recovery by human means",        "scale": [1,2,4,8]},
}

CONESA_CLASSIFICATION = {
    "Compatible":  {"min": 0,  "max": 25, "color": "#10B981"},
    "Moderate":    {"min": 25, "max": 50, "color": "#EAB308"},
    "Severe":      {"min": 50, "max": 75, "color": "#F97316"},
    "Critical":    {"min": 75, "max": 100,"color": "#EF4444"},
}

# ── Leopold Matrix ────────────────────────────────────────────────────────────
LEOPOLD_ACTIONS = [
    "Site clearing", "Excavation", "Construction", "Operation",
    "Transportation", "Waste disposal", "Chemical storage",
    "Water discharge", "Air emissions", "Maintenance",
]

LEOPOLD_FACTORS = [
    "Surface water quality", "Groundwater quality", "Air quality",
    "Soil quality", "Flora diversity", "Fauna diversity",
    "Human health", "Noise levels", "Visual landscape",
    "Community welfare",
]

# ── Life Cycle Stages ─────────────────────────────────────────────────────────
LIFE_CYCLE_STAGES = {
    "RAW_MATERIAL":  "Raw Material Acquisition",
    "DESIGN":        "Design & Development",
    "PRODUCTION":    "Production & Operation",
    "DISTRIBUTION":  "Distribution & Transport",
    "USE":           "Product Use",
    "END_OF_LIFE":   "End of Life & Disposal",
}

# ── PDCA Phases ───────────────────────────────────────────────────────────────
PDCA_PHASES = {
    "PLAN":  {"color": "#3B82F6", "description": "Regulatory calendar + objectives"},
    "DO":    {"color": "#10B981", "description": "Implementation + data entry"},
    "CHECK": {"color": "#F59E0B", "description": "Compliance score + audits"},
    "ACT":   {"color": "#EF4444", "description": "Corrective actions + improvement"},
}

# ── Compliance Score Weights ──────────────────────────────────────────────────
COMPLIANCE_WEIGHTS = {
    "tier_ii":      0.20,
    "tri":          0.15,
    "rcra":         0.20,
    "rmp":          0.15,
    "swppp":        0.10,
    "iso_14001":    0.20,
}
