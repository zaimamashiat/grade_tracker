import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
import json

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GradeFlow — Academic Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ---- Root Variables ---- */
:root {
    --bg:        #0e0f14;
    --surface:   #16181f;
    --surface2:  #1e2029;
    --border:    #2a2d3a;
    --accent:    #c8a96e;
    --accent2:   #7c9fcf;
    --green:     #6ec898;
    --red:       #e07b6b;
    --text:      #e8e4dc;
    --muted:     #7a7f94;
    --serif:     'DM Serif Display', Georgia, serif;
    --sans:      'DM Sans', system-ui, sans-serif;
}

/* ---- Base ---- */
html, body, [class*="css"] {
    font-family: var(--sans);
    color: var(--text);
    background-color: var(--bg);
}

.stApp { background: var(--bg); }

/* ---- Hide Streamlit chrome ---- */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: var(--serif);
    color: var(--accent);
    font-size: 1.4rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
}

/* ---- Metrics ---- */
[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
}
[data-testid="metric-container"] label {
    color: var(--muted) !important;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--serif);
    font-size: 2.2rem !important;
    color: var(--accent) !important;
}

/* ---- Section headings ---- */
.section-title {
    font-family: var(--serif);
    font-size: 1.6rem;
    color: var(--text);
    margin: 2rem 0 0.8rem;
    border-left: 3px solid var(--accent);
    padding-left: 0.8rem;
}
.subsection {
    font-family: var(--sans);
    font-size: 0.7rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 1rem;
}

/* ---- DataEditor / tables ---- */
[data-testid="stDataFrame"], .stDataEditor {
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
}

/* ---- Expander ---- */
details {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.4rem 1rem;
    margin-bottom: 0.8rem;
}
details summary {
    font-weight: 600;
    color: var(--accent2);
    cursor: pointer;
}

/* ---- Inputs ---- */
.stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox select {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
}

/* ---- Buttons ---- */
.stButton > button {
    background: var(--accent) !important;
    color: #0e0f14 !important;
    font-weight: 600;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.45rem 1.2rem;
    letter-spacing: 0.04em;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85; }

