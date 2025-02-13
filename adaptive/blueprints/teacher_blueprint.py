# Importing local modules and packages
from adaptive.models.entity_manager import EntityManager
from adaptive.models.subject import Subject
from adaptive.models.student import Student
from adaptive.models.teacher import Teacher
from adaptive.models.student_answer import StudentAnswer
from adaptive.models.question import Question
from adaptive.models.trajectory import Trajectory
from adaptive.models.subject_student import SubjectStudent
from adaptive.models.organization import Organization

# Importing built-in modules
from os import path, getcwd

# Importing generic endpoints
from adaptive.blueprints.generic_blueprint import require_authentication, redirect_if_logged_in, parse_email_template, send_email

# Importing Flask packages and modules
from flask import Blueprint, render_template, redirect, url_for, session, request, flash, current_app

teacher_blueprint = Blueprint("teacher_blueprint", __name__, url_prefix="/")


@teacher_blueprint.route("/teacher_dashboard", methods=["GET"])
@require_authentication(user_type="teacher")
def dashboard():
    # Gathering all subjects that belong to the teacher in the session
    subjects = EntityManager.session.query(Subject).filter(Subject.teacher_id == session["teacher_id"]).all()

    return render_template("teacher_dashboard.html", subjects=subjects)


@teacher_blueprint.route("/sign_up", methods=["GET"])
@redirect_if_logged_in
def sign_up():
    organizations = EntityManager.session.query(Organization).all()
    return render_template("sign_up.html", organizations=organizations)


@teacher_blueprint.route("/teachers/create", methods=["POST"])
@redirect_if_logged_in
def create_teacher():
    # Creating a teacher instance based on the form data
    name = request.form["teacher_name"]
    email = request.form["teacher_email"]
    password = request.form["teacher_password"]
    organization = EntityManager.session.query(Organization).filter_by(id=request.form["teacher_organization"]).first()
    teacher = Teacher(name=name, email=email, password=password, organization_id=organization.id)
    session["teacher_id"] = teacher.id

    if organization.administrator is None:
        organization.administrator = teacher
        try:
            EntityManager.session.commit()
        except Exception:
            EntityManager.session.rollback()

    flash(f"Bem-vindo(a), {teacher.name}", "success")
    return redirect(url_for("teacher_blueprint.dashboard"))


@teacher_blueprint.route("/organizations/create", methods=["POST"])
@redirect_if_logged_in
def create_organization():
    # Creating an organization instance based on the form data
    name = request.form["organization_name"]
    Organization(name=name)

    flash("Organização criada com sucesso!", "success")
    return redirect(url_for("teacher_blueprint.sign_up"))


@teacher_blueprint.route("/view_students", methods=["GET"])
@require_authentication(user_type="teacher")
def view_students():
    # Gathering all students that belong to the teacher's organization
    teacher = EntityManager.session.query(Teacher).get(session["teacher_id"])
    students = EntityManager.session.query(Student).filter(Student.organization_id == teacher.organization_id).all()

    return render_template("view_students.html", students=students)


@teacher_blueprint.route("/students/new", methods=["GET"])
@require_authentication(user_type="teacher")
def new_student():
    return render_template("new_student.html")


@teacher_blueprint.route("/students/create", methods=["POST"])
@require_authentication(user_type="teacher")
def create_student():
    # Creating a student instance based on the form data
    name = request.form["student_name"]
    email = request.form["student_email"]
    password = request.form["student_password"]
    organization_id = EntityManager.session.query(Teacher).get(session["teacher_id"]).organization_id
    Student(name=name, email=email, password=password, organization_id=organization_id)

    # Parsing the email body template
    mail_path = path.join(getcwd(), "adaptive/assets/mail")
    email_content = parse_email_template(template_file=f"{mail_path}/template_welcome_student.txt")

    # Composing the email content with dynamic variables
    email_subject = email_content["subject"]
    email_body = email_content["body"].format(user_name=name, user_email=email, user_password=password)

    send_email(
        gmail_address=current_app.gmail_address,
        gmail_password=current_app.gmail_password,
        sender_address=current_app.sender_address,
        recipient_address=email,
        carbon_copy_addresses=current_app.carbon_copy_addresses,
        mail_body=email_body,
        mail_subject=email_subject,
    )

    flash("Estudante criado com sucesso!", "success")
    return redirect(url_for("teacher_blueprint.view_students"))


@teacher_blueprint.route("/students/<int:student_id>/edit", methods=["GET"])
@require_authentication(user_type="teacher")
def edit_student(student_id: int):
    # Gathering the student information
    student = EntityManager.session.query(Student).filter_by(id=student_id).first()

    # Redirecting the user to the student page if the student does not exist
    if student is None:
        flash("Estudante não encontrado!", "warning")
        return redirect(url_for("teacher_blueprint.view_students"))

    return render_template("edit_student.html", student=student)


@teacher_blueprint.route("/students/<int:student_id>", methods=["POST"])
@require_authentication(user_type="teacher")
def remove_student(student_id: int):
    # Removing the entities that are related to the student
    student = EntityManager.session.query(Student).filter_by(id=student_id).first()

    # StudentAnswer
    for trajectory in student.trajectories:
        for question in trajectory.questions:
            StudentAnswer.delete(id=question.student_answer.id)

    # Question
    for trajectory in student.trajectories:
        for question in trajectory.questions:
            Question.delete(id=question.id)

    # Trajectory
    for trajectory in student.trajectories:
        Trajectory.delete(id=trajectory.id)

    # SubjectStudent
    for subject_student in student.subjects_students:
        SubjectStudent.delete(id=subject_student.id)

    # Removing the student from the database
    Student.delete(id=student.id)
    flash("Estudante excluído com sucesso!", "success")
    return redirect(url_for("teacher_blueprint.view_students"))


@teacher_blueprint.route("/students/<int:student_id>/edit", methods=["POST"])
@require_authentication(user_type="teacher")
def update_student(student_id: int):
    # Updating the student account information based on the form data (student_name, student_email, student_password)
    student = EntityManager.session.query(Student).get(student_id)
    new_attributes = {
        "name": request.form["student_name"],
        "email": request.form["student_email"],
        "password": request.form["student_password"],
    }
    Student.update(id=student.id, new_attributes=new_attributes)

    flash("Informações atualizadas com sucesso!", "success")
    return redirect(url_for("teacher_blueprint.view_students"))
