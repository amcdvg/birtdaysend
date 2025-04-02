from main import handler  # Importa el manejador creado en main.py

def lambda_handler(event, context):
    return handler(event, context)