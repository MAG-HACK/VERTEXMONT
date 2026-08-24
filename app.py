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
import requests

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
# CARPETAS LOCALES
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

SUPABASE_STORAGE_BUCKET = os.environ.get(
    "SUPABASE_STORAGE_BUCKET",
    "creator-photos"
)

CREATORS_TABLE = "creators"
ADMIN_TABLE = "admin"


# ==========================================
# ARCHIVOS LOCALES DE RESPALDO
# ==========================================

DATA_FILE = os.path.join(
    DATA_DIR,
    "data.json"
)

ADMIN_FILE = os.path.join(
    DATA_DIR,
    "admin.json"
)


# ==========================================
# ADMIN
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


def supabase_headers():

    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }


def supabase_storage_headers():

    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }


# ==========================================
# SUPABASE REQUEST
# ==========================================

def supabase_request(
    method,
    endpoint,
    **kwargs
):

    if not supabase_configured():

        raise Exception(
            "SUPABASE_URL o SUPABASE_KEY no están configuradas."
        )

    url = (
        SUPABASE_URL
        + endpoint
    )

    headers = kwargs.pop(
        "headers",
        {}
    )

    final_headers = supabase_headers()

    final_headers.update(
        headers
    )

    response = requests.request(
        method,
        url,
        headers=final_headers,
        timeout=30,
        **kwargs
    )

    if not response.ok:

        raise Exception(
            f"Supabase HTTP {response.status_code}: "
            f"{response.text}"
        )

    if not response.text:

        return None

    try:

        return response.json()

    except Exception:

        return response.text


# ==========================================
# CREAR DATA.JSON LOCAL SI NO EXISTE
# ==========================================

if not os.path.exists(DATA_FILE):

    try:

        with open(
            DATA_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                [],
                file,
                ensure_ascii=False,
                indent=4
            )

    except Exception as error:

        print(
            "ERROR creando data.json:",
            error
        )


# ==========================================
# NORMALIZAR HANDLE
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
# DETECTAR HASH
# ==========================================

def is_password_hash(value):

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
# ADMIN - SUPABASE
# ==========================================

def load_admin():

    try:

        if supabase_configured():

            data = supabase_request(
                "GET",
                f"/rest/v1/{ADMIN_TABLE}"
                "?select=*"
                "&limit=1"
            )

            if isinstance(
                data,
                list
            ) and data:

                return data[0]

            return None

        # ----------------------------------
        # RESPALDO LOCAL
        # ----------------------------------

        if not os.path.exists(
            ADMIN_FILE
        ):

            admin_data = {
                "username": ADMIN_USERNAME,
                "password":
                    generate_password_hash(
                        DEFAULT_ADMIN_PASSWORD
                    )
            }

            save_admin(
                admin_data
            )

            return admin_data

        with open(
            ADMIN_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            "ERROR cargando administrador:",
            error
        )

        return None


# ==========================================
# ADMIN - GUARDAR
# ==========================================

def save_admin(admin_data):

    try:

        if supabase_configured():

            existing = supabase_request(
                "GET",
                f"/rest/v1/{ADMIN_TABLE}"
                "?select=id"
                "&limit=1"
            )

            if (
                isinstance(existing, list)
                and existing
            ):

                admin_id = existing[0]["id"]

                supabase_request(
                    "PATCH",
                    f"/rest/v1/{ADMIN_TABLE}"
                    f"?id=eq.{admin_id}",
                    json={
                        "username":
                            admin_data.get(
                                "username",
                                ADMIN_USERNAME
                            ),
                        "password":
                            admin_data.get(
                                "password",
                                ""
                            )
                    }
                )

            else:

                supabase_request(
                    "POST",
                    f"/rest/v1/{ADMIN_TABLE}",
                    json={
                        "username":
                            admin_data.get(
                                "username",
                                ADMIN_USERNAME
                            ),
                        "password":
                            admin_data.get(
                                "password",
                                ""
                            )
                    }
                )

            return True

        # ----------------------------------
        # RESPALDO LOCAL
        # ----------------------------------

        temp_file = ADMIN_FILE + ".tmp"

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

        os.replace(
            temp_file,
            ADMIN_FILE
        )

        return True

    except Exception as error:

        print(
            "ERROR GUARDANDO ADMIN:",
            error
        )

        return False


