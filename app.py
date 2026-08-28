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
            WHERE id = %s
        """, (
            name,
            roll_number,
            class_name,
            section,
            parent_name,
            parent_contact,
            student_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/students")

    cursor.execute(
        "SELECT * FROM students WHERE id = %s",
        (student_id,)
    )

    student = cursor.fetchone()

    cursor.close()
    conn.close()

    if student is None:
        return "Student not found"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Student</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>

    <body>

        <div class="header">
            <h1>✏️ Edit Student</h1>
        </div>

        <div class="container">

            <div class="form-box">

                <form method="POST">

                    <input
                        name="name"
                        value="{student['name']}"
                        placeholder="Student Name"
                        required
                    >

                    <input
                        name="roll_number"
                        value="{student['roll_number']}"
                        placeholder="Roll Number"
                        required
                    >

                    <input
                        name="class_name"
                        value="{student['class_name']}"
                        placeholder="Class"
                        required
                    >

                    <input
                        name="section"
                        value="{student['section'] or ''}"
                        placeholder="Section"
                    >

                    <input
                        name="parent_name"
                        value="{student['parent_name'] or ''}"
                        placeholder="Parent Name"
                    >

                    <input
                        name="parent_contact"
                        value="{student['parent_contact'] or ''}"
                        placeholder="Parent Contact"
                    >

                    <br><br>

                    <button type="submit">
                        Update Student
                    </button>

                </form>

                <br>

                <a href="/students">
                    ← Back to Students
                </a>

            </div>

        </div>

    </body>
    </html>
    """


# =====================================================
# TEACHERS
# =====================================================

@app.route("/teachers")
def teachers():

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT * FROM teachers
        ORDER BY id DESC
    """)

    teachers_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "teachers.html",
        teachers=teachers_list
    )


# =====================================================
# ADD TEACHER
# =====================================================

@app.route("/add_teacher", methods=["POST"])
def add_teacher():

    name = request.form["name"]
    teacher_id = request.form["teacher_id"]
    subject = request.form["subject"]
    class_name = request.form["class_name"]
    phone = request.form.get("phone", "")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO teachers
        (name, teacher_id, subject, class_name, phone)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        name,
        teacher_id,
        subject,
        class_name,
        phone
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/teachers")


# =====================================================
# DELETE TEACHER
# =====================================================

@app.route("/delete_teacher/<int:teacher_id>")
def delete_teacher(teacher_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM teachers WHERE id = %s",
        (teacher_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/teachers")


# =====================================================
# EDIT TEACHER
# =====================================================

@app.route("/edit_teacher/<int:teacher_id>", methods=["GET", "POST"])
def edit_teacher(teacher_id):

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == "POST":

        name = request.form["name"]
        teacher_code = request.form["teacher_id"]
        subject = request.form["subject"]
        class_name = request.form["class_name"]
        phone = request.form.get("phone", "")

        cursor.execute("""
            UPDATE teachers
            SET
                name = %s,
                teacher_id = %s,
                subject = %s,
                class_name = %s,
                phone = %s
            WHERE id = %s
        """, (
            name,
            teacher_code,
            subject,
            class_name,
            phone,
            teacher_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/teachers")

    cursor.execute("""
        SELECT * FROM teachers
        WHERE id = %s
    """, (teacher_id,))

    teacher = cursor.fetchone()

    cursor.close()
    conn.close()

    if teacher is None:
        return "Teacher not found"

    return render_template(
        "edit_teacher.html",
        teacher=teacher
    )
# =====================================================
# MARKS / RESULTS
# =====================================================

@app.route("/marks")
def marks():

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT * FROM students
        ORDER BY class_name, roll_number
    """)

    students_list = cursor.fetchall()

    cursor.execute("""
        SELECT
            marks.id,
            marks.subject,
            marks.marks_obtained,
            marks.total_marks,
            students.name,
            students.roll_number,
            students.class_name
        FROM marks
        JOIN students
        ON marks.student_id = students.id
        ORDER BY marks.id DESC
    """)

    marks_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "marks.html",
        students=students_list,
        marks=marks_list
    )


# =====================================================
# ADD MARKS
# =====================================================

