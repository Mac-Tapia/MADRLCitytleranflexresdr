## Paso 0: Conectar VS Code al runtime A100 de Google Colab

> Haz este paso **UNA SOLA VEZ** antes de ejecutar cualquier celda.
> No se necesita ngrok ni tunnels: la extension `google.colab` de VS Code
> maneja la conexion directamente con tu cuenta de Google.

---

### 0.1  Seleccionar el kernel Colab en VS Code

1. Abre este notebook en VS Code
   (`CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb`)
2. Haz clic en **"Select Kernel"** (esquina superior derecha del notebook)
3. En el menu emergente elige **"Google Colab"**
   (aparece gracias a la extension `google.colab` ya instalada)
4. Si pide autenticacion → inicia sesion con **cualquier cuenta Google** que tenga Colab Pro+ y espacio en Drive (ej. **mactapiacc@gmail.com**)
5. En la lista de runtimes elige **"New Colab Server"** → acelerador **A100** → forma **High-RAM**
   *(NO elijas "Standard": 40 GiB VRAM + ~83 GiB RAM no alcanza; necesitas ~80 GiB VRAM + ~167 GiB RAM)*
   *(Colab Pro+ debe estar activo en la cuenta que elijas; no hay restriccion de correo en el notebook)*

> Si no ves "Google Colab" en el selector: abre la paleta de comandos
> (`Ctrl+Shift+P`) y escribe **"Colab: Sign In"**, autentica, luego repite.

---

### 0.2  Verificar la conexion

Ejecuta la celda de codigo siguiente. Debe mostrar:
```
GPU: NVIDIA A100-SXM4-80GB  RAM: ~167 GiB  Tipo: Colab
```
Si muestra otra GPU, menos VRAM o error → vuelve al paso 0.1 y verifica el tipo de runtime (A100 High-RAM).

---

### 0.3  Flujo de trabajo diario

```
VS Code (editor local)
       │
       │  google.colab extension
       ▼
Colab A100 runtime (servidor Google)
  /content/MADRLCitytleranflexresdr/   ← repo clonado en celda 1.2
  /content/drive/MyDrive/MADRLCitytleranflexresdr/outputs/  ← checkpoints en Drive
```

- El **codigo se ejecuta en el A100** de Google.
- Los **outputs y graficas** aparecen directamente en VS Code.
- Si Colab desconecta: repetir 0.1, luego reanudar desde celda 1.2.

> **Apertura directa en Colab (sin VS Code):**
> Haz clic en el badge del titulo o accede directamente:
> [`https://colab.research.google.com/github/Mac-Tapia/CityLearn/blob/codex/iquitos-distillation-madrl-docs/examples/madrl_citylearn_v3_tutorial.ipynb`](https://colab.research.google.com/github/Mac-Tapia/CityLearn/blob/codex/iquitos-distillation-madrl-docs/examples/madrl_citylearn_v3_tutorial.ipynb)
>
> Rama GitHub del notebook: `Mac-Tapia/CityLearn` → `codex/iquitos-distillation-madrl-docs`. Tras cada push, el badge abre esa version.
