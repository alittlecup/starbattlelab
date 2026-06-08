/* Star Battle 谜题预览 / 难度标注 —— 前端逻辑。
 *
 * 谜题区域用 SBN 编码（文件名即 SBN），由本地服务用权威 Python codec 解码后返回网格。
 * 难度分由本地服务运行时调用现有 Python 引擎计算。
 * 标注数据（预期分 + 收藏/特殊/丢弃）存 localStorage，可导出 JSON/CSV。
 */

const LS_KEY = 'sb_labels_v1';
const REGION_COLORS = [
  '#fca5a5', '#fdba74', '#fde047', '#bef264', '#86efac', '#5eead4',
  '#7dd3fc', '#a5b4fc', '#d8b4fe', '#f0abfc', '#fda4af', '#e5e7eb',
];

const state = {
  size: null,
  sbn: null,
  dim: 0,
  stars: 1,
  regionGrid: null,        // [r][c] -> region id
  cells: null,             // [r][c] -> 0 空 / 1 ✕ / 2 ★
  seen: [],                // 本会话看过的 sbn（用于 random 排除）
  solved: false,
};

// ---------------- localStorage ----------------
function loadLabels() {
  try { return JSON.parse(localStorage.getItem(LS_KEY)) || {}; }
  catch { return {}; }
}
function saveLabels(labels) {
  localStorage.setItem(LS_KEY, JSON.stringify(labels));
}
let labels = loadLabels();

function currentLabel() {
  return labels[state.sbn] || {};
}

// ---------------- 尺寸选择 ----------------
async function initSizes() {
  const wrap = document.getElementById('sizes');
  let available = {};
  try {
    const res = await fetch('/api/sizes');
    available = (await res.json()).sizes || {};
  } catch (e) {
    document.getElementById('status').textContent = '⚠ 无法连接本地服务，请先运行 server.py';
  }
  wrap.innerHTML = '';
  for (let s = 4; s <= 12; s++) {
    const btn = document.createElement('button');
    btn.className = 'size-btn';
    const cnt = available[s] || 0;
    btn.innerHTML = `${s}×${s}<span class="cnt">${cnt ? cnt + ' 题' : '无'}</span>`;
    btn.disabled = !cnt;
    btn.onclick = () => selectSize(s, btn);
    wrap.appendChild(btn);
    btn.dataset.size = s;
  }
  // 默认选第一个可用尺寸
  const first = Object.keys(available).map(Number).sort((a, b) => a - b)[0];
  if (first) {
    const btn = wrap.querySelector(`[data-size="${first}"]`);
    selectSize(first, btn);
  }
}

