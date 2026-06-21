import json
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Paths ─────────────────────────────────────────────────────────────────────
FUENTE_DIR = str(Path(__file__).parent / "data" / "fuentes")

# ── Mapeos UI → valores internos ─────────────────────────────────────────────
REGION_MAP = {
    "Lima": "lima_metropolitana",
    "Norte": "costa_norte",
    "Sur": "costa_sur",
    "Oriente": "selva",
    "Centro": "sierra_centro",
}

SEGMENTOS = ["mype", "consumidores", "financiero", "salud"]

SEGMENTO_LABEL = {
    "mype": "MYPE (microempresa)",
    "consumidores": "Consumidores",
    "financiero": "Sector financiero",
    "salud": "Salud",
}

# ── Config de página ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Demo — gen-peru-poblacion",
    page_icon="🇵🇪",
    layout="wide",
)

# ── Session state ─────────────────────────────────────────────────────────────
if "perfiles" not in st.session_state:
    st.session_state.perfiles = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "active_profile_id" not in st.session_state:
    st.session_state.active_profile_id = None


def _reset_chat():
    st.session_state.chat_history = []
    st.session_state.agent = None
    st.session_state.active_profile_id = None


def _profile_label(i: int, p: dict) -> str:
    detail = (
        p.get("rubro")
        or p.get("nivel_socioeconomico")
        or p.get("tipo_entidad_principal")
        or p.get("tipo_seguro")
        or "—"
    )
    return f"#{i + 1}  {detail}  |  {p.get('region', '?')}  |  id:{p.get('perfil_id', '')[:8]}"


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Parámetros")
    st.markdown("---")

    segmento = st.selectbox(
        "Segmento",
        options=SEGMENTOS,
        format_func=lambda s: SEGMENTO_LABEL[s],
        index=0,
    )

    region = st.selectbox(
        "Región",
        options=list(REGION_MAP.keys()),
        index=0,
    )

    n_profiles = st.slider(
        "Número de perfiles",
        min_value=1,
        max_value=50,
        value=10,
    )

    generar_btn = st.button(
        "Generar perfiles",
        type="primary",
        use_container_width=True,
    )

    st.markdown("---")
    st.caption(
        "Datos calibrados con fuentes **INEI**, **PRODUCE** y **SBS** 2023. "
        "Los perfiles son 100 % sintéticos — ningún dato corresponde a personas reales."
    )

# ─────────────────────────────────────────────────────────────────────────────
# ENCABEZADO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
st.title("🇵🇪 Generador de Población Sintética — Perú")
st.caption("Demo interactiva de la librería **gen-peru-poblacion** (PyPI)")

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — GENERADOR DE PERFILES
# ─────────────────────────────────────────────────────────────────────────────
st.header("Sección 1 — Generador de perfiles")

if generar_btn:
    with st.spinner("Generando perfiles sintéticos..."):
        try:
            from gen_peru_poblacion import Config, PopulationGenerator  # noqa: PLC0415

            config = Config(
                segmento=segmento,
                n=n_profiles,
                region=REGION_MAP[region],
                fuente_dir=FUENTE_DIR,
            )
            gen = PopulationGenerator(config)
            perfiles = gen.generate()
            st.session_state.perfiles = perfiles
            _reset_chat()
            st.success(
                f"Se generaron **{len(perfiles)} perfiles** · "
                f"segmento: **{SEGMENTO_LABEL[segmento]}** · región: **{region}**"
            )
        except Exception as exc:
            st.error(f"Error al generar perfiles: {exc}")

