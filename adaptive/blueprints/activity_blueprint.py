# Importing local modules and packages
from adaptive.models.entity_manager import EntityManager
from adaptive.models.subject import Subject
from adaptive.models.trajectory import Trajectory
from adaptive.models.activity import Activity
from adaptive.models.student import Student
from adaptive.models.student_answer import StudentAnswer
from adaptive.models.question import Question
from adaptive.models.text_chunk import TextChunk

# Importing native modules
from os import SEEK_END, path, makedirs, getcwd, environ
from random import random, sample
from time import time, sleep
from re import sub, UNICODE, compile, DOTALL
from unicodedata import normalize
from hashlib import sha256
from json import dump
from textwrap import dedent
from multiprocessing import Process
from threading import Thread


# Importing generic endpoints
from adaptive.blueprints.generic_blueprint import require_authentication

# Importing Flask packages and modules
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from docling.document_converter import DocumentConverter
from ftfy import fix_text
from werkzeug.utils import secure_filename
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from google import genai
from google.genai import types

activity_blueprint = Blueprint("activity_blueprint", __name__, url_prefix="/")

# Defining constants for PDF file handling
UPLOAD_DIRECTORY = path.join(getcwd(), "adaptive/assets/uploads")
ALLOWED_EXTENSIONS = {"pdf"}  # Only PDF files are allowed
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # The resulting file size should not exceed 5 MB
ACCENT_REPLACEMENTS = {
    r"\'a": "a",
    r"'a": "à",
    r"'e": "é",
    r"'i": "í",
    r"'i": "í",
    r"'o": "ó",
    r"'u": "ú",
    r"c¸ ˜a": "çã",
    r"c¸ ˜o": "çõ",
    r"c¸": "ç",
    r"˜a": "ã",
    r"˜o": "õ",
    r"ˆe": "ê",
    r"ˆa": "â",
    r"ˆo": "ô",
    r"`a": "à",
    r"`e": "è",
    r"`i": "ì",
    r"`o": "ò",
    r"`u": "ù",
    r"¨a": "ä",
    r"¨e": "ë",
    r"¨i": "ï",
    r"¨o": "ö",
    r"¨u": "ü",
    r"¸˜": "ão",
    r"¸ ˜": "ão",
    r"´a": "á",
    r"´e": "é",
    r"´i": "í",
    r"´o": "ó",
    r"´u": "ú",
    r"\'ı": "í",
    r"r\'a": "rá",
}

# Defining constants for LLM interaction
MAX_TOKENS = 800  # The maximum number of tokens per text chunk
LLM_PROVIDER = "groq"  # The Large Language Model provider (options: "groq", "gemini")


def fix_accents(text: str) -> str:
    # Replacing incorrect sequences of characters through regular expressions
    for pattern, correction in ACCENT_REPLACEMENTS.items():
        text = sub(pattern, correction, text, flags=UNICODE)

    # Normalizing the text to Unicode Normalization Form C (NFC)
    text = normalize("NFC", text)

    # Fixing remaining issues with ftfy
    text = fix_text(text)

    return text


def split_text(text: str, max_length: int) -> str:
    """This function splits a text into parts with a maximum length of tokens.

    Args:
        text (int): Text to be split.
        max_length (int): Maximum length of tokens.

    Yields:
        (str): Text parts with a maximum length of tokens.
    """
    words = text.split()
    for i in range(0, len(words), max_length):
        yield " ".join(words[i : i + max_length]).strip()


def ask_question_to_model(
    llm_provider: str, llm_caller: object, llm: str, system_prompt: str, user_prompt: str, temperature: float, show_response_metadata: bool = False
) -> dict:
    if llm_provider == "groq":
        # Defining the data structure that carries the system and user prompts.
        # The system prompt comprises pre-defined instructions for
        # the model, while the user prompt is the input from the user.
        messages = [
            SystemMessage(system_prompt),
            HumanMessage(user_prompt),
        ]

        # Calling the model to generate a response based on the system and user prompts
        response = llm_caller.invoke(messages)

        if show_response_metadata:
            return response
        else:
            return response.content

    elif llm_provider == "gemini":
        response = llm_caller.models.generate_content(
            model=llm,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
            ),
            contents=[user_prompt],
        ).text
        return response


