# CentrageAero

CentrageAero is a fork from [PrepaVol](https://gitlab.com/yannick.teresiak/flaskapp.git). This is a web app that helps preparing light aviation flights.  
It provides a _weight and balance_ form that allows to pick a plane from a fleet
and plan the load (passengers, baggages, fuel).  
It also allows to set the meteorological data for a given airfield so as to predict
the takeoff or landing distances for the planned weight.
It also provides an API for securing AD ALT using [eAIP France](https://www.sia.aviation-civile.gouv.fr/).  
The app produces an A4 report that can be added to the flight documents.  

> **Original work from yannick.teresiak :** https://gitlab.com/yannick.teresiak/flaskapp.git 

## Installation

Clone the original code:

```bash
git clone https://gitlab.com/yannick.teresiak/flaskapp.git
```
Clone this fork:
```bash
git clone https://github.com/mgcarre/centrage-aero
```

Then install the required softwares from services/web/requirements.txt.

## Usage

The code is meant to be used to build a docker image and run the container on Google Cloud Run.
However, it can be run locally with the Flask web server using the venv python module this way:

```bash
python3 -m venv venv
. venv/bin/activate
export APP_FOLDER=$PWD/services/web
export FLASK_APP=services/web/prepavol/__init__.py
export FLASK_ENV=dev
flask run
```

or by running a gunicorn server:

```bash
export PYTHONPATH=services/web
gunicorn --bind 0.0.0.0:5000 --access-logfile - --env FLASK_ENV=production --env FLASK_APP=prepavol/__init__.py --env APP_FOLDER=$PWD/services/web services.web.manage:app
```

## Run tests locally

Using pytest-cov, we can run tests and report coverage at the same time.

```bash
export PYTHONPATH=services/web/
python -m pytest -v --cov prepavol --cov-report term --cov-report xml --junitxml=report.xml services/web
```

## Linting

```bash
pylint --generated-members=form._,matplotlib.cm._ --ignore-patterns="venv/[\S+].py" services/web/prepavol/

flake8 services/web/prepavol/
```

# Building docker images and deploying on GCP

## Recipe for multi-container solution with nginx and gunicorn

This doesn't work on Cloud Run - nginx not needed there anyway.
It works on Google App Engine, but it is not the right solution.

```bash
docker-compose -f docker-compose.prod.yaml -f up -d --build
```

## Single container with gunicorn for Cloud Run

```bash
docker pull yayadock/prepavol_web:latest
docker build -f services/web/Dockerfile.prod services/web
docker tag ${CI_COMMIT_SHA} yayadock/prepavol_web
docker tag latest yayadock/prepavol_web
docker tag ${CI_COMMIT_SHA} eu.gcr.io/able-cogency-278718/prepavol_web
docker push eu.gcr.io/able-cogency-278718/prepavol_web
```

## Usage with the docker image

```bash
docker pull yayadock/prepavol_web:latest
docker run -p 5000:5000 -d yayadock/prepavol_web
```

Then browse http://0.0.0.0:5000

## Run tests in docker container

```bash
docker pull yayadock/prepavol_web:latest
docker run --entrypoint /venv/bin/python yayadock/prepavol_web:latest -m pytest -v --cov prepavol --cov-report term --cov-report xml --junitxml=report.xml -o junit_family="xunit2"
```
