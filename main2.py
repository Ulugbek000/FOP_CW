"""
Deep Breathing & Psychological Wellbeing Survey — Streamlit Version
====================================================================
Module: Fundamentals of Programming CW
Description:
    A Streamlit rewrite of main.py. All business logic, validation, and data
    handling are identical; only the interface layer uses Streamlit instead of Flask.
    Navigation is managed through st.session_state instead of URL routes.
"""

import streamlit as st
import json
import csv
import os
import re
import io
from datetime import datetime, date
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS  (same types as main.py — marking criteria)
# ══════════════════════════════════════════════════════════════════════════════

SURVEY_VERSION: str = "1.0.0"                        # str
MAX_SCORE: int = 80                                   # int
PASS_THRESHOLD: float = 0.5                           # float
ALLOWED_FORMATS: list = ["txt", "csv", "json"]        # list
SCORE_RANGE: tuple = (0, 80)                          # tuple
QUESTION_IDS: range = range(1, 21)                    # range
SURVEY_ACTIVE: bool = True                            # bool
RESULTS_STORE: dict = {}                              # dict
VALID_EXTENSIONS: set = {"txt", "csv", "json"}        # set
FROZEN_STATES: frozenset = frozenset(
    {"Excellent", "Good", "Mild", "Moderate", "Elevated", "High", "Severe"}
)

