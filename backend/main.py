from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3, json, os

app = FastAPI(title="GradeFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "backend/gradeflow.db"


# ── DB Init ───────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
    components: dict = {}

class CourseUpdate(BaseModel):
    credits: int
    components: dict

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
    actual: Optional[float]

class Note(BaseModel):
    course_name: str = "General"
    text: str
    date: Optional[str] = None


# ── Profile ───────────────────────────────────────────────────────────────────
@app.get("/profile")
def get_profile():
    conn = get_db()
    row = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    conn.close()
    return dict(row)

@app.put("/profile")
def update_profile(p: Profile):
    conn = get_db()
    conn.execute("UPDATE profile SET student=?, year=? WHERE id=1", (p.student, p.year))
    conn.commit()
    conn.close()
    return {"ok": True}


# ── Courses ───────────────────────────────────────────────────────────────────
@app.get("/courses")
def get_courses():
    conn = get_db()
    rows = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "name": r["name"],
            "credits": r["credits"],
            "components": json.loads(r["components"]),
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
        raise HTTPException(status_code=400, detail="Course already exists")
    finally:
        conn.close()
    return {"ok": True}

@app.put("/courses/{name}")
def update_course(name: str, c: CourseUpdate):
    conn = get_db()
    conn.execute(
        "UPDATE courses SET credits=?, components=? WHERE name=?",
        (c.credits, json.dumps(c.components), name)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@app.delete("/courses/{name}")
def delete_course(name: str):
    conn = get_db()
    conn.execute("DELETE FROM entries WHERE course_name=?", (name,))
    conn.execute("DELETE FROM courses WHERE name=?", (name,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ── Entries ───────────────────────────────────────────────────────────────────
@app.get("/courses/{course_name}/entries")
def get_entries(course_name: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM entries WHERE course_name=? ORDER BY id", (course_name,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/courses/{course_name}/entries")
def add_entry(course_name: str, e: Entry):
    conn = get_db()
    conn.execute(
        "INSERT INTO entries (course_name, name, component, max_marks, actual, date) VALUES (?,?,?,?,?,?)",
        (course_name, e.name, e.component, e.max_marks, e.actual, e.date)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@app.put("/entries/{entry_id}")
def update_entry(entry_id: int, e: EntryUpdate):
    conn = get_db()
    conn.execute(
        "UPDATE entries SET name=?, component=?, max_marks=?, actual=? WHERE id=?",
        (e.name, e.component, e.max_marks, e.actual, entry_id)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int):
    conn = get_db()
    conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()
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
        "INSERT INTO notes (course_name, text, date) VALUES (?,?,?)",
        (n.course_name, n.text, n.date)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()
    return {"ok": True}