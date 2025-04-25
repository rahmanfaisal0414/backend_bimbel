# 🧠 Backend Bimbel (Manajemen Bimbel)

Ini adalah backend dari aplikasi **Manajemen Bimbel** berbasis Django REST Framework dan PostgreSQL. Berfungsi sebagai API utama untuk fitur login/signup berbasis token, reset password via email, dan manajemen data siswa/tutor/kelas.

## 🧩 Fitur

- 🔐 Autentikasi User (Sign Up + Login)
- 📧 Reset password via OTP ke Email
- 🧑‍🏫 Relasi data siswa, tutor, kelas, absensi
- 📌 Validasi token signup (hanya bisa daftar jika dapat token dari admin)
- 📮 SMTP email support (via Gmail SMTP)
- ⚙️ Non-managed model (import dari PostgreSQL lewat `inspectdb`)

---

## Link Desain Figma Manajemen Bimbel

- [Desain UI Figma](https://www.figma.com/design/xJptZfx4oK4eYOSoDRPeAE/UI-UX-LMS---Gluon-IT?node-id=0-1&t=0Rk034BKqJzwQqM3-1).

## Link Frontend Manajemen Bimbel

- [Frontend](https://github.com/rahmanfaisal0414/manajemen-bimbel).
