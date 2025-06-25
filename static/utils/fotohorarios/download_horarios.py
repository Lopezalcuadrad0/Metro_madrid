import os
import requests
from tqdm import tqdm

def download_schedules():
    """Descarga los horarios oficiales del Metro de Madrid desde el CRTM."""
    
    # Directorio de salida
    output_dir = "fotohorarios"
    os.makedirs(output_dir, exist_ok=True)
    
    # Lista de horarios a descargar
    schedules = {
        "L1_ida": "https://www.crtm.es/datos_lineas/horarios/4001H1.png",
        "L1_vuelta": "https://www.crtm.es/datos_lineas/horarios/4001H2.png",
        "L2_ida": "https://www.crtm.es/datos_lineas/horarios/4002H1.png",
        "L2_vuelta": "https://www.crtm.es/datos_lineas/horarios/4002H2.png",
        "L3_ida": "https://www.crtm.es/datos_lineas/horarios/4003H1.png",
        "L3_vuelta": "https://www.crtm.es/datos_lineas/horarios/4003H2.png",
        "L4_ida": "https://www.crtm.es/datos_lineas/horarios/4004H1.png",
        "L4_vuelta": "https://www.crtm.es/datos_lineas/horarios/4004H2.png",
        "L5_ida": "https://www.crtm.es/datos_lineas/horarios/4005H1.png",
        "L5_vuelta": "https://www.crtm.es/datos_lineas/horarios/4005H2.png",
        "L6_ida": "https://www.crtm.es/datos_lineas/horarios/4006H1.png",
        "L6_vuelta": "https://www.crtm.es/datos_lineas/horarios/4006H2.png",
        "L7_ida": "https://www.crtm.es/datos_lineas/horarios/4007H1.png",
        "L7_vuelta": "https://www.crtm.es/datos_lineas/horarios/4007H2.png",
        "L8_ida": "https://www.crtm.es/datos_lineas/horarios/4008H1.png",
        "L8_vuelta": "https://www.crtm.es/datos_lineas/horarios/4008H2.png",
        "L9_ida": "https://www.crtm.es/datos_lineas/horarios/4009H1.png",
        "L9_vuelta": "https://www.crtm.es/datos_lineas/horarios/4009H2.png",
        "L10_ida": "https://www.crtm.es/datos_lineas/horarios/4010H1.png",
        "L10_vuelta": "https://www.crtm.es/datos_lineas/horarios/4010H2.png",
        "L11_ida": "https://www.crtm.es/datos_lineas/horarios/4011H1.png",
        "L11_vuelta": "https://www.crtm.es/datos_lineas/horarios/4011H2.png",
        "L12_ida": "https://www.crtm.es/datos_lineas/horarios/4012H1.png",
        "L12_vuelta": "https://www.crtm.es/datos_lineas/horarios/4012H2.png"
    }
    
    print(f"🚇 Descargando {len(schedules)} horarios en la carpeta '{output_dir}'...")
    
    # Barra de progreso
    with tqdm(total=len(schedules), desc="Descargando horarios", unit="archivo") as pbar:
        for name, url in schedules.items():
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                # Nombre del archivo
                filename = os.path.join(output_dir, f"horario_{name}.png")
                
                # Guardar el archivo
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                pbar.set_postfix_str(f"✅ {name}")
                
            except requests.exceptions.RequestException as e:
                pbar.set_postfix_str(f"❌ Error en {name}: {e}")
            
            pbar.update(1)
            
    print("\n✅ Descarga de horarios completada.")

if __name__ == "__main__":
    download_schedules() 