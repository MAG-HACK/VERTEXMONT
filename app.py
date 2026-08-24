
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

import os
import json
import uuid

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from werkzeug.utils import secure_filename


# ==========================================
# APP
# ==========================================

app = Flask(__name__)

app.secret_key = "vertex_month_secret_2026_change_this"


# ==========================================
# CARPETAS
# ==========================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "uploads"
)

CREATORS_FILE = os.path.join(
    DATA_DIR,
    "creators.json"
)

ADMIN_FILE = os.path.join(
    DATA_DIR,
    "admin.json"
)


os.makedirs(
    DATA_DIR,
    exist_ok=True
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ==========================================
# CREAR CREATORS.JSON SI NO EXISTE
# ==========================================

if not os.path.exists(CREATORS_FILE):

    with open(
        CREATORS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            [],
            file,
            ensure_ascii=False,
            indent=4
        )


# ==========================================
# ADMIN
# ==========================================

ADMIN_USERNAME = "admin"

# Esta es la contraseña inicial.
# Si admin.json ya existe, NO reemplaza
# automáticamente la contraseña guardada.
DEFAULT_ADMIN_PASSWORD = "admin123"


# ==========================================
# CREAR ADMIN.JSON SI NO EXISTE
# ==========================================

if not os.path.exists(ADMIN_FILE):

    initial_admin = {
        "username": ADMIN_USERNAME,
        "password": generate_password_hash(
            DEFAULT_ADMIN_PASSWORD
        )
    }

    with open(
        ADMIN_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            initial_admin,
            file,
            ensure_ascii=False,
            indent=4
        )


# ==========================================
# DETECTAR HASH
# ==========================================

def is_password_hash(value):

    value = str(value or "")

    return (
        value.startswith("scrypt:")
        or value.startswith("pbkdf2:")
        or value.startswith("argon2:")
    )


# ==========================================
# COMPROBAR CONTRASEÑA
# ==========================================

def verify_password(stored_password, entered_password):

    stored_password = str(
        stored_password or ""
    )

    entered_password = str(
        entered_password or ""
    )

    if not stored_password:
        return False

    # Contraseña guardada como hash
    if is_password_hash(stored_password):

        try:
            return check_password_hash(
                stored_password,
                entered_password
            )
        except Exception as error:

            print(
                "ERROR verificando hash:",
                error
            )

            return False

    # Compatibilidad con contraseñas antiguas
    # guardadas como texto normal
    return stored_password == entered_password


# ==========================================
# CARGAR ADMIN
# ==========================================

def load_admin():

    try:

        if not os.path.exists(ADMIN_FILE):

            print(
                "admin.json no existe. Creándolo..."
            )

            admin_data = {
                "username": ADMIN_USERNAME,
                "password": generate_password_hash(
                    DEFAULT_ADMIN_PASSWORD
                )
            }

            save_admin(admin_data)

            return admin_data

        with open(
            ADMIN_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):

            print(
                "ERROR: admin.json no contiene un objeto válido."
            )

            return None

        return data

    except Exception as error:

        print(
            "ERROR cargando admin.json:",
            error
        )

        return None


# ==========================================
# GUARDAR ADMIN
# ==========================================

def save_admin(admin_data):

    temp_file = ADMIN_FILE + ".tmp"

    try:

        # Crear el directorio por seguridad
        os.makedirs(
            DATA_DIR,
            exist_ok=True
        )

        # Escribir archivo temporal
        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                admin_data,
                file,
                ensure_ascii=False,
                indent=4
            )

            file.flush()

            # Intentar asegurar que se escriba
            # físicamente en disco
            try:
                os.fsync(file.fileno())
            except Exception:
                pass

        # Reemplazo atómico
        os.replace(
            temp_file,
            ADMIN_FILE
        )

        # Comprobar que realmente existe
        if not os.path.exists(ADMIN_FILE):

            print(
                "ERROR: admin.json no existe después de guardar."
            )

            return False

        # Volver a leer y comprobar que sea JSON válido
        with open(
            ADMIN_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            verification = json.load(file)

        if not isinstance(
            verification,
            dict
        ):

            print(
                "ERROR: admin.json quedó inválido."
            )

            return False

        print(
            "ADMIN GUARDADO CORRECTAMENTE:"
        )

        print(
            ADMIN_FILE
        )

        return True

    except Exception as error:

        print(
            "ERROR GUARDANDO admin.json:",
            error
        )

        # Intentar limpiar temporal
        try:

            if os.path.exists(temp_file):
                os.remove(temp_file)

        except Exception:
            pass

        return False


# ==========================================
# CARGAR CREADORES
# ==========================================

def load_creators():

    try:

        with open(
            CREATORS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):

            return data

        return []

    except Exception as error:

        print(
            "Error cargando creators.json:",
            error
        )

        return []


# ==========================================
# GUARDAR CREADORES
# ==========================================

def save_creators(creators):

    try:

        with open(
            CREATORS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                creators,
                file,
                ensure_ascii=False,
                indent=4
            )

        return True

    except Exception as error:

        print(
            "Error guardando creators.json:",
            error
        )

        return False


# ==========================================
# NORMALIZAR USUARIO
# ==========================================

def normalize_handle(value):

    value = str(
        value or ""
    ).strip()

    if not value:
        return ""

    if "tiktok.com/@" in value:

        try:

            value = (
                value
                .split("tiktok.com/@")[1]
                .split("?")[0]
                .split("/")[0]
            )

        except Exception:
            pass

    value = value.lstrip("@")

    return "@" + value


# ==========================================
# CREAR URL TIKTOK
# ==========================================

def get_tiktok_url(value):

    handle = normalize_handle(value)

    if not handle:
        return ""

    username = handle.lstrip("@")

    return (
        "https://www.tiktok.com/@"
        + username
    )


# ==========================================
# INICIO
# ==========================================

@app.route("/")
def index():

    creators = load_creators()

    admin = session.get(
        "admin",
        False
    )

    return render_template(
        "index.html",
        creators=creators,
        admin=admin
    )


# ==========================================
# LOGIN
# ==========================================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    print()
    print("==========================================")
    print("INTENTO DE LOGIN")
    print("Usuario:", username)
    print("Archivo:", ADMIN_FILE)
    print("==========================================")


    admin_data = load_admin()

    if not admin_data:

        return (
            "No se pudo cargar el usuario administrador.",
            500
        )


    stored_username = str(
        admin_data.get(
            "username",
            ADMIN_USERNAME
        )
    ).strip()

    stored_password = str(
        admin_data.get(
            "password",
            ""
        )
    )


    # ======================================
    # COMPROBAR USUARIO
    # ======================================

    if username != stored_username:

        print(
            "LOGIN FALLIDO: usuario incorrecto"
        )

        return (
            "Usuario o contraseña incorrectos",
            401
        )


    # ======================================
    # COMPROBAR CONTRASEÑA
    # ======================================

    password_correct = verify_password(
        stored_password,
        password
    )


    # ======================================
    # SI LA CONTRASEÑA ANTIGUA ESTABA
    # EN TEXTO NORMAL, CONVERTIRLA A HASH
    # ======================================

    if (
        password_correct
        and not is_password_hash(
            stored_password
        )
    ):

        admin_data["password"] = (
            generate_password_hash(
                password
            )
        )

        save_admin(
            admin_data
        )


    # ======================================
    # LOGIN CORRECTO
    # ======================================

    if password_correct:

        session.clear()

        session["admin"] = True

        session.permanent = True

        print(
            "LOGIN CORRECTO"
        )

        return redirect(
            url_for("index")
        )


    # ======================================
    # LOGIN INCORRECTO
    # ======================================

    print(
        "LOGIN FALLIDO: contraseña incorrecta"
    )

    return (
        "Usuario o contraseña incorrectos",
        401
    )


# ==========================================
# CAMBIAR CONTRASEÑA
# ==========================================

@app.route(
    "/change-password",
    methods=["POST"]
)
def change_password():

    print()
    print("==========================================")
    print("CAMBIO DE CONTRASEÑA")
    print("==========================================")


    # ======================================
    # SOLO ADMIN
    # ======================================

    if not session.get(
        "admin",
        False
    ):

        print(
            "ERROR: sesión no autorizada"
        )

        return jsonify({
            "success": False,
            "error": "No autorizado. Inicia sesión nuevamente."
        }), 401


    # ======================================
    # RECIBIR DATOS
    # ======================================

    current_password = request.form.get(
        "current_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    # También aceptar JSON por si el frontend
    # cambia posteriormente a JSON.

    if request.is_json:

        try:

            json_data = request.get_json(
                silent=True
            ) or {}

            current_password = json_data.get(
                "current_password",
                current_password
            )

            new_password = json_data.get(
                "new_password",
                new_password
            )

            confirm_password = json_data.get(
                "confirm_password",
                confirm_password
            )

        except Exception as error:

            print(
                "Error leyendo JSON:",
                error
            )


    current_password = str(
        current_password or ""
    )

    new_password = str(
        new_password or ""
    )

    confirm_password = str(
        confirm_password or ""
    )


    print(
        "Contraseña actual recibida:",
        bool(current_password)
    )

    print(
        "Nueva contraseña recibida:",
        bool(new_password)
    )

    print(
        "Confirmación recibida:",
        bool(confirm_password)
    )


    # ======================================
    # VALIDAR QUE SE RECIBIÓ LA NUEVA
    # ======================================

    if not new_password:

        return jsonify({
            "success": False,
            "error":
                "La nueva contraseña no puede estar vacía."
        }), 400


    if len(new_password) < 6:

        return jsonify({
            "success": False,
            "error":
                "La contraseña debe tener al menos 6 caracteres."
        }), 400


    # ======================================
    # CONFIRMAR NUEVA CONTRASEÑA
    # ======================================

    if new_password != confirm_password:

        return jsonify({
            "success": False,
            "error":
                "Las contraseñas nuevas no coinciden."
        }), 400


    # ======================================
    # CARGAR ADMIN
    # ======================================

    admin_data = load_admin()

    if not admin_data:

        return jsonify({
            "success": False,
            "error":
                "No se pudo cargar data/admin.json."
        }), 500


    stored_password = str(
        admin_data.get(
            "password",
            ""
        )
    )


    # ======================================
    # COMPROBAR CONTRASEÑA ACTUAL
    # ======================================

    current_password_correct = (
        verify_password(
            stored_password,
            current_password
        )
    )


    if not current_password_correct:

        print(
            "ERROR: contraseña actual incorrecta"
        )

        return jsonify({
            "success": False,
            "error":
                "La contraseña actual es incorrecta."
        }), 400


    # ======================================
    # GENERAR NUEVO HASH
    # ======================================

    new_password_hash = (
        generate_password_hash(
            new_password
        )
    )


    # ======================================
    # ACTUALIZAR DATOS
    # ======================================

    admin_data["username"] = str(
        admin_data.get(
            "username",
            ADMIN_USERNAME
        )
    ).strip()

    admin_data["password"] = (
        new_password_hash
    )


    # ======================================
    # GUARDAR REALMENTE
    # ======================================

    saved = save_admin(
        admin_data
    )

    if not saved:

        print(
            "ERROR: no se pudo guardar admin.json"
        )

        return jsonify({
            "success": False,
            "error":
                "No se pudo guardar la nueva contraseña en data/admin.json."
        }), 500


    # ======================================
    # VERIFICAR ARCHIVO DESDE DISCO
    # ==========================================

    verify_data = load_admin()

    if not verify_data:

        return jsonify({
            "success": False,
            "error":
                "La contraseña fue escrita pero no se pudo volver a leer admin.json."
        }), 500


    verify_hash = str(
        verify_data.get(
            "password",
            ""
        )
    )


    # ======================================
    # VERIFICACIÓN REAL
    # ======================================

    verified = verify_password(
        verify_hash,
        new_password
    )


    if not verified:

        print(
            "ERROR: la contraseña no pasó la verificación."
        )

        return jsonify({
            "success": False,
            "error":
                "La contraseña no pudo verificarse después de guardarla."
        }), 500


    # ======================================
    # ASEGURAR SESIÓN
    # ======================================

    session["admin"] = True


    print()
    print("==========================================")
    print("CONTRASEÑA CAMBIADA CORRECTAMENTE")
    print("Archivo actualizado:")
    print(ADMIN_FILE)
    print("==========================================")
    print()


    # ======================================
    # RESPUESTA FINAL
    # ======================================

    return jsonify({
        "success": True,
        "message":
            "Contraseña cambiada correctamente."
    }), 200


# ==========================================
# LOGOUT
# ==========================================

@app.route(
    "/logout",
    methods=["POST"]
)
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# ==========================================
# AGREGAR CREADOR
# ==========================================

@app.route(
    "/api/creator",
    methods=["POST"]
)
def add_creator():

    if not session.get(
        "admin"
    ):

        return jsonify({
            "error": "No autorizado"
        }), 403


    creators = load_creators()


    # ======================================
    # FOTO
    # ======================================

    photo = ""

    if (
        "photo" in request.files
        and request.files["photo"].filename
    ):

        file = request.files[
            "photo"
        ]

        original_name = secure_filename(
            file.filename
        )

        extension = os.path.splitext(
            original_name
        )[1]

        filename = (
            str(uuid.uuid4())
            + extension
        )

        file_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        file.save(
            file_path
        )

        photo = (
            "/static/uploads/"
            + filename
        )


    # ======================================
    # USUARIO
    # ======================================

    handle = normalize_handle(
        request.form.get(
            "handle",
            ""
        )
    )


    # ======================================
    # CREADOR
    # ======================================

    creator = {

        "id": str(
            uuid.uuid4()
        ),

        "name":
            request.form.get(
                "name",
                ""
            ).strip(),

        "handle":
            handle,

        "category":
            request.form.get(
                "category",
                ""
            ).strip(),

        "country":
            request.form.get(
                "country",
                ""
            ).strip(),

        "followers":
            request.form.get(
                "followers",
                ""
            ).strip(),

        "likes":
            request.form.get(
                "likes",
                ""
            ).strip(),

        "views":
            request.form.get(
                "views",
                ""
            ).strip(),

        "videos":
            request.form.get(
                "videos",
                ""
            ).strip(),

        "engagement":
            request.form.get(
                "engagement",
                ""
            ).strip(),

        "average_likes":
            request.form.get(
                "average_likes",
                ""
            ).strip(),

        "average_comments":
            request.form.get(
                "average_comments",
                ""
            ).strip(),

        "average_shares":
            request.form.get(
                "average_shares",
                ""
            ).strip(),

        "tiktok":
            get_tiktok_url(
                request.form.get(
                    "tiktok",
                    ""
                )
                or handle
            ),

        "instagram":
            request.form.get(
                "instagram",
                ""
            ).strip(),

        "youtube":
            request.form.get(
                "youtube",
                ""
            ).strip(),

        "photo":
            photo
    }


    creators.append(
        creator
    )


    if not save_creators(
        creators
    ):

        return jsonify({
            "error":
                "No se pudieron guardar los datos"
        }), 500


    return jsonify(
        creator
    )


# ==========================================
# EDITAR CREADOR
# ==========================================

@app.route(
    "/api/creator/<creator_id>",
    methods=["POST"]
)
def edit_creator(creator_id):

    if not session.get(
        "admin"
    ):

        return jsonify({
            "error": "No autorizado"
        }), 403


    creators = load_creators()


    creator = next(
        (
            item
            for item in creators
            if item.get("id") == creator_id
        ),
        None
    )


    if not creator:

        return jsonify({
            "error":
                "Creador no encontrado"
        }), 404


    # ======================================
    # ACTUALIZAR USUARIO
    # ======================================

    handle = normalize_handle(
        request.form.get(
            "handle",
            ""
        )
    )

    creator["handle"] = handle


    # ======================================
    # ACTUALIZAR CAMPOS
    # ======================================

    fields = [

        "name",
        "category",
        "country",
        "followers",
        "likes",
        "views",
        "videos",
        "engagement",
        "average_likes",
        "average_comments",
        "average_shares",
        "instagram",
        "youtube"

    ]


    for field in fields:

        creator[field] = (
            request.form.get(
                field,
                ""
            ).strip()
        )


    # ======================================
    # TIKTOK
    # ======================================

    tiktok_value = request.form.get(
        "tiktok",
        ""
    ).strip()


    if not tiktok_value:

        tiktok_value = handle


    creator["tiktok"] = get_tiktok_url(
        tiktok_value
    )


    # ======================================
    # FOTO NUEVA
    # ======================================

    if (
        "photo" in request.files
        and request.files["photo"].filename
    ):

        file = request.files[
            "photo"
        ]

        original_name = secure_filename(
            file.filename
        )

        extension = os.path.splitext(
            original_name
        )[1]

        filename = (
            str(uuid.uuid4())
            + extension
        )

        file_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        file.save(
            file_path
        )

        creator["photo"] = (
            "/static/uploads/"
            + filename
        )


    # ======================================
    # GUARDAR
    # ======================================

    if not save_creators(
        creators
    ):

        return jsonify({
            "error":
                "No se pudieron guardar los cambios"
        }), 500


    return jsonify(
        creator
    )


# ==========================================
# ELIMINAR CREADOR
# ==========================================

@app.route(
    "/api/creator/<creator_id>",
    methods=["DELETE"]
)
def delete_creator(creator_id):

    if not session.get(
        "admin"
    ):

        return jsonify({
            "error": "No autorizado"
        }), 403


    creators = load_creators()


    new_creators = [

        creator

        for creator in creators

        if creator.get("id") != creator_id

    ]


    if not save_creators(
        new_creators
    ):

        return jsonify({
            "error":
                "No se pudo eliminar"
        }), 500


    return jsonify({
        "success": True
    })


# ==========================================
# EJECUTAR
# ==========================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print(" VERTEX MONTH")
    print("==========================================")

    print("Archivo de administrador:")
    print(ADMIN_FILE)

    print()

    print("Usuario administrador:")
    print(ADMIN_USERNAME)

    print()

    print("Contraseña inicial:")
    print(DEFAULT_ADMIN_PASSWORD)

    print("==========================================")
    print()

    app.run(
        debug=True
    )
