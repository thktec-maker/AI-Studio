import streamlit as st
import urllib.parse
import random
import requests
import time
from datetime import datetime

# ── 1. CONFIGURACIÓN ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Studio Pro",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── 2. UTILIDADES ─────────────────────────────────────────────────────────────

def limpiar_prompt(prompt: str) -> str:
    """Elimina duplicados separados por coma y recorta para mostrar como título."""
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
    """Limpia el prompt antes de enviarlo a la API: elimina frases repetidas."""
    partes = [s.strip() for s in prompt.split(",") if s.strip()]
    usados = set()
    unicas = []
    for s in partes:
        if s.lower() not in usados:
            usados.add(s.lower())
            unicas.append(s)
    return ", ".join(unicas)


def construir_url(prompt: str, w: int, h: int, seed: int, model_tag: str,
                  enhance: bool, neg_prompt: str) -> str:
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
    if "FLUX" in modelo:
        return "flux"
    if "Stable" in modelo or "SDXL" in modelo:
        return "sdxl"
    return "turbo"


# ── 3. CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --primary: #10a37f;
    --primary-dark: #0d8a6a;
    --primary-glow: rgba(16, 163, 127, 0.25);
    --accent: #6366f1;
    --bg: radial-gradient(circle at 15% 10%, #dbeafe 0%, #f8fafc 50%, #f1f5f9 100%);
    --glass: rgba(255,255,255,0.82);
    --glass-border: rgba(255,255,255,0.65);
    --text: #0f172a;
    --text-sub: #475569;
    --text-muted: #94a3b8;
    --r-lg: 28px;
    --r-md: 18px;
    --shadow: 0 24px 60px -12px rgba(15,23,42,0.13);
}

[data-testid="stHeader"], [data-testid="stToolbar"], footer { display:none !important; }

.stApp {
    background: var(--bg) !important;
    font-family: 'Inter', sans-serif !important;
}

h1,h2,h3 { font-family: 'Outfit', sans-serif !important; }

/* Contenedor centrado, sin espacios gigantes */
main .block-container {
    max-width: 1020px !important;
    padding: 2rem 1.5rem 4rem !important;
    margin: 0 auto !important;
}

/* Hero */
.hero-title {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.04em !important;
    text-align: center;
    margin-bottom: 0.3rem !important;
    line-height: 1.1 !important;
}
.hero-sub {
    color: var(--text-sub);
    text-align: center;
    font-size: 1.05rem;
    margin-bottom: 2rem;
    font-weight: 400;
}

/* Panel glass */
.glass-panel {
    background: var(--glass);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border-radius: var(--r-lg);
    border: 1px solid var(--glass-border);
    padding: 2rem 2.2rem;
    box-shadow: var(--shadow);
}

/* Separador */
.divider {
    border: none;
    border-top: 1px solid rgba(0,0,0,0.06);
    margin: 1.6rem 0;
}

/* Label de sección */
.section-label {
    font-weight: 600;
    color: #64748b;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.7rem;
    display: block;
}

/* Textarea */
.stTextArea textarea {
    background: rgba(255,255,255,0.65) !important;
    border-radius: var(--r-md) !important;
    border: 1.5px solid rgba(0,0,0,0.07) !important;
    padding: 1rem 1.2rem !important;
    font-size: 1rem !important;
    line-height: 1.6 !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
    resize: none !important;
}
.stTextArea textarea:focus {
    background: #fff !important;
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 4px var(--primary-glow) !important;
}

