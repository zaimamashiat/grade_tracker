from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict
from pathlib import Path
import sqlite3
import json
import csv
import io

app = FastAPI(title="GradeFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB Path ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "backend" / "gradeflow.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ── DB Init ───────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id      INTEGER PRIMARY KEY DEFAULT 1,
            student TEXT    DEFAULT 'Student',
            year    TEXT    DEFAULT 'Y1S1'
        )
    """)
    c.execute("INSERT OR IGNORE INTO profile (id) VALUES (1)")

    c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT UNIQUE NOT NULL,
            credits    INTEGER DEFAULT 3,
            components TEXT DEFAULT '{}'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            name        TEXT NOT NULL,
            component   TEXT NOT NULL,
            max_marks   REAL DEFAULT 100,
            actual      REAL,
            date        TEXT,
            FOREIGN KEY (course_name) REFERENCES courses(name) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT DEFAULT 'General',
            text        TEXT NOT NULL,
            date        TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ── Pydantic Models ───────────────────────────────────────────────────────────
class Profile(BaseModel):
    student: str
    year: str


class Course(BaseModel):
    name: str
    credits: int = 3
    components: Dict = Field(default_factory=dict)


class CourseUpdate(BaseModel):
    credits: int
    components: Dict = Field(default_factory=dict)


class Entry(BaseModel):
    name: str
    component: str
    max_marks: float = 100
    actual: Optional[float] = None
    date: Optional[str] = None


class EntryUpdate(BaseModel):
    name: str
    component: str
    max_marks: float
    actual: Optional[float] = None
    date: Optional[str] = None


class Note(BaseModel):
    course_name: str = "General"
    text: str
    date: Optional[str] = None


# ── Profile ───────────────────────────────────────────────────────────────────
@app.get("/profile")
def get_profile():
    conn = get_db()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row)


@app.put("/profile")
def update_profile(p: Profile):
    conn = get_db()
    conn.execute(
        "UPDATE profile SET student = ?, year = ? WHERE id = 1",
        (p.student, p.year)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


# ── Courses ───────────────────────────────────────────────────────────────────
@app.get("/courses")
def get_courses():
    conn = get_db()
    rows = conn.execute("SELECT * FROM courses ORDER BY id").fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "name": r["name"],
            "credits": r["credits"],
            "components": json.loads(r["components"] or "{}"),
        })
    return result


@app.post("/courses")
def add_course(c: Course):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO courses (name, credits, components) VALUES (?, ?, ?)",
            (c.name, c.credits, json.dumps(c.components))
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Course already exists")
    conn.close()
    return {"ok": True}


@app.put("/courses/{name}")
def update_course(name: str, c: CourseUpdate):
    conn = get_db()
    cur = conn.execute(
        "UPDATE courses SET credits = ?, components = ? WHERE name = ?",
        (c.credits, json.dumps(c.components), name)
    )
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Course not found")

    return {"ok": True}


@app.delete("/courses/{name}")
def delete_course(name: str):
    conn = get_db()
    cur = conn.execute("DELETE FROM courses WHERE name = ?", (name,))
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Course not found")

    return {"ok": True}


# ── Entries ───────────────────────────────────────────────────────────────────
@app.get("/courses/{course_name}/entries")
def get_entries(course_name: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM entries WHERE course_name = ? ORDER BY id",
        (course_name,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/courses/{course_name}/entries")
def add_entry(course_name: str, e: Entry):
    conn = get_db()

    course = conn.execute(
        "SELECT name FROM courses WHERE name = ?",
        (course_name,)
    ).fetchone()

    if not course:
        conn.close()
        raise HTTPException(status_code=404, detail="Course not found")

    conn.execute(
        """
        INSERT INTO entries (course_name, name, component, max_marks, actual, date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (course_name, e.name, e.component, e.max_marks, e.actual, e.date)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.put("/entries/{entry_id}")
def update_entry(entry_id: int, e: EntryUpdate):
    conn = get_db()
    cur = conn.execute(
        """
        UPDATE entries
        SET name = ?, component = ?, max_marks = ?, actual = ?, date = ?
        WHERE id = ?
        """,
        (e.name, e.component, e.max_marks, e.actual, e.date, entry_id)
    )
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"ok": True}


@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int):
    conn = get_db()
    cur = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"ok": True}


# ── Notes ─────────────────────────────────────────────────────────────────────
@app.get("/notes")
def get_notes():
    conn = get_db()
    rows = conn.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/notes")