def parse_question_body_and_answer(text):
    question_body_pattern = compile(r"<BEGIN-ENUNCIADO>\n(.*?)\n<END-ENUNCIADO>", DOTALL)
    expected_answer_pattern = compile(r"<BEGIN-RESPOSTA-ESPERADA>\n(.*?)\n<END-RESPOSTA-ESPERADA>", DOTALL)

    question_body_match = question_body_pattern.search(text)
    answer_match = expected_answer_pattern.search(text)

    body = question_body_match.group(1).strip() if question_body_match else ""
    answer = answer_match.group(1).strip() if answer_match else ""

    return {"body": body, "answer": answer}


def parse_answer_correctness_sentiment_humor_and_feedback(text):
    sentiment_options = {
        1: "Confiança",
        2: "Entusiasmo",
        3: "Insegurança",
        4: "Indiferença",
    }
    humor_options = {
        1: "Negativo",
        2: "Neutro",
        3: "Positivo",
    }

    correctness_pattern = compile(r"<BEGIN-CORRETUDE>(\d+)<END-CORRETUDE>")
    correctness_match = correctness_pattern.search(text)
    correctness = int(correctness_match.group(1)) if correctness_match else 0

    sentiment_pattern = compile(r"<BEGIN-SENTIMENTO>(\d+)<END-SENTIMENTO>")
    sentiment_match = sentiment_pattern.search(text)
    sentiment = int(sentiment_match.group(1)) if sentiment_match else 0

    humor_pattern = compile(r"<BEGIN-HUMOR>(\d+)<END-HUMOR>")
    humor_match = humor_pattern.search(text)
    humor = int(humor_match.group(1)) if humor_match else 0

    feedback_pattern = compile(r"<BEGIN-FEEDBACK>\n(.*?)\n<END-FEEDBACK>")
    feedback_match = feedback_pattern.search(text)
    feedback = feedback_match.group(1).strip() if feedback_match else ""

    return {
        "correctness": correctness if correctness in [1, 2, 3] else "",
        "sentiment": sentiment_options[sentiment] if sentiment in sentiment_options else "",
        "humor": humor_options[humor] if humor in humor_options else "",
        "feedback": feedback,
    }


