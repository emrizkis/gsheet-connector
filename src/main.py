import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from src.config import load_config
from src.auth.service_account import ServiceAccountCredentialProvider
from src.core import GoogleSheetReader, CachedSheetReader
from src.exceptions import GSheetConnectorError
from src.visualization.gantt import GanttChartGenerator
from src.visualization.kanban import KanbanBoardGenerator


def parse_arguments():
    """Parses command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed CLI arguments.
    """
    parser = argparse.ArgumentParser(
        description="Membaca Google Sheets & Membuat Visualisasi SDLC bertipe SOLID."
    )
    parser.add_argument(
        "mode",
        choices=["gantt", "kanban"],
        nargs="?",
        default="gantt",
        help="Mode visualisasi: 'gantt' untuk Gantt Chart (default), atau 'kanban' untuk Board Kanban."
    )
    parser.add_argument(
        "-s", "--sprint",
        type=str,
        default=None,
        help="Sprint ID untuk memfilter visualisasi (contoh: 'SP1 May', 'SP2 May'). "
             "Jika dikosongkan, akan menggunakan filter default dari file .env."
    )
    parser.add_argument(
        "-f", "--format",
        choices=["html", "image"],
        default=None,
        help="Format output: 'html' atau 'image'. Jika dikosongkan, mode gantt default ke 'image', kanban default ke 'html'."
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Hapus file cache lokal untuk memaksa pengambilan data segar dari Google API."
    )
    return parser.parse_args()


