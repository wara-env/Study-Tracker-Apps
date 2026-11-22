# Study Tracker

Desktop app (PySide6) + backend Flask/SQLite.

Fitur: login multi-user · timer Pomodoro (sesi fokus otomatis tercatat) · tugas & deadline · statistik (grafik harian, per mata kuliah, streak) · concept map (node teori/rumus/penerapan + panah berlabel).

## Jalankan

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# terminal 1: server
cd server && python app.py

# terminal 2: client
cd client && python main.py
```

Server default `127.0.0.1:5000`. Ganti alamat client: `STUDY_API=http://host:port python main.py`.
Database: `server/instance/study_tracker.db` (SQLite).

## Test

```bash
pytest -q
```

## Struktur

```
server/  app.py (API + auth token) · models.py
client/  main.py · api.py · login.py · timer_tab.py · tasks_tab.py · stats_tab.py · conceptmap_tab.py
tests/   test_api.py
```

## Catatan

- Panggilan API di client berjalan di UI thread (cukup untuk server lokal). Kalau server dipindah ke jaringan, pindahkan ke `QThread`.
- Kalau server di-deploy publik: pakai HTTPS, ganti server dev Flask dengan gunicorn.
