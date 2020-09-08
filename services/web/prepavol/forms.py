# *_* coding: utf-8 *_*
"""Flaskform
"""

__author__ = "Yannick Teresiak"
__copyright__ = "Copyright 2020, Prepavol"
__credits__ = ["Yannick Teresiak"]
__license__ = None
__version__ = "1.0.0"
__maintainer__ = "Yannick Teresiak"
__email__ = "yannick.teresiak@gmail.com"
__status__ = "Production"

from pathlib import Path
import json
import yaml
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField
from wtforms.validators import DataRequired, NoneOf, InputRequired
from .planes import WeightBalance


class PrepflightForm(FlaskForm):
    """Form
    """
    # Get plane list from the planes data
    # jinja expects a string and not a dict
    planes_file = Path(__file__).parent / "data/planes.yaml"
    planes_data = yaml.safe_load(open(planes_file, "r"))
    planes = json.dumps(planes_data)

    callsigns = list(planes_data.keys())
    auxfuel_list = []
    for p in callsigns:
        auxfuel_list.append(planes_data[p]["maxauxfuel"])
    maxauxfuel = max(auxfuel_list)

    plane = WeightBalance(callsigns[0])
    pax_weight_range = range(0, 145, 5)
    baggage_weight_range = range(0, plane.bagmax + 1, 5)
    fuel_gauge_range = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]
    auxfuel_range = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]
    altitude_range = range(0, 8100, 100)
    temperature_range = range(-20, 51, 1)
    qnh_range = range(950, 1051, 1)

    callsign = SelectField(
        "Call sign",
        validators=[NoneOf("FXXXX", message=("Veuillez choisir un appareil"))],
        choices=list(zip(callsigns, callsigns)),
    )

    # Front row
    pax_weight_choices = list(zip(pax_weight_range, pax_weight_range))
    pax0 = SelectField(
        "pax0", coerce=int, validators=[DataRequired()], choices=pax_weight_choices
    )
    pax1 = SelectField(
        "pax1", coerce=int, validators=[InputRequired()], choices=pax_weight_choices
    )
    # Rear row
    pax2 = SelectField(
        "pax2", coerce=int, validators=[InputRequired()], choices=pax_weight_choices
    )
    pax3 = SelectField(
        "pax3", coerce=int, validators=[InputRequired()], choices=pax_weight_choices
    )
    # Baggage
    baggage_choices = list(zip(baggage_weight_range, baggage_weight_range))
    baggage = SelectField(
        "baggage", coerce=int, validators=[InputRequired()], choices=baggage_choices
    )
    # Fuel
    fuel_gauge_choices = list(zip(fuel_gauge_range, fuel_gauge_range))
    fuel_gauge = SelectField(
        "jauge fuel",
        coerce=float,
        validators=[InputRequired()],
        choices=fuel_gauge_choices,
    )
    # Aux fuel
    auxfuel_choices = list(zip(auxfuel_range, auxfuel_range))
    auxfuel_gauge = SelectField(
        "jauge fuel aux.",
        coerce=float,
        validators=[InputRequired()],
        choices=auxfuel_choices,
    )

    # Performances
    altitude_choices = list(zip(altitude_range, altitude_range))
    tkalt = SelectField(
        "alt (ft)", coerce=int, validators=[InputRequired()], choices=altitude_choices
    )
    ldalt = SelectField(
        "alt (ft)", coerce=int, validators=[InputRequired()], choices=altitude_choices
    )

    temperature_choices = list(zip(temperature_range, temperature_range))
    tktemp = SelectField(
        "temp (°C)",
        coerce=int,
        validators=[InputRequired()],
        choices=temperature_choices,
        default=15,
    )
    ldtemp = SelectField(
        "temp (°C)",
        coerce=int,
        validators=[InputRequired()],
        choices=temperature_choices,
        default=15,
    )

    qnh_choices = list(zip(qnh_range, qnh_range))
    tkqnh = SelectField(
        "QNH",
        coerce=int,
        validators=[InputRequired()],
        choices=qnh_choices,
        default=1013,
    )
    ldqnh = SelectField(
        "QNH",
        coerce=int,
        validators=[InputRequired()],
        choices=qnh_choices,
        default=1013,
    )

    submit = SubmitField("Valider")
