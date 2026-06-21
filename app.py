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
if "focus_history" not in st.session_state:
    # Lista de {"pregunta": str, "respuestas": [{"perfil": dict, "respuesta": str}]}
    st.session_state.focus_history = []


def _reset_focus_group() -> None:
    st.session_state.focus_history = []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _card_header(i: int, perfil: dict) -> str:
    detail = (
        perfil.get("rubro")
        or perfil.get("nivel_socioeconomico")
        or perfil.get("tipo_entidad_principal")
        or perfil.get("tipo_seguro")
        or "—"
    )
    edad = perfil.get("edad_dueño") or perfil.get("edad") or "?"
    adopcion = perfil.get("adopcion_digital", "")
    header = f"Perfil {i + 1} — {detail} | {perfil.get('region', '?')} | {edad} años"
    if adopcion:
        header += f" | adopción: {adopcion}"
    return header


def _render_profile_fields(perfil: dict) -> None:
    items = {k: v for k, v in perfil.items() if k not in ("data_sources", "synthetic")}
    col_a, col_b = st.columns(2)
    entries = list(items.items())
    half = len(entries) // 2
    with col_a:
        for k, v in entries[:half]:
            st.text(f"{k}: {v}")
    with col_b:
        for k, v in entries[half:]:
            st.text(f"{k}: {v}")


def _render_card(i: int, perfil: dict, respuesta: str, *, show_expander: bool = True) -> None:
    """Renderiza la card de un perfil con su respuesta."""
    with st.container(border=True):
        st.markdown(f"**{_card_header(i, perfil)}**")
        st.markdown(respuesta)
        if show_expander:
            with st.expander("Ver perfil completo"):
                _render_profile_fields(perfil)


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
            _reset_focus_group()
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
# SECCIÓN 2 — FOCUS GROUP SINTÉTICO
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.header("Sección 2 — Focus group sintético")
st.caption("Escribe una pregunta y todos los perfiles responden en secuencia.")

api_key = st.text_input(
    "API Key de DeepSeek",
    type="password",
    placeholder="sk-...",
    help="Tu clave de API de DeepSeek. No se almacena ni se registra entre sesiones.",
)

if not st.session_state.perfiles:
    st.info("Primero genera perfiles en la **Sección 1** para activar el focus group.")
    st.stop()

# ── Historial de preguntas anteriores (colapsado) ─────────────────────────────
# Se muestran todas las entradas menos la última (que se muestra abajo expandida)
previous_entries = st.session_state.focus_history[:-1]
if previous_entries:
    with st.expander(
        f"Preguntas anteriores ({len(previous_entries)})",
        expanded=False,
    ):
        for entry in reversed(previous_entries):
            st.markdown(f"**❓ {entry['pregunta']}**")
            for i, r in enumerate(entry["respuestas"]):
                # Sin expander anidado para evitar conflicto con el expander padre
                _render_card(i, r["perfil"], r["respuesta"], show_expander=False)
            if entry is not previous_entries[0]:
                st.divider()

# ── Última respuesta / resultados de la pregunta más reciente ─────────────────
if st.session_state.focus_history:
    latest = st.session_state.focus_history[-1]
    st.markdown(f"### ❓ {latest['pregunta']}")
    for i, r in enumerate(latest["respuestas"]):
        _render_card(i, r["perfil"], r["respuesta"], show_expander=True)
    st.divider()

# ── Input de pregunta ─────────────────────────────────────────────────────────
pregunta = st.text_area(
    "Escribe tu pregunta al grupo...",
    placeholder="Ej: ¿Cuál es tu mayor dificultad para cobrar a tus clientes?",
    height=100,
)

col_ask, col_reset = st.columns([3, 1])
with col_ask:
    preguntar_btn = st.button(
        f"Preguntar al grupo  ({len(st.session_state.perfiles)} perfiles)",
        type="primary",
        use_container_width=True,
    )
with col_reset:
    nueva_sesion_btn = st.button(
        "🗑️ Nueva sesión",
        use_container_width=True,
    )

# ── Acciones ──────────────────────────────────────────────────────────────────
if nueva_sesion_btn:
    _reset_focus_group()
    st.rerun()

if preguntar_btn:
    if not api_key:
        st.error("⚠️ Ingresa tu API Key de DeepSeek antes de preguntar al grupo.")
        st.stop()
    if not pregunta.strip():
        st.warning("⚠️ Escribe una pregunta antes de enviar.")
        st.stop()

    from gen_peru_poblacion.agent_builder import AgentBuilder  # noqa: PLC0415
    from gen_peru_poblacion.providers import DeepSeekProvider  # noqa: PLC0415

    current_entry: dict = {"pregunta": pregunta.strip(), "respuestas": []}

    for i, perfil in enumerate(st.session_state.perfiles):
        header = _card_header(i, perfil)

        with st.status(f"⏳ {header}", expanded=True) as status:
            try:
                provider = DeepSeekProvider(api_key=api_key)
                agent = AgentBuilder.from_profile(perfil, provider)
                response = agent.chat(pregunta.strip())

                status.update(label=f"✅ {header}", state="complete", expanded=True)
                st.markdown(response)
                with st.expander("Ver perfil completo"):
                    _render_profile_fields(perfil)

            except Exception as exc:
                response = f"Error: {exc}"
                status.update(label=f"❌ {header}", state="error", expanded=True)
                st.error(str(exc))

        current_entry["respuestas"].append({"perfil": perfil, "respuesta": response})

    st.session_state.focus_history.append(current_entry)
    st.rerun()
