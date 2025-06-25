import json
import os

def verificar_coordenadas_rutas():
    """
    Verifica las coordenadas de las rutas del metro
    """
    print("🔍 Verificando coordenadas de rutas...")
    
    # Cargar archivo de rutas
    try:
        with open('static/data/metro_routes.json', 'r', encoding='utf-8') as f:
            routes_data = json.load(f)
    except FileNotFoundError:
        print("❌ No se encontró el archivo metro_routes.json")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear JSON: {e}")
        return
    
    print(f"✅ Archivo cargado: {len(routes_data.get('lines', []))} líneas")
    
    # Verificar coordenadas de cada línea
    coordenadas_incorrectas = 0
    total_coordenadas = 0
    
    for linea in routes_data.get('lines', []):
        line_id = linea.get('line', '')
        print(f"\n📏 Verificando Línea {line_id}...")
        
        for i, path in enumerate(linea.get('paths', [])):
            path_incorrecto = False
            
            for j, coord in enumerate(path):
                total_coordenadas += 1
                
                # Verificar si las coordenadas están en formato correcto para Madrid
                if len(coord) == 2:
                    lat, lon = coord[0], coord[1]
                    
                    # Madrid está en latitud ~40.4 y longitud ~-3.7
                    # Si la primera coordenada es negativa y la segunda positiva, están invertidas
                    if lat < 0 and lon > 0:
                        # Intercambiar coordenadas
                        path[j] = [lon, lat]
                        path_incorrecto = True
                        coordenadas_incorrectas += 1
                        print(f"  🔄 Coordenada {j} corregida: [{lat}, {lon}] → [{lon}, {lat}]")
            
            if path_incorrecto:
                print(f"  ✅ Path {i} corregido")
    
    print(f"\n📊 RESUMEN:")
    print(f"  • Total de coordenadas verificadas: {total_coordenadas}")
    print(f"  • Coordenadas corregidas: {coordenadas_incorrectas}")
    
    if coordenadas_incorrectas > 0:
        # Guardar archivo corregido
        try:
            with open('static/data/metro_routes.json', 'w', encoding='utf-8') as f:
                json.dump(routes_data, f, indent=2, ensure_ascii=False)
            print("✅ Archivo guardado con coordenadas corregidas")
        except Exception as e:
            print(f"❌ Error al guardar archivo: {e}")
    else:
        print("✅ No se encontraron coordenadas que necesiten corrección")

if __name__ == "__main__":
    verificar_coordenadas_rutas() 