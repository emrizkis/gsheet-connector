import os
from datetime import timedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from src.models.sheet_data import ProjectRecord
from src.exceptions import SheetReaderError


class GanttChartGenerator:
    """Generates Gantt Charts from ProjectRecord lists.
    
    Adheres to the Single Responsibility Principle (SRP) by focusing strictly
    on data visualization, separate from fetching or parsing.
    """

    ORDERED_STAGES = [
        "Requirements", "Technical Design", "FSD", "Development",
        "SIT", "UAT", "Deployment", "SK/E", "Pilot", "Release", "Pentest"
    ]

    # Sleek dark-mode compatible palette for various SDLC stages
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

    def generate(self, records: list[ProjectRecord], output_path: str = "gantt_chart.png", filter_sprint_id: str = None, base_title: str = None) -> str:
        """Generates a Gantt chart. Automatically chooses HTML or Image format based on file extension."""
        if output_path.lower().endswith(".html") or output_path.lower().endswith(".htm"):
            return self.generate_html(records, output_path, filter_sprint_id, base_title)
        return self.generate_image(records, output_path, filter_sprint_id, base_title)

    def generate_image(self, records: list[ProjectRecord], output_path: str = "gantt_chart.png", filter_sprint_id: str = None, base_title: str = None) -> str:
        """Generates a highly readable Gantt chart where each stage has its own row,
        grouped by Project Name. Places the Project Name on its own dedicated header row
        (with no bar segment) to completely prevent overlapping with stage bars.

        Args:
            records (list[ProjectRecord]): The parsed list of project records.
            output_path (str): The filename of the generated image. Defaults to "gantt_chart.png".
            filter_sprint_id (str, optional): Filters the projects by Sprint ID.
            base_title (str, optional): The base title of the Gantt chart.

        Returns:
            str: Absolute path to the generated Gantt chart image.

        Raises:
            SheetReaderError: If there's no data to plot or rendering fails.
        """
        # 1. Filter by Sprint ID if provided (using case-insensitive substring matching)
        base = base_title or "Project Gantt Chart"
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
                f"Tidak ada data proyek untuk divisualisasikan dengan Sprint ID: '{filter_sprint_id}'"
            )

        # 2. Find the absolute maximum due date in the filtered records to represent the "Sprint End"
        all_dates = []
        for record in filtered_records:
            for stage in record.stages.values():
                if stage.due_date:
                    parsed = pd.to_datetime(stage.due_date, errors="coerce")
                    if not pd.isna(parsed):
                        all_dates.append(parsed)
        
        # Default sprint end date is max date found, or today + 14 days if none found
        sprint_end_date = max(all_dates) if all_dates else pd.to_datetime("today") + timedelta(days=14)

        # 3. Extract timelines for active stages
        tasks = []
        for record in filtered_records:
            proj_name = record.project_name
            active_stages_with_dates = []

            # Gather all stages for this project
            for stage_name in self.ORDERED_STAGES:
                stage = record.stages.get(stage_name)
                if stage:
                    # A stage is considered active if at least one field is filled
                    is_active = any([stage.pic, stage.target, stage.due_date, stage.status])
                    
                    if is_active:
                        is_date_fallback = False
                        parsed_date = pd.to_datetime(stage.due_date, errors="coerce") if stage.due_date else pd.NaT
                        
                        # Fallback empty due date to the end of the sprint
                        if pd.isna(parsed_date):
                            parsed_date = sprint_end_date
                            is_date_fallback = True

                        active_stages_with_dates.append({
                            "stage_name": stage_name,
                            "due_date": parsed_date,
                            "pic": stage.pic or "",
                            "is_fallback": is_date_fallback
                        })

            # Sort active stages chronologically by their order in ORDERED_STAGES
            active_stages_with_dates.sort(
                key=lambda x: self.ORDERED_STAGES.index(x["stage_name"])
            )

            # Determine start dates and durations
            for i, stage_info in enumerate(active_stages_with_dates):
                stage_name = stage_info["stage_name"]
                end_date = stage_info["due_date"]

                # Start date of a stage is the due date of the previous active stage
                if i > 0:
                    start_date = active_stages_with_dates[i - 1]["due_date"]
                    # If start date and end date are the same, give it 1 day duration for visibility
                    if start_date == end_date:
                        start_date = start_date - timedelta(days=1)
                else:
                    # Default duration for the first stage is 7 days before due date
                    start_date = end_date - timedelta(days=7)

                # Avoid zero or negative durations
                if start_date >= end_date:
                    start_date = end_date - timedelta(days=1)

                tasks.append({
                    "Project": proj_name,
                    "Stage": stage_name,
                    "Start": start_date,
                    "End": end_date,
                    "PIC": stage_info["pic"],
                    "IsFallback": stage_info["is_fallback"]
                })

        if not tasks:
            raise SheetReaderError(
                f"Tidak ada data tanggal (due date) yang valid untuk divisualisasikan pada Sprint: '{filter_sprint_id}'"
            )

        # 4. Group and sort tasks by Project, then by Stage order
        df_raw = pd.DataFrame(tasks)
        
        # Determine chronological start for each project to sort the project groups
        proj_min_starts = df_raw.groupby("Project")["Start"].min().to_dict()
        sorted_projects = sorted(proj_min_starts.keys(), key=lambda x: proj_min_starts[x])

        # Construct final ordered rows, inserting header rows for each project
        ordered_rows = []
        for proj in sorted_projects:
            proj_tasks = df_raw[df_raw["Project"] == proj].copy()
            # Sort the tasks of this project chronologically by Stage Order
            proj_tasks["stage_idx"] = proj_tasks["Stage"].apply(lambda s: self.ORDERED_STAGES.index(s))
            proj_tasks = proj_tasks.sort_values(by="stage_idx")
            
            # Add dedicated project header row (no bar segment)
            ordered_rows.append({
                "Project": proj,
                "Stage": "",
                "Start": pd.NaT,
                "End": pd.NaT,
                "PIC": "",
                "IsFallback": False,
                "IsHeader": True
            })
            
            # Add the actual project stage rows
            for row in proj_tasks.itertuples():
                ordered_rows.append({
                    "Project": row.Project,
                    "Stage": row.Stage,
                    "Start": row.Start,
                    "End": row.End,
                    "PIC": row.PIC,
                    "IsFallback": row.IsFallback,
                    "IsHeader": False
                })

        df = pd.DataFrame(ordered_rows)

        # 5. Generate the Matplotlib plot using a modern dark design
        plt.style.use("dark_background")
        
        num_tasks = len(df)
        # Set dynamic figure height (each task gets its own row now, so we need a taller figure)
        fig_height = max(6, num_tasks * 0.45)
        fig, ax = plt.subplots(figsize=(15, fig_height), dpi=150)

        # UI Color details
        fig.patch.set_facecolor("#121212")
        ax.set_facecolor("#1c1c1c")
        ax.tick_params(colors="#e0e0e0", labelsize=10)
        ax.xaxis.label.set_color("#e0e0e0")
        ax.yaxis.label.set_color("#e0e0e0")
        
        # Plot horizontal bar segments for each task
        y_labels = []
        project_boundary_indices = []

        for idx, row in enumerate(df.itertuples()):
            if row.IsHeader:
                # Add project header label
                short_project = row.Project[:35] + "..." if len(row.Project) > 38 else row.Project
                y_labels.append(f"■ {short_project.upper()}")
                
                # Draw project separator line above the header (except for the first project)
                if idx > 0:
                    project_boundary_indices.append(idx - 0.5)
                continue

            color = self.STAGE_COLORS.get(row.Stage, "#9e9e9e")
            duration = (row.End - row.Start).days
            
            # Draw the horizontal bar segment
            ax.barh(
                y=idx,
                width=duration,
                left=row.Start,
                color=color,
                edgecolor="#1c1c1c",
                height=0.6,
                alpha=0.95
            )
            
            # Format due date string
            due_str = row.End.strftime("%d %b")
            if row.IsFallback:
                due_str += " (Sprint End)"
                
            # Construct text label
            if row.PIC:
                label_text = f"{row.PIC} [Due: {due_str}]"
            else:
                label_text = f"[Due: {due_str}]"
            
            bar_center_x = row.Start + timedelta(days=duration / 2)

            # If the duration bar is wide enough, put the text inside. Otherwise, put it beside.
            # 7 days or more is generally wide enough for PIC [Due: Date] text in a 15-inch figure
            if duration >= 7:
                ax.text(
                    x=bar_center_x,
                    y=idx,
                    s=label_text,
                    va="center",
                    ha="center",
                    color="#121212", # Dark text for readability on soft pastel colors
                    fontsize=8,
                    weight="bold"
                )
            else:
                # Narrow bars: place labels to the right of the bar segment
                ax.text(
                    x=row.End + timedelta(days=0.5),
                    y=idx,
                    s=label_text,
                    va="center",
                    ha="left",
                    color=color, # Same color as the bar for context
                    fontsize=8,
                    weight="semibold"
                )

            # Sub-elements get just the stage name (indented for clean visual hierarchy)
            y_labels.append(f"   ↳ {row.Stage}")

        # Draw project separator lines
        for boundary in project_boundary_indices:
            ax.axhline(
                y=boundary,
                color="#444444",
                linestyle="--",
                linewidth=0.8,
                alpha=0.7
            )

        # Format Y-Axis (Projects and Stages)
        ax.set_yticks(range(num_tasks))
        ax.set_yticklabels(y_labels)
        
        # Apply custom styling for contrast between project rows and stage rows
        for idx, tick in enumerate(ax.get_yticklabels()):
            is_header = df.loc[idx, "IsHeader"]
            if is_header:
                tick.set_color("#ffffff")       # Bright white for project header row
                tick.set_fontsize(9.5)
                tick.set_weight("bold")
            else:
                tick.set_color("#888888")       # Soft muted grey for sub-stages
                tick.set_fontsize(8.5)
                tick.set_weight("normal")

        ax.invert_yaxis()  # Earliest projects and stages at the top

        # Format X-Axis (Dates)
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
        
        # Set dynamic major locator based on the date span
        date_min, date_max = df["Start"].min(), df["End"].max()
        day_span = (date_max - date_min).days
        if day_span > 60:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
        else:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
            
        # Pad the X-axis limits to prevent text labels on the right from being cut off
        padding_days = max(5, int(day_span * 0.18))
        ax.set_xlim(date_min - timedelta(days=2), date_max + timedelta(days=padding_days))
            
        plt.xticks(rotation=20)

        # Grid lines (vertical week dividers)
        ax.grid(axis="x", linestyle=":", alpha=0.15, color="#ffffff")

        # Title (with increased padding to avoid overlapping the legend)
        ax.set_title(title, fontsize=15, color="#ffffff", pad=70, weight="bold")

        # Custom Legend
        present_stages = df["Stage"].unique()
        legend_handles = []
        for stage in self.ORDERED_STAGES:
            if stage in present_stages:
                legend_handles.append(
                    plt.Line2D([0], [0], color=self.STAGE_COLORS[stage], lw=8, label=stage)
                )

        ax.legend(
            handles=legend_handles,
            loc="lower center",          # Grow upwards from anchor
            bbox_to_anchor=(0.5, 1.02),  # Sit just above the axis
            ncol=min(10, len(legend_handles)), # Increase columns to keep it in a single row
            fontsize=9,
            facecolor="#121212",
            edgecolor="#2a2a2a"
        )

        # Add minor border padding (using -1.5 at the top to prevent legend/title overlap)
        # We set the limits in inverted order to preserve the y-axis inversion.
        ax.set_ylim(num_tasks - 0.4, -1.5)
        
        plt.tight_layout()
        
        # Save output image
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
        plt.close()

        return os.path.abspath(output_path)

    def generate_html(self, records: list[ProjectRecord], output_path: str = "gantt_chart.html", filter_sprint_id: str = None, base_title: str = None) -> str:
        """Generates a highly readable HTML Gantt chart.

        Args:
            records (list[ProjectRecord]): The parsed list of project records.
            output_path (str): The filename of the generated HTML. Defaults to "gantt_chart.html".
            filter_sprint_id (str, optional): Filters the projects by Sprint ID.
            base_title (str, optional): The base title of the Gantt chart.

        Returns:
            str: Absolute path to the generated Gantt HTML file.
        """
        # 1. Filter by Sprint ID if provided (using case-insensitive substring matching)
        base = base_title or "Project Gantt Chart"
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
                f"Tidak ada data proyek untuk divisualisasikan dengan Sprint ID: '{filter_sprint_id}'"
            )

        # 2. Find the absolute maximum due date in the filtered records to represent the "Sprint End"
        all_dates = []
        for record in filtered_records:
            for stage in record.stages.values():
                if stage.due_date:
                    parsed = pd.to_datetime(stage.due_date, errors="coerce")
                    if not pd.isna(parsed):
                        all_dates.append(parsed)
        
        # Default sprint end date is max date found, or today + 14 days if none found
        sprint_end_date = max(all_dates) if all_dates else pd.to_datetime("today") + timedelta(days=14)

        # 3. Extract timelines for active stages
        tasks = []
        for record in filtered_records:
            proj_name = record.project_name
            active_stages_with_dates = []

            # Gather all stages for this project
            for stage_name in self.ORDERED_STAGES:
                stage = record.stages.get(stage_name)
                if stage:
                    # A stage is considered active if at least one field is filled
                    is_active = any([stage.pic, stage.target, stage.due_date, stage.status])
                    
                    if is_active:
                        is_date_fallback = False
                        parsed_date = pd.to_datetime(stage.due_date, errors="coerce") if stage.due_date else pd.NaT
                        
                        # Fallback empty due date to the end of the sprint
                        if pd.isna(parsed_date):
                            parsed_date = sprint_end_date
                            is_date_fallback = True

                        active_stages_with_dates.append({
                            "stage_name": stage_name,
                            "due_date": parsed_date,
                            "pic": stage.pic or "",
                            "is_fallback": is_date_fallback
                        })

            # Sort active stages chronologically by their order in ORDERED_STAGES
            active_stages_with_dates.sort(
                key=lambda x: self.ORDERED_STAGES.index(x["stage_name"])
            )

            # Determine start dates and durations
            for i, stage_info in enumerate(active_stages_with_dates):
                stage_name = stage_info["stage_name"]
                end_date = stage_info["due_date"]

                # Start date of a stage is the due date of the previous active stage
                if i > 0:
                    start_date = active_stages_with_dates[i - 1]["due_date"]
                    # If start date and end date are the same, give it 1 day duration for visibility
                    if start_date == end_date:
                        start_date = start_date - timedelta(days=1)
                else:
                    # Default duration for the first stage is 7 days before due date
                    start_date = end_date - timedelta(days=7)

                # Avoid zero or negative durations
                if start_date >= end_date:
                    start_date = end_date - timedelta(days=1)

                tasks.append({
                    "Project": proj_name,
                    "Stage": stage_name,
                    "Start": start_date,
                    "End": end_date,
                    "PIC": stage_info["pic"],
                    "IsFallback": stage_info["is_fallback"]
                })

        if not tasks:
            raise SheetReaderError(
                f"Tidak ada data tanggal (due date) yang valid untuk divisualisasikan pada Sprint: '{filter_sprint_id}'"
            )

        # 4. Group and sort tasks by Project, then by Stage order
        df_raw = pd.DataFrame(tasks)
        
        # Determine chronological start for each project to sort the project groups
        proj_min_starts = df_raw.groupby("Project")["Start"].min().to_dict()
        sorted_projects = sorted(proj_min_starts.keys(), key=lambda x: proj_min_starts[x])

        # Construct final ordered rows, inserting header rows for each project
        ordered_rows = []
        for proj in sorted_projects:
            proj_tasks = df_raw[df_raw["Project"] == proj].copy()
            # Sort the tasks of this project chronologically by Stage Order
            proj_tasks["stage_idx"] = proj_tasks["Stage"].apply(lambda s: self.ORDERED_STAGES.index(s))
            proj_tasks = proj_tasks.sort_values(by="stage_idx")
            
            # Add dedicated project header row (no bar segment)
            ordered_rows.append({
                "Project": proj,
                "Stage": "",
                "Start": pd.NaT,
                "End": pd.NaT,
                "PIC": "",
                "IsFallback": False,
                "IsHeader": True
            })
            
            # Add the actual project stage rows
            for row in proj_tasks.itertuples():
                ordered_rows.append({
                    "Project": row.Project,
                    "Stage": row.Stage,
                    "Start": row.Start,
                    "End": row.End,
                    "PIC": row.PIC,
                    "IsFallback": row.IsFallback,
                    "IsHeader": False
                })

        df = pd.DataFrame(ordered_rows)

        # Find min and max dates across stages to bound our timeline
        valid_starts = df["Start"].dropna()
        valid_ends = df["End"].dropna()
        if valid_starts.empty or valid_ends.empty:
            raise SheetReaderError("Tidak ada data tanggal yang valid untuk memetakan timeline.")
        date_min = valid_starts.min()
        date_max = valid_ends.max()
        
        # Pad the timeline slightly at start and end
        date_min = date_min - timedelta(days=2)
        date_max = date_max + timedelta(days=5)
        total_days = (date_max - date_min).days
        if total_days <= 0:
            total_days = 1

        # Generate tick dates (every 7 days)
        ticks = []
        curr_date = date_min
        while curr_date <= date_max:
            ticks.append(curr_date)
            curr_date += timedelta(days=7)
        if not ticks or (date_max - ticks[-1]).days > 2:
            ticks.append(date_max)

        # Generate HTML rows
        html_sidebar_rows = []
        html_timeline_rows = []

        # Background grid vertical lines
        grid_lines_html = ""
        for tick in ticks:
            tick_percent = ((tick - date_min).days / total_days) * 100
            grid_lines_html += f'<div class="gantt-grid-line" style="left: {tick_percent}%;"></div>\n'

        # Headers
        timeline_ticks_html = ""
        for tick in ticks:
            tick_percent = ((tick - date_min).days / total_days) * 100
            formatted_date = tick.strftime("%d %b %y")
            timeline_ticks_html += f'<div class="timeline-tick-label" style="left: {tick_percent}%;">{formatted_date}</div>\n'

        for idx, row in enumerate(df.itertuples()):
            if row.IsHeader:
                # Sidebar project header row
                short_project = row.Project
                html_sidebar_rows.append(f"""
                <div class="sidebar-row sidebar-row-header" title="{row.Project}">
                    ■ {short_project.upper()}
                </div>
                """)
                # Timeline project header row (empty timeline space, maybe separator)
                html_timeline_rows.append(f"""
                <div class="timeline-row timeline-row-header">
                    <!-- Project header separator background -->
                    <div class="timeline-header-line"></div>
                </div>
                """)
            else:
                # Sidebar stage row
                html_sidebar_rows.append(f"""
                <div class="sidebar-row sidebar-row-stage" title="{row.Stage}">
                    ↳ {row.Stage}
                </div>
                """)

                # Timeline stage row with bar
                color = self.STAGE_COLORS.get(row.Stage, "#9e9e9e")
                duration = (row.End - row.Start).days
                left_percent = ((row.Start - date_min).days / total_days) * 100
                width_percent = (duration / total_days) * 100

                due_str = row.End.strftime("%d %b")
                if row.IsFallback:
                    due_str += " (Sprint End)"
                
                label_text = f"{row.PIC} [Due: {due_str}]" if row.PIC else f"[Due: {due_str}]"

                # Check if width is small (< 15%) to place label outside
                label_outside_class = "bar-label-outside" if width_percent < 15 else ""
                label_color_style = f"color: {color};" if width_percent < 15 else ""

                html_timeline_rows.append(f"""
                <div class="timeline-row">
                    <div class="gantt-bar-container">
                        <div class="gantt-bar" style="left: {left_percent}%; width: {width_percent}%; background-color: {color};" title="{row.Stage}: {label_text}">
                            <span class="bar-label {label_outside_class}" style="{label_color_style}">{label_text}</span>
                        </div>
                    </div>
                </div>
                """)

        # Custom legend items
        present_stages = df["Stage"].unique()
        legend_html = ""
        for stage in self.ORDERED_STAGES:
            if stage in present_stages:
                color = self.STAGE_COLORS[stage]
                legend_html += f"""
                <div class="legend-item">
                    <span class="legend-dot" style="background-color: {color};"></span>
                    <span class="legend-label">{stage}</span>
                </div>
                """

        # Build full HTML
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
            --container-bg: #1c1c1e;
            --cell-bg: #2c2c2e;
            --text-color: #f5f5f7;
            --text-muted: #8e8e93;
            --border-color: #3a3a3c;
            --shadow-color: rgba(0, 0, 0, 0.4);
            --header-bg: rgba(255, 255, 255, 0.02);
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

        .gantt-wrapper {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background-color: var(--container-bg);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 12px var(--shadow-color);
            overflow: hidden;
            margin-bottom: 2rem;
        }}

        .gantt-chart-table {{
            display: flex;
            width: 100%;
            overflow: hidden;
            position: relative;
        }}

        .gantt-sidebar-column {{
            flex: 0 0 280px;
            background-color: var(--container-bg);
            border-right: 1px solid var(--border-color);
            z-index: 10;
            position: relative;
        }}

        .gantt-timeline-column-wrapper {{
            flex: 1;
            overflow-x: auto;
            position: relative;
        }}

        .gantt-timeline-column-wrapper::-webkit-scrollbar {{
            height: 8px;
        }}
        .gantt-timeline-column-wrapper::-webkit-scrollbar-track {{
            background: var(--container-bg);
        }}
        .gantt-timeline-column-wrapper::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 4px;
        }}
        .gantt-timeline-column-wrapper::-webkit-scrollbar-thumb:hover {{
            background: var(--text-muted);
        }}

        .gantt-timeline-content {{
            position: relative;
            min-width: 900px;
        }}

        /* Row configurations */
        .gantt-cell.header-cell {{
            height: 48px;
            display: flex;
            align-items: center;
            padding: 0 1rem;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            color: var(--text-color);
            background-color: var(--header-bg);
            border-bottom: 1px solid var(--border-color);
        }}

        .sidebar-row {{
            height: 40px;
            display: flex;
            align-items: center;
            padding: 0 1rem;
            font-size: 0.85rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .sidebar-row-header {{
            height: 40px;
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            color: #ffffff;
            font-size: 0.9rem;
            background-color: rgba(255, 255, 255, 0.01);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            border-top: 1px solid rgba(255, 255, 255, 0.03);
        }}

        .sidebar-row-stage {{
            color: #aeaeb2;
            padding-left: 1.5rem;
        }}

        .gantt-timeline-header-row {{
            height: 48px;
            position: relative;
            background-color: var(--header-bg);
            border-bottom: 1px solid var(--border-color);
        }}

        .timeline-tick-label {{
            position: absolute;
            top: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--text-muted);
            white-space: nowrap;
        }}

        .gantt-grid-background {{
            position: absolute;
            top: 48px;
            bottom: 0;
            left: 0;
            right: 0;
            pointer-events: none;
            z-index: 1;
        }}

        .gantt-grid-line {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 1px;
            background-color: rgba(255, 255, 255, 0.04);
            border-left: 1px dashed rgba(255, 255, 255, 0.06);
        }}

        .timeline-rows-container {{
            position: relative;
            z-index: 2;
        }}

        .timeline-row {{
            height: 40px;
            position: relative;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            display: flex;
            align-items: center;
        }}

        .timeline-row-header {{
            background-color: rgba(255, 255, 255, 0.01);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            border-top: 1px solid rgba(255, 255, 255, 0.03);
        }}

        .timeline-header-line {{
            width: 100%;
            height: 1px;
            background: linear-gradient(90deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0) 100%);
        }}

        .gantt-bar-container {{
            position: relative;
            width: 100%;
            height: 24px;
        }}

        .gantt-bar {{
            position: absolute;
            height: 100%;
            border-radius: 4px;
            display: flex;
            align-items: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }}

        .gantt-bar:hover {{
            transform: scaleY(1.08);
            filter: brightness(1.15);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
            z-index: 5;
        }}

        .bar-label {{
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            white-space: nowrap;
            font-size: 0.75rem;
            font-weight: 700;
            color: #121212;
            pointer-events: none;
        }}

        .bar-label-outside {{
            left: 102%;
            transform: none;
            font-weight: 600;
            background-color: var(--container-bg);
            padding: 0.1rem 0.3rem;
            border-radius: 2px;
        }}

        /* Legend container */
        .gantt-legend {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 1.2rem;
            padding: 1rem;
            background-color: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}

        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
            display: inline-block;
        }}

        .legend-label {{
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-color);
        }}
    </style>
</head>
<body>
    <header>
        <h1>{title}</h1>
        <p class="subtitle">Diagram Timeline Alur SDLC Proyek Aktif</p>
    </header>
    
    <div class="gantt-wrapper">
        <div class="gantt-chart-table">
            <div class="gantt-sidebar-column">
                <div class="gantt-cell header-cell">Proyek & Tahapan</div>
                {"".join(html_sidebar_rows)}
            </div>
            
            <div class="gantt-timeline-column-wrapper">
                <div class="gantt-timeline-content">
                    <!-- Timeline Header -->
                    <div class="gantt-timeline-header-row">
                        {timeline_ticks_html}
                    </div>
                    
                    <!-- Background Grid -->
                    <div class="gantt-grid-background">
                        {grid_lines_html}
                    </div>
                    
                    <!-- Rows with Bars -->
                    <div class="timeline-rows-container">
                        {"".join(html_timeline_rows)}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Legend -->
    <div class="gantt-legend">
        {legend_html}
    </div>
</body>
</html>
"""

        # 5. Save HTML output
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)

        return os.path.abspath(output_path)
