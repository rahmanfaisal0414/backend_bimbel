# 🧠 Backend Bimbel (Manajemen Bimbel)

Ini adalah backend dari aplikasi **Manajemen Bimbel** berbasis Django REST Framework dan PostgreSQL. Berfungsi sebagai API utama untuk fitur login/signup berbasis token, reset password via email, dan manajemen data siswa/tutor/kelas.

---

## 🧩 Fitur

- 🔐 Autentikasi User (Sign Up + Login)
- 📧 Reset password via OTP ke Email
- 🧑‍🏫 Relasi data siswa, tutor, kelas, absensi
- 📌 Validasi token signup (hanya bisa daftar jika dapat token dari admin)
- 📮 SMTP email support (via Gmail SMTP)
- ⚙️ Non-managed model (import dari PostgreSQL lewat `inspectdb`)

---

## 🎨 Link Desain Figma Manajemen Bimbel

- [Desain UI Figma](https://www.figma.com/design/xJptZfx4oK4eYOSoDRPeAE/UI-UX-LMS---Gluon-IT?node-id=0-1&t=0Rk034BKqJzwQqM3-1)

---

## 🖥️ Link Frontend Manajemen Bimbel

- [Frontend Repository (Next.js)](https://github.com/rahmanfaisal0414/manajemen-bimbel)

---

## 🚀 Cara Install & Jalankan

Ikuti langkah-langkah berikut untuk setup project ini di lokal:

### 1. Clone Repository

```bash
git clone https://github.com/rahmanfaisal0414/backend_bimbel.git
```

### 2. Masuk ke Direktori Project

```bash
cd backend_bimbel
```

Pastikan di dalam folder ini ada file manage.py.

### 3. Buat dan Aktifkan Virtual Environment

```bash
python -m venv env
```

Aktifkan virtualenv:

Windows:

```bash
.\env\Scripts\activate
```

### 4. Install Dependencies

Install semua library yang dibutuhkan:

```bash
pip install django djangorestframework djangorestframework-simplejwt psycopg2-binary django-cors-headers
```

(Disarankan: setelah install, buat file requirements.txt menggunakan pip freeze > requirements.txt)

### 5. Masuk ke Direktori Django

```bash
cd bimbel_backend
```

### 6. Setup Database PostgreSQL

Project ini membutuhkan database PostgreSQL.

Setting database default (di settings.py):

```bash
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bimbel_db',
        'USER': 'postgres',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Pastikan database bimbel_db sudah dibuat di PostgreSQL kamu.

### 7. Migrasi Database

Buat struktur tabel di database:

```bash
python manage.py migrate
```

### 8. Jalankan Development Server

```bash
python manage.py runserver
```
