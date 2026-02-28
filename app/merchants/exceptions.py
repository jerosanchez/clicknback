class CashbackPercentageNotValidException(Exception):
    def __init__(self, reason: str):
        super().__init__(f"Cashback percentage is not valid: {reason}")
        self.reason = reason


class MerchantNameAlreadyExistsException(Exception):
    def __init__(self, name: str):
        super().__init__(f"Merchant with name '{name}' already exists.")
        self.name = name


class MerchantNotFoundException(Exception):
    def __init__(self, merchant_id: str):
        super().__init__(f"Merchant with ID '{merchant_id}' does not exist.")
        self.merchant_id = merchant_id
