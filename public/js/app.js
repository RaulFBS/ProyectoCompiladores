import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";

const readJSON = (id, fallback) => {
  const element = document.getElementById(id);
  if (!element) return fallback;

  try {
    return JSON.parse(element.textContent);
  } catch (error) {
    console.error(`No se pudo leer ${id}`, error);
    return fallback;
  }
};

const models = readJSON("modelos-data", []);
const example = readJSON("ejemplo-data", "");
const selector = document.getElementById("tokenSelector");
const editor = document.getElementById("codigo");
const lineNumbers = document.getElementById("lineNumbers");
const fileInput = document.getElementById("archivo");
const fileLabel = document.getElementById("fileLabel");

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
    primaryColor: "#f8edef",
    primaryTextColor: "#242424",
    primaryBorderColor: "#a52a35",
    lineColor: "#606060",
    secondaryColor: "#f2f2f2",
    tertiaryColor: "#ffffff",
    edgeLabelBackground: "#ffffff",
    fontFamily: "Segoe UI, Arial, sans-serif"
  }
});

/* Menú lateral. En escritorio ocupa una columna independiente. */
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebarToggle");
const sidebarOverlay = document.getElementById("sidebarOverlay");

function closeSidebar() {
  sidebar?.classList.remove("open");
  sidebarOverlay?.classList.remove("visible");
  document.body.classList.remove("menu-open");
  sidebarToggle?.setAttribute("aria-expanded", "false");
  sidebarToggle?.setAttribute("aria-label", "Abrir menú");
}

function toggleSidebar() {
  if (!sidebar || !sidebarOverlay) return;

  const open = !sidebar.classList.contains("open");

  sidebar.classList.toggle("open", open);
  sidebarOverlay.classList.toggle("visible", open);
  document.body.classList.toggle("menu-open", open);

  sidebarToggle?.setAttribute("aria-expanded", String(open));
  sidebarToggle?.setAttribute(
    "aria-label",
    open ? "Cerrar menú" : "Abrir menú"
  );
}

sidebarToggle?.addEventListener("click", toggleSidebar);
sidebarOverlay?.addEventListener("click", closeSidebar);

document.addEventListener("keydown", event => {
  if (event.key === "Escape") closeSidebar();
});

window.addEventListener("resize", () => {
  if (window.innerWidth > 760) closeSidebar();
});

/* Navegación y sección activa. */
const navItems = [...document.querySelectorAll(".nav-item")];

function setActiveNav(id) {
  navItems.forEach(item => {
    item.classList.toggle("active", item.dataset.section === id);
  });
}

navItems.forEach(item => {
  item.addEventListener("click", () => {
    const target = item.getAttribute("href")?.slice(1);
    if (target) setActiveNav(target);
    closeSidebar();
  });
});

