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
    username = StringField('Nombre de usuario', 
                           validators=[DataRequired(message="El nombre de usuario es obligatorio."), 
                                       Length(min=3, max=25, message="Debe tener entre 3 y 25 caracteres."), 
                                       username_exists])
    email = StringField('Email',
                        validators=[DataRequired(message="El email es obligatorio."), 
                                    Email(message="Por favor, introduce un email válido."), 
                                    email_exists])
    password = PasswordField('Contraseña', 
                             validators=[DataRequired(message="La contraseña es obligatoria."), 
                                         Length(min=6, message="La contraseña debe tener al menos 6 caracteres.")])
    confirm_password = PasswordField('Confirmar Contraseña',
                                     validators=[DataRequired(message="Confirma la contraseña."), 
                                                 EqualTo('password', message="Las contraseñas no coinciden.")])
    submit = SubmitField('Registrarse')

class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""
    email = StringField('Email',
                        validators=[DataRequired(message="El email es obligatorio."), 
                                    Email(message="Email no válido.")])
    password = PasswordField('Contraseña', validators=[DataRequired(message="La contraseña es obligatoria.")])
    remember = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión') 