def generate_question(activity_id: int, student_id: int):
    # Gathering the information about the subject, the activity, and the student
    activity = EntityManager.session().query(Activity).filter_by(id=activity_id).first()

    # Checking if the student already has a trajectory for the activity and creating one if it does not
    trajectory = EntityManager.session().query(Trajectory).filter_by(activity_id=activity_id, student_id=student_id).first()

    if not isinstance(trajectory, Trajectory):
        trajectory = Trajectory(activity_id=activity_id, student_id=student_id)

    if isinstance(trajectory, Trajectory) and trajectory.status == "completed":
        return

    # Defining the difficulty level of the question based on the student's trajectory. There are three levels of difficulty:
    # 1 - Easy, 2 - Medium, and 3 - Hard. In addition, there are three levels of correctness:
    # 1 - Incorrect, 2 - Partially Correct, and 1 - Fully Correct.
    # ================================================================================================
    # The difficulty level starts at 1. Then:
    # ==> If the student answers a question incorrectly, the difficulty level is reduced by 1.
    # ==> If the student answers a question partially correctly, the difficulty level is maintained.
    # ==> If the student answers a question fully correctly, the difficulty level is increased by 1.
    # ================================================================================================
    # Once the maximum difficulty level (3) is reached, the level is maintained until the minimum
    # number of questions is answered correctly (activity.min_questions).
    difficulty_increased = True
    if len(trajectory.questions) == 0:
        difficulty = 1
    else:
        last_answered_question = trajectory.last_answered_question
        if last_answered_question is not None:
            difficulty = int(last_answered_question.difficulty)
            if last_answered_question.student_answer.correctness == 3:
                difficulty = min(3, difficulty + 1)

    # Selecting one of the text chunks of the activity to generate a question. To provide a better experience for the student,
    # we sort the text chunks in such a way that chunks less frequently used in previous questions within the trajectory are
    # more likely to be selected to generate a new question
    # Creating a dictionary to store the number of times each text chunk was used in previous questions
    text_chunks = {text_chunk.identifier: 0 for text_chunk in activity.text_chunks}
    for question in trajectory.questions:
        text_chunks[question.text_chunk.identifier] += 1

    # Sorting the text chunks (dict keys) based on the number of times they were used in
    # previous questions (dict values) and transforming the sorted keys into a list of text chunks
    sorted_text_chunks = [
        key
        for key, value in sorted(
            text_chunks.items(),
            key=lambda item: (item[1], random()),
            reverse=difficulty_increased,
        )
    ]

    # Selecting the first text chunk of the sorted list to generate a question
    text_chunk = EntityManager.session().query(TextChunk).filter_by(identifier=sorted_text_chunks[0]).first()

    # Generating a question based on the selected text chunk using a Large Language Model. First, we define the system and user prompts.
    # The system prompt comprises pre-defined instructions for the model, while the user prompt is the input from the user.
    # We format the user prompt as an unindented multi-line string using dedent.
    user_prompt = dedent(
        f"""
        ===============================
        ==== GERE UMA NOVA QUESTÃO ====
        ===============================
        ---- Dificuldade ----
        {difficulty}

        ---- Conteúdo-Base ----
        {text_chunk.content}
        """
    )

    # Defining the foundational model for the application
    if activity.llm_provider == "groq":
        groq_api_key = sample(current_app.groq_api_keys, 1)[0]
        environ.setdefault("GROQ_API_KEY", groq_api_key)
        print(f"\n\n[Groq] Making request with API key: {groq_api_key}\n\n")
        llm_caller = ChatGroq(
            model=activity.model_name,
            temperature=round(float(activity.model_temperature), 2),
            api_key=groq_api_key,
        )
    elif activity.llm_provider == "gemini":
        gemini_api_key = sample(current_app.gemini_api_keys, 1)[0]
        print(f"\n\n[Gemini] Making request with API key: {gemini_api_key}\n\n")
        llm_caller = genai.Client(
            api_key=gemini_api_key,
        )

    # Calling the function that messages the LLM
    parsed_response = {"body": "", "answer": ""}
    trial_count = 0
    while parsed_response["body"] == "" or parsed_response["answer"] == "":
        trial_count += 1
        response = ask_question_to_model(
            llm_provider=activity.llm_provider,
            llm_caller=llm_caller,
            llm=activity.model_name,
            system_prompt=activity.model_system_prompt,
            user_prompt=user_prompt,
            temperature=activity.model_temperature,
        )
        parsed_response = parse_question_body_and_answer(text=response)

    # Creating a new question based on the response generated by the model
    Question(
        body=parsed_response["body"],
        answer=parsed_response["answer"],
        difficulty=difficulty,
        text_chunk_id=text_chunk.id,
        trajectory_id=trajectory.id,
    )

    Trajectory.update(id=trajectory.id, new_attributes={"status": "active"})


def generate_question_wrapper(activity_id, student_id):
    from adaptive import app

    with app.app_context():
        generate_question(activity_id=activity_id, student_id=student_id)


def process_pdf_and_create_questions(activity_id: object, file_path: str):
    from adaptive import app
    from adaptive.models.entity_manager import EntityManager

    with app.app_context():
        sleep(0.5)
        activity = EntityManager.session().query(Activity).filter_by(id=activity_id).first()
        if not activity:
            return

        # Processing the PDF file content
        converter = DocumentConverter()
        raw_text = converter.convert(file_path).document.export_to_text()
        text = fix_accents(raw_text)

        # Splitting the text into parts with a maximum of tokens (this value should be adjusted according to the model's requirements)
        raw_text_chunks = split_text(text, MAX_TOKENS)

        # Creating JSON file to store the text chunks and pushing the text chunks into the file
        text_chunks = []
        number_of_chunks = 0
        print("\n\nText Chunks:\n")
        for text_chunk in raw_text_chunks:
            # Generating the text chunk metadata
            number_of_chunks += 1
            identifier = sha256(f"{number_of_chunks}_{text_chunk}".encode("utf-8")).hexdigest()

            # Saving the text chunk metadata into the text_chunks list
            text_chunks.append({"identifier": identifier, "content": text_chunk})

            # Creating a TextChunk instance in the database
            TextChunk(identifier=identifier, activity_id=activity.id)
            print(f"{text_chunk}")
        print("\n\n")

        # Storing the text chunks into the JSON file
        with open(activity.text_chunks_file_path, "w", encoding="utf-8") as file:
            dump(text_chunks, file, ensure_ascii=False, indent=4)

        # Generating questions for each student in the subject
        processes = []
        activity = EntityManager.session().query(Activity).filter_by(id=activity_id).first()
        subject = EntityManager.session().query(Subject).filter_by(id=activity.subject_id).first()
        for student in subject.students:
            print(f"==== [Subject={subject.name}, Atividade={activity.id}] Criando questões para o estudante {student.name} ====")
            student_obj = EntityManager.session().query(Student).filter_by(id=student.id).first()
            proc = Process(target=generate_question_wrapper, args=(activity.id, student_obj.id))
            processes.append(proc)
            proc.start()
        for proc in processes:
            proc.join()

        # Marking the activity as completed after generating the questions for all students
        activity.creation_status = "completed"
        Activity.update(id=activity.id, new_attributes={"creation_status": "completed"})


