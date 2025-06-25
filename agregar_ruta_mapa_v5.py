#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def agregar_ruta_mapa_v5():
    """Agrega la ruta para el mapa interactivo v5.0 al app.py"""
    
    codigo_nuevo = '''

@app.route('/mapa-v5')
def mapa_interactivo_v5():
    """Mapa interactivo del Metro Madrid v5.0"""
    return render_template('mapa_rutas_v5.html')

@app.route('/mapa-metro')
def mapa_metro_publico():
    """Acceso público al mapa interactivo"""
    return render_template('mapa_rutas_v5.html')

@app.route('/metro-mapa')
def metro_mapa_directo():
    """Ruta directa al mapa del metro"""
    return render_template('mapa_rutas_v5.html')

'''
    
    print("📝 Agregando rutas del mapa v5.0 al archivo app.py...")
    
    # Leer archivo actual
    with open('app.py', 'r', encoding='utf-8') as f:
        contenido_actual = f.read()
    
    # Verificar si ya existe
    if 'mapa_interactivo_v5' in contenido_actual:
        print("⚠️  Rutas del mapa v5.0 ya existen en app.py")
        return False
    
    # Encontrar donde agregar (antes de la API v5.0)
    if '# API v5.0 - SISTEMA AVANZADO DE RUTAS' in contenido_actual:
        # Insertar antes de la API v5.0
        partes = contenido_actual.split('# ============================================================================\n# API v5.0 - SISTEMA AVANZADO DE RUTAS')
        nuevo_contenido = partes[0] + codigo_nuevo + '\n# ============================================================================\n# API v5.0 - SISTEMA AVANZADO DE RUTAS' + partes[1]
    else:
        # Agregar al final si no encuentra la API v5.0
        nuevo_contenido = contenido_actual + codigo_nuevo
    
    # Escribir archivo actualizado
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(nuevo_contenido)
    
    print("✅ Rutas del mapa v5.0 agregadas exitosamente!")
    print("\n🗺️ Rutas disponibles:")
    print("   • /mapa-v5")
    print("   • /mapa-metro") 
    print("   • /metro-mapa")
    
    return True

if __name__ == '__main__':
    agregar_ruta_mapa_v5() 