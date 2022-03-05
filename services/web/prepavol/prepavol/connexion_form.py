from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.validators import InputRequired, NoneOf

class ConnexionForm(FlaskForm):
    
    pilot_name = StringField(
        "Nom pilote",
        validators=[InputRequired(), NoneOf("test")]
    )

    submit = SubmitField("Valider")
