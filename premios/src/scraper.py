import os
import time
import pandas as pd
import random
import sys
import argparse
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuración
BASE_URL = "https://www.losmundialesdefutbol.com/mundiales.php"
ARCHIVO_PREMIOS = "data/processed/premios_mundiales.csv"

def asegurar_directorios():
    os.makedirs("data/processed", exist_ok=True)

def guardar_premio(datos_dict):
    """Guarda un premio individual en el CSV de premios."""
    df = pd.DataFrame([datos_dict])
    df.to_csv(ARCHIVO_PREMIOS, mode='a', header=not os.path.exists(ARCHIVO_PREMIOS), index=False, encoding='utf-8')

def obtener_soup(url):
    """Petición robusta evadiendo Cloudflare con curl_cffi."""
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
        elif response.status_code == 404:
            print(f"    [!] No existe página de premios para: {url}")
            return None
        elif response.status_code != 200:
            print(f"Error HTTP en {url}: {response.status_code}")
            return None

        # Pausa aleatoria un poco más rápida (5 a 12 segs) ya que son menos páginas
        retraso = random.uniform(5, 12)
        print(f"    [Esperando {retraso:.1f}s simulando humano...]")
        time.sleep(retraso) 
        
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error de conexión en {url}: {e}")
        return None

def procesar_premios_mundial(url_premios, anio):
    """Extrae todos los premios de la página de un mundial específico."""
    print(f"-> Buscando premios del Mundial {anio}: {url_premios}")
    soup = obtener_soup(url_premios)
    if not soup:
        return

    # Buscamos todos los párrafos que actúan como título del premio
    titulos_premios = soup.find_all('p', class_='negri')
    
    premios_encontrados = 0

    for titulo in titulos_premios:
        nombre_premio = titulo.text.strip().replace(':', '')
        
        # Ignoramos títulos que no son premios reales
        if not nombre_premio or nombre_premio.lower() == "premios":
            continue

        ganador_texto = "N/A"

        # LÓGICA ESPECIAL: El "Equipo Ideal" tiene una estructura HTML diferente
        if "Equipo Ideal" in nombre_premio or "Estrellas" in nombre_premio:
            div_padre = titulo.parent
            div_jugadores = div_padre.find_next_sibling('div')
            if div_jugadores:
                # Extraemos todos los enlaces (nombres de jugadores)
                ganadores = [a.text.strip() for a in div_jugadores.find_all('a')]
                ganador_texto = " ; ".join(ganadores)
        
        # LÓGICA ESTÁNDAR: Para Balón de Oro, Botín de Oro, Fair Play, etc.
        else:
            p_ganador = titulo.find_next_sibling('p')
            if p_ganador:
                enlaces = p_ganador.find_all('a')
                if enlaces:
                    # Si hay enlaces (ej. un jugador o dos selecciones empatadas)
                    ganador_texto = " ; ".join([a.text.strip() for a in enlaces])
                else:
                    # Si por alguna razón es solo texto plano
                    ganador_texto = p_ganador.text.strip()
        
        if ganador_texto != "N/A":
            guardar_premio({
                "Año": anio,
                "Premio": nombre_premio,
                "Ganadores": ganador_texto
            })
            premios_encontrados += 1

    print(f"   ✓ Se guardaron {premios_encontrados} premios para el {anio}.")

def iniciar_scraper_premios(inicio, fin):
    asegurar_directorios()
    
    print("Obteniendo lista de mundiales para buscar premios...")
    soup = obtener_soup(BASE_URL)
    if not soup:
        return

    enlaces = soup.find_all('a', href=True)
    lista_mundiales = []
    
    for enlace in enlaces:
        href = enlace['href']
        if href.startswith('mundiales/') and href.endswith('_mundial.php'):
            anio = href.split('/')[1].split('_')[0] 
            # Construimos la URL de premios directamente
            url_premios = urljoin(BASE_URL, f"mundiales/{anio}_premios.php")
            
            if not any(m['anio'] == anio for m in lista_mundiales):
                lista_mundiales.append({
                    "anio": anio,
                    "url_premios": url_premios
                })
                
    lote = lista_mundiales[inicio:fin]
    print(f"Lote asignado: {len(lote)} mundiales (Índices del {inicio} al {fin-1}).\n" + "-"*40)
    
    for m in lote:
        procesar_premios_mundial(m['url_premios'], m['anio'])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper de Premios de los Mundiales")
    parser.add_argument("--inicio", type=int, default=0, help="Índice inicial")
    parser.add_argument("--fin", type=int, default=100, help="Índice final (exclusivo)")
    args = parser.parse_args()

    print(f"--- Iniciando Scraper de Premios: Rango {args.inicio} a {args.fin} ---")
    iniciar_scraper_premios(args.inicio, args.fin)
    print("\nExtracción de premios finalizada.")