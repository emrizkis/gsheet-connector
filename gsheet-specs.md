Ringkasan Sheet "Sprint Planning"
Berdasarkan data yang dianalisis, berikut adalah ringkasan mengenai sheet Sprint Planning:
1. Header dan Struktur Kolom
Sheet ini memiliki struktur yang cukup kompleks dengan penggabungan sel (merged cells) pada baris atas untuk mengelompokkan tahapan proyek.
Header Utama (Baris 3): Berisi kategori tahapan pengembangan seperti Requirements, Technical Design, FSD, Development, SIT, UAT, Deployment, SK/E, Pilot, Release, dan Pentest.
Sub-Header (Baris 4): Setiap kategori di atas umumnya memiliki sub-kolom yang konsisten, yaitu:
PIC: Orang yang bertanggung jawab untuk tahapan tersebut.
Target: Deskripsi target atau timeline pengerjaan.
Due Date: Batas waktu penyelesaian.
Status: Status progres (contoh: done, on-process, not-yet).
Kolom Identitas (Kolom B-D):
Project Name (Kolom B): Nama proyek atau fitur yang direncanakan.
Notes (Kolom C): Catatan tambahan atau update status terkini.
Sprint ID (Kolom D): ID Sprint yang merujuk pada periode pengerjaan tertentu (misal: SP1 May).
2. Lokasi Data (Start Cell)
Header dimulai dari baris ke-3 (Cell B3 untuk Project Name).
Data Proyek dimulai dari baris ke-5 (Cell B5).
Rentang data yang terdeteksi adalah dari kolom B hingga kolom AV.
3. Dependensi ke Sheet Lain
Sheet ini berfungsi sebagai pusat koordinasi yang bergantung pada beberapa sheet pendukung:
Sprints: Kolom Sprint ID (Kolom D) merujuk pada daftar sprint di sheet Sprints untuk menentukan periode waktu.
Teams: Nama-nama yang mengisi kolom PIC di berbagai tahapan merujuk pada daftar personil di sheet Teams.
BSya Projects / Feature List: Nama proyek di kolom Project Name sinkron dengan daftar fitur besar yang ada di sheet BSya Feature List atau BSya Projects.
4. Fungsi Masing-Masing Kolom
Secara garis besar, kolom-kolom ini berfungsi untuk melakukan tracking siklus hidup pengembangan perangkat lunak (SDLC) untuk setiap fitur:
Project Name & Notes: Identifikasi apa yang dikerjakan dan kendala/update terbarunya.
Sprint ID: Menentukan kapan fitur tersebut dijadwalkan masuk ke siklus produksi.
Requirements s.d. FSD: Tahap perencanaan dan dokumentasi teknis.
Development: Tahap pengkodean oleh tim pengembang.
SIT & UAT: Tahap pengujian internal (System Integration Test) dan pengujian oleh pengguna (User Acceptance Test).
Deployment s.d. Release: Tahap implementasi ke lingkungan produksi dan peluncuran resmi.
Pentest: Tahap pengujian keamanan untuk memastikan fitur aman dari kerentanan.
Sheet ini digunakan oleh Project Manager atau Scrum Master untuk memantau bottleneck di setiap tahapan proyek secara visual.