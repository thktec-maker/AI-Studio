import streamlit as st
import urllib.parse
import random
import requests
import time
from datetime import datetime

st.set_page_config(page_title="AI Studio Pro", page_icon="✨", layout="wide", initial_sidebar_state="collapsed")

# ── ESTILOS ───────────────────────────────────────────────────
QUICK_STYLES = [
    {"id": "realismo",    "label": "🎨 Realismo",    "inj": "ultra realistic, 8k photography, sharp focus, natural lighting"},
    {"id": "cinematic",   "label": "🎬 Cinematic",   "inj": "cinematic still frame from a movie, dramatic lighting, shallow depth of field, 35mm lens"},
    {"id": "cyberpunk",   "label": "🌌 Cyberpunk",   "inj": "cyberpunk style, neon lights, rainy atmosphere, high contrast, futuristic city mood"},
    {"id": "ilustracion", "label": "🖌️ Ilustración", "inj": "digital illustration, clean line art, soft shading, artstation quality"},
    {"id": "naturaleza",  "label": "🌿 Naturaleza",  "inj": "natural environment, soft daylight, realistic plants and rocks, peaceful mood"},
    {"id": "magico",      "label": "✨ Mágico",      "inj": "fantasy magical atmosphere, glowing particles, ethereal lighting, high detail"},
]
MAX_HISTORY = 3  # Solo 3 en historial para mantener reruns rápidos

# ── FUNCIONES ─────────────────────────────────────────────────
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def limpiar_prompt(p):
    parts = list(dict.fromkeys(s.strip() for s in p.split(",") if s.strip()))
    r = ", ".join(parts)
    return (r[:80] + "…") if len(r) > 82 else r.capitalize()

def deduplicar(p):
    seen = set()
    out = []
    for s in (s.strip() for s in p.split(",") if s.strip()):
        if s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return ", ".join(out)

def construir_url(prompt, w, h, seed, model, enhance, neg):
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width={w}&height={h}&seed={seed}&nologo=true&enhance={'true' if enhance else 'false'}&model={model}"
    if neg.strip():
        url += f"&negative={urllib.parse.quote(neg.strip())}"
    # Cache buster para evitar respuestas lentas por caché del CDN
    url += f"&t={int(time.time())}"
    return url

def map_modelo(m):
    if "FLUX" in m: return "flux"
    if "SDXL" in m: return "sdxl"
    return "turbo"

def get_style(sid):
    return next((s for s in QUICK_STYLES if s["id"] == sid), None)

