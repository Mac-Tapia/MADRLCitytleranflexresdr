# Despliegue en Kubernetes — Demo MADRL Iquitos

Manifests para levantar la **demo de operatividad** (NO entrenamiento) del stack
MADRL CityLearn v3 (Iquitos) sobre un clúster Kubernetes local:

- **mongo** (`mongo:7`): capa de persistencia/análisis (PVC `1Gi` en `/data/db`).
- **inference** (`madrl-inference:local`): FastAPI; arranca en **modo stub**
  (política aleatoria) porque `MODEL_PATH` apunta a una ruta inexistente a
  propósito. Persiste cada `/act` en MongoDB y expone analítica.
- **dashboard** (`madrl-dashboard:local`): panel Streamlit.
- **ingress** (clase `nginx`): acceso web opcional (`/` → dashboard, `/api` → inference).

> **Nota:** En esta sesión los manifests fueron creados y validados solo a nivel
> de *render* (`kubectl kustomize`). **No** se aplicaron a un clúster real ni se
> construyeron las imágenes (el daemon de Docker no estaba disponible).

## Recursos

| Archivo               | Recursos                                             |
|-----------------------|------------------------------------------------------|
| `namespace.yaml`      | Namespace `madrl`                                    |
| `mongo.yaml`          | PVC + Deployment + Service `mongo:27017`             |
| `inference.yaml`      | Deployment + Service `inference:8000`                |
| `dashboard.yaml`      | Deployment + Service `dashboard:8501`                |
| `ingress.yaml`        | Ingress `nginx` (`madrl.local`)                      |
| `kustomization.yaml`  | Agrupa todo en el namespace `madrl`                  |

## 1. Construir las imágenes

Desde la raíz del repo (`D:\MADRLCitytleranflexresdr`):

```bash
docker build -t madrl-inference:local deploy/inference
docker build -t madrl-dashboard:local deploy/dashboard
```

## 2. Cargar las imágenes en el clúster local

Las imágenes son locales (`imagePullPolicy: IfNotPresent`), así que hay que
ponerlas a disposición del clúster según el runtime:

- **kind:**
  ```bash
  kind load docker-image madrl-inference:local
  kind load docker-image madrl-dashboard:local
  ```
- **minikube:**
  ```bash
  minikube image load madrl-inference:local
  minikube image load madrl-dashboard:local
  ```
- **Docker Desktop (Kubernetes habilitado):** usa el mismo daemon de Docker, así
  que las imágenes locales ya están disponibles; no hace falta cargarlas.

## 3. Aplicar los manifests

```bash
kubectl apply -k deploy/k8s/
```

## 4. Verificar

```bash
kubectl get pods -n madrl
kubectl get svc  -n madrl
```

Espera a que `inference`, `mongo` y `dashboard` estén `Running`/`Ready`.

## 5. Probar con port-forward (sin ingress)

```bash
kubectl port-forward -n madrl svc/inference 8000:8000
```

En otra terminal:

```bash
# Liveness/readiness
curl http://localhost:8000/health

# Inferencia (modo stub) — 2 agentes, obs_dim 29
curl -X POST http://localhost:8000/act \
  -H "Content-Type: application/json" \
  -d "{\"observations\": [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1]]}"

# Analítica agregada (lee de MongoDB)
curl http://localhost:8000/analytics/summary
curl "http://localhost:8000/analytics/recent?limit=5"
```

Dashboard:

```bash
kubectl port-forward -n madrl svc/dashboard 8501:8501
# abrir http://localhost:8501
```

## 6. (Opcional) Acceso web vía Ingress

Requiere un ingress-controller NGINX instalado y resolver `madrl.local` a la IP
del ingress (editar el archivo `hosts`). Detalles en los comentarios de
`ingress.yaml`. Rutas:

- `http://madrl.local/` → dashboard
- `http://madrl.local/api/health` → inference `/health`

## Validación de los manifests (sin clúster)

```bash
# Render + comprobación de sintaxis kustomize
kubectl kustomize deploy/k8s/

# Si tienes kubeconform instalado, valida el render contra esquemas:
kubectl kustomize deploy/k8s/ | kubeconform -strict -summary
```

> No ejecutes `kubectl apply --dry-run=server` ni `apply` real si no tienes un
> clúster/kubeconfig activo.

## Variables de entorno relevantes (inference)

| Variable           | Default                                  | Descripción                                  |
|--------------------|------------------------------------------|----------------------------------------------|
| `MONGODB_URI`      | `mongodb://mongo:27017`                  | Si falta o no conecta, persistencia OFF.     |
| `MONGODB_DB`       | `madrl`                                  | Base de datos.                               |
| `MONGODB_COLLECTION`| `inferences`                            | Colección de inferencias.                    |
| `MODEL_PATH`       | (ruta inexistente → stub)                | Apunta a un `.onnx` real para modo no-stub.  |