def process_student_answer_and_advance_trajectory_wrapper(question_id: int):
    from adaptive import app

    with app.app_context():
        process_student_answer_and_advance_trajectory(question_id=question_id)


def process_student_answer_and_advance_trajectory(question_id: int):
    # Gathering the information about the subject, the activity, and the student
    question = EntityManager.session().query(Question).filter_by(id=question_id).first()
    trajectory = question.trajectory
    activity = question.trajectory.activity
    student_answer = question.student_answer

    # Generating a question based on the selected text chunk using a Large Language Model. First, we define the system and user prompts.
    # The system prompt comprises pre-defined instructions for the model, while the user prompt is the input from the user.
    # We format the user prompt as an unindented multi-line string using dedent.
    user_prompt = dedent(
        f"""
        =============================
        ==== AVALIE UMA RESPOSTA ====
        =============================
        ---- Resposta do Estudante ----
        {student_answer.content}

        ---- Resposta Esperada ----
        {question.answer}
        """
    )

    # Defining the foundational model for the application
    if activity.llm_provider == "groq":
        groq_api_key = sample(current_app.groq_api_keys, 1)[0]
        environ.setdefault("GROQ_API_KEY", groq_api_key)
        print(f"\n\n[Groq] Making request with API key: {groq_api_key}\n\n")
        llm_caller = ChatGroq(
            model=activity.model_name,
            temperature=round(float(activity.model_temperature), 2),
            api_key=groq_api_key,
        )
    elif activity.llm_provider == "gemini":
        gemini_api_key = sample(current_app.gemini_api_keys, 1)[0]
        print(f"\n\n[Gemini] Making request with API key: {gemini_api_key}\n\n")
        llm_caller = genai.Client(
            api_key=gemini_api_key,
        )

    # Calling the function that messages the LLM
    parsed_response = {"correctness": "", "sentiment": "", "humor": "", "feedback": ""}
    while parsed_response["correctness"] == "" or parsed_response["sentiment"] == "" or parsed_response["humor"] == "":
        response = ask_question_to_model(
            llm_provider=activity.llm_provider,
            llm_caller=llm_caller,
            llm=activity.model_name,
            system_prompt=activity.model_system_prompt,
            user_prompt=user_prompt,
            temperature=activity.model_temperature,
        )
        parsed_response = parse_answer_correctness_sentiment_humor_and_feedback(text=response)
        print(f"\n\nRaw Model Response:\n{response}\n\n")
        print(f"\n\nParsed Model Response:\n{parsed_response}\n\n")

    StudentAnswer.update(
        id=student_answer.id,
        new_attributes={
            "correctness": parsed_response["correctness"],
            "sentiment": parsed_response["sentiment"],
            "humor": parsed_response["humor"],
            "descriptive_feedback": parsed_response["feedback"],
        },
    )

    # Marking the trajectory as completed if the question difficulty is the maximum and the student's correctness level is the maximum and
    # the minimum number of questions was answered. Otherwise, generating a new question for the student within the trajectory based
    # on the student's performance
    if (
        question.difficulty == 3
        and parsed_response["correctness"] == 3
        and len(trajectory.questions) >= activity.min_questions
        or len(trajectory.questions) >= activity.max_questions
    ):
        Trajectory.update(id=trajectory.id, new_attributes={"status": "completed"})
    else:
        generate_question_wrapper(activity_id=activity.id, student_id=trajectory.student_id)


