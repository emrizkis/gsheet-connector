import os
import sys
import shutil

def clean_project():
    print("=" * 60)
    print("      PROJECT CLEANUP UTILITY (pyclean & cache removal)      ")
    print("=" * 60)

    # Check for optional arguments
    clear_outputs = "--all" in sys.argv or "-a" in sys.argv

    # Folders to completely remove
    folders_to_remove = ["__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"]
    # File extensions to remove
    extensions_to_remove = [".pyc", ".pyo", ".pyd"]
    # Directories to skip walking
    dirs_to_skip = {".venv", "venv", ".git", ".idea", ".vscode"}

    deleted_folders_count = 0
    deleted_files_count = 0

    # 1. Walk directory and clean python caches
    current_dir = os.path.abspath(os.path.dirname(__file__))
    for root, dirs, files in os.walk(current_dir, topdown=True):
        # Modify dirs in-place to skip virtual environment and git folders
        dirs[:] = [d for d in dirs if d not in dirs_to_skip]

        # Check and remove target folders
        for d in list(dirs):
            if d in folders_to_remove:
                folder_path = os.path.join(root, d)
                try:
                    shutil.rmtree(folder_path)
                    print(f"[Delete Folder] {os.path.relpath(folder_path, current_dir)}")
                    deleted_folders_count += 1
                    dirs.remove(d)  # Don't walk inside deleted directory
                except Exception as e:
                    print(f"[Error Folder] Gagal menghapus {folder_path}: {e}")

        # Check and remove target files
        for f in files:
            _, ext = os.path.splitext(f)
            if ext in extensions_to_remove:
                file_path = os.path.join(root, f)
                try:
                    os.remove(file_path)
                    print(f"[Delete File]   {os.path.relpath(file_path, current_dir)}")
                    deleted_files_count += 1
                except Exception as e:
                    print(f"[Error File]   Gagal menghapus {file_path}: {e}")

    # 2. Clear data/cache directory
    cache_dir = os.path.join(current_dir, "data", "cache")
    if os.path.exists(cache_dir):
        for item in os.listdir(cache_dir):
            item_path = os.path.join(cache_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                print(f"[Clear Cache]  data/cache/{item}")
                deleted_files_count += 1
            except Exception as e:
                print(f"[Error Cache]  Gagal menghapus cache item {item_path}: {e}")
    else:
        print("[Info] Folder data/cache tidak ditemukan, tidak ada cache aplikasi yang dihapus.")

    # 3. Optional: Clear data/output directory (when --all or -a is passed)
    if clear_outputs:
        output_dir = os.path.join(current_dir, "data", "output")
        if os.path.exists(output_dir):
            for item in os.listdir(output_dir):
                # Let's keep gitkeep or placeholder files if any, but clear others
                item_path = os.path.join(output_dir, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                    print(f"[Clear Output] data/output/{item}")
                    deleted_files_count += 1
                except Exception as e:
                    print(f"[Error Output] Gagal menghapus output item {item_path}: {e}")
        else:
            print("[Info] Folder data/output tidak ditemukan.")

    print("-" * 60)
    print(f"Hasil Cleanup:")
    print(f"- Folder dihapus: {deleted_folders_count}")
    print(f"- Berkas dihapus: {deleted_files_count}")
    if clear_outputs:
        print(f"- Output folder (data/output/) dibersihkan.")
    else:
        print(f"- Jalankan 'python clean.py --all' jika ingin menghapus berkas di data/output/ juga.")
    print("=" * 60)

if __name__ == "__main__":
    clean_project()
