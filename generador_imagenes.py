import streamlit as st
import urllib.parse
import random
import requests
from io import BytesIO

# ── 1. CONFIGURACIÓN DE PÁGINA ────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Studio Pro | Digital Art Engine",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── 2. UTILIDADES ─────────────────────────────────────────────────────────────
def limpiar_prompt(prompt: str) -> str:
    """
    Limpia el prompt para mostrarlo como título:
    - Quita espacios extra
    - Elimina frases repetidas separadas por comas
    - Recorta a ~80 caracteres
    """
    p = " ".join(prompt.split())
    partes = [s.strip() for s in p.split(",") if s.strip()]
    unicas = []
    usados = set()
    for s in partes:
        clave = s.lower()
        if clave not in usados:
            usados.add(clave)
            unicas.append(s)
    limpio = ", ".join(unicas)
    if len(limpio) > 85:
        limpio = limpio[:82] + "..."
    return limpio.capitalize()

# ── 3. DISEÑO PREMIUM (CSS) ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --primary: #10a37f;
    --primary-dark: #0d8a6a;
    --primary-glow: rgba(16, 163, 127, 0.4);
    --accent: #6366f1;
    --bg-gradient: radial-gradient(circle at 0% 0%, #e0f2fe 0%, #f9fafb 45%, #f3f4f6 100%);
    --glass-bg: rgba(255, 255, 255, 0.78);
    --glass-border: rgba(255, 255, 255, 0.6);
    --text-main: #0f172a;
    --text-sub: #475569;
    --text-muted: #94a3b8;
    --radius-lg: 32px;
    --radius-md: 20px;
    --shadow-premium: 0 35px 70px -15px rgba(15, 23, 42, 0.15);
}

/* Ocultar elementos nativos de Streamlit */
[data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none !important; }

.stApp {
    background: var(--bg-gradient) !important;
    font-family: 'Inter', sans-serif !important;
}

h1, h2, h3, .ai-title {
    font-family: 'Outfit', sans-serif !important;
}

/* Contenedor principal - Más estrecho para sensación "cerca" */
main .block-container {
    max-width: 1000px !important;
    padding: 2.5rem 1.5rem 5rem !important;
    margin: 0 auto !important;
}

