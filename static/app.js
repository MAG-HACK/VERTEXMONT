let creatorList = [...creators];

let currentCreator = null;

const PLACEHOLDER =
    "https://placehold.co/600x600?text=Creator";


/* =========================================
   MOSTRAR CREADORES
========================================= */

function renderCreators() {

    const grid =
        document.getElementById("creatorGrid");

    const search =
        document
            .getElementById("search")
            .value
            .toLowerCase()
            .trim();


    const filtered =
        creatorList.filter(creator => {

            const name =
                String(creator.name || "")
                    .toLowerCase();

            const handle =
                String(creator.handle || "")
                    .toLowerCase();

            return (
                name.includes(search) ||
                handle.includes(search)
            );

        });


    grid.innerHTML = "";


    if (!filtered.length) {

        grid.innerHTML = `
            <div class="empty">
                <h3>No encontramos creadores</h3>
                <p>Busca otro creador.</p>
            </div>
        `;

        return;

    }


    filtered.forEach(creator => {

        const card =
            document.createElement("article");

        card.className =
            "creator-card";


        card.innerHTML = `

            <img
                class="creator-image"
                src="${creator.photo || PLACEHOLDER}"
                alt="${escapeHtml(
                    creator.name || "Creator"
                )}"
            >

            <div class="creator-info">

                <h3>
                    ${escapeHtml(
                        creator.name || "Sin nombre"
                    )}
                </h3>

                <div class="handle">
                    ${escapeHtml(
                        creator.handle || ""
                    )}
                </div>

                <div class="card-stats">

                    <span class="stat-pill">
                        👥 ${escapeHtml(
                            creator.followers || "—"
                        )}
                    </span>

                    <span class="stat-pill">
                        👁 ${escapeHtml(
                            creator.views || "—"
                        )}
                    </span>

                </div>

            </div>

        `;


        card.onclick = () => {

            openProfile(creator);

        };


        grid.appendChild(card);

    });

}


/* =========================================
   PERFIL
========================================= */

function openProfile(creator) {

    currentCreator = creator;


    document.getElementById("profilePhoto").src =
        creator.photo || PLACEHOLDER;

    document.getElementById("profileName").textContent =
        creator.name || "Sin nombre";

    document.getElementById("profileHandle").textContent =
        creator.handle || "";

    document.getElementById("profileCategory").textContent =
        creator.category || "Sin categoría";

    document.getElementById("profileCountry").textContent =
        creator.country || "Sin país";

    document.getElementById("profileFollowers").textContent =
        creator.followers || "—";

    document.getElementById("profileLikes").textContent =
        creator.likes || "—";

    document.getElementById("profileViews").textContent =
        creator.views || "—";

    document.getElementById("profileVideos").textContent =
        creator.videos || "—";

    document.getElementById("profileEngagement").textContent =
        creator.engagement || "—";

    document.getElementById("profileAverageLikes").textContent =
        creator.average_likes || "—";

    document.getElementById("profileAverageComments").textContent =
        creator.average_comments || "—";

    document.getElementById("profileAverageShares").textContent =
        creator.average_shares || "—";


    const socials =
        document.getElementById("socialLinks");


    socials.innerHTML = "";


    /*
    =====================================
    REDES SOCIALES
    =====================================
    */

    addSocial(
        socials,
        "🎵 TikTok",
        creator.tiktok,
        "tiktok"
    );


    addSocial(
        socials,
        "📸 Instagram",
        creator.instagram,
        "instagram"
    );


    addSocial(
        socials,
        "▶ YouTube",
        creator.youtube,
        "youtube"
    );


    if (!socials.innerHTML) {

        socials.innerHTML = `
            <span class="handle">
                No hay redes agregadas.
            </span>
        `;

    }


    document
        .getElementById("profileModal")
        .classList.add("open");

}


function closeProfile() {

    document
        .getElementById("profileModal")
        .classList.remove("open");

}


/* =========================================
   CREAR LINKS DE REDES
========================================= */

function addSocial(
    container,
    name,
    value,
    platform
) {

    if (!value) return;


    const url =
        getSocialUrl(
            value,
            platform
        );


    container.innerHTML += `

        <a
            class="social-link"
            href="${escapeHtml(url)}"
            target="_blank"
            rel="noopener noreferrer"
        >
            ${name}
        </a>

    `;

}


