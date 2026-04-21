import streamlit as st
import plotly.graph_objects as go
from datetime import date
import requests
import os
API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GradeFlow",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Manrope:wght@300;400;500;600&display=swap');

:root {
    --bg:      #0d0f14;
    --surface: #141720;
    --sf2:     #1a1e2a;
    --border:  #262b38;
    --ink:     #e8e6f0;
    --muted:   #6b7280;
    --accent:  #6ee7a0;
    --gold:    #f0a84a;
    --blue:    #7eb3f5;
    --red:     #f07070;
    --r:       14px;
}
html,body,[class*="css"]{font-family:'Manrope',sans-serif;background:var(--bg);color:var(--ink);}
.stApp{background:var(--bg);}
#MainMenu,footer,header,.stDeployButton{visibility:hidden;display:none;}
section[data-testid="stSidebar"]{display:none;}

[data-testid="metric-container"]{
    background:var(--surface);border:1.5px solid var(--border);border-radius:var(--r);
    padding:0.9rem 1.1rem;box-shadow:0 4px 16px rgba(0,0,0,.4);
}
[data-testid="metric-container"] label{
    color:var(--muted)!important;font-size:.63rem!important;
    letter-spacing:.14em!important;text-transform:uppercase!important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"]{
    font-family:'Syne',sans-serif!important;font-size:1.9rem!important;color:var(--accent)!important;
}

.stTextInput input,.stNumberInput input,.stTextArea textarea{
    background:var(--sf2)!important;border:1.5px solid var(--border)!important;
    border-radius:10px!important;color:var(--ink)!important;
}
[data-baseweb="select"]>div{
    background:var(--sf2)!important;border:1.5px solid var(--border)!important;border-radius:10px!important;color:var(--ink)!important;
}
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
[data-baseweb="select"] span { color: var(--ink) !important; }

.stButton>button{
    background:var(--accent)!important;color:#0d0f14!important;border:none!important;
    border-radius:10px!important;font-weight:700!important;padding:.38rem 1rem!important;
    transition:opacity .18s!important;font-family:'Manrope',sans-serif!important;
}
.stButton>button:hover{opacity:.72!important;}

/* Secondary (ghost) button override via class — applied via container trick */
.btn-secondary > div > button {
    background:var(--sf2)!important;color:var(--ink)!important;
    border:1.5px solid var(--border)!important;
}
.btn-secondary > div > button:hover{background:var(--border)!important;opacity:1!important;}

details{background:var(--surface);border:1.5px solid var(--border)!important;border-radius:var(--r)!important;margin-bottom:.5rem;}
details summary{font-weight:600;font-family:'Manrope',sans-serif;color:var(--ink);}
details summary:hover{color:var(--accent);}
details>div{background:var(--surface);}

.ph{display:flex;align-items:baseline;gap:.6rem;border-bottom:2.5px solid var(--border);padding-bottom:.55rem;margin-bottom:1.5rem;}
.ph h1{font-family:'Syne',sans-serif;font-size:2.1rem;font-weight:800;margin:0;color:var(--ink);}
.ph .tl{color:var(--muted);font-size:.88rem;}

.sl{font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:var(--ink);
    margin:1.4rem 0 .55rem;padding-left:.65rem;border-left:3px solid var(--gold);}
.pl{font-size:.62rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600;}

.chip{display:inline-flex;align-items:center;padding:.18rem .65rem;border-radius:999px;
      font-weight:700;font-size:.8rem;font-family:'Syne',sans-serif;}