if st.session_state.perfiles:
    df = pd.DataFrame(st.session_state.perfiles)

    # Columnas de metadatos al final para mejor lectura
    meta_cols = ["perfil_id", "synthetic", "data_sources", "segmento"]
    data_cols = [c for c in df.columns if c not in meta_cols]
    df = df[data_cols + [c for c in meta_cols if c in df.columns]]

    st.dataframe(df, use_container_width=True, height=320)

    col_csv, col_json, _ = st.columns([1, 1, 3])
    with col_csv:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar CSV",
            data=csv_bytes,
            file_name=f"perfiles_{segmento}_{region.lower()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_json:
        json_bytes = json.dumps(
            st.session_state.perfiles, ensure_ascii=False, indent=2, default=str
        ).encode("utf-8")
        st.download_button(
            "⬇️ Descargar JSON",
            data=json_bytes,
            file_name=f"perfiles_{segmento}_{region.lower()}.json",
            mime="application/json",
            use_container_width=True,
        )
else:
    st.info(
        "Configura los parámetros en la barra lateral y haz clic en **Generar perfiles** "
        "para ver los resultados aquí."
    )

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2 — AGENTE CONVERSACIONAL
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.header("Sección 2 — Agente conversacional")

api_key = st.text_input(
    "API Key de DeepSeek",
    type="password",
    placeholder="sk-...",
    help="Tu clave de API de DeepSeek. No se almacena ni se registra entre sesiones.",
)

if not st.session_state.perfiles:
    st.info("Primero genera perfiles en la **Sección 1** para activar el agente conversacional.")
    st.stop()

# ── Selector de perfil ────────────────────────────────────────────────────────
profile_labels = [_profile_label(i, p) for i, p in enumerate(st.session_state.perfiles)]


def _on_profile_change():
    _reset_chat()


selected_idx = st.selectbox(
    "Perfil con el que vas a conversar",
    options=range(len(profile_labels)),
    format_func=lambda i: profile_labels[i],
    key="profile_selector",
    on_change=_on_profile_change,
)

selected_profile = st.session_state.perfiles[selected_idx]

# Inicializar agente cuando el perfil se selecciona por primera vez
if st.session_state.active_profile_id != selected_profile.get("perfil_id"):
    st.session_state.agent = None
    st.session_state.chat_history = []
    st.session_state.active_profile_id = selected_profile.get("perfil_id")

# ── Detalle del perfil seleccionado ──────────────────────────────────────────
with st.expander("Ver detalle del perfil seleccionado", expanded=False):
    items = {k: v for k, v in selected_profile.items() if k not in ("data_sources", "synthetic")}
    col_a, col_b = st.columns(2)
    entries = list(items.items())
    half = len(entries) // 2
    with col_a:
        for k, v in entries[:half]:
            st.text(f"{k}: {v}")
    with col_b:
        for k, v in entries[half:]:
            st.text(f"{k}: {v}")

# ── Controles de conversación ─────────────────────────────────────────────────
col_reset, _ = st.columns([1, 5])
with col_reset:
    if st.button("🔄 Nueva conversación", use_container_width=True):
        _reset_chat()
        st.rerun()

# ── Historial de chat ─────────────────────────────────────────────────────────
st.subheader("Conversación")

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input del usuario ─────────────────────────────────────────────────────────
user_input = st.chat_input("Escribe tu pregunta al agente...")

if user_input:
    if not api_key:
        st.error("⚠️ Ingresa tu API Key de DeepSeek antes de enviar un mensaje.")
        st.stop()

    # Mostrar mensaje del usuario de inmediato
    with st.chat_message("user"):
        st.markdown(user_input)

    # Obtener respuesta del agente
    with st.spinner("El agente está pensando..."):
        try:
            if st.session_state.agent is None:
                from gen_peru_poblacion.agent_builder import AgentBuilder  # noqa: PLC0415
                from gen_peru_poblacion.providers import DeepSeekProvider  # noqa: PLC0415

                provider = DeepSeekProvider(api_key=api_key)
                st.session_state.agent = AgentBuilder.from_profile(selected_profile, provider)

            response = st.session_state.agent.chat(user_input)

        except Exception as exc:
            response = f"❌ Error al procesar la respuesta: {exc}"

    # Mostrar y guardar respuesta
    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "assistant", "content": response})
