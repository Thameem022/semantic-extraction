"""
Comparison report: System-extracted candidates vs Golden Set (manual).
Produces a human-readable text report and a detailed CSV.
"""

import json
import os
import re
import pandas as pd
from difflib import SequenceMatcher
from pathlib import Path

# ── Paths (relative to repo root) ────────────────────────────────────────────
ROOT           = Path(__file__).resolve().parent.parent
CANDIDATES_DIR = ROOT / "downloads/candidates"
GOLDEN_XLSX    = ROOT / "data/Golden_Set_Policy_Data_Extraction.xlsx"
REPORT_TXT     = ROOT / "reports/accuracy_report.txt"
REPORT_CSV     = ROOT / "reports/field_comparison.csv"
CURRENT_YEAR   = 2026

os.makedirs(ROOT / "reports", exist_ok=True)

# ── Field mapping: (JSON_section, JSON_key) → Excel column label ─────────────
FIELD_MAP = [
    ("GeneralInformation", "Applicant",                          "Applicant"),
    ("GeneralInformation", "Address_Street",                     "Address - Street"),
    ("GeneralInformation", "Address_City",                       "Address - City"),
    ("GeneralInformation", "Address_State",                      "Address - State"),
    ("GeneralInformation", "Address_ZipCode",                    "Address - Zip Code"),
    ("GeneralInformation", "ApplicantsWebsite",                  "Applicant's Website"),
    ("GeneralInformation", "NAICSCode",                          "NAICS Code"),
    ("GeneralInformation", "DateOfFormation",                    "Date of Formation"),
    ("GeneralInformation", "NatureOfOperations",                 "Nature of Operations"),
    ("GeneralInformation", "Contact_Name",                       "Contact - Name"),
    ("GeneralInformation", "Contact_Title",                      "Contact - Title"),
    ("GeneralInformation", "Contact_Telephone",                  "Contact - Telephone"),
    ("GeneralInformation", "Contact_Email",                      "Contact - Email"),
    ("GeneralInformation", "RiskMgmtContact_Name",               "Risk Mgmt Contact - Name"),
    ("GeneralInformation", "RiskMgmtContact_Title",              "Risk Mgmt Contact - Title"),
    ("GeneralInformation", "RiskMgmtContact_Telephone",          "Risk Mgmt Contact - Telephone"),
    ("GeneralInformation", "RiskMgmtContact_Email",              "Risk Mgmt Contact - Email"),
    ("GeneralInformation", "TaxStatus",                          "Tax Status"),
    ("GeneralInformation", "OrganizationalStructure",            "Organizational Structure"),
    ("GeneralInformation", "TotalNumberOfLocations",             "Total Number of Locations"),
    ("GeneralInformation", "TotalNumberOfEmployees",             "Total Number of Employees"),
    ("GeneralInformation", "Employees_US",                       "Employees - U.S."),
    ("GeneralInformation", "Employees_California",               "Employees - California"),
    ("GeneralInformation", "Employees_Canada",                   "Employees - Canada"),
    ("GeneralInformation", "Employees_OutsideUSandCAN",          "Employees - Outside U.S. & CAN"),
    ("GeneralInformation", "CountriesOfOperationOutsideUS",      "Countries of Operation Outside U.S."),
    ("GeneralInformation", "RequestedEffectiveDate",             "Requested Effective Date"),
    ("CoverageDetails",    "LimitRequested",                     "EPL - Limit Requested"),
    ("CoverageDetails",    "RetentionRequested",                 "EPL - Retention Requested"),
    ("CoverageDetails",    "SharedLimit",                        "EPL - Shared Limit"),
    ("CoverageDetails",    "DutyToDefend",                       "EPL - Duty to Defend"),
    ("CoverageDetails",    "CurrentLimit",                       "EPL - Current Limit"),
    ("CoverageDetails",    "CurrentRetention",                   "EPL - Current Retention"),
    ("CoverageDetails",    "CurrentPremium",                     "EPL - Current Premium"),
    ("CoverageDetails",    "CurrentCarrier",                     "EPL - Current Carrier"),
    ("RiskAssessment",     "NoticeOfClaimOrPotentialClaim",      "Notice of Claim (Past 18 Mo)"),
    ("EmployeeCategory",   "FullTimeEmployees_CurrentYearTotal", "FT Employees - Current Year Total"),
    ("EmployeeCategory",   "FullTimeEmployees_CurrentYearCA",    "FT Employees - Current Year CA"),
    ("EmployeeCategory",   "FullTimeEmployees_PriorYearTotal",   "FT Employees - Prior Year Total"),
    ("EmployeeCategory",   "FullTimeEmployees_PriorYearCA",      "FT Employees - Prior Year CA"),
    ("EmployeeCategory",   "PartTimeEmployees_CurrentYearTotal", "PT Employees - Current Year Total"),
    ("EmployeeCategory",   "PartTimeEmployees_PriorYearTotal",   "PT Employees - Prior Year Total"),
    ("EmployeeCategory",   "IndependentContractors_CurrentYearTotal", "Independent Contractors"),
    ("EmployeeCategory",   "Volunteers_CurrentYearTotal",        "Volunteers"),
    ("EmployeeCategory",   "Top3StatesByEmployeeCount_State1",   "Top State 1"),
    ("EmployeeCategory",   "Top3StatesByEmployeeCount_State2",   "Top State 2"),
    ("EmployeeCategory",   "Top3StatesByEmployeeCount_State3",   "Top State 3"),
    ("EmployeeCategory",   "SalaryRanges_GreaterThan125k",       "Salary >= $125K (%)"),
    ("EmployeeCategory",   "SalaryRanges_LessThan125k",          "Salary < $125K (%)"),
    ("EPLISpecificQuestions", "WorkforceReduction_Impacted",          "Q1: >50 emp or 5%+ impacted (terminations)?"),
    ("EPLISpecificQuestions", "ConsultedOutsideCounsel",              "Q2: Outside counsel re: workforce reduction?"),
    ("EPLISpecificQuestions", "ReviewedExemptNonExemptClassifications","Q3: Exempt/nonexempt review (12 mo)?"),
    ("EPLISpecificQuestions", "CompletedWageAndHourAudit",            "Q4: Wage & hour audit (12 mo)?"),
    ("EPLISpecificQuestions", "EmploymentDisputeLitigationOver10k",   "Q5: Employment dispute >$10K (12 mo)?"),
    ("EPLISpecificQuestions", "EEOCOrSimilarProceeding",              "Q6: EEOC or similar (3 yrs)?"),
    ("EPLISpecificQuestions", "CrisisExpenseCoverage",                "Q7: Crisis Expense coverage?"),
    ("EPLISpecificQuestions", "WorkplaceViolenceExpenseCoverage",     "Q8: Workplace Violence Expense coverage?"),
    ("EPLISpecificQuestions", "WageAndHourDefenseExpensesCoverage",   "Q9: Wage & Hour Defense Expenses coverage?"),
    ("EPLISpecificQuestions", "AdditionalDefenseExpenseLimitCoverage","Q10: Additional Defense Expense Limit?"),
]