@activity_blueprint.route("/subjects/<int:subject_id>/activities/<int:activity_id>", methods=["GET"])
@require_authentication(user_type="teacher")
def view_activity(subject_id: int, activity_id: int):
    # Gathering the subject information
    subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()

    # Gathering the activity information
    activity = EntityManager.session().query(Activity).filter_by(id=activity_id).first()

    # Redirecting the user to the dashboard page if the subject or the activity do not exist
    if not subject or not activity:
        flash("A atividade informada na URL não existe.", "error")
        return redirect(url_for("teacher_blueprint.dashboard"))

    activity.number_of_fully_correct_answers = 0
    activity.number_of_partially_correct_answers = 0
    activity.number_of_incorrect_answers = 0
    activity.percentage_fully_correct_answers = 0
    activity.percentage_partially_correct_answers = 0
    activity.percentage_incorrect_answers = 0

    activity.answer_sentiments = {}
    activity.answer_humors = {}

    questions = []

    for trajectory in activity.trajectories:
        questions.extend(trajectory.questions)

        for index, question in enumerate(trajectory.questions):
            question.difficulty_name = "Fácil" if question.difficulty == 1 else "Médio" if question.difficulty == 2 else "Difícil"

            if question.student_answer is not None:
                # Processing information to be displayed in the trajectory list
                if index == 0:
                    question.border_radius = "8px 0px 0px 8px"
                elif index == len(trajectory.questions) - 1:
                    question.border_radius = "0px 8px 8px 0px"
                else:
                    question.border_radius = "0px 0px 0px 0px"

                if question.student_answer.correctness == 1:
                    question.bg_color = "bg-red-200"
                elif question.student_answer.correctness == 2:
                    question.bg_color = "bg-yellow-200"
                else:
                    question.bg_color = "bg-green-200"

                if question.student_answer.humor == "Negativo":
                    question.humor_image = "img/humor_negative.png"
                elif question.student_answer.humor == "Neutro":
                    question.humor_image = "img/humor_neutral.png"
                else:
                    question.humor_image = "img/humor_positive.png"

                if question.difficulty == 1:
                    question.difficulty_image = "img/difficulty1.png"
                elif question.difficulty == 2:
                    question.difficulty_image = "img/difficulty2.png"
                else:
                    question.difficulty_image = "img/difficulty3.png"

                # Processing information to be displayed in the activity graphs
                if question.student_answer.correctness == 3:
                    activity.number_of_fully_correct_answers += 1
                elif question.student_answer.correctness == 2:
                    activity.number_of_partially_correct_answers += 1
                else:
                    activity.number_of_incorrect_answers += 1

                if question.student_answer.sentiment not in activity.answer_sentiments:
                    activity.answer_sentiments[question.student_answer.sentiment] = 0
                activity.answer_sentiments[question.student_answer.sentiment] += 1

                if question.student_answer.humor not in activity.answer_humors:
                    activity.answer_humors[question.student_answer.humor] = 0
                activity.answer_humors[question.student_answer.humor] += 1

    activity.total_questions_answered = (
        activity.number_of_fully_correct_answers + activity.number_of_partially_correct_answers + activity.number_of_incorrect_answers
    )
    if activity.total_questions_answered > 0:
        activity.percentage_fully_correct_answers = round(activity.number_of_fully_correct_answers * 100 / activity.total_questions_answered, 2)
        activity.percentage_partially_correct_answers = round(activity.number_of_partially_correct_answers * 100 / activity.total_questions_answered, 2)
        activity.percentage_incorrect_answers = round(activity.number_of_incorrect_answers * 100 / activity.total_questions_answered, 2)
    else:
        activity.percentage_fully_correct_answers = 0
        activity.percentage_partially_correct_answers = 0
        activity.percentage_incorrect_answers = 0

    activity.sentiment_names = list(activity.answer_sentiments.keys())
    activity.number_of_answers_per_sentiment = list(activity.answer_sentiments.values())

    activity.humor_names = list(activity.answer_humors.keys())
    activity.number_of_answers_per_humor = list(activity.answer_humors.values())

    return render_template("view_activity.html", subject=subject, activity=activity, trajectories=activity.trajectories, questions=questions)


