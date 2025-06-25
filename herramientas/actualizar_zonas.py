import pandas as pd
import re
import unicodedata

def normalize_station_name(name):
    """
    Normaliza un nombre de estación para que coincida con las claves del diccionario.
    """
    name = name.lower()
    nfkd_form = unicodedata.normalize('NFD', name)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return only_ascii.strip()

def get_hardcoded_zones():
    """
    Devuelve un diccionario con las zonas tarifarias correctas para las estaciones
    de las coronas B1, B2 y B3.
    """
    zones_b1 = [
        "Alcorcón Central", "Alonso de Mendoza", "Arroyo Culebro", "Baunatal", 
        "Barrio del Puerto", "Casa del Reloj", "Conservatorio", "Coslada Central", 
        "El Bercial", "El Carrascal", "El Casar", "Getafe Central", "Henares", 
        "Hospital del Henares", "Hospital Infanta Sofía", "Hospital Severo Ochoa", 
        "Jarama", "Joaquín Vilumbrales", "Juan de la Cierva", "Julián Besteiro", 
        "La Granja", "La Moraleja", "La Rambla", "Leganés Central", "Los Espartales", 
        "Manuel de Falla", "Marqués de la Valdavia", "Parque Lisboa", "Parque Oeste", 
        "Puerta del Sur", "Reyes Católicos", "Rivas Futura", "Rivas Urbanizaciones", 
        "San Fernando", "San Nicasio"
    ]
    zones_b2 = [
        "Fuenlabrada Central", "Hospital de Fuenlabrada", "Hospital de Móstoles", 
        "Loranca", "Manuela Malasaña", "Móstoles Central", "Parque de los Estados", 
        "Parque Europa", "Pradillo", "Universidad Rey Juan Carlos"
    ]
    zones_b3 = ["Arganda del Rey", "La Poveda"]
    
    zone_map = {}
    for station in zones_b1:
        zone_map[normalize_station_name(station)] = 'B1'
    for station in zones_b2:
        zone_map[normalize_station_name(station)] = 'B2'
    for station in zones_b3:
        zone_map[normalize_station_name(station)] = 'B3'
        
    return zone_map

def update_csv_with_zones():
    """
    Actualiza el archivo CSV con el mapa de zonas codificado.
    """
    zone_map = get_hardcoded_zones()
    input_file = 'datos_clave_estaciones.csv'

    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {input_file}")
        return

    updated_count = 0
    
    print("Actualizando zonas en el archivo CSV con datos locales...")
    for index, row in df.iterrows():
        station_name_csv = row['nombre']
        normalized_name_csv = normalize_station_name(station_name_csv)
        
        # Buscar la zona en nuestro mapa codificado
        new_zone = zone_map.get(normalized_name_csv)
        
        # Si la encontramos y es diferente a la que hay, la actualizamos.
        if new_zone and str(row.get('zona', '')).upper() != str(new_zone).upper():
            df.at[index, 'zona'] = new_zone
            updated_count += 1

    df.to_csv(input_file, index=False)
    
    print("\n¡Proceso completado!")
    print(f"Estaciones actualizadas en el CSV: {updated_count}")
    print(f"El archivo '{input_file}' ha sido actualizado.")

if __name__ == '__main__':
    update_csv_with_zones()