# ── CSS LIMPIO ────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
:root{
  --c:#10a37f;--cd:#059669;--cg:rgba(16,163,127,.30);
  --t1:#111827;--t2:#4b5563;--t3:#9ca3af;
  --bdr:#e5e7eb;--card:#fff;--bg:#f9fafb;
}
#MainMenu,footer,header{visibility:hidden}
.stApp{font-family:'Inter',system-ui,sans-serif;background:radial-gradient(ellipse at 20% 0%,#dbeafe 0%,var(--bg) 50%,#f3f4f6 100%)}
main .block-container{max-width:960px!important;padding:1.5rem 1.5rem 3rem!important;margin:0 auto!important}
.topbar{text-align:center;padding:.8rem 0 1.2rem}
.topbar h1{font-size:2.1rem;font-weight:800;color:var(--t1);letter-spacing:-.03em;margin:0}
.topbar p{font-size:.95rem;color:var(--t2);margin:.25rem 0 0}
.st-key-main-card{background:var(--card);border-radius:20px!important;border:1px solid var(--bdr)!important;padding:1.6rem 1.8rem!important;box-shadow:0 16px 40px rgba(15,23,42,.08)!important}
.stRadio > label{font-size:.78rem!important;font-weight:700!important;letter-spacing:.06em!important;text-transform:uppercase!important;color:var(--t3)!important}
.stRadio [role="radiogroup"]{gap:.4rem!important}
.stRadio [role="radiogroup"] label{border-radius:999px!important;padding:.3rem .85rem!important;border:1px solid var(--bdr)!important;background:var(--bg)!important;font-size:.82rem!important;font-weight:500!important;color:var(--t2)!important;transition:all .15s ease!important;cursor:pointer!important}
.stRadio [role="radiogroup"] label:hover{border-color:var(--c)!important;color:var(--c)!important}
.stRadio [role="radiogroup"] label:has(input:checked){background:var(--c)!important;color:#fff!important;border-color:var(--c)!important;box-shadow:0 4px 12px var(--cg)!important}
.stRadio [role="radiogroup"] label input{display:none!important}
.stTextArea textarea{border-radius:12px!important;border:1px solid var(--bdr)!important;padding:.85rem 1rem!important;font-size:1rem!important;line-height:1.6!important;background:#fafafa!important;transition:border-color .2s,box-shadow .2s!important}
.stTextArea textarea:focus{border-color:var(--c)!important;box-shadow:0 0 0 3px var(--cg)!important;background:#fff!important}
.stSelectbox label,.stSlider label,label{font-size:.78rem!important;font-weight:600!important;color:var(--t2)!important;text-transform:uppercase!important;letter-spacing:.06em!important}
.stSelectbox [data-baseweb="select"]>div{border-radius:10px!important;border:1px solid var(--bdr)!important;font-size:.9rem!important;background:#fafafa!important}
.stButton>button{width:100%!important;border-radius:999px!important;border:none!important;padding:.72rem 1.4rem!important;font-size:.95rem!important;font-weight:600!important;background:linear-gradient(135deg,var(--c),var(--cd))!important;color:#fff!important;box-shadow:0 8px 22px var(--cg)!important;transition:transform .12s,box-shadow .12s!important}
.stButton>button:hover{transform:translateY(-1px)!important;box-shadow:0 12px 28px var(--cg)!important}
.stDownloadButton>button{border-radius:999px!important;border:1px solid var(--bdr)!important;padding:.6rem 1rem!important;font-size:.88rem!important;background:#fff!important;color:var(--t2)!important;width:100%!important}
.stDownloadButton>button:hover{border-color:var(--c)!important;color:var(--c)!important}
.divider{border:none;border-top:1px solid var(--bdr);margin:1.3rem 0 1rem}
.res-label{font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--t3);margin-bottom:.3rem}
.res-title{font-size:1.35rem;font-weight:700;color:var(--t1);margin-bottom:.5rem;line-height:1.3}
.badge{display:inline-flex;align-items:center;gap:.25rem;font-size:.78rem;padding:.15rem .55rem;border-radius:999px;border:1px solid var(--bdr);background:#f3f4f6;color:var(--t2);margin:0 .2rem .25rem 0}
.img-wrap{border-radius:16px;overflow:hidden;box-shadow:0 20px 48px rgba(15,23,42,.22);background:#0b1120;line-height:0}
.empty-state{background:var(--bg);border-radius:16px;border:1.5px dashed #d1d5db;padding:2.5rem 1.5rem;text-align:center;color:var(--t3)}
.active-tag{display:inline-block;padding:.3rem .75rem;border-radius:8px;background:rgba(16,163,127,.08);border:1px solid rgba(16,163,127,.2);color:var(--c);font-size:.82rem;font-weight:500;margin-top:.25rem}
</style>""", unsafe_allow_html=True)

# ── ESTADO (optimizado: mínimo en memoria) ────────────────────
for k, v in {"current_bytes":None, "current_meta":None, "history":[], "last_prompt":"", "active_style":None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── TOPBAR ────────────────────────────────────────────────────
st.markdown('<div class="topbar"><h1>AI Studio Pro</h1><p>Genera imágenes con IA · Pollinations · FLUX · SDXL · Turbo</p></div>', unsafe_allow_html=True)

# ── PANEL ─────────────────────────────────────────────────────
with st.container(key="main-card"):

    opts = ["Sin estilo"] + [s["label"] for s in QUICK_STYLES]
    cur_label = "Sin estilo"
    if st.session_state.active_style:
        s = get_style(st.session_state.active_style)
        if s: cur_label = s["label"]

    sel = st.radio("Estilo rápido", opts, index=opts.index(cur_label), horizontal=True)
    new_id = None if sel == "Sin estilo" else next((s["id"] for s in QUICK_STYLES if s["label"] == sel), None)
    if new_id != st.session_state.active_style:
        st.session_state.active_style = new_id
        safe_rerun()

    if st.session_state.active_style:
        e = get_style(st.session_state.active_style)
        st.markdown(f'<div class="active-tag">✓ {e["label"]} — se aplica automáticamente</div>', unsafe_allow_html=True)

    prompt = st.text_area("Prompt", value=st.session_state.last_prompt,
        placeholder="Describe tu imagen: sujeto, entorno, iluminación, estilo…",
        height=90, label_visibility="collapsed")

    c1, c2, c3 = st.columns([1.4, 1.1, 1.0])
    with c1: modelo = st.selectbox("Motor de IA", ["FLUX.1 [Dev]", "FLUX.1 Pro", "SDXL", "Turbo"])
    with c2: resolucion = st.selectbox("Dimensión", ["832×832 (1:1)", "1024×1024 (1:1)", "768×1024 (3:4)"])
    with c3: detalle = st.select_slider("Detalle", options=["Bajo", "Estándar", "Alto"], value="Estándar")

    with st.expander("Opciones avanzadas", expanded=False):
        neg_prompt = st.text_input("Prompt negativo", value="frame, border, text, watermark, logo")

    cg, cv = st.columns([2, 1])
    with cg: btn_gen = st.button("✨ Generar imagen", use_container_width=True)
    with cv: btn_var = st.button("🔄 Variante", use_container_width=True)

    # ── GENERACIÓN (optimizada) ──
    if btn_gen or btn_var:
        if not prompt.strip() and not st.session_state.last_prompt:
            st.warning("Escribe un prompt antes de generar.")
        else:
            if prompt.strip():
                st.session_state.last_prompt = prompt.strip()
            base = st.session_state.last_prompt
            est = get_style(st.session_state.active_style)
            api_prompt = deduplicar(f"{est['inj']}, {base}" if est else base)
            seed = random.randint(1, 99_999_999)

            dims = {"832×832 (1:1)":(832,832), "1024×1024 (1:1)":(1024,1024), "768×1024 (3:4)":(768,1024)}
            w, h = dims.get(resolucion, (832, 832))

            # OPTIMIZACIÓN: enhance=false siempre, inyectamos calidad vía prompt (ahorra 5-10s)
            quality_boost = ", masterpiece, best quality, highly detailed" if detalle == "Alto" else ""
            final_prompt = api_prompt + quality_boost

            url = construir_url(final_prompt, w, h, seed, map_modelo(modelo), False, neg_prompt)
            timeout = 40 if "Turbo" in modelo else 70

            with st.status("🎨 Generando…", expanded=True) as status:
                st.write(f"**{modelo}** · {resolucion} · {detalle} · Seed `{seed}`")

                t0 = time.time()
                ok = False
                try:
                    r = requests.get(url, timeout=timeout)
                    elapsed = time.time() - t0
                    if r.status_code == 200 and len(r.content) > 1000:
                        meta = {
                            "prompt": base, "seed": seed,
                            "elapsed": elapsed, "timestamp": datetime.now().strftime("%H:%M"),
                            "modelo": modelo, "resolucion": resolucion, "detalle": detalle,
                            "style": est["label"] if est else "—", "url": url,
                        }
                        # OPTIMIZACIÓN CLAVE: solo guardamos bytes de la imagen ACTUAL
                        # El historial solo guarda metadatos + URL (sin bytes)
                        st.session_state.current_bytes = r.content
                        st.session_state.current_meta = meta

                        # Historial ligero: solo metadatos, sin bytes pesados
                        st.session_state.history.insert(0, meta)
                        if len(st.session_state.history) > MAX_HISTORY:
                            st.session_state.history = st.session_state.history[:MAX_HISTORY]

                        status.update(label=f"✅ Lista en {elapsed:.1f}s", state="complete")
                        ok = True
                    else:
                        st.error(f"Error {r.status_code}. Intenta de nuevo.")
                        status.update(label="❌ Error", state="error")
                except requests.exceptions.Timeout:
                    st.error("⏱️ Timeout. Usa Turbo o baja resolución.")
                    status.update(label="⏱️ Timeout", state="error")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Sin conexión.")
                    status.update(label="🔌 Sin conexión", state="error")
                except Exception as e:
                    st.error(f"Error: {e}")
                    status.update(label="❌ Error", state="error")

            if ok:
                safe_rerun()

# ── RESULTADOS ────────────────────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)

col_info, col_img = st.columns([1.1, 1.6], gap="large")

with col_info:
    meta = st.session_state.current_meta
    img_bytes = st.session_state.current_bytes

    if meta and img_bytes:
        st.markdown('<p class="res-label">Resultado actual</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="res-title">{limpiar_prompt(meta["prompt"])}</p>', unsafe_allow_html=True)
        st.markdown(f'''<div>
          <span class="badge">🤖 {meta["modelo"]}</span>
          <span class="badge">📐 {meta["resolucion"]}</span>
          <span class="badge">🌱 {meta["seed"]}</span>
          <span class="badge">🎨 {meta["style"]}</span>
          <span class="badge">⏱️ {meta["elapsed"]:.1f}s</span>
        </div>''', unsafe_allow_html=True)

        st.write("")
        st.download_button("📥 Descargar imagen", img_bytes,
            f"aistudio_{meta['seed']}.png", "image/png", use_container_width=True)

        # Historial ligero (sin bytes, solo recupera vía URL)
        prev = st.session_state.history[1:]
        if prev:
            st.write("")
            st.markdown('<p class="res-label">Historial reciente</p>', unsafe_allow_html=True)
            for i, item in enumerate(prev):
                if st.button(f"🖼️ {limpiar_prompt(item['prompt'])} ({item['timestamp']})",
                             key=f"h_{i}", use_container_width=True):
                    # Re-descargar la imagen del historial (rápido, Pollinations la cachea)
                    with st.spinner("Recuperando…"):
                        try:
                            rh = requests.get(item["url"], timeout=30)
                            if rh.status_code == 200 and len(rh.content) > 1000:
                                st.session_state.current_bytes = rh.content
                                st.session_state.current_meta = item
                                safe_rerun()
                        except Exception:
                            st.error("No se pudo recuperar la imagen.")
    else:
        st.markdown('''<div class="empty-state">
          <div style="font-size:2rem;margin-bottom:.4rem">🖼️</div>
          <div>Tu imagen aparecerá aquí con detalles y descarga.</div>
        </div>''', unsafe_allow_html=True)

with col_img:
    meta = st.session_state.current_meta
    img_bytes = st.session_state.current_bytes
    if meta and img_bytes:
        st.markdown('<div class="img-wrap">', unsafe_allow_html=True)
        st.image(img_bytes, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('''<div class="empty-state" style="min-height:340px;display:flex;align-items:center;justify-content:center;">
          Vista previa de la imagen generada
        </div>''', unsafe_allow_html=True)
