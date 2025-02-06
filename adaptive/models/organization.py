# Importing the EntityManager class
from adaptive.models.entity_manager import EntityManager

# Importing the Object Relational Mapping (ORM)
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship


class Organization(EntityManager.base, EntityManager):
    """This class represents an organization in the system."""

    # Defining the table name
    __tablename__ = "organizations"

    # Defining the table columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)

    # Defining the relationship between organizations and administrators (teachers that manage the organization)
    administrator_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    administrator = relationship("Teacher", back_populates="administered_organization", foreign_keys=[administrator_id])

    # Defining the relationship between organizations and teachers
    teachers = relationship(
        "Teacher",
        back_populates="organization",
        cascade="all, delete-orphan",
        foreign_keys=lambda: [__import__("adaptive.models.teacher", fromlist=["Teacher"]).Teacher.organization_id],
    )

    # Defining the relationship between organizations and students
    students = relationship("Student", back_populates="organization", cascade="all, delete-orphan")

    def __init__(self, name: str) -> object:
        """Trajectory object initialization method.

        Args:
            name (str): Organization name.

        Returns:
            object: Initialized object instance.
        """
        self.administrator_id = None
        self.name = name

        # Calling the parent class (EntityManager) initialization method
        EntityManager.__init__(self)
