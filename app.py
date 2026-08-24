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
    "SECRET_KEY",
    "vertex_month_secret_2026_change_this"
)

app.permanent_session_lifetime = 60 * 60 * 24 * 7


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

os.makedirs(
    DATA_DIR,
    exist_ok=True
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

CREATORS_TABLE = os.environ.get(
    "SUPABASE_CREATORS_TABLE",
    "creators"
)

ADMIN_TABLE = os.environ.get(
    "SUPABASE_ADMIN_TABLE",
    "admin"
)


# ==========================================
# CONFIGURACIÓN ADMIN
# ==========================================

ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


# ==========================================
# COMPROBAR SUPABASE
# ==========================================

def supabase_configured():
    return bool(
        SUPABASE_URL
        and SUPABASE_KEY
    )


# ==========================================
# PETICIÓN SUPABASE
# ==========================================

def supabase_request(
    method,
    table,
    data=None,
    query="",
    prefer="return=representation"
):
    if not supabase_configured():
        raise RuntimeError(
            "SUPABASE_URL o SUPABASE_KEY no están configuradas."
        )

    url = (
        f"{SUPABASE_URL}/rest/v1/"
        f"{table}"
    )

    if query:
        url += "?" + query

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    if prefer:
        headers["Prefer"] = prefer

    body = None

    if data is not None:
        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=20
        ) as response:

            raw = response.read().decode(
                "utf-8"
            )

            if not raw:
                return []

            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw

    except urllib.error.HTTPError as error:

        error_body = ""

        try:
            error_body = (
                error.read()
                .decode("utf-8")
            )
        except Exception:
            pass

        print()
        print("==========================================")
        print("ERROR SUPABASE")
        print("HTTP:", error.code)
        print("Tabla:", table)
        print("Respuesta:", error_body)
        print("==========================================")
        print()

        raise RuntimeError(
            f"Supabase HTTP {error.code}: "
            f"{error_body}"
        )

    except Exception as error:

        print()
        print("==========================================")
        print("ERROR CONECTANDO CON SUPABASE")
        print(error)
        print("==========================================")
        print()

        raise


# ==========================================
# CARGAR CREADORES DESDE SUPABASE
# ==========================================

def load_creators():
    try:

        result = supabase_request(
            "GET",
            CREATORS_TABLE,
            query="select=*"
        )

        if not isinstance(
            result,
            list
        ):
            print(
                "ERROR: Supabase no devolvió una lista de creadores."
            )
            return []

        return result

    except Exception as error:

        print(
            "ERROR cargando creadores:",
            error
        )

        return []


# ==========================================
# BUSCAR CREADOR
# ==========================================

def get_creator(
    creator_id
):
    try:

        result = supabase_request(
            "GET",
            CREATORS_TABLE,
            query=(
                "select=*"
                f"&id=eq.{creator_id}"
            )
        )

        if isinstance(
            result,
            list
        ) and result:

            return result[0]

        return None

    except Exception as error:

        print(
            "ERROR buscando creador:",
            error
        )

        return None


# ==========================================
# CARGAR ADMIN
# ==========================================

def load_admin():
    try:

        result = supabase_request(
            "GET",
            ADMIN_TABLE,
            query=(
                "select=*"
                "&limit=1"
            )
        )

        if (
            isinstance(result, list)
            and result
        ):
            return result[0]

        # ==================================
        # CREAR ADMIN SI NO EXISTE
        # ==================================

        initial_admin = {
            "username": ADMIN_USERNAME,
            "password": generate_password_hash(
                DEFAULT_ADMIN_PASSWORD
            )
        }

        created = supabase_request(
            "POST",
            ADMIN_TABLE,
            data=initial_admin
        )

        if (
            isinstance(created, list)
            and created
        ):
            return created[0]

        return initial_admin

    except Exception as error:

        print(
            "ERROR cargando administrador:",
            error
        )

        return None


# ==========================================
# GUARDAR ADMIN
# ==========================================

def save_admin(
    admin_data
):

    try:

        username = str(
            admin_data.get(
                "username",
                ADMIN_USERNAME
            )
        ).strip()

        password = str(
            admin_data.get(
                "password",
                ""
            )
        )

        existing = supabase_request(
            "GET",
            ADMIN_TABLE,
            query=(
                "select=*"
                f"&username=eq.{username}"
            )
        )

        if (
            isinstance(existing, list)
            and existing
        ):

            admin_id = existing[0].get(
                "id"
            )

            if admin_id:

                result = supabase_request(
                    "PATCH",
                    ADMIN_TABLE,
                    data={
                        "username": username,
                        "password": password
                    },
                    query=(
                        f"id=eq.{admin_id}"
                    )
                )

                return True

        result = supabase_request(
            "POST",
            ADMIN_TABLE,
            data={
                "username": username,
                "password": password
            }
        )

        return bool(result is not None)

    except Exception as error:

        print(
            "ERROR guardando administrador:",
            error
        )

        return False


# ==========================================
# DETECTAR HASH
# ==========================================

def is_password_hash(
    value
):

    value = str(
        value or ""
    )

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
# NORMALIZAR USUARIO TIKTOK
# ==========================================

def normalize_handle(
    value
):

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
# URL TIKTOK
# ==========================================

