import re
from typing import Optional
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from models import CheckResult
from .base import BaseChecker


class AmazonChecker(BaseChecker):
    SITE_NAME = "Amazon"
    SEARCH_URL = "https://www.amazon.com/s?k={query}"

    def check(self, search_term: str, max_price: Optional[float] = None,
              date_start: Optional[str] = None, date_end: Optional[str] = None) -> CheckResult:
        url = self.SEARCH_URL.format(query=quote_plus(search_term))
        try:
            resp = self.get(url)
            text = resp.text

            if "captcha" in resp.url.lower() or (
                "robot" in text.lower() and "check" in text.lower()
            ):
                return CheckResult(
                    site=self.SITE_NAME,
                    available=False,
                    url=url,
                    message="Bot check triggered — try opening Amazon in your browser first",
                    error=True,
                )

            soup = BeautifulSoup(text, "lxml")
            results = soup.select('[data-component-type="s-search-result"]')

            for item in results:
                # Skip sponsored / unavailable
                if item.find(string=re.compile(r"Currently unavailable", re.I)):
                    continue
                if item.find(string=re.compile(r"Temporarily out of stock", re.I)):
                    continue

                price_el = item.select_one(".a-price .a-offscreen")
                price = None
                if price_el:
                    try:
                        price = float(
                            price_el.get_text().strip().replace("$", "").replace(",", "")
                        )
                    except ValueError:
                        pass

                if max_price and price and price > max_price:
                    continue

                link = item.select_one("h2 a")
                href = link["href"] if link and link.get("href") else ""
                product_url = (
                    f"https://www.amazon.com{href}" if href.startswith("/") else href or url
                )

                title_el = item.select_one("h2 span")
                title = title_el.get_text(strip=True) if title_el else search_term

                return CheckResult(
                    site=self.SITE_NAME,
                    available=True,
                    url=product_url,
                    price=price,
                    message=title[:80],
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
