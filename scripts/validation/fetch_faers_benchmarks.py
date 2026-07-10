#!/usr/bin/env python3
"""
External-validation benchmark fetch — FDA FAERS thyroid adverse-event reporting.

Queries the PUBLIC openFDA drug-event count API for the number of spontaneous
adverse-event reports mentioning thyroid MedDRA preferred terms (PTs) for each
immune checkpoint inhibitor (ICI), plus each drug's total report count, and
derives:
  * thyroid-AE reporting proportion per drug (thyroid reports / all drug reports),
  * hypothyroidism:hyperthyroidism reporting ratio,
  * a whole-database reporting odds ratio (ROR) for hypo- and hyperthyroidism.

These are REAL-WORLD pharmacovigilance data used as an INDEPENDENT, held-out
benchmark for the QSP model's emergent class-ordering and hypo/hyper behaviour.
FAERS is spontaneous reporting (subject to notoriety / Weber-effect / reporting
bias), so it validates RANK ORDER and RATIOS, not absolute incidence.

Output: results/v1/external_faers_benchmarks.json (with query strings + fetch
date; NOT stamped synthetic — this is real FDA data).

Usage:
    python scripts/validation/fetch_faers_benchmarks.py
Optional: set FDA_API_KEY env var for a higher openFDA rate limit.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import date, datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (_ROOT, os.path.join(_ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import v1_common as vc  # noqa: E402

API = "https://api.fda.gov/drug/event.json"
API_KEY = os.environ.get("FDA_API_KEY", "").strip()

# ICI drugs by mechanistic class (generic names as they appear in openfda).
DRUGS = {
    "nivolumab": "PD-1", "pembrolizumab": "PD-1",
    "atezolizumab": "PD-L1", "durvalumab": "PD-L1",
    "ipilimumab": "CTLA-4",
}
# Thyroid MedDRA PTs, grouped for hypo/hyper aggregation.
HYPO_PTS = ["hypothyroidism", "autoimmune thyroiditis",
            "blood thyroid stimulating hormone increased", "immune-mediated hypothyroidism"]
HYPER_PTS = ["hyperthyroidism", "blood thyroid stimulating hormone decreased",
             "thyrotoxicosis"]
OTHER_PTS = ["thyroiditis", "thyroid disorder"]
ALL_PTS = HYPO_PTS + HYPER_PTS + OTHER_PTS


def _get_total(search: str, retries: int = 4) -> int:
    """Return meta.results.total for an openFDA search; 0 if no matches (404).

    `search` must already be openFDA-encoded (quotes as %22, spaces/AND joined
    with '+'); openFDA treats '+' as the token separator, so we must NOT run a
    urlencode over it.
    """
    url = f"{API}?search={search}&limit=1"
    if API_KEY:
        url += f"&api_key={API_KEY}"
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                data = json.load(r)
            return int(data.get("meta", {}).get("results", {}).get("total", 0))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 0  # openFDA returns 404 when zero reports match
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return 0


def _phrase(text: str) -> str:
    """openFDA-encode a phrase: wrap in %22 quotes, spaces -> '+'."""
    return "%22" + text.replace(" ", "+") + "%22"


def _drug_q(drug: str) -> str:
    return "patient.drug.openfda.generic_name:" + _phrase(drug)


def _pt_q(pt: str) -> str:
    return "patient.reaction.reactionmeddrapt:" + _phrase(pt)


def _ror(a: int, drug_total: int, event_total: int, n_db: int) -> dict | None:
    """Whole-database reporting odds ratio with 95% CI (Woolf/log method)."""
    b = drug_total - a
    c = event_total - a
    d = n_db - drug_total - event_total + a
    if min(a, b, c, d) <= 0:
        return None
    import math
    ror = (a * d) / (b * c)
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    lo = math.exp(math.log(ror) - 1.96 * se)
    hi = math.exp(math.log(ror) + 1.96 * se)
    return {"ror": round(ror, 2), "ci_low": round(lo, 2), "ci_high": round(hi, 2)}


def main() -> None:
    cfg = vc.load_config()
    vc.banner("External benchmark fetch - FDA FAERS thyroid adverse events")
    out_dir = vc.output_dir(cfg)

    # Whole-database size and per-event totals (for ROR). Guarded: if these fail,
    # ROR is skipped but reporting proportions still compute.
    n_db = _get_total("receivedate:[19000101+TO+21001231]")
    print(f"  FAERS database size (approx): {n_db:,}")
    event_totals = {}
    for pt in ("hypothyroidism", "hyperthyroidism"):
        event_totals[pt] = _get_total(_pt_q(pt))
        time.sleep(0.3)

    per_drug = {}
    for drug, cls in DRUGS.items():
        total = _get_total(_drug_q(drug))
        time.sleep(0.3)
        by_pt = {}
        for pt in ALL_PTS:
            by_pt[pt] = _get_total(f"{_drug_q(drug)}+AND+{_pt_q(pt)}")
            time.sleep(0.25)
        hypo = sum(by_pt[p] for p in HYPO_PTS)
        hyper = sum(by_pt[p] for p in HYPER_PTS)
        thyroid = sum(by_pt.values())
        rec = {
            "class": cls,
            "total_reports": total,
            "by_pt": by_pt,
            "hypothyroidism_reports": hypo,
            "hyperthyroidism_reports": hyper,
            "thyroid_reports": thyroid,
            "thyroid_reporting_pct": round(100 * thyroid / total, 3) if total else None,
            "hypo_reporting_pct": round(100 * hypo / total, 3) if total else None,
            "hyper_reporting_pct": round(100 * hyper / total, 3) if total else None,
            "hypo_hyper_ratio": round(hypo / hyper, 2) if hyper else None,
            "ror_hypothyroidism": _ror(by_pt["hypothyroidism"], total,
                                       event_totals.get("hypothyroidism", 0), n_db) if n_db else None,
            "ror_hyperthyroidism": _ror(by_pt["hyperthyroidism"], total,
                                        event_totals.get("hyperthyroidism", 0), n_db) if n_db else None,
        }
        per_drug[drug] = rec
        print(f"  {drug:14s} ({cls:11s}) total={total:>7,}  thyroid={thyroid:>6,}  "
              f"hypo:hyper={rec['hypo_hyper_ratio']}  report%={rec['thyroid_reporting_pct']}")

    # Class aggregation (pool member drugs) for rank-ordering comparison.
    by_class = {}
    for cls in ("PD-1", "PD-L1", "CTLA-4"):
        members = [d for d, c in DRUGS.items() if c == cls]
        tot = sum(per_drug[d]["total_reports"] for d in members)
        hypo = sum(per_drug[d]["hypothyroidism_reports"] for d in members)
        hyper = sum(per_drug[d]["hyperthyroidism_reports"] for d in members)
        thy = sum(per_drug[d]["thyroid_reports"] for d in members)
        by_class[cls] = {
            "members": members, "total_reports": tot,
            "thyroid_reporting_pct": round(100 * thy / tot, 3) if tot else None,
            "hypo_reporting_pct": round(100 * hypo / tot, 3) if tot else None,
            "hyper_reporting_pct": round(100 * hyper / tot, 3) if tot else None,
            "hypo_hyper_ratio": round(hypo / hyper, 2) if hyper else None,
        }

    payload = {
        "_provenance": (
            "REAL-WORLD FDA FAERS DATA (openFDA drug-event API), NOT model output. "
            "Spontaneous adverse-event reports; counts are subject to reporting / "
            "notoriety / Weber-effect bias and are disproportionality signals, NOT "
            "incidence. Used as an independent, held-out external benchmark for the "
            "QSP model's emergent thyroid class-ordering and hypo/hyper behaviour "
            "(validate rank order and ratios, not absolute rates). Combination "
            "regimens are not separately isolable in FAERS and are omitted."
        ),
        "source": "openFDA /drug/event.json count API",
        "fetch_date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "api_key_used": bool(API_KEY),
        "faers_db_size": n_db,
        "event_totals_wholedb": event_totals,
        "meddra_pts": {"hypo": HYPO_PTS, "hyper": HYPER_PTS, "other": OTHER_PTS},
        "query_template": (
            'search=patient.drug.openfda.generic_name:"<drug>"'
            '+AND+patient.reaction.reactionmeddrapt:"<pt>" (limit=1, read meta.results.total)'
        ),
        "by_drug": per_drug,
        "by_class": by_class,
    }
    out = out_dir / "external_faers_benchmarks.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\n  Wrote {out}")
    print("  Class thyroid reporting %:",
          {c: v["thyroid_reporting_pct"] for c, v in by_class.items()})


if __name__ == "__main__":
    main()
