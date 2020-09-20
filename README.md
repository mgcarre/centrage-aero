[![pipeline status](https://gitlab.com/yannick.teresiak/flaskapp/badges/master/pipeline.svg)](https://gitlab.com/yannick.teresiak/flaskapp/-/commits/master)
[![coverage report](https://gitlab.com/yannick.teresiak/flaskapp/badges/master/coverage.svg)](https://gitlab.com/yannick.teresiak/flaskapp/-/commits/master)

# Recipe for multi-container solution with nginx and gunicorn

## doesn't work on Cloud Run so far - nginx not needed there anyway

docker-compose -f docker-compose.prod.yaml -f docker-compose.gcp.yaml up -d --build

# Single container with gunicorn for Cloud Run

docker build -f services/web/Dockerfile.prod services/web
docker tag 5fa49f708b68 yayadock/prepavol_web
docker tag 5fa49f708b68 eu.gcr.io/able-cogency-278718/prepavol_web
docker push eu.gcr.io/able-cogency-278718/prepavol_web

# Run tests locally

PYTHONPATH=services/web/ python -m pytest -v --cov prepavol --cov-report xml --junitxml=report.xml services/web

# Run tests in docker container

docker run --entrypoint /venv/bin/python yayadock/prepavol_web:latest -m pytest -v --cov prepavol --cov-report xml --junitxml=report.xml -o junit_family="xunit2"

# Linting

pylint --generated-members=form._,matplotlib.cm._ --ignore-patterns="venv/[\S+].py" services/web/prepavol/

flake8 services/web/prepavol/
