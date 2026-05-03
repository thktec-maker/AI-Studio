import streamlit as st
import urllib.parse
import random
import requests
import time
from datetime import datetime

st.set_page_config(page_title="AI Studio Pro", page_icon="✨", layout="wide", initial_sidebar_state="collapsed")

# ── ESTILOS ──────────────────────────────────────────────────
QUICK_STYLES = [
    {"id": "realismo",    "label": "🎨 Realismo",    "inj": "ultra realistic, 8k photography, sharp focus, natural lighting, photorealistic"},
    {"id": "cinematic",   "label": "🎬 Cinematic",   "inj": "cinematic still, dramatic movie lighting, 35mm anamorphic lens, shallow DOF"},
    {"id": "cyberpunk",   "label": "🌌 Cyberpunk",   "inj": "cyberpunk neon city, rain reflections, futuristic dark atmosphere, high contrast"},
    {"id": "ilustracion", "label": "🖌️ Ilustración", "inj": "digital illustration, clean line art, vibrant colors, artstation trending"},
    {"id": "naturaleza",  "label": "🌿 Naturaleza",  "inj": "wildlife photography, golden hour, national geographic, macro detail"},
    {"id": "magico",      "label": "✨ Mágico",      "inj": "fantasy ethereal atmosphere, glowing particles, dreamlike, magical lighting"},
]

# ── FUNCIONES ─────────────────────────────────────────────────
def safe_rerun():
    if hasattr(st, "rerun"): st.rerun()
    elif hasattr(st, "experimental_rerun"): st.experimental_rerun()

def limpiar_prompt(p):
    parts = [s.strip() for s in p.split(",") if s.strip()]
    seen, out = set(), []
    for s in parts:
        if s.lower() not in seen:
            seen.add(s.lower()); out.append(s)
    r = ", ".join(out)
    return (r[:82] + "...") if len(r) > 85 else r.capitalize()

def deduplicar(p):
    parts = [s.strip() for s in p.split(",") if s.strip()]
    seen, out = set(), []
    for s in parts:
        if s.lower() not in seen: seen.add(s.lower()); out.append(s)
    return ", ".join(out)

def construir_url(prompt, w, h, seed, model, enhance, neg):
    enc = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{enc}?width={w}&height={h}&seed={seed}&nologo=true&enhance={'true' if enhance else 'false'}&model={model}"
    if neg.strip(): url += f"&negative={urllib.parse.quote(neg.strip())}"
    return url

def map_modelo(m):
    if "FLUX" in m: return "flux"
    if "SDXL" in m or "Stable" in m: return "sdxl"
    return "turbo"

def get_style(sid):
    return next((s for s in QUICK_STYLES if s["id"] == sid), None)

# ── CSS PREMIUM ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Outfit:wght@700;800;900&display=swap');

:root {
  --p: #10a37f; --pd: #059669; --pg: rgba(16,163,127,.3);
  --bg: #f0f4f8; --card: rgba(255,255,255,.92);
  --t: #0f172a; --ts: #475569; --tm: #94a3b8;
  --br: 20px; --sh: 0 20px 60px rgba(15,23,42,.12);
}

*, *::before, *::after { box-sizing: border-box; }
#MainMenu, footer, header { visibility: hidden; }

