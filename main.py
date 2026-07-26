from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse # <--- NUEVO: Importación para mostrar archivos
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import hashlib
from typing import Optional

# 1. Configuración de Base de Datos SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./qxao.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Modelo de Usuario
class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    company_name = Column(String)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True) 

Base.metadata.create_all(bind=engine)

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

app = FastAPI()

# --- NUEVA RUTA PRINCIPAL: Carga el index.html al entrar al link ---
@app.get("/")
def mostrar_inicio():
    return FileResponse("index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/login")
def login(request: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.email == request.email).first()
        if not user:
            raise HTTPException(status_code=400, detail="Usuario no encontrado")
        
        if user.hashed_password != hash_password(request.password):
            raise HTTPException(status_code=400, detail="Contraseña incorrecta")
            
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Tu cuenta ha sido bloqueada por administración.")

        return {
            "token": "qxao-token-auth",
            "user_name": user.full_name,
            "company": user.company_name,
            "is_admin": user.is_admin
        }
    finally:
        db.close()

# --- RUTAS DE ADMINISTRACIÓN ---

@app.get("/api/admin/users")
def get_all_users():
    db = SessionLocal()
    try:
        users_db = db.query(UserModel).all()
        users_list = []
        for user in users_db:
            users_list.append({
                "id": user.id,
                "full_name": user.full_name,
                "company_name": user.company_name,
                "email": user.email,
                "status": "Activo" if user.is_active else "Bloqueado",
                "is_active": user.is_active
            })
        return users_list
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

class CreateUserRequest(BaseModel):
    full_name: str
    company_name: str
    email: str
    password: str

@app.post("/api/admin/users")
def create_new_user(request: CreateUserRequest):
    db = SessionLocal()
    try:
        if db.query(UserModel).filter(UserModel.email == request.email).first():
            return {"success": False, "detail": "Este correo ya está registrado."}
            
        new_user = UserModel(
            full_name=request.full_name, company_name=request.company_name,
            email=request.email, hashed_password=hash_password(request.password)
        )
        db.add(new_user)
        db.commit()
        return {"success": True, "message": "Usuario creado"}
    except Exception as e:
        db.rollback()
        return {"success": False, "detail": str(e)}
    finally:
        db.close()

# RUTA PARA EDITAR USUARIO (Ahora permite cambiar contraseña)
class UpdateUserRequest(BaseModel):
    full_name: str
    company_name: str
    email: str
    password: Optional[str] = None # <--- Puede venir vacía

@app.put("/api/admin/users/{user_id}")
def update_user(user_id: int, request: UpdateUserRequest):
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return {"success": False, "detail": "Usuario no encontrado"}
        
        user.full_name = request.full_name
        user.company_name = request.company_name
        user.email = request.email
        
        # Si enviaste algo en el campo de contraseña, la actualiza
        if request.password and request.password.strip() != "":
            user.hashed_password = hash_password(request.password)
            
        db.commit()
        return {"success": True, "message": "Usuario actualizado"}
    finally:
        db.close()

# RUTA PARA BLOQUEAR/DESBLOQUEAR
@app.put("/api/admin/users/{user_id}/toggle-block")
def toggle_block_user(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return {"success": False, "detail": "Usuario no encontrado"}
        
        user.is_active = not user.is_active 
        db.commit()
        return {"success": True, "is_active": user.is_active}
    finally:
        db.close()
