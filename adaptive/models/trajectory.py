# Importing the EntityManager class
from adaptive.models.entity_manager import EntityManager

# Importing the Object Relational Mapping (ORM)
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class Trajectory(EntityManager.base, EntityManager):
    """This class represents a student trajectory in the system."""

    # Defining the table name
    __tablename__ = "trajectories"

    # Defining the table columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(100), nullable=False)

    # Defining the relationship between trajectories and activities
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    activity = relationship("Activity", back_populates="trajectories")

    # Defining the relationship between trajectories and students
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    student = relationship("Student", back_populates="trajectories")

    # Defining the relationship between trajectories and questions
    questions = relationship("Question", back_populates="trajectory", cascade="all, delete-orphan")

    def __init__(self, student_id: int, activity_id: int) -> object:
        """Trajectory object initialization method.

        Args:
            student_id (int): ID of the student that the trajectory belongs to.
            activity_id (int): ID of the activity that the trajectory belongs to.

        Returns:
            object: Initialized object instance.
        """
        self.status = "active"
        self.student_id = student_id
        self.activity_id = activity_id

        # Calling the parent class (EntityManager) initialization method
        EntityManager.__init__(self)

    @property
    def last_unanswered_question(self) -> object:
        """Method that returns the latest unanswered question of the trajectory.

        Returns:
            object: Latest unanswered question.
        """
        for question in self.questions:
            if question.student_answer is None:
                return question

        return None

    @property
    def last_answered_question(self) -> object:
        """Method that returns the latest answered question of the trajectory.

        Returns:
            object: Latest answered question.
        """
        for question in reversed(self.questions):
            if question.student_answer is not None:
                return question

        return None
