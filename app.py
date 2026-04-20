"""
AutoPrompt Interactive Demo — Streamlit application v4.0.

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

# ── Page config ──────────────────────────────────────────────────────────────
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
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800;0,14..32,900;1,14..32,400&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
"""

# ── CSS v4.0 — Abyss Dark + Radial Depth ────────────────────────────────────
_CSS = """
<style>

/* ─── 0. GLOBAL RESET ─────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"], .stApp, .stMarkdown,
.stButton > button, .stTextArea textarea, .stTextArea label,
.stExpander, section[data-testid="stSidebar"] * {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ─── 1. HIDE STREAMLIT CHROME ────────────────────────────────────── */
#MainMenu, footer, header[data-testid="stHeader"], .stDeployButton,
div[data-testid="stToolbar"], div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"], .stAppToolbar { display: none !important; }

/* ─── 2. PAGE ─────────────────────────────────────────────────────── */
.stApp {
  background: #060818;
  background-image:
    radial-gradient(ellipse 100% 60% at 50% -15%, rgba(109,40,217,.22) 0%, transparent 55%),
    radial-gradient(ellipse 60% 50% at 90% 90%, rgba(6,182,212,.08) 0%, transparent 55%),
    radial-gradient(ellipse 40% 40% at 5% 70%, rgba(139,92,246,.05) 0%, transparent 50%);
}
.block-container {
  max-width: 1080px !important;
  padding: 0 2.5rem 6rem !important;
  margin: 0 auto !important;
}

/* ─── 3. SIDEBAR ──────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
  background: #080a18 !important;
  border-right: 1px solid rgba(255,255,255,.04) !important;
}
section[data-testid="stSidebar"] .block-container {
  padding: 2rem 1.25rem !important;
  max-width: 100% !important;
}
.sb-brand-name {
  font-size: 1.05rem; font-weight: 800; letter-spacing: -.025em;
  color: #f1f3ff; margin: 0 0 2px;
}
.sb-brand-sub {
  font-size: .67rem; color: #374060; font-weight: 400; margin: 0 0 1.1rem;
}
.s-sep { border: none; border-top: 1px solid rgba(255,255,255,.04); margin: 1.25rem 0; }
.slabel {
  font-size: .59rem; font-weight: 800; letter-spacing: .18em;
  text-transform: uppercase; color: #30355a; margin: 0 0 .7rem; display: block;
}
/* Status pills */
.pill {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 5px 12px; border-radius: 999px; font-size: .71rem; font-weight: 700;
}
.pill-g { background: rgba(16,185,129,.1); border: 1px solid rgba(16,185,129,.22); color: #34d399; }
.pill-r { background: rgba(239,68,68,.08); border: 1px solid rgba(239,68,68,.18); color: #fca5a5; }
.pill-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.8)} }
/* Steps */
.step-item { display: flex; align-items: flex-start; gap: 10px; padding: 7px 0; font-size: .77rem; color: #5a6080; line-height: 1.55; }
.step-num {
  flex-shrink: 0; width: 19px; height: 19px; border-radius: 50%;
  background: #0d1030; border: 1px solid rgba(109,40,217,.3);
  display: flex; align-items: center; justify-content: center;
  font-size: .58rem; font-weight: 800; color: #7c3aed; margin-top: 1px;
}
/* GitHub btn */
.gh-btn {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  width: 100%; padding: 8px 14px; border-radius: 9px;
  border: 1px solid rgba(255,255,255,.06); background: rgba(255,255,255,.02);
  color: #5a6080 !important; font-size: .76rem; font-weight: 500;
  text-decoration: none !important; transition: all .2s ease; margin-top: 4px;
}
.gh-btn:hover { border-color: rgba(124,58,237,.4); color: #dde2ff !important; background: rgba(124,58,237,.06); }
/* Selectbox override */
.stSelectbox > div > div {
  background: rgba(255,255,255,.03) !important; border: 1px solid rgba(255,255,255,.06) !important;
  border-radius: 9px !important; color: #6a7090 !important; font-size: .83rem !important;
}

/* ─── 4. HERO ─────────────────────────────────────────────────────── */
.hero-wrap {
  position: relative; padding: 4.5rem 0 3.5rem; text-align: center; overflow: hidden;
}
/* The large glow ring — actually visible */
.hero-glow {
  position: absolute; width: 700px; height: 700px; border-radius: 50%;
  top: -400px; left: 50%; transform: translateX(-50%);
  background: radial-gradient(circle, rgba(109,40,217,.2) 0%, rgba(109,40,217,.08) 40%, transparent 70%);
  pointer-events: none; animation: glow-breathe 5s ease-in-out infinite;
}
@keyframes glow-breathe {
  0%,100% { opacity: 1; transform: translateX(-50%) scale(1); }
  50% { opacity: .7; transform: translateX(-50%) scale(1.08); }
}
/* Dot grid */
.hero-dots {
  position: absolute; inset: 0; pointer-events: none;
  background-image: radial-gradient(circle, rgba(255,255,255,.06) 1px, transparent 1px);
  background-size: 26px 26px;
  -webkit-mask-image: radial-gradient(ellipse 70% 100% at 50% 0%, black 0%, transparent 65%);
  mask-image: radial-gradient(ellipse 70% 100% at 50% 0%, black 0%, transparent 65%);
}
.hero-inner { position: relative; z-index: 1; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 4px 14px; border-radius: 999px;
  background: rgba(109,40,217,.12); border: 1px solid rgba(109,40,217,.25);
  color: #a78bfa; font-size: .65rem; font-weight: 800; letter-spacing: .12em;
  text-transform: uppercase; margin-bottom: 1.4rem;
}
.hero-badge-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: #7c3aed; animation: pulse 1.6s ease-in-out infinite;
}
.hero-h1 {
  font-size: 4.25rem; font-weight: 900; letter-spacing: -.05em;
  line-height: 1; color: #eef0ff; margin-bottom: 1.2rem;
}
.hero-h1 .gr {
  background: linear-gradient(130deg, #a78bfa 0%, #38bdf8 55%, #a78bfa 100%);
  background-size: 200% auto;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  animation: shimmer 4s linear infinite;
}
@keyframes shimmer { to { background-position: 200% center; } }
.hero-sub {
  max-width: 460px; margin: 0 auto 2rem;
  font-size: .97rem; color: #414870; font-weight: 400; line-height: 1.65;
}
.hero-pills { display: flex; align-items: center; justify-content: center; gap: 1.5rem; flex-wrap: wrap; }
.hero-pill { display: flex; align-items: center; gap: 6px; font-size: .68rem; color: #282d50; font-weight: 500; }
.hero-pill-dot { width: 3px; height: 3px; border-radius: 50%; background: #6d28d9; opacity: .8; }
.hero-rule {
  width: 100%; height: 1px; margin-top: 3rem;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.05) 30%, rgba(255,255,255,.05) 70%, transparent);
}

/* ─── 5. INPUT PANEL ──────────────────────────────────────────────── */
.input-wrap {
  background: rgba(255,255,255,.018);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 18px; padding: 1.75rem 1.75rem 1.25rem;
  margin: 2rem 0 0; transition: border-color .25s;
}
.input-wrap:focus-within {
  border-color: rgba(109,40,217,.35);
  box-shadow: 0 0 0 3px rgba(109,40,217,.08), 0 0 40px rgba(109,40,217,.06);
}
.input-label {
  font-size: .6rem; font-weight: 800; letter-spacing: .16em;
  text-transform: uppercase; color: #30355a; margin-bottom: .85rem;
}
.stTextArea textarea {
  background: transparent !important; border: none !important;
  outline: none !important; box-shadow: none !important;
  color: #c8ccf0 !important; font-size: .92rem !important;
  line-height: 1.7 !important; padding: 0 !important;
  resize: none !important;
}
.stTextArea textarea::placeholder { color: #232740 !important; }
.stTextArea textarea:focus { box-shadow: none !important; border: none !important; }
.stTextArea > div { background: transparent !important; border: none !important; }
/* Hide Streamlit's default label for text_area */
.stTextArea > label { display: none; }
.char-row { display: flex; justify-content: flex-end; align-items: center; margin-top: .75rem; }
.char-badge {
  font-size: .63rem; font-weight: 600; color: #282d50;
  background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.05);
  border-radius: 6px; padding: 2px 8px; font-family: 'JetBrains Mono', monospace;
}
.char-badge.warn { color: #f59e0b; border-color: rgba(245,158,11,.25); }
.char-badge.danger { color: #ef4444; border-color: rgba(239,68,68,.25); }

/* ─── 6. ANALYSE BUTTON ───────────────────────────────────────────── */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #5b21b6, #7c3aed, #6d28d9) !important;
  background-size: 200% auto !important;
  color: #fff !important; border: none !important;
  border-radius: 12px !important; padding: .75rem 0 !important;
  font-size: .92rem !important; font-weight: 800 !important;
  letter-spacing: .02em !important; width: 100% !important;
  box-shadow: 0 4px 28px rgba(109,40,217,.38), inset 0 1px 0 rgba(255,255,255,.12) !important;
  transition: all .25s ease !important;
  animation: btn-shimmer 3s linear infinite !important;
}
@keyframes btn-shimmer { to { background-position: 200% center; } }
.stButton > button[kind="primary"]:hover:not(:disabled) {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 36px rgba(109,40,217,.52), inset 0 1px 0 rgba(255,255,255,.12) !important;
}
.stButton > button[kind="primary"]:active:not(:disabled) { transform: translateY(0) scale(.985) !important; }
.stButton > button[kind="primary"]:disabled { opacity: .25 !important; }
.stButton > button[kind="secondary"] {
  background: rgba(255,255,255,.03) !important; color: #5a6090 !important;
  border: 1px solid rgba(255,255,255,.07) !important;
  border-radius: 9px !important; font-size: .81rem !important; font-weight: 500 !important;
  transition: all .2s !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: rgba(124,58,237,.35) !important; color: #dde2ff !important;
  background: rgba(124,58,237,.06) !important;
}

/* ─── 7. LOADING TRACKER ──────────────────────────────────────────── */
.load-card {
  background: rgba(255,255,255,.018); border: 1px solid rgba(255,255,255,.06);
  border-radius: 18px; padding: 2rem 2rem 1.75rem; margin: 2rem 0;
}
.load-title {
  font-size:.6rem;font-weight:800;letter-spacing:.18em;text-transform:uppercase;
  color:#30355a;margin-bottom:1.5rem;text-align:center;
}
.ls-steps { display: flex; flex-direction: column; max-width: 380px; margin: 0 auto; }
.ls-row { display: flex; align-items: center; gap: 13px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,.03); font-size: .8rem; }
.ls-row:last-child { border-bottom: none; }
.ls-num { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 10px; font-weight: 800; }
.ls-num.done { background: rgba(16,185,129,.12); border: 1px solid rgba(16,185,129,.25); color: #34d399; }
.ls-num.active { background: rgba(109,40,217,.14); border: 1px solid rgba(109,40,217,.3); color: #a78bfa; }
.ls-num.wait { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06); color: #20243a; }
.ls-txt.done { color: #374060; }
.ls-txt.active { color: #c8ccf0; font-weight: 600; }
.ls-txt.wait { color: #20243a; }
.ls-spin { width: 13px; height: 13px; border-radius: 50%; border: 2px solid rgba(109,40,217,.2); border-top-color: #7c3aed; animation: spin .85s linear infinite; flex-shrink: 0; margin-left: auto; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ─── 8. RESULTS SECTION HEADER ───────────────────────────────────── */
.results-header { margin: 2.5rem 0 1.5rem; }
.results-sep {
  width: 100%; height: 1px; margin-bottom: 2rem;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.05) 30%, rgba(255,255,255,.05) 70%, transparent);
}
.results-title { font-size: .78rem; font-weight: 700; color: #9098cc; letter-spacing: -.01em; }
.results-sub { font-size: .68rem; color: #282d50; margin-left: .5rem; }

/* ─── 9. RESULT CARDS ─────────────────────────────────────────────── */
@keyframes card-rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
.rc {
  border-radius: 18px; padding: 1.75rem 1.75rem 1.5rem;
  background: linear-gradient(#090c20,#090c20) padding-box,
              linear-gradient(145deg,rgba(255,255,255,.07),rgba(255,255,255,.02)) border-box;
  border: 1px solid transparent;
  transition: box-shadow .3s, transform .3s;
  animation: card-rise .4s cubic-bezier(.4,0,.2,1) both;
}
.rc:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,.5); }
.rc.ap {
  background: linear-gradient(#090c20,#090c20) padding-box,
              linear-gradient(145deg,rgba(56,189,248,.35),rgba(109,40,217,.35)) border-box;
}
.rc.ap.winner {
  background: linear-gradient(#090c20,#090c20) padding-box,
              linear-gradient(145deg,rgba(16,185,129,.5),rgba(56,189,248,.4)) border-box;
  box-shadow: 0 0 50px rgba(16,185,129,.07), 0 0 100px rgba(16,185,129,.03);
}
.rc.ap.winner:hover { box-shadow: 0 12px 40px rgba(0,0,0,.5), 0 0 60px rgba(16,185,129,.1); }
/* Card elements */
.rc-eyebrow {
  font-size: .58rem; font-weight: 900; letter-spacing: .18em;
  text-transform: uppercase; color: #30355a; margin-bottom: 1rem; display: flex;
  align-items: center; justify-content: space-between;
}
.rc-eyebrow .lbl-ap  { color: #38bdf8; }
.rc-eyebrow .lbl-win { color: #34d399; }
.rc-winner-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 9px; border-radius: 999px;
  background: rgba(16,185,129,.1); border: 1px solid rgba(16,185,129,.25);
  color: #34d399; font-size: .6rem; font-weight: 800; letter-spacing: .07em;
  text-transform: uppercase;
}
.rc-divider { height: 1px; background: rgba(255,255,255,.04); margin: 1rem 0; }
/* Field rows */
.rc-field { margin-bottom: .85rem; }
.rc-field-key {
  font-size: .58rem; font-weight: 800; letter-spacing: .14em;
  text-transform: uppercase; color: #20243a; margin-bottom: 3px;
}
.rc-field-val { font-size: .9rem; font-weight: 600; color: #c0c6f0; }
.rc-field-reason { font-size: .78rem; color: #3d4368; line-height: 1.6; }
/* Sentiment chip */
.sc { display: inline-flex; align-items: center; gap: 5px; padding: 3px 9px; border-radius: 999px; font-size: .75rem; font-weight: 700; }
.sc-pos { background: rgba(16,185,129,.08); border: 1px solid rgba(16,185,129,.18); color: #34d399; }
.sc-neg { background: rgba(239,68,68,.08); border: 1px solid rgba(239,68,68,.18); color: #fca5a5; }
.sc-neu { background: rgba(148,163,184,.06); border: 1px solid rgba(148,163,184,.12); color: #94a3b8; }
.sc-mix { background: rgba(245,158,11,.08); border: 1px solid rgba(245,158,11,.18); color: #fcd34d; }
/* Gauge */
.rc-gauge { margin-top: 1.5rem; display: flex; justify-content: center; }

/* ─── 10. STAT CARDS ──────────────────────────────────────────────── */
.stats-row { display: grid; grid-template-columns: repeat(3,1fr); gap: .85rem; margin: 0; }
.sc-card {
  background: rgba(255,255,255,.018); border: 1px solid rgba(255,255,255,.05);
  border-radius: 16px; padding: 1.5rem 1.25rem; text-align: center; transition: border-color .2s;
}
.sc-card:hover { border-color: rgba(255,255,255,.09); }
.sc-card-lbl {
  font-size: .58rem; font-weight: 800; letter-spacing: .16em;
  text-transform: uppercase; color: #30355a; margin-bottom: .65rem;
}
.sc-card-val {
  font-size: 2.5rem; font-weight: 900; letter-spacing: -.045em;
  line-height: 1; margin-bottom: .35rem;
  font-family: 'JetBrains Mono', 'Inter', monospace;
}
.sc-card-val.violet { color: #a78bfa; }
.sc-card-val.muted  { color: #282d50; font-size: 2rem; }
.sc-unit { font-size: 1.1rem; font-weight: 700; }
.sc-unit.v { color: #5b21b6; }
.sc-unit.m { color: #181c2c; }
.sc-delta {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 3px 9px; border-radius: 999px; font-size: .68rem; font-weight: 800;
  font-family: 'JetBrains Mono', monospace; margin-bottom: 4px;
}
.sc-delta.pos { background: rgba(16,185,129,.08); color: #34d399; }
.sc-delta.neg { background: rgba(239,68,68,.08); color: #fca5a5; }
.sc-delta.neu { background: rgba(50,55,80,.3); color: #5a6080; }
.sc-card-sub { font-size: .62rem; color: #20243a; }
.agree-yes { display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:999px;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.18);color:#34d399;font-size:.75rem;font-weight:700; }
.agree-no  { display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:999px;background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.18);color:#fcd34d;font-size:.75rem;font-weight:700; }

/* ─── 11. EMPTY STATE ─────────────────────────────────────────────── */
.empty-card {
  border: 1px dashed rgba(255,255,255,.05); border-radius: 20px;
  background: rgba(255,255,255,.012); padding: 4.5rem 2rem; text-align: center;
  margin: 2.5rem 0;
}
.empty-icon-wrap {
  width: 56px; height: 56px; border-radius: 16px; margin: 0 auto 1.25rem;
  background: rgba(109,40,217,.1); border: 1px solid rgba(109,40,217,.18);
  display: flex; align-items: center; justify-content: center; font-size: 1.5rem;
}
.empty-title { font-size: .88rem; font-weight: 700; color: #30355a; margin-bottom: .4rem; }
.empty-sub   { font-size: .76rem; color: #1c2038; line-height: 1.5; }

/* ─── 12. ERROR STATE ─────────────────────────────────────────────── */
.err-card {
  background: rgba(239,68,68,.03); border: 1px solid rgba(239,68,68,.14);
  border-radius: 18px; padding: 2.5rem 2rem; text-align: center; margin: 1.5rem 0;
}
.err-icon  { font-size: 1.6rem; margin-bottom: .6rem; }
.err-title { font-size: .9rem; font-weight: 800; color: #fca5a5; margin-bottom: .4rem; }
.err-body  { font-size: .8rem; color: #3d4368; line-height: 1.6; }

/* ─── 13. EXPANDER ────────────────────────────────────────────────── */
.streamlit-expanderHeader {
  background: rgba(255,255,255,.02) !important; border: 1px solid rgba(255,255,255,.05) !important;
  border-radius: 10px !important; color: #3d4368 !important; font-size: .78rem !important;
}
.streamlit-expanderContent {
  background: rgba(0,0,0,.3) !important; border: 1px solid rgba(255,255,255,.03) !important;
  border-top: none !important; border-radius: 0 0 10px 10px !important;
}

/* ─── 14. FOOTER ──────────────────────────────────────────────────── */
.app-footer {
  margin-top: 5rem; padding-top: 1.75rem;
  border-top: 1px solid rgba(255,255,255,.04); text-align: center;
}
.footer-links { display: flex; align-items: center; justify-content: center; gap: 2rem; margin-bottom: .65rem; flex-wrap: wrap; }
.footer-a { color: #1e2238 !important; font-size: .73rem; font-weight: 500; text-decoration: none !important; transition: color .2s; }
.footer-a:hover { color: #5a6090 !important; }
.footer-sep { color: #141826; font-size: .73rem; }
.footer-copy { font-size: .65rem; color: #141826; }
.footer-copy strong { color: #1e2238; font-weight: 700; }

/* ─── 15. RESPONSIVE ──────────────────────────────────────────────── */
@media (max-width:768px) {
  .hero-h1      { font-size: 2.6rem !important; }
  .stats-row    { grid-template-columns: 1fr !important; }
  .block-container { padding: 1rem 1rem 4rem !important; }
}
@media (max-width:480px) {
  .hero-h1  { font-size: 2rem !important; }
  .hero-sub { font-size: .85rem !important; }
  .input-wrap { padding: 1.25rem !important; }
}

</style>
"""