/* Todos los botones base */
.stButton > button {
    border-radius: 99px !important;
    padding: 0.75rem 1.6rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

/* CTA principal: Generar */
[data-testid="stButton"][key="btn-generate"] > button,
.st-key-btn-generate > button {
    background: linear-gradient(135deg, #10a37f 0%, #059669 100%) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 8px 22px rgba(16,163,127,0.28) !important;
    width: 100% !important;
    font-size: 1rem !important;
    padding: 0.85rem 1.6rem !important;
}
.st-key-btn-generate > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 14px 30px rgba(16,163,127,0.38) !important;
}
.st-key-btn-generate > button:active { transform: translateY(0) !important; }

/* Botón variante */
.st-key-btn-variant > button {
    background: #fff !important;
    color: var(--text) !important;
    border: 1.5px solid rgba(0,0,0,0.09) !important;
    width: 100% !important;
    font-size: 1rem !important;
    padding: 0.85rem 1.6rem !important;
}
.st-key-btn-variant > button:hover {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    transform: translateY(-1px) !important;
}

/* Chips de estilo */
.stButton > button[kind="secondary"] {
    font-size: 0.82rem !important;
    padding: 0.4rem 0.9rem !important;
}

/* Chip activo */
.chip-active > button {
    background: var(--primary) !important;
    color: #fff !important;
    border-color: var(--primary) !important;
}

/* Imagen resultado */
.img-frame {
    border-radius: var(--r-md);
    overflow: hidden;
    box-shadow: 0 20px 50px rgba(0,0,0,0.18);
    background: #000;
    line-height: 0;
    transition: transform 0.4s ease;
}
.img-frame:hover { transform: scale(1.005); }
.img-frame img { max-height: 440px; object-fit: contain; width: 100%; }

/* Placeholder */
.placeholder {
    border: 2px dashed #cbd5e1;
    border-radius: var(--r-md);
    padding: 4rem 2rem;
    text-align: center;
    color: var(--text-muted);
    background: rgba(255,255,255,0.35);
    font-size: 1rem;
}

/* Tarjetas historial */
.h-card {
    padding: 0.7rem 1rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(0,0,0,0.04);
    margin-bottom: 0.5rem;
    font-size: 0.88rem;
    color: var(--text-sub);
    display: flex;
    align-items: center;
    gap: 10px;
    transition: all 0.2s;
    cursor: pointer;
}
.h-card:hover {
    background: #fff;
    border-color: var(--primary);
    transform: translateX(4px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    color: var(--text);
}
.h-card-active {
    border-color: var(--primary) !important;
    background: rgba(16,163,127,0.07) !important;
}

/* Info de resultado */
.result-label {
    font-size: 0.78rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
    margin-bottom: 0.3rem;
}
.result-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.3;
    margin-bottom: 0.3rem;
}
.result-meta {
    font-size: 0.88rem;
    color: var(--text-muted);
    margin-bottom: 1.2rem;
}

/* Download button */
.stDownloadButton > button {
    border-radius: 99px !important;
    width: 100% !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem !important;
    border: 1.5px solid rgba(0,0,0,0.1) !important;
    background: #fff !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
}

/* Select / Slider */
.stSelectbox label, .stSelectSlider label, .stNumberInput label, .stTextInput label {
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: var(--text-sub) !important;
}
</style>
""", unsafe_allow_html=True)

# ── 4. ESTADO ─────────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "history": [],       # lista de dicts con los resultados
        "current": None,     # resultado activo
        "last_prompt": "",   # texto del textarea entre reruns
        "active_style": None # chip de estilo seleccionado
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── 5. CABECERA ───────────────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">AI Studio Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Genera imágenes con IA · Pollinations · FLUX · SDXL · Turbo</p>', unsafe_allow_html=True)

# ── 6. PANEL PRINCIPAL ────────────────────────────────────────────────────────
st.markdown('<div class="glass-panel">', unsafe_allow_html=True)

col_main, col_settings = st.columns([2.6, 1], gap="large")

# ─── COLUMNA IZQUIERDA: Inspiración + Prompt ──────────────────────────────
with col_main:
    st.markdown('<span class="section-label">Estilo rápido</span>', unsafe_allow_html=True)

    STYLES = [
        ("🎨", "Realismo",   "photorealistic, hyperdetailed, 8k"),
        ("🎭", "Cinematic",  "cinematic lighting, anamorphic lens, film grain"),
        ("🏙️", "Cyberpunk",  "cyberpunk neon city, rain reflections, dark atmosphere"),
        ("🖼️", "Óleo",       "oil painting, thick brushstrokes, museum quality"),
        ("🌌", "Galáctico",  "deep space, nebula, cosmic, bioluminescent"),
        ("🌿", "Naturaleza", "lush nature, golden hour, macro photography"),
        ("✨", "Mágico",     "magical fantasy, ethereal glow, dreamlike"),
    ]

    chip_cols = st.columns(len(STYLES))
    for i, (emoji, label, tag) in enumerate(STYLES):
        with chip_cols[i]:
            is_active = st.session_state.active_style == label
            # Usamos help para mostrar el tag completo en tooltip
            if st.button(
                f"{emoji} {label}",
                key=f"chip_{i}",
                help=tag,
                use_container_width=True,
            ):
                if is_active:
                    # Toggle off: quitar el tag del prompt
                    st.session_state.last_prompt = st.session_state.last_prompt.replace(tag + ", ", "").replace(", " + tag, "").replace(tag, "").strip().strip(",").strip()
                    st.session_state.active_style = None
                else:
                    # Toggle on: reemplazar estilo anterior si había uno
                    if st.session_state.active_style:
                        old_tag = next((t for _, l, t in STYLES if l == st.session_state.active_style), "")
                        st.session_state.last_prompt = st.session_state.last_prompt.replace(old_tag + ", ", "").replace(old_tag, "").strip().strip(",").strip()
                    st.session_state.last_prompt = f"{tag}, {st.session_state.last_prompt}".strip(", ")
                    st.session_state.active_style = label
                st.rerun()

    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)

    prompt_val = st.text_area(
        "Prompt",
        value=st.session_state.last_prompt,
        placeholder="Describe la escena: sujeto, entorno, plano, estilo, iluminación...",
        height=110,
        label_visibility="collapsed",
        key="prompt_input"
    )

    # Actualizar last_prompt en tiempo real para que los chips lo lean
    st.session_state.last_prompt = prompt_val

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    b1, b2 = st.columns([1.6, 1], gap="small")
    with b1:
        btn_gen = st.button("✨ Generar imagen", key="btn-generate", use_container_width=True)
    with b2:
        btn_var = st.button("🔄 Nueva variante", key="btn-variant", use_container_width=True,
                            disabled=st.session_state.current is None,
                            help="Genera otra versión del mismo prompt con seed distinto")

# ─── COLUMNA DERECHA: Parámetros ─────────────────────────────────────────
with col_settings:
    st.markdown('<span class="section-label">Parámetros</span>', unsafe_allow_html=True)

    modelo = st.selectbox(
        "Motor",
        ["FLUX.1 [Dev]", "Stable Diffusion XL", "Turbo Engine"],
        help="FLUX = máxima calidad (lento). SDXL = equilibrado. Turbo = rápido."
    )
    resolucion = st.selectbox(
        "Dimensión",
        ["1024×1024 (cuadrado)", "832×1216 (retrato)", "1216×832 (paisaje)"]
    )
    calidad = st.select_slider(
        "Calidad",
        options=["Rápido", "Estándar", "Ultra"],
        value="Estándar"
    )

    with st.expander("⚙️ Avanzado"):
        seed_input = st.number_input("Seed (0 = aleatorio)", value=0, min_value=0, step=1)
        neg_prompt = st.text_input(
            "Prompt negativo",
            placeholder="blurry, watermark, text, distorted...",
            help="Lo que NO quieres que aparezca"
        )

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── 7. LÓGICA DE GENERACIÓN ───────────────────────────────────────────────────
DIM_MAP = {
    "1024×1024 (cuadrado)": (1024, 1024),
    "832×1216 (retrato)":   (832, 1216),
    "1216×832 (paisaje)":   (1216, 832),
}

def generar_imagen(prompt_raw: str, forzar_seed: int = 0):
    """Llama a Pollinations y guarda el resultado en session_state."""
    prompt_limpio = deduplicar_prompt(prompt_raw)
    if not prompt_limpio:
        st.error("⚠️ Escribe una descripción antes de generar.")
        return

    seed = forzar_seed if forzar_seed > 0 else random.randint(1, 999_999_999)
    w, h = DIM_MAP.get(resolucion, (1024, 1024))
    model_tag = map_modelo(modelo)
    enhance = calidad == "Ultra"
    neg = neg_prompt if "neg_prompt" in dir() else ""

    # Inyección de ultra detalles para evitar el enhance nativo lento
    if enhance:
        prompt_apical = f"{prompt_limpio}, masterpiece, best quality, ultra detailed, hyperrealistic, 8k resolution, cinematic lighting"
    else:
        prompt_apical = prompt_limpio

    # Construimos URL con enhance=False para velocidad y agregamos cache buster
    url = construir_url(prompt_apical, w, h, seed, model_tag, False, neg)
    url += f"&cb={int(time.time())}"

    status_placeholder = st.empty()
    with status_placeholder.status("Generando tu imagen…", expanded=True) as status:
        st.write(f"🧠 Modelo: **{modelo}** · {resolucion} · Seed: `{seed}`")
        try:
            # AUMENTAMOS EL TIMEOUT A 180s (3 Minutos) PARA PREVENIR EL ERROR 55s
            r = requests.get(url, timeout=180)
        except requests.exceptions.Timeout:
            status.update(label="⏱️ Tiempo de espera agotado", state="error")
            st.error("El servidor tardó más de 3 minutos. Prueba con Turbo Engine o reduce la resolución.")
            return
        except requests.exceptions.ConnectionError:
            status.update(label="🔌 Sin conexión", state="error")
            st.error("No se pudo conectar con Pollinations. Verifica tu conexión.")
            return
        except Exception as e:
            status.update(label="❌ Error inesperado", state="error")
            st.error(f"Error: {e}")
            return

        if r.status_code == 200 and r.content:
            res_obj = {
                "prompt":    prompt_limpio,
                "bytes":     r.content,
                "seed":      seed,
                "modelo":    modelo,
                "resolucion": resolucion,
                "timestamp": datetime.now().strftime("%H:%M"),
                "params":    f"{modelo} · {resolucion}",
            }
            st.session_state.current = res_obj
            # Evitar duplicado si se vuelve a generar el mismo prompt
            if not st.session_state.history or st.session_state.history[0]["seed"] != seed:
                st.session_state.history.insert(0, res_obj)
            status.update(label="✅ Imagen lista", state="complete", expanded=False)
        else:
            status.update(label=f"❌ Error del servidor ({r.status_code})", state="error")
            if r.status_code == 429:
                 st.error("El servidor está muy ocupado (Error 429). Prueba cambiar el Motor a Turbo Engine.")
            else:
                 st.error(f"Pollinations devolvió un error {r.status_code}. Intenta de nuevo.")
            return

    # Rerun fuera del context manager para no romper el status
    st.rerun()


if btn_gen:
    generar_imagen(prompt_val)

if btn_var and st.session_state.current:
    # Variante: mismo prompt, seed aleatorio forzado
    generar_imagen(st.session_state.current["prompt"], forzar_seed=0)

# ── 8. ÁREA DE RESULTADOS ─────────────────────────────────────────────────────
col_info, col_img = st.columns([1, 1.6], gap="large")

with col_info:
    curr = st.session_state.current

    if curr:
        titulo = limpiar_prompt(curr["prompt"])
        st.markdown(f'<p class="result-label">Resultado actual</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="result-title">{titulo}</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="result-meta">{curr["params"]} · Seed: {curr["seed"]} · {curr["timestamp"]}</p>',
            unsafe_allow_html=True
        )

        st.download_button(
            label="📥 Descargar imagen",
            data=curr["bytes"],
            file_name=f"aistudio_{curr['seed']}.png",
            mime="image/png",
            use_container_width=True,
        )

        # ── Historial clickeable ──────────────────────────────────────────
        history_rest = st.session_state.history[1:6]  # máx 5 anteriores
        if history_rest:
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            st.markdown('<span class="section-label">Historial</span>', unsafe_allow_html=True)

            for idx, item in enumerate(history_rest):
                h_titulo = limpiar_prompt(item["prompt"])
                h_key = f"hist_{idx}"
                # Botón invisible sobre la card para capturar el click
                if st.button(f"🖼️  {h_titulo}", key=h_key, use_container_width=True,
                             help=f"Seed {item['seed']} · {item['timestamp']}"):
                    st.session_state.current = item
                    st.rerun()
    else:
        st.markdown("""
            <div class="placeholder" style="padding:3rem 1.5rem;">
                <span style="font-size:2.4rem; display:block; margin-bottom:0.8rem;">🎨</span>
                <strong style="font-size:1rem; color:#475569;">Escribe un prompt y pulsa Generar</strong>
                <p style="margin-top:0.5rem; font-size:0.9rem;">Tu imagen aparecerá aquí con sus detalles y opciones de descarga.</p>
            </div>
        """, unsafe_allow_html=True)

with col_img:
    curr = st.session_state.current
    if curr:
        st.markdown('<div class="img-frame">', unsafe_allow_html=True)
        st.image(curr["bytes"], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="placeholder" style="min-height:340px; display:flex; align-items:center;
                 justify-content:center; flex-direction:column; gap:0.8rem;">
                <span style="font-size:3rem;">🖼️</span>
                <p>La vista previa aparecerá aquí</p>
            </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # cierre glass-panel