/* =========================================
   GENERAR URL CORRECTA
========================================= */

function getSocialUrl(
    value,
    platform
) {

    let username =
        String(value || "")
            .trim();


    if (!username) {

        return "#";

    }


    /*
    Si ya es una URL completa
    */

    if (
        username.startsWith("http://") ||
        username.startsWith("https://")
    ) {

        return username;

    }


    /*
    Quitar @
    */

    username =
        username.replace(
            /^@/,
            ""
        );


    /*
    TIKTOK
    */

    if (platform === "tiktok") {

        return (
            "https://www.tiktok.com/@"
            + username
        );

    }


    /*
    INSTAGRAM
    */

    if (platform === "instagram") {

        return (
            "https://www.instagram.com/"
            + username
            + "/"
        );

    }


    /*
    YOUTUBE
    */

    if (platform === "youtube") {

        /*
        Si es @canal
        */

        if (
            String(value)
                .trim()
                .startsWith("@")
        ) {

            return (
                "https://www.youtube.com/@"
                + username
            );

        }


        /*
        Buscar el canal
        */

        return (
            "https://www.youtube.com/results?search_query="
            + encodeURIComponent(username)
        );

    }


    return username;

}


/* =========================================
   MENÚ
========================================= */

function openMenu() {

    document
        .getElementById("menuOverlay")
        .classList.add("open");

}


function closeMenu() {

    document
        .getElementById("menuOverlay")
        .classList.remove("open");

}


function closeMenuOutside(event) {

    if (
        event.target.id === "menuOverlay"
    ) {

        closeMenu();

    }

}


/* =========================================
   TEMAS
========================================= */

function setTheme(theme) {

    localStorage.setItem(
        "vertex-theme",
        theme
    );

    applyTheme();

}


function applyTheme() {

    const theme =
        localStorage.getItem(
            "vertex-theme"
        ) || "system";


    if (theme === "dark") {

        document.documentElement
            .setAttribute(
                "data-theme",
                "dark"
            );

        return;

    }


    if (theme === "light") {

        document.documentElement
            .setAttribute(
                "data-theme",
                "light"
            );

        return;

    }


    const dark =
        window.matchMedia(
            "(prefers-color-scheme: dark)"
        ).matches;


    document.documentElement
        .setAttribute(
            "data-theme",
            dark
                ? "dark"
                : "light"
        );

}


/* =========================================
   ORDENAR
========================================= */

function sortCreators(type) {

    if (type === "az") {

        creatorList.sort(
            (a, b) =>
                String(a.name || "")
                    .localeCompare(
                        String(b.name || "")
                    )
        );

    }


    if (type === "za") {

        creatorList.sort(
            (a, b) =>
                String(b.name || "")
                    .localeCompare(
                        String(a.name || "")
                    )
        );

    }


    if (type === "followers") {

        creatorList.sort(
            (a, b) =>
                numberValue(b.followers)
                -
                numberValue(a.followers)
        );

    }


    if (type === "views") {

        creatorList.sort(
            (a, b) =>
                numberValue(b.views)
                -
                numberValue(a.views)
        );

    }


    renderCreators();

    closeMenu();

}


function numberValue(value) {

    if (!value) return 0;

    return (
        parseFloat(
            String(value)
                .replace(/,/g, "")
                .replace(/[^\d.]/g, "")
        )
        || 0
    );

}


/* =========================================
   LOGIN
========================================= */

function openLogin() {

    document
        .getElementById("loginModal")
        .classList.add("open");

}


function closeLogin() {

    document
        .getElementById("loginModal")
        .classList.remove("open");

}


function logout() {

    const form =
        document.createElement("form");

    form.method = "POST";

    form.action = "/logout";

    document.body.appendChild(form);

    form.submit();

}


/* =========================================
   AGREGAR / EDITAR
========================================= */

