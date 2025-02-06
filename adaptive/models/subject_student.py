# Importing the EntityManager class
from adaptive.models.entity_manager import EntityManager

# Importing the Object Relational Mapping (ORM)
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship


class SubjectStudent(EntityManager.base, EntityManager):
    """This class represents the relationship between students and subjects."""

    # Defining the table name
    __tablename__ = "subjects_students"

    # Defining the table columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)

    # Defining a foreign keys that point to the students and subjects
    student = relationship("Student", back_populates="subjects_students")
    subject = relationship("Subject", back_populates="subjects_students")

    def __init__(self, student_id: int, subject_id: int) -> object:
        """Subject object initialization method.

        Args:
            student_id (str): Student ID.
            subject_id (int): Subject ID.

        Returns:
            object: Initialized object instance.
        """
        self.student_id = student_id
        self.subject_id = subject_id
        EntityManager.__init__(self)
