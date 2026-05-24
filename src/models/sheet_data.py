from typing import Any, Optional
from pydantic import BaseModel


class StageDetail(BaseModel):
    """Represents the tracking details of a specific SDLC stage."""
    pic: Optional[str] = None
    target: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None


class ProjectRecord(BaseModel):
    """Represents a structured row of project data with its SDLC stages."""
    project_name: str
    notes: Optional[str] = None
    sprint_id: Optional[str] = None
    stages: dict[str, StageDetail]


class SheetData:
    """Represents tabular data retrieved from Google Sheets.
    
    Adheres to the Single Responsibility Principle (SRP) by managing raw data storage
    and structuring/parsing operations.
    """

    def __init__(self, values: list[list[Any]]):
        """Initializes SheetData with raw 2D list of values from Google Sheets API."""
        self._raw_values = values or []

    @property
    def raw_values(self) -> list[list[Any]]:
        """Gets the raw unmodified 2D values."""
        return self._raw_values

    def to_structured_records(self) -> list[ProjectRecord]:
        """Parses the raw values with merged-cells and hierarchical headers into ProjectRecord models.

        Handles:
        1. Parent category propagation (merged cells in Row 0).
        2. Sub-header mapping (Row 1).
        3. Identity mapping (Cols B, C, D -> index 0, 1, 2).
        4. Omitted or empty cells.

        Returns:
            list[ProjectRecord]: A list of parsed structured project records.
        """
        # We need at least 3 rows to have: Main Header (Row 0), Sub Header (Row 1), and at least 1 Data Row (Row 2)
        if len(self._raw_values) < 3:
            return []

        row_0_categories = self._raw_values[0]
        row_1_subheaders = self._raw_values[1]

        # 1. Map columns to their respective categories and sub-headers
        # col_idx -> (category_name, subheader_key)
        column_mappings: dict[int, tuple[str, str]] = {}
        current_category = ""

        # Identity columns:
        # Col B (index 0): Project Name
        # Col C (index 1): Notes
        # Col D (index 2): Sprint ID
        # Stage categories start from Col E (index 3) onwards
        for col_idx in range(3, len(row_1_subheaders)):
            # Propagate parent category if merged
            if col_idx < len(row_0_categories) and row_0_categories[col_idx]:
                current_category = str(row_0_categories[col_idx]).strip()

            if not current_category:
                continue

            subheader = str(row_1_subheaders[col_idx]).strip()
            # Normalize subheader name to lowercase attribute names of StageDetail
            subheader_key = self._normalize_subheader_key(subheader)

            if subheader_key:
                column_mappings[col_idx] = (current_category, subheader_key)

        # 2. Parse data rows starting from row index 2
        records: list[ProjectRecord] = []
        for row_idx, row in enumerate(self._raw_values[2:], start=3):
            if not row:
                continue

            # Project Name is at index 0 (Column B in range B3:AV)
            project_name = str(row[0]).strip() if len(row) > 0 else ""

            # Skip header indicator rows or empty rows
            if not project_name or project_name == "Project Name":
                continue

            notes = str(row[1]).strip() if len(row) > 1 else None
            sprint_id = str(row[2]).strip() if len(row) > 2 else None

            # Parse all stages for this project
            stages_data: dict[str, dict[str, Any]] = {}
            
            for col_idx, (category, subheader_key) in column_mappings.items():
                cell_value = str(row[col_idx]).strip() if col_idx < len(row) else None
                
                # We skip writing empty/None cells to keep output clean, but let Pydantic model handle defaults
                if cell_value == "":
                    cell_value = None

                if category not in stages_data:
                    stages_data[category] = {}
                
                stages_data[category][subheader_key] = cell_value

            # Convert dict stage data to Pydantic StageDetail models
            stages: dict[str, StageDetail] = {}
            for category, stage_dict in stages_data.items():
                stages[category] = StageDetail(**stage_dict)

            records.append(
                ProjectRecord(
                    project_name=project_name,
                    notes=notes,
                    sprint_id=sprint_id,
                    stages=stages
                )
            )

        return records

    @staticmethod
    def _normalize_subheader_key(subheader: str) -> Optional[str]:
        """Maps sub-header strings to the attributes of StageDetail model."""
        val = subheader.lower().replace(" ", "")
        if "pic" in val:
            return "pic"
        elif "target" in val:
            return "target"
        elif "due" in val:
            return "due_date"
        elif "status" in val:
            return "status"
        return None

    def __str__(self) -> str:
        return f"SheetData(rows={len(self._raw_values)})"