function openCreator(creator = null) {

    if (!IS_ADMIN) {

        openLogin();

        return;

    }


    currentCreator = creator;


    const modal =
        document.getElementById("creatorModal");

    const form =
        document.getElementById("creatorForm");


    form.reset();


    document.getElementById(
        "creatorModalTitle"
    ).textContent =
        creator
            ? "Editar creador"
            : "Agregar creador";


    const status =
        document.getElementById("csvStatus");

    status.textContent = "";

    status.className =
        "csv-status";


    if (creator) {

        const fields = [

            "name",
            "handle",
            "category",
            "country",
            "followers",
            "likes",
            "views",
            "videos",
            "engagement",
            "tiktok",
            "instagram",
            "youtube",
            "average_likes",
            "average_comments",
            "average_shares"

        ];


        fields.forEach(field => {

            if (form.elements[field]) {

                form.elements[field].value =
                    creator[field] || "";

            }

        });

    }


    modal.classList.add("open");

}


function closeCreator() {

    document
        .getElementById("creatorModal")
        .classList.remove("open");

}


/* =========================================
   GUARDAR
========================================= */

document
    .getElementById("creatorForm")
    .addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            const form =
                document.getElementById(
                    "creatorForm"
                );


            const data =
                new FormData(form);


            const url =
                currentCreator
                    ? `/api/creator/${currentCreator.id}`
                    : "/api/creator";


            const response =
                await fetch(
                    url,
                    {
                        method: "POST",
                        body: data
                    }
                );


            const result =
                await response.json();


            if (!response.ok) {

                alert(
                    result.error ||
                    "No se pudo guardar."
                );

                return;

            }


            if (currentCreator) {

                creatorList =
                    creatorList.map(
                        creator =>
                            creator.id === result.id
                                ? result
                                : creator
                    );

            } else {

                creatorList.unshift(result);

            }


            currentCreator = null;

            closeCreator();

            renderCreators();

        }
    );


/* =========================================
   IMPORTAR CSV
========================================= */

const csvFile =
    document.getElementById("csvFile");


csvFile.addEventListener(
    "change",
    handleCsv
);


async function handleCsv(event) {

    const file =
        event.target.files[0];


    const status =
        document.getElementById(
            "csvStatus"
        );


    if (!file) return;


    status.textContent =
        "Leyendo CSV...";


    status.className =
        "csv-status";


    try {

        const text =
            await file.text();


        const rows =
            parseCSV(text);


        if (!rows.length) {

            throw new Error(
                "El archivo está vacío."
            );

        }


        const data = {};


        rows.forEach(row => {

            const key =
                normalizeCsvHeader(
                    row[0]
                );


            const value =
                row
                    .slice(1)
                    .join(",")
                    .trim();


            if (key) {

                data[key] = value;

            }

        });


        const mapped = {

            name:
                data.nickname ||
                data.name ||
                "",

            handle:
                data.username ||
                data.handle ||
                "",

            country:
                data.country ||
                "",

            followers:
                data.followercount ||
                data.followers ||
                "",

            likes:
                data.heartcount ||
                data.likes ||
                "",

            views:
                data.averageviews ||
                data.views ||
                "",

            videos:
                data.videocount ||
                data.videos ||
                "",

            engagement:
                data.totalengagementrate ||
                data.engagement ||
                "",

            average_likes:
                data.averagelikes ||
                "",

            average_comments:
                data.averagecomments ||
                "",

            average_shares:
                data.averageshares ||
                ""

        };


        fillCreatorForm(mapped);


        const handle =
            document
                .getElementById("creatorForm")
                .elements
                .handle;


        if (
            handle.value &&
            !handle.value.startsWith("@")
        ) {

            handle.value =
                "@" + handle.value;

        }


        status.textContent =
            "✓ CSV importado correctamente.";

        status.className =
            "csv-status success";


    } catch (error) {

        status.textContent =
            "❌ Error: "
            + error.message;

        status.className =
            "csv-status error";

    }

}


function normalizeCsvHeader(header) {

    return String(header || "")
        .trim()
        .toLowerCase()
        .normalize("NFD")
        .replace(
            /[\u0300-\u036f]/g,
            ""
        )
        .replace(
            /[^a-z0-9]/g,
            ""
        );

}


function fillCreatorForm(data) {

    const form =
        document.getElementById(
            "creatorForm"
        );


    Object.entries(data)
        .forEach(
            ([field, value]) => {

                if (form.elements[field]) {

                    form.elements[field].value =
                        value || "";

                }

            }
        );

}


