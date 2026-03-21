import os
import time
import json
import random
import sys
import argparse
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.losmundialesdefutbol.com/jugadores.php"
TRACK_PAISES = "data/tracking/paises_visitados_jugadores.csv"
TRACK_JUGADORES = "data/tracking/jugadores_visitados.csv"

def asegurar_directorios():
    os.makedirs("data/tracking", exist_ok=True)
    os.makedirs("data/processed/jugadores", exist_ok=True)

def cargar_visitados(ruta_archivo):
    if os.path.exists(ruta_archivo):
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f.readlines())
    return set()

def guardar_visitado(ruta_archivo, url):
    with open(ruta_archivo, 'a', encoding='utf-8') as f:
        f.write(url + '\n')

def obtener_soup(url):
    headers_dinamicos = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.losmundialesdefutbol.com/"
    }
    try:
        res = requests.get(url, headers=headers_dinamicos, impersonate="chrome120", timeout=20)
        if res.status_code == 403: sys.exit("\n===== 403 BLOQUEO =====")
        if res.status_code != 200: return None
        
        time.sleep(random.uniform(5, 12))
        return BeautifulSoup(res.text, 'html.parser')
    except Exception:
        return None

def procesar_jugador(url_jugador, nombre_pais):
    print(f"    -> Extrayendo: {url_jugador}")
    soup = obtener_soup(url_jugador)
    if not soup: return None

    # Diccionario dinámico: aceptará todo lo que encuentre
    datos = {"URL": url_jugador, "Selección": nombre_pais}

    nombre_tag = soup.find('h2', class_='t-enc-1')
    if nombre_tag: datos['Nombre Principal'] = nombre_tag.text.strip()

    # 1. DATOS PERSONALES (Captura el 100% de las filas, incluyendo Redes, Apodos, etc.)
    tabla_personal = soup.find('div', class_='rd-100-70')
    if tabla_personal:
        for fila in tabla_personal.find_all('tr', class_='a-top'):
            cols = fila.find_all('td')
            if len(cols) == 2:
                clave = cols[0].text.replace(':', '').strip()
                valor = " | ".join(cols[1].stripped_strings)
                datos[clave] = valor

    # 2. ESTADÍSTICAS GENERALES
    div_mundiales = soup.find('div', class_='rd-100-60')
    if div_mundiales and div_mundiales.find('tr', class_='pad-y8'):
        tds = div_mundiales.find('tr', class_='pad-y8').find_all('td')
        if len(tds) >= 2:
            datos['Mundiales Jugados'] = tds[0].text.replace('Mundiales', '').replace('Mundial', '').strip()
            datos['Partidos Jugados'] = tds[1].text.replace('Partidos Jugados', '').replace('Partido Jugado', '').strip()

    div_goles = soup.find('div', class_='rd-100-40')
    if div_goles and div_goles.find('tr', class_='pad-y8'):
        tds = div_goles.find('tr', class_='pad-y8').find_all('td')
        if len(tds) >= 2:
            datos['Goles Anotados'] = tds[0].text.replace('Goles Anotados', '').replace('Gol Anotado', '').strip()
            datos['Promedio Gol'] = tds[1].text.replace('Promedio de Gol', '').strip()

    # 3. TOTALES DETALLADOS
    celda_totales = soup.find('td', string=lambda text: text and 'Totales:' in text)
    if celda_totales:
        valores = celda_totales.parent.find_all('strong')
        if len(valores) >= 12:
            datos['Titular'] = valores[2].text.strip()
            datos['Capitán'] = valores[3].text.strip()
            datos['Banca (No Jugó)'] = valores[4].text.strip()
            datos['Amarillas'] = valores[7].text.strip()
            datos['Rojas'] = valores[8].text.strip()
            datos['Partidos Ganados'] = valores[9].text.strip()
            datos['Partidos Empatados'] = valores[10].text.strip()
            datos['Partidos Perdidos'] = valores[11].text.strip()

    guardar_visitado(TRACK_JUGADORES, url_jugador)
    return datos

def procesar_pais(url_pais, jugadores_visitados):
    nombre_pais = url_pais.split('/')[-1].replace('.php', '').replace('_', ' ').title()
    print(f"-> Explorando selección de: {nombre_pais}")
    soup = obtener_soup(url_pais)
    if not soup: return

    jugadores_del_pais = []
    
    for enlace in soup.find_all('a', href=True):
        href = enlace['href']
        if '/jugadores/' in href and href.endswith('.php'):
            url_jugador = urljoin("https://www.losmundialesdefutbol.com", href)
            if url_jugador not in jugadores_visitados:
                datos_jugador = procesar_jugador(url_jugador, nombre_pais)
                if datos_jugador:
                    jugadores_del_pais.append(datos_jugador)
                jugadores_visitados.add(url_jugador)

    # Guardar todos los jugadores en un archivo JSON estructurado
    if jugadores_del_pais:
        nombre_archivo = f"data/processed/jugadores/jugadores_{url_pais.split('/')[-1].replace('.php', '.json')}"
        # Si el archivo ya existe, cargamos lo que hay y le agregamos los nuevos
        if os.path.exists(nombre_archivo):
            with open(nombre_archivo, 'r', encoding='utf-8') as f:
                datos_existentes = json.load(f)
            jugadores_del_pais = datos_existentes + jugadores_del_pais
            
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(jugadores_del_pais, f, ensure_ascii=False, indent=4)

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