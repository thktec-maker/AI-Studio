import streamlit as st
import urllib.parse
import random
import requests
import time
from datetime import datetime

# ──────────────────────────────────────────────────────────────
# 1. CONFIGURACIÓN DE PÁGINA
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Studio Pro",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────
# 2. DEFINICIÓN DE ESTILOS RÁPIDOS
# ──────────────────────────────────────────────────────────────
QUICK_STYLES = [
    {
        "id": "realismo",
        "label": "🎨 Realismo",
        "inj": "ultra realistic, 8k photography, sharp focus, natural lighting, highly detailed"
    },
    {
        "id": "cinematic",
        "label": "🎬 Cinematic",
        "inj": "cinematic still frame, dramatic movie lighting, 35mm lens, depth of field, anamorphic"
    },
    {
        "id": "cyberpunk",
        "label": "🌌 Cyberpunk",
        "inj": "cyberpunk style, neon glow, rainy night atmosphere, futuristic city, high contrast"
    },
    {
        "id": "ilustracion",
        "label": "🖌️ Ilustración",
        "inj": "digital illustration, clean line art, vibrant colors, Artstation style, masterwork"
    },
    {
        "id": "naturaleza",
        "label": "🌿 Naturaleza",
        "inj": "wildlife photography, national geographic style, soft sunlight, macro detail"
    },
    {
        "id": "magico",
        "label": "✨ Mágico",
        "inj": "fantasy ethereal atmosphere, glowing particles, dreamlike, soft pastel colors"
    },
]

# ──────────────────────────────────────────────────────────────
# 3. UTILIDADES DE PROMPT Y URL
# ──────────────────────────────────────────────────────────────

def limpiar_prompt(prompt: str) -> str:
    """Crea un título corto y limpio para la UI."""
    p = " ".join(prompt.split())
    partes = [s.strip() for s in p.split(",") if s.strip()]
    usados = set()
    unicas = []
    for s in partes:
        if s.lower() not in usados:
            usados.add(s.lower())
            unicas.append(s)
    limpio = ", ".join(unicas)
    return (limpio[:82] + "...") if len(limpio) > 85 else limpio.capitalize()

def deduplicar_prompt(prompt: str) -> str:
    """Limpia el prompt antes de enviarlo a la API."""
    partes = [s.strip() for s in prompt.split(",") if s.strip()]
    usados = set()
    unicas = []
    for s in partes:
        if s.lower() not in usados:
            usados.add(s.lower())
            unicas.append(s)
    return ", ".join(unicas)

def construir_url(prompt: str, w: int, h: int, seed: int, model_tag: str, enhance: bool, neg_prompt: str) -> str:
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
    if "FLUX" in modelo: return "flux"
    if "SDXL" in modelo: return "sdxl"
    return "turbo"

