# DESDE TEST-mundial

# 1. Actualizar índice de paquetes
sudo apt update

# 2. Instalar Python y herramientas esenciales
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential

# 3. Verificar instalaciones
python3 --version
pip3 --version

# 4. Crear entorno virtual en la carpeta del proyecto
python3 -m venv .venv

# 5. Activar el entorno virtual (Linux/Ubuntu)
source .venv/bin/activate

# 6. Actualizar pip dentro del entorno
pip install --upgrade pip

# 7. Instalar dependencias desde requirements.txt
pip install -r requirements.txt

# Desde proyecto

# 8. Correr el programa
cd proyecto
DAN 0-7
python src/scraper.py --inicio 0 --fin 1
python src/scraper.py --inicio 1 --fin 2
python src/scraper.py --inicio 2 --fin 3
MAT 7-14
python src/scraper.py --inicio 3 --fin 4
python src/scraper.py --inicio 4 --fin 5
ALE 14-22
python src/scraper.py --inicio 5 --fin 8
python src/scraper.py --inicio 6 --fin 7