import requests

# Probar Metro Ligero
response = requests.get("http://localhost:5001/api/transport/metro_ligero", timeout=30)
if response.status_code == 200:
    data = response.json()
    if data.get('success') and 'data' in data:
        features = data['data'].get('features', [])
        if features:
            first_feature = features[0]
            properties = first_feature.get('properties', {})
            print("Campos de Metro Ligero:")
            for key, value in properties.items():
                print(f"  {key}: {value}")
else:
    print("Error al obtener datos de Metro Ligero") 