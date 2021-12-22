# *_* coding: utf-8 *_*
"""FlaskForm."""

import json
import copy
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField
from wtforms.validators import DataRequired, NoneOf, InputRequired, NumberRange
from .planes import WeightBalance


class PrepflightForm(FlaskForm):
    """Form."""

    # Get plane list from the planes data
    # jinja expects a string and not a dict
    planes_data = WeightBalance.load_fleet_data()
    planes = json.dumps(planes_data)

    callsigns = list(planes_data.keys())

    # Run through the fleet to pick get the max mainfuel, wingfuel and auxfuel 
    # so as to build valid select lists for all aircrafts
    maxmainfuel_list = []
    maxwingfuel_list = []
    maxauxfuel_list = []
    bagmax_list = []
    bagmax2_list = []
    for k, v in planes_data.items():
        maxmainfuel_list.append(v["maxmainfuel"])
        maxwingfuel_list.append(v["maxwingfuel"])
        maxauxfuel_list.append(v["maxauxfuel"])
        bagmax_list.append(v["bagmax"])
        bagmax2_list.append(v["bagmax2"])
    maxmainfuel = max(maxmainfuel_list)
    maxwingfuel = max(maxwingfuel_list)
    maxauxfuel = max(maxauxfuel_list)
    maxbagmax = max(bagmax_list)
    maxbagmax2 = max(bagmax2_list)
    
    plane = WeightBalance(callsigns[0])
    pax_weight_range = range(0, 145, 5)
    baggage_weight_range = range(0, maxbagmax + 1, 5)
    baggage2_weight_range = range(0, maxbagmax2 + 1, 5)
    mainfuel_range = range(0, maxmainfuel + 5, 5)
    wingfuel_range = range(0, maxwingfuel + 5, 5)
    auxfuel_range = range(0, maxauxfuel + 5, 5)
    altitude_range = range(-100, 8100, 100)
    temperature_range = range(-20, 51, 1)
    qnh_range = range(950, 1051, 1)

    callsign = SelectField(
        "Call sign",
        validators=[NoneOf("F-XXXX", message=("Veuillez choisir un appareil"))],
        choices=list(zip(callsigns, callsigns)),
    )

    # Front row
    pax_weight_choices = list(zip(pax_weight_range, pax_weight_range))
    pax0 = SelectField(
        "pax0",
        coerce=int,
        validators=[DataRequired(message="Ce champ est requis"),NumberRange(min=1,message="Le cdb ne peut avoir un poids nul")],
        choices=pax_weight_choices,
    )
    pax1 = SelectField(
        "pax1",
        coerce=int,
        validators=[InputRequired(message="Ce champ est requis")],
        choices=pax_weight_choices,
    )
    # Rear row
    pax2 = SelectField(
        "pax2",
        coerce=int,
        validators=[InputRequired(message="Ce champ est requis")],
        choices=pax_weight_choices,
    )
    pax3 = SelectField(
        "pax3",
        coerce=int,
        validators=[InputRequired(message="Ce champ est requis")],
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
    # Zone 2 Baggage (Sonaca)
    baggage2_choices = list(zip(baggage2_weight_range, baggage2_weight_range))
    baggage2 = SelectField(
        "baggage 2",
        coerce=int,
        validators=[InputRequired()],
        choices=baggage2_choices,
    )
    # Main fuel
    mainfuel_choices = list(zip(mainfuel_range, mainfuel_range))
    mainfuel = SelectField(
        "fuel pcpl",
        coerce=float,
        validators=[NumberRange(min=1,message="Le carburant ne peut être nul")],
        choices=mainfuel_choices,
    )
    # Left wing fuel
    leftwingfuel_choices = list(zip(wingfuel_range, wingfuel_range))
    leftwingfuel = SelectField(
        "fuel aile gauche (L)",
        coerce=float,
        validators=[InputRequired()],
        choices=leftwingfuel_choices,
    )
    # Right wing fuel
    rightwingfuel_choices = list(zip(wingfuel_range, wingfuel_range))
    rightwingfuel = SelectField(
        "fuel aile droite (L)",
        coerce=float,
        validators=[InputRequired()],
        choices=rightwingfuel_choices,
    )
    # Aux fuel
    auxfuel_choices = list(zip(auxfuel_range, auxfuel_range))
    auxfuel = SelectField(
        "fuel suppl.",
        coerce=float,
        validators=[InputRequired()],
        choices=auxfuel_choices,
    )

    # Performances
    altitude_choices = list(zip(altitude_range, altitude_range))
    tkalt = SelectField(
        "alt (ft)",
        coerce=int,
        validators=[NumberRange(min=-99,message="Le QNE du terrain est requis")],
        choices=altitude_choices,
    )
    ldalt = SelectField(
        "alt (ft)",
        coerce=int,
        validators=[NumberRange(min=-99,message="Le QNE du terrain est requis")],
        choices=altitude_choices,
    )

    temperature_choices = list(zip(temperature_range, temperature_range))
    tktemp = SelectField(
        "temp (°C)",
        coerce=int,
        validators=[DataRequired(message="Ce champ est requis")],
        choices=temperature_choices,
        default=15,
    )
    ldtemp = SelectField(
        "temp (°C)",
        coerce=int,
        validators=[DataRequired(message="Ce champ est requis")],
        choices=temperature_choices,
        default=15,
    )

    qnh_choices = list(zip(qnh_range, qnh_range))
    tkqnh = SelectField(
        "QNH",
        coerce=int,
        validators=[DataRequired(message="Ce champ est requis")],
        choices=qnh_choices,
        default=1013,
    )
    ldqnh = SelectField(
        "QNH",
        coerce=int,
        validators=[DataRequired(message="Ce champ est requis")],
        choices=qnh_choices,
        default=1013,
    )

    submit = SubmitField("Valider")