function parseCSV(text) {

    const rows = [];

    let row = [];

    let value = "";

    let insideQuotes = false;


    for (
        let i = 0;
        i < text.length;
        i++
    ) {

        const char = text[i];

        const next = text[i + 1];


        if (
            char === '"' &&
            insideQuotes &&
            next === '"'
        ) {

            value += '"';

            i++;

            continue;

        }


        if (char === '"') {

            insideQuotes =
                !insideQuotes;

            continue;

        }


        if (
            char === "," &&
            !insideQuotes
        ) {

            row.push(value);

            value = "";

            continue;

        }


        if (
            (
                char === "\n" ||
                char === "\r"
            )
            &&
            !insideQuotes
        ) {

            if (
                char === "\r" &&
                next === "\n"
            ) {

                i++;

            }


            row.push(value);

            value = "";


            if (
                row.some(
                    cell =>
                        cell.trim() !== ""
                )
            ) {

                rows.push(row);

            }


            row = [];

            continue;

        }


        value += char;

    }


    if (
        value ||
        row.length
    ) {

        row.push(value);

        rows.push(row);

    }


    return rows;

}


function downloadCsvExample() {

    const csv =
`Username,isitabibbetann
Nickname,Ejemplo Creator
Country,Honduras
Follower Count,20167
Heart Count,583073
Video Count,327
Total Engagement Rate,31.34%
Average Views,115031
Average Likes,33070
Average Comments,104
Average Shares,2881`;


    const blob =
        new Blob(
            [csv],
            {
                type:
                    "text/csv;charset=utf-8"
            }
        );


    const url =
        URL.createObjectURL(blob);


    const link =
        document.createElement("a");


    link.href = url;

    link.download =
        "vertex-month-ejemplo.csv";


    document.body.appendChild(link);

    link.click();

    link.remove();

    URL.revokeObjectURL(url);

}


/* =========================================
   EDITAR
========================================= */

function editCurrentCreator() {

    if (!currentCreator) return;

    closeProfile();

    openCreator(currentCreator);

}


/* =========================================
   ELIMINAR
========================================= */

async function deleteCurrentCreator() {

    if (!currentCreator) return;


    const confirmed =
        confirm(
            "¿Seguro que quieres eliminar este creador?"
        );


    if (!confirmed) return;


    const response =
        await fetch(
            `/api/creator/${currentCreator.id}`,
            {
                method: "DELETE"
            }
        );


    if (!response.ok) {

        alert(
            "No se pudo eliminar."
        );

        return;

    }


    creatorList =
        creatorList.filter(
            creator =>
                creator.id !== currentCreator.id
        );


    currentCreator = null;

    closeProfile();

    renderCreators();

}


/* =========================================
   SEGURIDAD HTML
========================================= */

