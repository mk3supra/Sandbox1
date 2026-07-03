from typing import Optional

from models import CheckResult
from .base import BaseChecker

# SeatGeek's public API endpoint — no auth key required for basic queries.
_API = "https://api.seatgeek.com/2/events"


class SeatGeekChecker(BaseChecker):
    SITE_NAME = "SeatGeek"

    def check(self, search_term: str, max_price: Optional[float] = None,
              date_start: Optional[str] = None, date_end: Optional[str] = None) -> CheckResult:
        search_url = f"https://seatgeek.com/search#?q={search_term.replace(' ', '+')}"
        params: dict = {"q": search_term, "per_page": 20, "sort": "datetime_local.asc"}
        if date_start:
            params["datetime_local.gte"] = date_start
        if date_end:
            params["datetime_local.lte"] = date_end

        try:
            resp = self.get(_API, params=params)
            data = resp.json()

            for event in data.get("events", []):
                stats = event.get("stats", {})
                if not stats.get("listing_count"):
                    continue

                min_price = stats.get("lowest_price")
                if max_price and min_price and min_price > max_price:
                    continue

                title = event.get("title", search_term)
                date = (event.get("datetime_local") or "")[:10]
                venue = event.get("venue", {}).get("name", "")
                event_url = event.get("url", search_url)

                parts = [title]
                if date:
                    parts.append(f"on {date}")
                if venue:
                    parts.append(f"at {venue}")

                return CheckResult(
                    site=self.SITE_NAME,
                    available=True,
                    url=event_url,
                    price=min_price,
                    message=" ".join(parts)[:100],
                )

            return CheckResult(
                site=self.SITE_NAME,
                available=False,
                url=search_url,
                message="No tickets found",
            )
        except Exception as exc:
            return CheckResult(
                site=self.SITE_NAME,
                available=False,
                url=search_url,
                message=str(exc),
                error=True,
            )