if ("IntersectionObserver" in window) {
  const sections = [
    "inicio",
    "entrada",
    "resultado",
    "automatas",
    "gramatica"
  ]
    .map(id => document.getElementById(id))
    .filter(Boolean);

  const observer = new IntersectionObserver(entries => {
    const visible = entries
      .filter(entry => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

    if (visible) setActiveNav(visible.target.id);
  }, {
    rootMargin: "-18% 0px -67% 0px",
    threshold: [0, 0.1, 0.3, 0.6]
  });

  sections.forEach(section => observer.observe(section));
}

/* Obtener el modelo seleccionado. */
function selectedModel() {
  if (!models.length) return null;

  return models.find(
    model => model.token === selector?.value
  ) || models[0];
}

/* Renderizar diagramas Mermaid. */
async function drawDiagram(element, source) {
  if (!element) return;

  element.removeAttribute("data-processed");
  element.replaceChildren();

  if (!source || !String(source).trim()) {
    element.textContent =
      "No hay un diagrama disponible para este token.";
    return;
  }

  element.textContent = String(source);

  try {
    await mermaid.run({ nodes: [element] });
  } catch (error) {
    element.replaceChildren();

    const message = document.createElement("p");
    message.className = "diagram-error";
    message.textContent =
      "No se pudo representar el diagrama. Revisa la fuente Mermaid.";

    element.appendChild(message);
    console.error("Error al renderizar el autómata:", error);
  }
}

/* Crear celdas de forma segura. */
function appendCell(row, text, tag = "td", className = "") {
  const cell = document.createElement(tag);
  cell.textContent = text == null ? "" : String(text);

  if (className) cell.className = className;

  row.appendChild(cell);
  return cell;
}

/* Tabla de transiciones. */
function renderTransitionTable(tableData) {
  const container = document.getElementById("transitionTable");
  if (!container) return;

  container.replaceChildren();

  if (
    !tableData ||
    !Array.isArray(tableData.columnas) ||
    !Array.isArray(tableData.filas)
  ) {
    container.textContent =
      "No hay una tabla de transiciones disponible.";
    return;
  }

  const table = document.createElement("table");
  table.className = "transitions-table";

  const thead = document.createElement("thead");
  const header = document.createElement("tr");

  appendCell(header, "ESTADO", "th");

  tableData.columnas.forEach(column => {
    appendCell(header, column, "th");
  });

  thead.appendChild(header);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");

  tableData.filas.forEach(item => {
    const row = document.createElement("tr");

    const state =
      `${item.estado}` +
      `${item.inicial ? " →" : ""}` +
      `${item.final ? " *" : ""}`;

    appendCell(
      row,
      state,
      "td",
      item.final ? "final-state" : ""
    );

    (item.transiciones || []).forEach(target => {
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

/* Formatear los valores de la quíntupla. */
function formatFormalValue(value) {
  if (value == null) return "—";
  if (Array.isArray(value)) return `{ ${value.join(", ")} }`;

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

/* Mostrar la quíntupla. */
function renderQuintuple(quintuple) {
  const container = document.getElementById("quintupleContent");
  if (!container) return;

  container.replaceChildren();

  if (!quintuple) {
    container.textContent = "No hay una quíntupla disponible.";
    return;
  }

  const items = [
    ["Q", quintuple.Q],
    ["Σ", quintuple.Sigma ?? quintuple.sigma],
    ["δ", quintuple.delta],
    ["q₀", quintuple.q0],
    ["F", quintuple.F]
  ];

  items.forEach(([key, value]) => {
    const card = document.createElement("div");
    card.className = "quintuple-item";

    const symbol = document.createElement("span");
    symbol.className = "quintuple-symbol";
    symbol.textContent = key;

    const code = document.createElement("code");
    code.textContent = formatFormalValue(value);

    card.append(symbol, code);
    container.appendChild(card);
  });
}

/* Actualizar todos los datos del token seleccionado. */
async function renderSelectedModel() {
  const model = selectedModel();

  const regex = document.getElementById("regexValue");
  const afndCount = document.getElementById("afndCount");
  const afdCount = document.getElementById("afdCount");

  if (!model) {
    if (regex) regex.textContent = "No hay modelos de tokens.";
    if (afndCount) afndCount.textContent = "—";
    if (afdCount) afdCount.textContent = "—";

    renderTransitionTable(null);
    renderQuintuple(null);

    await drawDiagram(
      document.getElementById("afndDiagram"),
      ""
    );

    await drawDiagram(
      document.getElementById("afdDiagram"),
      ""
    );

    return;
  }

  if (regex) regex.textContent = model.regex ?? "—";

  if (afndCount) {
    afndCount.textContent =
      `${model.cantidad_estados_afnd ?? "—"} estados · ` +
      `inicial ${model.afnd_inicial ?? "—"} · ` +
      `final ${model.afnd_final ?? "—"}`;
  }

  const finals = Array.isArray(model.afd_finales)
    ? model.afd_finales
    : [];

  if (afdCount) {
    afdCount.textContent =
      `${model.cantidad_estados_afd ?? "—"} estados · ` +
      `inicial ${model.afd_inicial ?? "—"} · ` +
      `finales ${finals.join(", ") || "ninguno"}`;
  }

  await drawDiagram(
    document.getElementById("afndDiagram"),
    model.afnd_diagrama
  );

  await drawDiagram(
    document.getElementById("afdDiagram"),
    model.afd_diagrama
  );

  renderTransitionTable(model.tabla);
  renderQuintuple(model.quintupla);
}

selector?.addEventListener("change", renderSelectedModel);

/* Pestañas de AFND, AFD, transiciones y quíntupla. */
function activateTab(name) {
  document.querySelectorAll(".tab-button").forEach(button => {
    const active = button.dataset.tab === name;

    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });

  document.querySelectorAll(".automata-panel").forEach(panel => {
    const active = panel.id === `panel-${name}`;

    panel.classList.toggle("hidden", !active);
    panel.hidden = !active;
  });
}

document.querySelectorAll(".tab-button").forEach(button => {
  button.addEventListener("click", () => {
    activateTab(button.dataset.tab);
  });
});

/* Números de línea. */
function updateLineNumbers() {
  if (!editor || !lineNumbers) return;

  const count = Math.max(
    1,
    editor.value.split("\n").length
  );

  lineNumbers.replaceChildren();

  for (let i = 1; i <= count; i++) {
    if (i > 1) {
      lineNumbers.appendChild(document.createElement("br"));
    }

    lineNumbers.appendChild(
      document.createTextNode(String(i))
    );
  }

  const label = document.getElementById("lineCount");

  if (label) {
    label.textContent =
      count === 1 ? "1 línea" : `${count} líneas`;
  }
}

editor?.addEventListener("input", updateLineNumbers);

editor?.addEventListener("scroll", () => {
  if (lineNumbers) {
    lineNumbers.scrollTop = editor.scrollTop;
  }
});

/* Restaurar el ejemplo. */
document.getElementById("cargarEjemplo")?.addEventListener("click", () => {
  if (!editor) return;

  editor.value = typeof example === "string" ? example : "";

  if (fileInput) fileInput.value = "";
  if (fileLabel) fileLabel.textContent = "Ejemplo restaurado";

  updateLineNumbers();
  editor.focus();
});

/* Limpiar el editor. */
document.getElementById("limpiarCodigo")?.addEventListener("click", () => {
  if (!editor) return;

  editor.value = "";

  if (fileInput) fileInput.value = "";
  if (fileLabel) fileLabel.textContent = "TXT, LOG o DSL";

  updateLineNumbers();
  editor.focus();
});

/* Cargar archivo en el editor. */
fileInput?.addEventListener("change", async event => {
  const file = event.target.files?.[0];

  if (!file) {
    if (fileLabel) fileLabel.textContent = "TXT, LOG o DSL";
    return;
  }

  const extension = file.name.split(".").pop().toLowerCase();

  if (!["txt", "log", "dsl"].includes(extension)) {
    alert("Selecciona un archivo TXT, LOG o DSL.");
    fileInput.value = "";
    return;
  }

  if (file.size > 1024 * 1024) {
    alert("El archivo no puede superar 1 MB.");
    fileInput.value = "";
    return;
  }

  try {
    const content = await file.text();

    if (editor) editor.value = content;
    if (fileLabel) fileLabel.textContent = file.name;

    updateLineNumbers();
  } catch (error) {
    console.error("No se pudo leer el archivo:", error);
    alert("No se pudo leer el archivo seleccionado.");
    fileInput.value = "";
  }
});

/* Evitar doble envío del formulario. */
document.getElementById("compilerForm")?.addEventListener("submit", () => {
  const button = document.getElementById("analizarButton");

  if (button) {
    button.disabled = true;
    button.textContent = "Procesando...";
  }
});

/* Inicialización. */
updateLineNumbers();
activateTab("afnd");

renderSelectedModel().catch(error => {
  console.error("Error al inicializar TramaLab:", error);
});