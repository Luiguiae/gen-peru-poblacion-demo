# Demo — gen-peru-poblacion

Demo interactiva de la librería [`gen-peru-poblacion`](https://pypi.org/project/gen-peru-poblacion/), que genera perfiles sintéticos de población peruana calibrados con datos del INEI, PRODUCE y SBS 2023.

## Funcionalidades

- **Sección 1 — Generador de perfiles**: genera entre 1 y 50 perfiles sintéticos filtrables por segmento y región, con descarga en CSV y JSON.
- **Sección 2 — Agente conversacional**: conversa en tiempo real con un perfil generado usando DeepSeek como LLM. El agente adopta la voz y contexto del perfil seleccionado.

## Uso local

### 1. Clonar el repositorio

```bash
git clone https://github.com/luiguiavilae/gen-peru-poblacion-demo.git
cd gen-peru-poblacion-demo
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

> **Nota**: La primera vez que generes perfiles, SDV entrenará un modelo (~30 s). Las ejecuciones siguientes usan caché (`.sdv_model_*.pkl`).

### 3. Ejecutar la app

```bash
streamlit run app.py
```

La app abre automáticamente en `http://localhost:8501`.

## Uso del agente conversacional

1. Genera perfiles en la Sección 1.
2. Obtén una API Key gratuita en [platform.deepseek.com](https://platform.deepseek.com).
3. Ingresa la clave en el campo **API Key de DeepSeek** (solo se usa en memoria durante la sesión, nunca se guarda).
4. Selecciona un perfil del dropdown y comienza a conversar.

## Despliegue en Streamlit Cloud

1. Haz fork del repositorio en GitHub.
2. Ve a [share.streamlit.io](https://share.streamlit.io) y conecta tu repositorio.
3. Configura:
   - **Main file**: `app.py`
   - **Python version**: 3.11
4. Despliega — no se requieren secrets para el generador de perfiles; la API Key se ingresa en la UI.

## Segmentos disponibles

| Segmento | Descripción |
|---|---|
| `mype` | Microempresas y pequeñas empresas |
| `consumidores` | Consumidores finales |
| `financiero` | Usuarios del sistema financiero |
| `salud` | Usuarios del sistema de salud |

## Fuentes de datos

Los perfiles se calibran con distribuciones agregadas de:
- **INEI** — ENAHO 2023
- **PRODUCE** — ENAMIN 2023
- **SBS** — Estadísticas del sistema financiero 2023

Ningún perfil es trazable a personas individuales. Los datos son 100 % sintéticos.
