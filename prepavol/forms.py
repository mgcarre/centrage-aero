import json
from flask_wtf import FlaskForm
from wtforms import TextField, IntegerField, SubmitField, SelectField, DecimalField
from wtforms.validators import DataRequired, NoneOf, InputRequired
from .planes import WeightBalance, PlanePerf


class PrepflightForm(FlaskForm):

    # Get plane list from the planes module
    planes = json.dumps(WeightBalance._planes)

    callsigns = list(WeightBalance._planes.keys())
    auxfuel_list = []
    for p in callsigns:
        auxfuel_list.append(WeightBalance._planes[p]["maxauxfuel"])
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
    pax_weight_choices = [i for i in zip(pax_weight_range, pax_weight_range)]
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
    baggage_choices = [i for i in zip(baggage_weight_range, baggage_weight_range)]
    baggage = SelectField(
        "baggage", coerce=int, validators=[InputRequired()], choices=baggage_choices
    )
    # Fuel
    fuel_gauge_choices = [i for i in zip(fuel_gauge_range, fuel_gauge_range)]
    fuel_gauge = SelectField(
        "jauge fuel",
        coerce=float,
        validators=[InputRequired()],
        choices=fuel_gauge_choices,
    )
    # Aux fuel
    auxfuel_choices = [i for i in zip(auxfuel_range, auxfuel_range)]
    auxfuel_gauge = SelectField(
        "jauge fuel aux.",
        coerce=int,
        validators=[InputRequired()],
        choices=auxfuel_choices,
    )

    # Performances
    altitude_choices = [i for i in zip(altitude_range, altitude_range)]
    tkalt = SelectField(
        "alt (ft)", coerce=int, validators=[InputRequired()], choices=altitude_choices
    )
    ldalt = SelectField(
        "alt (ft)", coerce=int, validators=[InputRequired()], choices=altitude_choices
    )

    temperature_choices = [i for i in zip(temperature_range, temperature_range)]
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

    qnh_choices = [i for i in zip(qnh_range, qnh_range)]
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