# ==========================================
# CREADORES - SUPABASE
# ==========================================

def load_creators():

    try:

        if supabase_configured():

            data = supabase_request(
                "GET",
                f"/rest/v1/{CREATORS_TABLE}"
                "?select=*"
                "&order=name.asc"
            )

            if isinstance(
                data,
                list
            ):

                return data

            return []

        # ----------------------------------
        # RESPALDO LOCAL
        # ----------------------------------

        if not os.path.exists(
            DATA_FILE
        ):

            return []

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(
            data,
            list
        ):

            return data

        if isinstance(
            data,
            dict
        ):

            creators = data.get(
                "creators",
                []
            )

            if isinstance(
                creators,
                list
            ):

                return creators

        return []

    except Exception as error:

        print(
            "ERROR cargando creadores:",
            error
        )

        return []


# ==========================================
# GUARDAR CREADORES LOCAL
# ==========================================

def save_creators(creators):

    try:

        temp_file = DATA_FILE + ".tmp"

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                creators,
                file,
                ensure_ascii=False,
                indent=4
            )

            file.flush()

        os.replace(
            temp_file,
            DATA_FILE
        )

        return True

    except Exception as error:

        print(
            "ERROR GUARDANDO data.json:",
            error
        )

        return False


# ==========================================
# SUPABASE STORAGE
# ==========================================

def upload_photo_to_supabase(file):

    if not file or not file.filename:

        return ""

    if not supabase_configured():

        raise Exception(
            "Supabase no está configurado."
        )

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

    storage_path = filename

    file_content = file.read()

    if not file_content:

        raise Exception(
            "La imagen está vacía."
        )

    content_type = (
        file.content_type
        or "application/octet-stream"
    )

    url = (
        SUPABASE_URL
        + "/storage/v1/object/"
        + SUPABASE_STORAGE_BUCKET
        + "/"
        + storage_path
    )

    headers = supabase_storage_headers()

    headers["Content-Type"] = content_type

    headers["x-upsert"] = "false"

    response = requests.post(
        url,
        headers=headers,
        data=file_content,
        timeout=60
    )

    if not response.ok:

        raise Exception(
            f"No se pudo subir la foto: "
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )

    public_url = (
        SUPABASE_URL
        + "/storage/v1/object/public/"
        + SUPABASE_STORAGE_BUCKET
        + "/"
        + storage_path
    )

    return public_url


# ==========================================
# ELIMINAR FOTO DE SUPABASE
# ==========================================

