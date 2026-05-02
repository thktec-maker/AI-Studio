import streamlit as st
import urllib.parse
import random
import requests
import time
from datetime import datetime

# ──────────────────────────────────────────────────────────────
# 1. CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Studio Pro",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────
# 2. TABLA DE ESTILOS RÁPIDOS
# ──────────────────────────────────────────────────────────────
# Cada estilo tiene:
# - id: para manejar estado
# - label: lo que ve el usuario
# - inj: texto que se inyecta al prompt para el modelo (en inglés, preciso)

QUICK_STYLES = [
    {
        "id": "realismo",
        "label": "🎨 Realismo",
        "inj": "ultra realistic, 8k photography, sharp focus, natural lighting"
    },
    {
        "id": "cinematic",
        "label": "🎬 Cinematic",
        "inj": "cinematic still frame from a movie, dramatic lighting, shallow depth of field, 35mm lens"
    },
    {
        "id": "cyberpunk",
        "label": "🌌 Cyberpunk",
        "inj": "cyberpunk style, neon lights, rainy atmosphere, high contrast, futuristic city mood"
    },
    {
        "id": "ilustracion",
        "label": "🖌️ Ilustración",
        "inj": "digital illustration, clean line art, soft shading, artstation quality"
    },
    {
        "id": "naturaleza",
        "label": "🌿 Naturaleza",
        "inj": "natural environment, soft daylight, realistic plants and rocks, peaceful mood"
    },
    {
        "id": "magico",
        "label": "✨ Mágico",
        "inj": "fantasy magical atmosphere, glowing particles, ethereal lighting, high detail"
    },
]

# ──────────────────────────────────────────────────────────────
# 3. UTILIDADES PROMPT / URL
# ──────────────────────────────────────────────────────────────

def limpiar_prompt(prompt: str) -> str:
    """
    Versión “humana” del prompt para título:
    - Elimina duplicados separados por coma
    - Recorta a ~80 caracteres
    """
    p = " ".join(prompt.split())
    partes = [s.strip() for s in p.split(",") if s.strip()]
    usados = set()
    unicas = []
    for s in partes:
        clave = s.lower()
        if clave not in usados:
            usados.add(clave)
            unicas.append(s)
    limpio = ", ".join(unicas)
    return (limpio[:82] + "...") if len(limpio) > 85 else limpio.capitalize()


def deduplicar_prompt(prompt: str) -> str:
    """
    Limpia el prompt ANTES de enviarlo a la API:
    - Elimina frases repetidas
    """
    partes = [s.strip() for s in prompt.split(",") if s.strip()]
    usados = set()
    unicas = []
    for s in partes:
        if s.lower() not in usados:
            usados.add(s.lower())
            unicas.append(s)
    return ", ".join(unicas)


def construir_url(prompt: str, w: int, h: int, seed: int,
                  model_tag: str, enhance: bool, neg_prompt: str) -> str:
    p_enc = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{p_enc}"
        f"?width={w}&height={h}&seed={seed}"
        f"&nologo=true&enhance={'true' if enhance else 'false'}"
        f"&model={model_tag}"
    )
    if neg_prompt.strip():
        url += f"&negative={urllib.parse.quote(neg_prompt.strip())}"
    return url


def map_modelo(modelo: str) -> str:
    """Mapea el select de UI al tag interno de modelo."""
    if "FLUX" in modelo:
        return "flux"
    if "Stable" in modelo or "SDXL" in modelo:
        return "sdxl"
    return "turbo"


def estimar_tiempo(modelo: str, resolucion: str, detalle: str) -> tuple[float, float]:
    """
    Heurística simple de tiempo estimado en segundos (min, max).
    Ajusta estos valores según tus mediciones reales.
    """
    base = 3.0

    # Resolución
    if "1024" in resolucion:
        base += 2.0
    elif "768" in resolucion:
        base += 1.0

    # Modelo
    if "Pro" in modelo or "Dev" in modelo:
        base += 1.5
    elif "Turbo" in modelo:
        base -= 0.5

    # Detalle
    if detalle == "Alto":
        base += 2.0
    elif detalle == "Bajo":
        base -= 1.0

    base = max(1.5, base)
    return base * 0.7, base * 1.3  # rango min–max


def get_style_by_id(style_id: str):
    for s in QUICK_STYLES:
        if s["id"] == style_id:
            return s
    return None


