from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
from sqlite3 import OperationalError
import time

import pandas as pd
import urllib

from sqlalchemy import create_engine




params_ds = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=SQLBI;"
    "DATABASE=DS;"
    "Trusted_Connection=yes;"
)

# Crear conexión SQLAlchemy
ENGINE_DS = create_engine(f'mssql+pyodbc:///?odbc_connect={params_ds}')

params_dwh= urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=SQLBI;"
    "DATABASE=DWH;"
    "Trusted_Connection=yes;"
)
# Crear conexión SQLAlchemy
ENGINE_DWH = create_engine(f'mssql+pyodbc:///?odbc_connect={params_dwh}')


def enviar_correo(destinatarios, asunto, cuerpo):
    try:
        # Variables del archivo .env
        email_usuario = os.getenv('EMAIL_USUARIO')
        email_contrasena = os.getenv('EMAIL_CONTRASENA')
        
        # Crear la conexión con el servidor SMTP
        servidor = smtplib.SMTP('smtp.office365.com', 587)
        servidor.starttls()
        servidor.login(email_usuario, email_contrasena)
        
        # Crear el mensaje de correo
        mensaje = MIMEMultipart()
        mensaje['From'] = email_usuario
        
        if len(destinatarios) == 1:
            to = destinatarios[0] 
        else:
            to = ", ".join(destinatarios) if isinstance(destinatarios, list) else destinatarios
        mensaje['To'] = to
        mensaje['Subject'] = asunto
        cuerpo_html = cuerpo
        mensaje.attach(MIMEText(cuerpo_html, 'html'))
        
        # Enviar el correo
        servidor.send_message(mensaje)
        servidor.quit()
        print("Correo enviado exitosamente")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        
        
        
def ejecutar_consulta_segura(engine, query, dtype=None, reintentos=3, espera=5):
    """
    Ejecuta una consulta SQL con manejo de reconexión en caso de error de conexión.

    Parámetros:
    - engine: Conexión SQLAlchemy a la base de datos.
    - query: Consulta SQL en formato string.
    - dtype: Especificación opcional de tipos de datos para pandas.
    - reintentos: Número de veces que intentará reconectar si hay fallo de conexión.
    - espera: Tiempo en segundos antes de volver a intentar la conexión.

    Retorna:
    - DataFrame con los resultados de la consulta.
    """
    intentos = 0

    while intentos < reintentos:
        try:
            print(f"Ejecutando consulta... Intento {intentos + 1}/{reintentos}")
            with engine.connect() as connection:
                if dtype:
                    df = pd.read_sql_query(sql=query, con=connection, dtype=dtype)
                else:
                    df = pd.read_sql_query(sql=query, con=connection)
            print("Consulta ejecutada exitosamente.")
            return df

        except OperationalError as e:
            print(f"Error de conexión: {e}. Reintentando en {espera} segundos...")
            time.sleep(espera)
            intentos += 1

    print(f"Fallaron los {reintentos} intentos de conexión.")
    raise Exception("No se pudo conectar a la base de datos después de varios intentos.")