DATE_FIELDS  = {"Date of Formation"}
MONEY_FIELDS = {
    "EPL - Limit Requested", "EPL - Retention Requested",
    "EPL - Current Limit",   "EPL - Current Retention", "EPL - Current Premium",
}
# Fields where fuzzy/OCR-tolerance matching applies
FUZZY_FIELDS = {
    "Address - Street", "Address - City", "Address - State", "Address - Zip Code",
    "Applicant's Website", "Contact - Email", "Risk Mgmt Contact - Email",
}
# Fields where prefix/substring match is enough (system may return partial value)
PREFIX_MATCH_FIELDS = {
    "Applicant", "Nature of Operations",
    "Contact - Name", "Risk Mgmt Contact - Name",
    "Contact - Title", "Risk Mgmt Contact - Title",
}
FUZZY_THRESHOLD = 0.88

# ── Load Golden Set ───────────────────────────────────────────────────────────
raw = pd.read_excel(GOLDEN_XLSX, header=[0, 1])
raw.columns = [
    b.strip() if (str(b) != "nan" and not str(b).startswith("Unnamed")) else a.strip()
    for a, b in raw.columns
]
golden = raw.copy()
golden["_filename"] = golden["PDF Filename"].astype(str).str.strip()

# ── Load Candidates ───────────────────────────────────────────────────────────
def load_candidates():
    results = {}
    for f in CANDIDATES_DIR.glob("*.json"):
        stem     = f.name
        pdf_name = re.sub(r"^[0-9a-f\-]+__", "", stem).replace(".candidates.json", "").strip()
        with open(f) as fh:
            data = json.load(fh)
        results[pdf_name] = data
    return results

candidates = load_candidates()

