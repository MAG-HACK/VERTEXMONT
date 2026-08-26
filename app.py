
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
import uuid
import requests

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from werkzeug.utils import secure_filename


# ============================================================
# APP
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "vertex_month_secret_2026_change_this"
)

app.permanent_session_lifetime = 60 * 60 * 24 * 7


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    ""
).rstrip("/")

SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    ""
)

SUPABASE_STORAGE_BUCKET = os.environ.get(
    "SUPABASE_STORAGE_BUCKET",
    "creator-photos"
)

CREATORS_TABLE = os.environ.get(
    "SUPABASE_CREATORS_TABLE",
    "creators"
)

ADMIN_TABLE = os.environ.get(
    "SUPABASE_ADMIN_TABLE",
    "admin"
)


# ============================================================
# ADMIN
# ============================================================

ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


# ============================================================
# VALIDAR CONFIGURACIÓN
# ============================================================

def supabase_configured():
    return bool(
        SUPABASE_URL
        and SUPABASE_KEY
    )


# ============================================================
# HEADERS SUPABASE
# ============================================================

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }


# ============================================================
# URL TABLA SUPABASE
# ============================================================

def table_url(table_name):
    return (
        f"{SUPABASE_URL}/rest/v1/{table_name}"
    )


# ============================================================
# ERROR SUPABASE
# ============================================================

def supabase_error(response):
    try:
        return response.text
    except Exception:
        return "Error desconocido de Supabase."


# ============================================================
# GET CREADORES
# ============================================================

def load_creators():
    if not supabase_configured():
        print("ERROR: Supabase no está configurado.")
        return []

    try:
        response = requests.get(
            table_url(CREATORS_TABLE),
            headers={
                **supabase_headers(),
                "Accept": "application/json"
            },
            params={
                "select": "*",
                "order": "name.asc"
            },
            timeout=20
        )

        if not response.ok:
            print(
                "ERROR cargando creadores:",
                response.status_code,
                response.text
            )
            return []

        data = response.json()

        if not isinstance(data, list):
            print(
                "ERROR: Supabase no devolvió una lista de creadores."
            )
            return []

        return data

    except Exception as error:
        print(
            "ERROR conectando con Supabase:",
            error
        )
        return []


# ============================================================
# NORMALIZAR HANDLE
# ============================================================

def normalize_handle(value):
    value = str(value or "").strip()

    if not value:
        return ""

    if "tiktok.com/@" in value:
        try:
            value = (
                value
                .split("tiktok.com/@", 1)[1]
                .split("?", 1)[0]
                .split("/", 1)[0]
            )
        except Exception:
            pass

    value = value.lstrip("@")

    if not value:
        return ""

    return "@" + value


# ============================================================
# URL TIKTOK
# ============================================================

def get_tiktok_url(value):
    handle = normalize_handle(value)

    if not handle:
        return ""

    username = handle.lstrip("@")

    return (
        "https://www.tiktok.com/@"
        + username
    )


# ============================================================
# PASSWORD HASH
# ============================================================

def is_password_hash(value):
    value = str(value or "")

    return (
        value.startswith("scrypt:")
        or value.startswith("pbkdf2:")
        or value.startswith("argon2:")
    )


# ============================================================
# VERIFICAR PASSWORD
# ============================================================

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

    # Compatibilidad con contraseña antigua
    return stored_password == entered_password


# ============================================================
# CARGAR ADMIN
# ============================================================

def load_admin():
    if not supabase_configured():
        print(
            "ERROR: Supabase no está configurado."
        )
        return None

    try:
        response = requests.get(
            table_url(ADMIN_TABLE),
            headers={
                **supabase_headers(),
                "Accept": "application/json"
            },
            params={
                "select": "*",
                "username": f"eq.{ADMIN_USERNAME}",
                "limit": "1"
            },
            timeout=20
        )

        if not response.ok:
            print(
                "ERROR cargando admin:",
                response.status_code,
                response.text
            )
            return None

        data = response.json()

        if not data:
            return None

        return data[0]

    except Exception as error:
        print(
            "ERROR conectando con tabla admin:",
            error
        )
        return None


# ============================================================
# GUARDAR PASSWORD ADMIN
# ============================================================

