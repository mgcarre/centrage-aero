# *_* coding: utf-8 *_*
"""FlaskForm."""

import json
import copy
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField
from wtforms.validators import DataRequired, NoneOf, InputRequired
from .planes import WeightBalance


class PrepflightForm(FlaskForm):
    """Form."""

    # Get plane list from the planes data
    # jinja expects a string and not a dict
    planes_data = WeightBalance.load_fleet_data()
    planes = json.dumps(planes_data)

    callsigns = list(planes_data.keys())

    # Run through the fleet to pick get the max fuel and auxfuel
    # so as to build valid select lists for all aircrafts
    maxfuel_list = []
    maxauxfuel_list = []
    for k, v in planes_data.items():
        maxfuel_list.append(v["maxfuel"])
        maxauxfuel_list.append(v["maxauxfuel"])
    maxfuel = max(maxfuel_list)
    maxauxfuel = max(maxauxfuel_list)
    
    plane = WeightBalance(callsigns[0])
    pax_weight_range = range(0, 145, 5)
    baggage_weight_range = range(0, plane.bagmax + 1, 5)
    fuel_range = range(0, maxfuel + 5, 5)
    auxfuel_range = range(0, maxauxfuel + 5, 5)
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
        "pax0",
        coerce=int,
        validators=[DataRequired()],
        choices=pax_weight_choices,
    )
    pax1 = SelectField(
        "pax1",
        coerce=int,
        validators=[InputRequired()],
        choices=pax_weight_choices,
    )
    # Rear row
    pax2 = SelectField(
        "pax2",
        coerce=int,
        validators=[InputRequired()],
        choices=pax_weight_choices,
    )
    pax3 = SelectField(
        "pax3",
        coerce=int,
        validators=[InputRequired()],
        choices=pax_weight_choices,
    )
    # Baggage
    baggage_choices = list(zip(baggage_weight_range, baggage_weight_range))
    baggage = SelectField(
        "baggage",
        coerce=int,
        validators=[InputRequired()],
        choices=baggage_choices,
    )
    # Fuel
    fuel_choices = list(zip(fuel_range, fuel_range))
    fuel = SelectField(
        "fuel",
        coerce=float,
        validators=[InputRequired()],
        choices=fuel_choices,
    )
    # Aux fuel
    auxfuel_choices = list(zip(auxfuel_range, auxfuel_range))
    auxfuel = SelectField(
        "fuel aux",
        coerce=float,
        validators=[InputRequired()],
        choices=auxfuel_choices,
    )

    # Performances
    altitude_choices = list(zip(altitude_range, altitude_range))
    tkalt = SelectField(
        "alt (ft)",
        coerce=int,
        validators=[InputRequired()],
        choices=altitude_choices,
    )
    ldalt = SelectField(
        "alt (ft)",
        coerce=int,
        validators=[InputRequired()],
        choices=altitude_choices,
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
