# Importing local modules and packages
from adaptive import create_app
from adaptive.models import *

# Importing built-in modules
from random import choice, randint, random
from hashlib import sha256
from time import time
from os import path, getcwd
from json import dump

# Importing third-party libraries
from faker import Faker

app = create_app()

UPLOAD_DIRECTORY = path.join(getcwd(), "adaptive/assets/uploads")


def mock_all_data():
    # Defining a Faker instance for generating random data
    faker_instance = Faker(locale="pt_BR")

    # Deleting any existing instances
    for student_answer in StudentAnswer.all():
        student_answer.delete(id=student_answer.id)
    for question in Question.all():
        question.delete(id=question.id)
    for trajectory in Trajectory.all():
        trajectory.delete(id=trajectory.id)
    for text_chunk in TextChunk.all():
        text_chunk.delete(id=text_chunk.id)
    for activity in Activity.all():
        activity.delete(id=activity.id)
    for subject_student in SubjectStudent.all():
        subject_student.delete(id=subject_student.id)
    for student in Student.all():
        student.delete(id=student.id)
    for subject in Subject.all():
        subject.delete(id=subject.id)
    for teacher in Teacher.all():
        teacher.delete(id=teacher.id)
    for organization in Organization.all():
        organization.delete(id=organization.id)

    # Creating instances of the Organization class
    for x in range(1):
        print(f"Criando Organização_{x}")
        organization = Organization(name=faker_instance.word())

        # Creating instances of the Teacher class
        for i in range(2):
            print(f"Criando Professor_{i}")
            if i == 0:
                teacher = Teacher(name="Professor", email="professor@professor.com", password="professor", organization_id=organization.id)
                organization.administrator = teacher
                EntityManager.session.commit()

            else:
                Teacher(
                    name=faker_instance.name(),
                    email=faker_instance.email(),
                    password=faker_instance.password(),
                    organization_id=organization.id,
                ),

        # Creating instances of the Subject class
        student_count = 0
        for i in range(2):
            print(f"Criando Subject_{i}")
            subject = Subject(
                name=faker_instance.word(),
                teacher_id=Teacher.all()[0].id,
            )
            # Creating an instance of the Activity class and linking it to its subject
            text_chunk_file_name = f"{str(time()).replace('.', '')}_text_chunks.json"
            text_chunks_file_path = path.join(UPLOAD_DIRECTORY, text_chunk_file_name)
            activity = Activity(
                subject_id=subject.id,
                base_material="pdf_exemplo.pdf",
                text_chunks_file_path=text_chunks_file_path,
                min_questions=randint(1, 3),
                max_questions=randint(7, 10),
                model_name=choice(["llama3-8b-8192", "llama3-8b-4096", "llama3-4b-2048"]),
                model_temperature=random(),
                model_system_prompt=faker_instance.sentence(),
            )

            # Creating instances of the TextChunk class and linking them to the activity
            text_chunks = []
            for i in range(3):
                # Generating the text chunk metadata
                content = faker_instance.sentence()
                identifier = sha256(f"{i}_{content}".encode("utf-8")).hexdigest()

                # Saving the text chunk metadata into the text_chunks list
                text_chunks.append({"identifier": identifier, "content": content})

                # Creating a TextChunk instance in the database
                TextChunk(identifier=identifier, activity_id=activity.id)
                print(f"Criando TextChunk_{i}")
                print()
            # Storing the text chunks into the JSON file
            with open(text_chunks_file_path, "w", encoding="utf-8") as file:
                dump(text_chunks, file, ensure_ascii=False, indent=4)
            print(f"\nArquivo JSON criado para hospedar os registros da entidade TextChunk: {text_chunks_file_path}\n")

            # Creating instances of the Student class and linking them to the subject
            for _ in range(5):
                student_count += 1
                print(f"Criando Student_{student_count}")
                if student_count == 1:
                    student = Student(
                        name="Estudante",
                        email="estudante@estudante.com",
                        password="estudante",
                        organization_id=organization.id,
                    )
                else:
                    student = Student(
                        name=faker_instance.name(),
                        email=faker_instance.email(),
                        password=faker_instance.password(),
                        organization_id=organization.id,
                    )

                SubjectStudent(
                    student_id=student.id,
                    subject_id=subject.id,
                )
                print(f"Criando SubjectStudent_{student_count}")

                # Creating a trajectory for the student in the current activity
                trajectory = Trajectory(
                    activity_id=activity.id,
                    student_id=student.id,
                )
                trajectory.status = "completed"
                print(f"Criando Trajectory_{student_count}")

                # Creating questions for the trajectory
                for j in range(10):
                    print(f"Criando Question_{j} para o Student_{student_count}")
                    question = Question(
                        body=faker_instance.sentence(),
                        answer=faker_instance.word(),
                        difficulty=1,
                        text_chunk_id=choice(TextChunk.all()).id,
                        trajectory_id=trajectory.id,
                    )
                    StudentAnswer(
                        content=faker_instance.word(),
                        correctness=choice([1, 2, 3]),
                        descriptive_feedback=faker_instance.sentence(),
                        sentiment=choice(["Confiança", "Entusiasmo", "Insegurança", "Indiferença"]),
                        humor=choice(["Positivo", "Negativo", "Neutro"]),
                        question_id=question.id,
                    )
                    print(f"Criando StudentAnswer_{j} para a Question_{j} do Student_{student_count}")


if __name__ == "__main__":
    with app.app_context():
        mock_all_data()
        print("\n\n\n==== Dados mock inseridos com sucesso ====\n\n\n")