# ── Filename normalisation (robust: drop extension(s), alphanum tokens) ───────
def fname_tokens(s: str) -> set:
    s = str(s).lower()
    s = re.sub(r"(\.pdf)+$", "", s, flags=re.I)   # strip one or more .pdf/.PDF
    s = re.sub(r"[^a-z0-9]+", " ", s)             # replace non-alphanum with space
    return set(s.split())

def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)

def find_candidate(golden_filename: str, candidates: dict):
    gt = fname_tokens(golden_filename)
    best_name, best_data, best_score = None, None, 0.0
    for cname, data in candidates.items():
        ct    = fname_tokens(cname)
        score = jaccard(gt, ct)
        if score > best_score:
            best_score, best_name, best_data = score, cname, data
    if best_score >= 0.65:
        return best_name, best_data
    return None, None

# ── Value normalisers ─────────────────────────────────────────────────────────
def is_empty(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and pd.isna(v):
        return True
    s = str(v).strip()
    return s in ("", "nan", "none", "null")

def norm_bool(s: str) -> str | None:
    if s in ("yes", "true",  "1"): return "yes"
    if s in ("no",  "false", "0"): return "no"
    return None

def norm_numeric(s: str) -> str | None:
    """Strip trailing .0 from numeric strings so '46.0' == '46'."""
    try:
        f = float(s)
        if f == int(f):
            return str(int(f))
        return str(f)
    except ValueError:
        return None

def norm_date_to_year(s: str) -> str:
    """Return a 4-digit year string from various date representations."""
    s = s.strip()
    # "25 years" / "25 years ago" / "est. 25 years"
    m = re.search(r"(\d{1,3})\s*years?", s, re.I)
    if m:
        return str(CURRENT_YEAR - int(m.group(1)))
    # Extract 4-digit year (1900-2099)
    m = re.search(r"\b(19\d{2}|20\d{2})\b", s)
    if m:
        return m.group(1)
    # 2-digit year that's standalone (e.g. "97" → 1997)
    m = re.match(r"^(\d{2})$", s)
    if m:
        yr = int(m.group(1))
        return str(1900 + yr if yr > 25 else 2000 + yr)
    return s.lower()

def norm_money(s: str) -> str:
    """Normalise currency: remove spaces after $, strip .00 suffix, strip commas."""
    s = re.sub(r"\$\s+", "$", s)
    # Strip trailing .00 (only when followed by end)
    s = re.sub(r"\.00\b", "", s)
    return s

def norm_general(s: str) -> str:
    s = re.sub(r"\s+", " ", s).lower().strip()
    # Strip annotation suffixes like "(sic)", "(SIC)", "(sic code)"
    s = re.sub(r"\s*\(\s*sic[^)]*\)\s*$", "", s, flags=re.I).strip()
    return s

def fuzzy_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def normalize_value(raw, field_label: str) -> str | None:
    if is_empty(raw):
        return None
    if isinstance(raw, bool):
        return "yes" if raw else "no"
    s = str(raw).strip()
    if is_empty(s):
        return None

    # Boolean-like strings
    b = norm_bool(s.lower())
    if b:
        return b

    if field_label in DATE_FIELDS:
        return norm_date_to_year(s)

    if field_label in MONEY_FIELDS:
        s = norm_money(s)
        return norm_general(s)

    # Numeric: strip trailing .0 so '46.0' == '46', also treat 0.0 as '0'
    n = norm_numeric(s)
    if n is not None:
        # After numeric normalization, re-check bool equivalence (0→no, 1→yes)
        b2 = norm_bool(n)
        if b2:
            return b2
        return n

    return norm_general(s)

# ── Compare two normalised values ─────────────────────────────────────────────
def compare(sys_raw, gold_raw, field_label: str) -> str:
    """
    Returns: CORRECT | MISMATCH | MISSING | NOT_ON_FORM | SKIP

    Matching tiers (in order):
      1. Exact match after normalisation
      2. Prefix/substring: for name/description fields, if one value starts
         with the other (system may return base name without DBA or title suffix)
      3. Fuzzy ratio ≥ threshold: for address/email fields to handle OCR typos
    """
    sv = normalize_value(sys_raw,  field_label)
    gv = normalize_value(gold_raw, field_label)

    if gv is None and sv is None:
        return "NOT_ON_FORM"
    if gv is None:
        return "SKIP"
    if sv is None:
        return "MISSING"

    # Tier 1 — exact
    if sv == gv:
        return "CORRECT"

    # Tier 2 — prefix / substring (for name-like and description fields)
    if field_label in PREFIX_MATCH_FIELDS:
        # Accept if either is a leading substring of the other (min 4 chars)
        shorter, longer = (sv, gv) if len(sv) <= len(gv) else (gv, sv)
        if len(shorter) >= 4 and longer.startswith(shorter):
            return "CORRECT"
        # Also accept if expected name words are all contained in got
        # (handles "april nelson" inside "april nelson exec vp")
        gv_words = set(gv.split())
        sv_words = set(sv.split())
        if gv_words and gv_words.issubset(sv_words):
            return "CORRECT"

    # Tier 3 — fuzzy (for address / email fields — OCR/typo tolerance)
    if field_label in FUZZY_FIELDS:
        if fuzzy_ratio(sv, gv) >= FUZZY_THRESHOLD:
            return "CORRECT"

    return "MISMATCH"

# ── One-to-one matching: build all (candidate, golden) Jaccard scores ─────────
golden_rows = list(golden.iterrows())
candidate_items = list(candidates.items())

# Score every pair
pairs = []
for cname, cdata in candidate_items:
    ct = fname_tokens(cname)
    for idx, (_, grow) in enumerate(golden_rows):
        gt    = fname_tokens(grow["_filename"])
        score = jaccard(ct, gt)
        pairs.append((score, cname, idx, cdata, grow))

pairs.sort(key=lambda x: -x[0])   # best scores first

matched_candidate_names = set()
matched_golden_indices  = set()
assignments = []   # (cname, cdata, grow, gold_fname)

for score, cname, gidx, cdata, grow in pairs:
    if score < 0.65:
        break
    if cname in matched_candidate_names or gidx in matched_golden_indices:
        continue
    matched_candidate_names.add(cname)
    matched_golden_indices.add(gidx)
    assignments.append((cname, cdata, grow, grow["_filename"]))

no_golden = [cname for cname, _ in candidate_items
             if cname not in matched_candidate_names]
unmatched_golden = [grow["_filename"] for idx, (_, grow) in enumerate(golden_rows)
                    if idx not in matched_golden_indices]

# ── Run comparison ─────────────────────────────────────────────────────────────
rows = []

for cname, cdata, gold_row, gold_fname in assignments:
    for section, key, label in FIELD_MAP:
        sys_val  = (cdata.get(section) or {}).get(key)
        gold_val = gold_row.get(label)
        result   = compare(sys_val, gold_val, label)
        rows.append({
            "Document":      gold_fname,
            "CandidateFile": cname,
            "Field":         label,
            "Section":       section,
            "Golden":        gold_val,
            "System":        sys_val,
            "Result":        result,
        })

df = pd.DataFrame(rows)
df.to_csv(REPORT_CSV, index=False)

# ── Build per-field summary ───────────────────────────────────────────────────
total_candidates = len(candidates)
total_golden     = len(golden)
matched_count    = len(matched_candidate_names)

SCORED = {"CORRECT", "MISMATCH", "MISSING"}

summary = []
seen = set()
for _, _, label in FIELD_MAP:
    if label in seen:
        continue
    seen.add(label)
    sub        = df[df["Field"] == label]
    scored     = sub[sub["Result"].isin(SCORED)]
    correct    = (scored["Result"] == "CORRECT").sum()
    mismatch   = (scored["Result"] == "MISMATCH").sum()
    missing    = (scored["Result"] == "MISSING").sum()
    not_on     = (sub["Result"] == "NOT_ON_FORM").sum()
    n_scored   = len(scored)
    accuracy   = round(correct / n_scored * 100, 1) if n_scored else None
    summary.append({
        "Field":       label,
        "# Scored":    n_scored,
        "Correct":     correct,
        "Mismatch":    mismatch,
        "Missing":     missing,
        "Not on Form": not_on,
        "Accuracy %":  accuracy,
    })

summary_df = pd.DataFrame(summary)

# ── Write report ──────────────────────────────────────────────────────────────
def pct(n, d):
    return f"{round(n/d*100,1)}%" if d else "N/A"

with open(REPORT_TXT, "w") as out:
    W = 72

    def line(c="─"): out.write(c * W + "\n")
    def heading(t):
        line("═"); out.write(f"  {t}\n"); line("═"); out.write("\n")
    def subheading(t):
        line(); out.write(f"  {t}\n"); line(); out.write("\n")

    heading("SEMANTIC EXTRACTION — ACCURACY REPORT")

    out.write(f"  Total candidate files (system output) : {total_candidates}\n")
    out.write(f"  Total documents in Golden Set         : {total_golden}\n")
    out.write(f"  Matched (candidate ↔ golden)          : {matched_count}\n")
    out.write("\n")

    if no_golden:
        out.write(f"  Candidates with NO golden entry ({len(no_golden)}) — not scored:\n")
        for n in no_golden:
            out.write(f"    • {n}\n")
        out.write("\n")

    if unmatched_golden:
        out.write(f"  Golden rows with NO candidate match ({len(unmatched_golden)}):\n")
        for n in unmatched_golden:
            out.write(f"    • {n}\n")
        out.write("\n")

    # ── Overall & section summary ──────────────────────────────────────────
    subheading("ACCURACY BY SECTION")

    section_order = [
        "GeneralInformation", "CoverageDetails",
        "RiskAssessment", "EmployeeCategory", "EPLISpecificQuestions",
    ]
    section_labels = {
        "GeneralInformation":    "General Information",
        "CoverageDetails":       "Coverage Details",
        "RiskAssessment":        "Risk Assessment",
        "EmployeeCategory":      "Employee Category",
        "EPLISpecificQuestions": "EPLI Specific Questions",
    }
    field_to_section = {label: sec for sec, key, label in FIELD_MAP}

    for sec in section_order:
        sub  = df[(df["Section"] == sec) & df["Result"].isin(SCORED)]
        c    = (sub["Result"] == "CORRECT").sum()
        t    = len(sub)
        notf = (df[df["Section"] == sec]["Result"] == "NOT_ON_FORM").sum()
        out.write(f"  {section_labels[sec]:<35}  {c}/{t} ({pct(c,t)})  "
                  f"[{notf} field(s) correctly absent]\n")
    out.write("\n")

    evaled  = df[df["Result"].isin(SCORED)]
    ov_corr = (evaled["Result"] == "CORRECT").sum()
    ov_tot  = len(evaled)
    out.write(f"  ► OVERALL  {ov_corr}/{ov_tot} ({pct(ov_corr, ov_tot)})\n\n")

    # ── Per-field detail ───────────────────────────────────────────────────
    subheading("PER-FIELD ACCURACY  (scored = golden had a value)")

    for _, row in summary_df.iterrows():
        n   = int(row["# Scored"])
        c   = int(row["Correct"])
        mm  = int(row["Mismatch"])
        ms  = int(row["Missing"])
        nf  = int(row["Not on Form"])
        acc = row["Accuracy %"]
        acc_str = f"{acc}%" if acc is not None else "—"

        if n == 0 and nf == 0:
            out.write(f"  {row['Field']:<50}  [no data in golden — skipped]\n")
            continue
        if n == 0:
            out.write(f"  {row['Field']:<50}  [field absent on all forms ({nf} docs)]\n")
            continue

        out.write(f"  {row['Field']:<50}  {c}/{n} ({acc_str})")
        if nf:
            out.write(f"  + {nf} correctly absent")
        out.write("\n")

        if mm > 0:
            bad = df[(df["Field"] == row["Field"]) & (df["Result"] == "MISMATCH")]
            for _, br in bad.iterrows():
                doc   = Path(str(br["Document"])).stem[:40]
                sv    = normalize_value(br["System"], row["Field"]) or "(blank)"
                gv    = normalize_value(br["Golden"], row["Field"]) or "(blank)"
                out.write(f"      └─ MISMATCH  \"{doc}\"\n"
                          f"                   got:      {sv!r}\n"
                          f"                   expected: {gv!r}\n")

        if ms > 0:
            bad   = df[(df["Field"] == row["Field"]) & (df["Result"] == "MISSING")]
            names = [Path(str(r["Document"])).stem[:40] for _, r in bad.iterrows()]
            out.write(f"      └─ MISSING in {ms} doc(s): {', '.join(names)}\n")

    out.write("\n")
    line("═")
    out.write(f"  OVERALL ACCURACY : {ov_corr}/{ov_tot} fields correct  "
              f"({pct(ov_corr, ov_tot)})\n")
    line("═")
    out.write(f"\n  Detailed row-level comparison → {REPORT_CSV}\n")

print(f"Report  → {REPORT_TXT}")
print(f"CSV     → {REPORT_CSV}")
