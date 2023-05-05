def test_env():
    from app.core.config import settings  # pylint: disable=C0415

    assert settings.PROJECT_NAME == "leif"


def test_secret():
    "value from file in folder secret should be loaded"
    from app.core.config import settings  # pylint: disable=C0415

    assert settings.TEST_SECRET == "secret_value"