# ── Constants ────────────────────────────────────────────────────────────────
MAX_CHARS = 2_000
ARC_LEN   = 119.4   # half-circumference of r=38

SAMPLES: dict[str, str] = {
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

SENTI: dict[str, tuple[str, str]] = {
    "positive": ("sc sc-pos", "Positive"),
    "negative": ("sc sc-neg", "Negative"),
    "neutral":  ("sc sc-neu", "Neutral"),
    "mixed":    ("sc sc-mix", "Mixed"),
    "error":    ("sc sc-neg", "Error"),
    "unknown":  ("sc sc-neu", "Unknown"),
}


# ── Model loader ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_models() -> tuple:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None, None, (
            "GEMINI_API_KEY not found. "
            "Create a .env file with: GEMINI_API_KEY=your_key_here"
        )
    try:
        cfg = load_secure_config()
        return BaselinePipeline(cfg), AutoPromptEngine(cfg), None
    except Exception as exc:
        return None, None, str(exc)


# ── Helpers ──────────────────────────────────────────────────────────────────
def _gauge(value: float, uid: str, c0: str, c1: str) -> str:
    pct    = round(value * 100)
    offset = ARC_LEN * (1.0 - min(value, 1.0))
    return (
        f'<svg viewBox="0 0 100 65" width="148" height="96"'
        f' style="display:block;overflow:visible;">'
        f'<defs><linearGradient id="gg{uid}" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{c0}"/>'
        f'<stop offset="100%" stop-color="{c1}"/>'
        f'</linearGradient></defs>'
        f'<path d="M 12 60 A 38 38 0 0 1 88 60"'
        f' fill="none" stroke="rgba(255,255,255,.04)" stroke-width="9" stroke-linecap="round"/>'
        f'<path d="M 12 60 A 38 38 0 0 1 88 60"'
        f' fill="none" stroke="url(#gg{uid})" stroke-width="9" stroke-linecap="round"'
        f' stroke-dasharray="{ARC_LEN:.1f}" stroke-dashoffset="{offset:.2f}"/>'
        f'<text x="50" y="55" text-anchor="middle"'
        f' font-family="JetBrains Mono,Inter,monospace"'
        f' font-size="20" font-weight="800" fill="#eef0ff">{pct}%</text>'
        f'</svg>'
    )


