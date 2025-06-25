#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CREAR TABLAS FIJAS - Metro de Madrid
====================================

Crea 13 tablas fijas (una por línea) con estructura inmutable:
- Nombres y IDs no se pueden cambiar
- Límites establecidos por línea
- Solo se actualizan datos adicionales
"""

import sqlite3
import csv
import os
from datetime import datetime
import unicodedata
import re

# Configuración
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'estaciones_fijas_v2.db')

# Estructura fija de estaciones por línea (inmutable)
ESTACIONES_FIJAS = {
    '1': [
        {'id': 153, 'nombre': 'Pinar de Chamartín', 'orden': 1},
        {'id': 152, 'nombre': 'Bambú', 'orden': 2},
        {'id': 151, 'nombre': 'Chamartín', 'orden': 3},
        {'id': 101, 'nombre': 'Plaza de Castilla', 'orden': 4},
        {'id': 150, 'nombre': 'Valdeacederas', 'orden': 5},
        {'id': 149, 'nombre': 'Tetuán', 'orden': 6},
        {'id': 148, 'nombre': 'Estrecho', 'orden': 7},
        {'id': 147, 'nombre': 'Alvarado', 'orden': 8},
        {'id': 109, 'nombre': 'Cuatro Caminos', 'orden': 9},
        {'id': 110, 'nombre': 'Ríos Rosas', 'orden': 10},
        {'id': 111, 'nombre': 'Iglesia', 'orden': 11},
        {'id': 113, 'nombre': 'Bilbao', 'orden': 12},
        {'id': 114, 'nombre': 'Tribunal', 'orden': 13},
        {'id': 111, 'nombre': 'Gran Vía', 'orden': 14},
        {'id': 115, 'nombre': 'Sol', 'orden': 15},
        {'id': 116, 'nombre': 'Tirso de Molina', 'orden': 16},
        {'id': 117, 'nombre': 'Antón Martín', 'orden': 17},
        {'id': 118, 'nombre': 'Estación del Arte', 'orden': 18},
        {'id': 119, 'nombre': 'Menéndez Pelayo', 'orden': 19},
        {'id': 120, 'nombre': 'Pacífico', 'orden': 20},
        {'id': 121, 'nombre': 'Puente de Vallecas', 'orden': 21},
        {'id': 122, 'nombre': 'Nueva Numancia', 'orden': 22},
        {'id': 123, 'nombre': 'Portazgo', 'orden': 23},
        {'id': 124, 'nombre': 'Buenos Aires', 'orden': 24},
        {'id': 125, 'nombre': 'Alto del Arenal', 'orden': 25},
        {'id': 126, 'nombre': 'Miguel Hernández', 'orden': 26},
        {'id': 127, 'nombre': 'Sierra de Guadalupe', 'orden': 27},
        {'id': 128, 'nombre': 'Villa de Vallecas', 'orden': 28},
        {'id': 129, 'nombre': 'Congosto', 'orden': 29},
        {'id': 130, 'nombre': 'La Gavia', 'orden': 30},
        {'id': 131, 'nombre': 'Las Suertes', 'orden': 31},
        {'id': 130, 'nombre': 'Valdecarros', 'orden': 32}
    ],
    '2': [
        {'id': 220, 'nombre': 'Las Rosas', 'orden': 1},
        {'id': 219, 'nombre': 'Avenida de Guadalajara', 'orden': 2},
        {'id': 218, 'nombre': 'Alsacia', 'orden': 3},
        {'id': 217, 'nombre': 'La Almudena', 'orden': 4},
        {'id': 216, 'nombre': 'La Elipa', 'orden': 5},
        {'id': 213, 'nombre': 'Ventas', 'orden': 6},
        {'id': 212, 'nombre': 'Manuel Becerra', 'orden': 7},
        {'id': 211, 'nombre': 'Goya', 'orden': 8},
        {'id': 209, 'nombre': 'Príncipe de Vergara', 'orden': 9},
        {'id': 207, 'nombre': 'Retiro', 'orden': 10},
        {'id': 206, 'nombre': 'Banco de España', 'orden': 11},
        {'id': 205, 'nombre': 'Sevilla', 'orden': 12},
        {'id': 115, 'nombre': 'Sol', 'orden': 13},
        {'id': 208, 'nombre': 'Ópera', 'orden': 14},
        {'id': 203, 'nombre': 'Santo Domingo', 'orden': 15},
        {'id': 202, 'nombre': 'Noviciado', 'orden': 16},
        {'id': 201, 'nombre': 'San Bernardo', 'orden': 17},
        {'id': 210, 'nombre': 'Quevedo', 'orden': 18},
        {'id': 214, 'nombre': 'Canal', 'orden': 19},
        {'id': 220, 'nombre': 'Cuatro Caminos', 'orden': 20}
    ],
    '3': [
        {'id': 307, 'nombre': 'Villaverde Alto', 'orden': 1},
        {'id': 306, 'nombre': 'San Cristóbal', 'orden': 2},
        {'id': 305, 'nombre': 'Villaverde Bajo Cruce', 'orden': 3},
        {'id': 304, 'nombre': 'Ciudad de los Ángeles', 'orden': 4},
        {'id': 303, 'nombre': 'San Fermín – Orcasur', 'orden': 5},
        {'id': 302, 'nombre': 'Hospital 12 de Octubre', 'orden': 6},
        {'id': 301, 'nombre': 'Almendrales', 'orden': 7},
        {'id': 317, 'nombre': 'Legazpi', 'orden': 8},
        {'id': 104, 'nombre': 'Delicias', 'orden': 9},
        {'id': 312, 'nombre': 'Palos de la Frontera', 'orden': 10},
        {'id': 313, 'nombre': 'Embajadores', 'orden': 11},
        {'id': 109, 'nombre': 'Lavapiés', 'orden': 12},
        {'id': 115, 'nombre': 'Sol', 'orden': 13},
        {'id': 311, 'nombre': 'Callao', 'orden': 14},
        {'id': 308, 'nombre': 'Plaza de España', 'orden': 15},
        {'id': 307, 'nombre': 'Ventura Rodríguez', 'orden': 16},
        {'id': 401, 'nombre': 'Argüelles', 'orden': 17},
        {'id': 626, 'nombre': 'Moncloa', 'orden': 18}
    ],
    '4': [
        {'id': 428, 'nombre': 'Argüelles', 'orden': 1},
        {'id': 214, 'nombre': 'San Bernardo', 'orden': 2},
        {'id': 113, 'nombre': 'Bilbao', 'orden': 3},
        {'id': 404, 'nombre': 'Alonso Martínez', 'orden': 4},
        {'id': 403, 'nombre': 'Colón', 'orden': 5},
        {'id': 402, 'nombre': 'Serrano', 'orden': 6},
        {'id': 401, 'nombre': 'Velázquez', 'orden': 7},
        {'id': 211, 'nombre': 'Goya', 'orden': 8},
        {'id': 406, 'nombre': 'Lista', 'orden': 9},
        {'id': 410, 'nombre': 'Diego de León', 'orden': 10},
        {'id': 411, 'nombre': 'Avenida de América', 'orden': 11},
        {'id': 408, 'nombre': 'Prosperidad', 'orden': 12},
        {'id': 409, 'nombre': 'Alfonso XIII', 'orden': 13},
        {'id': 412, 'nombre': 'Avenida de la Paz', 'orden': 14},
        {'id': 413, 'nombre': 'Arturo Soria', 'orden': 15},
        {'id': 414, 'nombre': 'Esperanza', 'orden': 16},
        {'id': 415, 'nombre': 'Canillas', 'orden': 17},
        {'id': 418, 'nombre': 'Mar de Cristal', 'orden': 18},
        {'id': 416, 'nombre': 'San Lorenzo', 'orden': 19},
        {'id': 417, 'nombre': 'Parque de Santa María', 'orden': 20},
        {'id': 419, 'nombre': 'Hortaleza', 'orden': 21},
        {'id': 420, 'nombre': 'Manoteras', 'orden': 22},
        {'id': 153, 'nombre': 'Pinar de Chamartín', 'orden': 23}
    ],
    '5': [
        {'id': 521, 'nombre': 'Alameda de Osuna', 'orden': 1},
        {'id': 520, 'nombre': 'El Capricho', 'orden': 2},
        {'id': 519, 'nombre': 'Canillejas', 'orden': 3},
        {'id': 518, 'nombre': 'Torre Arias', 'orden': 4},
        {'id': 517, 'nombre': 'Suanzes', 'orden': 5},
        {'id': 516, 'nombre': 'Ciudad Lineal', 'orden': 6},
        {'id': 505, 'nombre': 'Pueblo Nuevo', 'orden': 7},
        {'id': 514, 'nombre': 'Quintana', 'orden': 8},
        {'id': 513, 'nombre': 'El Carmen', 'orden': 9},
        {'id': 213, 'nombre': 'Ventas', 'orden': 10},
        {'id': 409, 'nombre': 'Diego de León', 'orden': 11},
        {'id': 510, 'nombre': 'Núñez de Balboa', 'orden': 12},
        {'id': 507, 'nombre': 'Rubén Darío', 'orden': 13},
        {'id': 408, 'nombre': 'Alonso Martínez', 'orden': 14},
        {'id': 506, 'nombre': 'Chueca', 'orden': 15},
        {'id': 115, 'nombre': 'Gran Vía', 'orden': 16},
        {'id': 310, 'nombre': 'Callao', 'orden': 17},
        {'id': 208, 'nombre': 'Ópera', 'orden': 18},
        {'id': 505, 'nombre': 'La Latina', 'orden': 19},
        {'id': 502, 'nombre': 'Puerta de Toledo', 'orden': 20},
        {'id': 501, 'nombre': 'Acacias', 'orden': 21},
        {'id': 510, 'nombre': 'Pirámides', 'orden': 22},
        {'id': 512, 'nombre': 'Marqués de Vadillo', 'orden': 23},
        {'id': 511, 'nombre': 'Urgel', 'orden': 24},
        {'id': 529, 'nombre': 'Oporto', 'orden': 25},
        {'id': 528, 'nombre': 'Vista Alegre', 'orden': 26},
        {'id': 527, 'nombre': 'Carabanchel', 'orden': 27},
        {'id': 526, 'nombre': 'Eugenia de Montijo', 'orden': 28},
        {'id': 525, 'nombre': 'Aluche', 'orden': 29},
        {'id': 524, 'nombre': 'Empalme', 'orden': 30},
        {'id': 523, 'nombre': 'Campamento', 'orden': 31},
        {'id': 530, 'nombre': 'Casa de Campo', 'orden': 32}
    ],
    '6': [
        {'id': 615, 'nombre': 'Laguna', 'orden': 1},
        {'id': 614, 'nombre': 'Carpetana', 'orden': 2},
        {'id': 529, 'nombre': 'Oporto', 'orden': 3},
        {'id': 616, 'nombre': 'Opañel', 'orden': 4},
        {'id': 617, 'nombre': 'Plaza Elíptica', 'orden': 5},
        {'id': 619, 'nombre': 'Usera', 'orden': 6},
        {'id': 315, 'nombre': 'Legazpi', 'orden': 7},
        {'id': 623, 'nombre': 'Arganzuela – Planetario', 'orden': 8},
        {'id': 622, 'nombre': 'Méndez Álvaro', 'orden': 9},
        {'id': 120, 'nombre': 'Pacífico', 'orden': 10},
        {'id': 624, 'nombre': 'Conde de Casal', 'orden': 11},
        {'id': 613, 'nombre': 'Sainz de Baranda', 'orden': 12},
        {'id': 611, 'nombre': 'O\'Donnell', 'orden': 13},
        {'id': 212, 'nombre': 'Manuel Becerra', 'orden': 14},
        {'id': 410, 'nombre': 'Diego de León', 'orden': 15},
        {'id': 411, 'nombre': 'Avenida de América', 'orden': 16},
        {'id': 607, 'nombre': 'República Argentina', 'orden': 17},
        {'id': 618, 'nombre': 'Nuevos Ministerios', 'orden': 18},
        {'id': 110, 'nombre': 'Cuatro Caminos', 'orden': 19},
        {'id': 620, 'nombre': 'Guzmán el Bueno', 'orden': 20},
        {'id': 621, 'nombre': 'Vicente Aleixandre', 'orden': 21},
        {'id': 626, 'nombre': 'Ciudad Universitaria', 'orden': 22},
        {'id': 626, 'nombre': 'Moncloa', 'orden': 23},
        {'id': 428, 'nombre': 'Argüelles', 'orden': 24},
        {'id': 625, 'nombre': 'Príncipe Pío', 'orden': 25},
        {'id': 623, 'nombre': 'Puerta del Ángel', 'orden': 26},
        {'id': 627, 'nombre': 'Alto de Extremadura', 'orden': 27},
        {'id': 628, 'nombre': 'Lucero', 'orden': 28}
    ],
    '7': [
        {'id': 760, 'nombre': 'Hospital del Henares', 'orden': 1},
        {'id': 759, 'nombre': 'Henares', 'orden': 2},
        {'id': 758, 'nombre': 'Jarama', 'orden': 3},
        {'id': 757, 'nombre': 'San Fernando', 'orden': 4},
        {'id': 756, 'nombre': 'La Rambla', 'orden': 5},
        {'id': 755, 'nombre': 'Coslada Central', 'orden': 6},
        {'id': 754, 'nombre': 'Barrio del Puerto', 'orden': 7},
        {'id': 751, 'nombre': 'Estadio Metropolitano', 'orden': 8},
        {'id': 701, 'nombre': 'Las Musas', 'orden': 9},
        {'id': 702, 'nombre': 'San Blas', 'orden': 10},
        {'id': 703, 'nombre': 'Simancas', 'orden': 11},
        {'id': 704, 'nombre': 'García Noblejas', 'orden': 12},
        {'id': 705, 'nombre': 'Ascao', 'orden': 13},
        {'id': 505, 'nombre': 'Pueblo Nuevo', 'orden': 14},
        {'id': 707, 'nombre': 'Barrio de la Concepción', 'orden': 15},
        {'id': 708, 'nombre': 'Parque de las Avenidas', 'orden': 16},
        {'id': 709, 'nombre': 'Cartagena', 'orden': 17},
        {'id': 411, 'nombre': 'Avenida de América', 'orden': 18},
        {'id': 711, 'nombre': 'Gregorio Marañón', 'orden': 19},
        {'id': 712, 'nombre': 'Alonso Cano', 'orden': 20},
        {'id': 214, 'nombre': 'Canal', 'orden': 21},
        {'id': 714, 'nombre': 'Islas Filipinas', 'orden': 22},
        {'id': 620, 'nombre': 'Guzmán el Bueno', 'orden': 23},
        {'id': 716, 'nombre': 'Francos Rodríguez', 'orden': 24},
        {'id': 717, 'nombre': 'Valdezarza', 'orden': 25},
        {'id': 718, 'nombre': 'Antonio Machado', 'orden': 26},
        {'id': 719, 'nombre': 'Peñagrande', 'orden': 27},
        {'id': 720, 'nombre': 'Avenida de la Ilustración', 'orden': 28},
        {'id': 721, 'nombre': 'Lacoma', 'orden': 29},
        {'id': 722, 'nombre': 'Arroyofresno', 'orden': 30},
        {'id': 723, 'nombre': 'Pitis', 'orden': 31}
    ],
    '8': [
        {'id': 618, 'nombre': 'Nuevos Ministerios', 'orden': 1},
        {'id': 802, 'nombre': 'Colombia', 'orden': 2},
        {'id': 803, 'nombre': 'Pinar del Rey', 'orden': 3},
        {'id': 418, 'nombre': 'Mar de Cristal', 'orden': 4},
        {'id': 805, 'nombre': 'Feria de Madrid', 'orden': 5},
        {'id': 806, 'nombre': 'Aeropuerto T1-T2-T3', 'orden': 6},
        {'id': 807, 'nombre': 'Barajas', 'orden': 7},
        {'id': 808, 'nombre': 'Aeropuerto T4', 'orden': 8}
    ],
    '9': [
        {'id': 952, 'nombre': 'Paco de Lucía', 'orden': 1},
        {'id': 951, 'nombre': 'Mirasierra', 'orden': 2},
        {'id': 901, 'nombre': 'Herrera Oria', 'orden': 3},
        {'id': 902, 'nombre': 'Barrio del Pilar', 'orden': 4},
        {'id': 903, 'nombre': 'Ventilla', 'orden': 5},
        {'id': 101, 'nombre': 'Plaza de Castilla', 'orden': 6},
        {'id': 905, 'nombre': 'Duque de Pastrana', 'orden': 7},
        {'id': 906, 'nombre': 'Pío XII', 'orden': 8},
        {'id': 802, 'nombre': 'Colombia', 'orden': 9},
        {'id': 908, 'nombre': 'Concha Espina', 'orden': 10},
        {'id': 909, 'nombre': 'Cruz del Rayo', 'orden': 11},
        {'id': 411, 'nombre': 'Avenida de América', 'orden': 12},
        {'id': 510, 'nombre': 'Núñez de Balboa', 'orden': 13},
        {'id': 204, 'nombre': 'Príncipe de Vergara', 'orden': 14},
        {'id': 913, 'nombre': 'Ibiza', 'orden': 15},
        {'id': 612, 'nombre': 'Sainz de Baranda', 'orden': 16},
        {'id': 915, 'nombre': 'Estrella', 'orden': 17},
        {'id': 916, 'nombre': 'Vinateros', 'orden': 18},
        {'id': 917, 'nombre': 'Artilleros', 'orden': 19},
        {'id': 918, 'nombre': 'Pavones', 'orden': 20},
        {'id': 919, 'nombre': 'Valdebernardo', 'orden': 21},
        {'id': 920, 'nombre': 'Vicálvaro', 'orden': 22},
        {'id': 921, 'nombre': 'San Cipriano', 'orden': 23},
        {'id': 922, 'nombre': 'Puerta de Arganda', 'orden': 24},
        {'id': 923, 'nombre': 'Rivas Urbanizaciones', 'orden': 25},
        {'id': 924, 'nombre': 'Rivas Futura', 'orden': 26},
        {'id': 925, 'nombre': 'Rivas Vaciamadrid', 'orden': 27},
        {'id': 926, 'nombre': 'La Poveda', 'orden': 28},
        {'id': 927, 'nombre': 'Arganda del Rey', 'orden': 29}
    ],
    '10': [
        {'id': 1061, 'nombre': 'Hospital Infanta Sofía', 'orden': 1},
        {'id': 1060, 'nombre': 'Reyes Católicos', 'orden': 2},
        {'id': 1059, 'nombre': 'Baunatal', 'orden': 3},
        {'id': 1058, 'nombre': 'Manuel de Falla', 'orden': 4},
        {'id': 1057, 'nombre': 'Marqués de la Valdavia', 'orden': 5},
        {'id': 1056, 'nombre': 'La Moraleja', 'orden': 6},
        {'id': 1055, 'nombre': 'La Granja', 'orden': 7},
        {'id': 1054, 'nombre': 'Ronda de la Comunicación', 'orden': 8},
        {'id': 1053, 'nombre': 'Las Tablas', 'orden': 9},
        {'id': 1052, 'nombre': 'Montecarmelo', 'orden': 10},
        {'id': 1051, 'nombre': 'Tres Olivos', 'orden': 11},
        {'id': 1001, 'nombre': 'Fuencarral', 'orden': 12},
        {'id': 1002, 'nombre': 'Begoña', 'orden': 13},
        {'id': 151, 'nombre': 'Chamartín', 'orden': 14},
        {'id': 101, 'nombre': 'Plaza de Castilla', 'orden': 15},
        {'id': 1005, 'nombre': 'Cuzco', 'orden': 16},
        {'id': 1006, 'nombre': 'Santiago Bernabéu', 'orden': 17},
        {'id': 618, 'nombre': 'Nuevos Ministerios', 'orden': 18},
        {'id': 711, 'nombre': 'Gregorio Marañón', 'orden': 19},
        {'id': 404, 'nombre': 'Alonso Martínez', 'orden': 20},
        {'id': 110, 'nombre': 'Tribunal', 'orden': 21},
        {'id': 308, 'nombre': 'Plaza de España', 'orden': 22},
        {'id': 625, 'nombre': 'Príncipe Pío', 'orden': 23},
        {'id': 1013, 'nombre': 'Lago', 'orden': 24},
        {'id': 1014, 'nombre': 'Batán', 'orden': 25},
        {'id': 530, 'nombre': 'Casa de Campo', 'orden': 26},
        {'id': 1016, 'nombre': 'Colonia Jardín', 'orden': 27},
        {'id': 1018, 'nombre': 'Aviación Española', 'orden': 28},
        {'id': 1019, 'nombre': 'Cuatro Vientos', 'orden': 29},
        {'id': 1020, 'nombre': 'Joaquín Vilumbrales', 'orden': 30},
        {'id': 1021, 'nombre': 'Puerta del Sur', 'orden': 31}
    ],
    '11': [
        {'id': 605, 'nombre': 'Plaza Elíptica', 'orden': 1},
        {'id': 1102, 'nombre': 'Abrantes', 'orden': 2},
        {'id': 1103, 'nombre': 'Pan Bendito', 'orden': 3},
        {'id': 1104, 'nombre': 'San Francisco', 'orden': 4},
        {'id': 1105, 'nombre': 'Carabanchel Alto', 'orden': 5},
        {'id': 1106, 'nombre': 'La Peseta', 'orden': 6},
        {'id': 1107, 'nombre': 'La Fortuna', 'orden': 7}
    ],
    '12': [
        {'id': 1201, 'nombre': 'Puerta del Sur', 'orden': 1},
        {'id': 1202, 'nombre': 'Parque Lisboa', 'orden': 2},
        {'id': 1203, 'nombre': 'Alcorcón Central', 'orden': 3},
        {'id': 1204, 'nombre': 'Parque Oeste', 'orden': 4},
        {'id': 1205, 'nombre': 'Universidad Rey Juan Carlos', 'orden': 5},
        {'id': 1206, 'nombre': 'Móstoles Central', 'orden': 6},
        {'id': 1207, 'nombre': 'Pradillo', 'orden': 7},
        {'id': 1208, 'nombre': 'Hospital de Móstoles', 'orden': 8},
        {'id': 1209, 'nombre': 'Manuela Malasaña', 'orden': 9},
        {'id': 1210, 'nombre': 'Loranca', 'orden': 10},
        {'id': 1211, 'nombre': 'Parque Europa', 'orden': 11},
        {'id': 1212, 'nombre': 'Hospital de Fuenlabrada', 'orden': 12},
        {'id': 1214, 'nombre': 'Fuenlabrada Central', 'orden': 13},
        {'id': 1215, 'nombre': 'Parque de los Estados', 'orden': 14},
        {'id': 1217, 'nombre': 'Arroyo Culebro', 'orden': 15},
        {'id': 1218, 'nombre': 'Conservatorio', 'orden': 16},
        {'id': 1219, 'nombre': 'Alonso de Mendoza', 'orden': 17},
        {'id': 1220, 'nombre': 'Getafe Central', 'orden': 18},
        {'id': 1221, 'nombre': 'Juan de la Cierva', 'orden': 19},
        {'id': 1222, 'nombre': 'El Casar', 'orden': 20},
        {'id': 1223, 'nombre': 'Los Espartales', 'orden': 21},
        {'id': 1224, 'nombre': 'El Bercial', 'orden': 22},
        {'id': 1225, 'nombre': 'El Carrascal', 'orden': 23},
        {'id': 1226, 'nombre': 'Julián Besteiro', 'orden': 24},
        {'id': 1227, 'nombre': 'Casa del Reloj', 'orden': 25},
        {'id': 1228, 'nombre': 'Hospital Severo Ochoa', 'orden': 26},
        {'id': 1229, 'nombre': 'Leganés Central', 'orden': 27},
        {'id': 1230, 'nombre': 'San Nicasio', 'orden': 28}
    ],
    'Ramal': [
        {'id': 209, 'nombre': 'Ópera', 'orden': 1},
        {'id': 625, 'nombre': 'Príncipe Pío', 'orden': 2}
    ]
}

def normalizar_nombre(nombre):
    """Normaliza un nombre para facilitar las comparaciones."""
    # Quitar acentos y caracteres especiales
    nfkd_form = unicodedata.normalize('NFKD', str(nombre))
    nombre = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Convertir a minúsculas y quitar espacios extra
    return nombre.lower().strip()

def crear_base_de_datos_relacional_desde_gtfs(db_path_relacional, db_path_gtfs):
    """
    Crea y puebla la base de datos relacional 'estaciones_relacional.db'
    a partir de los datos de la base de datos GTFS 'metro_madrid.db'.
    Esta función reconstruye la base de datos desde cero.
    """
    print(f"Iniciando la creación de '{db_path_relacional}' desde '{db_path_gtfs}'...")

    # --- 1. Eliminar la base de datos antigua si existe ---
    if os.path.exists(db_path_relacional):
        os.remove(db_path_relacional)
        print(f"Base de datos antigua '{db_path_relacional}' eliminada.")

    # --- 2. Conectar a las bases de datos ---
    try:
        conn_relacional = sqlite3.connect(db_path_relacional)
        cursor_relacional = conn_relacional.cursor()
        
        conn_gtfs = sqlite3.connect(db_path_gtfs)
        cursor_gtfs = conn_gtfs.cursor()
        print("Conexión a las bases de datos establecida.")
    except sqlite3.Error as e:
        print(f"Error al conectar con las bases de datos: {e}")
        return

    # --- 3. Crear la tabla 'estaciones' en la base de datos relacional ---
    try:
        cursor_relacional.execute('''
            CREATE TABLE estaciones (
                id_fijo INTEGER PRIMARY KEY AUTOINCREMENT,
                id_gtfs TEXT,
                nombre TEXT NOT NULL,
                linea TEXT NOT NULL,
                latitud REAL,
                longitud REAL,
                zona_tarifaria TEXT,
                accesible INTEGER,
                orden_en_linea INTEGER,
                url TEXT,
                id_modal INTEGER,
                ultima_actualizacion TEXT
            )
        ''')
        print("Tabla 'estaciones' creada en la base de datos relacional.")
    except sqlite3.Error as e:
        print(f"Error al crear la tabla 'estaciones': {e}")
        conn_relacional.close()
        conn_gtfs.close()
        return

    # --- 4. Leer datos de GTFS ---
    try:
        # Obtener todas las rutas para mapear route_id a route_short_name (e.g., L1 -> 1)
        cursor_gtfs.execute('SELECT route_id, route_short_name FROM routes')
        routes = {row[0]: row[1] for row in cursor_gtfs.fetchall()}
        
        # Obtener todas las paradas (stops) y sus viajes (trips) para deducir la línea
        # Usamos stop_times para conectar stops con trips, y trips con routes
        query_stops = """
            SELECT DISTINCT
                s.stop_id,
                s.stop_name,
                s.stop_lat,
                s.stop_lon,
                s.zone_id,
                s.wheelchair_boarding,
                t.route_id,
                st.stop_sequence
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id
            JOIN trips t ON st.trip_id = t.trip_id
            WHERE s.location_type = 0 OR s.location_type = 1
        """
        cursor_gtfs.execute(query_stops)
        paradas_gtfs = cursor_gtfs.fetchall()
        print(f"Se han leído {len(paradas_gtfs)} registros de paradas con sus líneas desde GTFS.")

    except sqlite3.Error as e:
        print(f"Error al leer datos de GTFS: {e}")
        conn_gtfs.close()
        conn_relacional.close()
        return

    # --- 5. Poblar la tabla 'estaciones' ---
    estaciones_insertadas = set()
    for parada in paradas_gtfs:
        stop_id, stop_name, stop_lat, stop_lon, zone_id, wheelchair_boarding, route_id, stop_sequence = parada
        
        # Mapear route_id a nombre de línea (ej: 'L1' -> 'linea_1')
        linea_short_name = routes.get(route_id, "Desconocida")
        
        # Simplificar el nombre de la línea para agrupar A/B (e.g., '7A' -> '7')
        match = re.match(r'(\d+)', linea_short_name)
        if match:
            linea_base = match.group(1)
        else:
            linea_base = linea_short_name  # Para casos como 'Ramal'

        linea_db_format = f"linea_{linea_base}"

        # Usar una tupla de nombre normalizado y línea para evitar duplicados
        identificador_unico = (normalizar_nombre(stop_name), linea_db_format)
        
        if identificador_unico not in estaciones_insertadas:
            try:
                cursor_relacional.execute('''
                    INSERT INTO estaciones (
                        id_gtfs, nombre, linea, latitud, longitud, 
                        zona_tarifaria, accesible, orden_en_linea
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stop_id,
                    stop_name,
                    linea_db_format,
                    stop_lat,
                    stop_lon,
                    zone_id,
                    wheelchair_boarding,
                    stop_sequence
                ))
                estaciones_insertadas.add(identificador_unico)
            except sqlite3.Error as e:
                print(f"Error insertando la estación '{stop_name}' para la línea '{linea_db_format}': {e}")

    # --- 6. Confirmar cambios y cerrar conexiones ---
    conn_relacional.commit()
    print(f"Proceso completado. Se han insertado {len(estaciones_insertadas)} estaciones únicas en la base de datos.")

    conn_gtfs.close()
    conn_relacional.close()

def crear_tabla_linea(cursor, linea):
    """Crea una tabla para una línea específica con estructura fija"""
    tabla_nombre = f'linea_{linea}'
    
    # Crear tabla con estructura fija y campos detallados
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {tabla_nombre} (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            orden_en_linea INTEGER NOT NULL,
            url TEXT,
            
            -- Información básica
            zona_tarifaria TEXT DEFAULT 'A',
            
            -- Servicios con iconos
            estacion_accesible TEXT DEFAULT '',
            ascensores TEXT DEFAULT '',
            escaleras_mecanicas TEXT DEFAULT '',
            desfibrilador TEXT DEFAULT '',
            cobertura_movil TEXT DEFAULT '',
            bibliometro TEXT DEFAULT '',
            tiendas TEXT DEFAULT '',
            
            -- Estado de ascensores y escaleras
            estado_ascensores TEXT DEFAULT '',
            estado_escaleras TEXT DEFAULT '',
            
            -- Accesos detallados
            vestibulo TEXT DEFAULT '',
            nombre_acceso TEXT DEFAULT '',
            salidas TEXT DEFAULT '',
            
            -- Información adicional
            horarios_ida TEXT DEFAULT '',
            horarios_vuelta TEXT DEFAULT '',
            servicios TEXT DEFAULT '',
            intercambiadores TEXT DEFAULT '',
            
            -- Timestamps
            ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultima_actualizacion_detalles TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(id, nombre, orden_en_linea)
        )
    ''')
    
    # Insertar estaciones fijas
    estaciones = ESTACIONES_FIJAS[linea]
    for estacion in estaciones:
        cursor.execute(f'''
            INSERT OR IGNORE INTO {tabla_nombre} 
            (id, nombre, orden_en_linea) 
            VALUES (?, ?, ?)
        ''', (estacion['id'], estacion['nombre'], estacion['orden']))
    
    print(f"✅ Tabla {tabla_nombre} creada con {len(estaciones)} estaciones fijas")

def cargar_urls_desde_csv(cursor, linea):
    """Carga las URLs desde el CSV de estaciones procesadas"""
    tabla_nombre = f'linea_{linea}'
    
    try:
        with open('datos_estaciones/estaciones_procesadas.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['line_number'].strip() == linea:
                    # Actualizar URL en la tabla fija
                    cursor.execute(f'''
                        UPDATE {tabla_nombre} 
                        SET url = ? 
                        WHERE nombre = ?
                    ''', (row['url'], row['station_name']))
        
        print(f"✅ URLs cargadas para línea {linea}")
        
    except FileNotFoundError:
        print(f"⚠️ No se encontró estaciones_procesadas.csv para línea {linea}")

def crear_base_datos_fija():
    """Crea la base de datos con las 13 tablas fijas"""
    
    # Crear conexión
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🚇 CREANDO BASE DE DATOS CON 13 TABLAS FIJAS")
    print("=" * 50)
    
    # Crear tablas para cada línea
    for linea in ESTACIONES_FIJAS.keys():
        crear_tabla_linea(cursor, linea)
        cargar_urls_desde_csv(cursor, linea)
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Base de datos fija creada: {DB_PATH}")

def verificar_tablas():
    """Verifica que todas las tablas se crearon correctamente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n📊 VERIFICACIÓN DE TABLAS:")
    print("-" * 30)
    
    total_estaciones = 0
    for linea in ESTACIONES_FIJAS.keys():
        tabla_nombre = f'linea_{linea}'
        
        # Contar estaciones
        cursor.execute(f'SELECT COUNT(*) FROM {tabla_nombre}')
        count = cursor.fetchone()[0]
        
        # Contar URLs
        cursor.execute(f'SELECT COUNT(*) FROM {tabla_nombre} WHERE url IS NOT NULL')
        urls_count = cursor.fetchone()[0]
        
        print(f"Línea {linea}: {count} estaciones ({urls_count} con URL)")
        total_estaciones += count
    
    print(f"\nTotal: {total_estaciones} estaciones en 13 tablas")
    
    conn.close()

