git config --global core.editor "code --wait"
pipx install poetry
poetry config virtualenvs.create false && poetry install --with=dev
