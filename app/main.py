# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections import defaultdict
import os

# from dotenv import load_dotenv, find_dotenv
from fastapi import Body, FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
import uvicorn


app = FastAPI(
    title="leif",
    version="1.0",
    description="Search engine",
)


@app.get("/", include_in_schema=False)
def docs_redirect():
    return RedirectResponse(f"/docs")
