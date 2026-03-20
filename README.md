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
python src/scraper.py --inicio 0 --fin 15