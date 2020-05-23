from flask_wtf import FlaskForm
from wtforms import TextField, IntegerField, SubmitField, SelectField, DecimalField
from wtforms import validators, ValidationError

class PrepflightForm(FlaskForm):
    plane = SelectField("Call sign")

    # Empty plane
    #bew = DecimalField("bew")
    #bearm = DecimalField("arm")
    #bemoment = DecimalField("moment")
    
    # Front row
    pax0 = SelectField("pax0")
    pax1 = SelectField("pax1")
    #frontweight = DecimalField('frontweight')
    #frontarm = DecimalField()
    #frontmoment = DecimalField()
    # Rear row
    pax2 = SelectField("pax2")
    pax3 = SelectField("pax3")
    #rearweight = DecimalField()
    #reararm = DecimalField()
    #rearmoment = DecimalField()
    # Baggage
    baggage = SelectField("baggage")
    #bagweight = DecimalField()
    #bagarm = DecimalField()
    #bagmoment = DecimalField()
    # Fuel
    fuelgauge = SelectField("jauge fuel")
    #fuel = DecimalField()
    #fuelarm = DecimalField()
    #fuelmoment = DecimalField()
    auxfuel = SelectField("fuel aux. (l)")
    #auxfuelarm = DecimalField()
    #auxfuelmoment = DecimalField()

    # Performances
    tkalt = SelectField("alt (ft)")
    ldalt = SelectField("alt (ft)")
    tktemp = SelectField("temp (°C)")
    ldtemp = SelectField("temp (°C)")
    tkqnh = SelectField("QNH")
    ldqnh = SelectField("QNH")

    submit = SubmitField("Valider")