function escapeHtml(value) {

    return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


/* =========================================
   INICIAR
========================================= */

applyTheme();

renderCreators();

// =========================================
// CAMBIAR CONTRASEÑA
// =========================================

function openChangePassword() {

    if (!IS_ADMIN) {
        openLogin();
        return;
    }

    const modal = document.getElementById(
        "changePasswordModal"
    );

    const form = document.getElementById(
        "changePasswordForm"
    );

    const status = document.getElementById(
        "changePasswordStatus"
    );

    if (!modal || !form || !status) {
        console.error(
            "No se encontraron los elementos del cambio de contraseña."
        );
        return;
    }

    form.reset();

    status.textContent = "";

    status.className = "csv-status";

    modal.classList.add("open");
}


// =========================================
// CERRAR MODAL
// =========================================

function closeChangePassword() {

    const modal = document.getElementById(
        "changePasswordModal"
    );

    if (modal) {
        modal.classList.remove("open");
    }
}


// =========================================
// GUARDAR NUEVA CONTRASEÑA
// =========================================

const changePasswordForm =
    document.getElementById(
        "changePasswordForm"
    );


if (changePasswordForm) {

    changePasswordForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();

            const form = document.getElementById(
                "changePasswordForm"
            );

            const status = document.getElementById(
                "changePasswordStatus"
            );

            const submitButton =
                form.querySelector(
                    'button[type="submit"]'
                );


            // =================================
            // DATOS
            // =================================

            const data = new FormData(form);


            // =================================
            // ESTADO
            // =================================

            status.textContent =
                "Guardando contraseña...";

            status.className =
                "csv-status";


            if (submitButton) {

                submitButton.disabled = true;

                submitButton.textContent =
                    "Guardando...";
            }


            try {

                // =============================
                // ENVIAR AL SERVIDOR
                // =============================

                const response = await fetch(
                    "/change-password",
                    {
                        method: "POST",
                        body: data
                    }
                );


                // =============================
                // LEER RESPUESTA
                // =============================

                let result;

                try {

                    result =
                        await response.json();

                } catch {

                    result = {
                        error:
                            "El servidor devolvió una respuesta inválida."
                    };

                }


                // =============================
                // ERROR
                // =============================

                if (!response.ok) {

                    status.textContent =
                        "❌ " +
                        (
                            result.error ||
                            "No se pudo cambiar la contraseña."
                        );

                    status.className =
                        "csv-status error";

                    return;
                }


                // =============================
                // ÉXITO
                // =============================

                status.textContent =
                    "✓ Contraseña guardada correctamente.";

                status.className =
                    "csv-status success";


                // Limpiar campos
                form.reset();


                // IMPORTANTE:
                // NO cerramos el modal.
                // El usuario podrá ver el mensaje.


            } catch (error) {

                console.error(
                    "Error cambiando contraseña:",
                    error
                );

                status.textContent =
                    "❌ No se pudo conectar con el servidor.";

                status.className =
                    "csv-status error";


            } finally {

                if (submitButton) {

                    submitButton.disabled = false;

                    submitButton.textContent =
                        "Cambiar contraseña";
                }

            }

        }
    );

}
// =========================================
// SOLICITAR CREADOR
// =========================================

function requestCreator() {

    if (!currentCreator) {
        return;
    }

    const creatorName =
        currentCreator.name || "Creador";

    const creatorHandle =
        currentCreator.handle || "";

    const creatorCountry =
        currentCreator.country || "";

    const creatorCategory =
        currentCreator.category || "";

    const subject =
        `Solicitud de creador — ${creatorName}`;

    const body =
`Hola,

Quiero solicitar al creador:

Nombre: ${creatorName}
Usuario: ${creatorHandle}
País: ${creatorCountry}
Categoría: ${creatorCategory}

Me gustaría solicitar este creador para publicitar mi marca.

Gracias.`;

    const mailto =
        "mailto:patrocinersmanagement@gmail.com" +
        "?subject=" +
        encodeURIComponent(subject) +
        "&body=" +
        encodeURIComponent(body);

    window.location.href = mailto;
}


// =========================================
// COMPARTIR PERFIL DEL CREADOR
// =========================================
async function shareCurrentCreator() {
    if (!currentCreator) {
        return;
    }

    const creatorUuid =
        currentCreator.creator_uuid;

    if (!creatorUuid) {
        alert(
            "Este creador no tiene un enlace público disponible."
        );
        return;
    }

    const shareUrl =
        `${window.location.origin}/creator/${creatorUuid}`;

    const shareData = {
        title:
            currentCreator.name ||
            "Creador de VERTEXMONT",

        text:
            `Conoce el perfil de ${
                currentCreator.name ||
                "este creador"
            } en VERTEXMONT.`,

        url: shareUrl
    };

    try {
        if (
            navigator.share &&
            window.isSecureContext
        ) {
            await navigator.share(shareData);
            return;
        }

        await navigator.clipboard.writeText(
            shareUrl
        );

        alert(
            "✓ Enlace copiado al portapapeles."
        );

    } catch (error) {
        if (
            error &&
            error.name === "AbortError"
        ) {
            return;
        }

        try {
            const textarea =
                document.createElement("textarea");

            textarea.value = shareUrl;

            textarea.style.position =
                "fixed";

            textarea.style.opacity = "0";

            document.body.appendChild(
                textarea
            );

            textarea.focus();
            textarea.select();

            document.execCommand(
                "copy"
            );

            textarea.remove();

            alert(
                "✓ Enlace copiado al portapapeles."
            );

        } catch (copyError) {
            console.error(
                "No se pudo copiar el enlace:",
                copyError
            );

            alert(
                `Comparte este enlace:\n\n${shareUrl}`
            );
        }
    }
}