def repair_database_structure():
    """
    Script seguro para reparar la estructura de la base de datos.
    Su única función es AÑADIR columnas faltantes a las tablas de línea,
    sin borrar ni alterar datos existentes.
    """
    if not os.path.exists(DB_PATH):
        print(f"❌ ERROR: La base de datos no se encuentra en la ruta esperada.")
        print(f"Ruta buscada: {os.path.abspath(DB_PATH)}")
        return

    print(f"✅ Conectando a la base de datos: {os.path.abspath(DB_PATH)}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    except sqlite3.Error as e:
        print(f"❌ ERROR: No se pudo conectar a la base de datos. {e}")
        return

    # Obtener la lista de todas las tablas que parecen de líneas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'linea_%'")
    line_tables = [row[0] for row in cursor.fetchall()]

    if not line_tables:
        print("❌ ERROR: No se encontraron tablas de líneas (con formato 'linea_...'). No se puede continuar.")
        conn.close()
        return

    print(f"🔎 Encontradas {len(line_tables)} tablas de líneas. Procediendo a verificar y reparar...")
    
    # Columnas esenciales que deben existir en cada tabla de línea
    # El valor por defecto es un array JSON vacío, almacenado como texto.
    required_columns = {
        'servicios': "'[]'",
        'accesos': "'[]'",
        'correspondencias': "'[]'"
    }
    
    tables_repaired = 0
    for table in line_tables:
        try:
            print(f"\n--- Analizando tabla: `{table}` ---")
            cursor.execute(f"PRAGMA table_info(`{table}`)")
            existing_columns = [info[1] for info in cursor.fetchall()]
            
            # Para cada columna requerida, verificar si existe. Si no, añadirla.
            for col_name, default_value in required_columns.items():
                if col_name not in existing_columns:
                    print(f"  - Columna `{col_name}` no encontrada. Añadiéndola...")
                    
                    # Usar ALTER TABLE para añadir la columna de forma segura
                    alter_query = f"ALTER TABLE `{table}` ADD COLUMN `{col_name}` TEXT DEFAULT {default_value}"
                    cursor.execute(alter_query)
                    
                    print(f"    ✅ Columna `{col_name}` añadida exitosamente a `{table}`.")
                    tables_repaired += 1
                else:
                    print(f"  - Columna `{col_name}` ya existe. No se necesita acción.")

        except sqlite3.OperationalError as e:
            print(f"  ❌ ERROR al procesar la tabla `{table}`: {e}")
            print("      Saltando esta tabla y continuando con la siguiente.")

    # Guardar todos los cambios realizados en la base de datos
    if tables_repaired > 0:
        print(f"\n💾 Guardando {tables_repaired} cambios en la base de datos...")
        conn.commit()
        print("¡Cambios guardados!")
    else:
        print("\n✨ No se necesitaron reparaciones. La estructura de la base de datos es correcta.")

    conn.close()
    print("\n✅ Proceso de reparación finalizado.")

if __name__ == "__main__":
    print("--- INICIANDO SCRIPT DE REPARACIÓN DE BASE DE DATOS ---")
    repair_database_structure()
    print("-----------------------------------------------------")

    DB_RELACIONAL = 'db/estaciones_relacional.db'
    DB_GTFS = 'M4/metro_madrid.db'
    
    if not os.path.exists(DB_GTFS):
        print(f"Error: La base de datos GTFS '{DB_GTFS}' no se encuentra.")
        print("Asegúrate de que el archivo existe en la ruta correcta antes de ejecutar este script.")
    else:
        crear_base_de_datos_relacional_desde_gtfs(DB_RELACIONAL, DB_GTFS) 