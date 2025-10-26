# LAB02 – FastAPI CRUD (Książki i Użytkownicy)

Projekt na zajęcia z Programowania 2 – laboratorium FastAPI.

## 📦 Funkcjonalność
- Middleware: X-Process-Time
- Middleware: Admin guard (X-API-Key)
- CORS
- CRUD `/books`
- CRUD `/users`
- Lokalna baza danych w pliku `data.json`

## 🚀 Uruchomienie
```bash
pip install -r requirements.txt
uvicorn main:app --reload
