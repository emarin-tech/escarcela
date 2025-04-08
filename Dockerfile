# Usa la imagen oficial de Python
FROM python:3.9-slim

# Setea la variable de entorno para no interactuar con el terminal
ENV PYTHONUNBUFFERED 1

# Crea un directorio de trabajo en la imagen
WORKDIR /app

# Copia los archivos de tu proyecto dentro del contenedor
COPY . /app/

# Instala las dependencias de tu proyecto
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expón el puerto que usará la aplicación Flask (por defecto es el 5000)
EXPOSE 8080

# Ejecuta el comando para iniciar la aplicación Flask (asumiendo que el archivo principal es `main.py`)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
