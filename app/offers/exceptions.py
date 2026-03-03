from datetime import date


class InvalidCashbackValueException(Exception):
    def __init__(self, cashback_type: str, value: float, reason: str):
        super().__init__(
            f"Invalid cashback value {value} for type '{cashback_type}': {reason}"
        )
        self.cashback_type = cashback_type
        self.value = value
        self.reason = reason


class InvalidDateRangeException(Exception):
    def __init__(self, start_date: date, end_date: date):
        super().__init__(
            f"End date '{end_date}' must be after or equal to start date"
            f" '{start_date}'."
        )
        self.start_date = start_date
        self.end_date = end_date


class InvalidMonthlyCapException(Exception):
    def __init__(self, value: float):
        super().__init__(f"Monthly cap must be positive. Got: {value}.")
        self.value = value


class MerchantNotActiveException(Exception):
    def __init__(self, merchant_id: str):
        super().__init__(
            f"Cannot create offer for merchant '{merchant_id}'."
            " Merchant is not active."
        )
        self.merchant_id = merchant_id


class ActiveOfferAlreadyExistsException(Exception):
    def __init__(self, merchant_id: str):
        super().__init__(
            f"An active offer already exists for merchant '{merchant_id}'."
            " Deactivate the existing offer before creating a new one."
        )
        self.merchant_id = merchant_id


class PastOfferStartDateException(Exception):
    def __init__(self, start_date: date):
        super().__init__(
            f"Offer start date '{start_date}' is in the past."
            " Start date must be today or a future date."
        )
        self.start_date = start_date
