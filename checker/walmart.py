import json
import re
from typing import Optional
from urllib.parse import quote_plus

from models import CheckResult
from .base import BaseChecker


class WalmartChecker(BaseChecker):
    SITE_NAME = "Walmart"
    SEARCH_URL = "https://www.walmart.com/search?q={query}"

    def check(self, search_term: str, max_price: Optional[float] = None,
              date_start: Optional[str] = None, date_end: Optional[str] = None) -> CheckResult:
        url = self.SEARCH_URL.format(query=quote_plus(search_term))
        try:
            resp = self.get(url)
            text = resp.text

            # Walmart bakes search data into __NEXT_DATA__ as JSON
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
                    message="Could not parse Walmart page data",
                    error=True,
                )

            data = json.loads(match.group(1))

            # Navigate the nested response; the schema can shift between deploys
            search_result = (
                data.get("props", {})
                    .get("pageProps", {})
                    .get("initialData", {})
                    .get("searchResult", {})
            )
            stacks = search_result.get("itemStacks", [])
            items = []
            for stack in stacks:
                items.extend(stack.get("items", []))

            for item in items:
                availability = item.get("availabilityStatus", "")
                if availability not in ("IN_STOCK", "AVAILABLE"):
                    continue

                price_info = item.get("priceInfo", {})
                current = price_info.get("currentPrice", {})
                price = current.get("price") or current.get("priceString")
                if isinstance(price, str):
                    try:
                        price = float(price.replace("$", "").replace(",", ""))
                    except ValueError:
                        price = None

                if max_price and isinstance(price, float) and price > max_price:
                    continue

                item_id = item.get("id", "")
                product_url = (
                    f"https://www.walmart.com/ip/{item_id}" if item_id else url
                )
                name = item.get("name", search_term)

                return CheckResult(
                    site=self.SITE_NAME,
                    available=True,
                    url=product_url,
                    price=price if isinstance(price, float) else None,
                    message=name[:80],
                )

            return CheckResult(
                site=self.SITE_NAME,
                available=False,
                url=url,
                message="Not found / out of stock",
            )
        except Exception as exc:
            return CheckResult(
                site=self.SITE_NAME,
                available=False,
                url=url,
                message=str(exc),
                error=True,
            )
