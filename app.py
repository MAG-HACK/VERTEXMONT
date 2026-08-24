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
import urllib.request
import urllib.error
import urllib.parse

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from werkzeug.utils import secure_filename


# ==========================================
# APP
# ==========================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "vertex_month_secret_2026_change_this"
)

app.permanent_session_lifetime = 60 * 60 * 24 * 7


# ==========================================
# CARPETAS
# ==========================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ==========================================
# SUPABASE
# ==========================================

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    ""
).rstrip("/")

SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    ""
)

CREATORS_TABLE = "creators"
ADMIN_TABLE = "admin"


# ==========================================
# ADMIN
# ==========================================

ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


# ==========================================
# COMPROBAR SUPABASE
# ==========================================

def check_supabase_config():

    if not SUPABASE_URL:
        print("ERROR: falta SUPABASE_URL")

    if not SUPABASE_KEY:
        print("ERROR: falta SUPABASE_KEY")

    if SUPABASE_URL and SUPABASE_KEY:
        print("Supabase configurado correctamente.")


# ==========================================
# PETICIÓN SUPABASE
# ==========================================

def supabase_request(
    method,
    table,
    params=None,
    data=None
):

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "Supabase no está configurado."
        )

    url = (
        SUPABASE_URL
        + "/rest/v1/"
        + table
    )

    if params:
        url += "?" + urllib.parse.urlencode(
            params,
            doseq=True
        )

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
        "Content-Type": "application/json"
    }

    if method.upper() in ["POST", "PATCH", "PUT"]:
        headers["Prefer"] = "return=representation"

    body = None

    if data is not None:
        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

    request_object = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method.upper()
    )

    try:

        with urllib.request.urlopen(
            request_object,
            timeout=30
        ) as response:

            raw = response.read()

            if not raw:
                return []

            return json.loads(
                raw.decode("utf-8")
            )

    except urllib.error.HTTPError as error:

        error_body = error.read().decode(
            "utf-8",
            errors="replace"
        )

        print(
            "SUPABASE ERROR:",
            error.code,
            error_body
        )

        raise RuntimeError(
            f"Supabase HTTP {error.code}: {error_body}"
        )

    except Exception as error:

        print(
            "ERROR SUPABASE:",
            error
        )

        raise


# ==========================================
# CARGAR CREADORES
# ==========================================

def load_creators():

    try:

        data = supabase_request(
            "GET",
            CREATORS_TABLE,
            params={
                "select": "*",
                "order": "name.asc"
            }
        )

        if isinstance(data, list):
            return data

        return []

    except Exception as error:

        print(
            "ERROR cargando creadores:",
            error
        )

        return []


# ==========================================
# CARGAR ADMIN
# ==========================================

def load_admin():

    try:

        data = supabase_request(
            "GET",
            ADMIN_TABLE,
            params={
                "select": "*",
                "limit": "1"
            }
        )

        if isinstance(data, list) and data:

            return data[0]

        # ==================================
        # CREAR ADMIN SI NO EXISTE
        # ==================================

        admin_data = {
            "username": ADMIN_USERNAME,
            "password": generate_password_hash(
                DEFAULT_ADMIN_PASSWORD
            )
        }

        created = supabase_request(
            "POST",
            ADMIN_TABLE,
            data=admin_data
        )

        if isinstance(created, list) and created:
            return created[0]

        return None

    except Exception as error:

        print(
            "ERROR cargando admin:",
            error
        )

        return None


# ==========================================
# GUARDAR ADMIN
# ==========================================

def save_admin(admin_data):

    try:

        admin_id = admin_data.get("id")

        if admin_id:

            result = supabase_request(
                "PATCH",
                ADMIN_TABLE,
                params={
                    "id": "eq." + str(admin_id)
                },
                data={
                    "username": admin_data.get(
                        "username",
                        ADMIN_USERNAME
                    ),
                    "password": admin_data.get(
                        "password",
                        ""
                    )
                }
            )

        else:

            result = supabase_request(
                "POST",
                ADMIN_TABLE,
                data={
                    "username": admin_data.get(
                        "username",
                        ADMIN_USERNAME
                    ),
                    "password": admin_data.get(
                        "password",
                        ""
                    )
                }
            )

        return bool(result is not None)

    except Exception as error:

        print(
            "ERROR guardando admin:",
            error
        )

        return False


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
# VERIFICAR CONTRASEÑA
# ==========================================