def _chip(sentiment: str) -> str:
    k = sentiment.lower()
    cls, lbl = SENTI.get(k, ("sc sc-neu", sentiment.capitalize()))
    return f'<span class="{cls}">{lbl}</span>'


def _md(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)


# ── Render: Hero ─────────────────────────────────────────────────────────────
def render_hero() -> None:
    _md(
        '<div class="hero-wrap">'
        '<div class="hero-glow"></div>'
        '<div class="hero-dots"></div>'
        '<div class="hero-inner">'
        '<div class="hero-badge"><span class="hero-badge-dot"></span>'
        'Live Demo &nbsp;&middot;&nbsp; v4.0</div>'
        '<h1 class="hero-h1">Auto<span class="gr">Prompt</span></h1>'
        '<p class="hero-sub">Benchmark a static prompt against a dynamic '
        'multi-variant optimizer &mdash; watch the confidence gap close in real time.</p>'
        '<div class="hero-pills">'
        '<span class="hero-pill"><span class="hero-pill-dot"></span>Multi-variant scoring</span>'
        '<span class="hero-pill"><span class="hero-pill-dot"></span>Shared heuristics</span>'
        '<span class="hero-pill"><span class="hero-pill-dot"></span>Real Gemini inference</span>'
        '</div>'
        '</div>'
        '<div class="hero-rule"></div>'
        '</div>'
    )


