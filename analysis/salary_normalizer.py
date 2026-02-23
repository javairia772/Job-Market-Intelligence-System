"""
analysis/salary_normalizer.py
==============================
Converts any salary representation from any scraper into a single
normalised integer: USD per year.

Handles:
  • Plain integers / floats       →  95000
  • "k" shorthand                 →  "80k"         → 80,000
  • Range strings                 →  "$80k–$120k"  → 100,000  (midpoint)
  • Currency prefixes             →  "£65,000"     → USD equivalent
  • Hourly / monthly amounts      →  "$45/hr"      → annualised
  • Zero / missing / garbage      →  0

Exchange rates are static approximations suitable for a market-intelligence
dashboard. Update as needed.
"""

import re

# ── FX rates to USD ───────────────────────────────────────────────────────────
_FX: dict[str, float] = {
    "USD": 1.00, "$":  1.00,
    "GBP": 1.27, "£":  1.27,
    "EUR": 1.08, "€":  1.08,
    "CAD": 0.74,
    "AUD": 0.65,
    "INR": 0.012,
    "PKR": 0.0036,
}


def _detect_currency(text: str) -> float:
    upper = text.upper()
    for sym, rate in _FX.items():
        if sym.upper() in upper:
            return rate
    return 1.0   # assume USD


def _extract_numbers(text: str) -> list[float]:
    return [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))]


def _annualise(value: float, text: str) -> float:
    t = text.lower()
    if any(w in t for w in ("/hr", "/hour", "hourly", "per hour")):
        return value * 40 * 52
    if any(w in t for w in ("/mo", "/month", "monthly", "per month")):
        return value * 12
    return value


def normalize_salary(raw, source_currency: str = "USD") -> int:
    """
    Convert any salary value to an annual USD integer.

    Parameters
    ----------
    raw             : str | int | float | None — raw value from any scraper
    source_currency : str — ISO code or symbol of the source currency

    Returns
    -------
    int — annual salary in USD, or 0 if unparseable / missing.
    """
    if raw is None:
        return 0

    # ── already numeric (RemoteOK, Adzuna) ───────────────────────────────────
    if isinstance(raw, (int, float)):
        value = float(raw)
        if value <= 0:
            return 0
        fx = _FX.get(source_currency.upper(), 1.0)
        if value < 500:                          # looks hourly — annualise
            value = value * 40 * 52
        return int(round(value * fx))

    # ── string (Remotive, Indeed) ─────────────────────────────────────────────
    text = str(raw).strip()
    if not text or text.lower() in ("not specified", "n/a", "none", ""):
        return 0

    # expand "80k" → "80000" before extracting numbers
    text_k = re.sub(
        r"(\d+(?:\.\d+)?)\s*k",
        lambda m: str(float(m.group(1)) * 1000),
        text,
        flags=re.IGNORECASE,
    )

    fx      = _detect_currency(text)
    if not any(sym.upper() in text.upper() for sym in _FX):
        fx = _FX.get(source_currency.upper(), 1.0)

    numbers = _extract_numbers(text_k)
    if not numbers:
        return 0

    value = numbers[0] if len(numbers) == 1 else (numbers[0] + numbers[-1]) / 2
    value = _annualise(value, text)

    if value < 1_000 or value > 5_000_000:      # sanity cap
        return 0

    return int(round(value * fx))