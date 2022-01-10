from copy import copy
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, StringField
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.validators import DataRequired, NoneOf, InputRequired, NumberRange, Length, Optional, ValidationError
from .planes import WeightBalance
import json
from enum import Enum

def my_function(value):
    if value > 0:
        return f"Face +{value} kt"
    elif value == 0:
        return "Vent nul"
    else:
        return f"Arrière {value} kt"

class TypeVol(Enum):
    TDP = "Tour de piste"
    VLJVA = "Vol local de jour en vue de l'aérodrome"
    VLJHA = "Vol local de jour hors vue de l'aérodrome"
    NAV = "Vol de navigation de jour"
    NUIT = "Vol de nuit"

class DegagementForm(FlaskForm):
    distance_rng_index = range(5, 151, 5)
    distance_rng_values = [f"{x} Nm" for x in distance_rng_index ]
    distance_rng = list(zip(distance_rng_index, distance_rng_values))
    distance = SelectField(
        "Distance (Nm)",
        coerce=int,
        choices=distance_rng,
        default=0
    )

    vent_rng_index = range(-30, 31, 5)
    vent_rng_values = [my_function(x) for x in vent_rng_index]
    vent_rng = list(zip(vent_rng_index, vent_rng_values))
    vent = SelectField(
        "Vent",
        coerce=int,
        choices=vent_rng,
        default=0
    )

class EmportCarburantForm(FlaskForm):
    planes_data = WeightBalance.load_fleet_data()
    planes = json.dumps(planes_data)

    callsigns = list(planes_data.keys())

    fuel_range = range(0, 101, 10)

    callsign = SelectField(
        "Call sign",
        validators=[NoneOf("F-XXXX", message=("Veuillez choisir un appareil"))],
        choices=list(zip(callsigns, callsigns)),
    )

    type_vol_liste_values = list(zip((k.name for k in TypeVol),(k.value for k in TypeVol)))
    type_vol = SelectField(
        "Type de vol",
        validators=[DataRequired()],
        choices=type_vol_liste_values,
        default="TDP"
    )

    nb_branches_liste = range(0, 7)
    nb_branches = SelectField(
        "Nb branches",
        validators=[DataRequired(), NumberRange(1, 6)],
        coerce=int,
        choices=list(zip(nb_branches_liste, nb_branches_liste))
    )

    branches = FieldList(
        FormField(DegagementForm),
        min_entries=6,
        max_entries=6
    )

    degagement = FormField(
        DegagementForm,
        "Dégagement"
    )

    marge_rng = range(0, 61, 2)
    marge = SelectField(
        "Marge (mn)",
        validators=[NumberRange(min=2, max=60)],
        coerce=int,
        choices=list(zip(marge_rng, marge_rng))
    )

    
    def validate_carburant(form, field):
        plane = WeightBalance(form.data["callsign"])
        if field.name == "mainfuel":
            if plane.maxmainfuel > 0:
                if field.data == 0:
                    raise ValidationError("Le réservoir principal est vide")
            else:
                if field.data > 0:
                    raise ValidationError("Cet avion ne comporte pas de réservoir principal")
        if field.name == "rightwingfuel" or field.name == "leftwingfuel":
            if plane.maxwingfuel > 0:
                if form.data["leftwingfuel"] + form.data["rightwingfuel"] > 2 * 100:
                    raise ValidationError("Les réservoirs d'ailes débordent")
                if form.data["leftwingfuel"] + form.data["rightwingfuel"] == 0:
                    raise ValidationError("Les réservoirs d'aile sont vides")
            else:
                if field.data > 0:
                    raise ValidationError("Cet avion ne comporte pas de réservoir d'aile")
        else:
            if plane.maxauxfuel > 0:
                if field.data == 0:
                    raise ValidationError("Le réservoir supplémentaire est vide")
            else:
                if field.data > 0:
                    raise ValidationError("Cet avion ne comporte pas de réservoir supplémentaire")

    # Main fuel
    mainfuel_choices = list(zip(fuel_range, fuel_range))
    mainfuel = SelectField(
        "Niveau réservoir principal (%)",
        coerce=int,
        choices=mainfuel_choices,
        validators=[validate_carburant]
    )
    # Left wing fuel
    leftwingfuel_choices = list(zip(fuel_range, fuel_range))
    leftwingfuel = SelectField(
        "Niveau réservoir aile gauche (%)",
        coerce=int,
        choices=leftwingfuel_choices,
        validators=[validate_carburant]
    )
    # Right wing fuel
    rightwingfuel_choices = list(zip(fuel_range, fuel_range))
    rightwingfuel = SelectField(
        "Niveau réservoir aile droite (%)",
        coerce=int,
        choices=rightwingfuel_choices,
        validators=[validate_carburant]
    )
    # Aux fuel
    auxfuel_choices = list(zip(fuel_range, fuel_range))
    auxfuel = SelectField(
        "Niveau réservoir suppl. (%)",
        coerce=int,
        choices=auxfuel_choices,
        validators=[validate_carburant]
    )
    submit = SubmitField("Valider")
