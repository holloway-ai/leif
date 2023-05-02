# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import os
from starlette.testclient import TestClient


def test_docs_redirect():
    from app.main import app

    client = TestClient(app)
    response = client.get("/")
    assert response.history[0].status_code in [302, 307]
    assert response.status_code == 200
    assert response.url == "http://testserver/docs"


def test_api():
    from app.main import app
    from app.core.config import settings

    client = TestClient(app)

    response = client.get(f"{settings.API_V1_STR}/collection/")
    assert response.status_code == 200

    results = response.json()
    for x in results:
        if "name" in x and x["name"] == "joan":
            break
    else:
        assert False, "Cant find 'joan'"
