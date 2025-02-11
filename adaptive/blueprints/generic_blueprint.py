# Importing local modules and packages
from adaptive.models.entity_manager import EntityManager
from adaptive.models.teacher import Teacher
from adaptive.models.student import Student

# Importing Flask packages and modules
from flask import Blueprint, request, render_template, redirect, url_for, session, flash, current_app

# Importing the mailer libraries
import smtplib
from email.message import EmailMessage
from itsdangerous import URLSafeTimedSerializer

# Importing native Python modules
from os import path, getcwd
from functools import wraps

generic_blueprint = Blueprint("generic_blueprint", __name__, url_prefix="/")


def require_authentication(user_type=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if user_type == "teacher":
                if "teacher_id" not in session:
                    flash("Você precisa estar logado como professor para acessar esta página.", "warning")
                    return redirect(url_for("generic_blueprint.index"))

            elif user_type == "student":
                if "student_id" not in session:
                    flash("Você precisa estar logado como estudante para acessar esta página.", "warning")
                    return redirect(url_for("generic_blueprint.index"))

            else:
                # Verifica se qualquer tipo de usuário está autenticado
                if "teacher_id" not in session and "student_id" not in session:
                    flash("Por favor, faça login para acessar esta página.", "warning")
                    return redirect(url_for("generic_blueprint.index"))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def redirect_if_logged_in(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "teacher_id" in session:
            flash("Você já está logado como professor, enquanto essa página só é acessível para usuários não autenticados.", "warning")
            return redirect(url_for("teacher_blueprint.dashboard"))
        elif "student_id" in session:
            flash("Você já está logado como estudante, enquanto essa página só é acessível para usuários não autenticados.", "warning")
            return redirect(url_for("student_blueprint.dashboard"))
        return func(*args, **kwargs)

    return wrapper


def parse_email_template(template_file):
    # Reading a text file with the email template
    with open(template_file, "r") as file:
        email_template = file.read()

    # Separating the email subject and body (the first line is the subject and the rest is the body)
    email_template = email_template.split("\n", 1)
    email_subject = email_template[0].split("====> TÍTULO: ")[1]
    email_body = email_template[1]

    # Building a dictionary with the parsed email content
    parsed_email = {
        "subject": email_subject,
        "body": email_body,
    }

    return parsed_email


def send_email(gmail_address, gmail_password, sender_address, recipient_address, carbon_copy_addresses, mail_body, mail_subject):
    # Create the email message
    msg = EmailMessage()
    msg["Subject"] = mail_subject
    msg["From"] = sender_address
    msg["To"] = recipient_address
    msg["Cc"] = ", ".join(carbon_copy_addresses)

    msg.set_content(mail_body)

    # Send the email via SMTP server
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_address, gmail_password)
        smtp.send_message(msg)


def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.secret_key)
    return serializer.dumps(email, salt="password-reset-salt")


def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.secret_key)
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=expiration)
    except Exception:
        return None
    return email


@generic_blueprint.route("/", methods=["GET"])
@redirect_if_logged_in
def index():
    return render_template("index.html")


@generic_blueprint.route("/sign_in", methods=["GET"])
@redirect_if_logged_in
def sign_in():
    return render_template("sign_in.html")


@generic_blueprint.route("/authenticate", methods=["POST"])
def authenticate():
    """Authentication route."""
    # Gathering the form data
    email = request.form["email"]
    password = request.form["password"]

    # Trying to find the teacher in the database
    teacher = EntityManager.session.query(Teacher).filter_by(email=email).first()

    # Trying to find the student in the database
    student = EntityManager.session.query(Student).filter_by(email=email).first()

    # Checking if the teacher exists and the password is correct
    if teacher is not None and teacher.password == password:
        session["teacher_id"] = teacher.id
        flash(f"Bem-vindo(a), {teacher.name}!", "success")
        return redirect(url_for("teacher_blueprint.dashboard"))

    # Checking if the student exists and the password is correct
    elif student is not None and student.password == password:
        session["student_id"] = student.id
        flash(f"Bem-vindo(a), {student.name}!", "success")
        return redirect(url_for("student_blueprint.dashboard"))

    # Redirecting the user to the sign in page if the credentials are invalid
    flash("Credenciais Inválidas!", "error")
    return redirect(url_for("generic_blueprint.sign_in"))


