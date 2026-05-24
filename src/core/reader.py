from googleapiclient.discovery import build
from src.auth.base import CredentialProvider
from src.core.base import SheetReader
from src.exceptions import SheetReaderError
from src.models.sheet_data import SheetData


class GoogleSheetReader(SheetReader):
    """Concrete implementation of SheetReader using Google Sheets API v4.
    
    Adheres to the Dependency Inversion Principle (DIP) by injecting a 
    CredentialProvider interface to resolve authentication.
    """

    def __init__(self, credential_provider: CredentialProvider):
        """Initializes the GoogleSheetReader.

        Args:
            credential_provider (CredentialProvider): Any class implementing CredentialProvider.
        """
        self._credential_provider = credential_provider

    def read_sheet(self, spreadsheet_id: str, range_name: str) -> SheetData:
        """Reads a Google Sheet using the Sheets API v4.

        Args:
            spreadsheet_id (str): The Google Spreadsheet ID.
            range_name (str): The sheet range, e.g., 'Sheet1!A1:D100'.

        Returns:
            SheetData: Object containing parsed rows and helper methods.

        Raises:
            SheetReaderError: If call to the Google API fails.
        """
        try:
            # 1. Obtain credentials through our provider abstraction
            credentials = self._credential_provider.get_credentials()

            # 2. Build the Sheets API client
            service = build("sheets", "v4", credentials=credentials)

            # 3. Call the values.get endpoint
            sheet_api = service.spreadsheets()
            response = sheet_api.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()

            raw_values = response.get("values", [])
            return SheetData(raw_values)

        except Exception as e:
            # Wrap low-level Google API errors in our custom high-level domain exception
            raise SheetReaderError(
                f"Gagal membaca Google Sheet. ID: '{spreadsheet_id}', Range: '{range_name}'. Detail error: {e}"
            ) from e
