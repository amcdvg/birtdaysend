# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el requirements.txt y instala dependencias
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copia el código de la aplicación
COPY . .

# Exponer el puerto 80 (Netlify usa este puerto por defecto)
EXPOSE 80

# Comando para ejecutar la aplicación con Uvicorn
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]