function selectSize(s, btn) {
  state.size = s;
  document.querySelectorAll('.size-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  state.seen = [];
  loadRandom();
}

// ---------------- 出题 ----------------
async function loadRandom() {
  const status = document.getElementById('status');
  status.className = 'status';
  status.textContent = '加载中…';
  const exclude = state.seen.slice(-150).join(',');
  try {
    const res = await fetch(`/api/random?size=${state.size}&exclude=${encodeURIComponent(exclude)}`);
    const data = await res.json();
    if (data.error) { status.textContent = '⚠ ' + data.error; return; }
    loadPuzzle(data);
  } catch (e) {
    status.textContent = '⚠ 出题失败：' + e.message;
  }
}

// data: { sbn, dim, stars, regionGrid } —— 服务端用权威 Python codec 解码
function loadPuzzle(data) {
  const sbn = data.sbn;
  state.sbn = sbn;
  state.dim = data.dim;
  state.stars = data.stars;
  state.regionGrid = data.regionGrid;
  state.cells = Array.from({ length: state.dim }, () => new Array(state.dim).fill(0));
  state.solved = false;
  if (!state.seen.includes(sbn)) state.seen.push(sbn);

  document.getElementById('sbnLine').textContent = `SBN: ${sbn}  ·  ${state.stars} 星/区`;
  renderGrid();
  validate();
  syncMarksUI();
  fetchDifficulty(sbn);
}

// ---------------- 渲染 ----------------
function renderGrid() {
  const grid = document.getElementById('grid');
  const dim = state.dim;
  // 网格随尺寸自适应，整体宽度约 540px
  const px = Math.floor(Math.min(540, 60 * dim) / dim);
  grid.style.gridTemplateColumns = `repeat(${dim}, ${px}px)`;
  grid.style.gridTemplateRows = `repeat(${dim}, ${px}px)`;
  grid.innerHTML = '';
  const rg = state.regionGrid;
  for (let r = 0; r < dim; r++) {
    for (let c = 0; c < dim; c++) {
      const cell = document.createElement('div');
      cell.className = 'cell';
      cell.style.background = REGION_COLORS[rg[r][c] % REGION_COLORS.length];
      cell.style.fontSize = px + 'px';
      // 区域边界加粗
      if (r === 0 || rg[r - 1][c] !== rg[r][c]) cell.classList.add('bt');
      if (r === dim - 1 || rg[r + 1][c] !== rg[r][c]) cell.classList.add('bb');
      if (c === 0 || rg[r][c - 1] !== rg[r][c]) cell.classList.add('bl');
      if (c === dim - 1 || rg[r][c + 1] !== rg[r][c]) cell.classList.add('br');
      cell.dataset.r = r; cell.dataset.c = c;
      // 单击 = ✕排除，双击 = ★星（用延时区分，避免双击触发单击逻辑）
      cell.onclick = () => onCellClick(r, c);
      cell.ondblclick = () => onCellDblClick(r, c);
      // 右键直接放/取星，无延时，便于快速摆星
      cell.oncontextmenu = (e) => { e.preventDefault(); toggleStar(r, c); };
      grid.appendChild(cell);
    }
  }
  paintCells();
}

function paintCells() {
  const grid = document.getElementById('grid');
  const dim = state.dim;
  [...grid.children].forEach(cell => {
    const r = +cell.dataset.r, c = +cell.dataset.c;
    const v = state.cells[r][c];
    cell.classList.toggle('star', v === 2);
    let inner = cell.querySelector('.mark');
    if (!inner) { inner = document.createElement('span'); inner.className = 'mark'; cell.appendChild(inner); }
    inner.textContent = v === 2 ? '★' : v === 1 ? '✕' : '';
  });
}

// 单击 = 切换 ✕排除（延时执行，若紧接着双击则取消）
let clickTimer = null;
function onCellClick(r, c) {
  if (clickTimer) clearTimeout(clickTimer);
  clickTimer = setTimeout(() => {
    clickTimer = null;
    setCell(r, c, state.cells[r][c] === 1 ? 0 : 1);
  }, 220);
}
// 双击 = 切换 ★星
function onCellDblClick(r, c) {
  if (clickTimer) { clearTimeout(clickTimer); clickTimer = null; }
  toggleStar(r, c);
}
function toggleStar(r, c) {
  setCell(r, c, state.cells[r][c] === 2 ? 0 : 2);
}
function setCell(r, c, v) {
  state.cells[r][c] = v;
  paintCells();
  validate();
}

// ---------------- 校验 ----------------
function validate() {
  const dim = state.dim, k = state.stars, cells = state.cells;
  const status = document.getElementById('status');
  document.querySelectorAll('.cell.bad').forEach(e => e.classList.remove('bad'));

  const stars = [];
  for (let r = 0; r < dim; r++)
    for (let c = 0; c < dim; c++)
      if (cells[r][c] === 2) stars.push([r, c]);

  // 相邻冲突（含对角）
  let conflict = false;
  for (let i = 0; i < stars.length; i++) {
    for (let j = i + 1; j < stars.length; j++) {
      if (Math.abs(stars[i][0] - stars[j][0]) <= 1 && Math.abs(stars[i][1] - stars[j][1]) <= 1) {
        markBad(stars[i]); markBad(stars[j]); conflict = true;
      }
    }
  }

  // 行/列/区 计数
  const rowCnt = new Array(dim).fill(0), colCnt = new Array(dim).fill(0);
  const regCnt = {};
  for (const [r, c] of stars) {
    rowCnt[r]++; colCnt[c]++;
    const rid = state.regionGrid[r][c];
    regCnt[rid] = (regCnt[rid] || 0) + 1;
  }
  let over = false;
  for (let i = 0; i < dim; i++) if (rowCnt[i] > k || colCnt[i] > k) over = true;
  for (const rid in regCnt) if (regCnt[rid] > k) over = true;

  const totalNeeded = dim * k;
  const placed = stars.length;

  if (conflict) {
    status.className = 'status warn';
    status.textContent = `✕ 有相邻的星（${placed}/${totalNeeded}）`;
  } else if (over) {
    status.className = 'status warn';
    status.textContent = `✕ 某行/列/区星数超出 ${k}（${placed}/${totalNeeded}）`;
  } else if (placed === totalNeeded && allExact(rowCnt, colCnt, regCnt, dim, k)) {
    status.className = 'status ok';
    status.textContent = `✓ 解开了！自动进入下一题…`;
    onSolved();
  } else {
    status.className = 'status';
    status.textContent = `进行中：${placed}/${totalNeeded} 星`;
  }
}

function allExact(rowCnt, colCnt, regCnt, dim, k) {
  for (let i = 0; i < dim; i++) if (rowCnt[i] !== k || colCnt[i] !== k) return false;
  // 区域数应为 dim 个，每个 k 星
  const regs = new Set();
  for (let r = 0; r < dim; r++) for (let c = 0; c < dim; c++) regs.add(state.regionGrid[r][c]);
  for (const rid of regs) if ((regCnt[rid] || 0) !== k) return false;
  return true;
}

function markBad([r, c]) {
  const grid = document.getElementById('grid');
  const idx = r * state.dim + c;
  if (grid.children[idx]) grid.children[idx].classList.add('bad');
}

let solveTimer = null;
function onSolved() {
  if (state.solved) return;
  state.solved = true;
  saveCurrentLabel(true);
  clearTimeout(solveTimer);
  solveTimer = setTimeout(() => loadRandom(), 1200);
}

// ---------------- 难度 ----------------
async function fetchDifficulty(sbn) {
  setDiff({ score: '…', band: '…', hardest_rule: '…', solved_via: '…', steps: '', n_solutions: '' });
  try {
    const res = await fetch(`/api/difficulty?sbn=${encodeURIComponent(sbn)}`);
    const d = await res.json();
    if (sbn !== state.sbn) return;  // 已切题
    if (d.error) { setDiff({ score: 'ERR', band: d.error }); return; }
    setDiff(d);
  } catch (e) {
    setDiff({ score: 'ERR', band: e.message });
  }
}
function setDiff(d) {
  document.getElementById('diffScore').textContent =
    typeof d.score === 'number' ? d.score.toFixed(1) : d.score;
  const bandEl = document.getElementById('diffBand');
  bandEl.innerHTML = d.band ? `<span class="band ${d.band}">${d.band}</span>` : '—';
  document.getElementById('diffRule').textContent = d.hardest_rule || '—';
  document.getElementById('diffVia').textContent = d.solved_via || '—';
  document.getElementById('diffSteps').textContent =
    (d.steps !== undefined && d.steps !== '') ? `${d.steps} / ${d.n_solutions}` : '—';
}

// ---------------- 标记 / 预期分 ----------------
function syncMarksUI() {
  const l = currentLabel();
  document.getElementById('mkFav').classList.toggle('on', !!l.favorite);
  document.getElementById('mkSpecial').classList.toggle('on', !!l.special);
  document.getElementById('mkDiscard').classList.toggle('on', !!l.discard);
  document.getElementById('expScore').value = (l.expectedScore ?? '');
}

function ensureLabel() {
  if (!labels[state.sbn]) {
    labels[state.sbn] = { sbn: state.sbn, size: state.size, stars: state.stars };
  }
  return labels[state.sbn];
}

function toggleMark(field, btnId) {
  const l = ensureLabel();
  l[field] = !l[field];
  document.getElementById(btnId).classList.toggle('on', !!l[field]);
  l.ts = Date.now();
  saveLabels(labels);
  flashSaved();
  updateStats();
  // 丢弃后可立即下一题
  if (field === 'discard' && l.discard) {
    clearTimeout(solveTimer);
    solveTimer = setTimeout(() => loadRandom(), 400);
  }
}

function saveCurrentLabel(silent) {
  const l = ensureLabel();
  const v = document.getElementById('expScore').value;
  if (v !== '') l.expectedScore = Number(v);
  // 记录当时算法分，便于离线对比
  const ds = document.getElementById('diffScore').textContent;
  if (ds && !isNaN(parseFloat(ds))) l.algoScore = parseFloat(ds);
  const band = document.querySelector('#diffBand .band');
  if (band) l.algoBand = band.textContent;
  l.ts = Date.now();
  saveLabels(labels);
  if (!silent) flashSaved();
  updateStats();
}

let flashTimer = null;
function flashSaved() {
  const f = document.getElementById('savedFlash');
  f.classList.add('show');
  clearTimeout(flashTimer);
  flashTimer = setTimeout(() => f.classList.remove('show'), 900);
}

function updateStats() {
  const all = Object.values(labels);
  const scored = all.filter(l => l.expectedScore !== undefined).length;
  const fav = all.filter(l => l.favorite).length;
  const sp = all.filter(l => l.special).length;
  const disc = all.filter(l => l.discard).length;
  document.getElementById('stats').innerHTML =
    `共标注 <b>${all.length}</b> 题 · 打分 ${scored} · 收藏 ${fav} · 特殊 ${sp} · 丢弃 ${disc}`;
}

// ---------------- 导入导出 ----------------
function download(filename, text, type) {
  const blob = new Blob([text], { type });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}
function exportJson() {
  download('starbattle_labels.json', JSON.stringify(labels, null, 2), 'application/json');
}
function exportCsv() {
  const cols = ['sbn', 'size', 'stars', 'expectedScore', 'algoScore', 'algoBand', 'favorite', 'special', 'discard', 'ts'];
  const rows = [cols.join(',')];
  for (const l of Object.values(labels)) {
    rows.push(cols.map(c => {
      const v = l[c];
      if (v === undefined || v === null) return '';
      if (typeof v === 'boolean') return v ? '1' : '';
      return String(v);
    }).join(','));
  }
  download('starbattle_labels.csv', rows.join('\n'), 'text/csv');
}
function importJson(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result);
      let n = 0;
      for (const k in data) { labels[k] = { ...labels[k], ...data[k] }; n++; }
      saveLabels(labels);
      updateStats();
      syncMarksUI();
      alert(`已导入/合并 ${n} 条标注`);
    } catch (e) { alert('导入失败：' + e.message); }
  };
  reader.readAsText(file);
}

