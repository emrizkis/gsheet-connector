import json
import os
import time
from typing import Any
from src.core.base import SheetReader
from src.models.sheet_data import SheetData


class CachedSheetReader(SheetReader):
    """Decorator that wraps another SheetReader implementation to cache results in a local JSON file.
    
    Adheres to the Open/Closed Principle (OCP) by adding caching capabilities to the system
    without changing the existing reader class logic (Decorator Pattern).
    """

    CACHE_FILE = os.path.join("data", "cache", "sheet_cache.json")

    def __init__(self, wrapped_reader: SheetReader, ttl_seconds: int):
        """Initializes the cached reader.

        Args:
            wrapped_reader (SheetReader): The underlying reader class to delegate API queries to.
            ttl_seconds (int): Cache Time-To-Live in seconds. If <= 0, caching is bypassed.
        """
        self._wrapped_reader = wrapped_reader
        self._ttl_seconds = ttl_seconds

    def read_sheet(self, spreadsheet_id: str, range_name: str) -> SheetData:
        """Reads data from a sheet, returning cached results if valid, or querying Google API.

        Args:
            spreadsheet_id (str): Google Spreadsheet ID.
            range_name (str): Sheet range (e.g. 'Sheet1!A1:B10').

        Returns:
            SheetData: Object containing parsed spreadsheet rows.
        """
        # Bypass cache if TTL is set to 0 or negative
        if self._ttl_seconds <= 0:
            print("[Cache] Cache dinonaktifkan (TTL = 0). Mengambil data segar langsung dari API...")
            return self._wrapped_reader.read_sheet(spreadsheet_id, range_name)

        cache_key = f"{spreadsheet_id}::{range_name}"
        current_time = time.time()
        
        # Load the cache dictionary from disk
        cache = self._load_cache()

        # Check if the requested range is cached and still fresh
        if cache_key in cache:
            entry = cache[cache_key]
            timestamp = entry.get("timestamp", 0)
            values = entry.get("values", [])

            elapsed = current_time - timestamp
            if elapsed < self._ttl_seconds:
                remaining_seconds = int(self._ttl_seconds - elapsed)
                print(
                    f"[Cache] Memuat data dari cache lokal (menghemat pemanggilan API). "
                    f"Masa berlaku sisa: {remaining_seconds} detik."
                )
                return SheetData(values)

        # Cache miss or expired: fetch fresh data from the wrapped reader
        sheet_data = self._wrapped_reader.read_sheet(spreadsheet_id, range_name)

        # Save the new values back to the local cache
        cache[cache_key] = {
            "timestamp": current_time,
            "values": sheet_data.raw_values
        }
        self._save_cache(cache)

        return sheet_data

    def _load_cache(self) -> dict[str, Any]:
        """Loads cache content from the JSON file safely."""
        if not os.path.exists(self.CACHE_FILE):
            return {}
        try:
            with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # Return empty if file is corrupt or unreadable
            return {}

    def _save_cache(self, cache: dict[str, Any]) -> None:
        """Saves updated cache back to the JSON file safely."""
        try:
            os.makedirs(os.path.dirname(self.CACHE_FILE), exist_ok=True)
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Cache Warning] Gagal menyimpan file cache lokal: {e}")
