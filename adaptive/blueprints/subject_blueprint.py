# Importing local modules and packages
from adaptive.models.entity_manager import EntityManager
from adaptive.models.subject import Subject
from adaptive.models.student_answer import StudentAnswer
from adaptive.models.question import Question
from adaptive.models.trajectory import Trajectory
from adaptive.models.activity import Activity
from adaptive.models.subject_student import SubjectStudent
from adaptive.models.student import Student
from adaptive.models.teacher import Teacher

# Importing native modules
from multiprocessing import Process

# Importing generic endpoints
from adaptive.blueprints.generic_blueprint import require_authentication
from adaptive.blueprints.activity_blueprint import generate_question_wrapper

# Importing Flask packages and modules
from flask import Blueprint, render_template, redirect, url_for, session, request, flash

subject_blueprint = Blueprint("subject_blueprint", __name__, url_prefix="/")


@subject_blueprint.route("/subjects/<int:subject_id>", methods=["GET"])
@require_authentication(user_type="teacher")
def view_subject(subject_id: int):
    # Gathering the subject information
    subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()

    # Redirecting the user to the dashboard page if the subject does not exist
    if not subject:
        flash("Disciplina não encontrada", "error")
        return redirect(url_for("teacher_blueprint.dashboard"))

    return render_template("view_subject.html", subject=subject)


@subject_blueprint.route("/subjects/<int:subject_id>", methods=["POST"])
@require_authentication(user_type="teacher")
def remove_subject(subject_id: int):
    # Removing the subject from the database
    Subject.delete(id=subject_id)

    flash("Disciplina excluída com sucesso", "success")

    return redirect(url_for("teacher_blueprint.dashboard"))


@subject_blueprint.route("/subjects/new", methods=["GET", "POST"])
@require_authentication(user_type="teacher")
def new_subject():
    return render_template("new_subject.html")


@subject_blueprint.route("/subjects/create", methods=["POST"])
@require_authentication(user_type="teacher")
def create_subject():
    # Creating a subject instance based on the form data
    name = request.form["subject_name"]
    subject = Subject(name=name, teacher_id=session["teacher_id"])
    flash("Disciplina criada com sucesso", "success")
    return redirect(url_for("subject_blueprint.view_subject", subject_id=subject.id))


@subject_blueprint.route("/subjects/<int:subject_id>/students/register", methods=["GET"])
@require_authentication(user_type="teacher")
def new_subject_student(subject_id: int):
    subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()
    teacher = EntityManager.session().query(Teacher).get(session["teacher_id"])
    students = EntityManager.session().query(Student).filter(Student.organization_id == teacher.organization_id).all()

    return render_template("register_students_to_subject.html", subject=subject, students=students)


def remove_student_from_subject(student_id: int, subject_id: int):
    student = EntityManager.session().query(Student).filter_by(id=student_id).first()
    subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()

    subject_activities_ids = [activity.id for activity in EntityManager.session().query(Activity).filter_by(subject_id=subject.id).all()]
    subject_student = EntityManager.session().query(SubjectStudent).filter_by(student_id=student.id, subject_id=subject.id).first()

    if subject_student is not None:
        for trajectory in student.trajectories:
            if trajectory.activity_id in subject_activities_ids:
                trajectory = EntityManager.session().query(Trajectory).filter_by(id=trajectory.id).first()
                for question in trajectory.questions:
                    question = EntityManager.session().query(Question).filter_by(id=question.id).first()
                    if question.student_answer is not None:
                        student_answer = EntityManager.session().query(StudentAnswer).filter_by(id=question.student_answer.id).first()
                        StudentAnswer.delete(id=student_answer.id)
                    Question.delete(id=question.id)
                Trajectory.delete(id=trajectory.id)
        SubjectStudent.delete(id=subject_student.id)


@subject_blueprint.route("/subjects/<int:subject_id>/students/register", methods=["POST"])
@require_authentication(user_type="teacher")
def create_subject_student(subject_id: int):
    subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()

    # Gathering the IDs of the students that are supposed to be registered to the subject from the form data
    students_ids_to_register = [int(student_id) for student_id in request.form.getlist("students_to_register")]

    # Building lists of students that are supposed to be registered and not supposed to be registered to the subject
    teacher = EntityManager.session().query(Teacher).get(session["teacher_id"])
    all_students = EntityManager.session().query(Student).filter(Student.organization_id == teacher.organization_id).all()
    students_to_register = []
    students_not_to_register = []

    for student in all_students:
        if student.id in students_ids_to_register:
            students_to_register.append(student)
        else:
            students_not_to_register.append(student)

    # Removing the students that are not supposed to be registered to the subject
    for student in students_not_to_register:
        student = EntityManager.session().query(Student).filter_by(id=student.id).first()
        subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()
        remove_student_from_subject(student_id=student.id, subject_id=subject.id)

    # Registering the students that are supposed to attend the subject
    for student in students_to_register:
        student = EntityManager.session().query(Student).filter_by(id=student.id).first()
        subject_student = EntityManager.session().query(SubjectStudent).filter_by(student_id=student.id, subject_id=subject.id).first()
        if subject_student is None:
            subject_student = SubjectStudent(student_id=student.id, subject_id=subject.id)

            for activity in subject.activities:
                print(f"[Subject '{subject.name}'] Criando trajetória para a atividade {activity.id} do aluno {student.name}")
                proc = Process(target=generate_question_wrapper, args=(activity.id, student.id))
                proc.start()

    flash("Lista de alunos(as) da disciplina atualizada com sucesso!", "success")
    subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()
    return redirect(url_for("subject_blueprint.view_subject", subject_id=subject.id))