def safe_rerun():
    """Ejecuta rerun compatible con versiones viejas y nuevas de Streamlit."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# ──────────────────────────────────────────────────────────────
# 4. DISEÑO CSS (PREMIUM AI STUDIO)
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

:root {
    --primary: #10a37f;
    --primary-glow: rgba(16,163,127,0.2);
    --bg-card: #ffffff;
    --text-main: #111827;
    --text-sub: #4b5563;
}

#MainMenu, footer, header { visibility: hidden; }

.stApp {
    font-family: 'Inter', sans-serif;
    background: radial-gradient(circle at top left, #f3f4f6 0%, #e5e7eb 100%);
}

main .block-container {
    max-width: 950px !important;
    padding: 1.5rem !important;
}

/* Card Principal */
.st-key-main-card {
    background: var(--bg-card);
    border-radius: 24px;
    border: 1px solid #e5e7eb;
    padding: 2rem !important;
    box-shadow: 0 15px 35px rgba(0,0,0,0.05);
}

/* Estilos de botones (Chips) */
.ai-chip-btn > button {
    border-radius: 12px !important;
    border: 1px solid #e5e7eb !important;
    background: #f9fafb !important;
    font-size: 0.85rem !important;
    transition: all 0.2s ease !important;
}

.ai-chip-btn-active > button {
    border-color: var(--primary) !important;
    background: rgba(16,163,127,0.1) !important;
    color: var(--primary) !important;
    box-shadow: 0 0 10px var(--primary-glow) !important;
}

/* Imagen Frame */
.ai-img-frame {
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 25px 50px rgba(0,0,0,0.15);
    background: #000;
    margin-top: 1rem;
}

/* Placeholder */
.ai-placeholder {
    border: 2px dashed #d1d5db;
    border-radius: 20px;
    padding: 3rem;
    text-align: center;
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# 5. ESTADO DE SESIÓN
# ──────────────────────────────────────────────────────────────
if "history" not in st.session_state: st.session_state.history = []
if "current" not in st.session_state: st.session_state.current = None
if "last_prompt" not in st.session_state: st.session_state.last_prompt = ""
if "active_style" not in st.session_state: st.session_state.active_style = None

# ──────────────────────────────────────────────────────────────
# 6. INTERFAZ DE USUARIO (UI)
# ──────────────────────────────────────────────────────────────

st.markdown("<h1 style='text-align:center; font-weight:800;'>✨ AI Studio Pro</h1>", unsafe_allow_html=True)

with st.container(key="main-card"):
    # Fila de Estilos Rápidos
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#9ca3af; text-transform:uppercase;'>Selecciona un Estilo</p>", unsafe_allow_html=True)
    cols_styles = st.columns(len(QUICK_STYLES))
    for i, style in enumerate(QUICK_STYLES):
        is_active = st.session_state.active_style == style["id"]
        with cols_styles[i]:
            st.markdown(f'<div class="{"ai-chip-btn-active" if is_active else "ai-chip-btn"}">', unsafe_allow_html=True)
            if st.button(style["label"], key=f"btn_{style['id']}"):
                st.session_state.active_style = None if is_active else style["id"]
                safe_rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # Input de Texto
    prompt_input = st.text_area(
        "¿Qué quieres crear?",
        value=st.session_state.last_prompt,
        placeholder="Ej: A futuristic city under a crystal dome, high detail, masterpiece...",
        height=100,
        label_visibility="collapsed"
    )

    # Parámetros secundarios
    c1, c2, c3 = st.columns(3)
    with c1:
        modelo_ui = st.selectbox("Motor IA", ["FLUX.1 [Dev]", "SDXL", "Turbo"])
    with c2:
        res_ui = st.selectbox("Resolución", ["832×832", "1024×1024", "768×1024"])
    with c3:
        detalle_ui = st.select_slider("Detalle", options=["Bajo", "Normal", "Alto"], value="Normal")

    # Botones de Acción
    col_g, col_v = st.columns([2, 1])
    with col_g:
        btn_gen = st.button("🚀 GENERAR ARTE", use_container_width=True)
    with col_v:
        btn_var = st.button("🔄 VARIANTE", use_container_width=True)

    # ───── LÓGICA DE GENERACIÓN ─────
    if btn_gen or btn_var:
        if not prompt_input.strip() and not st.session_state.last_prompt:
            st.warning("Escribe algo primero.")
        else:
            st.session_state.last_prompt = prompt_input.strip() if prompt_input.strip() else st.session_state.last_prompt
            
            # Aplicar Estilo
            style_inj = ""
            for s in QUICK_STYLES:
                if s["id"] == st.session_state.active_style:
                    style_inj = s["inj"]
            
            final_prompt = deduplicar_prompt(f"{style_inj}, {st.session_state.last_prompt}")
            seed = random.randint(0, 9999999)
            w, h = (1024, 1024) if "1024" in res_ui else (832, 832)
            if "768" in res_ui: w, h = 768, 1024
            
            url = construir_url(final_prompt, w, h, seed, map_modelo(modelo_ui), (detalle_ui == "Alto"), "")
            
            with st.status("🎨 Conectando con los servidores de IA...", expanded=True) as status:
                try:
                    t0 = time.time()
                    r = requests.get(url, timeout=55)
                    elapsed = time.time() - t0
                    
                    if r.status_code == 200:
                        res_data = {
                            "prompt": st.session_state.last_prompt,
                            "bytes": r.content,
                            "url": url,
                            "seed": seed,
                            "elapsed": elapsed,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        }
                        st.session_state.current = res_data
                        st.session_state.history.insert(0, res_data)
                        status.update(label="✅ Arte Generado con éxito", state="complete")
                        safe_rerun()
                    else:
                        st.error("Error en la respuesta del servidor.")
                except Exception as e:
                    st.error(f"Error técnico: {e}")

# ──────────────────────────────────────────────────────────────
# 7. VISUALIZACIÓN DE RESULTADOS
# ──────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.current:
    curr = st.session_state.current
    col_info, col_img = st.columns([1, 1.8], gap="large")
    
    with col_info:
        st.markdown(f"### {limpiar_prompt(curr['prompt'])}")
        st.info(f"⏱️ Generado en {curr['elapsed']:.2f} segundos")
        st.write(f"**Semilla:** `{curr['seed']}`")
        st.download_button(
            "📥 Descargar Imagen (HD)",
            curr["bytes"],
            f"ai_studio_{curr['seed']}.png",
            "image/png",
            use_container_width=True
        )
        
        # Mini Historial
        if len(st.session_state.history) > 1:
            st.markdown("---")
            st.markdown("**Recientes**")
            for i, h in enumerate(st.session_state.history[1:4]):
                if st.button(f"🖼️ {limpiar_prompt(h['prompt'])}", key=f"hist_{i}"):
                    st.session_state.current = h
                    safe_rerun()
                    
    with col_img:
        st.markdown('<div class="ai-img-frame">', unsafe_allow_html=True)
        st.image(curr["bytes"])
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="ai-placeholder">
        <p style="font-size: 3rem;">🖼️</p>
        <p>Escribe tu idea arriba y haz clic en Generar para ver la magia.</p>
    </div>
    """, unsafe_allow_html=True)
