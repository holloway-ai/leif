# leif

Search engine

---
## Devcontainer 

Just run codespace of devcontainer
Note: Python path in dev environment : /usr/local/py-utils/venvs/poetry/bin/python 

### pytests 

[vscode pytest](https://code.visualstudio.com/docs/python/testing) should work from the box.
You can run pytest 

## Resources
This project has two key dependencies:

| Dependency Name | Documentation                | Description                                                                            |
|-----------------|------------------------------|----------------------------------------------------------------------------------------|
           |
| FastAPI         | https://fastapi.tiangolo.com | FastAPI framework, high performance, easy to learn, fast to code, ready for production |
---

## Run Locally
To run locally in debug mode run (in dev environment):

```
uvicorn app.main:app --reload
```
Open your browser to http://localhost:8000 to view the OpenAPI UI.

![Open API Image](./images/cookiecutter-docs.png)


For an alternate view of the docs navigate to http://localhost:8000/redoc

---