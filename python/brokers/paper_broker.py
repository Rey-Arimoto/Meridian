class PaperBroker:
    def __init__(self, init_cash: float = 1.0):
        self.cash = float(init_cash)
        self.pos = 0.0  # base units

    def equity(self, price: float) -> float:
        return self.cash + self.pos * price

    def rebalance_to_target_weight(self, target_weight: float, price: float):
        eq = self.equity(price)
        if eq <= 0:
            return 0.0

        current_w = (self.pos * price) / eq if eq > 0 else 0.0
        desired_pos_value = eq * target_weight
        desired_units = desired_pos_value / price if price > 0 else 0.0
        trade_units = desired_units - self.pos

        # execute instantly (paper)
        self.cash -= trade_units * price
        self.pos = desired_units

        new_eq = self.equity(price)
        new_w = (self.pos * price) / new_eq if new_eq > 0 else 0.0
        return new_w - current_w