def verify_password(
    stored_password,
    entered_password
):

    stored_password = str(
        stored_password or ""
    )

    entered_password = str(
        entered_password or ""
    )

    if not stored_password:
        return False

    if is_password_hash(
        stored_password
    ):

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

    return (
        stored_password
        ==
        entered_password
    )


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
                .split(
                    "tiktok.com/@",
                    1
                )[1]
                .split(
                    "?",
                    1
                )[0]
                .split(
                    "/",
                    1
                )[0]
            )

        except Exception:
            pass

    value = value.lstrip("@")

    if not value:
        return ""

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
    print("Base:", SUPABASE_URL)
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

    if username != stored_username:

        print(
            "LOGIN FALLIDO: usuario incorrecto"
        )

        return (
            "Usuario o contraseña incorrectos",
            401
        )

    password_correct = verify_password(
        stored_password,
        password
    )

    # ======================================
    # CONVERTIR PASSWORD ANTIGUA A HASH
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

    if not session.get(
        "admin",
        False
    ):

        return jsonify({
            "success": False,
            "error":
                "No autorizado. Inicia sesión nuevamente."
        }), 401

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

    if request.is_json:

        try:

            json_data = (
                request.get_json(
                    silent=True
                )
                or {}
            )

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

        except Exception:
            pass

    current_password = str(
        current_password or ""
    )

    new_password = str(
        new_password or ""
    )

    confirm_password = str(
        confirm_password or ""
    )

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

    if new_password != confirm_password:

        return jsonify({
            "success": False,
            "error":
                "Las contraseñas nuevas no coinciden."
        }), 400

    admin_data = load_admin()

    if not admin_data:

        return jsonify({
            "success": False,
            "error":
                "No se pudo cargar el administrador."
        }), 500

    stored_password = str(
        admin_data.get(
            "password",
            ""
        )
    )

    if not verify_password(
        stored_password,
        current_password
    ):

        return jsonify({
            "success": False,
            "error":
                "La contraseña actual es incorrecta."
        }), 400

    admin_data["password"] = (
        generate_password_hash(
            new_password
        )
    )

    saved = save_admin(
        admin_data
    )

    if not saved:

        return jsonify({
            "success": False,
            "error":
                "No se pudo guardar la nueva contraseña."
        }), 500

    session["admin"] = True

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
        "admin",
        False
    ):

        return jsonify({
            "error": "No autorizado"
        }), 403

    photo = ""

    if (
        "photo" in request.files
        and request.files["photo"].filename
    ):

        file = request.files["photo"]

        original_name = secure_filename(
            file.filename
        )

        extension = os.path.splitext(
            original_name
        )[1].lower()

        filename = (
            str(uuid.uuid4())
            + extension
        )

        file_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        file.save(file_path)

        photo = (
            "/static/uploads/"
            + filename
        )

    handle = normalize_handle(
        request.form.get(
            "handle",
            ""
        )
    )

    creator = {
        "id": str(uuid.uuid4()),

        "name": request.form.get(
            "name",
            ""
        ).strip(),

        "handle": handle,

        "category": request.form.get(
            "category",
            ""
        ).strip(),

        "country": request.form.get(
            "country",
            ""
        ).strip(),

        "followers": request.form.get(
            "followers",
            ""
        ).strip(),

        "likes": request.form.get(
            "likes",
            ""
        ).strip(),

        "views": request.form.get(
            "views",
            ""
        ).strip(),

        "videos": request.form.get(
            "videos",
            ""
        ).strip(),

        "engagement": request.form.get(
            "engagement",
            ""
        ).strip(),

        "average_likes": request.form.get(
            "average_likes",
            ""
        ).strip(),

        "average_comments": request.form.get(
            "average_comments",
            ""
        ).strip(),

        "average_shares": request.form.get(
            "average_shares",
            ""
        ).strip(),

        "tiktok": get_tiktok_url(
            request.form.get(
                "tiktok",
                ""
            )
            or handle
        ),

        "instagram": request.form.get(
            "instagram",
            ""
        ).strip(),

        "youtube": request.form.get(
            "youtube",
            ""
        ).strip(),

        "photo": photo
    }

    try:

        result = supabase_request(
            "POST",
            CREATORS_TABLE,
            data=creator
        )

        if isinstance(result, list) and result:
            return jsonify(result[0])

        return jsonify(creator)

    except Exception as error:

        return jsonify({
            "error":
                "No se pudo guardar el creador en Supabase.",
            "details": str(error)
        }), 500


