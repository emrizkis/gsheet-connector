import os
from google.oauth2 import service_account
from google.auth.credentials import Credentials
from src.auth.base import CredentialProvider
from src.exceptions import AuthenticationError


class ServiceAccountCredentialProvider(CredentialProvider):
    """Provides Google API credentials using a Service Account JSON key file.
    
    This is the industry standard for backend automation and server-to-server interaction.
    """

    def __init__(self, key_file_path: str, scopes: list[str] = None):
        """Initializes the provider with the path to the credentials file and the required scopes.

        Args:
            key_file_path (str): Absolute or relative path to the Google Service Account JSON file.
            scopes (list[str], optional): API scopes. Defaults to read-only sheets access.
        """
        self._key_file_path = key_file_path
        # Default scope is read-only for Google Sheets
        self._scopes = scopes or ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    def get_credentials(self) -> Credentials:
        """Loads and returns Google Service Account credentials.

        Returns:
            Credentials: A ServiceAccountCredentials instance.

        Raises:
            AuthenticationError: If the credential file is missing or invalid.
        """
        if not os.path.exists(self._key_file_path):
            raise AuthenticationError(
                f"File kredensial Service Account tidak ditemukan di path: '{self._key_file_path}'. "
                "Pastikan Anda telah mengunduh key JSON dari Google Cloud Console dan menyimpannya di tempat yang benar, "
                "serta menyesuaikan konfigurasi GOOGLE_SERVICE_ACCOUNT_FILE di .env."
            )

        try:
            credentials = service_account.Credentials.from_service_account_file(
                self._key_file_path,
                scopes=self._scopes
            )
            return credentials
        except Exception as e:
            raise AuthenticationError(
                f"Gagal membaca atau memvalidasi file kredensial Service Account '{self._key_file_path}': {e}"
            ) from e
