from .amazon import AmazonChecker
from .walmart import WalmartChecker
from .bestbuy import BestBuyChecker
from .seatgeek import SeatGeekChecker
from .stubhub import StubHubChecker

PHYSICAL_CHECKERS = {
    "amazon": AmazonChecker,
    "walmart": WalmartChecker,
    "bestbuy": BestBuyChecker,
}

EVENT_CHECKERS = {
    "seatgeek": SeatGeekChecker,
    "stubhub": StubHubChecker,
}
