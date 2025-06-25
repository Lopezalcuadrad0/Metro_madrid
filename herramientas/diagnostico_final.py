import sqlite3

# --- Diagnóstico de la Base de Datos Relacional ---

DB_PATH = 'db/estaciones_relacional.db'

print(f"--- Iniciando diagnóstico de '{DB_PATH}' ---")

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("✅ Conexión a la base de datos exitosa.")
except sqlite3.Error as e:
    print(f"❌ ERROR: No se pudo conectar a la base de datos: {e}")
    exit()

# 1. Verificar si la tabla 'estaciones' existe y tiene datos
try:
    cursor.execute("SELECT COUNT(*) FROM estaciones")
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"✅ La tabla 'estaciones' existe y contiene {count} filas.")
    else:
        print("❌ ERROR: La tabla 'estaciones' existe pero está vacía.")
        conn.close()
        exit()
except sqlite3.Error:
    print("❌ ERROR: La tabla 'estaciones' no existe en la base de datos.")
    conn.close()
    exit()

# 2. Verificar si las columnas de coordenadas existen
try:
    cursor.execute("PRAGMA table_info(estaciones)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'latitud' in columns and 'longitud' in columns:
        print("✅ Las columnas 'latitud' y 'longitud' existen.")
    else:
        print("❌ ERROR: Faltan las columnas 'latitud' y/o 'longitud'.")
        conn.close()
        exit()
except sqlite3.Error as e:
    print(f"❌ ERROR: No se pudo verificar la estructura de la tabla: {e}")
    conn.close()
    exit()

# 3. Muestrear algunos nombres de la base de datos
print("\n--- Muestreo de 10 nombres de la tabla 'estaciones' ---")
try:
    cursor.execute("SELECT nombre FROM estaciones LIMIT 10")
    sample_names = cursor.fetchall()
    for name in sample_names:
        print(f"  -> '{name[0]}'")
except sqlite3.Error as e:
    print(f"❌ ERROR al muestrear nombres: {e}")

# 4. Verificar el contenido de las coordenadas para estaciones clave
print("\n--- Verificando coordenadas de estaciones clave ---")
estaciones_clave = ['Sol', 'Nuevos Ministerios', 'Plaza de Castilla', 'Avenida de América', 'Legazpi']
encontradas_con_coords = 0

for estacion in estaciones_clave:
    cursor.execute("SELECT nombre, latitud, longitud FROM estaciones WHERE nombre = ?", (estacion,))
    resultado = cursor.fetchone()
    if resultado:
        nombre, lat, lon = resultado
        if lat is not None and lon is not None:
            print(f"  -> ✅ '{nombre}': Coordenadas encontradas ({lat}, {lon})")
            encontradas_con_coords += 1
        else:
            print(f"  -> ❌ '{nombre}': Las coordenadas son NULAS.")
    else:
        print(f"  -> ⚠️ '{estacion}' no encontrada en la base de datos.")

if encontradas_con_coords == len(estaciones_clave):
    print("\n✅ Diagnóstico preliminar: Las coordenadas parecen estar correctamente en la BD.")
else:
    print("\n❌ Diagnóstico preliminar: Hay un problema con los datos de coordenadas en la BD.")

conn.close()
print("\n--- Diagnóstico finalizado ---") 