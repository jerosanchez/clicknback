class CashbackPercentageNotValidException(Exception):
    def __init__(self, reason: str):
        super().__init__(f"Cashback percentage is not valid: {reason}")
        self.reason = reason


class MerchantNameAlreadyExistsException(Exception):
    def __init__(self, name: str):
        super().__init__(f"Merchant with name '{name}' already exists.")
        self.name = name
