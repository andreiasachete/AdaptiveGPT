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
            trajectory.percentage_fully_correct_answers = round((trajectory.fully_correct_answers * 100 / trajectory.questions_answered), 2)
            trajectory.percentage_partially_correct_answers = round((trajectory.partially_correct_answers * 100 / trajectory.questions_answered), 2)
            trajectory.percentage_incorrect_answers = round((trajectory.incorrect_answers * 100 / trajectory.questions_answered), 2)
        else:
            trajectory.percentage_fully_correct_answers = 0
            trajectory.percentage_partially_correct_answers = 0
            trajectory.percentage_incorrect_answers = 0

    student.total_questions_answered = (
        student.number_of_fully_correct_answers + student.number_of_partially_correct_answers + student.number_of_incorrect_answers
    )
    if student.total_questions_answered > 0:
        student.percentage_fully_correct_answers = round(student.number_of_fully_correct_answers * 100 / student.total_questions_answered, 2)
        student.percentage_partially_correct_answers = round(student.number_of_partially_correct_answers * 100 / student.total_questions_answered, 2)
        student.percentage_incorrect_answers = round(student.number_of_incorrect_answers * 100 / student.total_questions_answered, 2)
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
    active_trajectories_with_questions_being_generated = 0
    active_trajectories_with_no_pending_questions = 0
    for trajectory in student.trajectories:
        trajectory.questions_answered_by_student = len([question for question in trajectory.questions if question.student_answer is not None])

        if trajectory.status != "completed" and trajectory.questions_answered_by_student == trajectory.activity.max_questions:
            active_trajectories_with_no_pending_questions += 1

        if trajectory.status == "generating_question" and trajectory.questions_answered_by_student < trajectory.activity.max_questions:
            active_trajectories_with_questions_being_generated += 1

        if trajectory.activity.creation_status == "completed" and trajectory.status != "completed":
            active_trajectories.append(trajectory)

    return render_template(
        "view_active_trajectories.html",
        student=student,
        active_trajectories=active_trajectories,
        active_trajectories_with_questions_being_generated=active_trajectories_with_questions_being_generated,
        active_trajectories_with_no_pending_questions=active_trajectories_with_no_pending_questions,
    )
