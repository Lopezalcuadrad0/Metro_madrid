#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de inicio simplificado para el Sistema del Metro de Madrid
Usa la nueva estructura organizada del proyecto
"""

import os
import sys
import subprocess
from pathlib import Path

def mostrar_menu():
    """Muestra el menú principal del sistema"""
    print("=" * 60)
    print("SISTEMA DEL METRO DE MADRID")
    print("=" * 60)
    print("1. Iniciar aplicacion web")
    print("2. Generar CSV de datos clave")
    print("3. Ejecutar scraper estatico (datos detallados)")
    print("4. Diagnosticar base de datos")
    print("5. Forzar actualizacion completa")
    print("6. Verificar sistema completo")
    print("7. Menu de herramientas avanzadas")
    print("0. Salir")
    print("=" * 60)

def ejecutar_comando(comando, descripcion):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\nEjecutando: {descripcion}...")
    print("-" * 40)
    
    try:
        # Usar encoding específico para Windows
        resultado = subprocess.run(
            comando, 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='cp1252',  # Codificación de Windows
            errors='replace'    # Reemplazar caracteres problemáticos
        )
        
        if resultado.stdout:
            print("Salida:")
            print(resultado.stdout)
        
        if resultado.stderr:
            print("Errores:")
            print(resultado.stderr)
            
        if resultado.returncode == 0:
            print(f"OK: {descripcion} completado exitosamente")
        else:
            print(f"ERROR en {descripcion}")
            
    except Exception as e:
        print(f"ERROR ejecutando {descripcion}: {e}")
    
    input("\nPresiona Enter para continuar...")

def menu_herramientas_avanzadas():
    """Menú de herramientas avanzadas"""
    while True:
        print("\n" + "=" * 50)
        print("HERRAMIENTAS AVANZADAS")
        print("=" * 50)
        print("1. Completar datos faltantes")
        print("2. Verificar modal IDs")
        print("3. Actualizar tabla de estado de estaciones")
        print("4. Volver al menu principal")
        print("=" * 50)
        
        opcion = input("Selecciona una opcion: ").strip()
        
        if opcion == "1":
            ejecutar_comando("python herramientas/completar_datos_faltantes.py", 
                           "Completando datos faltantes")
        elif opcion == "2":
            ejecutar_comando("python herramientas/verify_all_modal_ids.py", 
                           "Verificando modal IDs")
        elif opcion == "3":
            ejecutar_comando("python herramientas/update_station_status_table.py", 
                           "Actualizando tabla de estado")
        elif opcion == "4":
            break
        else:
            print("ERROR: Opcion no valida")

def main():
    """Función principal"""
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("app.py"):
        print("ERROR: No se encuentra app.py")
        print("Asegurate de ejecutar este script desde el directorio raiz del proyecto")
        return
    
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opcion: ").strip()
        
        if opcion == "1":
            print("\nIniciando aplicacion web...")
            print("La aplicacion estara disponible en: http://localhost:5000")
            print("Presiona Ctrl+C para detener la aplicacion")
            print("-" * 40)
            
            try:
                subprocess.run([sys.executable, "app.py"])
            except KeyboardInterrupt:
                print("\nAplicacion detenida")
            except Exception as e:
                print(f"ERROR iniciando la aplicacion: {e}")
                
        elif opcion == "2":
            ejecutar_comando("python herramientas/generar_csv_datos_clave.py", 
                           "Generando CSV de datos clave")
            
        elif opcion == "3":
            ejecutar_comando("python herramientas/menu_scraper_estatico.py", 
                           "Ejecutando scraper estatico")
            
        elif opcion == "4":
            ejecutar_comando("python herramientas/diagnostico_datos.py", 
                           "Diagnosticando base de datos")
            
        elif opcion == "5":
            print("\nADVERTENCIA: Esta operacion puede tardar varios minutos")
            confirmacion = input("Estas seguro de que quieres continuar? (s/N): ").strip().lower()
            if confirmacion in ['s', 'si', 'sí', 'y', 'yes']:
                ejecutar_comando("python herramientas/forzar_actualizacion_completa.py", 
                               "Forzando actualizacion completa")
            else:
                print("Operacion cancelada")
                
        elif opcion == "6":
            ejecutar_comando("python herramientas/verificar_sistema_completo.py", 
                           "Verificando sistema completo")
            
        elif opcion == "7":
            menu_herramientas_avanzadas()
            
        elif opcion == "0":
            print("\nHasta luego!")
            break
            
        else:
            print("ERROR: Opcion no valida")
            input("Presiona Enter para continuar...")

if __name__ == "__main__":
    main() 