def main():
    """Main execution point of the Google Sheets Reader program.
    
    Demonstrates Dependency Injection by passing the Service Account Credential Provider
    to the Google Sheet Reader, adhering to the SOLID principles.
    
    Additionally wraps the GoogleSheetReader with a CachedSheetReader (Decorator Pattern)
    to prevent excessive API requests, and supports dynamic filtering and cache-clearing via CLI arguments.
    """
    print("=" * 60)
    print("      GOOGLE SHEETS READER & GANTT CHART GENERATOR (SOLID)      ")
    print("=" * 60)

    # Parse CLI arguments
    args = parse_arguments()

    # Logika penghapusan cache jika parameter --clear-cache disertakan
    if args.clear_cache:
        cache_file = os.path.join("data", "cache", "sheet_cache.json")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print(f"[Cache] Berhasil menghapus file cache lokal ({cache_file})!")
            except Exception as e:
                print(f"[Cache Warning] Gagal menghapus file cache lokal: {e}", file=sys.stderr)
        else:
            print("[Cache] Tidak ada file cache lokal yang tersimpan untuk dihapus.")

    try:
        # 1. Memuat konfigurasi dari file .env secara type-safe
        print("[1/5] Memuat dan memverifikasi file konfigurasi (.env)...")
        config = load_config()

        # Tentukan filter Sprint ID yang digunakan (CLI argument memiliki prioritas lebih tinggi dibanding .env)
        sprint_filter = args.sprint if args.sprint is not None else config.filter_sprint_id

        # Membuat ID unik untuk eksekusi run ini (format: YYYYMMDDHHIISS-sprint_id-id_uniq)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        sprint_suffix = f"-{sprint_filter.lower().replace(' ', '_')}" if sprint_filter else ""
        unique_token = uuid.uuid4().hex[:6]
        run_id = f"{timestamp}{sprint_suffix}-{unique_token}"

        # 2. Menginisialisasi dependency autentikasi (Dependency Injection)
        print("[2/5] Menyiapkan modul autentikasi (Service Account)...")
        credential_provider = ServiceAccountCredentialProvider(
            key_file_path=config.google_service_account_file
        )

        # 3. Menginisialisasi core reader dengan menginjeksikan dependency auth
        print("[3/5] Menyiapkan pembaca Google Sheets...")
        raw_reader = GoogleSheetReader(credential_provider=credential_provider)
        
        # Membungkus pembaca asli dengan Caching Decorator (SOLID OCP & Decorator Pattern)
        reader = CachedSheetReader(
            wrapped_reader=raw_reader,
            ttl_seconds=config.cache_ttl_seconds
        )

        # 4. Membaca data sheet menggunakan range & ID yang ditentukan (melewati cache jika masih fresh)
        print(f"[4/5] Mengambil data dari Spreadsheet ID: '{config.spreadsheet_id}'...")
        print(f"      Range Target: '{config.sheet_range}'")
        sheet_data = reader.read_sheet(
            spreadsheet_id=config.spreadsheet_id,
            range_name=config.sheet_range
        )

        # 5. Mem-parsing data ke model hierarkis terstruktur
        records = sheet_data.to_structured_records()

        # Menyimpan hasil parsing terstruktur ke file JSON lokal agar mudah dibaca
        structured_json_path = os.path.join("data", "output", f"{run_id}-projects_structured.json")
        try:
            os.makedirs(os.path.dirname(structured_json_path), exist_ok=True)
            records_serialized = [r.model_dump() for r in records]
            with open(structured_json_path, "w", encoding="utf-8") as f:
                json.dump(records_serialized, f, indent=2, ensure_ascii=False)
            print(f"[Cache/Output] Berhasil menyimpan data terstruktur ke: '{structured_json_path}'")
        except Exception as e:
            print(f"[Warning] Gagal menyimpan data terstruktur ke JSON: {e}", file=sys.stderr)

        # 6. Menampilkan hasil pembacaan
        print("\n" + "=" * 22 + " HASIL DATA SPRINT PLANNING " + "=" * 22)
        print(f"Total Proyek Ditemukan: {len(records)} baris data aktif")
        print("-" * 72)

        if not records:
            print("[Info] Tidak ada data ditemukan atau format rentang salah.")
        else:
            print("Baris Data Terstruktur (Pretty-Printed JSON per Proyek):")
            display_count = min(3, len(records))
            for idx in range(display_count):
                record = records[idx]
                record_dict = record.model_dump()
                pretty_json = json.dumps(record_dict, indent=2, ensure_ascii=False)
                
                print(f"\n[{idx+1:02d}] Proyek: {record.project_name}")
                print("-" * 50)
                print(pretty_json)
                print("-" * 50)
            
            if len(records) > display_count:
                print(f"\n... (dan {len(records) - display_count} proyek lainnya dicatat)")
        
        print("=" * 72)

        # 7. Menghasilkan visualisasi berdasarkan mode dan format yang dipilih
        output_format = args.format
        if not output_format:
            output_format = "html" if args.mode == "kanban" else "image"

        ext = "html" if output_format == "html" else "png"

        if args.mode == "kanban":
            print(f"\n[5/5] Menghasilkan visualisasi Kanban Board ({output_format.upper()})...")
            kanban_generator = KanbanBoardGenerator()
            output_file_name = os.path.join("data", "output", f"{run_id}-kanban_board.{ext}")
            
            final_path = kanban_generator.generate(
                records=records,
                output_path=output_file_name,
                filter_sprint_id=sprint_filter,
                base_title=config.kanban_title
            )
            
            print(f"\n[SUKSES] Board Kanban ({output_format.upper()}) berhasil dibuat!")
            print(f"         Filter Sprint : '{sprint_filter or 'Semua Sprint'}'")
            print(f"         Lokasi File   : {final_path}")
            print("=" * 72)
        else:
            print(f"\n[5/5] Menghasilkan visualisasi Gantt Chart ({output_format.upper()})...")
            gantt_generator = GanttChartGenerator()
            output_file_name = os.path.join("data", "output", f"{run_id}-gantt_chart.{ext}")
            
            final_path = gantt_generator.generate(
                records=records,
                output_path=output_file_name,
                filter_sprint_id=sprint_filter,
                base_title=config.gantt_title
            )
            
            print(f"\n[SUKSES] Diagram Gantt ({output_format.upper()}) berhasil dibuat!")
            print(f"         Filter Sprint : '{sprint_filter or 'Semua Sprint'}'")
            print(f"         Lokasi File   : {final_path}")
            print("=" * 72)

        # Print the machine-readable path for caller tools
        print(f"OUTPUT_PATH:{final_path}")

    except GSheetConnectorError as e:
        print(f"\n[ERROR] Kesalahan dalam proses: \n{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] Kesalahan sistem tidak terduga: \n{e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