.ca{background:#0d2e1a;color:#6ee7a0;}
.cb{background:#0d1e35;color:#7eb3f5;}
.cc{background:#2e2208;color:#f0c070;}
.cd{background:#2e1208;color:#f0a070;}
.cf{background:#2e0d0d;color:#f07070;}
.cn{background:#1e2030;color:#6b7280;}

.nc{background:var(--surface);border:1.5px solid var(--border);border-left:4px solid var(--blue);
    border-radius:10px;padding:.7rem 1rem;margin-bottom:.45rem;font-size:.83rem;}
.nm{font-size:.63rem;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);margin-bottom:.25rem;}

.div{border:none;border-top:1.5px solid var(--border);margin:1.2rem 0;}
.wok{color:var(--accent);font-size:.73rem;font-weight:600;}
.wbad{color:var(--red);font-size:.73rem;font-weight:600;}

/* ── Backup bar ── */
.backup-bar{
    display:flex;align-items:center;gap:1rem;
    background:var(--surface);border:1.5px solid var(--border);
    border-radius:12px;padding:.6rem 1rem;margin-bottom:1rem;
}
.backup-label{
    font-size:.65rem;letter-spacing:.14em;text-transform:uppercase;
    color:var(--muted);font-weight:600;white-space:nowrap;
}
/* file uploader tweaks */
[data-testid="stFileUploader"]{background:transparent!important;}
[data-testid="stFileUploader"] section{background:var(--sf2)!important;border:1.5px dashed var(--border)!important;border-radius:10px!important;}
[data-testid="stFileUploader"] label{color:var(--muted)!important;font-size:.8rem!important;}
</style>
""", unsafe_allow_html=True)


# ── API Helpers ───────────────────────────────────────────────────────────────
def api_get(path):
    try:
        r = requests.get(f"{API}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def api_post(path, data):
    try:
        r = requests.post(f"{API}{path}", json=data, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def api_put(path, data):
    try:
        r = requests.put(f"{API}{path}", json=data, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def api_delete(path):
    try:
        r = requests.delete(f"{API}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# ── Grading ───────────────────────────────────────────────────────────────────
GPA_SCALE = [
    (80,"A+",4.00),(75,"A",3.75),(70,"A-",3.50),
    (65,"B+",3.25),(60,"B",3.00),(55,"B-",2.75),
    (50,"C+",2.50),(45,"C",2.25),(40,"D",2.00),(0,"F",0.00),
]

def pct_to_grade(p):
    for t,l,g in GPA_SCALE:
        if p >= t: return l,g
    return "F",0.0

def chip_cls(letter):
    if letter.startswith("A"): return "ca"
    if letter.startswith("B"): return "cb"
    if letter in ("C+","C"):   return "cc"
    if letter == "D":          return "cd"
    if letter == "F":          return "cf"
    return "cn"

def course_score(entries, components):
    from collections import defaultdict
    if not entries: return None
    by_comp = defaultdict(list)
    for e in entries:
        if e["actual"] is not None and e["max_marks"] > 0:
            by_comp[e["component"]].append(e["actual"] / e["max_marks"] * 100)
    tw, ts = 0, 0
    for comp, ow in components.items():
        if comp in by_comp:
            avg = sum(by_comp[comp]) / len(by_comp[comp])
            ts += ow * avg
            tw += ow
    return ts / tw if tw else None


# ── Session State ─────────────────────────────────────────────────────────────
if "show_add_course" not in st.session_state: st.session_state.show_add_course = False
if "new_comps"       not in st.session_state:
    st.session_state.new_comps = [{"name":"Assignments","w":25},{"name":"Midterm","w":35},{"name":"Final","w":40}]


# ── Load Data ─────────────────────────────────────────────────────────────────
profile  = api_get("/profile") or {"student": "Student", "year": "Y1S1"}
courses  = api_get("/courses") or []
notes    = api_get("/notes")   or []

for c in courses:
    c["entries"] = api_get(f"/courses/{c['name']}/entries") or []

rows, pts, creds = [], 0, 0
for c in courses:
    score = course_score(c["entries"], c["components"])
    if score is not None:
        l, g = pct_to_grade(score)
    else:
        l, g = "—", None
    rows.append({"name": c["name"], "credits": c["credits"], "score": score, "letter": l, "gp": g})
    if g is not None:
        pts   += g * c["credits"]
        creds += c["credits"]
cgpa = pts / creds if creds else None


# ════════════════════════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════════════════════════
hc1, hc2 = st.columns([4, 1])
with hc1:
    st.markdown("<div class='ph'><h1>GradeFlow</h1><span class='tl'>Academic Grade Tracker</span></div>",
                unsafe_allow_html=True)
with hc2:
    student_val = st.text_input("Student Name", value=profile["student"],
                                placeholder="Your name", label_visibility="collapsed", key="sn")
    year_val    = st.text_input("Year/Semester", value=profile["year"],
                                placeholder="Year/Semester", label_visibility="collapsed", key="yr")
    if student_val != profile["student"] or year_val != profile["year"]:
        api_put("/profile", {"student": student_val, "year": year_val})

m1,m2,m3,m4,m5 = st.columns(5)
with m1: st.metric("CGPA", f"{cgpa:.2f}" if cgpa is not None else "N/A")
with m2: st.metric("Courses", len(courses))
with m3: st.metric("Graded", sum(1 for r in rows if r["score"] is not None))
with m4: st.metric("Assessments", sum(len(c["entries"]) for c in courses))
with m5: st.metric("Notes", len(notes))

st.markdown("<hr class='div'>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  BACKUP BAR — CSV Export / Import
# ════════════════════════════════════════════════════════════════════════════
with st.expander("💾 Backup & Restore  ·  CSV Export / Import", expanded=False):
    bcol1, bcol2 = st.columns([1, 1], gap="large")

    with bcol1:
        st.markdown("<div class='sl' style='margin-top:.2rem;font-size:.95rem'>⬇ Download Backup</div>",
                    unsafe_allow_html=True)
        st.markdown(
            "<div style='color:var(--muted);font-size:.8rem;margin-bottom:.6rem'>"
            "Exports all courses, assessments, and notes into a single CSV file you can store safely."
            "</div>", unsafe_allow_html=True
        )
        # Build CSV locally from already-loaded data (no extra API call)
        import csv, io as _io, json as _json
        _out = _io.StringIO()
        _w   = csv.writer(_out)

        _w.writerow(["## PROFILE ##"])
        _w.writerow(["student", "year"])
        _w.writerow([profile.get("student",""), profile.get("year","")])
        _w.writerow([])

        _w.writerow(["## COURSES ##"])
        _w.writerow(["name", "credits", "components_json"])
        for _c in courses:
            _w.writerow([_c["name"], _c["credits"], _json.dumps(_c["components"])])
        _w.writerow([])

        _w.writerow(["## ENTRIES ##"])
        _w.writerow(["course_name", "name", "component", "max_marks", "actual", "date"])
        for _c in courses:
            for _e in _c.get("entries", []):
                _w.writerow([_c["name"], _e["name"], _e["component"],
                             _e["max_marks"],
                             _e["actual"] if _e["actual"] is not None else "",
                             _e.get("date","") or ""])
        _w.writerow([])

        _w.writerow(["## NOTES ##"])
        _w.writerow(["course_name", "text", "date"])
        for _n in notes:
            _w.writerow([_n["course_name"], _n["text"], _n.get("date","") or ""])

        st.download_button(
            label="⬇ Download gradeflow_backup.csv",
            data=_out.getvalue().encode("utf-8"),
            file_name="gradeflow_backup.csv",
            mime="text/csv",
            key="dl_csv",
        )

    with bcol2:
        st.markdown("<div class='sl' style='margin-top:.2rem;font-size:.95rem'>⬆ Restore from Backup</div>",
                    unsafe_allow_html=True)
        st.markdown(
            "<div style='color:var(--muted);font-size:.8rem;margin-bottom:.6rem'>"
            "Upload a previously downloaded CSV. Existing data is kept; duplicate entries are skipped."
            "</div>", unsafe_allow_html=True
        )
        uploaded = st.file_uploader(
            "Upload CSV backup",
            type=["csv"],
            key="upload_csv",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            if st.button("⬆ Import Data", key="btn_import"):
                try:
                    files = {"file": (uploaded.name, uploaded.getvalue(), "text/csv")}
                    resp2 = requests.post(f"{API}/import/csv", files=files, timeout=15)
                    if resp2.status_code == 200:
                        result = resp2.json()
                        imp = result.get("imported", {})
                        st.success(
                            f"✅ Import complete — "
                            f"{imp.get('courses', 0)} courses, "
                            f"{imp.get('entries', 0)} assessments, "
                            f"{imp.get('notes', 0)} notes imported."
                            + (f" ({imp.get('skipped_courses', 0)} duplicate courses skipped)" if imp.get("skipped_courses") else "")
                        )
                        st.rerun()
                    else:
                        st.error(f"Import failed: {resp2.text}")
                except Exception as e:
                    st.error(f"API error: {e}")


st.markdown("<hr class='div'>", unsafe_allow_html=True)

LC, RC = st.columns([11, 8], gap="large")


# ════════════════════════════════════════════════════════════════════════════
#  LEFT — Courses
# ════════════════════════════════════════════════════════════════════════════
with LC:
    lh1, lh2 = st.columns([3, 1])
    with lh1: st.markdown("<div class='sl'>📚 Courses</div>", unsafe_allow_html=True)
    with lh2:
        if st.button("＋ Add Course", key="btn_add"):
            st.session_state.show_add_course = not st.session_state.show_add_course
            if st.session_state.show_add_course:
                st.session_state.new_comps = [{"name":"Assignments","w":25},{"name":"Midterm","w":35},{"name":"Final","w":40}]

    if st.session_state.show_add_course:
        with st.container(border=True):
            ac1, ac2 = st.columns(2)
            with ac1: nc_name = st.text_input("Course Name", key="nc_name", placeholder="e.g. Thermodynamics")
            with ac2: nc_cred = st.number_input("Credit Hours", 1, 6, 3, key="nc_cred")

            st.markdown("<div class='pl' style='margin:.5rem 0 .3rem'>Components — weights must sum to 100%</div>",
                        unsafe_allow_html=True)

            for i, comp in enumerate(st.session_state.new_comps):
                cc1, cc2, cc3 = st.columns([3, 1, .5])
                with cc1:
                    v = st.text_input("Component Name", value=comp["name"], key=f"nc_nm_{i}", label_visibility="collapsed")
                    st.session_state.new_comps[i]["name"] = v
                with cc2:
                    w = st.number_input("Weight", value=comp["w"], min_value=0, max_value=100,
                                        key=f"nc_w_{i}", label_visibility="collapsed")
                    st.session_state.new_comps[i]["w"] = w
                with cc3:
                    if st.button("✕", key=f"nc_del_{i}") and len(st.session_state.new_comps) > 1:
                        st.session_state.new_comps.pop(i); st.rerun()

            tw = sum(c["w"] for c in st.session_state.new_comps)
            st.markdown(f"<div class='{'wok' if abs(tw-100)<.5 else 'wbad'}'>Total: {tw}%</div>",
                        unsafe_allow_html=True)

            ba, bb, bc_ = st.columns([1, 1, 2])
            with ba:
                if st.button("＋ Component", key="nc_add_comp"):
                    st.session_state.new_comps.append({"name": "New", "w": 0}); st.rerun()
            with bb:
                if st.button("✔ Save Course", key="nc_save"):
                    if not nc_name.strip():
                        st.error("Enter a name.")
                    elif abs(tw - 100) >= .5:
                        st.error("Weights must sum to 100%.")
                    else:
                        api_post("/courses", {
                            "name": nc_name.strip(),
                            "credits": nc_cred,
                            "components": {c["name"]: c["w"] for c in st.session_state.new_comps if c["name"].strip()},
                        })
                        st.session_state.show_add_course = False
                        st.rerun()
            with bc_:
                if st.button("Cancel", key="nc_cancel"):
                    st.session_state.show_add_course = False; st.rerun()

    # ── Course expanders ──────────────────────────────────────────────────
    for cdata in courses:
        cname    = cdata["name"]
        entries  = cdata["entries"]
        comps    = cdata["components"]
        score    = course_score(entries, comps)
        letter   = pct_to_grade(score)[0] if score is not None else "—"
        score_str = f"{score:.1f}%" if score is not None else "No data"

        with st.expander(f"**{cname}** · {score_str} · {cdata['credits']} cr", expanded=False):

            st.markdown("<div class='pl'>Assessment Components & Weights</div>", unsafe_allow_html=True)
            new_comps_data = {}
            for cn in list(comps.keys()):
                cw = comps[cn]
                wc1, wc2, wc3, wc4 = st.columns([3, 1, 1, .5])
                with wc1:
                    new_cn = st.text_input("Component Name", value=cn, key=f"cn_{cname}_{cn}", label_visibility="collapsed")
                with wc2:
                    new_cw = st.number_input("Weight", value=cw, min_value=0, max_value=100,
                                             key=f"cw_{cname}_{cn}", label_visibility="collapsed")
                with wc3:
                    comp_ents = [e for e in entries if e["component"] == cn
                                 and e["actual"] is not None and e["max_marks"] > 0]
                    if comp_ents:
                        avg_raw     = sum(e["actual"] / e["max_marks"] * 100 for e in comp_ents) / len(comp_ents)
                        wtd_contrib = cw * avg_raw / 100
                        st.markdown(f"<div style='padding-top:.48rem;font-size:.75rem;color:var(--accent);font-weight:700'>{wtd_contrib:.1f}/{cw}%</div>",
                                    unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='padding-top:.48rem;font-size:.8rem;color:var(--muted)'>—</div>",
                                    unsafe_allow_html=True)
                with wc4:
                    if st.button("✕", key=f"dc_{cname}_{cn}"):
                        new_comps_copy = dict(comps)
                        del new_comps_copy[cn]
                        api_put(f"/courses/{cname}", {"credits": cdata["credits"], "components": new_comps_copy})
                        for e in entries:
                            if e["component"] == cn:
                                api_delete(f"/entries/{e['id']}")
                        st.rerun()
                new_comps_data[new_cn] = new_cw

            tw2 = sum(new_comps_data.values())
            st.markdown(f"<div class='{'wok' if abs(tw2-100)<.5 else 'wbad'}'>Total: {tw2}%</div>",
                        unsafe_allow_html=True)

            ra, rb, rc_col, rd = st.columns(4)
            with ra:
                if st.button("＋ Component", key=f"acomp_{cname}"):
                    new_c = dict(comps)
                    new_c["New Component"] = 0
                    api_put(f"/courses/{cname}", {"credits": cdata["credits"], "components": new_c})
                    st.rerun()
            with rb:
                if st.button("Save Weights", key=f"sw_{cname}"):
                    api_put(f"/courses/{cname}", {"credits": cdata["credits"], "components": new_comps_data})
                    st.success("Weights saved!"); st.rerun()
            with rc_col:
                new_cr = st.number_input("Credits", 1, 6, cdata["credits"], key=f"cr_{cname}")
                if new_cr != cdata["credits"]:
                    api_put(f"/courses/{cname}", {"credits": new_cr, "components": comps})
            with rd:
                if st.button("🗑 Delete", key=f"del_{cname}"):
                    api_delete(f"/courses/{cname}")
                    st.rerun()

            st.markdown("<hr class='div' style='margin:.6rem 0'>", unsafe_allow_html=True)

            st.markdown("<div class='pl'>Add Assessment Entry</div>", unsafe_allow_html=True)
            ge1, ge2, ge3, ge4, ge5 = st.columns([2.5, 1.5, 1, 1, 1])
            with ge1: g_name   = st.text_input("Assessment Name", placeholder="e.g. Final Exam",
                                                key=f"gn_{cname}", label_visibility="collapsed")
            with ge2:
                comp_opts = list(comps.keys())
                g_comp    = st.selectbox("Component", comp_opts, key=f"gc_{cname}", label_visibility="collapsed")
            with ge3: g_max    = st.number_input("Max Marks", min_value=1, value=100,
                                                 key=f"gmax_{cname}", label_visibility="collapsed")
            with ge4: g_actual = st.number_input("Marks Obtained", min_value=0.0, value=0.0, step=.5,
                                                 key=f"gact_{cname}", label_visibility="collapsed")
            with ge5: g_date   = st.date_input("Date", value=date.today(),
                                               key=f"gd_{cname}", label_visibility="collapsed")

            if st.button("＋ Add Entry", key=f"ae_{cname}"):
                if g_name.strip():
                    api_post(f"/courses/{cname}/entries", {
                        "name":      g_name.strip(),
                        "component": g_comp,
                        "max_marks": g_max,
                        "actual":    g_actual if g_actual > 0 else None,
                        "date":      str(g_date),
                    })
                    st.rerun()
                else:
                    st.error("Enter an assessment name.")

            if entries:
                from collections import defaultdict
                comp_raw_lists = defaultdict(list)
                for e in entries:
                    if e["actual"] is not None and e["max_marks"] > 0:
                        comp_raw_lists[e["component"]].append(e["actual"] / e["max_marks"] * 100)

                st.markdown("""
                <div style='display:grid;grid-template-columns:2.5fr 1.8fr .9fr .9fr .7fr .9fr .4fr;
                            gap:.4rem;padding:.2rem .1rem;margin-top:.6rem;'>
                  <div class='pl'>Name</div><div class='pl'>Component</div>
                  <div class='pl'>Max</div><div class='pl'>Actual</div>
                  <div class='pl'>Raw %</div><div class='pl'>Wtd contrib</div><div></div>
                </div>""", unsafe_allow_html=True)

                for e in entries:
                    raw_pct  = e["actual"] / e["max_marks"] * 100 if e["actual"] is not None and e["max_marks"] > 0 else None
                    raw_str  = f"{raw_pct:.1f}%" if raw_pct is not None else "—"
                    cw_e     = comps.get(e["component"], 0)
                    sibs     = comp_raw_lists.get(e["component"], [])
                    wtd_str  = f"{cw_e * sum(sibs)/len(sibs)/100:.2f} / {cw_e}%" if sibs else "pending"
                    wtd_color = "var(--accent)" if sibs else "var(--muted)"

                    ec1,ec2,ec3,ec4,ec5,ec6,ec7 = st.columns([2.5,1.8,.9,.9,.7,.9,.4])
                    with ec1:
                        nv = st.text_input("Entry Name", value=e["name"], key=f"en_{e['id']}", label_visibility="collapsed")
                    with ec2:
                        ci  = list(comps.keys()).index(e["component"]) if e["component"] in comps else 0
                        nc_ = st.selectbox("Entry Component", list(comps.keys()), index=ci,
                                           key=f"ec_{e['id']}", label_visibility="collapsed")
                    with ec3:
                        nm_ = st.number_input("Entry Max", value=float(e["max_marks"]), min_value=1.0,
                                              key=f"em_{e['id']}", label_visibility="collapsed")
                    with ec4:
                        na_ = st.number_input("Entry Actual", value=float(e["actual"] or 0), min_value=0.0, step=.5,
                                              key=f"ea_{e['id']}", label_visibility="collapsed")
                    with ec5:
                        st.markdown(f"<div style='padding-top:.45rem;font-weight:600;color:#7eb3f5;font-size:.8rem'>{raw_str}</div>",
                                    unsafe_allow_html=True)
                    with ec6:
                        st.markdown(f"<div style='padding-top:.45rem;font-weight:700;color:{wtd_color};font-size:.78rem'>{wtd_str}</div>",
                                    unsafe_allow_html=True)
                    with ec7:
                        if st.button("✕", key=f"de_{e['id']}"):
                            api_delete(f"/entries/{e['id']}")
                            st.rerun()

                    if nv != e["name"] or nc_ != e["component"] or nm_ != e["max_marks"] or na_ != (e["actual"] or 0):
                        api_put(f"/entries/{e['id']}", {
                            "name": nv, "component": nc_,
                            "max_marks": nm_, "actual": na_ if na_ > 0 else None,
                        })

                st.markdown("<hr class='div' style='margin:.5rem 0'>", unsafe_allow_html=True)
                st.markdown("<div class='pl'>Component Score Breakdown</div>", unsafe_allow_html=True)
                total_weighted, total_weight_covered = 0, 0
                for comp_n, comp_w in comps.items():
                    raws = comp_raw_lists.get(comp_n, [])
                    if raws:
                        avg_raw = sum(raws) / len(raws)
                        wtd     = comp_w * avg_raw / 100
                        total_weighted       += wtd
                        total_weight_covered += comp_w
                        avg_label = f"avg of {len(raws)}" if len(raws) > 1 else "1 entry"
                        st.markdown(f"""
                        <div style='background:var(--sf2);border:1px solid var(--border);border-radius:8px;
                                    padding:.5rem .8rem;margin-bottom:.3rem;font-size:.8rem;'>
                          <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:.3rem;'>
                            <span style='font-weight:700'>{comp_n}</span>
                            <span style='color:var(--muted);font-size:.72rem'>{avg_label} · avg {avg_raw:.1f}% raw</span>
                            <span style='color:var(--accent);font-weight:700'>{wtd:.2f} / {comp_w}% weighted</span>
                          </div>
                          <div style='background:var(--border);border-radius:999px;height:5px;'>
                            <div style='background:var(--accent);width:{int(avg_raw)}%;height:5px;border-radius:999px;'></div>
                          </div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='background:var(--sf2);border:1px solid var(--border);border-radius:8px;
                                    padding:.5rem .8rem;margin-bottom:.3rem;font-size:.8rem;
                                    display:flex;justify-content:space-between;'>
                          <span style='font-weight:700'>{comp_n}</span>
                          <span style='color:var(--muted)'>no entries yet</span>
                          <span style='color:var(--muted)'>— / {comp_w}%</span>
                        </div>""", unsafe_allow_html=True)

                if total_weight_covered > 0:
                    final_pct   = total_weighted / total_weight_covered * 100
                    letter_f, _ = pct_to_grade(final_pct)
                    chip_f      = chip_cls(letter_f)
                    st.markdown(f"""
                    <div style='background:var(--surface);border:1.5px solid var(--accent);border-radius:10px;
                                padding:.6rem 1rem;margin-top:.4rem;display:flex;justify-content:space-between;align-items:center;'>
                      <span style='font-family:Syne,sans-serif;font-weight:700;font-size:.9rem'>Current Score</span>
                      <span style='color:var(--muted);font-size:.75rem'>{total_weighted:.2f} pts out of {total_weight_covered}% covered</span>
                      <span style='font-family:Syne,sans-serif;font-weight:800;font-size:1.1rem;color:var(--accent)'>{final_pct:.1f}%
                        &nbsp;<span class='chip {chip_f}' style='font-size:.8rem'>{letter_f}</span>
                      </span>
                    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  RIGHT — CGPA gauge + summary + chart + notes
# ════════════════════════════════════════════════════════════════════════════
with RC:

    st.markdown("<div class='sl'>🎓 CGPA Overview</div>", unsafe_allow_html=True)
    gauge_val = cgpa if cgpa is not None else 0
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=gauge_val,
        domain={"x":[0,1],"y":[0,1]},
        number={"font":{"color":"#6ee7a0","family":"Syne","size":38},"suffix":" / 4.0"},
        gauge={
            "axis":{"range":[0,4],"tickcolor":"#6b7280","tickfont":{"color":"#6b7280","size":10}},
            "bar":{"color":"#6ee7a0","thickness":.22},
            "bgcolor":"#1a1e2a","borderwidth":0,
            "steps":[
                {"range":[0,1],"color":"#2e0d0d"},{"range":[1,2],"color":"#2e1208"},
                {"range":[2,3],"color":"#2e2208"},{"range":[3,4],"color":"#0d2e1a"},
            ],
            "threshold":{"line":{"color":"#6ee7a0","width":3},"thickness":.85,"value":gauge_val},
        },
    ))
    fig_g.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e8e6f0", height=200, margin=dict(t=10,b=0,l=20,r=20),
    )
    st.plotly_chart(fig_g, width="stretch")

    with st.expander("📋 EWU Grading Scale Reference"):
        st.markdown("""
        <table style='width:100%;border-collapse:collapse;font-size:.78rem;font-family:Manrope,sans-serif;'>
          <thead>
            <tr style='background:#262b38;color:#e8e6f0;text-align:center;'>
              <th style='padding:.35rem .6rem;'>Marks</th><th style='padding:.35rem .6rem;'>Letter</th>
              <th style='padding:.35rem .6rem;'>Grade Point</th>
            </tr>
          </thead>
          <tbody>
            <tr style='background:#0d2e1a;color:#6ee7a0;text-align:center;'><td>80 – 100</td><td><b>A+</b></td><td>4.00</td></tr>
            <tr style='background:#0d2e1a;color:#6ee7a0;text-align:center;'><td>75 – 79</td><td><b>A</b></td><td>3.75</td></tr>
            <tr style='background:#0d2e1a;color:#6ee7a0;text-align:center;'><td>70 – 74</td><td><b>A−</b></td><td>3.50</td></tr>
            <tr style='background:#0d1e35;color:#7eb3f5;text-align:center;'><td>65 – 69</td><td><b>B+</b></td><td>3.25</td></tr>
            <tr style='background:#0d1e35;color:#7eb3f5;text-align:center;'><td>60 – 64</td><td><b>B</b></td><td>3.00</td></tr>
            <tr style='background:#0d1e35;color:#7eb3f5;text-align:center;'><td>55 – 59</td><td><b>B−</b></td><td>2.75</td></tr>
            <tr style='background:#2e2208;color:#f0c070;text-align:center;'><td>50 – 54</td><td><b>C+</b></td><td>2.50</td></tr>
            <tr style='background:#2e2208;color:#f0c070;text-align:center;'><td>45 – 49</td><td><b>C</b></td><td>2.25</td></tr>
            <tr style='background:#2e1208;color:#f0a070;text-align:center;'><td>40 – 44</td><td><b>D</b></td><td>2.00</td></tr>
            <tr style='background:#2e0d0d;color:#f07070;text-align:center;'><td>Less than 40</td><td><b>F</b></td><td>0.00</td></tr>
          </tbody>
        </table>
        <div style='color:#6b7280;font-size:.65rem;margin-top:.4rem;text-align:center'>East West University Grading System</div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='pl' style='margin-bottom:.35rem'>Course Breakdown</div>", unsafe_allow_html=True)
    for r in rows:
        ss  = f"{r['score']:.1f}%" if r["score"] is not None else "—"
        gps = f"{r['gp']:.1f} pts" if r["gp"] is not None else "—"
        bc  = chip_cls(r["letter"])
        st.markdown(f"""
        <div style='display:flex;align-items:center;justify-content:space-between;
                    background:var(--surface);border:1.5px solid var(--border);border-radius:10px;
                    padding:.55rem .9rem;margin-bottom:.35rem;'>
            <div>
                <div style='font-weight:700;font-size:.86rem'>{r['name']}</div>
                <div style='color:var(--muted);font-size:.68rem'>{r['credits']} cr · {ss}</div>
            </div>
            <div style='display:flex;align-items:center;gap:.65rem'>
                <div style='color:var(--muted);font-size:.72rem'>{gps}</div>
                <span class='chip {bc}'>{r['letter']}</span>
            </div>
        </div>""", unsafe_allow_html=True)

    graded = [r for r in rows if r["score"] is not None]
    if graded:
        st.markdown("<div class='sl' style='font-size:1rem;margin-top:1rem'>📊 Score Distribution</div>",
                    unsafe_allow_html=True)
        cmap = {"A":"#6ee7a0","B":"#7eb3f5","C":"#f0a84a","D":"#f0784a","F":"#f07070"}
        bcolors = []
        for r in graded:
            for k, v in cmap.items():
                if r["letter"].startswith(k): bcolors.append(v); break
            else: bcolors.append("#6b7280")
        fig_b = go.Figure(go.Bar(
            x=[r["name"] for r in graded], y=[r["score"] for r in graded],
            marker_color=bcolors,
            text=[f"{r['score']:.1f}%" for r in graded],
            textposition="outside", textfont_color="#e8e6f0", textfont_size=10,
        ))
        fig_b.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8e6f0", font_family="Manrope",
            yaxis=dict(range=[0,115], gridcolor="#262b38", color="#6b7280"),
            xaxis=dict(color="#6b7280"), showlegend=False, height=230,
            margin=dict(t=25,b=10,l=10,r=10),
        )
        st.plotly_chart(fig_b, width="stretch")

    st.markdown("<hr class='div'>", unsafe_allow_html=True)

    st.markdown("<div class='sl'>📝 Notes</div>", unsafe_allow_html=True)
    with st.expander("＋ New Note"):
        n_course = st.selectbox("Course", ["General"] + [c["name"] for c in courses], key="nc")
        n_text   = st.text_area("Note Content", placeholder="e.g. Midterm covers chapters 1–6…",
                                key="nt", label_visibility="collapsed")
        if st.button("Save Note", key="sn_btn"):
            if n_text.strip():
                api_post("/notes", {"course_name": n_course, "text": n_text.strip(), "date": str(date.today())})
                st.rerun()

    for note in notes:
        nc1, nc2 = st.columns([10, 1])
        with nc1:
            st.markdown(f"""
            <div class='nc'>
                <div class='nm'>{note['course_name']} · {note['date']}</div>
                <div>{note['text']}</div>
            </div>""", unsafe_allow_html=True)
        with nc2:
            if st.button("✕", key=f"dn_{note['id']}"):
                api_delete(f"/notes/{note['id']}")
                st.rerun()

    if not notes:
        st.markdown("<div style='color:var(--muted);font-size:.82rem'>No notes yet.</div>",
                    unsafe_allow_html=True)