def delete_photo_from_supabase(photo_url):

    if not photo_url:

        return True

    if not supabase_configured():

        return True

    marker = (
        "/storage/v1/object/public/"
        + SUPABASE_STORAGE_BUCKET
        + "/"
    )

    if marker not in photo_url:

        return True

    storage_path = photo_url.split(
        marker,
        1
    )[1]

    url = (
        SUPABASE_URL
        + "/storage/v1/object/"
        + SUPABASE_STORAGE_BUCKET
    )

    try:

        response = requests.delete(
            url,
            headers={
                **supabase_storage_headers(),
                "Content-Type":
                    "application/json"
            },
            json={
                "prefixes": [
                    storage_path
                ]
            },
            timeout=30
        )

        if response.ok:

            return True

        print(
            "No se pudo eliminar foto:",
            response.text
        )

        return False

    except Exception as error:

        print(
            "ERROR eliminando foto:",
            error
        )

        return False


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

        return redirect(
            url_for("index")
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

    if not save_admin(
        admin_data
    ):

        return jsonify({
            "success": False,
            "error":
                "No se pudo guardar la nueva contraseña."
        }), 500

    verify_data = load_admin()

    if not verify_data:

        return jsonify({
            "success": False,
            "error":
                "No se pudo verificar la contraseña."
        }), 500

    if not verify_password(
        verify_data.get(
            "password",
            ""
        ),
        new_password
    ):

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

    try:

        handle = normalize_handle(
            request.form.get(
                "handle",
                ""
            )
        )

        photo_url = ""

        # ==================================
        # SUBIR FOTO A SUPABASE
        # ==================================

        if (
            "photo" in request.files
            and request.files["photo"].filename
        ):

            photo_url = (
                upload_photo_to_supabase(
                    request.files["photo"]
                )
            )

        creator = {

            "id":
                str(uuid.uuid4()),

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
                photo_url
        }

        # ==================================
        # SUPABASE
        # ==================================

        if supabase_configured():

            result = supabase_request(
                "POST",
                f"/rest/v1/{CREATORS_TABLE}",
                headers={
                    "Prefer":
                        "return=representation"
                },
                json=creator
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

        # ==================================
        # LOCAL
        # ==================================

        creators = load_creators()

        creators.append(
            creator
        )

        if not save_creators(
            creators
        ):

            return jsonify({
                "error":
                    "No se pudieron guardar los datos."
            }), 500

        return jsonify(
            creator
        )

    except Exception as error:

        print(
            "ERROR agregando creador:",
            error
        )

        return jsonify({
            "error":
                f"No se pudo guardar el creador: {error}"
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

    try:

        creators = load_creators()

        creator = next(
            (
                item
                for item in creators
                if str(
                    item.get("id")
                ) == str(creator_id)
            ),
            None
        )

        if not creator:

            return jsonify({
                "error":
                    "Creador no encontrado"
            }), 404

        old_photo = creator.get(
            "photo",
            ""
        )

        handle = normalize_handle(
            request.form.get(
                "handle",
                ""
            )
        )

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

        creator["handle"] = handle

        for field in fields:

            creator[field] = (
                request.form.get(
                    field,
                    ""
                ).strip()
            )

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

        # ==================================
        # FOTO NUEVA
        # ==================================

        if (
            "photo" in request.files
            and request.files["photo"].filename
        ):

            new_photo = (
                upload_photo_to_supabase(
                    request.files["photo"]
                )
            )

            creator["photo"] = new_photo

            if (
                old_photo
                and old_photo != new_photo
            ):

                delete_photo_from_supabase(
                    old_photo
                )

        # ==================================
        # SUPABASE
        # ==================================

        if supabase_configured():

            result = supabase_request(
                "PATCH",
                f"/rest/v1/{CREATORS_TABLE}"
                f"?id=eq.{creator_id}",
                headers={
                    "Prefer":
                        "return=representation"
                },
                json=creator
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

        # ==================================
        # LOCAL
        # ==================================

        if not save_creators(
            creators
        ):

            return jsonify({
                "error":
                    "No se pudieron guardar los cambios."
            }), 500

        return jsonify(
            creator
        )

    except Exception as error:

        print(
            "ERROR editando creador:",
            error
        )

        return jsonify({
            "error":
                f"No se pudo editar el creador: {error}"
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

    try:

        creators = load_creators()

        creator = next(
            (
                item
                for item in creators
                if str(
                    item.get("id")
                ) == str(creator_id)
            ),
            None
        )

        if not creator:

            return jsonify({
                "error":
                    "Creador no encontrado"
            }), 404

        photo = creator.get(
            "photo",
            ""
        )

        # ==================================
        # SUPABASE
        # ==================================

        if supabase_configured():

            supabase_request(
                "DELETE",
                f"/rest/v1/{CREATORS_TABLE}"
                f"?id=eq.{creator_id}"
            )

            if photo:

                delete_photo_from_supabase(
                    photo
                )

            return jsonify({
                "success": True
            })

        # ==================================
        # LOCAL
        # ==================================

        new_creators = [
            creator
            for creator in creators
            if str(
                creator.get("id")
            ) != str(creator_id)
        ]

        if not save_creators(
            new_creators
        ):

            return jsonify({
                "error":
                    "No se pudo eliminar el creador."
            }), 500

        return jsonify({
            "success": True
        })

    except Exception as error:

        print(
            "ERROR eliminando creador:",
            error
        )

        return jsonify({
            "error":
                f"No se pudo eliminar el creador: {error}"
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
        "Supabase:",
        "CONECTADO"
        if supabase_configured()
        else "NO CONFIGURADO"
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

    print("==========================================")
    print()

    app.run(
        debug=True
    )