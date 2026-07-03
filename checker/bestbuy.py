from typing import Optional
from urllib.parse import quote_plus

from models import CheckResult
from .base import BaseChecker

# Best Buy exposes an internal search JSON API used by their own frontend.
# It doesn't require auth and returns structured availability data.
_SEARCH_API = (
    "https://www.bestbuy.com/api/1.0/product/search"
    "?q={query}&format=json&pageSize=10"
)
_SEARCH_PAGE = "https://www.bestbuy.com/site/searchpage.jsp?st={query}"


class BestBuyChecker(BaseChecker):
    SITE_NAME = "Best Buy"

    def check(self, search_term: str, max_price: Optional[float] = None,
              date_start: Optional[str] = None, date_end: Optional[str] = None) -> CheckResult:
        encoded = quote_plus(search_term)
        api_url = _SEARCH_API.format(query=encoded)
        page_url = _SEARCH_PAGE.format(query=encoded)

        try:
            resp = self.get(api_url, headers={"Accept": "application/json"})
            data = resp.json()

            products = data.get("products", [])
            for product in products:
                # "orderable" values: "Available", "SoldOut", "ComingSoon", etc.
                if product.get("orderable") != "Available":
                    continue

                price = product.get("salePrice") or product.get("regularPrice")
                if max_price and price and price > max_price:
                    continue

                path = product.get("url", "")
                product_url = (
                    f"https://www.bestbuy.com{path}" if path.startswith("/") else page_url
                )
                name = product.get("name", search_term)

                return CheckResult(
                    site=self.SITE_NAME,
                    available=True,
                    url=product_url,
                    price=price,
                    message=name[:80],
                )

            return CheckResult(
                site=self.SITE_NAME,
                available=False,
                url=page_url,
                message="Not found / out of stock",
            )
        except Exception as exc:
            return CheckResult(
                site=self.SITE_NAME,
                available=False,
                url=page_url,
                message=str(exc),
                error=True,
            )
