import os

try:
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv("REAL8_ISSUER"):
        raise ValueError("REAL8_ISSUER no está definido en el archivo .env")
except ImportError:
    pass

def is_cloud_run():
    """
    Detecta si estamos ejecutando en Cloud Run, usando la variable de entorno K_SERVICE
    """
    return os.getenv("K_SERVICE") is not None

def get_secret_local(name):
    """
    Obtiene secretos desde variables de entorno (modo local / .env)
    """
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Secreto {name} no encontrado en el archivo .env")
    return value

def get_secret_cloud(name):
    """
    Obtiene secretos desde Google Secret Manager (modo Cloud Run)
    """
    from google.cloud import secretmanager_v1
    client = secretmanager_v1.SecretManagerServiceClient()
    project_id = os.getenv("GCP_PROJECT")
    secret_path = f"projects/{project_id}/secrets/{name}/versions/latest"
    response = client.access_secret_version(name=secret_path)
    return response.payload.data.decode("UTF-8")


def get_secret(name):
    if is_cloud_run():
        return get_secret_cloud(name)
    else:
        return get_secret_local(name)
