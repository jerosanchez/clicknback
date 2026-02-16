from fastapi import FastAPI

from app.users import api as users_api

app = FastAPI()

app.include_router(users_api.router)
