# Google Sheets Reader & Gantt Chart Generator - SOLID Python Implementation

Repositori ini berisi program Python untuk membaca data dari Google Sheets secara aman, terstruktur, dan modular menggunakan konsep desain **SOLID** serta menghasilkan visualisasi **Gantt Chart** berdasarkan data tahapan proyek (SDLC) yang difilter oleh **Sprint ID**.

---

## 🌟 Penerapan Prinsip SOLID

Program ini dibangun dengan sangat memperhatikan arsitektur kode standar industri melalui konsep SOLID:
1. **Single Responsibility Principle (SRP)**:
   - `SheetData` hanya bertanggung jawab untuk menstrukturkan dan mem-parsing baris spreadsheet dengan *merged cells*.
   - `ServiceAccountCredentialProvider` hanya mengurusi inisialisasi autentikasi Google.
   - `GoogleSheetReader` hanya berfokus pada pengambilan data dari Google Sheets API.
   - `GanttChartGenerator` hanya bertanggung jawab menggambar visualisasi grafik Gantt.
2. **Open/Closed Principle (OCP)**:
   - Modul autentikasi menggunakan abstraksi interface `CredentialProvider`. Jika ingin beralih ke OAuth2.0 atau metode token lainnya di masa mendatang, kita dapat menambahkan kelas baru tanpa mengubah kode pembaca sheets.
3. **Liskov Substitution Principle (LSP)**:
   - Setiap turunan dari `CredentialProvider` dapat menggantikan perannya secara transparan tanpa merusak logika pembaca sheet.
4. **Interface Segregation Principle (ISP)**:
   - Pembagian interface dilakukan secara terpisah (misalnya `SheetReader` didefinisikan khusus untuk membaca), sehingga client tidak bergantung pada metode penulisan (write) jika mereka hanya butuh membaca.
5. **Dependency Inversion Principle (DIP)**:
   - `GoogleSheetReader` bergantung pada abstraksi interface `CredentialProvider` yang diinjeksikan melalui konstruktor (`Dependency Injection`), bukan pada implementasi konkret tertentu.

---

## 🛠️ Langkah Instalasi & Persiapan

### 1. Klon / Buka Workspace & Persiapkan Virtual Environment
Virtual environment sudah dibuat dan dependensi telah diinstal oleh sistem. Untuk mengaktifkan dan menginstal ulang (jika diperlukan):

**Windows (PowerShell):**
```powershell
# Membuat virtual environment (jika belum ada)
python -m venv .venv

# Mengaktifkan virtual environment
.venv\Scripts\Activate.ps1

# Menginstal dependensi
pip install -r requirements.txt
```

---

## 🔑 Cara Mendapatkan Kredensial Google Sheets (Service Account)

Karena Anda belum memiliki kredensial Google Cloud, ikuti langkah-langkah mudah berikut untuk membuatnya secara gratis:

### Langkah A: Membuat Google Cloud Project & Aktifkan API
1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. Login menggunakan akun Google Anda.
3. Di pojok kiri atas, klik dropdown project lalu pilih **"New Project"**. Beri nama project Anda lalu klik **Create**.
4. Setelah project berhasil dibuat, pastikan project tersebut terpilih di dropdown header.
5. Pada kolom pencarian di bagian atas, cari **"Google Sheets API"**.
6. Klik pada hasil pencarian tersebut, lalu klik tombol **Enable**.

### Langkah B: Membuat Service Account & Mengunduh Kunci JSON
1. Di bilah menu sebelah kiri, masuk ke menu **IAM & Admin** > **Service Accounts**.
2. Klik tombol **"+ Create Service Account"** di bagian atas.
3. Isi detail Service Account:
   - **Service account name**: misal `gsheet-reader`.
   - Klik **Create and Continue**.
   - Untuk langkah Role/Permissions dan User Access, klik langsung **Done** (bisa dilewati).
4. Anda akan melihat Service Account baru di daftar. **Salin alamat email** Service Account tersebut (contoh: `gsheet-reader@xxxxx.iam.gserviceaccount.com`).
5. Klik ikon **tiga titik (Actions)** di sebelah kanan Service Account yang baru dibuat, lalu pilih **Manage Keys**.
6. Klik **Add Key** > **Create new key**.
7. Pilih format **JSON** lalu klik **Create**.
8. File kunci JSON Anda akan otomatis terunduh ke komputer Anda. 
9. **Pindahkan** file JSON yang terunduh tersebut ke folder root project ini (`c:\Users\mikonku\Documents\Projects\python\gsheet-connectors`) dan ganti namanya menjadi **`credentials.json`**.

### Langkah C: Membagikan Google Sheet Anda ke Service Account
Service Account bertindak seperti pengguna virtual. Agar ia bisa membaca spreadsheet Anda:
1. Buka Google Sheet yang ingin Anda baca di browser.
2. Klik tombol **Share (Bagikan)** di pojok kanan atas.
3. **Tempel (paste) alamat email** Service Account yang disalin pada Langkah B nomor 4.
4. Atur hak akses sebagai **Viewer (Pengakses lihat-saja)**.
5. Hapus centang "Notify people" agar tidak mengirim email notifikasi, lalu klik **Share (Bagikan)**.

---

## ⚙️ Konfigurasi File `.env`

Ubah isi file `.env` di folder root project Anda dengan informasi spreadsheet Anda:

