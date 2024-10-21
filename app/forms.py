from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Regexp, Length


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField(
        "Email", validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=12)]
    )
    submit = SubmitField("Register")


class PaymentForm(FlaskForm):
    card_number = StringField("Card Number", validators=[DataRequired()])
    expiration = StringField("Expiration Date (MM/YY)", validators=[DataRequired()])
    cvv = PasswordField("CVV", validators=[DataRequired()])
    submit = SubmitField("Submit Payment")
