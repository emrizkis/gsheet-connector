from abc import ABC, abstractmethod
from google.auth.credentials import Credentials


class CredentialProvider(ABC):
    """Interface (Abstract Base Class) for obtaining Google API credentials.
    
    Adheres to the Open/Closed Principle (OCP) and Dependency Inversion Principle (DIP).
    Any new authentication mechanism (e.g. OAuth, ID tokens) can implement this interface.
    """

    @abstractmethod
    def get_credentials(self) -> Credentials:
        """Retrieves Google Authentication credentials.

        Returns:
            Credentials: The loaded Google Auth credentials object.

        Raises:
            AuthenticationError: If credentials cannot be loaded or validated.
        """
        pass