.stApp {
  font-family: 'Inter', sans-serif;
  background: linear-gradient(135deg, #667eea22 0%, #764ba222 25%, #10a37f11 75%, #06b6d411 100%), #f0f4f8;
  min-height: 100vh;
}

main .block-container { max-width: 1000px !important; padding: 2rem 1.5rem !important; margin: 0 auto !important; }

/* Hero */
.hero { text-align: center; padding: 1.5rem 0 1rem; }
.hero h1 {
  font-family: 'Outfit', sans-serif; font-size: 3rem; font-weight: 900;
  background: linear-gradient(135deg, #0f172a 0%, #10a37f 60%, #06b6d4 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  letter-spacing: -0.04em; line-height: 1.1; margin: 0;
}
.hero p { color: var(--ts); font-size: 1.05rem; margin: .5rem 0 0; }

/* Card */
.glass-card {
  background: var(--card); backdrop-filter: blur(24px) saturate(180%);
  border-radius: var(--br); border: 1px solid rgba(255,255,255,.7);
  padding: 2rem; box-shadow: var(--sh); margin-bottom: 1.5rem;
  transition: box-shadow .3s ease;
}
.glass-card:hover { box-shadow: 0 28px 80px rgba(15,23,42,.16); }

/* Radio buttons como chips */
.stRadio > div { flex-direction: row !important; flex-wrap: wrap !important; gap: .4rem !important; }
.stRadio > div > label {
  border-radius: 999px !important; border: 1.5px solid #e2e8f0 !important;
  padding: .35rem .9rem !important; font-size: .82rem !important; font-weight: 500 !important;
  cursor: pointer !important; transition: all .2s ease !important;
  background: #f8fafc !important; color: var(--ts) !important;
}
.stRadio > div > label:hover { border-color: var(--p) !important; color: var(--p) !important; transform: translateY(-1px); }
.stRadio > div > label[data-baseweb="radio"] { background: red !important; }
div[data-baseweb="radio-group"] label[aria-checked="true"] {
  background: linear-gradient(135deg, var(--p), var(--pd)) !important;
  color: white !important; border-color: transparent !important;
  box-shadow: 0 4px 14px var(--pg) !important;
}

/* TextArea */
.stTextArea textarea {
  border-radius: 14px !important; border: 1.5px solid #e2e8f0 !important;
  font-size: 1rem !important; line-height: 1.65 !important; padding: .85rem 1rem !important;
  background: rgba(255,255,255,.8) !important; transition: all .25s !important;
  resize: none !important;
}
.stTextArea textarea:focus {
  border-color: var(--p) !important; background: #fff !important;
  box-shadow: 0 0 0 4px rgba(16,163,127,.15) !important;
}

/* Selectbox */
.stSelectbox [data-baseweb="select"] > div {
  border-radius: 12px !important; border: 1.5px solid #e2e8f0 !important;
  background: rgba(255,255,255,.8) !important; transition: border-color .2s !important;
}
.stSelectbox [data-baseweb="select"] > div:hover { border-color: var(--p) !important; }

/* Labels */
label, .stSelectbox label, .stSlider label {
  font-size: .78rem !important; font-weight: 700 !important; letter-spacing: .07em !important;
  text-transform: uppercase !important; color: var(--tm) !important;
}

/* Botón principal generar */
.stButton > button {
  border-radius: 999px !important; border: none !important;
  padding: .8rem 1.8rem !important; font-weight: 700 !important; font-size: .95rem !important;
  background: linear-gradient(135deg, var(--p) 0%, var(--pd) 100%) !important;
  color: white !important; box-shadow: 0 8px 24px var(--pg) !important;
  transition: all .2s ease !important; width: 100% !important; letter-spacing: .02em !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 14px 36px var(--pg) !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* Download */
.stDownloadButton > button {
  border-radius: 999px !important; border: 1.5px solid #e2e8f0 !important;
  background: white !important; color: var(--ts) !important;
  font-weight: 600 !important; transition: all .2s !important; width: 100% !important;
}
.stDownloadButton > button:hover { border-color: var(--p) !important; color: var(--p) !important; transform: translateY(-1px) !important; }

/* Result title */
.result-badge {
  display: inline-flex; align-items: center; gap: .3rem;
  padding: .2rem .65rem; border-radius: 999px; font-size: .75rem; font-weight: 600;
  border: 1px solid #e2e8f0; background: #f8fafc; color: var(--ts);
  margin: .15rem .2rem .15rem 0;
}

/* Image frame */
.img-frame {
  border-radius: 18px; overflow: hidden;
  box-shadow: 0 24px 64px rgba(15,23,42,.22); background: #0b1120; line-height: 0;
  transition: transform .4s ease, box-shadow .4s ease;
}
.img-frame:hover { transform: scale(1.01); box-shadow: 0 32px 80px rgba(15,23,42,.3); }

/* Placeholder */
.placeholder {
  border: 2px dashed #cbd5e1; border-radius: 18px; padding: 3rem 1.5rem;
  text-align: center; color: var(--tm); background: rgba(255,255,255,.4);
}

/* Historial */
.hist-btn > button {
  text-align: left !important; border-radius: 12px !important;
  border: 1px solid #e2e8f0 !important; background: rgba(255,255,255,.6) !important;
  color: var(--ts) !important; font-size: .85rem !important; padding: .5rem .8rem !important;
  box-shadow: none !important; transition: all .2s !important;
}
.hist-btn > button:hover { border-color: var(--p) !important; color: var(--p) !important; background: rgba(16,163,127,.05) !important; transform: none !important; }

/* Caption info */
.style-info {
  background: linear-gradient(135deg, rgba(16,163,127,.1), rgba(6,182,212,.1));
  border: 1px solid rgba(16,163,127,.25); border-radius: 10px;
  padding: .5rem .9rem; font-size: .82rem; color: var(--p); font-weight: 500;
  margin-top: .3rem;
}

/* Select slider */
.stSlider { padding: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── ESTADO ────────────────────────────────────────────────────
for k, v in {"history": [], "current": None, "last_prompt": "", "active_style": None, "last_estimate": None}.items():
    if k not in st.session_state: st.session_state[k] = v

# ── HERO ──────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>✨ AI Studio Pro</h1>
  <p>Genera arte con IA de nivel mundial · Pollinations API · FLUX · SDXL · Turbo</p>
</div>
""", unsafe_allow_html=True)

# ── PANEL PRINCIPAL ───────────────────────────────────────────
st.markdown('<div class="glass-card">', unsafe_allow_html=True)

# Selector de estilo con radio (nativo, fiable)
style_options = ["🚫 Sin estilo"] + [s["label"] for s in QUICK_STYLES]
active_label = "🚫 Sin estilo"
if st.session_state.active_style:
    s = get_style(st.session_state.active_style)
    if s: active_label = s["label"]

selected = st.radio("🎨 Estilo artístico", options=style_options,
                    index=style_options.index(active_label), horizontal=True)

# Procesar cambio de estilo
new_id = None if selected == "🚫 Sin estilo" else next((s["id"] for s in QUICK_STYLES if s["label"] == selected), None)
if new_id != st.session_state.active_style:
    st.session_state.active_style = new_id
    safe_rerun()

if st.session_state.active_style:
    est = get_style(st.session_state.active_style)
    st.markdown(f'<div class="style-info">✅ <b>{est["label"]}</b> activo — se fusionará con tu prompt automáticamente</div>', unsafe_allow_html=True)

st.write("")

# Prompt
prompt = st.text_area("", value=st.session_state.last_prompt,
    placeholder="✍️ Describe tu visión: sujeto, escena, iluminación, emoción... Sé específico para mejores resultados.",
    height=100, label_visibility="collapsed")

# Parámetros
c1, c2, c3 = st.columns([1.4, 1.1, 1.0])
with c1: modelo = st.selectbox("⚙️ Motor IA", ["FLUX.1 [Dev]", "FLUX.1 Pro", "SDXL Turbo", "Turbo"])
with c2: resolucion = st.selectbox("📐 Resolución", ["832×832 (1:1)", "1024×1024 (1:1)", "768×1024 (Retrato)", "1024×768 (Paisaje)"])
with c3: detalle = st.select_slider("🔬 Detalle", options=["Rápido", "Estándar", "Ultra"], value="Estándar")

with st.expander("⚙️ Opciones avanzadas"):
    neg_prompt = st.text_input("🚫 Prompt negativo", value="blurry, watermark, text, logo, border, distorted, low quality")

cg, cv = st.columns([2.2, 1])
with cg: btn_gen = st.button("🚀 Generar imagen", use_container_width=True)
with cv: btn_var = st.button("🔄 Nueva variante", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── GENERACIÓN ────────────────────────────────────────────────
if btn_gen or btn_var:
    if not prompt.strip() and not st.session_state.last_prompt:
        st.warning("✍️ Escribe un prompt primero.")
    else:
        if prompt.strip(): st.session_state.last_prompt = prompt.strip()
        base = st.session_state.last_prompt
        est = get_style(st.session_state.active_style)
        combined = f"{est['inj']}, {base}" if est else base
        api_prompt = deduplicar(combined)
        seed = random.randint(1, 99_999_999)

        dim_map = {"832×832 (1:1)": (832,832), "1024×1024 (1:1)": (1024,1024),
                   "768×1024 (Retrato)": (768,1024), "1024×768 (Paisaje)": (1024,768)}
        w, h = dim_map.get(resolucion, (832, 832))
        enhance = detalle == "Ultra"
        timeout_sec = 45 if "Turbo" in modelo else 90

        url = construir_url(api_prompt, w, h, seed, map_modelo(modelo), enhance, neg_prompt)

        with st.status("🎨 Conectando con los servidores de IA...", expanded=True) as status:
            st.write(f"**Prompt base:** {base}")
            if est: st.write(f"**Estilo inyectado:** `{est['inj']}`")
            st.write(f"**Prompt final:** `{api_prompt[:120]}...`" if len(api_prompt) > 120 else f"**Prompt final:** `{api_prompt}`")
            st.write(f"**Config:** {modelo} · {resolucion} · {detalle} · Seed `{seed}`")

            t0 = time.time()
            error_msg = None
            result_data = None
            try:
                r = requests.get(url, timeout=timeout_sec)
                elapsed = time.time() - t0
                if r.status_code == 200 and len(r.content) > 1000:
                    result_data = {
                        "prompt": base, "prompt_api": api_prompt, "seed": seed, "url": url,
                        "bytes": r.content, "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "modelo": modelo, "resolucion": resolucion, "detalle": detalle, "elapsed": elapsed,
                        "style": est["label"] if est else "Sin estilo"
                    }
                    st.session_state.current = result_data
                    if not st.session_state.history or st.session_state.history[0]["seed"] != seed:
                        st.session_state.history.insert(0, result_data)
                    status.update(label=f"✅ Imagen generada en {elapsed:.1f}s", state="complete")
                else:
                    error_msg = f"Error HTTP {r.status_code} — intenta con otro modelo."
                    status.update(label="❌ Error del servidor", state="error")
            except requests.exceptions.Timeout:
                elapsed = time.time() - t0
                error_msg = f"⏱️ Timeout después de {elapsed:.0f}s. Usa **Turbo** o baja la resolución."
                status.update(label="⏱️ Tiempo agotado", state="error")
            except requests.exceptions.ConnectionError:
                error_msg = "🔌 Sin conexión. Verifica tu internet."
                status.update(label="🔌 Error de conexión", state="error")
            except Exception as e:
                error_msg = f"Error inesperado: {str(e)[:200]}"
                status.update(label="❌ Error inesperado", state="error")

        if error_msg:
            st.error(error_msg)
        elif result_data:
            safe_rerun()

# ── RESULTADOS ────────────────────────────────────────────────
if st.session_state.current:
    curr = st.session_state.current
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col_info, col_img = st.columns([1, 1.7], gap="large")

    with col_info:
        st.markdown(f"<p style='font-size:.75rem;font-weight:700;text-transform:uppercase;color:#94a3b8;letter-spacing:.07em;'>Resultado actual</p>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='font-family:Outfit,sans-serif;font-size:1.3rem;font-weight:800;color:#0f172a;margin:0 0 .7rem;'>{limpiar_prompt(curr['prompt'])}</h3>", unsafe_allow_html=True)

        badges = f"""
        <div style="margin-bottom:.8rem;">
          <span class="result-badge">🤖 {curr['modelo']}</span>
          <span class="result-badge">📐 {curr['resolucion']}</span>
          <span class="result-badge">🌱 {curr['seed']}</span>
          <span class="result-badge">🎨 {curr['style']}</span>
          <span class="result-badge">⏱️ {curr['elapsed']:.1f}s</span>
        </div>"""
        st.markdown(badges, unsafe_allow_html=True)

        if curr.get("bytes"):
            st.download_button("📥 Descargar HD", curr["bytes"],
                               f"aistudio_{curr['seed']}.png", "image/png", use_container_width=True)

        # Historial
        prev = st.session_state.history[1:5]
        if prev:
            st.markdown("<br><p style='font-size:.75rem;font-weight:700;text-transform:uppercase;color:#94a3b8;letter-spacing:.07em;'>Historial</p>", unsafe_allow_html=True)
            for idx, item in enumerate(prev):
                st.markdown('<div class="hist-btn">', unsafe_allow_html=True)
                if st.button(f"🖼️ {limpiar_prompt(item['prompt'])}", key=f"h_{idx}",
                             use_container_width=True, help=f"Seed {item['seed']} · {item['timestamp']}"):
                    st.session_state.current = item
                    safe_rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    with col_img:
        st.markdown('<div class="img-frame">', unsafe_allow_html=True)
        st.image(curr["bytes"] if curr.get("bytes") else curr["url"], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("""
    <div class="placeholder">
      <p style="font-size:3rem;margin:0 0 .5rem;">🎨</p>
      <p style="font-size:1.1rem;font-weight:600;color:#475569;">Tu obra maestra aparecerá aquí</p>
      <p style="font-size:.9rem;color:#94a3b8;">Escribe un prompt, elige un estilo y pulsa Generar</p>
    </div>
    """, unsafe_allow_html=True)
