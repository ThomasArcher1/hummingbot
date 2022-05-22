from hummingbot.core.event.events import BuyOrderCompletedEvent, SellOrderCompletedEvent
from hummingbot.script.script_base import ScriptBase
from decimal import Decimal

"""
This script will adjust spreads after buy or sell order is filled respectively.
"""

s_decimal_1 = Decimal("1")

# Enter value to be used if buy or sell order is filled
new_spread = Decimal("0.0001")

class AdjustSpreadsAfterFilledOrder(ScriptBase):

    band_upper_bound_pct = Decimal("0.03")
    band_lower_bound_pct = Decimal("0.03")

    def __init__(self):
        super().__init__()
        # Declaration of variables used by the script
        self.original_bid_spread = None
        self.original_ask_spread = None
        self.upper_band = None
        self.lower_band = None
        self.current_mid_price = None

    def on_tick(self):

        # At the script start, the values of the original configuration bid and ask spread is stored for later use
        if self.original_bid_spread is None or self.original_ask_spread is None:
            self.original_bid_spread = self.pmm_parameters.bid_spread
            self.original_ask_spread = self.pmm_parameters.ask_spread

        # At script start, store values of upper & lower band, and current mid-price
        if self.upper_band is None or self.lower_band is None:
            upper_bound = self.mid_price * (s_decimal_1 + self.band_upper_bound_pct)
            lower_bound = self.mid_price * (s_decimal_1 - self.band_lower_bound_pct)
            self.upper_band = upper_bound
            self.lower_band = lower_bound
            self.current_mid_price = self.mid_price

        # Check whether mid-price has reached either upper or lower bands
        if self.mid_price >= self.upper_band:
            self.pmm_parameters.buy_levels = 0
            self.notify("Price is rising. 2% Upper Bound Reached!")
            self.notify("Please STOP bot, BUY Asset, & START again.\n")
        else:
            self.pmm_parameters.buy_levels = self.pmm_parameters.order_levels

        if self.mid_price <= self.lower_band:
            self.pmm_parameters.sell_levels = 0
            self.notify("Price is falling. 2% Lower Bound Reached!")
            self.notify("Please STOP bot, SELL Asset, & START again.\n")
        else:
            self.pmm_parameters.sell_levels = self.pmm_parameters.order_levels

        return

    def on_buy_order_completed(self, event: BuyOrderCompletedEvent):
        # 1a. Bid filled order for downtrend movement
        if self.original_ask_spread == self.pmm_parameters.ask_spread and self.original_bid_spread == self.pmm_parameters.bid_spread:
            self.pmm_parameters.ask_spread = new_spread
            self.pmm_parameters.buy_levels = 0  # no buy order is issued while waiting to re-balance
            self.notify("Asset Re-balancing in Progress...\n")

        # 2b. Re-balancing of ask filled order few seconds ago
        elif self.pmm_parameters.bid_spread == new_spread and self.pmm_parameters.ask_spread == self.original_ask_spread:
            self.pmm_parameters.bid_spread = self.original_bid_spread
            self.pmm_parameters.sell_levels = 1  # to resume issuing 1 sell order after re-balancing
            self.notify("Asset Re-balancing Completed\n")

        return

    def on_sell_order_completed(self, event: SellOrderCompletedEvent):
        # 2a. Ask filled order for uptrend movement
        if self.original_ask_spread == self.pmm_parameters.ask_spread and self.original_bid_spread == self.pmm_parameters.bid_spread:
            self.pmm_parameters.bid_spread = new_spread
            self.pmm_parameters.sell_levels = 0  # no sell order is issued while waiting to re-balance
            self.notify("Asset Re-balancing in Progress...\n")

        # 1b. Re-balancing of bid filled order few seconds ago
        elif self.pmm_parameters.ask_spread == new_spread and self.pmm_parameters.bid_spread == self.original_bid_spread:
            self.pmm_parameters.ask_spread = self.original_ask_spread
            self.pmm_parameters.buy_levels = 1  # to resume issuing 1 buy order after re-balancing
            self.notify("Asset Re-balancing Completed\n")

        return

    def on_status(self) -> str:
        # Show the current values when using the `status` command
        return f"\n" \
               f"upper bound = {self.upper_band} \n" \
               f"mid-price = {self.current_mid_price} \n" \
               f"lower bound = {self.lower_band}"
