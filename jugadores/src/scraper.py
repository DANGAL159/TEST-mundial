import os
import time
import pandas as pd
import random
import sys
import argparse
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.losmundialesdefutbol.com/jugadores.php"
TRACK_PAISES = "data/tracking/paises_visitados_jugadores.csv"
TRACK_JUGADORES = "data/tracking/jugadores_visitados.csv"

PLANTILLA_MESSI = [
    "URL", "Selección", "Nombre Principal", "Nombre completo", "Fecha de Nacimiento", 
    "Lugar de nacimiento", "Posición", "Números de camiseta", "Altura", "Apodo", 
    "Sitio Web Oficial", "Redes Sociales", "Mundiales Jugados", "Partidos Jugados", 
    "Goles Anotados", "Promedio Gol", "Titular", "Capitán", "Banca (No Jugó)", 
    "Amarillas", "Rojas", "Partidos Ganados", "Partidos Empatados", "Partidos Perdidos"
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
    # Identidad única, sólida y coherente (Edge en Windows)
    headers_dinamicos = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-419,es;q=0.9,es-ES;q=0.8,en;q=0.7",
        "Referer": "https://www.losmundialesdefutbol.com/",
        "Sec-Ch-Ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Microsoft Edge";v="146"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }
    try:
        # impersonate="chrome120" combina perfecto con un User-Agent de Windows
        res = requests.get(url, headers=headers_dinamicos, impersonate="chrome120", timeout=20)
        
        if res.status_code == 403: 
            sys.exit(f"\n🚫 ===== 403 BLOQUEO =====\nLa IP ha sido bloqueada al intentar acceder a: {url}")
            
        if res.status_code != 200: 
            print(f"    ⚠️ [HTTP {res.status_code}] Página no encontrada o error en servidor: {url}")
            return None
            
        # Pausa aleatoria para cuidar la IP
        time.sleep(random.uniform(5, 12)) 
        return BeautifulSoup(res.text, 'html.parser')
        
    except Exception as e:
        print(f"    🔌 [ERROR DE RED / TIMEOUT] Saltando URL: {url} -> Detalle: {e}")
        return None
        
def procesar_jugador(url_jugador, url_pais):
    print(f"    -> Extrayendo: {url_jugador}")
    
    try:
        soup = obtener_soup(url_jugador)
        # Si no hay soup (por error 500, timeout, etc.), devolvemos Falso
        if not soup: 
            return False

        datos_jugador = {col: "" for col in PLANTILLA_MESSI}
        datos_jugador["URL"] = url_jugador
        datos_jugador["Selección"] = url_pais.split('/')[-1].replace('.php', '').replace('_', ' ').title()

        nombre_tag = soup.find('h2', class_='t-enc-1')
        if nombre_tag: datos_jugador['Nombre Principal'] = nombre_tag.text.strip()

        tabla_personal = soup.find('div', class_='rd-100-70')
        if tabla_personal:
            for fila in tabla_personal.find_all('tr', class_='a-top'):
                cols = fila.find_all('td')
                if len(cols) == 2:
                    clave = cols[0].text.replace(':', '').strip()
                    valor = " | ".join(cols[1].stripped_strings)
                    if clave in datos_jugador:
                        datos_jugador[clave] = valor

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

        celda_totales = soup.find('td', string=lambda text: text and 'Totales:' in text)
        if celda_totales:
            valores = celda_totales.parent.find_all('strong')
            if len(valores) >= 12:
                datos_jugador['Titular'] = valores[2].text.strip()
                datos_jugador['Capitán'] = valores[3].text.strip()
                datos_jugador['Banca (No Jugó)'] = valores[4].text.strip()
                datos_jugador['Amarillas'] = valores[7].text.strip()
                datos_jugador['Rojas'] = valores[8].text.strip()
                datos_jugador['Partidos Ganados'] = valores[9].text.strip()
                datos_jugador['Partidos Empatados'] = valores[10].text.strip()
                datos_jugador['Partidos Perdidos'] = valores[11].text.strip()

        nombre_archivo = f"data/processed/jugadores/jugadores_{url_pais.split('/')[-1].replace('.php', '.csv')}"
        df = pd.DataFrame([datos_jugador])
        df.to_csv(nombre_archivo, mode='a', header=not os.path.exists(nombre_archivo), index=False, encoding='utf-8')
        
        # Guardamos en el tracking SOLO si todo fue exitoso
        guardar_visitado(TRACK_JUGADORES, url_jugador)
        return True
        
    except Exception as e:
        print(f"    💥 [ERROR DE CÓDIGO] Falló el parseo de {url_jugador} -> Detalle: {e}")
        return False

def procesar_pais(url_pais, jugadores_visitados):
    print(f"-> Explorando selección: {url_pais}")
    soup = obtener_soup(url_pais)
    
    # Si la página del país falla, devolvemos Falso inmediatamente
    if not soup: 
        return False

    exito_total_pais = True
    
    for enlace in soup.find_all('a', href=True):
        href = enlace['href']
        if '/jugadores/' in href and href.endswith('.php'):
            url_jugador = urljoin("https://www.losmundialesdefutbol.com", href)
            if url_jugador not in jugadores_visitados:
                # Extraemos el jugador y verificamos si fue exitoso
                exito_jugador = procesar_jugador(url_jugador, url_pais)
                if exito_jugador:
                    jugadores_visitados.add(url_jugador)
                else:
                    # Si un solo jugador falla, el país no puede marcarse como completado
                    exito_total_pais = False

    return exito_total_pais

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
            exito_pais = procesar_pais(url_pais, jugadores_visitados)
            # Solo guardamos el país como visitado si NADIE dio error
            if exito_pais:
                guardar_visitado(TRACK_PAISES, url_pais)
                paises_visitados.add(url_pais)
            else:
                print(f"    ⚠️ [PAÍS INCOMPLETO] Hubo errores en {url_pais}. Se reintentará en la próxima ejecución.")
        else:
            print(f"⏭️  Saltando país ya visitado completamente: {url_pais}")

    print(f"\n✅ ¡Trabajo terminado! Se completó la ejecución del lote asignado.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inicio", type=int, default=0)
    parser.add_argument("--fin", type=int, default=1000)
    args = parser.parse_args()
    
    try:
        iniciar_scraper(args.inicio, args.fin)
    except KeyboardInterrupt:
        print("\n🛑 [INTERRUPCIÓN] Has presionado Ctrl+C. El progreso hasta el último jugador extraído con éxito se ha guardado correctamente.")
        sys.exit(0)