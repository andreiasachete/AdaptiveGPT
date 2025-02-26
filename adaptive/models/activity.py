# Importing the EntityManager class
from adaptive.models.entity_manager import EntityManager

# Importing the Object Relational Mapping (ORM)
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float
from sqlalchemy.orm import relationship


class Activity(EntityManager.base, EntityManager):
    """This class represents a student activity in the system."""

    # Defining the table name
    __tablename__ = "activities"

    # Defining the table columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    creation_status = Column(String(80), nullable=False)
    base_material = Column(String(180), nullable=False)
    text_chunks_file_path = Column(String(600), nullable=False)
    min_questions = Column(Integer, nullable=False)
    max_questions = Column(Integer, nullable=False)
    llm_provider = Column(String(180), nullable=False)
    model_name = Column(String(180), nullable=False)
    model_temperature = Column(Float, nullable=False)
    model_system_prompt = Column(Text(3000), nullable=False)

    # Defining the relationship between activities and subjects
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    subject = relationship("Subject", back_populates="activities")

    # Defining the relationship between activities and trajectories
    trajectories = relationship("Trajectory", back_populates="activity", cascade="all, delete-orphan")

    # Defining the relationship between activities and text chunks located within its text chunk file path
    text_chunks = relationship("TextChunk", back_populates="activity", cascade="all, delete-orphan")

    def __init__(
        self,
        subject_id: int,
        base_material: str,
        text_chunks_file_path: str,
        min_questions: str,
        max_questions: str,
        llm_provider: str,
        model_name: str,
        model_temperature: str,
        model_system_prompt: str,
    ) -> object:
        """Activity object initialization method.

        Args:
            base_material (str): Base material used in the activity.
            text_chunks_file_path (str): Location of the JSON file that contains the text chunk.
            min_questions (str): Minimum number of questions to be asked in the activity.
            max_questions (str): Maximum number of questions to be asked in the activity.
            llm_provider (str): Name of the LLM provider used.
            model_name (str): Name of the foundational model used to generate questions in the activity.
            model_temperature (str): Model temperature used to generate questions in the activity.
            model_system_prompt (str): System prompt used by the chosen model to generate questions in the activity.

        Returns:
            object: Initialized object instance.
        """
        self.subject_id = subject_id
        self.creation_status = "pending"
        self.base_material = base_material
        self.text_chunks_file_path = text_chunks_file_path
        self.min_questions = min_questions
        self.max_questions = max_questions
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.model_temperature = model_temperature
        self.model_system_prompt = model_system_prompt

        # Calling the parent class (EntityManager) initialization method
        EntityManager.__init__(self)

    @property
    def questions(self):
        all_questions = []
        for trajectory in self.trajectories:
            for question in trajectory.questions:
                all_questions.append(question)

        return all_questions

    @property
    def student_answers(self):
        all_student_answers = []
        for trajectory in self.trajectories:
            for question in trajectory.questions:
                if question.student_answer is not None:
                    all_student_answers.append(question.student_answer)

        return all_student_answers

    @property
    def respondents(self):
        all_respondents = []
        for trajectory in self.trajectories:
            for question in trajectory.questions:
                if question.answer is not None:
                    all_respondents.append(trajectory.student)
                    break

        return all_respondents

    @property
    def avg_respondent_correctness(self):
        correct = 0
        total = 0
        for trajectory in self.trajectories:
            for question in trajectory.questions:
                if question.student_answer is not None:
                    total += 1
                    if question.student_answer.correctness == 3:
                        correct += 1

        return round((correct / total) * 100, 2) if total > 0 else 0