/* Utilidad Glassmorphism Refinada */
.glass-card {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(25px) saturate(200%) !important;
    -webkit-backdrop-filter: blur(25px) saturate(200%) !important;
    border-radius: var(--radius-lg) !important;
    border: 1px solid var(--glass-border) !important;
    padding: 3rem !important;
    box-shadow: var(--shadow-premium) !important;
    animation: fadeIn 1s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Título Impactante */
.hero-title {
    background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3.5rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.05em !important;
    text-align: center;
    margin-bottom: 0.4rem !important;
}

.hero-subtitle {
    color: var(--text-sub);
    text-align: center;
    font-size: 1.25rem;
    margin-bottom: 3.5rem;
    font-weight: 400;
    letter-spacing: -0.01em;
}

/* Inputs de Texto */
.stTextArea textarea {
    background: rgba(255, 255, 255, 0.6) !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid rgba(0,0,0,0.06) !important;
    padding: 1.5rem !important;
    font-size: 1.15rem !important;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.stTextArea textarea:focus {
    background: #ffffff !important;
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 6px var(--primary-glow) !important;
}

/* Botones Premium */
.stButton > button {
    border-radius: 99px !important;
    padding: 0.9rem 2.2rem !important;
    font-weight: 600 !important;
    font-size: 1.05rem !important;
    transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
}

/* Botón Generar - Estilo Leonardo.ai */
.st-key-btn-generate button {
    background: linear-gradient(135deg, #10a37f 0%, #059669 100%) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 12px 28px rgba(16, 163, 127, 0.3) !important;
    width: 100% !important;
    height: 3.8rem !important;
}
.st-key-btn-generate button:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 18px 35px rgba(16, 163, 127, 0.4) !important;
}

/* Botón Variante */
.st-key-btn-variant button {
    background: rgba(255,255,255,0.8) !important;
    color: var(--text-main) !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    width: 100% !important;
    height: 3.8rem !important;
}
.st-key-btn-variant button:hover {
    background: #ffffff !important;
    border-color: var(--primary) !important;
    transform: translateY(-2px);
}

/* Chips de Estilo Interactivos */
.style-chip button {
    background: rgba(255,255,255,0.7) !important;
    border: 1px solid rgba(0,0,0,0.04) !important;
    color: var(--text-sub) !important;
    padding: 0.5rem 1.2rem !important;
    font-size: 0.9rem !important;
    margin: 3px !important;
}
.style-chip button:hover {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background: white !important;
}

/* Imagen Frame */
.img-container {
    border-radius: var(--radius-md);
    overflow: hidden;
    box-shadow: 0 40px 80px rgba(0,0,0,0.2);
    background: #000;
    line-height: 0;
    border: 1px solid rgba(255,255,255,0.15);
    transition: transform 0.5s ease;
}
.img-container:hover {
    transform: scale(1.01);
}

/* Placeholder */
.placeholder-box {
    border: 2px dashed #cbd5e1;
    border-radius: var(--radius-md);
    padding: 6rem 2rem;
    text-align: center;
    color: #94a3b8;
    background: rgba(255,255,255,0.4);
    font-size: 1.1rem;
}

/* Historial */
.history-card {
    padding: 0.85rem 1.2rem;
    border-radius: 16px;
    background: rgba(255,255,255,0.5);
    border: 1px solid rgba(0,0,0,0.03);
    margin-bottom: 0.6rem;
    font-size: 0.9rem;
    color: var(--text-sub);
    display: flex;
    align-items: center;
    gap: 12px;
    transition: all 0.3s;
    cursor: pointer;
}
.history-card:hover {
    background: #ffffff;
    border-color: var(--primary);
    transform: translateX(6px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# ── 3. LÓGICA DE ESTADO ──────────────────────────────────────────────────────
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current' not in st.session_state:
    st.session_state.current = None
if 'last_prompt' not in st.session_state:
    st.session_state.last_prompt = ""

# ── 4. CABECERA ──────────────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">AI Studio Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Visualiza el futuro con inteligencia artificial de vanguardia</p>', unsafe_allow_html=True)

# ── 5. MOTOR DE GENERACIÓN ───────────────────────────────────────────────────
with st.container(key="main-container"):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    # Grid Superior: Prompt + Ajustes
    col_main, col_settings = st.columns([2.5, 1], gap="large")
    
    with col_main:
        st.markdown("<p style='font-weight:600; color:#64748b; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.8rem;'>Inspiración rápida</p>", unsafe_allow_html=True)
        
        # Chips de estilo compactos
        styles = ["🎨 Realismo", "🎭 Cinematic", "🏙️ Cyberpunk", "🖼️ Óleo", "🌌 Galáctico", "🌿 Naturaleza", "✨ Mágico"]
        style_cols = st.columns(len(styles))
        for i, s in enumerate(styles):
            with style_cols[i]:
                if st.button(s, key=f"s_{i}", help=f"Aplicar estilo {s}", use_container_width=True):
                    style_tag = s.split(" ")[1]
                    st.session_state.last_prompt = f"{style_tag} style, {st.session_state.last_prompt}"
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        prompt_val = st.text_area(
            "Prompt",
            value=st.session_state.last_prompt,
            placeholder="Describe una escena épica, un retrato detallado o un paisaje onírico...",
            height=120,
            label_visibility="collapsed"
        )
        
        # Botones de Acción
        b_col1, b_col2 = st.columns([1.5, 1])
        with b_col1:
            btn_gen = st.button("✨ Generar Obra Maestra", key="btn-generate")
        with b_col2:
            btn_var = st.button("🔄 Crear Variante", key="btn-variant")

    with col_settings:
        st.markdown("<p style='font-weight:600; color:#64748b; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.8rem;'>Parámetros</p>", unsafe_allow_html=True)
        
        modelo = st.selectbox("Motor de IA", ["FLUX.1 [Dev]", "Stable Diffusion XL", "Turbo Engine"])
        resolucion = st.selectbox("Dimensión", ["1024×1024 (1:1)", "832×1216 (2:3)", "1216×832 (3:2)"])
        calidad = st.select_slider("Nivel de Detalle", options=["Básico", "Estándar", "Ultra ✨"], value="Estándar")
        
        with st.expander("⚙️ Opciones avanzadas"):
            seed_input = st.number_input("Seed (0 para aleatorio)", value=0, min_value=0)
            neg_prompt = st.text_input("Prompt Negativo", placeholder="Lo que NO quieres ver...")

    # ── 6. ÁREA DE RESULTADOS ────────────────────────────────────────────────
    st.markdown("<hr style='border:none; border-top:1px solid rgba(0,0,0,0.05); margin:2rem 0;'>", unsafe_allow_html=True)
    
    # Procesamiento
    if btn_gen or btn_var:
        current_prompt = prompt_val.strip()
        if not current_prompt:
            st.error("Por favor, introduce una descripción.")
        else:
            st.session_state.last_prompt = current_prompt
            seed = seed_input if seed_input > 0 else random.randint(1, 999999999)
            
            # Mapeo de dimensiones
            dim_map = {
                "1024×1024 (1:1)": (1024, 1024),
                "832×1216 (2:3)": (832, 1216),
                "1216×832 (3:2)": (1216, 832)
            }
            w, h = dim_map.get(resolucion, (1024, 1024))
            
            with st.status("🚀 Procesando con redes neuronales...", expanded=True) as status:
                p_enc = urllib.parse.quote(current_prompt)
                model_tag = "flux" if "FLUX" in modelo else "turbo"
                enhance_val = "true" if calidad == "Ultra ✨" else "false"
                
                url = f"https://image.pollinations.ai/prompt/{p_enc}?width={w}&height={h}&seed={seed}&nologo=true&enhance={enhance_val}&model={model_tag}"
                
                try:
                    r = requests.get(url, timeout=55)
                    if r.status_code == 200:
                        res_obj = {
                            "prompt": current_prompt,
                            "url": url,
                            "bytes": r.content,
                            "seed": seed,
                            "params": f"{modelo} • {resolucion}",
                            "timestamp": "Hoy"
                        }
                        st.session_state.current = res_obj
                        st.session_state.history.insert(0, res_obj)
                        status.update(label="✅ Renderizado completado", state="complete", expanded=False)
                        st.rerun()
                    else:
                        st.error("El servidor de IA no respondió a tiempo. Reintentando...")
                except Exception as e:
                    st.error(f"Error técnico: {e}")

    # Display de Resultados
    res_info, res_img = st.columns([1, 1.5], gap="large")
    
    with res_info:
        if st.session_state.current:
            curr = st.session_state.current
            # Título Limpio y Profesional
            titulo_limpio = limpiar_prompt(curr['prompt'])
            st.markdown(f"### {titulo_limpio}")
            st.markdown(f"<p style='color:var(--text-sub); font-size:0.95rem; margin-top:-0.5rem;'>{curr['params']} • Seed: {curr['seed']}</p>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Botón de Descarga Premium
            st.download_button(
                label="📥 Descargar Obra en Alta Resolución",
                data=curr['bytes'],
                file_name=f"ai_studio_{curr['seed']}.png",
                mime="image/png",
                use_container_width=True
            )
            
            st.markdown("<br><p style='font-weight:700; color:#1e293b; font-size:0.9rem; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:1rem;'>Historial Reciente</p>", unsafe_allow_html=True)
            for h in st.session_state.history[1:5]:
                h_titulo = limpiar_prompt(h['prompt'])
                st.markdown(f'''
                    <div class="history-card">
                        <span style="font-size:1.3rem;">🖼️</span>
                        <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-weight:500;">
                            {h_titulo}
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
        else:
            st.markdown('<div class="placeholder-box">Esperando tu próxima creación...</div>', unsafe_allow_html=True)

    with res_img:
        if st.session_state.current:
            st.markdown('<div class="img-container">', unsafe_allow_html=True)
            st.image(st.session_state.current['bytes'], use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('''
                <div class="placeholder-box" style="height:100%; display:flex; align-items:center; justify-content:center; flex-direction:column;">
                    <span style="font-size:3rem; margin-bottom:1rem;">🎨</span>
                    <p>La vista previa aparecerá aquí</p>
                </div>
            ''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # Cierre glass-card