@app.route("/add_marks", methods=["POST"])
def add_marks():

    student_id = request.form["student_id"]
    subject = request.form["subject"]
    marks_obtained = float(request.form["marks_obtained"])
    total_marks = float(request.form["total_marks"])

    if total_marks <= 0:
        return "Total marks must be greater than 0"

    if marks_obtained < 0 or marks_obtained > total_marks:
        return "Obtained marks must be between 0 and total marks"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO marks
        (student_id, subject, marks_obtained, total_marks)
        VALUES (%s, %s, %s, %s)
    """, (
        student_id,
        subject,
        marks_obtained,
        total_marks
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/marks")


# =====================================================
# DELETE MARKS
# =====================================================

@app.route("/delete_marks/<int:mark_id>")
def delete_marks(mark_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM marks WHERE id = %s",
        (mark_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/marks")


# =====================================================
# STUDENT RESULT
# =====================================================

@app.route("/result/<int:student_id>")
def result(student_id):

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT * FROM students
        WHERE id = %s
    """, (student_id,))

    student = cursor.fetchone()

    if student is None:
        cursor.close()
        conn.close()
        return "Student not found"

    cursor.execute("""
        SELECT *
        FROM marks
        WHERE student_id = %s
        ORDER BY id
    """, (student_id,))

    marks_list = cursor.fetchall()

    cursor.close()
    conn.close()

    total_obtained = sum(
        mark["marks_obtained"]
        for mark in marks_list
    )

    total_marks = sum(
        mark["total_marks"]
        for mark in marks_list
    )

    if total_marks > 0:
        percentage = round(
            (total_obtained / total_marks) * 100,
            2
        )
    else:
        percentage = 0

    if percentage >= 80:
        grade = "A+"
    elif percentage >= 70:
        grade = "A"
    elif percentage >= 60:
        grade = "B"
    elif percentage >= 50:
        grade = "C"
    elif percentage >= 40:
        grade = "D"
    else:
        grade = "F"

    result_status = "Pass" if percentage >= 40 else "Fail"

    return render_template(
        "result.html",
        student=student,
        marks=marks_list,
        total_obtained=total_obtained,
        total_marks=total_marks,
        percentage=percentage,
        grade=grade,
        result_status=result_status
    )


# =====================================================
# ATTENDANCE
# =====================================================

@app.route("/attendance")
def attendance():

    selected_date = request.args.get(
        "date",
        date.today().isoformat()
    )

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT * FROM students
        ORDER BY class_name, roll_number
    """)

    students_list = cursor.fetchall()

    cursor.execute("""
        SELECT student_id, status
        FROM attendance
        WHERE attendance_date = %s
    """, (selected_date,))

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    attendance_data = {
        row["student_id"]: row["status"]
        for row in records
    }

    return render_template(
        "attendance.html",
        students=students_list,
        selected_date=selected_date,
        attendance=attendance_data
    )


# =====================================================
# SAVE ATTENDANCE
# =====================================================

@app.route("/save_attendance", methods=["POST"])
def save_attendance():

    attendance_date = request.form["attendance_date"]

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT id FROM students"
    )

    students_list = cursor.fetchall()

    for student in students_list:

        student_id = student["id"]

        status = request.form.get(
            f"status_{student_id}",
            "Present"
        )

        cursor.execute("""
            INSERT INTO attendance
            (student_id, attendance_date, status)
            VALUES (%s, %s, %s)

            ON CONFLICT(student_id, attendance_date)
            DO UPDATE SET status = EXCLUDED.status
        """, (
            student_id,
            attendance_date,
            status
        ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(
        f"/attendance?date={attendance_date}"
    )


# =====================================================
# ATTENDANCE REPORT
# =====================================================

@app.route("/report")
def report():

    search = request.args.get("search", "")

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if search:

        cursor.execute("""
            SELECT * FROM students
            WHERE name ILIKE %s
            OR roll_number ILIKE %s
            ORDER BY class_name, roll_number
        """, (
            "%" + search + "%",
            "%" + search + "%"
        ))

    else:

        cursor.execute("""
            SELECT * FROM students
            ORDER BY class_name, roll_number
        """)

    students_list = cursor.fetchall()

    reports = []

    for student in students_list:

        cursor.execute("""
            SELECT status
            FROM attendance
            WHERE student_id = %s
        """, (student["id"],))

        records = cursor.fetchall()

        total_days = len(records)

        present = sum(
            1 for r in records
            if r["status"] == "Present"
        )

        absent = sum(
            1 for r in records
            if r["status"] == "Absent"
        )

        leave = sum(
            1 for r in records
            if r["status"] == "Leave"
        )

        if total_days > 0:
            percentage = round(
                (present / total_days) * 100,
                2
            )
        else:
            percentage = 0

        reports.append({
            "name": student["name"],
            "roll_number": student["roll_number"],
            "class_name": student["class_name"],
            "total_days": total_days,
            "present": present,
            "absent": absent,
            "leave": leave,
            "percentage": percentage
        })

    cursor.close()
    conn.close()

    return render_template(
        "report.html",
        reports=reports,
        search=search
    )


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)
