"""Restaura language_info en metadata del notebook para que Colab reconozca Python."""
import json
from pathlib import Path

NB = Path("d:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb")
with open(NB, "r", encoding="utf-8") as f:
    nb = json.load(f)

nb["metadata"]["language_info"] = {
    "name": "python",
    "version": "3.10.12",  # version que usa Colab por defecto (3.10.x)
    "mimetype": "text/x-python",
    "codemirror_mode": {"name": "ipython", "version": 3},
    "pygments_lexer": "ipython3",
    "nbformat": 4,
    "file_extension": ".py"
}

# Asegurar kernelspec correcto para Colab
nb["metadata"]["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3"
}

# Asegurar acelerador GPU A100
nb["metadata"]["accelerator"] = "GPU"
nb["metadata"]["colab"]["gpuType"] = "A100"

# nbformat requerido
nb["nbformat"] = 4
nb["nbformat_minor"] = 5

with open(NB, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

# Verificar
with open(NB, "r", encoding="utf-8") as f:
    nb2 = json.load(f)
m = nb2["metadata"]
assert m["language_info"]["version"] == "3.10.12"
assert m["kernelspec"]["name"] == "python3"
assert m["accelerator"] == "GPU"
assert m["colab"]["gpuType"] == "A100"
print("OK metadata:")
print(f"  language_info.version = {m['language_info']['version']}")
print(f"  kernelspec.name       = {m['kernelspec']['name']}")
print(f"  accelerator           = {m['accelerator']}")
print(f"  colab.gpuType         = {m['colab']['gpuType']}")
