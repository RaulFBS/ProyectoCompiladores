import mermaid from
    "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";


/* ==================================================
   1. DATOS RECIBIDOS DESDE FLASK
================================================== */

function readJSON(id, fallback) {
    const element = document.getElementById(id);

    if (!element) {
        return fallback;
    }

    try {
        return JSON.parse(element.textContent);
    } catch (error) {
        console.error(`No se pudo leer el elemento ${id}:`, error);
        return fallback;
    }
}

const models = readJSON("modelos-data", []);
const example = readJSON("ejemplo-data", "");

const selector = document.getElementById("tokenSelector");
const codeEditor = document.getElementById("codigo");
const lineNumbers = document.getElementById("lineNumbers");


/* ==================================================
   2. CONFIGURACIÓN DE MERMAID
================================================== */

mermaid.initialize({
    startOnLoad: false,
    theme: "base",
    securityLevel: "strict",

    flowchart: {
        curve: "linear",
        htmlLabels: false,
        nodeSpacing: 38,
        rankSpacing: 48
    },

    themeVariables: {
        background: "#ffffff",

        primaryColor: "#f8eded",
        primaryTextColor: "#202020",
        primaryBorderColor: "#a62632",

        lineColor: "#606060",

        secondaryColor: "#f4f4f4",
        tertiaryColor: "#ffffff",

        edgeLabelBackground: "#ffffff",

        fontFamily: "Segoe UI, Arial, sans-serif"
    }
});


/* ==================================================
   3. MENÚ LATERAL
================================================== */

const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebarToggle");
const sidebarOverlay = document.getElementById("sidebarOverlay");

function closeSidebar() {
    if (!sidebar || !sidebarToggle || !sidebarOverlay) {
        return;
    }

    sidebar.classList.remove("open");
    sidebarOverlay.classList.remove("visible");

    document.body.classList.remove("menu-open");

    sidebarToggle.setAttribute("aria-expanded", "false");
    sidebarToggle.setAttribute(
        "aria-label",
        "Abrir menú de navegación"
    );
}

function toggleSidebar() {
    if (!sidebar || !sidebarToggle || !sidebarOverlay) {
        return;
    }

    const isOpen = sidebar.classList.toggle("open");

    sidebarOverlay.classList.toggle("visible", isOpen);
    document.body.classList.toggle("menu-open", isOpen);

    sidebarToggle.setAttribute("aria-expanded", String(isOpen));

    sidebarToggle.setAttribute(
        "aria-label",
        isOpen
            ? "Cerrar menú de navegación"
            : "Abrir menú de navegación"
    );
}

if (sidebarToggle) {
    sidebarToggle.addEventListener("click", toggleSidebar);
}

if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", closeSidebar);
}

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeSidebar();
    }
});


/* ==================================================
   4. NAVEGACIÓN ENTRE SECCIONES
================================================== */

const sideLinks = document.querySelectorAll(".side-link");

function setActiveLink(sectionId) {
    sideLinks.forEach((link) => {
        const isActive =
            link.dataset.section === sectionId;

        link.classList.toggle("active", isActive);
    });
}

function activateTab(tabName) {
    const buttons = document.querySelectorAll(".tab-button");
    const panels = document.querySelectorAll(".automata-panel");

    buttons.forEach((button) => {
        const isActive = button.dataset.tab === tabName;

        button.classList.toggle("active", isActive);
        button.setAttribute(
            "aria-selected",
            String(isActive)
        );
    });

    panels.forEach((panel) => {
        const isActive = panel.id === `panel-${tabName}`;

        panel.classList.toggle("hidden", !isActive);
        panel.hidden = !isActive;
    });
}

sideLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
        const href = link.getAttribute("href");

        if (!href || !href.startsWith("#")) {
            closeSidebar();
            return;
        }

        const targetId = href.slice(1);

        /*
         * La tabla y la quíntupla están dentro de una
         * pestaña que inicialmente está oculta.
         * Primero se abre esa pestaña y luego se navega.
         */
        if (targetId === "tabla" || targetId === "quintupla") {
            event.preventDefault();

            activateTab("formal");

            const target = document.getElementById(targetId);

            closeSidebar();

            if (target) {
                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

                history.replaceState(null, "", `#${targetId}`);
            }

            setActiveLink("automatas");
            return;
        }

        closeSidebar();

        setActiveLink(targetId);
    });
});


/* ==================================================
   5. SELECCIÓN DE TOKEN
================================================== */

function getSelectedModel() {
    if (!Array.isArray(models) || models.length === 0) {
        return null;
    }

    if (!selector) {
        return models[0];
    }

    return (
        models.find(
            (model) => model.token === selector.value
        ) || models[0]
    );
}


/* ==================================================
   6. REPRESENTACIÓN DE AUTÓMATAS
================================================== */

async function setDiagram(element, source) {
    if (!element) {
        return;
    }

    element.removeAttribute("data-processed");
    element.replaceChildren();

    if (!source || !String(source).trim()) {
        element.textContent =
            "No hay un diagrama disponible para este modelo.";

        return;
    }

    element.classList.add("mermaid");
    element.textContent = String(source);

    try {
        await mermaid.run({
            nodes: [element]
        });
    } catch (error) {
        element.replaceChildren();

        const message = document.createElement("p");
        message.className = "diagram-error";
        message.textContent =
            "No se pudo representar el diagrama. " +
            "Revisa la fuente Mermaid del autómata.";

        element.appendChild(message);

        console.error(
            "Error renderizando el autómata:",
            error
        );
    }
}


/* ==================================================
   7. CREACIÓN SEGURA DE CELDAS
================================================== */

function appendCell(
    row,
    text,
    tag = "td",
    className = ""
) {
    const cell = document.createElement(tag);

    cell.textContent =
        text === null || text === undefined
            ? ""
            : String(text);

    if (className) {
        cell.className = className;
    }

    row.appendChild(cell);

    return cell;
}


/* ==================================================
   8. TABLA DE TRANSICIONES
================================================== */

