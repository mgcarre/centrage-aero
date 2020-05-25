from flask_wtf import FlaskForm
from wtforms import TextField, IntegerField, SubmitField, SelectField, DecimalField
from wtforms import validators, ValidationError


class PrepflightForm(FlaskForm):
    plane = SelectField("Call sign", [
        validators.NoneOf("FXXXX",
        message=("Veuillez choisir un appareil"))])

    # Front row
    pax0 = SelectField("pax0", [validators.DataRequired()])
    pax1 = SelectField("pax1", [validators.DataRequired()])
    # Rear row
    pax2 = SelectField("pax2", [validators.DataRequired()])
    pax3 = SelectField("pax3", [validators.DataRequired()])
    # Baggage
    baggage = SelectField("baggage", [validators.DataRequired()])
    # Fuel
    fuelgauge = SelectField("jauge fuel", [validators.DataRequired()])
    auxfuel = SelectField("fuel aux. (l)", [validators.DataRequired()])

    # Performances
    tkalt = SelectField("alt (ft)", [validators.DataRequired()])
    ldalt = SelectField("alt (ft)", [validators.DataRequired()])
    tktemp = SelectField("temp (°C)", [validators.DataRequired()])
    ldtemp = SelectField("temp (°C)", [validators.DataRequired()])
    tkqnh = SelectField("QNH", [validators.DataRequired()])
    ldqnh = SelectField("QNH", [validators.DataRequired()])

    submit = SubmitField("Valider")