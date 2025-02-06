# Importing the EntityManager class
from adaptive.models.entity_manager import EntityManager

# Importing the Object Relational Mapping (ORM)
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class Subject(EntityManager.base, EntityManager):
    """This class represents a subject in the system."""

    # Defining the table name
    __tablename__ = "subjects"

    # Defining the table columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)

    # Defining the relationship between subjects and teachers
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    teacher = relationship("Teacher", back_populates="subjects")

    # Defining the relationship between students and subjects
    subjects_students = relationship("SubjectStudent", back_populates="subject", cascade="all, delete-orphan")

    # Defining the relationship between subjects and activities
    activities = relationship("Activity", back_populates="subject", cascade="all, delete-orphan")

    def __init__(self, name: str, teacher_id: int) -> object:
        """Subject object initialization method.

        Args:
            name (str): Subject name.
            teacher_id (int): Teacher ID.

        Returns:
            object: Initialized object instance.
        """
        self.name = name
        self.teacher_id = teacher_id

        # Calling the parent class (EntityManager) initialization method
        EntityManager.__init__(self)

    @property
    def students(self):
        return [association.student for association in self.subjects_students]

    @property
    def student_answers(self):
        answers = []
        for student in self.students:
            for trajectory in student.trajectories:
                for question in trajectory.questions:
                    answers.append(question.student_answer)

        return answers

    @property
    def questions(self):
        questions = []
        for student in self.students:
            for trajectory in student.trajectories:
                for question in trajectory.questions:
                    questions.append(question)

        return questions

    @property
    def trajectories(self):
        trajectories = []
        for student in self.students:
            for trajectory in student.trajectories:
                trajectories.append(trajectory)

        return trajectories

    # SubjectStudent