def add_note(n: Note):
    conn = get_db()
    conn.execute(
        "INSERT INTO notes (course_name, text, date) VALUES (?, ?, ?)",
        (n.course_name, n.text, n.date)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    conn = get_db()
    cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")

    return {"ok": True}


# ── CSV Export ────────────────────────────────────────────────────────────────
@app.get("/export/csv")
def export_csv():
    """
    Export all data as a single CSV file with multiple sections.
    Sections are separated by a header row: ## SECTION_NAME ##
    """
    conn = get_db()

    profile = dict(conn.execute("SELECT * FROM profile WHERE id = 1").fetchone())
    courses = conn.execute("SELECT * FROM courses ORDER BY id").fetchall()
    entries = conn.execute("SELECT * FROM entries ORDER BY id").fetchall()
    notes   = conn.execute("SELECT * FROM notes ORDER BY id").fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    # ── Profile section ──
    writer.writerow(["## PROFILE ##"])
    writer.writerow(["student", "year"])
    writer.writerow([profile["student"], profile["year"]])
    writer.writerow([])

    # ── Courses section ──
    writer.writerow(["## COURSES ##"])
    writer.writerow(["name", "credits", "components_json"])
    for c in courses:
        writer.writerow([c["name"], c["credits"], c["components"]])
    writer.writerow([])

    # ── Entries section ──
    writer.writerow(["## ENTRIES ##"])
    writer.writerow(["course_name", "name", "component", "max_marks", "actual", "date"])
    for e in entries:
        writer.writerow([e["course_name"], e["name"], e["component"],
                         e["max_marks"], e["actual"] if e["actual"] is not None else "", e["date"] or ""])
    writer.writerow([])

    # ── Notes section ──
    writer.writerow(["## NOTES ##"])
    writer.writerow(["course_name", "text", "date"])
    for n in notes:
        writer.writerow([n["course_name"], n["text"], n["date"] or ""])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=gradeflow_backup.csv"},
    )


# ── CSV Import ────────────────────────────────────────────────────────────────
@app.post("/import/csv")
async def import_csv(file: UploadFile = File(...)):
    """
    Import all data from a GradeFlow CSV backup.
    Merges courses/entries/notes; updates profile.
    Existing courses with same name are skipped (not overwritten).
    """
    content = await file.read()
    text = content.decode("utf-8-sig")   # handle BOM
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    section = None
    profile_data  = None
    courses_data  = []
    entries_data  = []
    notes_data    = []

    i = 0
    while i < len(rows):
        row = rows[i]
        if not row or all(c.strip() == "" for c in row):
            i += 1
            continue

        first = row[0].strip()
        if first == "## PROFILE ##":
            section = "profile"
            i += 2   # skip header row
            if i < len(rows) and rows[i]:
                r = rows[i]
                profile_data = {"student": r[0], "year": r[1] if len(r) > 1 else "Y1S1"}
            i += 1
            continue
        elif first == "## COURSES ##":
            section = "courses"
            i += 2   # skip header
            continue
        elif first == "## ENTRIES ##":
            section = "entries"
            i += 2
            continue
        elif first == "## NOTES ##":
            section = "notes"
            i += 2
            continue

        if section == "courses" and len(row) >= 3:
            courses_data.append({
                "name":       row[0],
                "credits":    int(row[1]) if row[1].isdigit() else 3,
                "components": row[2],
            })
        elif section == "entries" and len(row) >= 5:
            courses_data_names = [c["name"] for c in courses_data]
            actual = None
            if row[4].strip() not in ("", "None"):
                try: actual = float(row[4])
                except ValueError: pass
            entries_data.append({
                "course_name": row[0],
                "name":        row[1],
                "component":   row[2],
                "max_marks":   float(row[3]) if row[3] else 100,
                "actual":      actual,
                "date":        row[5] if len(row) > 5 else "",
            })
        elif section == "notes" and len(row) >= 2:
            notes_data.append({
                "course_name": row[0],
                "text":        row[1],
                "date":        row[2] if len(row) > 2 else "",
            })

        i += 1

    # ── Write to DB ───────────────────────────────────────────────────────────
    conn = get_db()

    if profile_data:
        conn.execute(
            "UPDATE profile SET student = ?, year = ? WHERE id = 1",
            (profile_data["student"], profile_data["year"])
        )

    imported_courses, skipped_courses = 0, 0
    for c in courses_data:
        try:
            conn.execute(
                "INSERT INTO courses (name, credits, components) VALUES (?, ?, ?)",
                (c["name"], c["credits"], c["components"])
            )
            imported_courses += 1
        except sqlite3.IntegrityError:
            skipped_courses += 1

    imported_entries = 0
    for e in entries_data:
        existing_course = conn.execute(
            "SELECT name FROM courses WHERE name = ?", (e["course_name"],)
        ).fetchone()
        if not existing_course:
            continue
        # Avoid duplicate entries (same course+name+component+date)
        dup = conn.execute(
            "SELECT id FROM entries WHERE course_name=? AND name=? AND component=? AND date=?",
            (e["course_name"], e["name"], e["component"], e["date"])
        ).fetchone()
        if not dup:
            conn.execute(
                "INSERT INTO entries (course_name, name, component, max_marks, actual, date) VALUES (?,?,?,?,?,?)",
                (e["course_name"], e["name"], e["component"], e["max_marks"], e["actual"], e["date"] or None)
            )
            imported_entries += 1

    imported_notes = 0
    for n in notes_data:
        dup = conn.execute(
            "SELECT id FROM notes WHERE course_name=? AND text=? AND date=?",
            (n["course_name"], n["text"], n["date"])
        ).fetchone()
        if not dup:
            conn.execute(
                "INSERT INTO notes (course_name, text, date) VALUES (?, ?, ?)",
                (n["course_name"], n["text"], n["date"] or None)
            )
            imported_notes += 1

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "imported": {
            "courses": imported_courses,
            "skipped_courses": skipped_courses,
            "entries": imported_entries,
            "notes": imported_notes,
        }
    }


# ── Optional Debug Route ──────────────────────────────────────────────────────
@app.get("/debug/db-path")
def debug_db_path():
    return {"db_path": str(DB_PATH.resolve())}