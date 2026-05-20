import os, json, time
import regex as re
from pathlib import Path
from typing import List, Tuple

import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# ---------- Setup ----------
st.set_page_config(page_title="AI in Education Demo: QA Tool", layout="centered")
st.title("AI in Education Demo: QA Tool")
st.caption("Authors: Student, Collaborator")
st.markdown("""
<style>
.stTextInput input, .stTextArea textarea {font-size:20px!important;}
.stSlider label, .stTextInput label, .stTextArea label {font-size:18px!important;font-weight:600;}
</style>""", unsafe_allow_html=True)

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# ---------- Config ----------
try:
    CONF = json.loads(Path("config.json").read_text(encoding="utf-8"))
except Exception:
    CONF = {"block_keywords": ["plagiarism","cheat on exam","bypass","violent threat"]}
BLOCK_KEYWORDS = list(CONF.get("block_keywords", []))

# ---------- Docs ----------
def load_docs_from_folder(folder="corpus"):
    docs, p = [], Path(folder)
    if not p.exists(): return docs
    for f in sorted(p.glob("*.txt")):
        text = f.read_text(encoding="utf-8", errors="ignore").strip()
        if text: docs.append({"title": f"Doc · {f.stem}", "text": text})
    return docs

if "docs" not in st.session_state:
    st.session_state.docs = load_docs_from_folder("corpus")

st.subheader("Upload course materials")
uploaded = st.file_uploader(
    "Upload 1–10 plain text files (.txt/.md). We will answer strictly based on these materials.",
    type=["txt","md"], accept_multiple_files=True
)
if uploaded:
    docs = []
    for f in uploaded:
        try:    text = f.read().decode("utf-8", errors="ignore").strip()
        except: text = f.read().decode("latin-1", errors="ignore").strip()
        if text: docs.append({"title": f"Uploaded · {Path(f.name).stem}", "text": text})
    st.session_state.docs = docs

if not st.session_state.docs:
    st.info("No materials loaded. Upload files above or place them in 'corpus/' and refresh.")
    st.stop()

DOC_TITLES = [d["title"] for d in st.session_state.docs]
DOC_TEXTS  = [d["text"]  for d in st.session_state.docs]
VECTORIZER = TfidfVectorizer(stop_words="english")
DOC_MATRIX = VECTORIZER.fit_transform(DOC_TEXTS)

# ---------- Guardrails ----------
PII_PATTERNS = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)")
]
def sanitize_pii(text: str) -> str:
    for pat in PII_PATTERNS: text = pat.sub("[REDACTED]", text)
    return text
def violates_policy(text: str) -> bool:
    t = text.lower(); return any(kw in t for kw in BLOCK_KEYWORDS)

# ---------- Retrieval ----------
def retrieve(query: str, k: int = 2) -> List[Tuple[str, str, float]]:
    qv = VECTORIZER.transform([query])
    sims = cosine_similarity(qv, DOC_MATRIX).flatten()
    idxs = sims.argsort()[::-1][:k]
    return [(DOC_TITLES[i], DOC_TEXTS[i], float(sims[i])) for i in idxs]

# ---------- Out-of-scope gate ----------
MIN_SIM_DEFAULT = float(os.getenv("MIN_SIM", "0.08"))
def is_summary_intent(q: str) -> bool:
    return bool(re.search(r"\b(summarize|summary|overview|main ideas|key points)\b", q.lower()))

# ---------- LLM ----------
try:
    from openai import OpenAI
    _openai_ok = True
except Exception:
    _openai_ok = False
_client = OpenAI(api_key=OPENAI_API_KEY) if (_openai_ok and OPENAI_API_KEY) else None

SYSTEM_INSTR = (
    "You are an educational assistant. Answer ONLY using the provided context. "
    "If the question cannot be answered from context, say: 'I don't know based on the provided materials.' "
    "Keep answers concise (<150 words). Cite sources as [1], [2]."
)