# ── Render: Sidebar ───────────────────────────────────────────────────────────
def render_sidebar(ready: bool) -> None:
    with st.sidebar:
        _md(
            '<p class="sb-brand-name">&#9889; AutoPrompt</p>'
            '<p class="sb-brand-sub">Prompt Optimization Engine</p>'
        )
        if ready:
            _md('<span class="pill pill-g"><span class="pill-dot"></span>Models Ready</span>')
        else:
            _md('<span class="pill pill-r"><span class="pill-dot"></span>No API Key</span>')

        _md('<hr class="s-sep"><span class="slabel">Sample Reviews</span>')
        sel = st.selectbox("sample", list(SAMPLES.keys()), label_visibility="collapsed")
        if st.button("Load Sample \u2192", use_container_width=True, type="secondary"):
            st.session_state["review_text"] = SAMPLES[sel]
            st.rerun()

        _md('<hr class="s-sep"><span class="slabel">How It Works</span>')
        steps = [
            "Baseline runs a single static prompt via the Gemini API.",
            "AutoPrompt generates N variant prompts and calls the LLM for each.",
            "Each extraction is scored with a shared confidence heuristic.",
            "The highest-scoring variant wins — delta shown in results.",
        ]
        for i, s in enumerate(steps, 1):
            _md(f'<div class="step-item"><span class="step-num">{i}</span><span>{s}</span></div>')

        _md('<hr class="s-sep"><span class="slabel">Resources</span>')
        _md(
            '<a class="gh-btn" href="https://github.com/Ayush-o1/auto-Prompt" target="_blank">'
            '&#8663; &nbsp; View on GitHub</a>'
        )


