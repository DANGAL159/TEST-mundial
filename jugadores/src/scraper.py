import os
import time
import pandas as pd
import random
import sys
import argparse
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ==========================================
# CONFIGURACIÓN
# ==========================================
BASE_URL = "https://www.losmundialesdefutbol.com/jugadores.php"
TRACK_PAISES = "data/tracking/paises_visitados_jugadores.csv"
TRACK_JUGADORES = "data/tracking/jugadores_visitados.csv"

# PLANTILLA ESTRICTA: Estas serán las columnas del CSV, en este orden exacto.
COLUMNAS_PERMITIDAS = [
    "URL", "Nombre", "Selección", "Nombre completo", "Fecha de Nacimiento", 
    "Lugar de nacimiento", "Posición", "Números de camiseta", "Altura", 
    "Mundiales Jugados", "Partidos Jugados", "Goles Anotados", "Promedio Gol", 
    "Titular", "Capitán", "Banca (No Jugó)", "Amarillas", "Rojas", 
    "Partidos Ganados", "Partidos Empatados", "Partidos Perdidos"
]

def asegurar_directorios():
    os.makedirs("data/tracking", exist_ok=True)
    os.makedirs("data/processed/jugadores", exist_ok=True)

def cargar_visitados(ruta_csv):
    if os.path.exists(ruta_csv):
        return set(pd.read_csv(ruta_csv)['url'].tolist())
    return set()

def guardar_visitado(ruta_csv, url):
    pd.DataFrame([{"url": url}]).to_csv(ruta_csv, mode='a', header=not os.path.exists(ruta_csv), index=False)

def obtener_soup(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    }
    try:
        res = requests.get(url, headers=headers, impersonate="chrome120", timeout=20)
        if res.status_code == 403: sys.exit("403 BLOQUEO")
        if res.status_code != 200: return None
        time.sleep(random.uniform(5, 12)) 
        return BeautifulSoup(res.text, 'html.parser')
    except Exception:
        return None

def procesar_jugador(url_jugador, url_pais):
    print(f"    -> Extrayendo: {url_jugador}")
    soup = obtener_soup(url_jugador)
    if not soup: return

    # Inicializamos el diccionario con la plantilla, todo vacío por defecto
    datos_jugador = {col: "" for col in COLUMNAS_PERMITIDAS}
    datos_jugador["URL"] = url_jugador
    
    # El nombre de la selección viene en la URL del país (ej. "francia.php" -> "Francia")
    nombre_pais = url_pais.split('/')[-1].replace('.php', '').replace('_', ' ').title()
    datos_jugador["Selección"] = nombre_pais

    # 1. Nombre Principal
    nombre_tag = soup.find('h2', class_='t-enc-1')
    if nombre_tag: datos_jugador['Nombre'] = nombre_tag.text.strip()

    # 2. Datos Personales (Solo guardamos los que coincidan con COLUMNAS_PERMITIDAS)
    tabla_personal = soup.find('div', class_='rd-100-70')
    if tabla_personal:
        for fila in tabla_personal.find_all('tr', class_='a-top'):
            cols = fila.find_all('td')
            if len(cols) == 2:
                clave = cols[0].text.replace(':', '').strip()
                valor = " | ".join(cols[1].stripped_strings)
                if clave in datos_jugador:
                    datos_jugador[clave] = valor

    # 3. Estadísticas Generales
    div_mundiales = soup.find('div', class_='rd-100-60')
    if div_mundiales and div_mundiales.find('tr', class_='pad-y8'):
        tds = div_mundiales.find('tr', class_='pad-y8').find_all('td')
        if len(tds) >= 2:
            datos_jugador['Mundiales Jugados'] = tds[0].text.replace('Mundiales', '').replace('Mundial', '').strip()
            datos_jugador['Partidos Jugados'] = tds[1].text.replace('Partidos Jugados', '').replace('Partido Jugado', '').strip()

    div_goles = soup.find('div', class_='rd-100-40')
    if div_goles and div_goles.find('tr', class_='pad-y8'):
        tds = div_goles.find('tr', class_='pad-y8').find_all('td')
        if len(tds) >= 2:
            datos_jugador['Goles Anotados'] = tds[0].text.replace('Goles Anotados', '').replace('Gol Anotado', '').strip()
            datos_jugador['Promedio Gol'] = tds[1].text.replace('Promedio de Gol', '').strip()

    # 4. Totales Detallados (La fila "Totales:" al final de la página)
    celda_totales = soup.find('td', string=lambda text: text and 'Totales:' in text)
    if celda_totales:
        valores = celda_totales.parent.find_all('strong')
        # Según el HTML de Messi/Mbappé, los índices de los <strong> son:
        # [0]="Totales:", [1]=PG, [2]=Titular, [3]=Capitán, [4]=Banca, [5]=Goles, 
        # [6]=Prom, [7]=Amarillas, [8]=Rojas, [9]=Ganados, [10]=Empatados, [11]=Perdidos
        if len(valores) >= 12:
            datos_jugador['Titular'] = valores[2].text.strip()
            datos_jugador['Capitán'] = valores[3].text.strip()
            datos_jugador['Banca (No Jugó)'] = valores[4].text.strip()
            datos_jugador['Amarillas'] = valores[7].text.strip()
            datos_jugador['Rojas'] = valores[8].text.strip()
            datos_jugador['Partidos Ganados'] = valores[9].text.strip()
            datos_jugador['Partidos Empatados'] = valores[10].text.strip()
            datos_jugador['Partidos Perdidos'] = valores[11].text.strip()

    # 5. Guardar en CSV separado por país
    nombre_archivo = f"data/processed/jugadores/jugadores_{url_pais.split('/')[-1]}"
    df = pd.DataFrame([datos_jugador])
    df.to_csv(nombre_archivo, mode='a', header=not os.path.exists(nombre_archivo), index=False, encoding='utf-8')
    guardar_visitado(TRACK_JUGADORES, url_jugador)

def procesar_pais(url_pais, jugadores_visitados):
    print(f"-> Explorando país: {url_pais}")
    soup = obtener_soup(url_pais)
    if not soup: return

    for enlace in soup.find_all('a', href=True):
        href = enlace['href']
        if '/jugadores/' in href and href.endswith('.php'):
            url_jugador = urljoin("https://www.losmundialesdefutbol.com", href)
            if url_jugador not in jugadores_visitados:
                procesar_jugador(url_jugador, url_pais)
                jugadores_visitados.add(url_jugador)

def iniciar_scraper(inicio, fin):
    asegurar_directorios()
    paises_visitados = cargar_visitados(TRACK_PAISES)
    jugadores_visitados = cargar_visitados(TRACK_JUGADORES)

    soup = obtener_soup(BASE_URL)
    enlaces_paises = []
    if soup:
        for a in soup.find_all('a', href=True):
            if 'jugadores_indice/' in a['href'] and 'letra_' not in a['href']:
                url = urljoin(BASE_URL, a['href'])
                if url not in enlaces_paises: enlaces_paises.append(url)

    lote = enlaces_paises[inicio:fin]
    print(f"Procesando lote de {len(lote)} países (Índices {inicio} a {fin-1})...")

    for url_pais in lote:
        if url_pais not in paises_visitados:
            procesar_pais(url_pais, jugadores_visitados)
            guardar_visitado(TRACK_PAISES, url_pais)
        else:
            print(f"Saltando país ya visitado: {url_pais}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inicio", type=int, default=0)
    parser.add_argument("--fin", type=int, default=1000)
    args = parser.parse_args()
    iniciar_scraper(args.inicio, args.fin)