```env
# Path ke file JSON kredensial Google Service Account yang diunduh
GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json

# ID Google Sheet yang ingin dibaca (terdapat pada URL sheet Anda)
# Contoh URL: https://docs.google.com/spreadsheets/d/ID_INI_YANG_DISALIN/edit
SPREADSHEET_ID=YOUR_SPREADSHEET_ID_HERE

# Range data yang ingin dibaca (disesuaikan untuk baris header tingkat atas)
SHEET_RANGE="'Sprint Planning'!B3:AV100"

# Sprint ID yang ingin divisualisasikan (contoh: "SP1 May" atau "SP2 May")
# Kosongkan jika ingin memvisualisasikan seluruh proyek tanpa filter
FILTER_SPRINT_ID=SP1 May
```

---

## 🚀 Cara Menjalankan Program & Membuat Visualisasi (Gantt & Kanban)

Setelah file `.env` dikonfigurasi dan file `credentials.json` diletakkan di root project, jalankan perintah berikut menggunakan *virtual environment* Python di terminal Anda:

**Windows (PowerShell):**
```powershell
# 1. Menghasilkan Diagram Gantt (Default format: image/PNG)
.venv\Scripts\python -m src.main gantt -s "SP2 May"

# 2. Menghasilkan Board Kanban (Default format: html)
.venv\Scripts\python -m src.main kanban -s "SP2 May"

# 3. Memilih format output secara eksplisit (-f atau --format)
# Membuat Gantt Chart dalam format HTML interaktif:
.venv\Scripts\python -m src.main gantt -f html -s "SP2 May"

# Membuat Kanban Board dalam format Gambar (PNG):
.venv\Scripts\python -m src.main kanban -f image -s "SP2 May"

# Menjalankan tanpa filter (menggunakan default FILTER_SPRINT_ID dari .env)
.venv\Scripts\python -m src.main gantt

# Menjalankan sambil menghapus cache lokal (memaksa fetch data segar dari Google Sheets)
.venv\Scripts\python -m src.main kanban --clear-cache -s "SP2 May"
```

---

## 📂 Struktur Output & Folder Sementara (Industry Standard)

Program ini merapikan semua berkas sementara dan keluaran ke dalam folder `data/` di root proyek agar direktori utama tetap bersih:

```text
gsheet-connectors/
├── data/
│   ├── cache/
│   │   └── sheet_cache.json            # File cache lokal berisi data mentah dari API Google Sheets
│   └── output/
│       ├── YYYYMMDDHHIISS-[sprint]-[id_uniq]-projects_structured.json    # Ekspor data proyek terstruktur (nested JSON)
│       ├── YYYYMMDDHHIISS-[sprint]-[id_uniq]-gantt_chart.[png|html]      # Visualisasi diagram Gantt (Format Gambar / HTML)
│       └── YYYYMMDDHHIISS-[sprint]-[id_uniq]-kanban_board.[html|png]     # Visualisasi Board Kanban (Format HTML / Gambar)
```

> [!NOTE]
> Nama berkas keluaran di `data/output/` bersifat unik menggunakan format stempel waktu (`YYYYMMDDHHIISS`), nama sprint, dan token unik (`id_uniq`). Hal ini mencegah hasil eksekusi menimpa (*overwrite*) hasil sebelumnya dan mempermudah pelacakan secara kronologis. Untuk melihat visualisasi format **HTML**, Anda tinggal membuka file `.html` yang dihasilkan langsung di browser pilihan Anda (klik ganda pada file).
> 
> Program ini juga akan mencetak baris mesin-readable `OUTPUT_PATH:<path_lengkap>` di baris terakhir output terminal. Baris ini dapat digunakan oleh sistem otomatisasi (seperti Open Claw) untuk menangkap lokasi file keluaran secara tepat sebelum mengirimkannya via email atau memprosesnya lebih lanjut.

---

## 📅 Logika Penentuan Tanggal Mulai (Start Date)

Karena Google Sheet sumber hanya menyediakan kolom `Due Date` untuk setiap tahapan, program menghitung `Start Date` (tanggal mulai) tahapan secara otomatis dengan logika berikut:

1. **Tahap Aktif Pertama (`i == 0`):**
   * **Logika:** Disetel default **7 hari sebelum `Due Date`** tahap tersebut.
   * **Contoh:** Jika tahap *Requirements* selesai 31 Mei, maka tanggal mulainya dihitung tanggal 24 Mei.
2. **Tahap Aktif Selanjutnya (`i > 0`):**
   * **Logika:** Diambil dari **`Due Date` tahapan aktif sebelumnya** (asumsi tahap baru dapat dimulai setelah tahap sebelumnya selesai).
   * **Contoh:** Jika tahap *Requirements* selesai 31 Mei, maka tahap *Development* dimulai tanggal 31 Mei.
3. **Pengaman Durasi Negatif (Fallback):**
   * **Logika:** Jika tanggal dalam spreadsheet tidak kronologis (misalnya *Development* diatur selesai 30 Mei sedangkan *Requirements* baru selesai 31 Mei), sistem otomatis mengatur tanggal mulai menjadi **1 hari sebelum `Due Date`** tahap saat ini.
   * **Tujuan:** Mencegah visualisasi durasi pengerjaan yang minus (mundur ke belakang) sehingga diagram batang Gantt tetap terlukis dengan durasi minimal 1 hari.

---

## 🧹 Pembersihan Berkas Cache & Temporary (pyclean)

Untuk menjaga agar direktori server tetap bersih dari berkas cache kompilasi Python (`__pycache__`, `.pyc`, dll.) serta seluruh file cache data Google Sheets lokal (`data/cache/`), Anda dapat menjalankan skrip utilitas pembersihan berikut:

**Windows (PowerShell):**
```powershell
# 1. Bersihkan bytecode Python dan cache Google Sheet lokal
.venv\Scripts\python clean.py

# 2. Bersihkan semuanya (termasuk hasil visualisasi lama di data/output/)
.venv\Scripts\python clean.py --all
```

"# gsheet-connector" 
