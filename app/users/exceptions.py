from app.core.exceptions import DomainException


class EmailAlreadyRegisteredException(DomainException):
    pass


class PasswordNotComplexEnoughException(DomainException):
    pass
