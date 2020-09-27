# PrepaVol

Prepavol is a web app that helps preparing light aviation flights.  
It provides a _weight and balance_ form that allows to pick a plane from a fleet
and plan the load (passengers, baggages, fuel).  
It also allows to set the meteorological data for a given airfield so as to predict
the takeoff or landing distances for the planned weight.  
The app produces an A4 report that can be added to the flight documents.  
Check the Wiki for app usage.

# Installation

```bash
pip install prepavol
```

# Usage

In a non-production environment, run the flask app in Python:

```python
import prepavol
import os
os.environ["FLASK_ENV"] = "dev"
app = prepavol.create_app()
app.run(host="0.0.0.0", debug=True)
```

Example in a production environment with gunicorn (install with pip if required):  
Create python script _manage.py_ with the following commands:

```python
from flask.cli import FlaskGroup
from prepavol import create_app

app = create_app()
cli = FlaskGroup(app)

if __name__ == "__main__":
    cli()
```

Then run in a shell:

```bash
export FLASK_ENV="prod"
gunicorn --bind 0.0.0.0:5000 manage:app
```