def llm_answer(question: str, contexts: List[Tuple[str, str, float]]) -> str:
    context_text = "\n\n".join([f"[{i+1}] {t}: {x}" for i, (t, x, _s) in enumerate(contexts)])
    user_prompt = f"Context materials:\n{context_text}\n\nQuestion: {question}\nAnswer:"
    if _client is not None:
        try:
            resp = _client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                messages=[{"role":"system","content":SYSTEM_INSTR},
                          {"role":"user","content":user_prompt}],
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception:
            pass
    if not contexts: return "I don't know based on the provided materials."
    sents = []
    for i, (title, text, _s) in enumerate(contexts[:2], start=1):
        for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
            sents.append((i, sent))
    qtok = set(re.findall(r"[A-Za-z]+", question.lower()))
    score = lambda x: len(qtok & set(re.findall(r"[A-Za-z]+", x[1].lower())))
    top = sorted(sents, key=score, reverse=True)[:2]
    if not top: return "I don't know based on the provided materials."
    body = " ".join(s for _i, s in top)
    cites = "".join([f" [{i}]" for i in sorted({i for i,_ in top})])
    return body + cites

# ---------- Logging ----------
LOG_DIR = Path("logs"); LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "workshop_log.jsonl"
def log_event(event: dict):
    event["ts"] = time.time()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

# ---------- UI ----------
st.sidebar.caption("OpenAI key detected ✅" if OPENAI_API_KEY else "No OpenAI key (offline) ❌")
MIN_SIM = st.sidebar.slider("Out-of-scope threshold", 0.00, 0.30, MIN_SIM_DEFAULT, 0.01)

st.subheader("Ask a question about the materials:")
question = st.text_area(" ", placeholder="Type your question here...", height=80, label_visibility="collapsed")

col1, col2 = st.columns([3, 2])
with col2:
    responsible = st.toggle("Responsible Mode", value=True,
                            help="ON: redact PII, block disallowed requests, and log.")
    k = st.slider("Citations to show (Top-K)", 1, 3, 2,
                  help="Larger K = more evidence; smaller K = concise.")
with col1:
    st.write(f"Loaded materials: {len(DOC_TITLES)} file(s).")

if st.button("Answer", type="primary"):
    q_raw = (question or "").strip()
    if not q_raw:
        st.warning("Please enter a question.")
    else:
        q = q_raw
        policy_hit = False
        if responsible:
            if violates_policy(q): policy_hit = True
            q = sanitize_pii(q)

        ctx = retrieve(q, k=k)
        scores = [s for _, _, s in ctx]
        max_sim = max(scores) if scores else 0.0
        out_of_scope = (not is_summary_intent(q)) and (max_sim < float(MIN_SIM))

        if responsible and policy_hit:
            answer = "Request blocked by policy (Responsible Mode). Try an educational question."
            ctx_show = ctx
        elif out_of_scope:
            answer = "I don't know based on the provided materials."
            ctx_show = []  # 不展示引用
        else:
            answer = llm_answer(q, ctx)
            ctx_show = ctx

        st.subheader("Answer"); st.write(answer)

        st.subheader("Citations")
        if ctx_show:
            for i, (title, text, score) in enumerate(ctx_show, start=1):
                st.markdown(f"**[{i}] {title}** — similarity: {score:.3f}")
                st.caption(text[:400] + ("..." if len(text) > 400 else ""))
        else:
            st.caption(f"No relevant materials found (max similarity: {max_sim:.3f}).")

        log_event({
            "question_raw": q_raw,
            "question_effective": q,
            "responsible": responsible,
            "policy_blocked": policy_hit,
            "out_of_scope": out_of_scope,
            "max_similarity": float(max_sim),
            "citations": [t for t, _x, _s in ctx_show],
            "answer_preview": (answer or "")[:200]
        })

st.divider()
with st.expander("Metrics (from logs)", expanded=False):
    try:
        lines = Path("logs/workshop_log.jsonl").read_text(encoding="utf-8").splitlines()
        total = len(lines); blocked = with_cite = idk = 0
        for ln in lines[-200:]:
            j = json.loads(ln)
            blocked += int(j.get("policy_blocked", False))
            with_cite += int(bool(j.get("citations")))
            idk += int("I don't know" in j.get("answer_preview",""))
        st.write({"total": total, "blocked": blocked, "with_citation": with_cite, "idk": idk})
    except FileNotFoundError:
        st.caption("No logs yet.")
