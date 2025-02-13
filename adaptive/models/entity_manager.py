# Importing third-party libraries
from sqlalchemy.orm import declarative_base
from sqlalchemy import func

VERBOSE = False


class EntityManager:
    """This class provides auxiliary methods that facilitate object manipulation."""

    base = declarative_base()

    def __init__(self) -> object:
        """Initializes the object and registers it in the database.

        Returns:
            object: Instance of the class being instantiated.
        """
        if VERBOSE:
            print(f"Instância {self} criada com sucesso.")

        try:
            # Adding the instance to the database
            EntityManager.session.add(self)

            # Confirming the transaction
            EntityManager.session.commit()

        except Exception:
            EntityManager.session.rollback()

    def __str__(self) -> str:
        """Defines how the object is represented inside print statements.

        Returns:
            obj (str): Object representation
        """
        return f"{self.__class__.__name__}_{self.id}"

    def __repr__(self) -> str:
        """Defines how the object is represented inside the console.

        Returns:
            str: Object representation.
        """
        return f"{self.__class__.__name__}_{self.id}"

    @classmethod
    def all(cls) -> list:
        """Returns the list of created objects of a given class.

        Returns:
            list: List of objects from a given class.
        """
        return EntityManager.session.query(cls).all()

    @classmethod
    def update(cls, id: int, new_attributes: dict) -> object:
        """Updates an instance based on its ID and a dictionary with the new attributes.

        Args:
            id (int): ID of the instance to be updated.
            new_attributes (dict): Dictionary with the new attributes.

        Returns:
            instance (object): Updated instance or None if the instance was not found.
        """
        # Gathering the instance by its ID
        instance = EntityManager.session.query(cls).filter(cls.id == id).first()

        # If the instance exists, update its attributes
        if instance:
            try:
                for attribute_name, attribute_value in new_attributes.items():
                    if hasattr(instance, attribute_name):
                        setattr(instance, attribute_name, attribute_value)

                # Confirming the transaction
                EntityManager.session.commit()

                # Printing the success message
                print(f"{instance.__class__.__name__}{instance.id} atualizada com sucesso.")

            except Exception:
                # Rolling back the transaction
                EntityManager.session.rollback()

                # Printing the error message
                print(f"Erro ao atualizar {instance.__class__.__name__}_{instance.id}.")

            # Returning the updated instance
            return instance

        else:
            # Printing the error message
            print(f"{instance.__class__.__name__}{instance.id} não encontrada.")

            # Returning None as the instance was not found
            return None

    @classmethod
    def delete(cls, id: int) -> bool:
        """Removes an instance from the database based on an specific ID.

        Args:
            id (int): ID of the instance to be removed.

        Returns:
            bool: True if the instance was successfully removed, False otherwise.
        """
        # Gathering the instance by its ID
        instance = EntityManager.session.query(cls).filter(cls.id == id).first()

        if instance:
            try:
                # Removing the instance from the database
                EntityManager.session.delete(instance)

                # Confirming the transaction
                EntityManager.session.commit()

                if VERBOSE:
                    print(f"{instance.__class__.__name__}_{id} deletada com sucesso.")

                # Returning True as the instance was successfully removed
                return True
            except Exception:
                # Rolling back the transaction
                EntityManager.session.rollback()

                if VERBOSE:
                    print(f"Erro ao deletar {instance.__class__name__}_{id}.")

                # Returning False as the instance was not removed
                return False
        else:
            if VERBOSE:
                print(f"Instância com ID {id} não encontrada.")

            # Returning False as the instance was not found
            return False

    @classmethod
    def find_by(cls, attribute_name: str, attribute_value: str) -> object:
        """Finds an instance based on an attribute name and its value.

        Args:
            attribute_name (str): Name of the attribute to be used as filter.
            attribute_value (str): Value of the attribute to be used as filter.

        Returns:
            obj: Instance found.
        """
        return EntityManager.session.query(cls).filter(getattr(cls, attribute_name) == attribute_value).first()
