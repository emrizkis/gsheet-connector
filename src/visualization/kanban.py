import os
import textwrap
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from src.models.sheet_data import ProjectRecord
from src.exceptions import SheetReaderError


class KanbanBoardGenerator:
    """Generates an interactive HTML-based or Image-based Kanban Board from ProjectRecord lists.
    
    Adheres to the Single Responsibility Principle (SRP) by focusing strictly
    on Kanban board visualization.
    """

    ORDERED_STAGES = [
        "Requirements", "Technical Design", "FSD", "Development",
        "SIT", "UAT", "Deployment", "SK/E", "Pilot", "Release", "Pentest"
    ]

    STAGE_COLORS = {
        "Requirements": "#FFD54F",      # Yellow
        "Technical Design": "#FFB74D",  # Orange
        "FSD": "#FF8A65",               # Deep Orange
        "Development": "#4DD0E1",       # Cyan
        "SIT": "#64B5F6",               # Blue
        "UAT": "#81C784",               # Green
        "Deployment": "#BA68C8",        # Purple
        "SK/E": "#A1887F",              # Brown
        "Pilot": "#90A4AE",             # Blue-Grey
        "Release": "#F06292",           # Pink
        "Pentest": "#E57373"            # Red
    }

    def generate(self, records: list[ProjectRecord], output_path: str = "kanban_board.html", filter_sprint_id: str = None, base_title: str = None) -> str:
        """Generates a Kanban board. Automatically chooses HTML or Image format based on file extension."""
        if output_path.lower().endswith(".png") or output_path.lower().endswith(".jpg") or output_path.lower().endswith(".jpeg"):
            return self.generate_image(records, output_path, filter_sprint_id, base_title)
        return self.generate_html(records, output_path, filter_sprint_id, base_title)

    def generate_html(self, records: list[ProjectRecord], output_path: str = "kanban_board.html", filter_sprint_id: str = None, base_title: str = None) -> str:
        """Generates a responsive and beautiful HTML Kanban board.

        Args:
            records (list[ProjectRecord]): The parsed list of project records.
            output_path (str): The filename of the generated HTML.
            filter_sprint_id (str, optional): Filters the projects by Sprint ID.
            base_title (str, optional): The base title of the Kanban board.

        Returns:
            str: Absolute path to the generated Kanban HTML file.
        """
        # 1. Filter by Sprint ID if provided
        base = base_title or "Project Kanban Board"
        if filter_sprint_id:
            filter_clean = str(filter_sprint_id).strip().lower()
            filtered_records = [
                r for r in records 
                if r.sprint_id and filter_clean in str(r.sprint_id).strip().lower()
            ]
            title = f"{base} - Sprint: {filter_sprint_id}"
        else:
            filtered_records = records
            title = f"{base} - Semua Proyek"

        if not filtered_records:
            raise SheetReaderError(
                f"Tidak ada data proyek untuk divisualisasikan Kanban dengan Sprint ID: '{filter_sprint_id}'"
            )

        # 2. Group projects and their details by active stage
        columns_data: dict[str, list[dict]] = {stage: [] for stage in self.ORDERED_STAGES}

        for record in filtered_records:
            for stage_name in self.ORDERED_STAGES:
                stage = record.stages.get(stage_name)
                if stage:
                    # Consider a stage active if at least one field is filled
                    is_active = any([stage.pic, stage.target, stage.due_date, stage.status])
                    if is_active:
                        columns_data[stage_name].append({
                            "project_name": record.project_name,
                            "pic": stage.pic or "-",
                            "target": stage.target or "",
                            "due_date": stage.due_date or "",
                            "status": stage.status or "not-yet"
                        })

        # 3. Build HTML components
        html_columns = ""
        for stage in self.ORDERED_STAGES:
            tasks = columns_data[stage]
            color = self.STAGE_COLORS.get(stage, "#9e9e9e")
            
            # Header column
            html_columns += f"""
            <div class="kanban-column">
                <div class="column-header" style="border-top: 4px solid {color};">
                    <span class="column-title">{stage}</span>
                    <span class="column-count" style="background-color: {color}22; color: {color};">{len(tasks)}</span>
                </div>
                <div class="column-cards">
            """
            
            if not tasks:
                html_columns += """
                    <div class="empty-column-message">Tidak ada aktivitas</div>
                """
            else:
                for t in tasks:
                    status_class = t["status"].lower().strip()
                    status_label = t["status"]
                    
                    due_html = f'<div class="card-field card-due"><strong>Due:</strong> {t["due_date"]}</div>' if t["due_date"] else ""
                    target_html = f'<div class="card-field card-target"><strong>Target:</strong> {t["target"]}</div>' if t["target"] else ""

                    html_columns += f"""
                    <div class="kanban-card">
                        <div class="card-project-name">{t["project_name"]}</div>
                        <div class="card-field card-pic"><strong>PIC:</strong> {t["pic"]}</div>
                        {target_html}
                        {due_html}
                        <div class="card-status-container">
                            <span class="status-badge status-{status_class}">{status_label}</span>
                        </div>
                    </div>
                    """
            
            html_columns += """
                </div>
            </div>
            """

        # 4. Final HTML Template with modern styles
        html_template = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #121212;
            --column-bg: #1c1c1e;
            --card-bg: #2c2c2e;
            --text-color: #f5f5f7;
            --text-muted: #8e8e93;
            --border-color: #3a3a3c;
            --shadow-color: rgba(0, 0, 0, 0.4);
            
            --status-done-text: #34c759;
            --status-done-bg: rgba(52, 199, 89, 0.15);
            --status-process-text: #ff9500;
            --status-process-bg: rgba(255, 149, 0, 0.15);
            --status-notyet-text: #ff3b30;
            --status-notyet-bg: rgba(255, 59, 48, 0.15);
            --status-default-text: #aeaeb2;
            --status-default-bg: rgba(142, 142, 147, 0.15);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            padding: 2rem 1.5rem;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }}

        header {{
            margin-bottom: 2rem;
            padding: 0 1rem;
        }}

        h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #ffffff, #a1a1a1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .subtitle {{
            color: var(--text-muted);
            font-size: 0.95rem;
            font-weight: 400;
        }}

        .kanban-board-container {{
            flex: 1;
            display: flex;
            gap: 1.2rem;
            overflow-x: auto;
            padding-bottom: 1.5rem;
            scroll-behavior: smooth;
        }}

        /* Custom scrollbar for column horizontal container */
        .kanban-board-container::-webkit-scrollbar {{
            height: 8px;
        }}
        .kanban-board-container::-webkit-scrollbar-track {{
            background: var(--bg-color);
        }}
        .kanban-board-container::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 4px;
        }}
        .kanban-board-container::-webkit-scrollbar-thumb:hover {{
            background: var(--text-muted);
        }}

        .kanban-column {{
            flex: 0 0 320px;
            background-color: var(--column-bg);
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            max-height: 80vh;
            box-shadow: 0 4px 12px var(--shadow-color);
            border: 1px solid var(--border-color);
        }}

        .column-header {{
            padding: 1.2rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 12px 12px 0 0;
            background-color: rgba(255, 255, 255, 0.02);
            border-bottom: 1px solid var(--border-color);
        }}

        .column-title {{
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            font-size: 1.05rem;
            letter-spacing: -0.01em;
        }}

        .column-count {{
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.2rem 0.6rem;
            border-radius: 20px;
        }}

        .column-cards {{
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
        }}

        /* Scrollbar for inside column cards list */
        .column-cards::-webkit-scrollbar {{
            width: 5px;
        }}
        .column-cards::-webkit-scrollbar-track {{
            background: transparent;
        }}
        .column-cards::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }}

        .kanban-card {{
            background-color: var(--card-bg);
            border-radius: 8px;
            padding: 1.1rem;
            border: 1px solid rgba(255, 255, 255, 0.04);
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }}

        .kanban-card:hover {{
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.15);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35);
        }}

        .card-project-name {{
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            font-size: 0.95rem;
            line-height: 1.4;
            margin-bottom: 0.75rem;
            color: #ffffff;
        }}

        .card-field {{
            font-size: 0.82rem;
            line-height: 1.5;
            margin-bottom: 0.4rem;
            color: #d1d1d6;
        }}

        .card-field strong {{
            color: var(--text-muted);
            font-weight: 500;
            margin-right: 0.2rem;
        }}

        .card-status-container {{
            margin-top: 0.9rem;
            display: flex;
        }}

        .status-badge {{
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.25rem 0.65rem;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}

        .status-done {{
            color: var(--status-done-text);
            background-color: var(--status-done-bg);
        }}

        .status-on-process {{
            color: var(--status-process-text);
            background-color: var(--status-process-bg);
        }}

        .status-not-yet {{
            color: var(--status-notyet-text);
            background-color: var(--status-notyet-bg);
        }}

        .status-not_yet {{
            color: var(--status-notyet-text);
            background-color: var(--status-notyet-bg);
        }}

        .status-default {{
            color: var(--status-default-text);
            background-color: var(--status-default-bg);
        }}

        .empty-column-message {{
            color: var(--text-muted);
            font-size: 0.8rem;
            text-align: center;
            padding: 2rem 0;
            border: 1px dashed var(--border-color);
            border-radius: 6px;
            background-color: rgba(255, 255, 255, 0.01);
        }}
    </style>
</head>
<body>
    <header>
        <h1>{title}</h1>
        <p class="subtitle">Diagram Kanban Alur SDLC Proyek Aktif</p>
    </header>
    
    <div class="kanban-board-container">
        {html_columns}
    </div>
</body>
</html>
"""

        # 5. Save HTML output
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)

        return os.path.abspath(output_path)

    def generate_image(self, records: list[ProjectRecord], output_path: str = "kanban_board.png", filter_sprint_id: str = None, base_title: str = None) -> str:
        """Generates a high-quality static PNG image of the Kanban board using Matplotlib.

        Args:
            records (list[ProjectRecord]): The parsed list of project records.
            output_path (str): The filename of the generated image. Defaults to "kanban_board.png".
            filter_sprint_id (str, optional): Filters the projects by Sprint ID.
            base_title (str, optional): The base title of the Kanban board.

        Returns:
            str: Absolute path to the generated image.
        """
        # 1. Filter by Sprint ID if provided
        base = base_title or "Project Kanban Board"
        if filter_sprint_id:
            filter_clean = str(filter_sprint_id).strip().lower()
            filtered_records = [
                r for r in records 
                if r.sprint_id and filter_clean in str(r.sprint_id).strip().lower()
            ]
            title = f"{base} - Sprint: {filter_sprint_id}"
        else:
            filtered_records = records
            title = f"{base} - Semua Proyek"

        if not filtered_records:
            raise SheetReaderError(
                f"Tidak ada data proyek untuk divisualisasikan Kanban dengan Sprint ID: '{filter_sprint_id}'"
            )

        # 2. Group projects by active stage
        columns_data: dict[str, list[dict]] = {stage: [] for stage in self.ORDERED_STAGES}
        max_tasks_in_any_column = 0

        for record in filtered_records:
            for stage_name in self.ORDERED_STAGES:
                stage = record.stages.get(stage_name)
                if stage:
                    is_active = any([stage.pic, stage.target, stage.due_date, stage.status])
                    if is_active:
                        columns_data[stage_name].append({
                            "project_name": record.project_name,
                            "pic": stage.pic or "-",
                            "target": stage.target or "",
                            "due_date": stage.due_date or "",
                            "status": stage.status or "not-yet"
                        })
                        max_tasks_in_any_column = max(max_tasks_in_any_column, len(columns_data[stage_name]))

        # 3. Create Matplotlib figure
        plt.style.use("dark_background")
        num_columns = len(self.ORDERED_STAGES)
        
        # Scale figure size: each column gets 2.2 inches width, height scales with number of cards
        fig_width = 24.5
        fig_height = max(7, 2.5 + (max_tasks_in_any_column * 2.2))
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=150)
        fig.patch.set_facecolor("#121212")
        ax.set_facecolor("#121212")
        
        # Turn off axis borders & ticks
        ax.axis("off")
        ax.set_xlim(0, num_columns)
        ax.set_ylim(0, fig_height)
        
        # 4. Draw Columns and Cards
        # The coordinates are: X from 0 to num_columns, Y from 0 to fig_height.
        # Top of the axis is Y = fig_height.
        y_header_top = fig_height - 0.8
        
        for col_idx, stage in enumerate(self.ORDERED_STAGES):
            color = self.STAGE_COLORS.get(stage, "#9e9e9e")
            tasks = columns_data[stage]
            
            # Draw Column Background
            col_bg = patches.Rectangle(
                (col_idx + 0.05, 0.2),
                0.9,
                fig_height - 1.2,
                facecolor="#1c1c1e",
                edgecolor="#2c2c2e",
                linewidth=0.8,
                zorder=1
            )
            ax.add_patch(col_bg)
            
            # Draw Column Header Colored Line
            header_line = patches.Rectangle(
                (col_idx + 0.05, y_header_top),
                0.9,
                0.05,
                facecolor=color,
                edgecolor="none",
                zorder=2
            )
            ax.add_patch(header_line)
            
            # Draw Column Header Text (Stage Name and Task Count)
            ax.text(
                col_idx + 0.1,
                y_header_top - 0.2,
                stage,
                color="#ffffff",
                fontsize=9.5,
                weight="bold",
                va="center",
                ha="left",
                zorder=3
            )
            
            # Badge showing count
            badge_box = FancyBboxPatch(
                (col_idx + 0.8, y_header_top - 0.3),
                0.12,
                0.18,
                boxstyle="round,pad=0.01,rounding_size=0.02",
                facecolor=f"{color}22",
                edgecolor="none",
                zorder=3
            )
            ax.add_patch(badge_box)
            ax.text(
                col_idx + 0.86,
                y_header_top - 0.2,
                str(len(tasks)),
                color=color,
                fontsize=8,
                weight="bold",
                va="center",
                ha="center",
                zorder=4
            )
            
            # Draw Cards for this column
            y_start = y_header_top - 0.45
            
            if not tasks:
                # Draw empty column message box
                empty_box = FancyBboxPatch(
                    (col_idx + 0.08, y_start - 0.8),
                    0.84,
                    0.6,
                    boxstyle="round,pad=0.02,rounding_size=0.04",
                    facecolor="#121212",
                    edgecolor="#2c2c2e",
                    linestyle="--",
                    linewidth=0.8,
                    zorder=2
                )
                ax.add_patch(empty_box)
                ax.text(
                    col_idx + 0.5,
                    y_start - 0.5,
                    "Tidak ada aktivitas",
                    color="#555555",
                    fontsize=8,
                    style="italic",
                    va="center",
                    ha="center",
                    zorder=3
                )
            else:
                for t in tasks:
                    # Determine card layout size dynamically based on text length
                    proj_wrapped = textwrap.wrap(t["project_name"], width=23)
                    proj_lines = len(proj_wrapped)
                    
                    target_wrapped = textwrap.wrap(t["target"], width=24) if t["target"] else []
                    target_lines = len(target_wrapped)
                    
                    # Calculate card height dynamically
                    card_h = 0.45  # Padding and project name spacing
                    card_h += proj_lines * 0.18
                    card_h += 0.16  # PIC line
                    if target_lines > 0:
                        card_h += 0.15 + (target_lines * 0.16)
                    if t["due_date"]:
                        card_h += 0.18
                    card_h += 0.28  # Status badge spacing
                    
                    # Draw Rounded Card Box (using FancyBboxPatch)
                    card_box = FancyBboxPatch(
                        (col_idx + 0.08, y_start - card_h + 0.02),
                        0.84,
                        card_h - 0.04,
                        boxstyle="round,pad=0.02,rounding_size=0.04",
                        facecolor="#2c2c2e",
                        edgecolor="#3a3a3c",
                        linewidth=0.8,
                        zorder=2
                    )
                    ax.add_patch(card_box)
                    
                    # 1. Project Name Text
                    proj_y = y_start - 0.18
                    ax.text(
                        col_idx + 0.12,
                        proj_y,
                        "\n".join(proj_wrapped),
                        color="#ffffff",
                        fontsize=8.5,
                        weight="bold",
                        linespacing=1.3,
                        va="top",
                        ha="left",
                        zorder=3
                    )
                    
                    # 2. PIC Text
                    pic_y = proj_y - (proj_lines * 0.18) - 0.08
                    ax.text(
                        col_idx + 0.12,
                        pic_y,
                        f"PIC: {t['pic']}",
                        color="#d1d1d6",
                        fontsize=7.5,
                        va="top",
                        ha="left",
                        zorder=3
                    )
                    
                    # 3. Target Text (optional)
                    if target_lines > 0:
                        target_y = pic_y - 0.18
                        ax.text(
                            col_idx + 0.12,
                            target_y,
                            f"Target: " + "\n        ".join(target_wrapped),
                            color="#aeaeb2",
                            fontsize=7.2,
                            linespacing=1.2,
                            va="top",
                            ha="left",
                            zorder=3
                        )
                        due_y_start = target_y - (target_lines * 0.16)
                    else:
                        due_y_start = pic_y
                        
                    # 4. Due Date Text (optional)
                    if t["due_date"]:
                        due_y = due_y_start - 0.18
                        ax.text(
                            col_idx + 0.12,
                            due_y,
                            f"Due: {t['due_date']}",
                            color="#aeaeb2",
                            fontsize=7.2,
                            va="top",
                            ha="left",
                            zorder=3
                        )
                        status_y_start = due_y
                    else:
                        status_y_start = due_y_start
                        
                    # 5. Status Badge
                    status_y = status_y_start - 0.28
                    status_label = t["status"]
                    status_clean = status_label.lower().strip().replace(" ", "_")
                    
                    if status_clean in ["done"]:
                        color_text = "#34c759"
                        color_bg = "#1a3b22"
                    elif status_clean in ["on-process", "on_process"]:
                        color_text = "#ff9500"
                        color_bg = "#3d2600"
                    elif status_clean in ["not-yet", "not_yet"]:
                        color_text = "#ff3b30"
                        color_bg = "#3d0f0d"
                    else:
                        color_text = "#aeaeb2"
                        color_bg = "#2c2c2e"
                        
                    # Status Badge Shape
                    status_badge = FancyBboxPatch(
                        (col_idx + 0.12, status_y),
                        0.4,
                        0.14,
                        boxstyle="round,pad=0.01,rounding_size=0.02",
                        facecolor=color_bg,
                        edgecolor="none",
                        zorder=3
                    )
                    ax.add_patch(status_badge)
                    
                    # Status Text
                    ax.text(
                        col_idx + 0.12 + 0.21,
                        status_y + 0.08,
                        status_label.upper(),
                        color=color_text,
                        fontsize=5.8,
                        weight="bold",
                        va="center",
                        ha="center",
                        zorder=4
                    )
                    
                    # Update Y tracker for the next card in this column
                    y_start -= (card_h + 0.18)

        # 5. Main Figure Title
        plt.suptitle(title, fontsize=16, color="#ffffff", weight="bold", y=0.97, ha="center")
        plt.figtext(
            0.5, 
            0.94, 
            "Diagram Kanban Alur SDLC Proyek Aktif", 
            color="#8e8e93", 
            fontsize=10, 
            ha="center"
        )
        
        plt.tight_layout()
        
        # Save output image
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
        plt.close()

        return os.path.abspath(output_path)
