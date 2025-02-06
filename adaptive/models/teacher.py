# Importing the EntityManager class
from adaptive.models.entity_manager import EntityManager

# Importing the Object Relational Mapping (ORM)
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class Teacher(EntityManager.base, EntityManager):
    """This class represents a teacher in the system."""

    # Defining the table name
    __tablename__ = "teachers"

    # Defining the table columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False)

    # Defining the relationship between teachers and subjects
    subjects = relationship("Subject", back_populates="teacher", cascade="all, delete-orphan")

    # Defining the relationship between teachers and organizations
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="teachers", foreign_keys=[organization_id])

    administered_organization = relationship(
        "Organization",
        back_populates="administrator",
        foreign_keys=lambda: [__import__("adaptive.models.organization", fromlist=["Organization"]).Organization.administrator_id],
        uselist=False,
    )

    def __init__(self, name: str, email: str, password: str, organization_id: int) -> object:
        """Teacher object initialization method.

        Args:
            name (str): Teacher name.
            email (str): Teacher email.
            password (str): Teacher password.
            organization_id (int): ID of the organization the teacher belongs to.

        Returns:
            object: Initialized object instance.
        """
        self.name = name
        self.email = email
        self.password = password
        self.organization_id = organization_id

        # Calling the parent class (EntityManager) initialization method
        EntityManager.__init__(self)
