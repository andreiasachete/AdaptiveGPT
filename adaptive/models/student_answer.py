# Importing the EntityManager class
from adaptive.models.entity_manager import EntityManager

# Importing the Object Relational Mapping (ORM)
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship


class StudentAnswer(EntityManager.base, EntityManager):
    """This class represents a student answer for a question in the system."""

    # Defining the table name
    __tablename__ = "student_answers"

    # Defining the table columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text(3000), nullable=False)
    correctness = Column(Integer, nullable=False)
    descriptive_feedback = Column(Text(3000), nullable=True)
    sentiment = Column(String(320), nullable=True)
    humor = Column(String(320), nullable=True)

    # Defining the relationship between student answers and questions
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    question = relationship("Question", uselist=False, viewonly=True)

    def __init__(self, content: str, correctness: int, descriptive_feedback: str, sentiment: str, humor: str, question_id: int) -> object:
        """Student answer object initialization method.

        Args:
            content (str): Student answer.
            correctness (int): Answer correctness (1=correct, 0.5=partially correct, 0=incorrect).
            descriptive_feedback (str): Descriptive feedback.
            sentiment (str): Sentiment analysis.
            humor (str): Humor analysis.
            question_id (int): Question ID.

        Returns:
            object: Initialized object instance.
        """
        self.content = content
        self.correctness = correctness
        self.descriptive_feedback = descriptive_feedback
        self.sentiment = sentiment
        self.humor = humor
        self.question_id = question_id

        # Calling the parent class (EntityManager) initialization method
        EntityManager.__init__(self)