# ==========================================
# EDITAR CREADOR
# ==========================================

@app.route(
    "/api/creator/<creator_id>",
    methods=["POST"]
)
def edit_creator(creator_id):

    if not session.get(
        "admin",
        False
    ):

        return jsonify({
            "error": "No autorizado"
        }), 403

    handle = normalize_handle(
        request.form.get(
            "handle",
            ""
        )
    )

    update_data = {
        "name": request.form.get(
            "name",
            ""
        ).strip(),

        "handle": handle,

        "category": request.form.get(
            "category",
            ""
        ).strip(),

        "country": request.form.get(
            "country",
            ""
        ).strip(),

        "followers": request.form.get(
            "followers",
            ""
        ).strip(),

        "likes": request.form.get(
            "likes",
            ""
        ).strip(),

        "views": request.form.get(
            "views",
            ""
        ).strip(),

        "videos": request.form.get(
            "videos",
            ""
        ).strip(),

        "engagement": request.form.get(
            "engagement",
            ""
        ).strip(),

        "average_likes": request.form.get(
            "average_likes",
            ""
        ).strip(),

        "average_comments": request.form.get(
            "average_comments",
            ""
        ).strip(),

        "average_shares": request.form.get(
            "average_shares",
            ""
        ).strip(),

        "instagram": request.form.get(
            "instagram",
            ""
        ).strip(),

        "youtube": request.form.get(
            "youtube",
            ""
        ).strip(),

        "tiktok": get_tiktok_url(
            request.form.get(
                "tiktok",
                ""
            ).strip()
            or handle
        )
    }

    if (
        "photo" in request.files
        and request.files["photo"].filename
    ):

        file = request.files["photo"]

        original_name = secure_filename(
            file.filename
        )

        extension = os.path.splitext(
            original_name
        )[1].lower()

        filename = (
            str(uuid.uuid4())
            + extension
        )

        file_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        file.save(file_path)

        update_data["photo"] = (
            "/static/uploads/"
            + filename
        )

    try:

        result = supabase_request(
            "PATCH",
            CREATORS_TABLE,
            params={
                "id": "eq." + str(creator_id)
            },
            data=update_data
        )

        if not result:

            return jsonify({
                "error":
                    "Creador no encontrado"
            }), 404

        return jsonify(result[0])

    except Exception as error:

        return jsonify({
            "error":
                "No se pudieron guardar los cambios.",
            "details": str(error)
        }), 500


# ==========================================
# ELIMINAR CREADOR
# ==========================================

@app.route(
    "/api/creator/<creator_id>",
    methods=["DELETE"]
)
def delete_creator(creator_id):

    if not session.get(
        "admin",
        False
    ):

        return jsonify({
            "error": "No autorizado"
        }), 403

    try:

        result = supabase_request(
            "DELETE",
            CREATORS_TABLE,
            params={
                "id": "eq." + str(creator_id)
            }
        )

        return jsonify({
            "success": True
        })

    except Exception as error:

        return jsonify({
            "error":
                "No se pudo eliminar el creador.",
            "details": str(error)
        }), 500


# ==========================================
# EJECUTAR
# ==========================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print(" VERTEXMONT")
    print("==========================================")
    print("Base de datos: SUPABASE")
    print("URL:")
    print(SUPABASE_URL)
    print()
    print("Tabla creadores:")
    print(CREATORS_TABLE)
    print()
    print("Tabla administrador:")
    print(ADMIN_TABLE)
    print()
    print("Usuario administrador:")
    print(ADMIN_USERNAME)
    print("==========================================")
    print()

    check_supabase_config()

    app.run(
        debug=False
    )