def get_tiktok_url(
    value
):

    handle = normalize_handle(
        value
    )

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
    print("Supabase:", SUPABASE_URL)
    print("Tabla admin:", ADMIN_TABLE)
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
                "No se pudo cargar el administrador desde Supabase."
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

    admin_data["username"] = str(
        admin_data.get(
            "username",
            ADMIN_USERNAME
        )
    ).strip()

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
                "No se pudo guardar la nueva contraseña en Supabase."
        }), 500

    verify_data = load_admin()

    if not verify_data:

        return jsonify({
            "success": False,
            "error":
                "No se pudo verificar la contraseña en Supabase."
        }), 500

    verified = verify_password(
        verify_data.get(
            "password",
            ""
        ),
        new_password
    )

    if not verified:

        return jsonify({
            "success": False,
            "error":
                "La contraseña no pudo verificarse después de guardarla."
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
# CREAR CREADOR
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
        )[1].lower()

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
    # HANDLE
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

    # ======================================
    # GUARDAR EN SUPABASE
    # ======================================

    try:

        result = supabase_request(
            "POST",
            CREATORS_TABLE,
            data=creator
        )

        if (
            isinstance(result, list)
            and result
        ):

            return jsonify(
                result[0]
            )

        return jsonify(
            creator
        )

    except Exception as error:

        return jsonify({
            "error":
                f"No se pudo guardar el creador en Supabase: {error}"
        }), 500


# ==========================================
# EDITAR CREADOR
# ==========================================

@app.route(
    "/api/creator/<creator_id>",
    methods=["POST"]
)
def edit_creator(
    creator_id
):

    if not session.get(
        "admin",
        False
    ):

        return jsonify({
            "error": "No autorizado"
        }), 403

    creator = get_creator(
        creator_id
    )

    if not creator:

        return jsonify({
            "error":
                "Creador no encontrado"
        }), 404

    # ======================================
    # HANDLE
    # ======================================

    handle = normalize_handle(
        request.form.get(
            "handle",
            ""
        )
    )

    creator["handle"] = handle

    # ======================================
    # CAMPOS
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

    creator["tiktok"] = (
        get_tiktok_url(
            tiktok_value
        )
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
        )[1].lower()

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
    # QUITAR CAMPOS QUE NO DEBEMOS ENVIAR
    # ======================================

    update_data = dict(
        creator
    )

    update_data.pop(
        "id",
        None
    )

    # ======================================
    # GUARDAR
    # ======================================

    try:

        result = supabase_request(
            "PATCH",
            CREATORS_TABLE,
            data=update_data,
            query=(
                f"id=eq.{creator_id}"
            )
        )

        if (
            isinstance(result, list)
            and result
        ):

            return jsonify(
                result[0]
            )

        creator["id"] = creator_id

        return jsonify(
            creator
        )

    except Exception as error:

        return jsonify({
            "error":
                f"No se pudieron guardar los cambios en Supabase: {error}"
        }), 500


# ==========================================
# ELIMINAR CREADOR
# ==========================================

@app.route(
    "/api/creator/<creator_id>",
    methods=["DELETE"]
)
def delete_creator(
    creator_id
):

    if not session.get(
        "admin",
        False
    ):

        return jsonify({
            "error": "No autorizado"
        }), 403

    creator = get_creator(
        creator_id
    )

    if not creator:

        return jsonify({
            "error":
                "Creador no encontrado"
        }), 404

    try:

        supabase_request(
            "DELETE",
            CREATORS_TABLE,
            query=(
                f"id=eq.{creator_id}"
            ),
            prefer=""
        )

        return jsonify({
            "success": True
        })

    except Exception as error:

        return jsonify({
            "error":
                f"No se pudo eliminar el creador: {error}"
        }), 500


# ==========================================
# PRUEBA DE SUPABASE
# ==========================================

@app.route(
    "/api/supabase-test"
)
def supabase_test():

    if not session.get(
        "admin",
        False
    ):

        return jsonify({
            "success": False,
            "error": "No autorizado"
        }), 403

    try:

        creators = supabase_request(
            "GET",
            CREATORS_TABLE,
            query="select=id&limit=1"
        )

        admin = supabase_request(
            "GET",
            ADMIN_TABLE,
            query="select=id&limit=1"
        )

        return jsonify({
            "success": True,
            "supabase": SUPABASE_URL,
            "creators_table": CREATORS_TABLE,
            "admin_table": ADMIN_TABLE,
            "creators_connection": True,
            "admin_connection": True,
            "creator_rows_found":
                len(creators)
                if isinstance(creators, list)
                else 0,
            "admin_rows_found":
                len(admin)
                if isinstance(admin, list)
                else 0
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ==========================================
# EJECUTAR
# ==========================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print(" VERTEXMONT")
    print("==========================================")

    print(
        "Supabase:"
    )

    print(
        SUPABASE_URL
        if SUPABASE_URL
        else "NO CONFIGURADO"
    )

    print()

    print(
        "Tabla de creadores:"
    )

    print(
        CREATORS_TABLE
    )

    print()

    print(
        "Tabla de administrador:"
    )

    print(
        ADMIN_TABLE
    )

    print()

    print(
        "Supabase configurado:",
        supabase_configured()
    )

    print(
        "=========================================="
    )

    print()

    app.run(
        debug=False
    )