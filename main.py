import os
import json
import threading
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
LOCK = threading.Lock()


def _ensure_db():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"books": [], "next_id": 1}, f, ensure_ascii=False, indent=2)


def load_db():
    _ensure_db()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(db):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


# MODELE
class BookIn(BaseModel):
    title: str
    author: str
    year: int
    genre: str
    price: float


class BookOut(BookIn):
    id: int


# KONFIGURACJA FASTAPI
app = FastAPI(
    title="LAB02 - FastAPI (CRUD /books)",
    description="Middleware + CORS + X-Process-Time + Admin guard + CRUD dla książek",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# MIDDLEWARE – pomiar czasu
@app.middleware("http")
async def timing_header(request: Request, call_next):
    import time
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000.0
    response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
    return response


# ADMIN GUARD
API_KEY = os.getenv("API_KEY", "sekretnyklucz")


@app.middleware("http")
async def admin_guard(request: Request, call_next):
    if request.url.path.startswith("/admin/"):
        provided = request.headers.get("X-API-Key")
        if provided != API_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized (missing/invalid X-API-Key)"}
            )
    return await call_next(request)


# ENDPOINTY ADMINA
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/admin/secret")
def admin_secret():
    return {"ok": True, "msg": "Welcome, admin."}


# --- CRUD dla /books ---
@app.get("/books", response_model=List[BookOut])
def list_books():
    db = load_db()
    return db["books"]


@app.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int):
    db = load_db()
    for book in db["books"]:
        if book["id"] == book_id:
            return book
    raise HTTPException(status_code=404, detail="Book not found")


@app.post("/books", response_model=BookOut, status_code=201)
def create_book(book: BookIn):
    with LOCK:
        db = load_db()
        new_id = int(db.get("next_id", 1))
        record = {"id": new_id, **book.dict()}
        db["books"].append(record)
        db["next_id"] = new_id + 1
        save_db(db)
        return record


@app.put("/books/{book_id}", response_model=BookOut)
def update_book(book_id: int, book: BookIn):
    with LOCK:
        db = load_db()
        for i, bk in enumerate(db["books"]):
            if bk["id"] == book_id:
                updated = {"id": book_id, **book.dict()}
                db["books"][i] = updated
                save_db(db)
                return updated
    raise HTTPException(status_code=404, detail="Book not found")


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    with LOCK:
        db = load_db()
        for i, bk in enumerate(db["books"]):
            if bk["id"] == book_id:
                db["books"].pop(i)
                save_db(db)
                return
    raise HTTPException(status_code=404, detail="Book not found")

# --- CRUD dla /users ---
class UserIn(BaseModel):
    name: str
    email: str
    role: str = "reader"

class UserOut(UserIn):
    id: int

@app.get("/users", response_model=List[UserOut])
def list_users():
    db = load_db()
    return db.get("users", [])

@app.post("/users", response_model=UserOut, status_code=201)
def create_user(user: UserIn):
    with LOCK:
        db = load_db()
        if "users" not in db:
            db["users"] = []
            db["next_user_id"] = 1
        new_id = int(db.get("next_user_id", 1))
        record = {"id": new_id, **user.dict()}
        db["users"].append(record)
        db["next_user_id"] = new_id + 1
        save_db(db)
        return record

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    db = load_db()
    for user in db.get("users", []):
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user: UserIn):
    with LOCK:
        db = load_db()
        for i, u in enumerate(db.get("users", [])):
            if u["id"] == user_id:
                updated = {"id": user_id, **user.dict()}
                db["users"][i] = updated
                save_db(db)
                return updated
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    with LOCK:
        db = load_db()
        for i, u in enumerate(db.get("users", [])):
            if u["id"] == user_id:
                db["users"].pop(i)
                save_db(db)
                return
    raise HTTPException(status_code=404, detail="User not found")
