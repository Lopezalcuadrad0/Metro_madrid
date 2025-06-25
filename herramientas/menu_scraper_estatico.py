#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from datetime import datetime

def mostrar_menu():
    """Muestra el menú de opciones"""
    print("\n" + "="*60)
    print("🔧 SCRAPER ESTÁTICO - METRO DE MADRID")
    print("="*60)
    print("Este script ejecuta el scraper de datos detallados de estaciones")
    print("(dirección, accesos, servicios, vestíbulos, etc.)")
    print()
    print("⚠️  ADVERTENCIA: Este proceso puede tardar varios minutos")
    print("💡 Solo ejecuta esto cuando quieras actualizar los datos estáticos")
    print()
    print("Opciones:")
    print("  1. Ejecutar scraper completo (todas las estaciones)")
    print("  2. Ejecutar scraper para estaciones específicas")
    print("  3. Verificar estado actual de la base de datos")
    print("  4. Generar CSV de datos clave")
    print("  5. Salir")
    print()

def ejecutar_scraper_completo():
    """Ejecuta el scraper completo para todas las estaciones"""
    print("\n🚀 EJECUTANDO SCRAPER COMPLETO")
    print("="*40)
    
    try:
        # Verificar que existe el script
        script_path = "scraper_datos_detallados.py"
        if not os.path.exists(script_path):
            print(f"❌ No se encontró el script: {script_path}")
            return False
        
        print("⏳ Iniciando scraper...")
        print("💡 Esto puede tardar varios minutos...")
        
        # Ejecutar el script
        resultado = subprocess.run([sys.executable, script_path], 
                                 capture_output=True, text=True, timeout=3600)  # 1 hora timeout
        
        if resultado.returncode == 0:
            print("✅ Scraper completado exitosamente")
            print("📄 Salida del scraper:")
            print(resultado.stdout)
            return True
        else:
            print("❌ Error ejecutando scraper")
            print("📄 Error del scraper:")
            print(resultado.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ El scraper tardó demasiado tiempo (más de 1 hora)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def ejecutar_scraper_especifico():
    """Ejecuta el scraper para estaciones específicas"""
    print("\n🎯 SCRAPER PARA ESTACIONES ESPECÍFICAS")
    print("="*40)
    
    # Solicitar estaciones
    print("Introduce los nombres de las estaciones (separados por comas):")
    estaciones_input = input("Estaciones: ").strip()
    
    if not estaciones_input:
        print("❌ No se introdujeron estaciones")
        return False
    
    estaciones = [e.strip() for e in estaciones_input.split(',')]
    print(f"Estaciones a procesar: {', '.join(estaciones)}")
    
    try:
        # Verificar que existe el script
        script_path = "scraper_datos_detallados.py"
        if not os.path.exists(script_path):
            print(f"❌ No se encontró el script: {script_path}")
            return False
        
        print("⏳ Iniciando scraper para estaciones específicas...")
        
        # Ejecutar el script con las estaciones específicas
        comando = [sys.executable, script_path] + estaciones
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if resultado.returncode == 0:
            print("✅ Scraper completado exitosamente")
            print("📄 Salida del scraper:")
            print(resultado.stdout)
            return True
        else:
            print("❌ Error ejecutando scraper")
            print("📄 Error del scraper:")
            print(resultado.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ El scraper tardó demasiado tiempo (más de 30 minutos)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verificar_estado_bd():
    """Verifica el estado actual de la base de datos"""
    print("\n📊 VERIFICANDO ESTADO DE BASE DE DATOS")
    print("="*40)
    
    try:
        # Ejecutar script de verificación
        script_path = "verificar_bd_actualizada.py"
        if not os.path.exists(script_path):
            print(f"❌ No se encontró el script: {script_path}")
            return False
        
        resultado = subprocess.run([sys.executable, script_path], 
                                 capture_output=True, text=True, timeout=60)
        
        if resultado.returncode == 0:
            print("📄 Estado de la base de datos:")
            print(resultado.stdout)
            return True
        else:
            print("❌ Error verificando base de datos")
            print(resultado.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def generar_csv_datos_clave():
    """Genera el CSV de datos clave"""
    print("\n📄 GENERANDO CSV DE DATOS CLAVE")
    print("="*40)
    
    try:
        # Verificar que existe el script
        script_path = "generar_csv_datos_clave.py"
        if not os.path.exists(script_path):
            print(f"❌ No se encontró el script: {script_path}")
            return False
        
        print("⏳ Generando CSV...")
        
        resultado = subprocess.run([sys.executable, script_path], 
                                 capture_output=True, text=True, timeout=300)  # 5 min timeout
        
        if resultado.returncode == 0:
            print("✅ CSV generado exitosamente")
            print("📄 Salida del generador:")
            print(resultado.stdout)
            return True
        else:
            print("❌ Error generando CSV")
            print("📄 Error del generador:")
            print(resultado.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ El generador tardó demasiado tiempo")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    while True:
        mostrar_menu()
        
        try:
            opcion = input("Selecciona una opción (1-5): ").strip()
            
            if opcion == "1":
                confirmacion = input("¿Estás seguro de que quieres ejecutar el scraper completo? (s/N): ").strip().lower()
                if confirmacion in ['s', 'si', 'sí', 'y', 'yes']:
                    ejecutar_scraper_completo()
                else:
                    print("❌ Operación cancelada")
                    
            elif opcion == "2":
                ejecutar_scraper_especifico()
                
            elif opcion == "3":
                verificar_estado_bd()
                
            elif opcion == "4":
                generar_csv_datos_clave()
                
            elif opcion == "5":
                print("👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción no válida. Introduce un número del 1 al 5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Operación cancelada por el usuario")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
        
        # Pausa antes de mostrar el menú de nuevo
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main() 