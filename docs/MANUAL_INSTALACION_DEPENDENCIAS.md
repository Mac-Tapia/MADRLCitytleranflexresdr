# Manual de Instalacion de Dependencias — CityLearn v3 MADRL

**Proyecto:** `MADRLCitytleranflexresdr`
**Ultima actualizacion:** 2026-06-16
**Entornos cubiertos:** Windows local (RTX 4060) y AWS Linux (entrenamiento en la nube)

Este manual documenta que dependencias instalar, en que orden y en que archivos del repositorio estan definidas, para poder entrenar los 4 MADRL (HAPPO, MASAC, MATD3, MAAC) sin errores de compatibilidad.

Desde 2026-06-16 todas las dependencias del proyecto estan consolidadas en un
unico archivo en la raiz: **`requirements.txt`**. Windows y AWS instalan a
partir de ese mismo archivo (antes habia listas duplicadas en el script de
Windows y en `deploy/aws/training/requirements-training-aws.txt`).

## 1. Requisitos de sistema

| Requisito | Version/detalle | Para que |
| --------- | ---------------- | -------- |
| Python | 3.9 (exacto, no 3.10+) | Compatibilidad MARLlib/Ray 1.8.0 |
| Git | con soporte de submodules | Clonar repo principal + 9 submodulos |
| `uv` (astral) | ultima | Crea el venv 3.9 reproducible |
| PowerShell 7 (`pwsh.exe`) | local Windows | Lanzar entrenamiento |
| Driver NVIDIA | >=560.94 | Soporte CUDA 12.6 |
| CUDA Toolkit | 12.6 (via wheel de torch, sin instalacion aparte) | Entrenamiento GPU |
| Google Chrome | version reciente | Solo para `tools/generate_architecture_pdfs.py` y `generate_architecture_pngs.py` |

## 2. Mapa de archivos de dependencias

```text
requirements.txt                                           FUENTE UNICA: todas las dependencias (incluye -e ./CityLearn y -e .)
pyproject.toml                                              paquete uc3m (raiz del proyecto, leido por -e .)
CityLearn/requirements.txt                                  CityLearn v2 base (leido por -e ./CityLearn)
CityLearn/setup.py                                           instala CityLearn editable
CityLearn/scripts/setup_citylearn_v3_training_env.ps1        script Windows: crea el venv y corre `pip install -r requirements.txt`
deploy/aws/training/bootstrap_ubuntu_gpu.sh                  script bash: crea el venv y corre `pip install -r requirements.txt`
external/HARL/setup.py                                       backend HAPPO (usado via sys.path, no se pip-instala)
external/MARLlib/requirements.txt                            backend MASAC (usado via sys.path, no se pip-instala el paquete)
external/off-policy/requirements.txt                         OBSOLETO — no usar (ver nota)
```

**Nota sobre `external/off-policy/requirements.txt`:** es el requirements original del repositorio upstream (torch 1.5.1+cu101, TensorFlow 2.0.0, dependencias estilo Python 2). Es obsoleto y no se instala. El backend MATD3 reutiliza el codigo de `external/off-policy` ejecutandose sobre el mismo venv principal (torch 2.8.0+cu126, numpy 1.23.5), no sobre ese requirements.txt.

**Nota sobre `external/HARL` y `external/MARLlib`:** sus paquetes (`harl`, `marllib`) NO se instalan con `pip install -e`. El codigo se usa directamente agregando esas carpetas a `sys.path` en tiempo de ejecucion (ver `CityLearn/scripts/check_citylearn_v3_training_ready.py`). Lo que SI se instala via `requirements.txt` son las dependencias reales que ese codigo necesita para importarse: `ray[rllib]==1.8.0`, `gym==0.20.0`, `icecream`, `supersuit`, `pettingzoo`, etc.

## 3. Instalacion — comando unico (Windows y AWS)

Con el venv Python 3.9 ya creado y activado, **todo el proyecto se instala con un solo comando** desde la raiz:

```powershell
pip install -r requirements.txt
```

Ese comando instala, en una sola resolucion de dependencias: CityLearn editable (`-e ./CityLearn`), el paquete `uc3m` editable (`-e .`), y todas las versiones fijas de compatibilidad RL (numpy, gym, gymnasium, protobuf, ray[rllib], etc.). No requiere pasos de `--force-reinstall` separados porque todas las restricciones de version se resuelven juntas.

El unico paso que queda fuera de ese archivo es PyTorch con soporte CUDA, porque necesita un indice de wheels especifico (no se puede mezclar con el indice por defecto de PyPI sin arriesgar version incorrecta):

```powershell
pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

Este segundo comando debe ejecutarse **despues** del primero: `-e ./CityLearn` instala una build CPU generica de torch como dependencia transitiva, y este paso la reemplaza por la build CUDA.

## 4. Secuencia de instalacion — Windows local

### 4.1 Opcion rapida (script wrapper, recomendada)

```powershell
# 1. Clonar con submodulos
git clone --recurse-submodules https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git
cd MADRLCitytleranflexresdr

# 2. Crear venv 3.9 + instalar TODO desde requirements.txt
pwsh.exe -File CityLearn\scripts\setup_citylearn_v3_training_env.ps1

# 3. Instalar PyTorch CUDA explicitamente (el paso 2 deja build CPU)
.\.venv39-citylearn-v3\Scripts\python.exe -m pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu126

# 4. Verificar
.\.venv39-citylearn-v3\Scripts\python.exe -m pip check
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\check_citylearn_v3_training_ready.py --strict
```

### 4.2 Opcion manual paso a paso (mismos comandos que ejecuta el script anterior)

Util para depurar un fallo puntual de instalacion sin tener que reejecutar todo el wrapper.

```powershell
# Paso 0 — clonar con submodulos y entrar al proyecto
git clone --recurse-submodules https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git
cd MADRLCitytleranflexresdr

# Paso 1 — verificar que uv esta instalado (si no, instalarlo)
Get-Command uv -ErrorAction SilentlyContinue
# Si no aparece nada, instalar uv:
#   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Paso 2 — instalar Python 3.9 via uv y crear el venv del proyecto
uv python install 3.9
uv venv --python 3.9 .venv39-citylearn-v3

# Paso 3 — definir la ruta al interprete del venv (se usa en todos los pasos siguientes)
$Python = ".\.venv39-citylearn-v3\Scripts\python.exe"

# Paso 4 — actualizar pip/setuptools/wheel a las versiones validadas
& $Python -m ensurepip --upgrade
& $Python -m pip install --force-reinstall "pip==21.3.1" "setuptools==65.5.0" "wheel==0.38.0"

# Paso 5 — instalar TODAS las dependencias en un solo comando (requirements.txt
# incluye -e ./CityLearn, -e . y las versiones fijas de compatibilidad RL)
& $Python -m pip install -r requirements.txt

# Paso 6 — instalar PyTorch con soporte CUDA (el paso 5 deja build CPU)
& $Python -m pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu126

# Paso 7 — verificar consistencia de paquetes instalados
& $Python -m pip check

# Paso 8 — smoke test especifico del proyecto (falla si algo critico no esta listo)
& $Python -B CityLearn\scripts\check_citylearn_v3_training_ready.py --strict

# Paso 8b — variante con esquema y escenario explicitos (igual que en la seccion 7)
& $Python -B CityLearn\scripts\check_citylearn_v3_training_ready.py --strict `
    --schema-path "CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json" `
    --scenario E1
