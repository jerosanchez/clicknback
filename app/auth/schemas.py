from pydantic import BaseModel, EmailStr


class LoginSchemaBase(BaseModel):
    email: EmailStr
    password: str


class Login(LoginSchemaBase):
    pass