@activity_blueprint.route("/subjects/<int:subject_id>/activities/<int:activity_id>/remove", methods=["POST"])
@require_authentication(user_type="teacher")
def remove_activity(subject_id: int, activity_id: int):
    # Removing the activity from the database
    Activity.delete(id=activity_id)

    flash("Atividade excluída com sucesso!", "success")

    return redirect(url_for("subject_blueprint.view_subject", subject_id=subject_id))


@activity_blueprint.route("/subjects/<int:subject_id>/activities/new", methods=["GET"])
@require_authentication(user_type="teacher")
def new_activity(subject_id: int):
    subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()
    return render_template("new_activity.html", subject=subject)


@activity_blueprint.route("/subjects/<int:subject_id>/activities/new", methods=["POST"])
@require_authentication(user_type="teacher")
def create_activity(subject_id: int):
    # Gathering the subject information
    subject = EntityManager.session().query(Subject).filter_by(id=subject_id).first()

    # Creating an activity instance based on the form data
    base_material = request.files["activity_base_material"]
    min_questions = int(request.form["activity_min_questions"])
    max_questions = int(request.form["activity_max_questions"])

    llm_provider = request.form["activity_model_name"].split("] ")[0].replace("[", "")
    model_name = request.form["activity_model_name"].split("] ")[1]
    model_temperature = float(request.form["activity_model_temperature"])
    model_system_prompt = request.form["activity_model_system_prompt"]

    # Triggering an error message if the base material is not a PDF file
    if not ("." in base_material.filename and base_material.filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS):
        flash("Apenas arquivos PDF são permitidos.", "error")
        return redirect(request.url)

    # Verifying if the file size is within the allowed limits
    base_material.seek(0, SEEK_END)
    file_length = base_material.tell()
    base_material.seek(0)
    if file_length > MAX_CONTENT_LENGTH:
        flash(f"O arquivo excede o tamanho máximo de {MAX_CONTENT_LENGTH / 1024 / 1024}MB.", "error")
        return redirect(request.url)

    # Building the PDF file name based on a combination of the current timestamp and the original file name
    timestamp = str(time()).replace(".", "")
    secure_name = secure_filename(base_material.filename)
    new_filename = f"{timestamp}_{secure_name}"

    # Saving the PDF file
    makedirs(UPLOAD_DIRECTORY, exist_ok=True)  # Criar o diretório se não existir
    file_path = path.join(UPLOAD_DIRECTORY, new_filename)
    base_material.save(file_path)

    # Defining the name of the JSON file that will store the activity text chunks
    text_chunk_file_name = f"{timestamp}_text_chunks.json"
    text_chunks_file_path = path.join(UPLOAD_DIRECTORY, text_chunk_file_name)

    # Creating the activity instance
    activity = Activity(
        base_material=new_filename,
        min_questions=min_questions,
        max_questions=max_questions,
        llm_provider=llm_provider,
        model_name=model_name,
        model_temperature=model_temperature,
        model_system_prompt=model_system_prompt,
        subject_id=subject_id,
        text_chunks_file_path=text_chunks_file_path,
    )
    Thread(target=process_pdf_and_create_questions, args=(activity.id, file_path)).start()

    flash("Atividade criada com sucesso! As questões estão sendo geradas e estarão disponíveis em breve.", "success")
    return redirect(url_for("activity_blueprint.view_activity", subject_id=subject.id, activity_id=activity.id))


@activity_blueprint.route("/questions/<int:question_id>/analyze", methods=["POST"])
@require_authentication()
def analyze_answer(question_id: int):
    # Gathering the information about the subject, the activity, and the student
    question = EntityManager.session().query(Question).filter_by(id=question_id).first()
    trajectory = question.trajectory

    Trajectory.update(id=trajectory.id, new_attributes={"status": "generating_question"})

    StudentAnswer(
        content=request.form["question_answer"],
        correctness=0,
        sentiment="",
        humor="",
        question_id=question.id,
        descriptive_feedback="",
    )

    Thread(target=process_student_answer_and_advance_trajectory_wrapper, args=(question.id,)).start()

    flash("Sua resposta está sendo avaliada! Em breve você receberá uma nova questão ou a atividade será finalizada.", "success")
    return redirect(url_for("student_blueprint.view_active_trajectories"))
