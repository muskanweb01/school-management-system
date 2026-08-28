from flask import Flask, request, redirect, render_template
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date

app = Flask(
    __name__,
    template_folder="New folder/templates",
    static_folder="New folder/templates/static"
)


# =====================================================
# DATABASE
# =====================================================

def get_db():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    conn = psycopg2.connect(database_url)
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            class_name TEXT NOT NULL,
            section TEXT,
            parent_name TEXT,
            parent_contact TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL,
            UNIQUE(student_id, attendance_date),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            teacher_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            class_name TEXT NOT NULL,
            phone TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id SERIAL PRIMARY KEY,
            class_name TEXT NOT NULL,
            section TEXT,
            teacher_name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            marks_obtained REAL NOT NULL,
            total_marks REAL NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


init_db()


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/")
def home():
    return render_template("dashboard.html")


# =====================================================
# CLASSES
# =====================================================

@app.route("/classes")
def classes():

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT * FROM classes
        ORDER BY id DESC
    """)

    class_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "classes.html",
        classes=class_list
    )


# =====================================================
# ADD CLASS
# =====================================================

@app.route("/add_class", methods=["GET", "POST"])
def add_class():

    if request.method == "POST":

        class_name = request.form["class_name"]
        section = request.form.get("section", "")
        teacher_name = request.form.get("teacher_name", "")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO classes
            (class_name, section, teacher_name)
            VALUES (%s, %s, %s)
        """, (
            class_name,
            section,
            teacher_name
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/classes")

    return render_template("add_class.html")


# =====================================================
# DELETE CLASS
# =====================================================

@app.route("/delete_class/<int:class_id>")
def delete_class(class_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM classes WHERE id = %s",
        (class_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/classes")


# =====================================================
# EDIT CLASS
# =====================================================

@app.route("/edit_class/<int:class_id>", methods=["GET", "POST"])
def edit_class(class_id):

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == "POST":

        class_name = request.form["class_name"]
        section = request.form.get("section", "")
        teacher_name = request.form.get("teacher_name", "")

        cursor.execute("""
            UPDATE classes
            SET class_name = %s,
                section = %s,
                teacher_name = %s
            WHERE id = %s
        """, (
            class_name,
            section,
            teacher_name,
            class_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/classes")

    cursor.execute(
        "SELECT * FROM classes WHERE id = %s",
        (class_id,)
    )

    class_item = cursor.fetchone()

    cursor.close()
    conn.close()

    if class_item is None:
        return "Class not found"

    return render_template(
        "edit_class.html",
        class_item=class_item
    )


# =====================================================
# STUDENTS
# =====================================================

@app.route("/students")
def students():

    search = request.args.get("search", "")

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if search:

        cursor.execute("""
            SELECT * FROM students
            WHERE name ILIKE %s
            OR roll_number ILIKE %s
            OR class_name ILIKE %s
            ORDER BY id DESC
        """, (
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        ))

    else:

        cursor.execute("""
            SELECT * FROM students
            ORDER BY id DESC
        """)

    student_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "students.html",
        students=student_list,
        search=search
    )


# =====================================================
# ADD STUDENT
# =====================================================

@app.route("/add_student", methods=["POST"])
def add_student():

    name = request.form["name"]
    roll_number = request.form["roll_number"]
    class_name = request.form["class_name"]
    section = request.form.get("section", "")
    parent_name = request.form.get("parent_name", "")
    parent_contact = request.form.get("parent_contact", "")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO students
        (name, roll_number, class_name, section,
         parent_name, parent_contact)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        name,
        roll_number,
        class_name,
        section,
        parent_name,
        parent_contact
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/students")


# =====================================================
# DELETE STUDENT
# =====================================================

@app.route("/delete_student/<int:student_id>")
def delete_student(student_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM marks WHERE student_id = %s",
        (student_id,)
    )

    cursor.execute(
        "DELETE FROM attendance WHERE student_id = %s",
        (student_id,)
    )

    cursor.execute(
        "DELETE FROM students WHERE id = %s",
        (student_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/students")


# =====================================================
# EDIT STUDENT
# =====================================================

@app.route("/edit_student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == "POST":

        name = request.form["name"]
        roll_number = request.form["roll_number"]
        class_name = request.form["class_name"]
        section = request.form.get("section", "")
        parent_name = request.form.get("parent_name", "")
        parent_contact = request.form.get("parent_contact", "")

        cursor.execute("""
            UPDATE students
            SET
                name = %s,
                roll_number = %s,
                class_name = %s,
                section = %s,
                parent_name = %s,
                parent_contact = %s
