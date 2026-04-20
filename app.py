"""
AutoPrompt Interactive Demo — Streamlit application v3.0.

Run with:
    python3 -m streamlit run app.py

Environment:
    GEMINI_API_KEY — must be set in .env or as a Streamlit Cloud secret.
"""
import os
import time

import streamlit as st
from dotenv import load_dotenv

from src.autoprompt import AutoPromptEngine
from src.baseline import BaselinePipeline
from src.config_loader import load_secure_config
from src.utils import Review

# ── Page config — first Streamlit call ──────────────────────────────────────
st.set_page_config(
    page_title="AutoPrompt — AI Prompt Optimization",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/Ayush-o1/auto-Prompt",
        "Report a bug": "https://github.com/Ayush-o1/auto-Prompt/issues",
        "About": "AutoPrompt: dynamic prompt optimization for LLM extraction tasks.",
    },
)

# ── Google Fonts ─────────────────────────────────────────────────────────────
_FONTS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
"""

# ── Design system CSS v3.0 — Abyss Violet ───────────────────────────────────
_CSS = """
<style>
/* 0. RESET & GLOBAL FONT */
*,*::before,*::after{box-sizing:border-box;}
html,body,[class*="css"],.stApp,.stMarkdown,
.stButton>button,.stTextArea textarea,.stTextArea label,
.stExpander,section[data-testid="stSidebar"] *{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif!important;
}

/* 1. HIDE STREAMLIT CHROME */
#MainMenu,footer,header[data-testid="stHeader"],.stDeployButton,
div[data-testid="stToolbar"],div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"]{display:none!important;}

/* 2. PAGE BACKGROUND & CONTAINER */
.stApp{
  background:#050714;
  background-image:
    radial-gradient(ellipse 80% 50% at 50% -5%,rgba(124,58,237,.14) 0%,transparent 60%),
    radial-gradient(ellipse 50% 40% at 85% 85%,rgba(14,165,233,.07) 0%,transparent 50%);
}
.block-container{max-width:1080px!important;padding:2rem 2.5rem 5rem!important;margin:0 auto!important;}