function renderTransitionTable(tableData) {
    const container = document.getElementById("transitionTable");

    if (!container) {
        return;
    }

    container.replaceChildren();

    if (
        !tableData ||
        !Array.isArray(tableData.columnas) ||
        !Array.isArray(tableData.filas)
    ) {
        const message = document.createElement("p");
        message.className = "diagram-error";
        message.textContent =
            "No hay una tabla de transiciones disponible.";

        container.appendChild(message);
        return;
    }

    const table = document.createElement("table");
    table.className = "transitions-table";

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    appendCell(headerRow, "ESTADO", "th");

    tableData.columnas.forEach((column) => {
        appendCell(headerRow, column, "th");
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    tableData.filas.forEach((rowData) => {
        const row = document.createElement("tr");

        const stateLabel =
            `${rowData.estado}` +
            `${rowData.inicial ? " →" : ""}` +
            `${rowData.final ? " *" : ""}`;

        appendCell(
            row,
            stateLabel,
            "td",
            rowData.final ? "final-state" : ""
        );

        const transitions = Array.isArray(rowData.transiciones)
            ? rowData.transiciones
            : [];

        transitions.forEach((target) => {
            appendCell(
                row,
                target,
                "td",
                target === "—" ? "no-transition" : ""
            );
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}


/* ==================================================
   9. QUÍNTUPLA FORMAL
================================================== */

function formatFormalValue(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    if (typeof value === "string") {
        return value;
    }

    if (Array.isArray(value)) {
        return `{ ${value.join(", ")} }`;
    }

    if (typeof value === "object") {
        return JSON.stringify(value, null, 2);
    }

    return String(value);
}

function renderQuintuple(quintuple) {
    const container = document.getElementById("quintupleContent");

    if (!container) {
        return;
    }

    container.replaceChildren();

    if (!quintuple) {
        const message = document.createElement("p");
        message.textContent =
            "No hay una quíntupla disponible para este modelo.";

        container.appendChild(message);
        return;
    }

    const items = [
        [
            "Q",
            formatFormalValue(quintuple.Q)
        ],
        [
            "Σ",
            formatFormalValue(
                quintuple.Sigma ?? quintuple.sigma
            )
        ],
        [
            "δ",
            formatFormalValue(quintuple.delta)
        ],
        [
            "q₀",
            formatFormalValue(quintuple.q0)
        ],
        [
            "F",
            formatFormalValue(quintuple.F)
        ]
    ];

    items.forEach(([key, value]) => {
        const card = document.createElement("div");
        card.className = "quintuple-item";

        const symbol = document.createElement("span");
        symbol.className = "quintuple-symbol";
        symbol.textContent = key;

        const content = document.createElement("code");
        content.textContent = value;

        card.append(symbol, content);
        container.appendChild(card);
    });
}


/* ==================================================
   10. ACTUALIZACIÓN DEL TOKEN SELECCIONADO
================================================== */

async function renderSelectedModel() {
    const model = getSelectedModel();

    const regexValue = document.getElementById("regexValue");
    const afndCount = document.getElementById("afndCount");
    const afdCount = document.getElementById("afdCount");

    if (!model) {
        if (regexValue) {
            regexValue.textContent =
                "No hay modelos de tokens disponibles.";
        }

        if (afndCount) {
            afndCount.textContent = "—";
        }

        if (afdCount) {
            afdCount.textContent = "—";
        }

        renderTransitionTable(null);
        renderQuintuple(null);

        await setDiagram(
            document.getElementById("afndDiagram"),
            ""
        );

        await setDiagram(
            document.getElementById("afdDiagram"),
            ""
        );

        return;
    }

    if (regexValue) {
        regexValue.textContent = model.regex ?? "—";
    }

    if (afndCount) {
        afndCount.textContent =
            `${model.cantidad_estados_afnd ?? "—"} estados · ` +
            `inicial ${model.afnd_inicial ?? "—"} · ` +
            `final ${model.afnd_final ?? "—"}`;
    }

    if (afdCount) {
        const finales = Array.isArray(model.afd_finales)
            ? model.afd_finales
            : [];

        afdCount.textContent =
            `${model.cantidad_estados_afd ?? "—"} estados · ` +
            `inicial ${model.afd_inicial ?? "—"} · ` +
            `finales ${finales.join(", ") || "ninguno"}`;
    }

    await setDiagram(
        document.getElementById("afndDiagram"),
        model.afnd_diagrama
    );

    await setDiagram(
        document.getElementById("afdDiagram"),
        model.afd_diagrama
    );

    renderTransitionTable(model.tabla);
    renderQuintuple(model.quintupla);
}

if (selector) {
    selector.addEventListener("change", renderSelectedModel);
}


/* ==================================================
   11. PESTAÑAS AFND, AFD Y TABLA
================================================== */

document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => {
        activateTab(button.dataset.tab);
    });
});


/* ==================================================
   12. NÚMEROS DE LÍNEA
================================================== */

function updateLineNumbers() {
    if (!codeEditor || !lineNumbers) {
        return;
    }

    const lines = Math.max(
        1,
        codeEditor.value.split("\n").length
    );

    lineNumbers.replaceChildren();

    for (let index = 1; index <= lines; index++) {
        if (index > 1) {
            lineNumbers.appendChild(
                document.createElement("br")
            );
        }

        lineNumbers.appendChild(
            document.createTextNode(String(index))
        );
    }

    const lineCount = document.getElementById("lineCount");

    if (lineCount) {
        lineCount.textContent =
            lines === 1 ? "1 línea" : `${lines} líneas`;
    }
}

if (codeEditor) {
    codeEditor.addEventListener("input", updateLineNumbers);

    codeEditor.addEventListener("scroll", () => {
        if (lineNumbers) {
            lineNumbers.scrollTop = codeEditor.scrollTop;
        }
    });
}


/* ==================================================
   13. CARGAR EJEMPLO
================================================== */

const loadExampleButton = document.getElementById("cargarEjemplo");
const fileInput = document.getElementById("archivo");
const fileLabel = document.getElementById("fileLabel");

if (loadExampleButton && codeEditor) {
    loadExampleButton.addEventListener("click", () => {
        codeEditor.value =
            typeof example === "string" ? example : "";

        if (fileInput) {
            fileInput.value = "";
        }

        if (fileLabel) {
            fileLabel.textContent =
                "Ejemplo de trama cargado";
        }

        updateLineNumbers();
        codeEditor.focus();
    });
}


/* ==================================================
   14. LIMPIAR EL EDITOR
================================================== */

const clearCodeButton = document.getElementById("limpiarCodigo");

if (clearCodeButton && codeEditor) {
    clearCodeButton.addEventListener("click", () => {
        codeEditor.value = "";

        if (fileInput) {
            fileInput.value = "";
        }

        if (fileLabel) {
            fileLabel.textContent =
                "Ningún archivo seleccionado";
        }

        updateLineNumbers();
        codeEditor.focus();
    });
}


/* ==================================================
   15. CARGAR ARCHIVO EN EL EDITOR
================================================== */

if (fileInput && codeEditor) {
    fileInput.addEventListener("change", async (event) => {
        const file = event.target.files?.[0];

        if (!file) {
            if (fileLabel) {
                fileLabel.textContent =
                    "Ningún archivo seleccionado";
            }

            return;
        }

        const allowedExtensions = ["txt", "log", "dsl"];
        const extension = file.name
            .split(".")
            .pop()
            .toLowerCase();

        if (!allowedExtensions.includes(extension)) {
            alert(
                "Selecciona un archivo TXT, LOG o DSL."
            );

            fileInput.value = "";
            return;
        }

        const maxSize = 1024 * 1024;

        if (file.size > maxSize) {
            alert("El archivo no puede superar 1 MB.");

            fileInput.value = "";
            return;
        }

        try {
            const content = await file.text();

            codeEditor.value = content;

            if (fileLabel) {
                fileLabel.textContent = file.name;
            }

            updateLineNumbers();
            codeEditor.focus();

        } catch (error) {
            console.error("Error leyendo el archivo:", error);

            alert("No se pudo leer el archivo seleccionado.");

            fileInput.value = "";
        }
    });
}


/* ==================================================
   16. ESTADO DEL BOTÓN DE ANÁLISIS
================================================== */

const compilerForm = document.getElementById("compilerForm");
const analyzeButton = document.getElementById("analizarButton");

if (compilerForm && analyzeButton) {
    compilerForm.addEventListener("submit", () => {
        analyzeButton.disabled = true;
        analyzeButton.setAttribute("aria-busy", "true");

        analyzeButton.textContent = "Procesando...";
    });
}


/* ==================================================
   17. NAVEGACIÓN ACTIVA AL DESPLAZARSE
================================================== */

const observedSections = [
    "inicio",
    "editor",
    "analisis",
    "automatas"
]
    .map((id) => document.getElementById(id))
    .filter(Boolean);

if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
        (entries) => {
            const visibleEntries = entries
                .filter((entry) => entry.isIntersecting)
                .sort(
                    (a, b) =>
                        b.intersectionRatio - a.intersectionRatio
                );

            if (visibleEntries.length > 0) {
                setActiveLink(visibleEntries[0].target.id);
            }
        },
        {
            rootMargin: "-20% 0px -65% 0px",
            threshold: [0, 0.1, 0.3, 0.6]
        }
    );

    observedSections.forEach((section) => {
        observer.observe(section);
    });
}


/* ==================================================
   18. INICIALIZACIÓN
================================================== */

updateLineNumbers();

activateTab("afnd");

renderSelectedModel().catch((error) => {
    console.error(
        "No se pudo inicializar la visualización:",
        error
    );
});