# VaultX

**VaultX (Safe Your Account)** adalah aplikasi password manager yang dibuat menggunakan Python dan Kivy. Aplikasi ini digunakan untuk menyimpan, mengelola, dan melindungi data akun secara lebih aman.

## ✨ Fitur

- 🔐 Login dan registrasi akun VaultX
- 🔑 Menyimpan password akun
- 👁️ Menampilkan atau menyembunyikan password
- 🔒 Mengenkripsi password dan catatan
- 🖼️ Menambahkan foto pada data akun
- ⭐ Menandai akun sebagai favorit
- 🔎 Mencari data akun dengan mudah
- ✏️ Mengedit data akun
- 🗑️ Menghapus data akun
- ☁️ Menggunakan Supabase sebagai database
- 🚪 Logout tanpa menghapus data akun

## 📱 Cara Menggunakan

### 1. Membuat Akun

Saat pertama kali membuka VaultX:

1. Pilih **CREATE ACCOUNT**.
2. Masukkan email.
3. Masukkan password.
4. Konfirmasi password.
5. Tekan tombol **CREATE ACCOUNT**.
6. Jika diperlukan, lakukan verifikasi email.

Setelah akun berhasil dibuat, kembali ke halaman login dan masuk menggunakan akun tersebut.

### 2. Login

Masukkan:

- Email akun VaultX
- Password VaultX

Kemudian tekan **LOGIN**.

Jika sebelumnya sudah login dan sesi masih tersimpan, aplikasi dapat langsung membuka halaman utama.

### 3. Menambahkan Password

Pada halaman utama:

1. Tekan tombol **Add Account** atau tombol tambah.
2. Masukkan nama website/aplikasi.
3. Masukkan username atau email akun.
4. Masukkan password.
5. Tambahkan catatan jika diperlukan.
6. Pilih foto jika ingin menambahkan gambar.
7. Tekan **Save**.

Data akun akan tersimpan pada database dan password disimpan dalam bentuk terenkripsi.

### 4. Melihat Password

Pada data akun yang sudah tersimpan, gunakan tombol **Show/Hide** untuk menampilkan atau menyembunyikan password.

### 5. Mengedit Data

Pilih akun yang ingin diubah, kemudian tekan **Edit**.

Setelah selesai mengubah data, tekan **Save** untuk menyimpan perubahan.

### 6. Favorit

Gunakan tombol ⭐ pada akun untuk menandai akun sebagai favorit.

Fitur ini memudahkan pengguna menemukan akun yang sering digunakan.

### 7. Mencari Akun

Gunakan kolom pencarian pada halaman utama untuk mencari data berdasarkan informasi akun yang tersedia.

### 8. Menghapus Akun

Pilih data akun yang ingin dihapus kemudian gunakan tombol **Delete**.

> Data yang sudah dihapus sebaiknya dianggap tidak dapat dikembalikan.

### 9. Logout

Untuk keluar dari VaultX, gunakan tombol **Logout**.

Logout hanya mengakhiri sesi pengguna dan **tidak menghapus data password yang tersimpan**.

## 🛠️ Teknologi

VaultX dibuat menggunakan:

- Python
- Kivy
- Supabase
- PostgreSQL
- Cryptography / Fernet
- Plyer

## 📂 Struktur Project

```text
VaultX/
├── main.py
├── dashboard.py
├── screens.py
├── crypto_utils.py
├── supabase_client.py
├── supabase_schema.sql
├── vaultx.kv
├── requirements.txt
└── README.md

⚙️ Menjalankan di Windows

Clone repository:

git clone https://github.com/reskt48-lab/VaultX.git
cd VaultX

Buat virtual environment:

python -m venv .venv

Aktifkan:

.venv\Scripts\activate

Install dependency:

pip install -r requirements.txt

Buat file .env:

SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

Kemudian jalankan:

python main.py

🗄️ Database

VaultX menggunakan Supabase untuk menyimpan data akun pengguna dan data password.

File:

supabase_schema.sql

digunakan untuk menyiapkan struktur database yang diperlukan.

🔐 Keamanan

VaultX dirancang agar password yang disimpan tidak disimpan sebagai plaintext. Data password dan catatan dienkripsi sebelum disimpan.

Jangan memasukkan Supabase service_role key ke dalam aplikasi atau repository GitHub.

Gunakan key yang memang aman untuk aplikasi client.

📌 Status Project

VaultX masih dalam tahap pengembangan.

Fitur dan tampilan aplikasi dapat berubah pada pengembangan berikutnya.