def save_admin_password(new_password):
    admin_data = load_admin()

    if not admin_data:
        return False

    admin_id = admin_data.get("id")

    password_hash = generate_password_hash(
        new_password
    )

    try:
        response = requests.patch(
            table_url(ADMIN_TABLE),
            headers={
                **supabase_headers(),
                "Prefer": "return=representation"
            },
            params={
                "id": f"eq.{admin_id}"
            },
            json={
                "password": password_hash
            },
            timeout=20
        )

        if not response.ok:
            print(
                "ERROR guardando contraseña:",
                response.status_code,
                response.text
            )
            return False

        return True

    except Exception as error:
        print(
            "ERROR actualizando contraseña:",
            error
        )
        return False


# ============================================================
# STORAGE — URL PÚBLICA
# ============================================================

def storage_public_url(path):
    if not path:
        return ""

    return (
        f"{SUPABASE_URL}/storage/v1/object/public/"
        f"{SUPABASE_STORAGE_BUCKET}/{path}"
    )


# ============================================================
# STORAGE — SUBIR FOTO
# ============================================================

def upload_photo(file):
    if not file:
        return ""

    if not file.filename:
        return ""

    original_name = secure_filename(
        file.filename
    )

    extension = os.path.splitext(
        original_name
    )[1].lower()

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }

    if extension not in allowed_extensions:
        raise ValueError(
            "Formato de imagen no permitido. "
            "Usa JPG, JPEG, PNG o WEBP."
        )

    # UUID para evitar colisiones
    filename = (
        str(uuid.uuid4())
        + extension
    )

    storage_path = (
        "creators/"
        + filename
    )

    upload_url = (
        f"{SUPABASE_URL}/storage/v1/object/"
        f"{SUPABASE_STORAGE_BUCKET}/"
        f"{storage_path}"
    )

    content_type = file.content_type

    if not content_type:
        content_type = "application/octet-stream"

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": content_type,
        "x-upsert": "false"
    }

    try:
        file.stream.seek(0)

        response = requests.post(
            upload_url,
            headers=headers,
            data=file.stream,
            timeout=60
        )

        if not response.ok:
            raise RuntimeError(
                "Supabase Storage "
                f"{response.status_code}: "
                f"{response.text}"
            )

        return storage_path

    except Exception as error:
        print(
            "ERROR subiendo foto:",
            error
        )
        raise


# ============================================================
# STORAGE — ELIMINAR FOTO
# ============================================================

def delete_photo(storage_path):
    if not storage_path:
        return True

    delete_url = (
        f"{SUPABASE_URL}/storage/v1/object/"
        f"{SUPABASE_STORAGE_BUCKET}"
    )

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.delete(
            delete_url,
            headers=headers,
            json={
                "prefixes": [
                    storage_path
                ]
            },
            timeout=30
        )

        if not response.ok:
            print(
                "AVISO: no se pudo eliminar "
                "la foto antigua:",
                response.text
            )
            return False

        return True

    except Exception as error:
        print(
            "AVISO eliminando foto:",
            error
        )
        return False


# ============================================================
# OBTENER IDENTIFICADOR DEL CREADOR
# ============================================================

def find_creator_filter(creator_id):
    """
    Permite trabajar tanto con:
    - id bigint
    - creator_uuid uuid

    Así no rompemos los creadores existentes.
    """

    creator_id = str(
        creator_id or ""
    ).strip()

    if not creator_id:
        return None

    # UUID
    try:
        uuid.UUID(creator_id)

        return {
            "creator_uuid": creator_id
        }

    except ValueError:
        pass

    # bigint
    try:
        int(creator_id)

        return {
            "id": creator_id
        }

    except ValueError:
        return None


# ============================================================
# BUSCAR CREADOR
# ============================================================

def get_creator(creator_id):
    creator_filter = find_creator_filter(
        creator_id
    )

    if not creator_filter:
        return None

    column, value = next(
        iter(creator_filter.items())
    )

    try:
        response = requests.get(
            table_url(CREATORS_TABLE),
            headers={
                **supabase_headers(),
                "Accept": "application/json"
            },
            params={
                "select": "*",
                column: f"eq.{value}",
                "limit": "1"
            },
            timeout=20
        )

        if not response.ok:
            print(
                "ERROR buscando creador:",
                response.status_code,
                response.text
            )
            return None

        data = response.json()

        if not data:
            return None

        return data[0]

    except Exception as error:
        print(
            "ERROR buscando creador:",
            error
        )
        return None


# ============================================================
# INICIO
# ============================================================

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