```

## 5. Secuencia de instalacion — AWS Linux

```bash
bash deploy/aws/training/bootstrap_ubuntu_gpu.sh
```

Pasos internos del script:

1. `apt-get install`: build-essential, ca-certificates, curl, git, git-lfs, htop, jq, tmux, unzip.
2. Instala `uv`, crea venv Python 3.9 en `.venv39-citylearn-v3`.
3. `git submodule update --init --recursive`.
4. `pip install --upgrade "pip>=23.3,<25" "setuptools>=68,<76" wheel`.
5. `pip install -r requirements.txt` (mismo archivo que Windows: CityLearn editable, uc3m editable, numpy 1.23.5, ray[rllib]==1.8.0, gym/gymnasium, pvlib, scikit-learn, pandas, scipy, etc.).
6. `pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu126` (despues del paso 5, para reemplazar el torch CPU transitorio).
7. Verifica `nvidia-smi` y reporta `torch.__version__`, `torch.cuda.is_available()`, `torch.cuda.device_count()`.

### 5.1 Entrenamiento AWS con Docker / Docker Compose

Para EC2 Ubuntu con Docker, Compose V2 y NVIDIA Container Toolkit ya
configurados en el host, el contenedor se construye desde la raiz del repo y
reutiliza `requirements.txt` como fuente unica de dependencias. No instala
drivers NVIDIA ni CUDA del host dentro de la imagen; Docker expone la GPU al
contenedor mediante `--gpus all`/Compose.

```bash
cd ~/MADRLCitytleranflexresdr
git submodule update --init --recursive
docker run --rm --gpus all ubuntu:22.04 nvidia-smi
docker compose -f deploy/aws/training/docker-compose.yml up -d --build
docker compose -f deploy/aws/training/docker-compose.yml logs -f
```

El Compose lanza los 4 MADRL (`happo,masac,matd3,maac`) sobre los 3
escenarios (`E1,E2,E3`) con `--episodes 50`, `--episode-time-steps 8760`,
`--cuda`, `--log-chunk-size 10M` y `--log-max-files 100`.

Persistencia y organizacion:

- `outputs/` del host se monta en `/workspace/outputs` dentro del contenedor.
- Los artefactos quedan en `outputs/aws_citylearn_v3_madrl_<timestamp>/<algoritmo>/<escenario>_seed_0/`.
- Los logs se ven en `docker compose logs -f` y se guardan rotados en
  `logs/<escenario>_<algoritmo>-00001.log`, `00002.log`, etc.
- Si el entrenamiento termina correctamente se crea `outputs/.training_completed`.
- Si un job falla se crea `outputs/.training_failed` y el contenedor queda
  inactivo en el siguiente reinicio, evitando bucles infinitos con
  `restart: unless-stopped`.

Comandos utiles:

```bash
bash deploy/aws/training/tail_aws_training.sh
docker exec -it madrl-training nvidia-smi
docker exec -it madrl-training ps aux | grep python
docker compose -f deploy/aws/training/docker-compose.yml stop
docker compose -f deploy/aws/training/docker-compose.yml down
```

Manual operativo completo: `deploy/aws/README_TRAINING_AWS.md`.

## 6. Librerias clave y por que la version esta fija

| Libreria | Version fija | Por que no se puede subir |
| -------- | ------------- | -------------------------- |
| `numpy` | `1.23.5` | MARLlib 1.0.3 / Ray 1.8.0 rompen con NumPy >=2.0 |
| `ray[rllib]` | `1.8.0` | Backend MASAC depende de la API antigua de RLlib |
| `gym` | `0.20.0` | Compatibilidad con Ray 1.8.0 |
| `gymnasium` | `0.28.1` | Wrapper que usa CityLearn v2/v3 |
| `protobuf` | `3.20.3` | Conflicto con Ray 1.8.0 si se sube |
| `torch` | `2.8.0+cu126` | Version validada con RTX 4060 (CUDA 12.6) |
| `scikit-learn` | `<=1.2.2` | Compatibilidad de API con doe_xstock/CityLearn |

## 7. Verificacion final

Antes de lanzar una corrida larga, confirmar:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -m pip check
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\check_citylearn_v3_training_ready.py --strict --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json --scenario E1
```

Documentacion relacionada: `docs/architecture/dataset_construction_pipeline.md`, `docs/architecture/FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.md`, `deploy/aws/README_TRAINING_AWS.md`.
