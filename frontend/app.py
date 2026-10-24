import os
import time
from collections import Counter

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")

SAMPLES = {
    "KeyError": 'user = {"name": "Anu"}\nprint(user["age"])',
    "IndexError": 'scores = [90, 85, 70]\nprint(scores[3])',
    "NameError": 'total = 10\nprint(totl + 5)',
    "ZeroDivisionError": 'def average(nums):\n    return sum(nums) / len(nums)\n\nprint(average([]))',
    "TypeError": 'age = 20\nprint("I am " + age + " years old")',
}

st.set_page_config(page_title="Explain My Error", page_icon="🪲", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #172238;
        --muted: #5e6b82;
        --accent: #6964f5;
        --accent-dark: #514bd4;
        --mint: #c8eadf;
    }
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 12% 0%, rgba(105, 100, 245, .13), transparent 34rem),
            linear-gradient(180deg, #eceef6 0%, #e7eaf2 48%, #edf0f5 100%);
        color: var(--ink);
    }
    [data-testid="stAppViewContainer"] .stMarkdown,
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
    [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"],
    [data-testid="stAppViewContainer"] [data-testid="stExpander"] summary,
    [data-testid="stAppViewContainer"] [data-testid="stMetricLabel"],
    [data-testid="stAppViewContainer"] [data-testid="stMetricValue"],
    [data-testid="stAppViewContainer"] [data-testid="stMetricDelta"],
    [data-testid="stAppViewContainer"] [data-testid="stMetricValue"] *,
    [data-testid="stAppViewContainer"] [data-testid="stDataFrame"],
    [data-testid="stAppViewContainer"] [data-testid="stTable"] {
        color: var(--ink) !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] {
        color: var(--muted) !important;
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container {
        max-width: 1440px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }
    .hero {
        position: relative;
        overflow: hidden;
        padding: 2.25rem 2.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(105, 100, 245, .2);
        border-radius: 24px;
        background: linear-gradient(120deg, #f5f5fc 0%, #e6e5f8 58%, #dcefe8 100%);
        box-shadow: 0 16px 44px rgba(31, 40, 68, .11);
    }
    .hero:after {
        content: "</>";
        position: absolute;
        right: 3rem;
        top: 50%;
        transform: translateY(-50%) rotate(-8deg);
        color: rgba(81, 75, 212, .14);
        font: 800 5rem/1 monospace;
    }
    .eyebrow {
        margin: 0 0 .65rem;
        color: var(--accent-dark);
        font-size: .76rem;
        font-weight: 750;
        letter-spacing: .13em;
        text-transform: uppercase;
    }
    .hero h1 {
        margin: 0;
        color: var(--ink);
        font-size: clamp(2rem, 4vw, 3.1rem);
        font-weight: 780;
        letter-spacing: -.055em;
        line-height: 1.08;
    }
    .hero p {
        max-width: 620px;
        margin: .85rem 0 0;
        color: var(--muted);
        font-size: 1.03rem;
        line-height: 1.65;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #d6dbe7;
        border-radius: 18px;
        background: rgba(247, 248, 252, .94);
        box-shadow: 0 10px 30px rgba(31, 40, 68, .07);
    }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: .5rem;
        border-bottom: 1px solid #d6dbe7;
    }
    [data-testid="stTabs"] [role="tab"] {
        padding: .7rem 1rem;
        color: var(--muted) !important;
        -webkit-text-fill-color: var(--muted) !important;
        font-weight: 650;
    }
    [data-testid="stTabs"] [role="tab"] * {
        color: var(--muted) !important;
        -webkit-text-fill-color: var(--muted) !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"],
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] * {
        color: var(--accent-dark) !important;
        -webkit-text-fill-color: var(--accent-dark) !important;
    }
    [data-testid="stTextArea"] textarea {
        border-color: #d3d9e6;
        border-radius: 12px;
        background: #eef0f6;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink);
        font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
        font-size: .91rem;
        line-height: 1.55;
    }
    [data-testid="stTextArea"] textarea::placeholder {
        color: #77839a !important;
        -webkit-text-fill-color: #77839a;
        opacity: 1;
    }
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--accent);
        background: #f5f5fc;
        box-shadow: 0 0 0 1px var(--accent);
    }
    .stButton > button[kind="primary"] {
        min-height: 2.9rem;
        border: 0;
        border-radius: 11px;
        background: linear-gradient(110deg, var(--accent), #8178ff);
        box-shadow: 0 7px 16px rgba(81, 75, 212, .24);
        color: #ffffff !important;
        font-weight: 700;
    }
    .stButton > button[kind="primary"]:hover {
        border: 0;
        background: linear-gradient(110deg, var(--accent-dark), #7168f5);
        box-shadow: 0 9px 20px rgba(81, 75, 212, .32);
    }
    .stButton > button:not([kind="primary"]) {
        border: 1px solid #cbd2e1;
        border-radius: 10px;
        background: #e3e7f0;
        color: #26334b !important;
        font-weight: 650;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: #aeb8ce;
        background: #d8deeb;
        color: #172238 !important;
    }
    [data-baseweb="select"] > div {
        border-color: #cbd2e1;
        background: #e3e7f0;
        color: #26334b !important;
    }
    [data-baseweb="select"] * {
        color: #26334b !important;
        -webkit-text-fill-color: #26334b;
    }
    [data-baseweb="popover"] [role="option"] {
        background: #f7f8fc;
        color: #26334b !important;
    }
    [data-baseweb="popover"] [role="option"]:hover {
        background: #e6e8f5;
    }
    [data-testid="stMetric"] {
        padding: .8rem 1rem;
        border: 1px solid #dfe3ed;
        border-radius: 14px;
        background: #eef0f6;
    }
    [data-testid="stAlert"] p { color: #26334b !important; }
    [data-testid="stCode"] {
        border: 1px solid #d6dbe7;
        border-radius: 13px;
    }
    @media (max-width: 700px) {
        .block-container { padding-top: 1rem; }
        .hero { padding: 1.6rem 1.35rem; border-radius: 18px; }
        .hero:after { right: 1rem; top: 1.3rem; transform: none; font-size: 2.5rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []
if "result" not in st.session_state:
    st.session_state.result = None
if "code" not in st.session_state:
    st.session_state.code = ""


def load_sample():
    st.session_state.code = SAMPLES[st.session_state.sample_choice]


def call_backend(code: str, error: str):
    """Returns (result_dict or None, error_message or None)."""
    try:
        r = requests.post(f"{BACKEND_URL}/explain", json={"code": code, "error": error}, timeout=90)
    except requests.exceptions.ConnectionError:
        return None, "Can't reach the backend. Is it running (or still waking up)?"
    except requests.exceptions.Timeout:
        return None, "The backend took too long. It may be waking up, so try again in a moment."
    if r.status_code == 429:
        return None, "Too many requests. Wait a minute and try again."
    if r.status_code == 503:
        return None, "The server is busy. Try again in a few seconds."
    if r.status_code == 422:
        return None, "Input too long or empty. Keep the code under 10,000 characters."
    if r.status_code != 200:
        return None, f"Unexpected error from the backend ({r.status_code})."
    return r.json(), None


st.markdown(
    """
    <section class="hero">
        <div class="eyebrow">Your personal Python debugging assistant</div>
        <h1>Debugging, made clearer.</h1>
        <p>Reproduce an error, understand what caused it, and get a corrected version
        checked before you use it.</p>
    </section>
    """,
    unsafe_allow_html=True,
)
st.info(
    "Using the Streamlit Community Cloud demo? It may sleep after about 12 hours "
    "of inactivity. Open it shortly before your demo or submission and wait for it to wake."
)

tab_explain, tab_history = st.tabs(["🔍  Explain an error", "📈  Learning history"])

# ---------------------------------------------------------------- Explain tab
with tab_explain:
    left, right = st.columns(2, gap="large")

    with left:
        with st.container(border=True):
            st.subheader("Start with your code")
            st.caption("Paste a snippet or load an example to see how the analyzer works.")
            s1, s2 = st.columns([3, 1])
            s1.selectbox("Example error", list(SAMPLES), key="sample_choice")
            s2.button("Load example", on_click=load_sample, width="stretch")

            st.text_area("Your Python code", key="code", height=260,
                         placeholder="Paste the code that is failing...",
                         help="Keep the snippet focused on the code related to the error.")
            with st.expander("Have a traceback? Add it here (optional)"):
                error_text = st.text_area(
                    "Traceback",
                    height=125,
                    placeholder="Paste the full traceback. Leave blank and we’ll try to reproduce the error.",
                    label_visibility="collapsed",
                )
            run_clicked = st.button("✨  Analyze my code", type="primary", width="stretch")

    if run_clicked:
        if not st.session_state.code.strip():
            st.warning("Paste some code first.")
        else:
            with st.spinner("Reproducing the error and checking a possible fix..."):
                result, problem = call_backend(st.session_state.code, error_text)
            if problem:
                st.session_state.result = {"status": "client_error", "message": problem}
            else:
                st.session_state.result = result
                if result.get("status") == "ok":
                    st.session_state.history.append({
                        "category": result["label"],
                        "error_type": result["error_type"],
                        "verified": result["verified"],
                        "time": time.strftime("%H:%M:%S"),
                    })

    with right:
        with st.container(border=True):
            st.subheader("Your explanation")
            st.caption("The cause, a suggested fix, and whether it passed verification.")
            res = st.session_state.result
            if res is None:
                st.markdown(
                    """
                    <div style="padding:2.6rem 1rem;text-align:center">
                        <div style="font-size:2.8rem">🧭</div>
                        <p style="font-size:1.05rem;font-weight:700;margin:.7rem 0 .3rem">
                            Your next step starts here
                        </p>
                        <p style="color:#68758a;margin:0">
                            Add code on the left and run an analysis to see a clear, verified explanation.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif res["status"] in ("client_error", "timeout", "llm_error"):
                st.error(res["message"])
            elif res["status"] == "no_error":
                st.success(res["message"])
            else:  # ok
                m1, m2 = st.columns(2)
                m1.metric("Category", res["label"])
                m2.metric("Error", f'{res["error_type"]} · line {res["line"]}')

                if res["verified"] and res["reproduced"]:
                    st.success("Verified — the original error was reproduced and the fix runs.")
                elif res["verified"]:
                    st.warning("The fix runs, but the original error could not be reproduced here. "
                               "It may depend on files or inputs, so review the suggestion.")
                else:
                    st.warning(f'Could not verify the fix: {res["verify_note"]}. Review it carefully.')

                st.markdown("#### What it means")
                st.write(res["meaning"])
                st.markdown("#### Why it happened")
                st.write(res["reason"])
                st.markdown("#### Suggested fix")
                st.code(res["fixed_code"], language="python")
                st.info(f'💡 **Remember:** {res["how_to_avoid"]}')
                st.caption(f'Verification attempts: {res["attempts"]}')

# ---------------------------------------------------------------- History tab
with tab_history:
    hist = st.session_state.history
    if not hist:
        st.info("Your learning history is empty for now. Analyze an error and your patterns will appear here.")
    else:
        counts = Counter(h["category"] for h in hist)
        top, n = counts.most_common(1)[0]
        st.metric("Most common mistake this session", top, f"{n} occurrence(s)")
        df = pd.DataFrame({"category": list(counts), "count": list(counts.values())}).set_index("category")
        st.bar_chart(df)
        st.subheader("Recent analyses")
        st.dataframe(pd.DataFrame(hist[::-1]), width="stretch", hide_index=True)
        if st.button("Clear history"):
            st.session_state.history = []
            st.rerun()