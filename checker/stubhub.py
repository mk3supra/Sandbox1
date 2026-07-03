import json
import re
from typing import Optional
from urllib.parse import quote_plus

from models import CheckResult
from .base import BaseChecker


class StubHubChecker(BaseChecker):
    SITE_NAME = "StubHub"
    SEARCH_URL = "https://www.stubhub.com/find/s/?q={query}"

    def check(self, search_term: str, max_price: Optional[float] = None,
              date_start: Optional[str] = None, date_end: Optional[str] = None) -> CheckResult:
        url = self.SEARCH_URL.format(query=quote_plus(search_term))
        try:
            resp = self.get(url)
            text = resp.text

            # StubHub is Next.js; product data lives in __NEXT_DATA__
            match = re.search(
                r'<script\s+id="__NEXT_DATA__"\s+type="application/json">\s*(\{.+?\})\s*</script>',
                text,
                re.DOTALL,
            )
            if not match:
                return CheckResult(
                    site=self.SITE_NAME,
                    available=False,
                    url=url,
                    message="Could not parse StubHub page data",
                    error=True,
                )

            data = json.loads(match.group(1))
            page_props = data.get("props", {}).get("pageProps", {})

            # Try multiple known paths for the events list
            events = (
                page_props.get("searchResult", {}).get("events")
                or page_props.get("events")
                or []
            )

            for event in events:
                ticket_count = event.get("ticketCount") or event.get("totalListings", 0)
                if not ticket_count:
                    continue

                price_info = event.get("minPrice") or {}
                min_price = (
                    price_info.get("amount")
                    if isinstance(price_info, dict)
                    else price_info
                )
                if isinstance(min_price, str):
                    try:
                        min_price = float(min_price.replace("$", "").replace(",", ""))
                    except ValueError:
                        min_price = None

                if max_price and min_price and min_price > max_price:
                    continue

                path = event.get("url") or event.get("webURI", "")
                event_url = (
                    f"https://www.stubhub.com{path}"
                    if path and path.startswith("/")
                    else path or url
                )
                name = event.get("name") or event.get("title", search_term)
                raw_date = event.get("eventDate") or event.get("date", "")
                date = raw_date[:10] if raw_date else ""

                parts = [name]
                if date:
                    parts.append(f"on {date}")

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
                url=url,
                message="No tickets found",
            )
        except Exception as exc:
            return CheckResult(
                site=self.SITE_NAME,
                available=False,
                url=url,
                message=str(exc),
                error=True,
            )
