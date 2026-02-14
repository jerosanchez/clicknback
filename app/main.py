from fastapi import FastAPI

from app.api import users as users_api

app = FastAPI()

app.include_router(users_api.router)
