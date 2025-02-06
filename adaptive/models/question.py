# Importing the EntityManager class
from adaptive.models.entity_manager import EntityManager

# Importing the Object Relational Mapping (ORM)
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship


class Question(EntityManager.base, EntityManager):
    """This class represents a trajectory question in the system."""

    # Defining the table name
    __tablename__ = "questions"

    # Defining the table columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    body = Column(Text(3000), nullable=False)
    answer = Column(Text(3000), nullable=False)
    difficulty = Column(Integer, nullable=False)

    # Defining the relationship between questions and trajectories
    trajectory_id = Column(Integer, ForeignKey("trajectories.id"), nullable=False)
    trajectory = relationship("Trajectory", back_populates="questions")

    # Defining the relationship between questions and text chunks used as base for the question generation
    text_chunk_id = Column(Integer, ForeignKey("text_chunks.id"), nullable=False)
    text_chunk = relationship("TextChunk", back_populates="questions")

    # Defining the relationship between questions and student answers
    student_answer = relationship("StudentAnswer", uselist=False, cascade="all, delete-orphan")

    def __init__(self, body: str, answer: str, difficulty: str, text_chunk_id: int, trajectory_id: int) -> object:
        """Subject object initialization method.

        Args:
            body (str): Question body.
            answer (str): Question answer.
            difficulty (str): Question difficulty.
            text_chunk_id (int): TextChunk ID.
            trajectory_id (int): Trajectory ID.

        Returns:
            object: Initialized object instance.
        """
        self.body = body
        self.answer = answer
        self.difficulty = difficulty
        self.text_chunk_id = text_chunk_id
        self.trajectory_id = trajectory_id

        # Calling the parent class (EntityManager) initialization method
        EntityManager.__init__(self)
