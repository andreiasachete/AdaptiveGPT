# Importing third-party libraries
from sqlalchemy.orm import declarative_base


class EntityManager:
    """This class provides auxiliary methods that facilitate object manipulation."""

    base = declarative_base()

    def __init__(self) -> object:
        """Initializes the object and registers it in the database.

        Returns:
            object: Instance of the class being instantiated.
        """
        print(f"Instância {self} criada com sucesso.")
        # Creating a new session to perform the transaction
        current_session = EntityManager.session()

        # Adding the instance to the database
        current_session.add(self)

        # Confirming the transaction
        current_session.commit()

        return self

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
        # Creating a new session to perform the transaction
        current_session = EntityManager.session()

        # Trying to execute the query
        try:
            return current_session.query(cls).all()

        except Exception:
            return []

    @classmethod
    def update(cls, id: int, new_attributes: dict) -> object:
        """Updates an instance based on its ID and a dictionary with the new attributes.

        Args:
            id (int): ID of the instance to be updated.
            new_attributes (dict): Dictionary with the new attributes.

        Returns:
            instance (object): Updated instance or None if the instance was not found.
        """
        # Creating a new session to perform the transaction
        current_session = EntityManager.session()

        # Trying to execute the query
        try:
            # Gathering the instance by its ID
            instance = current_session.query(cls).filter(cls.id == id).first()

            if instance is not None:
                for attribute_name, attribute_value in new_attributes.items():
                    if hasattr(instance, attribute_name):
                        setattr(instance, attribute_name, attribute_value)

                # Confirming the transaction
                current_session.commit()
                print(f"{instance.__class__.__name__}{instance.id} atualizada com sucesso.")

                # Returning the updated instance
                return instance

        except Exception:
            # Rolling back the transaction
            current_session.rollback()

            # Printing the error message
            print(f"Erro ao atualizar {instance.__class__.__name__}_{instance.id}.")

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
        # Creating a new session to perform the transaction
        current_session = EntityManager.session()

        # Trying to execute the query
        try:
            # Gathering the instance by its ID
            instance = cls.find_by_id(id=id)
            if instance is not None:
                # Removing the instance from the database
                current_session.delete(instance)

                # Confirming the transaction
                current_session.commit()
                print(f"{instance.__class__.__name__}_{id} deletada com sucesso.")

                # Returning True as the instance was successfully removed
                return True

        except Exception as error:
            # Rolling back the transaction
            current_session.rollback()
            print(f"Erro ao deletar {cls.__name__}_{id}. Erro:\n{error}")

            # Returning False as the instance was not removed
            return False

    @classmethod
    def find_by(cls, attribute_name: str, attribute_value: str) -> list:
        """Finds a list of instances based on an attribute name and its value.

        Args:
            attribute_name (str): Name of the attribute to be used as filter.
            attribute_value (str): Value of the attribute to be used as filter.

        Returns:
            list: Instances that match the filter criteria found or an empty list if no instance was found.
        """
        # Creating a new session to perform the transaction
        current_session = EntityManager.session()

        # Trying to execute the query
        try:
            instances = current_session.query(cls).filter(getattr(cls, attribute_name) == attribute_value).all()

        except Exception:
            instances = []

        # Returning the instances found
        return instances

    @classmethod
    def find_by_id(cls, id: int) -> object:
        """Finds an instance based on its ID.

        Args:
            id (int): ID of the instance to be found.

        Returns:
            obj: Instance found.
        """
        # Creating a new session to perform the transaction
        current_session = EntityManager.session()

        # Trying to execute the query
        try:
            return current_session.query(cls).filter(cls.id == id).first()

        except Exception:
            return None
