"""
ui/workers.py — Background worker for all job scraping sources.

UnifiedFetchWorker runs all sources in sequence (Remotive → RemoteOK → Indeed → Adzuna).
Each source is independently try/caught so one failure never kills the rest.

Features:
  • Pause / Resume / Stop  (threading.Event + flag)
  • Salary normalised to USD via analysis.salary_normalizer
  • Skills enriched from text via analysis.skills_extractor
  • Deduplication via db.insert_job_safe()
  • Source tag on every inserted row
"""

import json
import os
import threading
from PyQt6.QtCore import QThread, pyqtSignal

try:
    from config.constants import get_project_root
    _STATE_PATH = os.path.join(get_project_root(), "data", "state.json")
except ImportError:
    _STATE_PATH = os.path.join(os.getcwd(), "data", "state.json")


# ── checkpoint helpers ────────────────────────────────────────────────────────

def _save_state(data: dict):
    os.makedirs(os.path.dirname(_STATE_PATH), exist_ok=True)
    with open(_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _clear_state():
    if os.path.exists(_STATE_PATH):
        os.remove(_STATE_PATH)


# ── base worker ───────────────────────────────────────────────────────────────

class _BaseWorker(QThread):
    """Adds pause / resume / stop to any QThread subclass."""
    progress = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._pause_event = threading.Event()
        self._pause_event.set()          # not paused by default
        self._stop_flag   = False

    def pause(self):
        self._pause_event.clear()
        self.progress.emit("⏸  Paused")

    def resume(self):
        self._pause_event.set()
        self.progress.emit("▶  Resumed")

    def stop(self):
        self._stop_flag = True
        self._pause_event.set()          # unblock if currently paused
        self.progress.emit("⏹  Stopping…")

    def _check(self) -> bool:
        """Block while paused. Returns True if the worker should stop."""
        self._pause_event.wait()
        return self._stop_flag


# ═════════════════════════════════════════════════════════════════════════════
#  UNIFIED FETCH WORKER
# ═════════════════════════════════════════════════════════════════════════════

class UnifiedFetchWorker(_BaseWorker):
    """
    Fetches jobs from all available sources in one pass:
      1. Remotive   — remote jobs, public API, no key needed
      2. RemoteOK   — remote jobs, public API, no key needed
      3. Indeed     — onsite/hybrid, HTML scraper, uses role + location
      4. Adzuna     — onsite/hybrid, API, skipped if env keys not set

    Signal: finished(total_count: int, source_counts: dict, errors: list)
    """
    finished = pyqtSignal(int, dict, list)

    def __init__(self, role: str = "", location: str = "", clear_before: bool = True):
        super().__init__()
        self.role         = role.strip()     or "developer"
        self.location     = location.strip() or ""
        self.clear_before = clear_before

    # ── entry point ───────────────────────────────────────────────────────────

    def run(self):
        import os
        import requests
        from datetime import datetime

        from database.db_manager       import DatabaseManager
        from analysis.salary_normalizer import normalize_salary
        from analysis.skills_extractor  import enrich_skills

        db = DatabaseManager()
        if self.clear_before:
            db.clear_jobs()

        counts = {"remotive": 0, "remoteok": 0, "indeed": 0, "adzuna": 0}
        errors: list[str] = []

        # ── shared date helpers ───────────────────────────────────────────────

        def fmt_iso(s: str) -> str:
            try:
                return datetime.fromisoformat(
                    (s or "").replace("Z", "+00:00")
                ).strftime("%Y-%m-%d")
            except Exception:
                return "Not Specified"

        def fmt_epoch(val) -> str:
            if val is None:
                return "Not Specified"
            try:
                if isinstance(val, (int, float)):
                    return datetime.fromtimestamp(val).strftime("%Y-%m-%d")
                s = str(val)[:10]
                import re
                return s if re.match(r"\d{4}-\d{2}-\d{2}", s) else "Not Specified"
            except Exception:
                return "Not Specified"

        def experience(title: str) -> str:
            t = title.lower()
            if any(w in t for w in ("senior", "lead", "principal", "staff")):
                return "3+ years"
            if any(w in t for w in ("junior", "entry", "graduate", "intern")):
                return "0-2 years"
            return "Not Specified"

        # ─────────────────────────────────────────────────────────────────────
        # SOURCE 1 — Remotive
        # ─────────────────────────────────────────────────────────────────────
        try:
            self.progress.emit("🌐  Fetching Remotive…")
            resp = requests.get(
                "https://remotive.com/api/remote-jobs",
                params={"limit": 50}, timeout=15,
            )
            resp.raise_for_status()

            for j in resp.json().get("jobs") or []:
                if self._check():
                    self.finished.emit(sum(counts.values()), counts, ["Stopped by user"])
                    return

                title   = (j.get("title")                          or "N/A").strip()
                company = (j.get("company_name")                   or "N/A").strip()
                loc     = (j.get("candidate_required_location")    or "Remote").strip()
                desc    = j.get("description") or ""
                salary  = normalize_salary(j.get("salary") or 0, "USD")
                tags    = j.get("tags") or []
                skills  = enrich_skills(title, desc,
                                        ", ".join(str(t) for t in tags[:10]) if tags else "")
                job_type = (j.get("job_type") or "full_time").replace("_", " ").title()
                posted   = fmt_iso(j.get("publication_date"))

                db.insert_job_safe(
                    (title, company, loc, salary, experience(title), skills, job_type, posted),
                    source="remotive",
                )
                counts["remotive"] += 1

            self.progress.emit(f"✅  Remotive: {counts['remotive']} jobs")

        except Exception as e:
            errors.append(f"Remotive: {e}")
            self.progress.emit(f"⚠  Remotive failed: {e}")

        # ─────────────────────────────────────────────────────────────────────
        # SOURCE 2 — RemoteOK
        # ─────────────────────────────────────────────────────────────────────
        try:
            self.progress.emit("🌐  Fetching RemoteOK…")
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp    = requests.get("https://remoteok.com/api", headers=headers, timeout=30)
            resp.raise_for_status()
            data     = resp.json()
            jobs_raw = data[1:501] if isinstance(data, list) and len(data) > 1 else []

            for j in jobs_raw:
                if not isinstance(j, dict):
                    continue
                if self._check():
                    self.finished.emit(sum(counts.values()), counts, ["Stopped by user"])
                    return

                title   = (j.get("position") or "N/A").strip()
                company = (j.get("company")  or "N/A").strip()
                loc     = (j.get("location") or "Remote").strip()
                desc    = j.get("description") or ""

                try:
                    sal_min = int(float(j.get("salary_min") or 0))
                    sal_max = int(float(j.get("salary_max") or 0))
                except Exception:
                    sal_min = sal_max = 0
                salary = normalize_salary(sal_max if sal_max > 0 else sal_min, "USD")

                tags   = j.get("tags") or []
                skills = enrich_skills(title, desc,
                                       ", ".join(str(t) for t in tags[:12]) if tags else "")
                posted = fmt_epoch(j.get("epoch") or j.get("date"))

                db.insert_job_safe(
                    (title, company, loc, salary, experience(title), skills, "Remote", posted),
                    source="remoteok",
                )
                counts["remoteok"] += 1

                if counts["remoteok"] % 100 == 0:
                    self.progress.emit(f"🌐  RemoteOK: {counts['remoteok']} jobs…")

            self.progress.emit(f"✅  RemoteOK: {counts['remoteok']} jobs")

        except Exception as e:
            errors.append(f"RemoteOK: {e}")
            self.progress.emit(f"⚠  RemoteOK failed: {e}")

        # ─────────────────────────────────────────────────────────────────────
        # SOURCE 3 — JSearch via RapidAPI
        #   Replaces direct Indeed HTML scraping (which returns 403 because
        #   Indeed blocks all automated requests).
        #   JSearch aggregates Indeed, LinkedIn, Glassdoor and more through
        #   a legitimate API — no scraping, no blocking.
        #
        #   Free tier: 200 requests / month  (plenty for daily use)
        #   Get key:   rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
        #   Set env:   JSEARCH_API_KEY=your_rapidapi_key
        #
        #   Falls back gracefully if key is not set — zero errors shown.
        # ─────────────────────────────────────────────────────────────────────
        jsearch_key = os.environ.get("JSEARCH_API_KEY")

        if jsearch_key:
            try:
                self.progress.emit(
                    f"🌐  Fetching JSearch (Indeed/LinkedIn): '{self.role}'…"
                )
                query = self.role
                if self.location:
                    query += f" in {self.location}"

                resp = requests.get(
                    "https://jsearch.p.rapidapi.com/search",
                    headers={
                        "X-RapidAPI-Key":  jsearch_key,
                        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                    },
                    params={
                        "query":           query,
                        "page":            "1",
                        "num_pages":       "3",   # up to 30 results
                        "date_posted":     "all",
                    },
                    timeout=20,
                )
                resp.raise_for_status()

                for j in resp.json().get("data") or []:
                    if self._check():
                        self.finished.emit(sum(counts.values()), counts, ["Stopped by user"])
                        return

                    title   = (j.get("job_title")             or "N/A").strip()
                    company = (j.get("employer_name")         or "N/A").strip()
                    loc     = (j.get("job_city") or j.get("job_country") or "N/A").strip()
                    desc    = (j.get("job_description")       or "")[:600]
                    is_remote = bool(j.get("job_is_remote"))
                    job_type  = "Remote" if is_remote else (
                        (j.get("job_employment_type") or "Full-time").replace("_", " ").title()
                    )

                    try:
                        sal_min = int(float(j.get("job_min_salary") or 0))
                        sal_max = int(float(j.get("job_max_salary") or 0))
                    except Exception:
                        sal_min = sal_max = 0
                    sal_raw = sal_max if sal_max > 0 else sal_min
                    salary  = normalize_salary(sal_raw, "USD")

                    skills  = enrich_skills(title, desc,
                                            ", ".join(j.get("job_required_skills") or []))
                    posted  = fmt_iso(j.get("job_posted_at_datetime_utc") or "")

                    db.insert_job_safe(
                        (title, company, loc, salary, experience(title), skills, job_type, posted),
                        source="indeed",
                    )
                    counts["indeed"] += 1

                self.progress.emit(f"✅  JSearch (Indeed/LinkedIn): {counts['indeed']} jobs")

            except Exception as e:
                errors.append(f"JSearch: {e}")
                self.progress.emit(f"⚠  JSearch failed: {e}")
        else:
            # No key — skip silently, don't count as an error
            self.progress.emit(
                "ℹ  JSearch skipped — set JSEARCH_API_KEY for Indeed/LinkedIn jobs  "
                "(free at rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)"
            )

        # ─────────────────────────────────────────────────────────────────────
        # SOURCE 4 — Adzuna  (silently skipped if no API key)
        # ─────────────────────────────────────────────────────────────────────
        app_id  = os.environ.get("ADZUNA_APP_ID")
        app_key = os.environ.get("ADZUNA_APP_KEY")

        if app_id and app_key:
            try:
                country  = os.environ.get("ADZUNA_COUNTRY", "gb").lower()
                currency = "GBP" if country == "gb" else "USD"
                self.progress.emit("🌐  Fetching Adzuna…")

                resp = requests.get(
                    f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
                    params={
                        "app_id": app_id, "app_key": app_key,
                        "results_per_page": 50,
                        "what": self.role,
                        **({"where": self.location} if self.location else {}),
                        "content-type": "application/json",
                    },
                    timeout=15,
                )
                resp.raise_for_status()

                for r in resp.json().get("results") or []:
                    if self._check():
                        self.finished.emit(sum(counts.values()), counts, ["Stopped by user"])
                        return

                    title   = (r.get("title") or "N/A").strip()
                    company = ((r.get("company") or {}).get("display_name") or "N/A").strip()
                    loc_obj = r.get("location") or {}
                    loc     = (loc_obj.get("display_name") if isinstance(loc_obj, dict)
                               else str(loc_obj)).strip() or "Onsite"

                    try:
                        raw_sal = int(r.get("salary_max") or r.get("salary_min") or 0)
                    except Exception:
                        raw_sal = 0
                    salary = normalize_salary(raw_sal, currency)

                    desc     = (r.get("description") or "")[:600]
                    skills   = enrich_skills(title, desc, "")
                    contract = (
                        ((r.get("contract_type") or "") + " " + (r.get("contract_time") or "")).strip()
                        or "Full-time"
                    )
                    posted = fmt_iso(r.get("created"))

                    db.insert_job_safe(
                        (title, company, loc, salary, experience(title), skills, contract, posted),
                        source="adzuna",
                    )
                    counts["adzuna"] += 1

                self.progress.emit(f"✅  Adzuna: {counts['adzuna']} jobs")

            except Exception as e:
                errors.append(f"Adzuna: {e}")
                self.progress.emit(f"⚠  Adzuna failed: {e}")
        else:
            self.progress.emit("ℹ  Adzuna skipped — API key not set")

        # ── done ──────────────────────────────────────────────────────────────
        _clear_state()
        total = sum(counts.values())
        self.progress.emit(f"🎉  Done — {total} total jobs loaded")
        self.finished.emit(total, counts, errors)