from main import SessionLocal, UserModel, hash_password

db = SessionLocal()

# Definimos tu usuario intocable
admin_user = UserModel(
    full_name="Administrador Qxao",
    email="admin@qxao.com",
    company_name="Qxao Team",
    hashed_password=hash_password("admin1234"),
    is_admin=True # <--- LA LLAVE DORADA
)

try:
    db.add(admin_user)
    db.commit()
    print("¡Superusuario Administrador creado con éxito en la nueva base de datos!")
except Exception as e:
    print("Hubo un error:", e)
finally:
    db.close()