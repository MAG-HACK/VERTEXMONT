import json
from werkzeug.security import generate_password_hash

NUEVA_PASSWORD = "admin123"

ARCHIVO = "data/admin.json"

with open(ARCHIVO, "r", encoding="utf-8") as file:
    user = json.load(file)

user["password"] = generate_password_hash(NUEVA_PASSWORD)

with open(ARCHIVO, "w", encoding="utf-8") as file:
    json.dump(user, file, indent=4, ensure_ascii=False)

print("================================")
print("Contraseña cambiada correctamente")
print("Usuario: admin")
print("Contraseña: admin123")
print("================================")