# ── Render: Input panel ───────────────────────────────────────────────────────
def render_input() -> tuple[str, bool]:
    """Render styled input card. Returns (stripped_text, run_clicked)."""
    _md('<div class="input-wrap">'
        '<div class="input-label">Review Input</div>')

    review: str = st.text_area(
        "Review",
        value=st.session_state.get("review_text", ""),
        height=120,
        max_chars=MAX_CHARS,
        placeholder=(
            'Paste or type a product review \u2014 e.g. '
            '"Outstanding audio, but the cable frays after a month..."'
        ),
        label_visibility="collapsed",
    )

    n   = len(review)
    cls = "danger" if n > MAX_CHARS * 0.9 else "warn" if n > MAX_CHARS * 0.7 else ""
    counter_html = f'<span class="char-badge {cls}">{n:,}&thinsp;/&thinsp;{MAX_CHARS:,}</span>' if n > 0 else ''
    _md(f'<div class="char-row">{counter_html}</div></div>')

    stripped  = review.strip()
    too_short = len(stripped) < 10
    too_long  = len(stripped) > MAX_CHARS

    _, btn_col, _ = st.columns([1.2, 1, 1.2])
    with btn_col:
        run = st.button(
            "\u26a1\u2002 Analyse",
            type="primary",
            use_container_width=True,
            disabled=too_short or too_long,
        )
    return stripped, run


