from main import SessionLocal, UserModel, hash_password

db = SessionLocal()

# Creamos tu usuario de prueba oficial
nuevo_cliente = UserModel(
    full_name="Ricardo",
    email="test@qxao.com",
    company_name="Empresa de Prueba C.A.",
    hashed_password=hash_password("123456")
)

db.add(nuevo_cliente)
db.commit()
db.close()

print("¡Usuario de prueba creado con éxito en la base de datos qxao.db!") 