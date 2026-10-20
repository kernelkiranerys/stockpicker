import requests
from datetime import datetime, timezone
from django.conf import settings


def fetch_indicators(series_ids):
    api_key = settings.FRED_API_KEY
    if not api_key:
        return []

    results = []
    for series_id in series_ids:
        try:
            resp = requests.get(
                f"https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": series_id,
                    "api_key": api_key,
                    "file_type": "json",
                    "limit": 1,
                    "sort_order": "desc",
                },
                timeout=10,
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            observations = data.get("observations", [])
            if not observations:
                continue
            obs = observations[0]
            value_str = obs.get("value", "")
            try:
                value = float(value_str)
            except (ValueError, TypeError):
                value = None
            date_str = obs.get("date", "")
            try:
                from datetime import date as date_cls
                obs_date = date_cls.fromisoformat(date_str)
            except Exception:
                obs_date = datetime.now(timezone.utc).date()

            results.append({
                "name": series_id,
                "value": value,
                "date": obs_date,
                "raw": obs,
            })
        except Exception:
            continue

    return results