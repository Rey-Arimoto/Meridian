# python/brokers/paper_broker.py
class PaperBroker:
    """
    v0.1 paper execution:
    - instant rebalance to target weight
    - no fees, no slippage, no partial fills
    """

    def __init__(self, init_cash: float = 1.0):
        self.cash = float(init_cash)
        self.pos = 0.0  # base units

    def equity(self, price: float) -> float:
        return self.cash + self.pos * price

    def rebalance_to_target_weight(self, target_weight: float, price: float) -> float:
        """
        Returns delta_weight (new_weight - old_weight)
        """
        eq = self.equity(price)
        if eq <= 0 or price <= 0:
            return 0.0

        old_w = (self.pos * price) / eq if eq > 0 else 0.0

        desired_pos_value = eq * float(target_weight)
        desired_units = desired_pos_value / price
        trade_units = desired_units - self.pos

        # execute instantly (paper)
        self.cash -= trade_units * price
        self.pos = desired_units

        new_eq = self.equity(price)
        new_w = (self.pos * price) / new_eq if new_eq > 0 else 0.0
        return new_w - old_w