@subject_blueprint.route("/subjects/<int:subject_id>/students/<int:student_id>/unregister", methods=["POST"])
@require_authentication(user_type="teacher")
def remove_subject_student(subject_id: int, student_id: int):
    subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()
    student = EntityManager.session().query(Student).filter_by(id=student_id).first()
    remove_student_from_subject(student_id=student.id, subject_id=subject.id)
    flash("Aluno(a) removido(a) da disciplina com sucesso!", "success")
    return redirect(url_for("subject_blueprint.view_subject", subject_id=subject.id))


@subject_blueprint.route("/subjects/<int:subject_id>/activities/new", methods=["GET"])
@require_authentication(user_type="teacher")
def new_activity(subject_id: int):
    subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()
    return render_template("new_activity.html", subject=subject)


@subject_blueprint.route("/subjects/<int:subject_id>/students/<int:student_id>", methods=["GET"])
@require_authentication(user_type="teacher")
def view_student_progress(subject_id: int, student_id: int):
    subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()
    student = EntityManager.session().query(Student).filter_by(id=student_id).first()

    subject_activities_ids = [activity.id for activity in EntityManager.session().query(Activity).filter_by(subject_id=subject.id).all()]

    student.total_questions_answered = 0
    student.number_of_fully_correct_answers = 0
    student.number_of_partially_correct_answers = 0
    student.number_of_incorrect_answers = 0
    student.percentage_fully_correct_answers = 0
    student.percentage_partially_correct_answers = 0
    student.percentage_incorrect_answers = 0
    student.answer_sentiments = {}
    student.answer_humors = {}
    student.humor_names = []
    student.sentiment_names = []
    student.number_of_answers_per_sentiment = []
    student.number_of_answers_per_humor = []

    trajectories = []
    subject_trajectories = 0
    for trajectory in student.trajectories:
        trajectory.questions_answered = 0
        trajectory.fully_correct_answers = 0
        trajectory.partially_correct_answers = 0
        trajectory.incorrect_answers = 0

        if trajectory.activity_id in subject_activities_ids:
            subject_trajectories += 1

            for question in trajectory.questions:
                if question.student_answer is not None:
                    trajectory.questions_answered += 1

                    if question.student_answer.correctness == 3:
                        trajectory.fully_correct_answers += 1
                        student.number_of_fully_correct_answers += 1
                    elif question.student_answer.correctness == 2:
                        trajectory.partially_correct_answers += 1
                        student.number_of_partially_correct_answers += 1
                    else:
                        trajectory.incorrect_answers += 1
                        student.number_of_incorrect_answers += 1

                    if question.student_answer.sentiment not in student.answer_sentiments:
                        student.answer_sentiments[question.student_answer.sentiment] = 0
                    student.answer_sentiments[question.student_answer.sentiment] += 1

                    if question.student_answer.humor not in student.answer_humors:
                        student.answer_humors[question.student_answer.humor] = 0
                    student.answer_humors[question.student_answer.humor] += 1

            # Calculating the percentage values of the trajectory
            if trajectory.questions_answered > 0:
                trajectory.percentage_fully_correct_answers = round((trajectory.fully_correct_answers / trajectory.questions_answered) * 100, 2)
                trajectory.percentage_partially_correct_answers = round((trajectory.partially_correct_answers / trajectory.questions_answered) * 100, 2)
                trajectory.percentage_incorrect_answers = round((trajectory.incorrect_answers / trajectory.questions_answered) * 100, 2)

                student.percentage_fully_correct_answers += trajectory.percentage_fully_correct_answers
                student.percentage_partially_correct_answers += trajectory.percentage_partially_correct_answers
                student.percentage_incorrect_answers += trajectory.percentage_incorrect_answers
            else:
                trajectory.percentage_fully_correct_answers = 0
                trajectory.percentage_partially_correct_answers = 0
                trajectory.percentage_incorrect_answers = 0

                student.percentage_fully_correct_answers = 0
                student.percentage_partially_correct_answers = 0
                student.percentage_incorrect_answers = 0

            trajectories.append(trajectory)

    student.total_questions_answered = (
        student.number_of_fully_correct_answers + student.number_of_partially_correct_answers + student.number_of_incorrect_answers
    )
    if student.total_questions_answered > 0:
        student.percentage_fully_correct_answers = round(student.percentage_fully_correct_answers / student.total_questions_answered, 2)
        student.percentage_partially_correct_answers = round(student.percentage_partially_correct_answers / student.total_questions_answered, 2)
        student.percentage_incorrect_answers = round(student.percentage_incorrect_answers / student.total_questions_answered, 2)
    else:
        student.percentage_fully_correct_answers = 0
        student.percentage_partially_correct_answers = 0
        student.percentage_incorrect_answers = 0

    student.sentiment_names = list(student.answer_sentiments.keys())
    student.number_of_answers_per_sentiment = list(student.answer_sentiments.values())

    student.humor_names = list(student.answer_humors.keys())
    student.number_of_answers_per_humor = list(student.answer_humors.values())

    return render_template("view_student_progress_in_subject.html", subject=subject, student=student, trajectories=trajectories)
