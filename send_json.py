import requests
import json

# Configuración
OUTPUT_JSON = 'tests3.json'  # Ruta del archivo JSON generado
ENDPOINT_URL = 'https://xray.cloud.getxray.app/api/v1/import/test/bulk'  # URL del endpoint
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0ZW5hbnQiOiI5Y2NmODIyNC0wZjdlLTM4NWItYmQ2YS0yY2U0ZGFiMmMwN2QiLCJhY2NvdW50SWQiOiI3MTIwMjA6MThiMjliZWMtMDA5Ny00ZDVlLWJhMGYtMTYwYTk1NDQ1YTIwIiwiaXNYZWEiOmZhbHNlLCJpYXQiOjE3NDUzMzAyMzAsImV4cCI6MTc0NTQxNjYzMCwiYXVkIjoiNTEyNTY5M0MwOTFFNDA3Qjk4RTQ0NEE4NTNDNkMxMTIiLCJpc3MiOiJjb20ueHBhbmRpdC5wbHVnaW5zLnhyYXkiLCJzdWIiOiI1MTI1NjkzQzA5MUU0MDdCOThFNDQ0QTg1M0M2QzExMiJ9.344gMWl5KW578PZq3oS1Srx6fMu444u-74ApBx2E4A0'

# Leer el archivo JSON
with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

# Configurar los headers para la solicitud
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {TOKEN}'  # Autenticación con token
}

# Enviar la solicitud POST
response = requests.post(ENDPOINT_URL, headers=headers, json=json_data)

# Verificar la respuesta
if response.status_code == 200:
    print("JSON enviado exitosamente.")
else:
    print(f"Error al enviar JSON: {response.status_code} - {response.text}")