# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

# from dotenv import load_dotenv, find_dotenv
from fastapi import Body, FastAPI

# from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from app.api.api_v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def docs_redirect():
    return RedirectResponse("/docs")