# ──────────────────────────────────────────────────────────────
# 4. CSS / LAYOUT
# ──────────────────────────────────────────────────────────────

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --primary: #10a37f;
    --primary-dark: #059669;
    --primary-glow: rgba(16,163,127,0.35);
    --bg-card: #ffffff;
    --border: #e5e7eb;
    --text-main: #111827;
    --text-sub: #4b5563;
    --text-muted: #9ca3af;
}

/* Ocultar chrome de Streamlit */
#MainMenu, footer, header { visibility: hidden; }

.stApp {
    font-family: 'Inter', system-ui, sans-serif;
    background: radial-gradient(circle at top left, #dbeafe 0%, #f9fafb 35%, #f3f4f6 100%);
}

/* Contenedor principal centrado */
main .block-container {
    max-width: 980px !important;
    padding: 1.5rem 1.75rem 3rem !important;
    margin: 0 auto !important;
}

/* Topbar */
.ai-topbar {
    text-align: center;
    margin-bottom: 1.5rem;
}
.ai-topbar h1 {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text-main);
    margin-bottom: 0.1rem;
}
.ai-topbar p {
    font-size: 1rem;
    color: var(--text-sub);
}

/* Card principal */
.st-key-main-card {
    background: var(--bg-card);
    border-radius: 20px !important;
    border: 1px solid var(--border) !important;
    padding: 1.6rem 1.9rem !important;
    box-shadow: 0 18px 40px rgba(15,23,42,0.10) !important;
}

/* Textarea */
.stTextArea textarea {
    border-radius: 12px !important;
    padding: 0.85rem 1rem !important;
    border: 1px solid var(--border) !important;
    font-size: 1.02rem !important;
    line-height: 1.6 !important;
    background: #fafafa !important;
}

/* Labels */
.stSelectbox label, .stSlider label, label {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: var(--text-sub) !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Selects */
.stSelectbox [data-baseweb="select"] > div {
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    font-size: 0.9rem !important;
    padding: 0.25rem 0.5rem !important;
    background: #fafafa !important;
}

/* Botones principales */
.stButton > button {
    width: 100% !important;
    border-radius: 999px !important;
    border: none !important;
    padding: 0.7rem 1.2rem !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
    color: white !important;
    box-shadow: 0 8px 22px var(--primary-glow) !important;
    transition: transform 0.12s ease, box-shadow 0.12s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
}

/* Botón descarga */
.stDownloadButton > button {
    border-radius: 999px !important;
    border: 1px solid var(--border) !important;
    padding: 0.65rem 1rem !important;
    font-size: 0.88rem !important;
    background: #f9fafb !important;
    color: var(--text-sub) !important;
}

/* Estilos rápidos (chips) */
.ai-styles-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-bottom: 0.8rem;
}
.ai-chip-btn > button {
    border-radius: 999px !important;
    border: 1px solid var(--border) !important;
    padding: 0.25rem 0.8rem !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    background: #f9fafb !important;
    color: var(--text-sub) !important;
    box-shadow: none !important;
}
.ai-chip-btn-active > button {
    border-color: var(--primary) !important;
    background: rgba(16,163,127,0.06) !important;
    color: var(--primary) !important;
}

/* Resultados */
.ai-divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.4rem 0 1.1rem;
}
.ai-results-label {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.4rem;
}
.ai-results-title {
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--text-main);
    margin-bottom: 0.5rem;
}
.ai-meta-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.8rem;
    padding: 0.18rem 0.6rem;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: #f3f4f6;
    color: var(--text-sub);
    margin-right: 0.3rem;
    margin-bottom: 0.3rem;
}

/* Imagen */
.ai-img-frame {
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.7);
    box-shadow: 0 20px 45px rgba(15,23,42,0.25);
    max-height: 420px;
    overflow: hidden;
    background: #0b1120;
    display: flex;
    align-items: center;
    justify-content: center;
}
.ai-img-frame img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    max-height: 420px;
}

