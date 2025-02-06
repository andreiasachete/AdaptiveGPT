# Importing the EntityManager class
from adaptive.models.entity_manager import EntityManager

# Importing the Object Relational Mapping (ORM)
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class Student(EntityManager.base, EntityManager):
    """This class represents a student in the system."""

    # Defining the table name
    __tablename__ = "students"

    # Defining the table columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False)

    # Defining the relationship between students and subjects
    subjects_students = relationship("SubjectStudent", back_populates="student", cascade="all, delete-orphan")

    # Defining the relationship between students and trajectories
    trajectories = relationship("Trajectory", back_populates="student", cascade="all, delete-orphan")

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="students")

    def __init__(self, name: str, email: str, password: str, organization_id: int) -> object:
        """Teacher object initialization method.

        Args:
            name (str): Teacher name.
            email (str): Teacher email.
            password (str): Teacher password.
            organization_id (int): ID of the organization the student belongs to.

        Returns:
            object: Initialized object instance.
        """
        self.name = name
        self.email = email
        self.password = password
        self.organization_id = organization_id

        # Calling the parent class (EntityManager) initialization method
        EntityManager.__init__(self)

    @property
    def subjects(self):
        return [association.subject for association in self.subjects_students]

    @property
    def questions_answered(self):
        questions = []

        for trajectory in self.trajectories:
            for question in trajectory.questions:
                if question.student_answer is not None:
                    questions.append(question)

        return questions

    @property
    def percentage_of_questions_answered_correctly(self):
        questions_answered = self.questions_answered

        if len(questions_answered) == 0:
            return 0

        questions_answered_correctly = 0
        for question in questions_answered:
            if question.student_answer.correctness == 1:
                questions_answered_correctly += 1

        return round((questions_answered_correctly / len(questions_answered)) * 100, 2)