/* 3. SIDEBAR */
section[data-testid="stSidebar"]{
  background:#080b1a!important;
  border-right:1px solid #151830!important;
}
section[data-testid="stSidebar"] .block-container{
  padding:1.75rem 1.25rem!important;max-width:100%!important;
}
.slabel{font-size:.62rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#3d4270;margin:0 0 .6rem;}
.s-rule{border:none;border-top:1px solid #151830;margin:1.2rem 0;}
.pill{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:999px;font-size:.72rem;font-weight:600;}
.pill-g{background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);color:#34d399;}
.pill-r{background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);color:#fca5a5;}
.pill-dot{width:7px;height:7px;border-radius:50%;background:currentColor;animation:breathe 2s ease-in-out infinite;}
@keyframes breathe{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.85)}}
.step-row{display:flex;align-items:flex-start;gap:10px;padding:6px 0;font-size:.78rem;color:#7b82b4;line-height:1.5;}
.step-num{flex-shrink:0;width:20px;height:20px;border-radius:50%;background:#0c1025;border:1px solid #1c2040;display:flex;align-items:center;justify-content:center;font-size:.6rem;font-weight:700;color:#7c3aed;margin-top:1px;}
.gh-btn{display:flex;align-items:center;justify-content:center;gap:6px;width:100%;padding:9px 14px;border-radius:10px;border:1px solid #1c2040;background:#0c1025;color:#7b82b4!important;font-size:.77rem;font-weight:500;text-decoration:none!important;transition:all .2s;margin-top:4px;}
.gh-btn:hover{border-color:#7c3aed;color:#e8ecff!important;}

/* 4. HERO */
.hero{position:relative;padding:3.5rem 0 3rem;text-align:center;overflow:hidden;}
.hero::before{
  content:'';position:absolute;width:600px;height:600px;border-radius:50%;
  background:radial-gradient(circle,rgba(124,58,237,.18) 0%,transparent 60%);
  top:-220px;left:50%;transform:translateX(-50%);pointer-events:none;
  animation:orb-pulse 6s ease-in-out infinite;
}
@keyframes orb-pulse{
  0%,100%{transform:translateX(-50%) scale(1);opacity:1}
  50%{transform:translateX(-50%) scale(1.12);opacity:.75}
}
.hero::after{
  content:'';position:absolute;inset:0;
  background-image:radial-gradient(circle,rgba(28,32,64,.65) 1px,transparent 1px);
  background-size:28px 28px;
  -webkit-mask-image:radial-gradient(ellipse 75% 85% at 50% 0%,black 5%,transparent 72%);
  mask-image:radial-gradient(ellipse 75% 85% at 50% 0%,black 5%,transparent 72%);
  pointer-events:none;
}
.hero-content{position:relative;z-index:1;}
.hero-badge{
  display:inline-flex;align-items:center;gap:7px;padding:4px 14px;border-radius:999px;
  background:rgba(124,58,237,.12);border:1px solid rgba(124,58,237,.3);
  color:#a78bfa;font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  margin-bottom:1.1rem;
}
.hero-dot{width:5px;height:5px;border-radius:50%;background:#7c3aed;animation:breathe 1.8s ease-in-out infinite;}
.hero-title{font-size:3.75rem;font-weight:900;letter-spacing:-.045em;line-height:1;color:#e8ecff;margin:0 0 1rem;}
.hero-title .accent{
  background:linear-gradient(135deg,#a78bfa 0%,#38bdf8 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.hero-sub{max-width:480px;margin:0 auto 1.75rem;font-size:.96rem;color:#4a5080;line-height:1.65;}
.hero-stats{display:flex;align-items:center;justify-content:center;gap:1.5rem;flex-wrap:wrap;}
.hero-stat{font-size:.7rem;color:#2a2d50;font-weight:500;display:flex;align-items:center;gap:6px;}
.hs-dot{width:4px;height:4px;border-radius:50%;background:#7c3aed;opacity:.7;}
.hero-divider{width:100%;height:1px;background:linear-gradient(90deg,transparent,#1c2040 25%,#1c2040 75%,transparent);margin-top:2.5rem;}

/* 5. SECTION LABELS */
.sec-label{font-size:.62rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#3d4270;margin:0 0 .7rem;}
.sec-head{display:flex;align-items:baseline;gap:.6rem;margin-bottom:1.2rem;}
.sec-head-t{font-size:.93rem;font-weight:700;color:#c4caf5;}
.sec-head-s{font-size:.77rem;color:#3d4270;}
.sec-rule{width:100%;height:1px;background:linear-gradient(90deg,transparent,#1c2040 20%,#1c2040 80%,transparent);margin:2.5rem 0 2rem;}

/* 6. TEXTAREA */
.stTextArea textarea{
  background:#080b1a!important;border:1px solid #1c2040!important;border-radius:12px!important;
  color:#c4caf5!important;font-size:.9rem!important;line-height:1.65!important;
  padding:1rem 1.25rem!important;transition:border-color .2s,box-shadow .2s!important;resize:vertical!important;
}
.stTextArea textarea:focus{
  border-color:#7c3aed!important;
  box-shadow:0 0 0 3px rgba(124,58,237,.12),0 0 20px rgba(124,58,237,.07)!important;
  outline:none!important;
}
.stTextArea textarea::placeholder{color:#252850!important;}
.char-pill{display:flex;justify-content:flex-end;margin-top:5px;}
.char-pill span{
  font-size:.67rem;color:#3d4270;background:#080b1a;border:1px solid #151830;
  border-radius:999px;padding:2px 9px;font-family:'JetBrains Mono',monospace;
}
.char-pill span.warn{color:#f59e0b;border-color:rgba(245,158,11,.3);}
.char-pill span.danger{color:#ef4444;border-color:rgba(239,68,68,.3);}

/* 7. BUTTONS */
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,#6d28d9,#7c3aed)!important;
  color:#fff!important;border:none!important;border-radius:11px!important;
  padding:.7rem 2rem!important;font-size:.9rem!important;font-weight:700!important;
  box-shadow:0 4px 24px rgba(109,40,217,.35),inset 0 1px 0 rgba(255,255,255,.1)!important;
  transition:all .2s!important;width:100%!important;
}
.stButton>button[kind="primary"]:hover:not(:disabled){
  box-shadow:0 6px 32px rgba(109,40,217,.5),inset 0 1px 0 rgba(255,255,255,.1)!important;
  transform:translateY(-1px)!important;
}
.stButton>button[kind="primary"]:active:not(:disabled){transform:translateY(0) scale(.99)!important;}
.stButton>button[kind="primary"]:disabled{opacity:.3!important;}
.stButton>button[kind="secondary"]{
  background:#0c1025!important;color:#7b82b4!important;border:1px solid #1c2040!important;
  border-radius:10px!important;font-size:.83rem!important;font-weight:500!important;transition:all .2s!important;
}
.stButton>button[kind="secondary"]:hover{border-color:#7c3aed!important;color:#e8ecff!important;background:#111630!important;}

/* 8. LOADING STEP TRACKER */
.load-wrap{background:#080b1a;border:1px solid #1c2040;border-radius:16px;padding:2rem;margin:1.5rem 0;}
.load-title{font-size:.63rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#3d4270;margin-bottom:1.5rem;text-align:center;}
.ls-steps{display:flex;flex-direction:column;max-width:400px;margin:0 auto;}
.ls-row{display:flex;align-items:center;gap:12px;padding:11px 0;border-bottom:1px solid #0a0d18;font-size:.81rem;}
.ls-row:last-child{border-bottom:none;}
.ls-icon{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:11px;font-weight:700;}
.ls-icon.done{background:rgba(16,185,129,.14);border:1px solid rgba(16,185,129,.28);color:#34d399;}
.ls-icon.active{background:rgba(124,58,237,.14);border:1px solid rgba(124,58,237,.3);color:#a78bfa;}
.ls-icon.pending{background:#0c1025;border:1px solid #151830;color:#1c2040;}
.ls-lbl{flex:1;}
.ls-lbl.done{color:#4a5080;}
.ls-lbl.active{color:#c4caf5;font-weight:600;}
.ls-lbl.pending{color:#1c2040;}
.spin-ring{width:14px;height:14px;border-radius:50%;border:2px solid rgba(124,58,237,.2);border-top-color:#7c3aed;animation:spin .9s linear infinite;flex-shrink:0;}
@keyframes spin{to{transform:rotate(360deg)}}

/* 9. RESULT CARDS — gradient border technique */
@keyframes card-in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.rc{
  border-radius:16px;padding:1.75rem;
  background:
    linear-gradient(#0c1025,#0c1025) padding-box,
    linear-gradient(135deg,#1c2040,#252850) border-box;
  border:1px solid transparent;
  transition:box-shadow .3s;
  animation:card-in .35s cubic-bezier(.4,0,.2,1) both;
}
.rc:hover{box-shadow:0 0 50px rgba(28,32,64,.7);}
.rc.ap{
  background:
    linear-gradient(#0c1025,#0c1025) padding-box,
    linear-gradient(135deg,#0ea5e9,#7c3aed) border-box;
}
.rc.ap.winner{
  background:
    linear-gradient(#0c1025,#0c1025) padding-box,
    linear-gradient(135deg,#10b981,#0ea5e9) border-box;
  box-shadow:0 0 40px rgba(16,185,129,.09),0 0 80px rgba(16,185,129,.04);
}
.rc.ap.winner:hover{box-shadow:0 0 60px rgba(16,185,129,.16),0 0 100px rgba(16,185,129,.06);}
.rc-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem;}
.rc-t{display:flex;align-items:center;gap:10px;}
.rc-icon{font-size:1.1rem;}
.rc-lbl{font-size:.65rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#4a5080;}
.lbl-ap{color:#38bdf8;}
.lbl-win{color:#34d399;}
.rc-sub{font-size:.67rem;color:#2a2d50;margin-top:1px;}
.w-chip{
  display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:999px;
  background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.28);
  color:#34d399;font-size:.63rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;white-space:nowrap;
}
.rc-hr{height:1px;background:#0d1020;margin:0 0 1.1rem;}
.rc-f{margin-bottom:.9rem;}
.rc-fk{font-size:.6rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#2a2d50;margin-bottom:3px;}
.rc-fv{font-size:.92rem;font-weight:600;color:#c4caf5;}
.rc-fr{font-size:.79rem;color:#4a5080;line-height:1.55;}
.sc{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:999px;font-size:.77rem;font-weight:600;}
.sc-pos{background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.22);color:#34d399;}
.sc-neg{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.22);color:#fca5a5;}
.sc-neu{background:rgba(148,163,184,.08);border:1px solid rgba(148,163,184,.15);color:#94a3b8;}
.sc-mix{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.2);color:#fcd34d;}
.sc-err{background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.15);color:#fca5a5;}
.rc-gauge{margin-top:1.5rem;display:flex;flex-direction:column;align-items:center;}

/* 10. STAT CARDS */
.stats-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:.5rem 0;}
.stat-card{background:#080b1a;border:1px solid #1c2040;border-radius:14px;padding:1.5rem 1.25rem;text-align:center;transition:border-color .2s;}
.stat-card:hover{border-color:#252850;}
.sc-lbl{font-size:.6rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;color:#3d4270;margin-bottom:.6rem;}
.sc-val{font-size:2.4rem;font-weight:900;letter-spacing:-.04em;line-height:1;margin-bottom:.35rem;font-family:'JetBrains Mono','Inter',monospace;}
.sc-val.violet{color:#a78bfa;}
.sc-val.muted{color:#3d4270;font-size:1.9rem;}
.sc-unit{font-size:1.1rem;font-weight:600;color:#6d28d9;}
.sc-unit-m{color:#252850;}
.stat-delta{display:inline-flex;align-items:center;gap:3px;padding:3px 9px;border-radius:999px;font-size:.7rem;font-weight:700;font-family:'JetBrains Mono',monospace;}
.stat-delta.pos{background:rgba(16,185,129,.1);color:#34d399;}
.stat-delta.neg{background:rgba(239,68,68,.1);color:#fca5a5;}
.stat-delta.neu{background:rgba(61,66,112,.2);color:#7b82b4;}
.sc-sub{font-size:.68rem;color:#2a2d50;margin-top:5px;}
.agree-m{background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.2);color:#34d399;padding:4px 12px;border-radius:999px;font-size:.78rem;font-weight:600;display:inline-flex;align-items:center;gap:4px;}
.agree-d{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.2);color:#fcd34d;padding:4px 12px;border-radius:999px;font-size:.78rem;font-weight:600;display:inline-flex;align-items:center;gap:4px;}

/* 11. EMPTY & ERROR STATES */
.empty-wrap{border:1px dashed #151830;border-radius:18px;background:#080b1a;padding:4rem 2rem;text-align:center;margin-top:2rem;}
.empty-icon{font-size:2.25rem;margin-bottom:1rem;opacity:.55;}
.empty-title{font-size:.92rem;font-weight:600;color:#3d4270;margin-bottom:5px;}
.empty-sub{font-size:.78rem;color:#1c2040;line-height:1.5;}
.err-wrap{background:rgba(239,68,68,.04);border:1px solid rgba(239,68,68,.18);border-radius:16px;padding:2.5rem 2rem;text-align:center;margin-top:1rem;}
.err-icon{font-size:1.8rem;margin-bottom:.65rem;}
.err-title{font-size:.95rem;font-weight:700;color:#fca5a5;margin-bottom:.4rem;}
.err-body{font-size:.82rem;color:#4a5080;line-height:1.6;}

/* 12. EXPANDER */
.streamlit-expanderHeader{background:#080b1a!important;border:1px solid #1c2040!important;border-radius:10px!important;color:#4a5080!important;font-size:.8rem!important;}
.streamlit-expanderContent{background:#060912!important;border:1px solid #151830!important;border-top:none!important;border-radius:0 0 10px 10px!important;}

/* 13. SELECTBOX */
.stSelectbox>div>div{background:#0c1025!important;border:1px solid #1c2040!important;border-radius:10px!important;color:#7b82b4!important;font-size:.84rem!important;}

/* 14. FOOTER */
.footer{margin-top:5rem;padding-top:1.75rem;border-top:1px solid #0d1020;text-align:center;}
.footer-links{display:flex;align-items:center;justify-content:center;gap:1.75rem;margin-bottom:.7rem;flex-wrap:wrap;}
.footer-link{color:#2a2d50!important;font-size:.75rem;font-weight:500;text-decoration:none!important;transition:color .2s;}
.footer-link:hover{color:#7b82b4!important;}
.footer-dot{color:#151830;font-size:.75rem;}
.footer-copy{font-size:.68rem;color:#1c2040;}
.footer-copy strong{color:#2a2d50;font-weight:600;}

/* 15. RESPONSIVE */
@media(max-width:768px){
  .hero-title{font-size:2.4rem!important;}
  .stats-grid{grid-template-columns:1fr!important;}
  .block-container{padding:1.25rem 1rem 4rem!important;}
}
@media(max-width:480px){
  .hero-title{font-size:1.8rem!important;}
  .hero-sub{font-size:.85rem!important;}
}
</style>
"""

# ── Constants ────────────────────────────────────────────────────────────────
MAX_REVIEW_CHARS = 2_000

SAMPLE_REVIEWS: dict[str, str] = {
    "☕ Coffee Maker — Positive": (
        "I absolutely love this coffee maker! Makes perfect coffee every morning "
        "and looks great on my kitchen counter. Worth every penny."
    ),
    "🔧 Blender — Negative": (
        "This blender is terrible. It broke after just two weeks of use. "
        "Very disappointed with the build quality and customer service."
    ),
    "🎧 Headphones — Mixed": (
        "The sound quality is amazing but they're quite uncomfortable "
        "for long listening sessions. A trade-off I didn't expect at this price."
    ),
    "💻 Laptop — Neutral": (
        "It's a laptop. Does what it's supposed to do. Nothing special, "
        "nothing bad. Average performance for the price."
    ),
}

SENTIMENT_CFG: dict[str, tuple[str, str]] = {
    "positive": ("sc sc-pos", "Positive"),
    "negative": ("sc sc-neg", "Negative"),
    "neutral":  ("sc sc-neu", "Neutral"),
    "mixed":    ("sc sc-mix", "Mixed"),
    "error":    ("sc sc-err", "Error"),
    "unknown":  ("sc sc-neu", "Unknown"),
}

# Half-circumference of r=38: π × 38 ≈ 119.4
ARC_LEN: float = 119.4


# ── Cached model loader ──────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_models() -> tuple:
    """Initialise pipelines once and cache them for the session."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, None, (
            "GEMINI_API_KEY not set. "
            "Add it to a .env file: GEMINI_API_KEY=your_key_here"
        )
    try:
        config = load_secure_config()
        return BaselinePipeline(config), AutoPromptEngine(config), None
    except Exception as exc:
        return None, None, str(exc)


# ── Render helpers ───────────────────────────────────────────────────────────

def render_hero() -> None:
    """Hero section: animated glow orb, dot grid, badge, title, stats."""
    st.markdown(
        '<div class="hero">'
        '<div class="hero-content">'
        '<div class="hero-badge">'
        '<span class="hero-dot"></span>'
        'Live Demo &nbsp;&middot;&nbsp; v3.0'
        '</div>'
        '<h1 class="hero-title">Auto<span class="accent">Prompt</span></h1>'
        '<p class="hero-sub">'
        'Benchmark a static prompt against a dynamic multi-variant optimizer'
        ' &mdash; watch the confidence gap close in real time.'
        '</p>'
        '<div class="hero-stats">'
        '<span class="hero-stat"><span class="hs-dot"></span>Multi-variant scoring</span>'
        '<span class="hero-stat"><span class="hs-dot"></span>Shared heuristics</span>'
        '<span class="hero-stat"><span class="hs-dot"></span>Real Gemini inference</span>'
        '</div>'
        '<div class="hero-divider"></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_sidebar(ready: bool, error_msg) -> None:
    """Upgraded sidebar: brand, status pill, samples, how-it-works, GitHub."""
    with st.sidebar:
        st.markdown(
            '<p style="font-size:1.05rem;font-weight:800;letter-spacing:-.025em;'
            'color:#e8ecff;margin:0 0 3px;">&#9889; AutoPrompt</p>'
            '<p style="font-size:.67rem;color:#3d4270;margin:0 0 1rem;font-weight:400;">'
            'Prompt Optimization Engine</p>',
            unsafe_allow_html=True,
        )
        if ready:
            st.markdown(
                '<span class="pill pill-g"><span class="pill-dot"></span>Models Ready</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="pill pill-r"><span class="pill-dot"></span>No API Key</span>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="s-rule"><p class="slabel">Sample Reviews</p>', unsafe_allow_html=True)
        selected = st.selectbox("sample", list(SAMPLE_REVIEWS.keys()), label_visibility="collapsed")
        if st.button("Load Sample \u2192", use_container_width=True, type="secondary"):
            st.session_state["review_text"] = SAMPLE_REVIEWS[selected]
            st.rerun()

        st.markdown('<hr class="s-rule"><p class="slabel">How It Works</p>', unsafe_allow_html=True)
        steps = [
            "Baseline sends a single static prompt to the Gemini API.",
            "AutoPrompt generates N variant prompts and calls the LLM for each.",
            "Each extraction is scored with a shared confidence heuristic.",
            "The best-scoring variant wins \u2014 delta is shown in results.",
        ]
        for i, s in enumerate(steps, 1):
            st.markdown(
                f'<div class="step-row"><span class="step-num">{i}</span><span>{s}</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="s-rule"><p class="slabel">Resources</p>', unsafe_allow_html=True)
        st.markdown(
            '<a class="gh-btn" href="https://github.com/Ayush-o1/auto-Prompt" target="_blank">'
            '&#8663; &nbsp; View on GitHub</a>',
            unsafe_allow_html=True,
        )


def _gauge_svg(value: float, uid: str, c0: str, c1: str) -> str:
    """Return an SVG half-donut confidence gauge with gradient fill."""
    pct = round(value * 100)
    offset = ARC_LEN * (1.0 - min(value, 1.0))
    return (
        f'<svg viewBox="0 0 100 65" width="150" height="97"'
        f' style="display:block;overflow:visible;">'
        f'<defs>'
        f'<linearGradient id="g{uid}" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{c0}"/>'
        f'<stop offset="100%" stop-color="{c1}"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<path d="M 12 60 A 38 38 0 0 1 88 60"'
        f' fill="none" stroke="#0d1020" stroke-width="9" stroke-linecap="round"/>'
        f'<path d="M 12 60 A 38 38 0 0 1 88 60"'
        f' fill="none" stroke="url(#g{uid})" stroke-width="9" stroke-linecap="round"'
        f' stroke-dasharray="{ARC_LEN:.1f}" stroke-dashoffset="{offset:.2f}"/>'
        f'<text x="50" y="56" text-anchor="middle"'
        f' font-family="JetBrains Mono,Inter,monospace"'
        f' font-size="20" font-weight="800" fill="#e8ecff">{pct}%</text>'
        f'</svg>'
    )


def _sentiment_html(sentiment: str) -> str:
    """Return an HTML sentiment pill chip."""
    key = sentiment.lower()
    cls, label = SENTIMENT_CFG.get(key, ("sc sc-neu", sentiment.capitalize()))
    return f'<span class="{cls}">{label}</span>'


def render_result_card(data, card_type: str, is_winner: bool) -> None:
    """Premium dark card with gradient border, fields, and SVG gauge."""
    if card_type == "baseline":
        card_cls = "rc"
        lbl_cls  = ""
        lbl      = "BASELINE"
        sub      = "Static Prompt"
        icon     = "&#x26A1;"
        g0, g1   = "#3d4270", "#7b82b4"
        uid      = "b"
        badge    = ""
    else:
        wp       = " winner" if is_winner else ""
        card_cls = f"rc ap{wp}"
        lbl_cls  = "lbl-win" if is_winner else "lbl-ap"
        lbl      = "AUTOPROMPT"
        sub      = "Dynamic Optimization"
        icon     = "&#x1F680;"
        uid      = "a"
        if is_winner:
            g0, g1 = "#10b981", "#0ea5e9"
        else:
            g0, g1 = "#0ea5e9", "#7c3aed"
        badge = '<span class="w-chip">&#10003;&nbsp;Best Result</span>' if is_winner else ""

    gauge   = _gauge_svg(data.confidence, uid, g0, g1)
    sent    = _sentiment_html(data.sentiment)
    em_dash = "\u2014"
    ellipsis = "\u2026"
    reason  = data.reason or em_dash
    if len(reason) > 200:
        reason = reason[:200] + ellipsis
    product = data.product or em_dash

    st.markdown(
        f'<div class="{card_cls}">'
        f'<div class="rc-head">'
        f'<div class="rc-t">'
        f'<span class="rc-icon">{icon}</span>'
        f'<div>'
        f'<div class="rc-lbl {lbl_cls}">{lbl}</div>'
        f'<div class="rc-sub">{sub}</div>'
        f'</div>'
        f'</div>'
        f'{badge}'
        f'</div>'
        f'<div class="rc-hr"></div>'
        f'<div class="rc-f"><div class="rc-fk">Product</div>'
        f'<div class="rc-fv">{product}</div></div>'
        f'<div class="rc-f"><div class="rc-fk">Sentiment</div>{sent}</div>'
        f'<div class="rc-f"><div class="rc-fk">Reason</div>'
        f'<div class="rc-fr">{reason}</div></div>'
        f'<div class="rc-gauge">{gauge}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Technical details", expanded=False):
        st.markdown(
            '<span style="font-size:.6rem;font-weight:700;letter-spacing:.14em;'
            'text-transform:uppercase;color:#3d4270;">Prompt Key</span>',
            unsafe_allow_html=True,
        )
        st.code(data.prompt_used, language=None)
        st.json(data.model_dump())


def render_stat_cards(bl, ap) -> None:
    """Three-column stat card row with JetBrains Mono numbers and delta."""
    d   = ap.confidence - bl.confidence
    dp  = round(d * 100, 1)
    app = round(ap.confidence * 100, 1)
    blp = round(bl.confidence * 100, 1)
    agree = (
        bl.product.lower() == ap.product.lower()
        and bl.sentiment.lower() == ap.sentiment.lower()
    )
    dc = "pos" if d > 0 else "neg" if d < 0 else "neu"
    da = "&#8593;" if d > 0 else "&#8595;" if d < 0 else "&#8594;"
    ds = "+" if d > 0 else ""
    agree_html = (
        '<span class="agree-m">&#10003;&nbsp;Match</span>'
        if agree else
        '<span class="agree-d">&#9726;&nbsp;Differs</span>'
    )
    st.markdown(
        f'<div class="stats-grid">'

        f'<div class="stat-card">'
        f'<div class="sc-lbl">AutoPrompt Confidence</div>'
        f'<div class="sc-val violet">{app:.1f}<span class="sc-unit">%</span></div>'
        f'<div class="stat-delta {dc}">{da}&nbsp;{ds}{dp:.1f}%</div>'
        f'<div class="sc-sub">vs baseline</div>'
        f'</div>'

        f'<div class="stat-card">'
        f'<div class="sc-lbl">Baseline Confidence</div>'
        f'<div class="sc-val muted">{blp:.1f}<span class="sc-unit sc-unit-m">%</span></div>'
        f'<div class="sc-sub">Static single prompt</div>'
        f'</div>'

        f'<div class="stat-card">'
        f'<div class="sc-lbl">Pipeline Agreement</div>'
        f'<div style="margin:.6rem 0;">{agree_html}</div>'
        f'<div class="sc-sub">Product &amp; sentiment</div>'
        f'</div>'

        f'</div>',
        unsafe_allow_html=True,
    )


def render_loading(slot, step: int) -> None:
    """
    Live step tracker rendered into a st.empty() slot.
    step: 0=init, 1=baseline, 2=autoprompt, 3=done
    """
    STEPS = [
        ("Initialising engines", 0),
        ("Running Baseline pipeline", 1),
        ("Running AutoPrompt \u2014 multi-variant", 2),
        ("Scoring and ranking results", 3),
    ]
    rows = ""
    for label, idx in STEPS:
        if idx < step:
            ic, lc, spin, ch = "done", "done", "", "&#10003;"
        elif idx == step:
            ic, lc = "active", "active"
            ch, spin = "", '<span class="spin-ring"></span>'
        else:
            ic, lc, spin, ch = "pending", "pending", "", "&middot;"
        rows += (
            f'<div class="ls-row">'
            f'<span class="ls-icon {ic}">{ch}</span>'
            f'<span class="ls-lbl {lc}">{label}</span>'
            f'{spin}'
            f'</div>'
        )
    slot.markdown(
        f'<div class="load-wrap">'
        f'<div class="load-title">Analysis Pipeline</div>'
        f'<div class="ls-steps">{rows}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_empty() -> None:
    """Pre-run illustrated empty state."""
    st.markdown(
        '<div class="empty-wrap">'
        '<div class="empty-icon">&#128300;</div>'
        '<div class="empty-title">Ready to benchmark</div>'
        '<div class="empty-sub">Enter a product review above and click '
        '<strong style="color:#4a5080;">Analyse</strong> to run the pipeline.</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_error(msg: str) -> None:
    """Structured error state card."""
    st.markdown(
        f'<div class="err-wrap">'
        f'<div class="err-icon">&#9888;</div>'
        f'<div class="err-title">Could Not Initialise Models</div>'
        f'<div class="err-body">{msg}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Polished minimal footer."""
    st.markdown(
        '<div class="footer">'
        '<div class="footer-links">'
        '<a class="footer-link" href="https://github.com/Ayush-o1/auto-Prompt" target="_blank">GitHub</a>'
        '<span class="footer-dot">&middot;</span>'
        '<a class="footer-link" href="https://github.com/Ayush-o1/auto-Prompt/issues" target="_blank">Report a Bug</a>'
        '<span class="footer-dot">&middot;</span>'
        '<span class="footer-link">AutoPrompt v3.0</span>'
        '</div>'
        '<div class="footer-copy">Built by <strong>Ayush Kumar</strong>'
        ' &nbsp;&middot;&nbsp; Dynamic prompt optimization for LLM extraction tasks</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Main application ─────────────────────────────────────────────────────────
def main() -> None:
    st.markdown(_FONTS, unsafe_allow_html=True)
    st.markdown(_CSS,   unsafe_allow_html=True)

    baseline, autoprompt, error = load_models()
    models_ready = baseline is not None

    render_sidebar(models_ready, error)
    render_hero()

    if error:
        render_error(error)
        render_footer()
        st.stop()

    # ── Input section ────────────────────────────────────────────────────────
    st.markdown('<p class="sec-label">Review Input</p>', unsafe_allow_html=True)

    review_text: str = st.text_area(
        "Review",
        value=st.session_state.get("review_text", ""),
        height=130,
        max_chars=MAX_REVIEW_CHARS,
        placeholder=(
            'Paste or type a product review \u2014 e.g. '
            '"Outstanding audio, but the cable frays after a month..."'
        ),
        label_visibility="collapsed",
    )

    n = len(review_text)
    if n > 0:
        cls = "danger" if n > MAX_REVIEW_CHARS * 0.9 else "warn" if n > MAX_REVIEW_CHARS * 0.7 else ""
        st.markdown(
            f'<div class="char-pill"><span class="{cls}">{n:,} / {MAX_REVIEW_CHARS:,}</span></div>',
            unsafe_allow_html=True,
        )

    stripped  = review_text.strip()
    too_short = len(stripped) < 10
    too_long  = len(stripped) > MAX_REVIEW_CHARS

    _, btn_col, _ = st.columns([1.5, 1, 1.5])
    with btn_col:
        run = st.button(
            "\u26a1  Analyse",
            type="primary",
            use_container_width=True,
            disabled=too_short or too_long,
        )

    if run and too_long:
        render_error(f"Review exceeds {MAX_REVIEW_CHARS:,} character limit.")
        return

    # ── Analysis pipeline ────────────────────────────────────────────────────
    if run and stripped:
        review = Review(review_id="demo", review_text=stripped)
        slot   = st.empty()

        render_loading(slot, 0)

        render_loading(slot, 1)
        baseline_result = baseline.process(review)

        render_loading(slot, 2)
        autoprompt_result = autoprompt.process(review)

        render_loading(slot, 3)
        time.sleep(0.4)
        slot.empty()

        # ── Results ──────────────────────────────────────────────────────────
        st.markdown('<div class="sec-rule"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sec-head">'
            '<span class="sec-head-t">&#128202; Results Comparison</span>'
            '<span class="sec-head-s">Baseline vs AutoPrompt</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        ap_wins = autoprompt_result.confidence >= baseline_result.confidence
        col_l, col_r = st.columns(2, gap="medium")
        with col_l:
            render_result_card(baseline_result, "baseline", is_winner=not ap_wins)
        with col_r:
            render_result_card(autoprompt_result, "autoprompt", is_winner=ap_wins)

        # ── Confidence delta ─────────────────────────────────────────────────
        st.markdown('<div class="sec-rule"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sec-head">'
            '<span class="sec-head-t">&#128200; Confidence Delta</span>'
            '<span class="sec-head-s">Quantified improvement</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        render_stat_cards(baseline_result, autoprompt_result)

        # ── Raw JSON ─────────────────────────────────────────────────────────
        with st.expander("\U0001f5c3  Raw JSON \u2014 both pipelines", expanded=False):
            jc1, jc2 = st.columns(2)
            with jc1:
                st.caption("Baseline")
                st.json(baseline_result.model_dump())
            with jc2:
                st.caption("AutoPrompt")
                st.json(autoprompt_result.model_dump())

    elif not run:
        render_empty()

    render_footer()


if __name__ == "__main__":
    main()