/* Placeholder */
.ai-placeholder {
    background: #f9fafb;
    border-radius: 16px;
    border: 1.5px dashed #d1d5db;
    padding: 2.5rem 1.5rem;
    text-align: center;
    color: var(--text-muted);
    font-size: 0.9rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────
# 5. ESTADO
# ──────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "history": [],
        "current": None,
        "last_prompt": "",
        "active_style": None,      # id del estilo seleccionado
        "last_time": None,
        "last_estimate": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ──────────────────────────────────────────────────────────────
# 6. TOPBAR
# ──────────────────────────────────────────────────────────────

st.markdown(
    """
<div class="ai-topbar">
  <h1>AI Studio Pro</h1>
  <p>Genera imágenes con IA · Pollinations · FLUX · SDXL · Turbo</p>
</div>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────
# 7. PANEL PRINCIPAL (PROMPT + PARÁMETROS + ESTILOS)
# ──────────────────────────────────────────────────────────────

with st.container(key="main-card"):

    # Estilos rápidos FUNCIONALES (solo uno activo)
    st.markdown('<div class="ai-styles-row">', unsafe_allow_html=True)
    cols = st.columns(len(QUICK_STYLES))
    for i, style in enumerate(QUICK_STYLES):
        is_active = st.session_state.active_style == style["id"]
        cls = "ai-chip-btn-active" if is_active else "ai-chip-btn"
        with cols[i]:
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            clicked = st.button(style["label"], key=f"style_{style['id']}")
            st.markdown("</div>", unsafe_allow_html=True)

            if clicked:
                # Exclusivo: si estaba activo, lo quitamos; si no, activamos este y desactivamos el resto
                if is_active:
                    st.session_state.active_style = None
                else:
                    st.session_state.active_style = style["id"]
    st.markdown("</div>", unsafe_allow_html=True)

    # Prompt principal (base, sin estilo)
    prompt = st.text_area(
        "Describe tu imagen",
        value=st.session_state.last_prompt,
        placeholder="Ejemplo: small tabby cat standing on a blue asteroid in deep space, cinematic lighting...",
        height=90,
        label_visibility="collapsed",
    )

    # Parámetros
    col_modelo, col_res, col_det = st.columns([1.4, 1.1, 1.0])
    with col_modelo:
        modelo = st.selectbox(
            "Motor de IA",
            ["FLUX.1 [Dev]", "FLUX.1 Pro", "SDXL", "Turbo"],
        )
    with col_res:
        resolucion = st.selectbox(
            "Dimensión",
            ["832×832 (1:1)", "1024×1024 (1:1)", "768×1024 (3:4)"],
        )
    with col_det:
        detalle = st.select_slider(
            "Nivel de detalle",
            options=["Bajo", "Estándar", "Alto"],
            value="Estándar",
        )

    with st.expander("Opciones avanzadas", expanded=False):
        neg_prompt = st.text_input(
            "Qué NO quieres que aparezca",
            value="frame, border, text, watermark, logo",
            help="Se envía como negative prompt a la API para evitar elementos indeseados.",
        )

    c_gen, c_var = st.columns([2, 1])
    with c_gen:
        btn_gen = st.button("✨ Generar imagen", use_container_width=True)
    with c_var:
        btn_var = st.button("🔄 Crear variante", use_container_width=True)

    # ───── LÓGICA DE GENERACIÓN ─────
    lanzar = btn_gen or btn_var
    if lanzar:
        if not prompt.strip() and not st.session_state.last_prompt:
            st.warning("Escribe un prompt antes de generar.")
        else:
            if prompt.strip():
                st.session_state.last_prompt = prompt.strip()

            base_prompt = st.session_state.last_prompt

            # 1) Aplicar estilo activo (si hay) → prompt para la API
            estilo = get_style_by_id(st.session_state.active_style) if st.session_state.active_style else None
            if estilo:
                prompt_combinado = f"{estilo['inj']}, {base_prompt}"
            else:
                prompt_combinado = base_prompt

            # 2) Deduplicar
            prompt_api = deduplicar_prompt(prompt_combinado)

            # Semilla
            seed = random.randint(1, 99_999_999)

            # Dimensiones
            if "1024" in resolucion:
                w, h = 1024, 1024
            elif "768×1024" in resolucion:
                w, h = 768, 1024
            else:
                w, h = 832, 832

            # Modelo y detalle
            model_tag = map_modelo(modelo)
            enhance = detalle == "Alto"

            # Estimación de tiempo
            t_min, t_max = estimar_tiempo(modelo, resolucion, detalle)
            st.session_state.last_estimate = (t_min, t_max)

            url = construir_url(
                prompt=prompt_api,
                w=w,
                h=h,
                seed=seed,
                model_tag=model_tag,
                enhance=enhance,
                neg_prompt=neg_prompt,
            )

            with st.status(
                f"🎨 Generando... (estimado {t_min:0.1f}–{t_max:0.1f} s)",
                expanded=True,
            ) as status:
                st.write(f"Prompt base: `{base_prompt}`")
                if estilo:
                    st.write(f"Estilo aplicado: `{estilo['inj']}`")
                st.write(f"Prompt final para la API: `{prompt_api}`")
                st.write(f"Modelo: **{modelo}** · Resolución: **{resolucion}** · Detalle: **{detalle}**")
                st.write(f"URL: `{url}`")

                t0 = time.time()
                try:
                    r = requests.get(url, timeout=int(t_max) + 15)
                    elapsed = time.time() - t0
                    st.session_state.last_time = elapsed

                    if r.status_code == 200 and len(r.content) > 1000:
                        result = {
                            "prompt": base_prompt,
                            "prompt_api": prompt_api,
                            "seed": seed,
                            "url": url,
                            "bytes": r.content,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "modelo": modelo,
                            "resolucion": resolucion,
                            "detalle": detalle,
                            "elapsed": elapsed,
                            "style_id": estilo["id"] if estilo else None,
                        }
                        st.session_state.current = result
                        st.session_state.history.insert(0, result)
                        status.update(label="✅ Imagen generada", state="complete")
                    else:
                        st.error(f"Error {r.status_code} al obtener la imagen.")
                        status.update(label="❌ Error al generar", state="error")
                except requests.exceptions.Timeout:
                    elapsed = time.time() - t0
                    st.session_state.last_time = elapsed
                    st.error("⏱️ Tiempo de espera agotado. La API está lenta, intenta de nuevo.")
                    status.update(label="⏱️ Timeout", state="error")
                except Exception as e:
                    elapsed = time.time() - t0
                    st.session_state.last_time = elapsed
                    st.error(f"Error inesperado: {e}")
                    status.update(label="❌ Error inesperado", state="error")

            st.experimental_rerun()

# ──────────────────────────────────────────────────────────────
# 8. RESULTADOS (TEXTO + IMAGEN + TIEMPO + HISTORIAL)
# ──────────────────────────────────────────────────────────────

st.markdown("<hr class='ai-divider'>", unsafe_allow_html=True)

col_info, col_img = st.columns([1.1, 1.6], gap="large")

with col_info:
    if st.session_state.current:
        curr = st.session_state.current

        st.markdown("<div class='ai-results-label'>Resultado actual</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='ai-results-title'>{limpiar_prompt(curr['prompt'])}</div>",
            unsafe_allow_html=True,
        )

        # Meta chips
        st.markdown(
            f"""
        <div>
          <span class="ai-meta-chip">🤖 {curr.get('modelo')}</span>
          <span class="ai-meta-chip">📐 {curr.get('resolucion')}</span>
          <span class="ai-meta-chip">🌱 Seed {curr.get('seed')}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Tiempo estimado vs real
        if st.session_state.last_estimate and curr.get("elapsed") is not None:
            est_min, est_max = st.session_state.last_estimate
            real = curr["elapsed"]
            st.write(
                f"⏱️ Tiempo estimado: {est_min:0.1f}–{est_max:0.1f} s · "
                f"tiempo real: **{real:0.2f} s**"
            )

        # Descargar
        if curr.get("bytes"):
            st.download_button(
                label="📥 Descargar imagen",
                data=curr["bytes"],
                file_name=f"aistudio_{curr['seed']}.png",
                mime="image/png",
                use_container_width=True,
            )

        st.write("")
        st.markdown(
            f"<span style='font-size:0.8rem;color:#9ca3af;'>URL original: <code>{curr['url']}</code></span>",
            unsafe_allow_html=True,
        )

        # Historial (máx 5 previas)
        history_rest = st.session_state.history[1:6]
        if history_rest:
            st.write("")
            st.markdown("<div class='ai-results-label'>Historial</div>", unsafe_allow_html=True)
            for idx, item in enumerate(history_rest):
                h_titulo = limpiar_prompt(item["prompt"])
                if st.button(
                    f"🖼️ {h_titulo}",
                    key=f"hist_{idx}",
                    use_container_width=True,
                    help=f"Seed {item['seed']} · {item['timestamp']}",
                ):
                    st.session_state.current = item
                    st.experimental_rerun()
    else:
        st.markdown(
            """
        <div class="ai-placeholder">
          <div style="font-size:2.2rem;margin-bottom:0.4rem;">🖼️</div>
          <div>Tu imagen aparecerá aquí con sus detalles, tiempo de generación y descarga.</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

with col_img:
    if st.session_state.current:
        curr = st.session_state.current
        st.markdown("<div class='ai-img-frame'>", unsafe_allow_html=True)
        st.image(curr["bytes"] if curr.get("bytes") else curr["url"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
        <div class="ai-placeholder" style="min-height:360px;">
          Vista previa de la imagen generada
        </div>
        """,
            unsafe_allow_html=True,
        )