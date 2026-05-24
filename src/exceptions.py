class GSheetConnectorError(Exception):
    """Base exception class for the Google Sheets Connector application."""
    pass


class ConfigurationError(GSheetConnectorError):
    """Raised when application configuration is missing, invalid, or misconfigured."""
    pass


class AuthenticationError(GSheetConnectorError):
    """Raised when authentication credentials cannot be loaded or are invalid."""
    pass


class SheetReaderError(GSheetConnectorError):
    """Raised when an error occurs while reading data from a Google Sheet."""
    pass