/* ---- Grade badge ---- */
.grade-badge {
    display: inline-block;
    padding: 0.25rem 0.8rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 0.06em;
}
.badge-a  { background: #1e3a2e; color: #6ec898; }
.badge-b  { background: #1e2e3a; color: #7cb8e0; }
.badge-c  { background: #2e2e1e; color: #d4c96e; }
.badge-d  { background: #3a1e1e; color: #e07b6b; }
.badge-f  { background: #2a0e0e; color: #e03b3b; }

/* ---- CGPA ring ---- */
.cgpa-display {
    text-align: center;
    padding: 1.5rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
}
.cgpa-number {
    font-family: var(--serif);
    font-size: 4rem;
    color: var(--accent);
    line-height: 1;
}
.cgpa-label {
    font-size: 0.7rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: 0.4rem;
}

/* ---- Note card ---- */
.note-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent2);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
}
.note-meta {
    font-size: 0.68rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Init ────────────────────────────────────────────────────────
def default_state():
    if "student_name" not in st.session_state:
        st.session_state.student_name = "Student"
    if "academic_year" not in st.session_state:
        st.session_state.academic_year = "Year 1 Semester 1"
    if "courses" not in st.session_state:
        st.session_state.courses = [
            {"Course": "Mathematics", "Credits": 3, "Weight Assignments (%)": 20, "Weight Projects (%)": 20, "Weight Quizzes (%)": 20, "Weight Tests (%)": 40},
            {"Course": "Physics",     "Credits": 3, "Weight Assignments (%)": 15, "Weight Projects (%)": 25, "Weight Quizzes (%)": 20, "Weight Tests (%)": 40},
        ]
    if "grades" not in st.session_state:
        st.session_state.grades = {}   # {course: [{name, type, date_given, date_due, weight_pct, max, actual}]}
    if "notes" not in st.session_state:
        st.session_state.notes = []    # [{course, note, date}]

default_state()


# ── Helper functions ──────────────────────────────────────────────────────────
GPA_SCALE = [
    (95, "A+", 4.0), (90, "A",  4.0), (85, "A-", 3.7),
    (80, "B+", 3.3), (75, "B",  3.0), (70, "B-", 2.7),
    (65, "C+", 2.3), (60, "C",  2.0), (55, "C-", 1.7),
    (50, "D+", 1.3), (45, "D",  1.0),  (0,  "F",  0.0),
]

def pct_to_grade(pct):
    for threshold, letter, gp in GPA_SCALE:
        if pct >= threshold:
            return letter, gp
    return "F", 0.0

def badge_class(letter):
    if letter.startswith("A"): return "badge-a"
    if letter.startswith("B"): return "badge-b"
    if letter.startswith("C"): return "badge-c"
    if letter.startswith("D"): return "badge-d"
    return "badge-f"

def course_score(course_name):
    """Return weighted % score for a course from its grade entries."""
    entries = st.session_state.grades.get(course_name, [])
    if not entries:
        return None
    total_weight = 0
    weighted_sum = 0
    for e in entries:
        if e["Max"] and e["Actual"] is not None:
            w   = e["Weight (%)"]
            pct = (e["Actual"] / e["Max"]) * 100
            weighted_sum += w * pct
            total_weight  += w
    if total_weight == 0:
        return None
    return weighted_sum / total_weight

def compute_cgpa():
    courses = st.session_state.courses
    total_points  = 0
    total_credits = 0
    rows = []
    for c in courses:
        name    = c["Course"]
        credits = c["Credits"]
        score   = course_score(name)
        if score is not None:
            letter, gp = pct_to_grade(score)
        else:
            letter, gp = "—", None
        rows.append({"Course": name, "Credits": credits, "Score (%)": score, "Grade": letter, "GPA Points": gp})
        if gp is not None:
            total_points  += gp * credits
            total_credits += credits
    cgpa = total_points / total_credits if total_credits else None
    return rows, cgpa


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✦ GradeFlow")
    st.markdown("---")

    st.session_state.student_name  = st.text_input("Student Name",  st.session_state.student_name)
    st.session_state.academic_year = st.text_input("Academic Year", st.session_state.academic_year)

    st.markdown("---")
    st.markdown("**Navigation**")
    page = st.radio("", ["📋 Dashboard", "📚 Courses & Weights", "✏️ Enter Grades", "📝 Notes"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"<div style='color:var(--muted);font-size:0.72rem;letter-spacing:0.1em'>LOGGED IN AS</div>"
                f"<div style='font-weight:600'>{st.session_state.student_name}</div>"
                f"<div style='color:var(--muted);font-size:0.8rem'>{st.session_state.academic_year}</div>",
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "📋 Dashboard":
    st.markdown(f"<div class='section-title'>Academic Dashboard</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subsection'>{st.session_state.student_name} · {st.session_state.academic_year}</div>", unsafe_allow_html=True)

    rows, cgpa = compute_cgpa()

    # ── Top metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Courses Tracked", len(st.session_state.courses))
    with c2:
        graded = sum(1 for r in rows if r["Score (%)"] is not None)
        st.metric("Courses Graded", graded)
    with c3:
        total_entries = sum(len(v) for v in st.session_state.grades.values())
        st.metric("Grade Entries", total_entries)
    with c4:
        st.metric("Notes Added", len(st.session_state.notes))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CGPA + Course cards
    left, right = st.columns([1, 2])

    with left:
        cgpa_str = f"{cgpa:.2f}" if cgpa is not None else "N/A"
        if cgpa is not None:
            _, cgpa_letter = pct_to_grade(cgpa * 25), pct_to_grade(cgpa * 25)
        st.markdown(f"""
        <div class='cgpa-display'>
            <div class='cgpa-number'>{cgpa_str}</div>
            <div class='cgpa-label'>Cumulative GPA (4.0 Scale)</div>
        </div>
        """, unsafe_allow_html=True)

        # Gauge chart
        if cgpa is not None:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=cgpa,
                domain={"x": [0, 1], "y": [0, 1]},
                gauge={
                    "axis": {"range": [0, 4], "tickcolor": "#7a7f94"},
                    "bar":  {"color": "#c8a96e"},
                    "bgcolor": "#1e2029",
                    "steps": [
                        {"range": [0,   1], "color": "#3a1e1e"},
                        {"range": [1,   2], "color": "#2a2212"},
                        {"range": [2,   3], "color": "#1a2a1a"},
                        {"range": [3,   4], "color": "#1a2e3a"},
                    ],
                    "threshold": {"line": {"color": "#c8a96e", "width": 3}, "thickness": 0.8, "value": cgpa},
                },
                number={"font": {"color": "#c8a96e", "family": "DM Serif Display"}, "suffix": " / 4.0"},
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e8e4dc", height=220, margin=dict(t=20, b=10, l=20, r=20),
            )
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("<div class='subsection'>Course Summary</div>", unsafe_allow_html=True)
        if rows:
            for r in rows:
                score_str = f"{r['Score (%)']:.1f}%" if r["Score (%)"] is not None else "No data yet"
                gp_str    = f"{r['GPA Points']:.1f}" if r["GPA Points"] is not None else "—"
                bc        = badge_class(r["Grade"])
                st.markdown(f"""
                <div style='display:flex;align-items:center;justify-content:space-between;
                            background:var(--surface);border:1px solid var(--border);
                            border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.5rem;'>
                    <div>
                        <div style='font-weight:600'>{r['Course']}</div>
                        <div style='color:var(--muted);font-size:0.78rem'>{r['Credits']} credits · {score_str}</div>
                    </div>
                    <div style='text-align:right'>
                        <span class='grade-badge {bc}'>{r['Grade']}</span>
                        <div style='color:var(--muted);font-size:0.72rem;margin-top:0.2rem'>{gp_str} pts</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Add courses in the Courses & Weights tab.")

    # ── Distribution chart
    if any(r["Score (%)"] is not None for r in rows):
        st.markdown("<div class='section-title' style='font-size:1.2rem'>Grade Distribution</div>", unsafe_allow_html=True)
        names  = [r["Course"]  for r in rows if r["Score (%)"] is not None]
        scores = [r["Score (%)"] for r in rows if r["Score (%)"] is not None]
        colors = []
        for s in scores:
            l, _ = pct_to_grade(s)
            if l.startswith("A"):   colors.append("#6ec898")
            elif l.startswith("B"): colors.append("#7cb8e0")
            elif l.startswith("C"): colors.append("#d4c96e")
            elif l.startswith("D"): colors.append("#e0956b")
            else:                   colors.append("#e03b3b")

        fig2 = go.Figure(go.Bar(
            x=names, y=scores, marker_color=colors, text=[f"{s:.1f}%" for s in scores],
            textposition="outside", textfont_color="#e8e4dc",
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8e4dc", font_family="DM Sans",
            yaxis=dict(range=[0, 110], gridcolor="#2a2d3a", color="#7a7f94"),
            xaxis=dict(color="#7a7f94"),
            showlegend=False, height=320,
            margin=dict(t=30, b=20, l=10, r=10),
        )
        st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — COURSES & WEIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📚 Courses & Weights":
    st.markdown("<div class='section-title'>Courses & Assessment Weights</div>", unsafe_allow_html=True)
    st.markdown("<div class='subsection'>Define each course, its credit hours, and how each assessment type is weighted</div>", unsafe_allow_html=True)

    st.info("ℹ️  Weights per course must sum to 100%. Edit directly in the table below.", icon="💡")

    df = pd.DataFrame(st.session_state.courses)
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Course": st.column_config.TextColumn("Course Name", width="medium"),
            "Credits": st.column_config.NumberColumn("Credits", min_value=1, max_value=6, step=1, width="small"),
            "Weight Assignments (%)": st.column_config.NumberColumn("Assignments %", min_value=0, max_value=100, step=5),
            "Weight Projects (%)":    st.column_config.NumberColumn("Projects %",    min_value=0, max_value=100, step=5),
            "Weight Quizzes (%)":     st.column_config.NumberColumn("Quizzes %",     min_value=0, max_value=100, step=5),
            "Weight Tests (%)":       st.column_config.NumberColumn("Tests %",       min_value=0, max_value=100, step=5),
        },
        hide_index=True,
        key="courses_editor",
    )

    # Validate weights
    issues = []
    for _, row in edited.iterrows():
        total = (row.get("Weight Assignments (%)", 0) or 0) + \
                (row.get("Weight Projects (%)", 0) or 0) + \
                (row.get("Weight Quizzes (%)", 0) or 0) + \
                (row.get("Weight Tests (%)", 0) or 0)
        if abs(total - 100) > 0.5:
            issues.append(f"**{row['Course']}**: weights sum to {total:.0f}% (need 100%)")

    if issues:
        for issue in issues:
            st.warning(issue)
    else:
        st.success("✓ All course weights sum to 100%")

    if st.button("💾 Save Courses"):
        st.session_state.courses = edited.to_dict("records")
        # Remove grade entries for deleted courses
        valid_names = {c["Course"] for c in st.session_state.courses}
        st.session_state.grades = {k: v for k, v in st.session_state.grades.items() if k in valid_names}
        st.success("Courses saved!")
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 3 — ENTER GRADES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "✏️ Enter Grades":
    st.markdown("<div class='section-title'>Grade Entry</div>", unsafe_allow_html=True)
    st.markdown("<div class='subsection'>Log assessments per course — scores update automatically</div>", unsafe_allow_html=True)

    if not st.session_state.courses:
        st.warning("Please add courses first in the Courses & Weights tab.")
        st.stop()

    course_names = [c["Course"] for c in st.session_state.courses]
    selected_course = st.selectbox("Select Course", course_names)

    # Get course weight config
    course_cfg = next((c for c in st.session_state.courses if c["Course"] == selected_course), {})

    # ── Add new entry
    with st.expander("➕ Add New Assessment", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            a_name = st.text_input("Assessment Name", placeholder="e.g. Midterm Exam")
            a_type = st.selectbox("Type", ["Assignment", "Project", "Quiz", "Test"])
        with col2:
            a_weight = st.number_input("Weight within Type (%)", min_value=0.0, max_value=100.0, value=50.0, step=5.0,
                                       help="What % of this assessment type does this item count for?")
            a_max    = st.number_input("Max Marks", min_value=1.0, value=100.0, step=1.0)
        with col3:
            a_actual = st.number_input("Actual Marks (leave 0 if pending)", min_value=0.0, value=0.0, step=0.5)
            a_date   = st.date_input("Due Date", value=date.today())

        if st.button("Add Assessment"):
            if a_name.strip():
                # Compute contribution: weight_of_type * (a_weight/100) maps to overall %
                type_key = f"Weight {a_type}s (%)"
                type_weight = course_cfg.get(type_key, 0) or 0
                overall_weight = type_weight * (a_weight / 100)

                entry = {
                    "Name": a_name,
                    "Type": a_type,
                    "Due Date": str(a_date),
                    "Weight (%)": overall_weight,
                    "Max": a_max,
                    "Actual": a_actual if a_actual > 0 else None,
                }
                if selected_course not in st.session_state.grades:
                    st.session_state.grades[selected_course] = []
                st.session_state.grades[selected_course].append(entry)
                st.success(f"Added '{a_name}' to {selected_course}")
                st.rerun()
            else:
                st.error("Please enter an assessment name.")

    # ── Show existing entries for selected course
    entries = st.session_state.grades.get(selected_course, [])
    if entries:
        st.markdown(f"<div class='subsection'>Current Entries for {selected_course}</div>", unsafe_allow_html=True)

        df_entries = pd.DataFrame(entries)
        edited_entries = st.data_editor(
            df_entries,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Name":       st.column_config.TextColumn("Assessment"),
                "Type":       st.column_config.SelectboxColumn("Type", options=["Assignment", "Project", "Quiz", "Test"]),
                "Due Date":   st.column_config.TextColumn("Due Date"),
                "Weight (%)": st.column_config.NumberColumn("Overall Weight %", min_value=0, max_value=100, format="%.1f"),
                "Max":        st.column_config.NumberColumn("Max Marks", min_value=1),
                "Actual":     st.column_config.NumberColumn("Actual Marks", min_value=0),
            },
            hide_index=True,
            key=f"grades_editor_{selected_course}",
        )

        if st.button("💾 Save Changes"):
            st.session_state.grades[selected_course] = edited_entries.to_dict("records")
            st.success("Grades updated!")
            st.rerun()

        # ── Live score for this course
        score = course_score(selected_course)
        if score is not None:
            letter, gp = pct_to_grade(score)
            bc = badge_class(letter)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style='background:var(--surface);border:1px solid var(--border);border-radius:12px;
                        padding:1.2rem 1.6rem;display:flex;align-items:center;gap:2rem;'>
                <div>
                    <div style='color:var(--muted);font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase'>Current Score</div>
                    <div style='font-family:"DM Serif Display",serif;font-size:2.4rem;color:var(--accent)'>{score:.1f}%</div>
                </div>
                <div>
                    <span class='grade-badge {bc}' style='font-size:1.4rem;padding:0.4rem 1.2rem'>{letter}</span>
                </div>
                <div>
                    <div style='color:var(--muted);font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase'>GPA Points</div>
                    <div style='font-family:"DM Serif Display",serif;font-size:2.4rem;color:var(--accent2)'>{gp:.1f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Per-type breakdown chart
        if entries:
            type_data = {}
            for e in entries:
                t = e["Type"]
                if e["Max"] and e["Actual"] is not None:
                    pct = (e["Actual"] / e["Max"]) * 100
                    if t not in type_data:
                        type_data[t] = []
                    type_data[t].append(pct)
            if type_data:
                labels = list(type_data.keys())
                avgs   = [sum(v)/len(v) for v in type_data.values()]
                fig3 = go.Figure(go.Bar(
                    x=labels, y=avgs,
                    marker_color=["#c8a96e", "#7c9fcf", "#6ec898", "#e07b6b"],
                    text=[f"{a:.1f}%" for a in avgs], textposition="outside", textfont_color="#e8e4dc",
                ))
                fig3.update_layout(
                    title=f"{selected_course} — Avg Score by Type",
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e8e4dc", font_family="DM Sans",
                    yaxis=dict(range=[0, 115], gridcolor="#2a2d3a", color="#7a7f94"),
                    xaxis=dict(color="#7a7f94"),
                    showlegend=False, height=280,
                    margin=dict(t=40, b=20, l=10, r=10),
                )
                st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info(f"No assessments added for {selected_course} yet.")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 4 — NOTES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Notes":
    st.markdown("<div class='section-title'>Study Notes</div>", unsafe_allow_html=True)
    st.markdown("<div class='subsection'>Attach notes to any course — reminders, study tips, exam alerts</div>", unsafe_allow_html=True)

    with st.expander("➕ Add New Note", expanded=True):
        n_course = st.selectbox("Course (or General)", ["General"] + [c["Course"] for c in st.session_state.courses])
        n_text   = st.text_area("Note", placeholder="e.g. Midterm covers chapters 1-6. Focus on integration techniques.")
        if st.button("Save Note"):
            if n_text.strip():
                st.session_state.notes.append({"Course": n_course, "Note": n_text, "Date": str(date.today())})
                st.success("Note saved!")
                st.rerun()
            else:
                st.error("Please write something first.")

    if st.session_state.notes:
        filter_course = st.selectbox("Filter by Course", ["All"] + list({n["Course"] for n in st.session_state.notes}))
        filtered = st.session_state.notes if filter_course == "All" else [n for n in st.session_state.notes if n["Course"] == filter_course]

        for i, note in enumerate(reversed(filtered)):
            idx = len(filtered) - 1 - i
            col_note, col_del = st.columns([10, 1])
            with col_note:
                st.markdown(f"""
                <div class='note-card'>
                    <div class='note-meta'>{note['Course']} · {note['Date']}</div>
                    <div>{note['Note']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button("🗑", key=f"del_note_{idx}"):
                    real_idx = st.session_state.notes.index(note)
                    st.session_state.notes.pop(real_idx)
                    st.rerun()
    else:
        st.info("No notes yet. Add one above!")