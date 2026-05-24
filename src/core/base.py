from abc import ABC, abstractmethod
from src.models.sheet_data import SheetData


class SheetReader(ABC):
    """Interface (Abstract Base Class) for reading spreadsheets.
    
    Adheres to the Interface Segregation Principle (ISP) by only specifying reading capability,
    and Dependency Inversion Principle (DIP) so high-level modules depend on this abstraction.
    """

    @abstractmethod
    def read_sheet(self, spreadsheet_id: str, range_name: str) -> SheetData:
        """Reads spreadsheet data from a given sheet ID and cell range.

        Args:
            spreadsheet_id (str): The unique ID of the spreadsheet.
            range_name (str): The range of cells to read (e.g., 'Sheet1!A1:D50').

        Returns:
            SheetData: Object containing the parsed sheet data.

        Raises:
            SheetReaderError: If reading fails due to API errors or invalid ranges.
        """
        pass
