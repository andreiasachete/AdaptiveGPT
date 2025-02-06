# Importing the EntityManager class
from adaptive.models.entity_manager import EntityManager

# Importing the Object Relational Mapping (ORM)
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

# Importing native modules
from json import load, dumps


class TextChunk(EntityManager.base, EntityManager):
    """This class represents a text chunk used to generate questions in the system."""

    # Defining the table name
    __tablename__ = "text_chunks"

    # Defining the table columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String(256), nullable=False)  # Auto-generated hash based on the chunk content and its position in the whole text

    # Defining the relationship between text chunks and activities
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    activity = relationship("Activity", back_populates="text_chunks")

    # Defining the relationship between text chunks and questions
    questions = relationship("Question", back_populates="text_chunk", cascade="all, delete-orphan")

    def __init__(self, identifier: str, activity_id: int) -> object:
        """TextChunk object initialization method.

        Args:
            identifier (str): Auto-generated hash based on the chunk content and its position in the whole text used to guarantee integrity.
            activity_id (str): ID of the activity that the text chunk belongs to.

        Returns:
            object: Initialized object instance.
        """
        self.identifier = identifier
        self.activity_id = activity_id

        # Calling the parent class (EntityManager) initialization method
        EntityManager.__init__(self)

    @property
    def content(self):
        # Gathering the JSON file containing the text chunk content
        file_name = self.activity.text_chunks_file_path

        # Reading the JSON file content
        with open(file_name, "r") as file:
            all_activity_text_chunks = load(file)

        # Finding the text chunk content based on its identifier
        text_chunk_content = next((chunk["content"] for chunk in all_activity_text_chunks if chunk["identifier"] == self.identifier), "")

        return text_chunk_content