// ---------------- 事件绑定 ----------------
function bind() {
  document.getElementById('mkFav').onclick = () => toggleMark('favorite', 'mkFav');
  document.getElementById('mkSpecial').onclick = () => toggleMark('special', 'mkSpecial');
  document.getElementById('mkDiscard').onclick = () => toggleMark('discard', 'mkDiscard');

  document.getElementById('btnNext').onclick = () => { saveCurrentLabel(false); clearTimeout(solveTimer); loadRandom(); };
  document.getElementById('btnSkip').onclick = () => { clearTimeout(solveTimer); loadRandom(); };

  document.querySelectorAll('#quickBands button').forEach(b => {
    b.onclick = () => { document.getElementById('expScore').value = b.dataset.v; };
  });
  document.getElementById('expScore').addEventListener('change', () => saveCurrentLabel(false));

  document.getElementById('btnExportJson').onclick = exportJson;
  document.getElementById('btnExportCsv').onclick = exportCsv;
  document.getElementById('btnImport').onclick = () => document.getElementById('importFile').click();
  document.getElementById('importFile').onchange = (e) => { if (e.target.files[0]) importJson(e.target.files[0]); };

  // 键盘快捷键
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'n' || e.key === 'Enter') { saveCurrentLabel(false); clearTimeout(solveTimer); loadRandom(); }
    else if (e.key === 's') { clearTimeout(solveTimer); loadRandom(); }
    else if (e.key === 'f') toggleMark('favorite', 'mkFav');
    else if (e.key === 'd') toggleMark('discard', 'mkDiscard');
    else if (e.key === 'x') toggleMark('special', 'mkSpecial');
  });
}

bind();
updateStats();
initSizes();
