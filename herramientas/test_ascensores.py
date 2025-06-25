# test_ascensores.py
from scraper_ninja_tiempo_real import ScraperNinjaTiempoReal

scraper = ScraperNinjaTiempoReal()

tests = [
    # (URL de la línea, nombre de la estación EXACTO como aparece en la web)
    ("https://www.metromadrid.es/es/linea/linea-4", "Alfonso XIII"),
    ("https://www.metromadrid.es/es/linea/linea-4", "Avenida de América"),
    ("https://www.metromadrid.es/es/linea/linea-1", "Sol"),
    ("https://www.metromadrid.es/es/linea/linea-5", "Callao"),
    ("https://www.metromadrid.es/es/linea/linea-6", "Argüelles"),
    ("https://www.metromadrid.es/es/linea/linea-10", "Chamartín"),
]

for url, nombre in tests:
    print(f"\n--- Probando {nombre} en {url} ---")
    try:
        # Si tu método devuelve también la última actualización, descomenta la siguiente línea:
        # asc, esc, actualizacion = scraper.obtener_estado_servicios_por_estacion(url, nombre)
        # print(f"Ascensores: {asc} | Escaleras: {esc} | Última actualización: {actualizacion}")

        # Si solo devuelve ascensores y escaleras:
        asc, esc = scraper.obtener_estado_servicios_por_estacion(url, nombre)
        print(f"Ascensores: {asc} | Escaleras: {esc}")
    except Exception as e:
        print(f"❌ Error: {e}")