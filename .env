import os
import time
import pandas as pd
import random
import sys
import argparse
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv

load_dotenv()

# Configuración
BASE_URL = os.getenv("BASE_URL", "https://www.losmundialesdefutbol.com/mundiales.php")

# Rutas de tracking
TRACK_MUNDIALES = "data/tracking/mundiales_visitados.csv"
TRACK_PARTIDOS = "data/tracking/partidos_visitados.csv"

def asegurar_directorios():
    os.makedirs("data/tracking", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

def cargar_visitados(ruta_csv):
    if os.path.exists(ruta_csv):
        df = pd.read_csv(ruta_csv)
        return set(df['url'].tolist())
    return set()

def guardar_visitado(ruta_csv, url):
    df = pd.DataFrame([{"url": url}])
    df.to_csv(ruta_csv, mode='a', header=not os.path.exists(ruta_csv), index=False)

def guardar_datos(datos_dict, nombre_archivo):
    ruta = f"data/processed/{nombre_archivo}"
    df = pd.DataFrame([datos_dict])
    df.to_csv(ruta, mode='a', header=not os.path.exists(ruta), index=False, encoding='utf-8')

def obtener_soup(url):
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
        response = requests.get(url, headers=headers_dinamicos, impersonate="chrome120", timeout=20)
        
        if response.status_code == 403:
            print("\n" + "="*60 + "\n===== 403 FUIMOS BLOQUEADOS =====\n" + "="*60 + "\n")
            sys.exit(1) 
        elif response.status_code != 200:
            print(f"Error HTTP en {url}: {response.status_code}")
            return None

        # Pausa aleatoria para evadir detección (10 a 25 segundos)
        retraso = random.uniform(10, 25)
        print(f"    [Esperando {retraso:.1f}s simulando humano...]")
        time.sleep(retraso) 
        
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error de conexión en {url}: {e}")
        return None

# ==========================================
# NIVEL 4: Detalle Minucioso del Partido
# ==========================================
def procesar_detalle_partido(url_partido):
    print(f"      -> Extrayendo eventos: {url_partido}")
    soup = obtener_soup(url_partido)
    if not soup:
        return {"Goles": [], "Tarjetas": [], "Cambios": []}

    eventos = {"Goles": [], "Tarjetas": [], "Cambios": []}

    # Tarjetas
    tit_tarjetas = soup.find(lambda tag: tag.name == 'h3' and 'Tarjetas' in tag.text)
    if tit_tarjetas:
        tabla_tarjetas = tit_tarjetas.find_next('table')
        if tabla_tarjetas:
            for fila in tabla_tarjetas.find_all('tr', class_=lambda c: c and 'a-top' in c):
                cols = fila.find_all('td')
                if len(cols) >= 3:
                    equipo = cols[0].text.strip()
                    jugador = cols[1].text.strip()
                    detalle = cols[2].text.strip().replace('\n', ' ').replace('\r', '')
                    eventos["Tarjetas"].append(f"[{equipo}] {jugador}: {detalle}")

    # Cambios
    tit_cambios = soup.find(lambda tag: tag.name == 'h3' and 'Cambios' in tag.text)
    if tit_cambios:
        tabla_cambios = tit_cambios.find_next('table')
        if tabla_cambios:
            for fila in tabla_cambios.find_all('tr', class_=lambda c: c and 'a-top' in c):
                cols = fila.find_all('td')
                if len(cols) >= 5: 
                    minuto = cols[0].text.replace('Minuto', '').replace('(en el entretiempo)', '').strip()
                    entra = cols[2].text.strip()
                    sale = cols[4].text.strip()
                    eventos["Cambios"].append(f"Min {minuto}: Entra {entra} | Sale {sale}")

    # Goles (buscando el icono de la pelota)
    divs_goles = soup.find_all('div', class_=lambda c: c and 'w-50' in c)
    for div in divs_goles:
        if div.find('img', src=lambda s: s and 'ball.jpg' in s):
            texto_gol = " ".join(div.stripped_strings)
            if texto_gol:
                eventos["Goles"].append(texto_gol)

    return eventos

# ==========================================
# NIVEL 3: Calendario de Resultados
# ==========================================
def procesar_resultados(url_resultados, anio_mundial, partidos_visitados):
    print(f"  -> Extrayendo calendario de resultados: {url_resultados}")
    soup = obtener_soup(url_resultados)
    if not soup:
        return

    bloques_fecha = soup.find_all('h3', string=lambda text: text and 'Fecha:' in text)
    archivo_partidos = f"partidos_{anio_mundial}.csv"

    for bloque in bloques_fecha:
        fecha_tag = bloque.find('strong')
        fecha = fecha_tag.text.strip() if fecha_tag else "Desconocida"
        contenedor_dia = bloque.parent
        filas_partidos = contenedor_dia.find_all('div', class_=lambda c: c and 'margen-y3' in c and 'pad-y5' in c)
        
        for fila in filas_partidos:
            num_tag = fila.find('div', class_='wpx-30')
            if not num_tag: continue
            num_partido = num_tag.text.replace('.', '').strip()
            
            etapa_tag = fila.find('div', class_='wpx-170')
            etapa = etapa_tag.text.strip() if etapa_tag else "Desconocida"
            
            equipos_tags = fila.find_all('div', style=lambda s: s and 'width: 129px' in s)
            if len(equipos_tags) < 2: continue
            equipo_local = equipos_tags[0].text.strip()
            equipo_visitante = equipos_tags[1].text.strip()
                
            marcador_tag = fila.find('div', class_='wpx-60')
            link_partido = ""
            marcador = "N/A"
            if marcador_tag and marcador_tag.find('a'):
                enlace = marcador_tag.find('a')
                marcador = enlace.text.strip()
                link_partido = urljoin(url_resultados, enlace['href']) 
            
            # Si ya procesamos este partido exacto, lo saltamos
            if link_partido and link_partido in partidos_visitados:
                print(f"      [Saltando partido ya visitado: {equipo_local} vs {equipo_visitante}]")
                continue

            info_extra = ""
            divs_extra = fila.find_all('div', class_=lambda c: c and 'justify-center' in c and 'margen-b3' in c)
            for div_ex in divs_extra:
                if 'game' not in div_ex.get('class', []):
                    textos = " ".join(div_ex.stripped_strings)
                    info_extra += f"[{textos}] "

            # --- LLAMADA AL NIVEL 4 ---
            eventos_partido = {"Goles": [], "Tarjetas": [], "Cambios": []}
            if link_partido:
                eventos_partido = procesar_detalle_partido(link_partido)

            datos_completos = {
                "Año": anio_mundial,
                "Fecha": fecha,
                "Partido_Num": num_partido,
                "Etapa": etapa,
                "Local": equipo_local,
                "Marcador": marcador,
                "Visitante": equipo_visitante,
                "Tiempo_Extra_Penales": info_extra.strip(),
                "Goles_Detalle": " ; ".join(eventos_partido["Goles"]),
                "Tarjetas_Detalle": " ; ".join(eventos_partido["Tarjetas"]),
                "Cambios_Detalle": " ; ".join(eventos_partido["Cambios"]),
                "URL_Partido": link_partido
            }

            # Guardar el partido y marcarlo como visitado
            guardar_datos(datos_completos, archivo_partidos)
            if link_partido:
                guardar_visitado(TRACK_PARTIDOS, link_partido)
                partidos_visitados.add(link_partido)

# ==========================================
# NIVEL 2: Información General y Grupos
# ==========================================
def procesar_mundial(url_mundial, anio_mundial):
    print(f"-> Explorando Mundial {anio_mundial}: {url_mundial}")
    soup = obtener_soup(url_mundial)
    if not soup:
        return

    # Extraer Grupos (Simple)
    titulo_grupos = soup.find(lambda tag: tag.name == 'h3' and 'Grupos y Planteles' in tag.text)
    if titulo_grupos:
        tabla_grupos = titulo_grupos.find_next('table')
        if tabla_grupos:
            filas_grupos = tabla_grupos.find_all('tr', class_='a-top')
            archivo_grupos = f"grupos_{anio_mundial}.csv"
            
            for fila in filas_grupos:
                cols = fila.find_all('td')
                if len(cols) >= 3:
                    nombre_grupo = cols[0].text.strip()
                    links_equipos = cols[2].find_all('a')
                    for enlace in links_equipos:
                        guardar_datos({
                            "Año": anio_mundial,
                            "Grupo": nombre_grupo,
                            "Selección": enlace.text.strip()
                        }, archivo_grupos)

# ==========================================
# NIVEL 1: Página Principal (Punto de Entrada)
# ==========================================
def iniciar_scraper(inicio, fin):
    asegurar_directorios()
    mundiales_visitados = cargar_visitados(TRACK_MUNDIALES)
    partidos_visitados = cargar_visitados(TRACK_PARTIDOS)

    print("Obteniendo lista histórica de mundiales...")
    soup = obtener_soup(BASE_URL)
    if not soup:
        return

    enlaces = soup.find_all('a', href=True)
    lista_mundiales = []
    
    # Recolectar todos los mundiales
    for enlace in enlaces:
        href = enlace['href']
        if href.startswith('mundiales/') and href.endswith('_mundial.php'):
            anio = href.split('/')[1].split('_')[0] 
            url_mundial = urljoin(BASE_URL, href)
            url_resultados = urljoin(BASE_URL, f"mundiales/{anio}_resultados.php")
            
            if not any(m['anio'] == anio for m in lista_mundiales):
                lista_mundiales.append({
                    "anio": anio,
                    "url_mundial": url_mundial,
                    "url_resultados": url_resultados
                })
                
    # Aplicar el recorte (sharding) para las VMs
    lote_mundiales = lista_mundiales[inicio:fin]
    print(f"Lote asignado: {len(lote_mundiales)} mundiales (Índices del {inicio} al {fin-1}).\n" + "-"*40)
    
    for m in lote_mundiales:
        if m['url_mundial'] not in mundiales_visitados:
            # 1. Sacamos Grupos
            procesar_mundial(m['url_mundial'], m['anio'])
            # 2. Sacamos Partidos y Detalles
            procesar_resultados(m['url_resultados'], m['anio'], partidos_visitados)
            
            # Marcamos Mundial como terminado
            guardar_visitado(TRACK_MUNDIALES, m['url_mundial'])
            mundiales_visitados.add(m['url_mundial'])
        else:
            print(f"Saltando Mundial ya procesado: {m['anio']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper distribuido de Mundiales y Partidos")
    parser.add_argument("--inicio", type=int, default=0, help="Índice inicial del mundial (empieza en 0)")
    parser.add_argument("--fin", type=int, default=100, help="Índice final del mundial (exclusivo)")
    args = parser.parse_args()

    print(f"--- Iniciando Scraper: Rango {args.inicio} a {args.fin} ---")
    iniciar_scraper(args.inicio, args.fin)
    print("\nScraping finalizado exitosamente para este lote.")