# CM Broadcast Generator

Tool lokal sederhana untuk mengubah tabel jadwal kelas mingguan menjadi
broadcast WhatsApp untuk mentor dan student — tanpa mengubah format
tabel yang sudah kamu pakai, tanpa database, tanpa internet.

## Cara Menjalankan

```
pip install -r requirements-local.txt
streamlit run streamlit_app.py
```

Browser akan terbuka otomatis ke `http://localhost:8501`. Ini berjalan
sepenuhnya di laptopmu — tidak ada data yang dikirim keluar, dan tidak
ada yang tersimpan setelah tab ditutup.

## Deploy Gratis ke Vercel

Repository ini juga memiliki versi web Vercel. `index.html` adalah halaman
web-nya dan `api/index.py` adalah API generator broadcast. Versi web tidak
memerlukan Laragon, VS Code, atau server lokal setelah berhasil dideploy.

1. Pastikan file project sudah di-push ke repository GitHub
  `athyzr/TemplateChatCMDMW1`.
2. Buka `https://vercel.com` lalu login dengan GitHub.
3. Klik **Add New Project** → pilih repository tersebut → **Import**.
4. Biarkan Framework Preset **Other**, lalu klik **Deploy**.
5. Setelah selesai, buka URL `.vercel.app` yang diberikan Vercel.

Vercel Hobby cukup untuk penggunaan pribadi ringan. Tidak ada biaya selama
tidak melewati batas pemakaian gratis Vercel.

## Cara Pakai

1. Copy tabel jadwal pekan ini (dari Google Sheets, Excel, atau Markdown).
2. Paste ke text area di halaman.
3. (Opsional) isi nama kelas/batch — dipakai di kalimat pembuka broadcast mentor.
4. Klik **Generate Broadcast**.
5. Copy hasil broadcast mentor (per mentor), broadcast student, dan D-Day
  hari ini, atau
   pakai kotak **Copy All** untuk menyalin semuanya sekaligus.

Minggu depan, tinggal ganti isi text area dengan tabel yang baru dan
generate ulang.

## Format Input yang Didukung

Tool ini menerima tabel dengan 5 kolom (Mentor, Session, Materi,
Pelengkap Kelas, Link Pretest) dalam tiga bentuk:

- **Markdown** — tabel `| ... | ... |` seperti yang biasa kamu tulis,
  termasuk sel dengan `<br>` untuk baris baru di dalam sel.
- **Copy-paste dari spreadsheet** (Google Sheets / Excel) — otomatis
  terbaca sebagai tab-separated values.
- **HTML table** — tag `<table>`.

Tool otomatis mendeteksi format mana yang kamu paste; tidak perlu
mengatur apa pun.

## Aturan Parsing Penting

- **Mentor**: `Mba Naya` → confirmed. `Mas Raka -hold` → mentor "Mas
  Raka", status hold. `Tidak Ada` → session ini tidak masuk broadcast
  mentor sama sekali.
- **Session**: baris 1 = Day, baris 2 = tanggal, baris 3 = jam. Kalau
  jam kosong/`- WIB` (biasanya untuk Day-VL), jam tidak ditampilkan.
- **Pelengkap Kelas**: baris yang diawali `PG`, `AG`, `Untuk CM:`,
  `Untuk Student:` otomatis dikenali. Baris `AG untuk Day 35, Day 36,
  Day 37` berarti link AG di baris itu juga berlaku untuk Day-35,
  Day-36, Day-37 tanpa perlu ditulis ulang. Apa pun yang tidak
  dikenali tetap disimpan sebagai info tambahan — tidak pernah dibuang.
- **Link Pretest**: `Tidak Ada` → tidak ditampilkan. Kalau kolomnya
  berisi `Untuk CM: ...` / `Untuk Student: ...`, masing-masing audiens
  dapat link yang sesuai. Kalau cuma satu link, dipakai sesuai konteks
  (muncul di broadcast mentor sebagai "Pretest/CM" dan di broadcast
  student sebagai "Pretest").
- **Student tidak pernah melihat** link yang memang ditujukan "Untuk
  CM", begitu juga sebaliknya.
- Semua session dengan mentor yang sama digabung jadi **satu**
  broadcast per mentor, diurutkan berdasarkan tanggal & jam.
- Broadcast **Kelas Hari Ini** dibuat terpisah untuk student dan mentor.
  Student mendapat pre-test bila tersedia lalu link Zoom; mentor langsung
  mendapat link Zoom tanpa pre-test.
- Link Zoom D-Day yang dipakai untuk semua kelas adalah link Zoom yang sama.
- Sesi **Day-VL** tetap masuk ke broadcast jadwal pekan student.
- Kalau ada baris yang gagal dibaca, tool menampilkan peringatan untuk
  baris itu saja dan tetap memproses baris lainnya.

## Struktur Proyek

```
app.py            # UI Streamlit
parser.py         # Parsing tabel -> data session
templates.py       # Data session -> teks broadcast
utils.py           # Helper: deteksi URL, normalisasi tanggal/hari
requirements.txt
```

## Yang Sengaja Tidak Ada

Tidak ada database, tidak ada login, tidak ada API eksternal (AI,
WhatsApp, Google, dll), tidak ada penyimpanan setelah aplikasi
ditutup. Tool ini murni untuk satu pekan yang sedang dikerjakan —
minggu depan tinggal paste tabel baru.