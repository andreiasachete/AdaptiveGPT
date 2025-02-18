# Importing local modules and packages
from adaptive.models.entity_manager import EntityManager
from adaptive.models.student import Student

# Importing generic endpoints
from adaptive.blueprints.generic_blueprint import require_authentication

# Importing Flask packages and modules
from flask import Blueprint, render_template, session

student_blueprint = Blueprint("student_blueprint", __name__, url_prefix="/")


@student_blueprint.route("/student_dashboard", methods=["GET"])
@require_authentication(user_type="student")
def dashboard():
    # Gathering the student logged in
    student = EntityManager.session().query(Student).filter_by(id=session["student_id"]).first()

    student.number_of_fully_correct_answers = 0
    student.number_of_partially_correct_answers = 0
    student.number_of_incorrect_answers = 0
    student.percentage_fully_correct_answers = 0
    student.percentage_partially_correct_answers = 0
    student.percentage_incorrect_answers = 0

    student.answer_sentiments = {}
    student.answer_humors = {}

    for trajectory in student.trajectories:
        trajectory.questions_answered = 0
        trajectory.fully_correct_answers = 0
        trajectory.partially_correct_answers = 0
        trajectory.incorrect_answers = 0

        for question in trajectory.questions:
            if question.student_answer is not None:
                trajectory.questions_answered += 1

                if question.student_answer.correctness == 1:
                    trajectory.fully_correct_answers += 1
                    student.number_of_fully_correct_answers += 1
                elif question.student_answer.correctness == 0.5:
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

    return render_template("student_dashboard.html", student=student, subjects=student.subjects, trajectories=student.trajectories)


@student_blueprint.route("/trajectories/active", methods=["GET"])
@require_authentication(user_type="student")
def view_active_trajectories():
    # Gathering the student logged in
    student = EntityManager.session().query(Student).filter_by(id=session["student_id"]).first()

    active_trajectories = []
    for trajectory in student.trajectories:
        if trajectory.status == "active":
            active_trajectories.append(trajectory)

    return render_template("view_active_trajectories.html", student=student, active_trajectories=active_trajectories)