QUESTIONS_FILE: str = "survey_questions.json"
SAMPLE_SCORES_FILE: str = "sample_scores.json"
RESULTS_DIR: str = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & CSS
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Psychological Wellbeing Survey",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  /* ── Hide Streamlit chrome ── */
  #MainMenu {visibility: hidden;}
  footer     {visibility: hidden;}
  header     {visibility: hidden;}

  /* ── Global background ── */
  .stApp { background-color: #f5f5f5; }
  .block-container { max-width: 780px; padding-top: 2rem; padding-bottom: 3rem; }

  /* ── Card style (applied via st.container with border) ── */
  [data-testid="stVerticalBlockBorderWrapper"] {
    background: white !important;
    border-radius: 12px !important;
    border: 1px solid #e8e8e8 !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
    padding: 1.5rem !important;
  }

  /* ── Buttons ── */
  div.stButton > button {
    background-color: #111111;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.6rem 1.6rem;
    width: 100%;
  }
  div.stButton > button:hover        { background-color: #333333; border: none; }
  div.stButton > button:focus        { box-shadow: none; border: none; }
  div.stButton > button[kind="secondary"] {
    background-color: #eeeeee;
    color: #333333;
    border: 1px solid #d4d4d4;
  }
  div.stButton > button[kind="secondary"]:hover { background-color: #d4d4d4; }

  /* ── Download buttons ── */
  div.stDownloadButton > button {
    background-color: #eeeeee;
    color: #333333;
    border: 1px solid #d4d4d4;
    border-radius: 8px;
    font-weight: 600;
    width: 100%;
  }
  div.stDownloadButton > button:hover { background-color: #d4d4d4; }

  /* ── Text inputs ── */
  .stTextInput > div > div > input {
    border: 2px solid #e0e0e0 !important;
    border-radius: 8px !important;
  }
  .stTextInput > div > div > input:focus {
    border-color: #111111 !important;
    box-shadow: none !important;
  }

  /* ── Progress bar ── */
  div[data-testid="stProgressBar"] > div { background-color: #111111 !important; }

  /* ── Radio options ── */
  [data-testid="stRadio"] > div > label {
    padding: 10px 14px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    background: white;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
  }
  [data-testid="stRadio"] > div > label:hover { border-color: #111111; }

  /* ── Custom HTML helpers ── */
  .result-banner {
    background: #111111; color: white; border-radius: 12px;
    padding: 2rem; margin-bottom: 1.5rem;
  }
  .score-big   { font-size: 3.2rem; font-weight: 800; letter-spacing: -1px; }
  .score-denom { font-size: 1.5rem; font-weight: 400; color: #aaaaaa; }
  .state-label { font-size: 1.1rem; font-weight: 500; color: #cccccc; margin-top: 0.5rem; }
  .pct-track   { background:#333333; border-radius:4px; height:10px; margin:10px 0 4px; overflow:hidden; }
  .pct-fill    { height:100%; background:white; border-radius:4px; }
  .pct-lbls    { display:flex; justify-content:space-between; font-size:0.75rem; color:#888; }
  .pct-note    { font-size:0.9rem; color:#cccccc; margin-top:8px; }
  .answer-row  { display:flex; justify-content:space-between; align-items:center;
                 padding:8px 0; border-bottom:1px solid #f0f0f0; font-size:0.9rem; }
  .answer-row:last-child { border-bottom:none; }
  .badge       { padding:3px 10px; border-radius:99px; font-size:0.8rem; font-weight:600;
                 background:#f0f0f0; color:#555555; }
  .section-title { font-size:1.3rem; font-weight:600; color:#222222; margin-bottom:0.75rem; }
  .hint-text   { font-size:0.82rem; color:#999999; margin-top:0.25rem; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTIONS  (identical logic to main.py)
# ══════════════════════════════════════════════════════════════════════════════

def load_questions(filepath: str) -> dict:
    """Load survey questions and states from an external JSON file at runtime."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def load_sample_scores(filepath: str) -> list:
    """Load the sample population scores from an external JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["scores"]


def append_score_to_sample(score: int, filepath: str) -> None:
    """
    Append a new respondent score to the sample scores file.
    Grows the dataset over time for more accurate future percentiles.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["scores"].append(score)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def validate_name(name: str) -> bool:
    """
    Validate that a name contains only letters, hyphens, apostrophes, and spaces.
    Uses a for loop to check each character (required by marking criteria).
    """
    if not name or not name.strip():
        return False
    allowed_chars: set = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ -'")
    # For loop — marking criteria
    for char in name:
        if char not in allowed_chars:
            return False
    return True


def validate_date_of_birth(dob_str: str) -> bool:
    """Validate date of birth in DD/MM/YYYY format using regex then date logic."""
    pattern = r"^\d{2}/\d{2}/\d{4}$"
    if not re.match(pattern, dob_str):
        return False
    try:
        dob = datetime.strptime(dob_str, "%d/%m/%Y").date()
        today = date.today()
        if dob >= today:
            return False
        if (today - dob).days > 120 * 365:
            return False
        return True
    except ValueError:
        return False


def validate_student_id(sid: str) -> bool:
    """
    Validate student ID: digits only.
    Uses a while loop to check each character (required by marking criteria).
    """
    if not sid:
        return False
    index: int = 0
    # While loop — marking criteria
    while index < len(sid):
        if not sid[index].isdigit():
            return False
        index += 1
    return len(sid) > 0


def calculate_result(total_score: int, states: list) -> dict:
    """
    Determine the psychological state band from the total score.
    Uses if / elif / else (required by marking criteria).
    """
    if total_score < 0:
        return states[0]
    elif total_score > MAX_SCORE:
        return states[-1]
    else:
        for state in states:
            if state["min"] <= total_score <= state["max"]:
                return state
        return states[-1]


def calculate_percentile(score: int, sample_scores: list) -> int:
    """
    Return the percentage of sample respondents who scored worse (higher) than
    the given score. Higher = better wellbeing relative to the sample.
    """
    count_higher: int = sum(1 for s in sample_scores if s > score)
    percentile: int = round((count_higher / len(sample_scores)) * 100)
    return percentile


def build_histogram(sample_scores: list, bin_size: int = 5) -> dict:
    """Build histogram data from sample scores using fixed-width bins."""
    bins: list = list(range(0, MAX_SCORE + bin_size, bin_size))
    labels: list = []
    counts: list = []
    boundaries: list = []
    for i in range(len(bins) - 1):
        low: int = bins[i]
        high: int = min(bins[i + 1] - 1, MAX_SCORE)
        labels.append(f"{low}-{high}")
        boundaries.append((low, high))
        count: int = sum(1 for s in sample_scores if low <= s <= high)
        counts.append(count)
    return {"labels": labels, "counts": counts, "boundaries": boundaries}


def build_result_data(user_info: dict, answers: list, questions: list, states: list) -> dict:
    """Build a unified result dictionary from user info and survey answers."""
    total_score: int = sum(a["score"] for a in answers)
    state: dict = calculate_result(total_score, states)
    sample_scores: list = load_sample_scores(SAMPLE_SCORES_FILE)
    percentile: int = calculate_percentile(total_score, sample_scores)
    answer_records: list = []
    for i, ans in enumerate(answers):
        q = questions[i]
        answer_records.append({
            "question": q["text"],
            "chosen": ans["label"],
            "score": ans["score"],
        })
    return {
        "surname": user_info["surname"],
        "given_name": user_info["given_name"],
        "dob": user_info["dob"],
        "student_id": user_info["student_id"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": total_score,
        "state_label": state["label"],
        "state_description": state["description"],
        "percentile": percentile,
        "sample_size": len(sample_scores),
        "answers": answer_records,
    }


# ─── Content generators for download buttons ──────────────────────────────────

def generate_txt(result_data: dict) -> str:
    """Generate TXT file content from result data."""
    lines: list = [
        "=" * 60,
        "  PSYCHOLOGICAL WELLBEING SURVEY — RESULTS",
        "=" * 60,
        "",
        f"Surname:      {result_data['surname']}",
        f"Given Name:   {result_data['given_name']}",
        f"Date of Birth:{result_data['dob']}",
        f"Student ID:   {result_data['student_id']}",
        f"Date Taken:   {result_data['timestamp']}",
        "",
        f"Total Score:  {result_data['score']} / {MAX_SCORE}",
        "",
        f"State:        {result_data['state_label']}",
        "",
        "Interpretation:",
        result_data['state_description'],
        "",
        "=" * 60,
        "Answers:",
    ]
    for i, ans in enumerate(result_data["answers"], 1):
        lines.append(f"  Q{i}: {ans['question'][:60]}... -> {ans['chosen']} (score: {ans['score']})")
    return "\n".join(lines)


def generate_csv(result_data: dict) -> str:
    """Generate CSV file content from result data."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Field", "Value"])
    writer.writerow(["Surname", result_data["surname"]])
    writer.writerow(["Given Name", result_data["given_name"]])
    writer.writerow(["Date of Birth", result_data["dob"]])
    writer.writerow(["Student ID", result_data["student_id"]])
    writer.writerow(["Date Taken", result_data["timestamp"]])
    writer.writerow(["Total Score", result_data["score"]])
    writer.writerow(["Max Score", MAX_SCORE])
    writer.writerow(["Psychological State", result_data["state_label"]])
    writer.writerow(["Description", result_data["state_description"]])
    writer.writerow([])
    writer.writerow(["Q#", "Question", "Answer Chosen", "Score"])
    for i, ans in enumerate(result_data["answers"], 1):
        writer.writerow([i, ans["question"], ans["chosen"], ans["score"]])
    return buf.getvalue()


def generate_json(result_data: dict) -> str:
    """Generate JSON file content from result data."""
    output: dict = {
        "survey": "Deep Breathing & Psychological Wellbeing Survey",
        "version": SURVEY_VERSION,
        "respondent": {
            "surname": result_data["surname"],
            "given_name": result_data["given_name"],
            "date_of_birth": result_data["dob"],
            "student_id": result_data["student_id"],
        },
        "result": {
            "timestamp": result_data["timestamp"],
            "total_score": result_data["score"],
            "max_score": MAX_SCORE,
            "percentage": round(result_data["score"] / MAX_SCORE * 100, 1),
            "state": result_data["state_label"],
            "description": result_data["state_description"],
        },
        "answers": result_data["answers"],
    }
    return json.dumps(output, indent=4, ensure_ascii=False)


# ─── Matplotlib chart helper ──────────────────────────────────────────────────

def build_chart_figure(sample_scores: list, user_score: int | None) -> plt.Figure:
    """
    Build a grayscale matplotlib bar chart of the score distribution.
    The bar containing the user's score is filled black; all others are light gray.
    """
    histogram: dict = build_histogram(sample_scores)
    labels: list = histogram["labels"]
    counts: list = histogram["counts"]
    boundaries: list = histogram["boundaries"]

    user_bin: int | None = None
    if user_score is not None:
        for i, (low, high) in enumerate(boundaries):
            if low <= user_score <= high:
                user_bin = i
                break

    colors: list = [
        "#111111" if i == user_bin else "#d4d4d4"
        for i in range(len(counts))
    ]

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bars = ax.bar(labels, counts, color=colors, edgecolor="#bbbbbb", linewidth=0.6,
                  width=0.7)

    # Label the user's bar
    if user_bin is not None:
        bar = bars[user_bin]
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.2,
            "Your\nscore",
            ha="center", va="bottom", fontsize=8, color="#111111", fontweight="bold"
        )

    ax.set_xlabel("Score Range", color="#888888", fontsize=11)
    ax.set_ylabel("Number of Respondents", color="#888888", fontsize=11)
    ax.tick_params(axis="x", colors="#888888", labelsize=9, rotation=45)
    ax.tick_params(axis="y", colors="#888888", labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#e8e8e8")
    ax.spines["bottom"].set_color("#e8e8e8")
    ax.yaxis.grid(True, color="#f0f0f0", linewidth=0.8)
    ax.set_axisbelow(True)

    fig.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════

def init_state() -> None:
    """Initialise all required session state keys on first run."""
    defaults: dict = {
        "page": "home",
        "user": {},
        "answers": [],
        "current_q": 1,
        "result_data": None,
        "score_recorded": False,
        "survey_data": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def nav(page: str) -> None:
    """Navigate to a page and trigger a rerun."""
    st.session_state.page = page
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def show_home() -> None:
    st.markdown('<h1 style="text-align:center; color:#111111;">Psychological Wellbeing Survey</h1>',
                unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#888888; margin-bottom:2rem;">'
                'Deep Breathing &amp; Task Confidence Assessment &middot; 20 Questions &middot; ~5 Minutes'
                '</p>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="section-title">What would you like to do?</div>', unsafe_allow_html=True)
        st.write("You can start a new survey session, or load a previously saved result from a file.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start New Survey", use_container_width=True):
                st.session_state.answers = []
                st.session_state.current_q = 1
                st.session_state.score_recorded = False
                st.session_state.result_data = None
                nav("details")
        with col2:
            if st.button("Load Existing Result", use_container_width=True):
                nav("load")

    with st.container(border=True):
        st.markdown('<div class="section-title">About This Survey</div>', unsafe_allow_html=True)
        st.write(
            "This questionnaire measures your psychological wellbeing through 20 original questions "
            "covering deep breathing habits, task initiation confidence, stress resilience, and mental clarity. "
            "Results are scored from 0–80 and mapped to one of 7 psychological states."
        )
        st.write(
            "Your score is also compared against a growing sample of respondents so you can see "
            "where you stand relative to others. Each completed survey contributes to the dataset."
        )
        st.markdown('<p style="font-size:0.85rem; color:#9ca3af; margin-top:0.5rem;">'
                    'Fundamentals of Programming CW</p>', unsafe_allow_html=True)


def show_details() -> None:
    st.markdown("[← Home](#)", unsafe_allow_html=False)
    if st.button("← Home", key="details_home"):
        nav("home")

    with st.container(border=True):
        st.markdown('<h1 style="color:#111111;">Your Details</h1>', unsafe_allow_html=True)
        st.markdown('<p class="hint-text" style="color:#888888; margin-bottom:1.5rem;">'
                    'Please enter your information below. All fields are required and validated.'
                    '</p>', unsafe_allow_html=True)

        with st.form("details_form"):
            col1, col2 = st.columns(2)
            with col1:
                surname = st.text_input("Surname", placeholder="e.g. Smith-Jones")
                st.markdown('<p class="hint-text">Letters, hyphens, apostrophes only</p>',
                            unsafe_allow_html=True)
            with col2:
                given_name = st.text_input("Given Name(s)", placeholder="e.g. Mary Ann")
                st.markdown('<p class="hint-text">Letters and spaces only</p>',
                            unsafe_allow_html=True)

            col3, col4 = st.columns(2)
            with col3:
                dob = st.text_input("Date of Birth", placeholder="DD/MM/YYYY")
                st.markdown('<p class="hint-text">Format: DD/MM/YYYY</p>',
                            unsafe_allow_html=True)
            with col4:
                student_id = st.text_input("Student ID", placeholder="e.g. 012345")
                st.markdown('<p class="hint-text">Digits only</p>', unsafe_allow_html=True)

            submitted = st.form_submit_button("Continue to Survey", use_container_width=True)

        if submitted:
            errors: list = []
            if not validate_name(surname.strip()):
                errors.append("Surname: only letters, hyphens (-), apostrophes ('), and spaces allowed. No digits.")
            if not validate_name(given_name.strip()):
                errors.append("Given name: only letters, hyphens (-), apostrophes ('), and spaces allowed. No digits.")
            if not validate_date_of_birth(dob.strip()):
                errors.append("Date of Birth: must be a valid date in DD/MM/YYYY format, and must be in the past.")
            if not validate_student_id(student_id.strip()):
                errors.append("Student ID: must contain digits only.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                st.session_state.user = {
                    "surname": surname.strip(),
                    "given_name": given_name.strip(),
                    "dob": dob.strip(),
                    "student_id": student_id.strip(),
                }
                st.session_state.answers = []
                st.session_state.current_q = 1
                nav("survey")


def show_survey() -> None:
    # Load questions once per session
    if st.session_state.survey_data is None:
        st.session_state.survey_data = load_questions(QUESTIONS_FILE)

    questions: list = st.session_state.survey_data["questions"]
    total: int = len(questions)
    q_num: int = st.session_state.current_q

    if q_num < 1 or q_num > total:
        nav("home")
        return

    # Navigation bar
    col_nav1, col_nav2 = st.columns([1, 4])
    with col_nav1:
        if st.button("← Home", key="survey_home"):
            nav("home")
    with col_nav2:
        st.markdown(f'<p style="color:#888888; font-size:0.9rem; padding-top:0.6rem;">'
                    f'Question {q_num} of {total}</p>', unsafe_allow_html=True)

    # Progress bar
    st.progress((q_num - 1) / total)

    question: dict = questions[q_num - 1]
    options: list = [opt["label"] for opt in question["options"]]

    # Determine pre-selected option
    answers: list = st.session_state.answers
    default_idx: int | None = None
    if len(answers) >= q_num and answers[q_num - 1] is not None:
        prev_label: str = answers[q_num - 1]["label"]
        if prev_label in options:
            default_idx = options.index(prev_label)

    with st.container(border=True):
        st.markdown(f'<div class="question-text" style="font-size:1.1rem; font-weight:600; '
                    f'color:#111111; margin-bottom:1rem; line-height:1.5;">'
                    f'{q_num}. {question["text"]}</div>', unsafe_allow_html=True)

        selected: str | None = st.radio(
            label="Select your answer:",
            options=options,
            index=default_idx,
            key=f"radio_q{q_num}",
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns(2)

        with btn_col1:
            if q_num > 1:
                if st.button("Back", key="back_btn", use_container_width=True):
                    # Save current selection before going back (if one was made)
                    if selected is not None:
                        _save_answer(q_num, question, selected, questions)
                    st.session_state.current_q -= 1
                    st.rerun()

        with btn_col2:
            btn_label: str = "Finish & See Results" if q_num == total else "Next"
            if st.button(btn_label, key="next_btn", use_container_width=True):
                if selected is None:
                    st.error("Please select an answer before continuing.")
                    st.stop()
                _save_answer(q_num, question, selected, questions)
                if q_num == total:
                    _compute_and_store_result()
                    nav("result")
                else:
                    st.session_state.current_q += 1
                    st.rerun()


def _save_answer(q_num: int, question: dict, selected_label: str, questions: list) -> None:
    """Store the selected answer for the given question number in session state."""
    answers: list = st.session_state.answers
    while len(answers) < q_num:
        answers.append(None)
    chosen_score: int = next(
        opt["score"] for opt in question["options"] if opt["label"] == selected_label
    )
    answers[q_num - 1] = {
        "question": question["text"],
        "label": selected_label,
        "score": chosen_score,
    }
    st.session_state.answers = answers


def _compute_and_store_result() -> None:
    """Build result_data from current session answers and cache it."""
    survey_data: dict = st.session_state.survey_data
    st.session_state.result_data = build_result_data(
        st.session_state.user,
        st.session_state.answers,
        survey_data["questions"],
        survey_data["states"],
    )


def show_result() -> None:
    if st.session_state.result_data is None:
        nav("home")
        return

    result: dict = st.session_state.result_data

    # Append score to sample file once per survey completion
    if not st.session_state.score_recorded:
        append_score_to_sample(result["score"], SAMPLE_SCORES_FILE)
        st.session_state.score_recorded = True

    if st.button("← Home", key="result_home"):
        nav("home")

    # ── Result banner ──────────────────────────────────────────────────────
    pct = result["percentile"]
    st.markdown(f"""
    <div class="result-banner">
      <div>
        <span class="score-big">{result['score']}</span>
        <span class="score-denom">&nbsp;/ 80</span>
      </div>
      <div class="state-label">{result['state_label']}</div>
      <div style="margin-top:1.2rem;">
        <div style="font-size:0.85rem; color:#aaaaaa; margin-bottom:6px;">
          Wellbeing percentile &mdash; {result['sample_size']} respondents
        </div>
        <div class="pct-track"><div class="pct-fill" style="width:{pct}%;"></div></div>
        <div class="pct-lbls"><span>0th</span><span>50th</span><span>100th</span></div>
        <div class="pct-note">
          Better wellbeing than <strong style="color:white;">{pct}%</strong>
          of the sample population
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Interpretation ─────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown('<div class="section-title">Interpretation</div>', unsafe_allow_html=True)
        st.write(result["state_description"])

    # ── How You Compare ────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown('<div class="section-title">How You Compare</div>', unsafe_allow_html=True)
        st.write(
            f"Your score of **{result['score']}** out of 80 places you at the "
            f"**{pct}th percentile** for psychological wellbeing among "
            f"{result['sample_size']} respondents. A lower score indicates better wellbeing."
        )

        table_html = """
        <table style="width:100%;border-collapse:collapse;font-size:0.88rem;margin-top:12px;">
          <thead>
            <tr style="border-bottom:2px solid #e8e8e8;">
              <th style="text-align:left;padding:8px 0;color:#555;font-weight:600;">State</th>
              <th style="text-align:right;padding:8px 0;color:#555;font-weight:600;">Score Range</th>
              <th style="text-align:right;padding:8px 0;color:#555;font-weight:600;">Sample Share</th>
            </tr>
          </thead><tbody>
        """
        rows = [
            ("Excellent Wellbeing", "0 – 14", "15%"),
            ("Good Wellbeing",      "15 – 27", "25%"),
            ("Mild Tension",        "28 – 40", "30%"),
            ("Moderate Stress",     "41 – 53", "20%"),
            ("Elevated Distress",   "54 – 66", "7%"),
            ("High Distress",       "67 – 75", "2%"),
            ("Severe Crisis",       "76 – 80", "1%"),
        ]
        for i, (label, rng, share) in enumerate(rows):
            sep = "" if i == len(rows) - 1 else "border-bottom:1px solid #f0f0f0;"
            table_html += (
                f'<tr style="{sep}"><td style="padding:8px 0;">{label}</td>'
                f'<td style="text-align:right;color:#888;">{rng}</td>'
                f'<td style="text-align:right;color:#888;">{share}</td></tr>'
            )
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("View Score Distribution Chart", use_container_width=True):
            nav("graph")

    # ── Respondent ─────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown('<div class="section-title">Respondent</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Name:** {result['surname']}, {result['given_name']}")
            st.write(f"**Student ID:** {result['student_id']}")
        with col2:
            st.write(f"**DOB:** {result['dob']}")
            st.write(f"**Date Taken:** {result['timestamp']}")

    # ── Save results ───────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown('<div class="section-title">Save Your Results</div>', unsafe_allow_html=True)
        st.write("Choose a file format to download your results:")
        sid: str = result["student_id"]
        ts: str = datetime.now().strftime("%Y%m%d_%H%M%S")

        dl1, dl2, dl3 = st.columns(3)
        with dl1:
            st.download_button(
                label="Save as TXT",
                data=generate_txt(result),
                file_name=f"{sid}_{ts}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                label="Save as CSV",
                data=generate_csv(result),
                file_name=f"{sid}_{ts}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dl3:
            st.download_button(
                label="Save as JSON",
                data=generate_json(result),
                file_name=f"{sid}_{ts}.json",
                mime="application/json",
                use_container_width=True,
            )

    # ── Your answers ───────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown('<div class="section-title">Your Answers</div>', unsafe_allow_html=True)
        rows_html = ""
        for i, ans in enumerate(result["answers"], 1):
            q_text = ans["question"][:70] + ("..." if len(ans["question"]) > 70 else "")
            rows_html += (
                f'<div class="answer-row">'
                f'<span style="color:#555555;">Q{i}: {q_text}</span>'
                f'<span>{ans["chosen"]} <span class="badge">+{ans["score"]}</span></span>'
                f'</div>'
            )
        rows_html += (
            f'<div style="margin-top:16px;padding-top:14px;border-top:2px solid #e8e8e8;'
            f'font-weight:700;font-size:1.05rem;">Total Score: {result["score"]} / 80</div>'
        )
        st.markdown(rows_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Take Survey Again", use_container_width=True):
            st.session_state.answers = []
            st.session_state.current_q = 1
            st.session_state.score_recorded = False
            st.session_state.result_data = None
            nav("details")
    with col_b:
        if st.button("Home", key="result_home2", use_container_width=True):
            nav("home")


def show_graph() -> None:
    col_nav1, col_nav2 = st.columns([1, 2])
    with col_nav1:
        if st.button("← Home", key="graph_home"):
            nav("home")
    with col_nav2:
        if st.session_state.result_data is not None:
            if st.button("← Back to Results", key="graph_results"):
                nav("result")

    sample_scores: list = load_sample_scores(SAMPLE_SCORES_FILE)
    user_score: int | None = (
        st.session_state.result_data["score"]
        if st.session_state.result_data is not None
        else None
    )
    percentile: int | None = (
        calculate_percentile(user_score, sample_scores)
        if user_score is not None
        else None
    )

    with st.container(border=True):
        st.markdown('<h1 style="color:#111111;">Score Distribution</h1>', unsafe_allow_html=True)
        subtitle = f"How scores are spread across {len(sample_scores)} respondents in the sample dataset."
        if user_score is not None:
            subtitle += f" Your score of **{user_score}** is highlighted in black."
        st.write(subtitle)

        # Legend
        legend_html = '<div style="margin-bottom:1rem;">'
        legend_html += ('<span style="display:inline-flex;align-items:center;gap:8px;'
                        'margin-right:1.5rem;font-size:0.88rem;color:#555;">'
                        '<span style="width:14px;height:14px;background:#d4d4d4;border-radius:3px;'
                        'display:inline-block;"></span> Other respondents</span>')
        if user_score is not None:
            legend_html += ('<span style="display:inline-flex;align-items:center;gap:8px;'
                            f'font-size:0.88rem;color:#555;">'
                            '<span style="width:14px;height:14px;background:#111111;border-radius:3px;'
                            f'display:inline-block;"></span> Your score ({user_score})</span>')
        legend_html += "</div>"
        st.markdown(legend_html, unsafe_allow_html=True)

        fig = build_chart_figure(sample_scores, user_score)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        st.markdown(
            '<p class="hint-text">Each bar represents a 5-point score range. '
            'A lower score indicates better psychological wellbeing. '
            'The dataset grows automatically as more users complete the survey.</p>',
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.markdown('<div class="section-title">Dataset Summary</div>', unsafe_allow_html=True)
        avg_score: float = round(sum(sample_scores) / len(sample_scores), 1)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Respondents", len(sample_scores))
        with col2:
            st.metric("Average Score", avg_score)
        with col3:
            st.metric("Lowest Score", min(sample_scores))
        with col4:
            st.metric("Highest Score", max(sample_scores))

        if user_score is not None and percentile is not None:
            st.write(
                f"Your score of **{user_score}** is better than "
                f"**{percentile}%** of respondents."
            )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.session_state.result_data is not None:
            if st.button("Back to Results", use_container_width=True):
                nav("result")
    with col_b:
        if st.button("Home", key="graph_home2", use_container_width=True):
            nav("home")


def show_load() -> None:
    if st.button("← Home", key="load_home"):
        nav("home")

    with st.container(border=True):
        st.markdown('<h1 style="color:#111111;">Load Existing Result</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color:#888888;">Upload a previously saved result file (TXT, CSV, or JSON).</p>',
                    unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Select Result File",
            type=["txt", "csv", "json"],
            help="Accepted: .txt, .csv, .json files saved by this program",
        )

        if uploaded is not None:
            filename: str = uploaded.name.lower()
            ext: str = filename.rsplit(".", 1)[-1] if "." in filename else ""

            if ext not in VALID_EXTENSIONS:
                st.error(f"Unsupported file type '.{ext}'. Please upload a TXT, CSV, or JSON file.")
            else:
                content: str = uploaded.read().decode("utf-8", errors="replace")
                loaded: dict = {}
                try:
                    if ext == "json":
                        data = json.loads(content)
                        loaded = {
                            "name": f"{data['respondent']['surname']}, {data['respondent']['given_name']}",
                            "score": f"{data['result']['total_score']} / {data['result']['max_score']}",
                            "state": data["result"]["state"],
                            "description": data["result"]["description"],
                            "timestamp": data["result"]["timestamp"],
                        }
                    elif ext == "csv":
                        reader = csv.reader(io.StringIO(content))
                        rows = {row[0]: row[1] for row in reader if len(row) >= 2}
                        loaded = {
                            "name": f"{rows.get('Surname', '?')}, {rows.get('Given Name', '?')}",
                            "score": f"{rows.get('Total Score', '?')} / {rows.get('Max Score', '?')}",
                            "state": rows.get("Psychological State", "Unknown"),
                            "description": rows.get("Description", ""),
                            "timestamp": rows.get("Date Taken", "Unknown"),
                        }
                    elif ext == "txt":
                        lines = content.splitlines()
                        info: dict = {}
                        for line in lines:
                            if ":" in line:
                                k, _, v = line.partition(":")
                                info[k.strip()] = v.strip()
                        loaded = {
                            "name": f"{info.get('Surname', '?')}, {info.get('Given Name', '?')}",
                            "score": info.get("Total Score", "?"),
                            "state": info.get("State", "Unknown"),
                            "description": info.get("Interpretation", ""),
                            "timestamp": info.get("Date Taken", "Unknown"),
                        }
                    st.success(f"File '{uploaded.name}' loaded successfully.")
                except Exception as e:
                    st.error(f"Could not parse file: {e}")
                    loaded = {}

                if loaded:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="result-banner" style="padding:1.5rem;">
                      <div style="font-size:2rem; font-weight:800;">Score: {loaded['score']}</div>
                      <div style="font-size:1.2rem; color:#cccccc;">{loaded['state']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Name:** {loaded['name']}")
                    with col2:
                        st.write(f"**Taken:** {loaded['timestamp']}")
                    st.write(loaded["description"])


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    init_state()
    page: str = st.session_state.page

    if page == "home":
        show_home()
    elif page == "details":
        show_details()
    elif page == "survey":
        if not st.session_state.user:
            nav("home")
        show_survey()
    elif page == "result":
        show_result()
    elif page == "graph":
        show_graph()
    elif page == "load":
        show_load()
    else:
        nav("home")


if __name__ == "__main__" or True:
    main()
