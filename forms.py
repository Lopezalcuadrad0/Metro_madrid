from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
import sqlite3
import os

def get_db_connection():
    """Función helper para conectar a la base de datos."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'estaciones_fijas_v2.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def email_exists(form, field):
    """Validador para comprobar si un email ya está en uso."""
    conn = get_db_connection()
    user = conn.execute('SELECT email FROM users WHERE email = ?', (field.data,)).fetchone()
    conn.close()
    if user:
        raise ValidationError('Este email ya está registrado. Por favor, inicia sesión o elige otro.')

def username_exists(form, field):
    """Validador para comprobar si un nombre de usuario ya está en uso."""
    conn = get_db_connection()
    user = conn.execute('SELECT username FROM users WHERE username = ?', (field.data,)).fetchone()
    conn.close()
    if user:
        raise ValidationError('Este nombre de usuario ya existe. Por favor, elige otro.')

class RegistrationForm(FlaskForm):
    """Formulario de registro de usuarios."""
    username = StringField('Usuario',
                         validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                       validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña',
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""
    username = StringField('Usuario',
                         validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión') 