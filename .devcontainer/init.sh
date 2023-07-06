pipx install poetry
poetry config virtualenvs.create false && poetry install --with=dev
docker-compose -f docker/docker-local-redis.yml up -d