# ── Render: Loading tracker ───────────────────────────────────────────────────
def render_loading(slot, step: int) -> None:
    STEPS = [
        ("Initialising engines", 0),
        ("Running Baseline pipeline", 1),
        ("Running AutoPrompt \u2014 multi-variant", 2),
        ("Scoring and ranking results", 3),
    ]
    rows = ""
    for lbl, idx in STEPS:
        if idx < step:
            nc, tc, spin, ch = "done", "done", "", "&#10003;"
        elif idx == step:
            nc, tc = "active", "active"
            ch, spin = "", '<span class="ls-spin"></span>'
        else:
            nc, tc, spin, ch = "wait", "wait", "", "&middot;"
        rows += (
            f'<div class="ls-row">'
            f'<span class="ls-num {nc}">{ch}</span>'
            f'<span class="ls-txt {tc}">{lbl}</span>'
            f'{spin}'
            f'</div>'
        )
    slot.markdown(
        f'<div class="load-card">'
        f'<div class="load-title">Analysis Pipeline</div>'
        f'<div class="ls-steps">{rows}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Render: Result card ───────────────────────────────────────────────────────
def render_card(data, card_type: str, is_winner: bool) -> None:
    if card_type == "baseline":
        card_cls, ey_cls = "rc", ""
        eyebrow, uid     = "BASELINE", "b"
        g0, g1           = "#475569", "#94a3b8"
        sub_lbl          = "Static Prompt"
        badge            = ""
    else:
        wp               = " winner" if is_winner else ""
        card_cls         = f"rc ap{wp}"
        ey_cls           = "lbl-win" if is_winner else "lbl-ap"
        eyebrow, uid     = "AUTOPROMPT", "a"
        sub_lbl          = "Dynamic Optimization"
        g0, g1           = ("#10b981", "#38bdf8") if is_winner else ("#38bdf8", "#818cf8")
        badge = (
            '<span class="rc-winner-badge">&#10003;&nbsp;Best Result</span>'
            if is_winner else ""
        )

    em   = "\u2014"
    reason = (data.reason or em)[:200] + ("\u2026" if len(data.reason or "") > 200 else "")
    product = data.product or em

    st.markdown(
        f'<div class="{card_cls}">'
        f'<div class="rc-eyebrow">'
        f'<span class="{ey_cls}">{eyebrow}</span>'
        f'{badge}'
        f'</div>'
        f'<div style="font-size:.64rem;font-weight:600;color:#282d50;margin-bottom:1.1rem;">{sub_lbl}</div>'
        f'<div class="rc-divider"></div>'
        f'<div class="rc-field"><div class="rc-field-key">Product</div>'
        f'<div class="rc-field-val">{product}</div></div>'
        f'<div class="rc-field"><div class="rc-field-key">Sentiment</div>'
        f'{_chip(data.sentiment)}</div>'
        f'<div class="rc-field"><div class="rc-field-key">Reason</div>'
        f'<div class="rc-field-reason">{reason}</div></div>'
        f'<div class="rc-gauge">{_gauge(data.confidence, uid, g0, g1)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Technical details", expanded=False):
        st.markdown(
            '<span style="font-size:.58rem;font-weight:800;letter-spacing:.14em;'
            'text-transform:uppercase;color:#30355a;">Prompt used</span>',
            unsafe_allow_html=True,
        )
        st.code(data.prompt_used, language=None)
        st.json(data.model_dump())


# ── Render: Stat cards row ────────────────────────────────────────────────────
def render_stats(bl, ap) -> None:
    d   = ap.confidence - bl.confidence
    dp  = round(d * 100, 1)
    app = round(ap.confidence * 100, 1)
    blp = round(bl.confidence * 100, 1)
    dc  = "pos" if d > 0 else "neg" if d < 0 else "neu"
    da  = "&#8593;" if d > 0 else "&#8595;" if d < 0 else "&#8594;"
    ds  = "+" if d > 0 else ""
    agree = (
        bl.product.lower() == ap.product.lower()
        and bl.sentiment.lower() == ap.sentiment.lower()
    )
    agree_html = (
        '<span class="agree-yes">&#10003;&nbsp;Match</span>'
        if agree else
        '<span class="agree-no">&#9632;&nbsp;Differs</span>'
    )
    _md(
        f'<div class="stats-row">'

        f'<div class="sc-card">'
        f'<div class="sc-card-lbl">AutoPrompt Confidence</div>'
        f'<div class="sc-card-val violet">{app:.1f}<span class="sc-unit v">%</span></div>'
        f'<div class="sc-delta {dc}">{da}&nbsp;{ds}{dp:.1f}%</div>'
        f'<div class="sc-card-sub">vs baseline</div>'
        f'</div>'

        f'<div class="sc-card">'
        f'<div class="sc-card-lbl">Baseline Confidence</div>'
        f'<div class="sc-card-val muted">{blp:.1f}<span class="sc-unit m">%</span></div>'
        f'<div class="sc-card-sub">Static single prompt</div>'
        f'</div>'

        f'<div class="sc-card">'
        f'<div class="sc-card-lbl">Pipeline Agreement</div>'
        f'<div style="margin:.65rem 0;">{agree_html}</div>'
        f'<div class="sc-card-sub">Product &amp; sentiment</div>'
        f'</div>'

        f'</div>'
    )


# ── Render: Empty state ───────────────────────────────────────────────────────
def render_empty() -> None:
    _md(
        '<div class="empty-card">'
        '<div class="empty-icon-wrap">&#9889;</div>'
        '<div class="empty-title">Ready to benchmark</div>'
        '<div class="empty-sub">Paste a product review above and click '
        '<strong style="color:#30355a;">Analyse</strong> to run the pipeline.</div>'
        '</div>'
    )


# ── Render: Error state ───────────────────────────────────────────────────────
def render_error(msg: str) -> None:
    _md(
        f'<div class="err-card">'
        f'<div class="err-icon">&#9888;</div>'
        f'<div class="err-title">Could Not Initialise Models</div>'
        f'<div class="err-body">{msg}</div>'
        f'</div>'
    )


# ── Render: Footer ────────────────────────────────────────────────────────────
def render_footer() -> None:
    _md(
        '<div class="app-footer">'
        '<div class="footer-links">'
        '<a class="footer-a" href="https://github.com/Ayush-o1/auto-Prompt" target="_blank">GitHub</a>'
        '<span class="footer-sep">&middot;</span>'
        '<a class="footer-a" href="https://github.com/Ayush-o1/auto-Prompt/issues" target="_blank">Report a Bug</a>'
        '<span class="footer-sep">&middot;</span>'
        '<span class="footer-a">AutoPrompt v4.0</span>'
        '</div>'
        '<div class="footer-copy">Built by <strong>Ayush Kumar</strong>'
        ' &nbsp;&middot;&nbsp; Dynamic prompt optimization for LLM extraction</div>'
        '</div>'
    )


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    _md(_FONTS)
    _md(_CSS)

    baseline, autoprompt, error = load_models()
    ready = baseline is not None

    render_sidebar(ready)
    render_hero()

    if error:
        render_error(error)
        render_footer()
        st.stop()

    stripped, run = render_input()

    # ── Guard: too long ───────────────────────────────────────────────────────
    if run and len(stripped) > MAX_CHARS:
        render_error(f"Review exceeds {MAX_CHARS:,} character limit.")
        return

    # ── Run pipeline ──────────────────────────────────────────────────────────
    if run and stripped:
        review = Review(review_id="demo", review_text=stripped)
        slot   = st.empty()

        render_loading(slot, 0)
        render_loading(slot, 1)
        bl_res = baseline.process(review)

        render_loading(slot, 2)
        ap_res = autoprompt.process(review)

        render_loading(slot, 3)
        time.sleep(0.35)
        slot.empty()

        # Results header
        _md(
            '<div class="results-sep"></div>'
            '<div class="results-header">'
            '<span class="results-title">&#128202; Results Comparison</span>'
            '<span class="results-sub">Baseline &rarr; AutoPrompt</span>'
            '</div>'
        )

        ap_wins = ap_res.confidence >= bl_res.confidence
        col_l, col_r = st.columns(2, gap="medium")
        with col_l:
            render_card(bl_res, "baseline", is_winner=not ap_wins)
        with col_r:
            render_card(ap_res, "autoprompt", is_winner=ap_wins)

        _md(
            '<div class="results-sep" style="margin:2.5rem 0 1.5rem;"></div>'
            '<div class="results-header">'
            '<span class="results-title">&#128200; Confidence Delta</span>'
            '<span class="results-sub">Quantified improvement</span>'
            '</div>'
        )
        render_stats(bl_res, ap_res)

        with st.expander("\U0001f5c3  Raw JSON \u2014 both pipelines", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.caption("Baseline")
                st.json(bl_res.model_dump())
            with c2:
                st.caption("AutoPrompt")
                st.json(ap_res.model_dump())

    elif not run:
        render_empty()

    render_footer()


if __name__ == "__main__":
    main()