# ============================================================
# LOGIN
# ============================================================

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
    print("==========================================")

    admin_data = load_admin()

    if not admin_data:
        return (
            "No se pudo cargar el administrador desde Supabase.",
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

    # Convertir contraseña antigua a hash
    if (
        password_correct
        and not is_password_hash(
            stored_password
        )
    ):

        save_admin_password(
            password
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


# ============================================================
# CAMBIAR CONTRASEÑA
# ============================================================

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

    saved = save_admin_password(
        new_password
    )

    if not saved:
        return jsonify({
            "success": False,
            "error":
                "No se pudo guardar la nueva contraseña."
        }), 500

    # Verificación
    verify_data = load_admin()

    if not verify_data:
        return jsonify({
            "success": False,
            "error":
                "No se pudo verificar la contraseña."
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
    })


# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/logout",
    methods=["POST"]
)
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# ============================================================
# AGREGAR CREADOR
# ============================================================

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

    # ========================================================
    # UUID PROPIO
    #
    # IMPORTANTE:
    # NO enviamos "id".
    #
    # Supabase genera automáticamente el id bigint.
    # Python genera creator_uuid.
    # ========================================================

    creator_uuid = str(
        uuid.uuid4()
    )

    # ========================================================
    # FOTO
    # ========================================================

    photo_url = ""

    photo_storage_path = ""

    try:

        if (
            "photo" in request.files
            and request.files["photo"].filename
        ):

            photo_storage_path = upload_photo(
                request.files["photo"]
            )

            photo_url = storage_public_url(
                photo_storage_path
            )

    except Exception as error:

        return jsonify({
            "error":
                f"No se pudo subir la foto: {error}"
        }), 500

    # ========================================================
    # HANDLE
    # ========================================================

    handle = normalize_handle(
        request.form.get(
            "handle",
            ""
        )
    )

    # ========================================================
    # DATOS
    # ========================================================

    creator = {

        # UUID
        "creator_uuid":
            creator_uuid,

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
            photo_url,

        "photo_storage_path":
            photo_storage_path
    }

    # ========================================================
    # GUARDAR EN SUPABASE
    #
    # NOTA:
    # "id" NO aparece aquí.
    # Supabase genera el bigint automáticamente.
    # ========================================================

    try:

        response = requests.post(
            table_url(CREATORS_TABLE),
            headers={
                **supabase_headers(),
                "Prefer": "return=representation"
            },
            json=creator,
            timeout=30
        )

        if not response.ok:

            # Si falló DB después de subir foto,
            # intentamos eliminar la foto para no dejar basura.
            if photo_storage_path:
                delete_photo(
                    photo_storage_path
                )

            return jsonify({
                "error":
                    "No se pudo guardar el creador en Supabase: "
                    + supabase_error(response)
            }), 500

        data = response.json()

        if isinstance(data, list) and data:
            return jsonify(data[0])

        return jsonify(creator)

    except Exception as error:

        if photo_storage_path:
            delete_photo(
                photo_storage_path
            )

        return jsonify({
            "error":
                f"Error conectando con Supabase: {error}"
        }), 500


# ============================================================
# EDITAR CREADOR
# ============================================================

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

    creator = get_creator(
        creator_id
    )

    if not creator:
        return jsonify({
            "error":
                "Creador no encontrado"
        }), 404

    # ========================================================
    # HANDLE
    # ========================================================

    handle = normalize_handle(
        request.form.get(
            "handle",
            ""
        )
    )

    # ========================================================
    # CAMPOS
    # ========================================================

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

    update_data = {}

    for field in fields:

        update_data[field] = (
            request.form.get(
                field,
                ""
            ).strip()
        )

    update_data["handle"] = handle

    # ========================================================
    # TIKTOK
    # ========================================================

    tiktok_value = request.form.get(
        "tiktok",
        ""
    ).strip()

    if not tiktok_value:
        tiktok_value = handle

    update_data["tiktok"] = get_tiktok_url(
        tiktok_value
    )

    # ========================================================
    # FOTO NUEVA
    # ========================================================

    new_photo_path = ""

    try:

        if (
            "photo" in request.files
            and request.files["photo"].filename
        ):

            new_photo_path = upload_photo(
                request.files["photo"]
            )

            update_data["photo"] = (
                storage_public_url(
                    new_photo_path
                )
            )

            update_data[
                "photo_storage_path"
            ] = new_photo_path

    except Exception as error:

        return jsonify({
            "error":
                f"No se pudo subir la nueva foto: {error}"
        }), 500

    # ========================================================
    # FILTRO
    # ========================================================

    creator_filter = find_creator_filter(
        creator_id
    )

    if not creator_filter:

        if new_photo_path:
            delete_photo(
                new_photo_path
            )

        return jsonify({
            "error":
                "Identificador de creador inválido."
        }), 400

    column, value = next(
        iter(creator_filter.items())
    )

    # ========================================================
    # ACTUALIZAR
    # ========================================================

    try:

        response = requests.patch(
            table_url(CREATORS_TABLE),
            headers={
                **supabase_headers(),
                "Prefer": "return=representation"
            },
            params={
                column: f"eq.{value}"
            },
            json=update_data,
            timeout=30
        )

        if not response.ok:

            if new_photo_path:
                delete_photo(
                    new_photo_path
                )

            return jsonify({
                "error":
                    "No se pudieron guardar los cambios: "
                    + supabase_error(response)
            }), 500

        data = response.json()

        # ====================================================
        # ELIMINAR FOTO ANTERIOR
        # SOLO DESPUÉS DE ACTUALIZAR CORRECTAMENTE
        # ====================================================

        if new_photo_path:

            old_photo_path = creator.get(
                "photo_storage_path",
                ""
            )

            if old_photo_path:
                delete_photo(
                    old_photo_path
                )

        if isinstance(data, list) and data:

            return jsonify(data[0])

        updated_creator = {
            **creator,
            **update_data
        }

        return jsonify(
            updated_creator
        )

    except Exception as error:

        if new_photo_path:
            delete_photo(
                new_photo_path
            )

        return jsonify({
            "error":
                f"Error actualizando Supabase: {error}"
        }), 500


# ============================================================
# ELIMINAR CREADOR
# ============================================================

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

    creator = get_creator(
        creator_id
    )

    if not creator:
        return jsonify({
            "error":
                "Creador no encontrado"
        }), 404

    creator_filter = find_creator_filter(
        creator_id
    )

    if not creator_filter:
        return jsonify({
            "error":
                "Identificador inválido."
        }), 400

    column, value = next(
        iter(creator_filter.items())
    )

    try:

        response = requests.delete(
            table_url(CREATORS_TABLE),
            headers={
                **supabase_headers(),
                "Prefer": "return=minimal"
            },
            params={
                column: f"eq.{value}"
            },
            timeout=30
        )

        if not response.ok:

            return jsonify({
                "error":
                    "No se pudo eliminar el creador: "
                    + supabase_error(response)
            }), 500

        # ====================================================
        # ELIMINAR FOTO DE STORAGE
        # ====================================================

        old_photo_path = creator.get(
            "photo_storage_path",
            ""
        )

        if old_photo_path:
            delete_photo(
                old_photo_path
            )

        return jsonify({
            "success": True
        })

    except Exception as error:

        return jsonify({
            "error":
                f"Error eliminando creador: {error}"
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health"
)
def health():

    if not supabase_configured():

        return jsonify({
            "status": "error",
            "supabase": False
        }), 500

    try:

        response = requests.get(
            table_url(CREATORS_TABLE),
            headers={
                **supabase_headers(),
                "Accept": "application/json"
            },
            params={
                "select": "id",
                "limit": "1"
            },
            timeout=10
        )

        if not response.ok:

            return jsonify({
                "status": "error",
                "supabase": False,
                "code":
                    response.status_code,
                "message":
                    response.text
            }), 500

        return jsonify({
            "status": "ok",
            "supabase": True
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "supabase": False,
            "message": str(error)
        }), 500

# ============================================================
# PERFIL PÚBLICO DEL CREADOR
# ============================================================
@app.route("/creator/<creator_uuid>")
def public_creator(creator_uuid):
    try:
        uuid.UUID(creator_uuid)
    except ValueError:
        return "Enlace de creador inválido.", 404

    creator = get_creator(creator_uuid)

    if not creator:
        return "Creador no encontrado.", 404

    return render_template(
        "index.html",
        creators=[creator],
        admin=False,
        shared_creator=creator
    )
# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print(" VERTEXMONT")
    print("==========================================")

    print(
        "Supabase URL:",
        SUPABASE_URL
    )

    print(
        "Tabla de creadores:",
        CREATORS_TABLE
    )

    print(
        "Tabla de administrador:",
        ADMIN_TABLE
    )

    print(
        "Bucket de fotos:",
        SUPABASE_STORAGE_BUCKET
    )

    print(
        "Supabase configurado:",
        supabase_configured()
    )

    print("==========================================")
    print()

    app.run(
        debug=False
    )

