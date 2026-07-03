import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Union

from checker import EVENT_CHECKERS, PHYSICAL_CHECKERS
from models import CheckResult, EventProduct, PhysicalProduct


def _jitter():
    """Small polite delay between requests to avoid hammering servers."""
    time.sleep(random.uniform(0.5, 2.0))


def check_product(product: PhysicalProduct) -> List[CheckResult]:
    results: List[CheckResult] = []

    def _check(site: str) -> CheckResult:
        _jitter()
        checker_cls = PHYSICAL_CHECKERS.get(site.lower().replace(" ", ""))
        if checker_cls is None:
            return CheckResult(site=site, available=False, url="",
                               message=f"Unknown site: {site}", error=True)
        return checker_cls().check(product.search_term, product.max_price)

    with ThreadPoolExecutor(max_workers=len(product.sites)) as pool:
        futures = {pool.submit(_check, s): s for s in product.sites}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                site = futures[future]
                results.append(CheckResult(site=site, available=False, url="",
                                           message=str(exc), error=True))
    return results


def check_event(event: EventProduct) -> List[CheckResult]:
    results: List[CheckResult] = []

    def _check(site: str) -> CheckResult:
        _jitter()
        checker_cls = EVENT_CHECKERS.get(site.lower().replace(" ", ""))
        if checker_cls is None:
            return CheckResult(site=site, available=False, url="",
                               message=f"Unknown site: {site}", error=True)
        return checker_cls().check(
            event.search_term, event.max_price, event.date_start, event.date_end
        )

    with ThreadPoolExecutor(max_workers=len(event.sites)) as pool:
        futures = {pool.submit(_check, s): s for s in event.sites}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                site = futures[future]
                results.append(CheckResult(site=site, available=False, url="",
                                           message=str(exc), error=True))
    return results


def run_all_checks(products: List[Union[PhysicalProduct, EventProduct]]):
    """Check every product and return a list of (product, [results]) tuples."""
    output = []
    for product in products:
        if isinstance(product, PhysicalProduct):
            results = check_product(product)
        else:
            results = check_event(product)
        output.append((product, results))
    return output
