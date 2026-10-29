import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';

const models = JSON.parse(document.getElementById('modelos-data').textContent);
const example = JSON.parse(document.getElementById('ejemplo-data').textContent);
const selector = document.getElementById('tokenSelector');
const codeEditor = document.getElementById('codigo');
const lineNumbers = document.getElementById('lineNumbers');

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'strict',
  flowchart: { curve: 'basis', htmlLabels: true, nodeSpacing: 34, rankSpacing: 46 },
  themeVariables: {
    background: '#101c2a',
    primaryColor: '#17374a',
    primaryTextColor: '#e7f4fa',
    primaryBorderColor: '#43c9bd',
    lineColor: '#51bdb4',
    secondaryColor: '#182b3c',
    tertiaryColor: '#10212f',
    edgeLabelBackground: '#172535'
  }
});

function getSelectedModel() {
  return models.find((model) => model.token === selector.value) || models[0];
}

async function setDiagram(element, source) {
  element.removeAttribute('data-processed');
  element.innerHTML = '';
  element.textContent = source;
  try {
    await mermaid.run({ nodes: [element] });
  } catch (error) {
    element.textContent = 'No se pudo renderizar el diagrama. Fuente Mermaid:\n' + source;
    console.error('Error renderizando el autómata:', error);
  }
}

function appendCell(row, text, tag = 'td', className = '') {
  const cell = document.createElement(tag);
  cell.textContent = text ?? '';
  if (className) cell.className = className;
  row.appendChild(cell);
  return cell;
}

function renderTransitionTable(tableData) {
  const container = document.getElementById('transitionTable');
  container.replaceChildren();
  const table = document.createElement('table');
  table.className = 'transitions-table';
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  appendCell(headerRow, 'ESTADO', 'th');
  tableData.columnas.forEach((column) => appendCell(headerRow, column, 'th'));
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement('tbody');
  tableData.filas.forEach((rowData) => {
    const row = document.createElement('tr');
    appendCell(row, `${rowData.estado}${rowData.inicial ? ' →' : ''}${rowData.final ? ' *' : ''}`, 'td', rowData.final ? 'final-state' : '');
    rowData.transiciones.forEach((target) => appendCell(row, target, 'td', target === '—' ? 'no-transition' : ''));
    tbody.appendChild(row);
  });
  table.appendChild(tbody);
  container.appendChild(table);
}

function renderQuintuple(quintuple) {
  const container = document.getElementById('quintupleContent');
  container.replaceChildren();
  const items = [
    ['Q', `{ ${quintuple.Q.join(', ')} }`],
    ['Σ', `{ ${quintuple.Sigma.join(', ')} }`],
    ['δ', quintuple.delta],
    ['q₀', quintuple.q0],
    ['F', `{ ${quintuple.F.join(', ')} }`]
  ];
  items.forEach(([key, value]) => {
    const card = document.createElement('div');
    card.className = 'quintuple-item';
    const symbol = document.createElement('span');
    symbol.className = 'quintuple-symbol';
    symbol.textContent = key;
    const content = document.createElement('code');
    content.textContent = value;
    card.append(symbol, content);
    container.appendChild(card);
  });
}

async function renderSelectedModel() {
  const model = getSelectedModel();
  document.getElementById('regexValue').textContent = model.regex;
  document.getElementById('afndCount').textContent = `${model.cantidad_estados_afnd} estados · inicial ${model.afnd_inicial} · final ${model.afnd_final}`;
  document.getElementById('afdCount').textContent = `${model.cantidad_estados_afd} estados · inicial ${model.afd_inicial} · finales ${model.afd_finales.join(', ') || 'ninguno'}`;
  await setDiagram(document.getElementById('afndDiagram'), model.afnd_diagrama);
  await setDiagram(document.getElementById('afdDiagram'), model.afd_diagrama);
  renderTransitionTable(model.tabla);
  renderQuintuple(model.quintupla);
}

selector.addEventListener('change', () => { renderSelectedModel(); });

document.querySelectorAll('.tab-button').forEach((button) => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.tab-button').forEach((item) => item.classList.toggle('active', item === button));
    document.querySelectorAll('.automata-panel').forEach((panel) => panel.classList.add('hidden'));
    document.getElementById(`panel-${button.dataset.tab}`).classList.remove('hidden');
  });
});

function updateLineNumbers() {
  const lines = Math.max(1, codeEditor.value.split('\n').length);
  lineNumbers.innerHTML = Array.from({ length: lines }, (_, index) => index + 1).join('<br>');
}

codeEditor.addEventListener('input', updateLineNumbers);
codeEditor.addEventListener('scroll', () => { lineNumbers.scrollTop = codeEditor.scrollTop; });
document.getElementById('cargarEjemplo').addEventListener('click', () => {
  codeEditor.value = example;
  updateLineNumbers();
  codeEditor.focus();
});

document.getElementById('archivo').addEventListener('change', (event) => {
  const file = event.target.files?.[0];
  document.getElementById('fileLabel').textContent = file ? file.name : 'Cargar archivo .txt / .dsl';
});

updateLineNumbers();
renderSelectedModel();