@generic_blueprint.route("/my_account", methods=["GET"])
@require_authentication()
def my_account():
    # Finding the user account based on the session data
    if "teacher_id" in session:
        user = EntityManager.session.query(Teacher).get(session["teacher_id"])
    elif "student_id" in session:
        user = EntityManager.session.query(Student).get(session["student_id"])

    return render_template("my_account.html", user=user)


@generic_blueprint.route("/my_account", methods=["POST"])
@require_authentication()
def update_account():
    # Finding the user account based on the session data
    if "teacher_id" in session:
        user = EntityManager.session.query(Teacher).get(session["teacher_id"])
    elif "student_id" in session:
        user = EntityManager.session.query(Student).get(session["student_id"])

    # Updating the user account information based on the form data (name, email, password)
    new_attributes = {
        "name": request.form["name"],
        "email": request.form["email"],
        "password": request.form["password"],
    }
    user.__class__.update(id=user.id, new_attributes=new_attributes)

    flash("Informações atualizadas com sucesso!", "success")

    if "teacher_id" in session:
        return redirect(url_for("teacher_blueprint.dashboard"))
    elif "student_id" in session:
        return redirect(url_for("student_blueprint.dashboard"))


@generic_blueprint.route("/sign_out", methods=["GET"])
@require_authentication()
def sign_out():
    # Removing the teacher credential from the session
    if "teacher_id" in session:
        session.pop("teacher_id")
    elif "student_id" in session:
        session.pop("student_id")

    flash("Você foi desconectado(a) com sucesso!", "success")

    return redirect(url_for("generic_blueprint.index"))


@generic_blueprint.route("/reset_password_request", methods=["POST"])
@redirect_if_logged_in
def reset_password_request():
    # Gathering the form data
    email = request.form["email"]

    # Trying to find the teacher in the database
    user = EntityManager.session.query(Teacher).filter_by(email=email).first()

    if user is None:
        # Trying to find the student in the database
        user = EntityManager.session.query(Student).filter_by(email=email).first()

    # Redirecting the user to the sign in page if the credentials are invalid
    if user is None:
        return redirect(url_for("generic_blueprint.index"))

    # Defining a reset link
    token = generate_reset_token(user.email)

    # Generating the reset link based on the user type (this is needed as we have
    # to understand the user type when latter updating the password using the ORM
    reset_link = url_for(
        "generic_blueprint.reset_password_page",
        user_type=user.__class__.__name__.lower(),
        _external=True,
        token=token,
    )

    # Parsing the email body template
    mail_path = path.join(getcwd(), "adaptive/assets/mail")
    email_content = parse_email_template(template_file=f"{mail_path}/template_forgot_password.txt")

    # Composing the email content with dynamic variables
    email_subject = email_content["subject"]
    email_body = email_content["body"].format(user_name=user.name, reset_link=reset_link)

    send_email(
        gmail_address=current_app.gmail_address,
        gmail_password=current_app.gmail_password,
        sender_address=current_app.sender_address,
        recipient_address=user.email,
        carbon_copy_addresses=current_app.carbon_copy_addresses,
        mail_body=email_body,
        mail_subject=email_subject,
    )

    flash("Um link para redefinir a senha foi enviado para o seu email.", "success")
    return redirect(url_for("generic_blueprint.index"))


@generic_blueprint.route("/reset_password/<user_type>/<token>", methods=["GET"])
@redirect_if_logged_in
def reset_password_page(token: str, user_type: str):
    # Verifying the reset token
    email = verify_reset_token(token)

    # Redirecting the user to the sign in page if the token is invalid
    if email is None:
        flash("O link para redefinir a senha é inválido ou expirou.", "warning")
        return redirect(url_for("generic_blueprint.reset_password_request"))

    return render_template("reset_password.html", token=token, user_type=user_type, email=email)


@generic_blueprint.route("/reset_password/<user_type>", methods=["POST"])
@redirect_if_logged_in
def apply_password_reset(user_type: str):
    # Handling the password reset form
    new_password = request.form["password"]
    email = request.form["email"]

    # Updating the user password
    user_class = globals()[user_type.capitalize()]
    user = EntityManager.session.query(user_class).filter_by(email=email).first()
    if user:
        new_attributes = {"password": new_password}
        user_class.update(id=user.id, new_attributes=new_attributes)

        flash("Sua senha foi atualizada com sucesso. Você pode agora fazer login.", "success")
        return redirect(url_for("generic_blueprint.sign_in"))
