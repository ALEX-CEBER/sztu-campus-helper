/* 校园办事万事屋 —— 前端检索逻辑（离线优先，AI 增强预留） */
const state = { qa: [], query: "" };

// ---------- 数据加载 ----------
async function loadQA() {
  try {
    const res = await fetch("../data/qa.json");
    state.qa = await res.json();
  } catch (e) {
    // file:// 直接打开会被浏览器 CORS 拦截 —— 请用本地服务器打开（见 README）
    document.getElementById("results").innerHTML =
      '<div class="empty">⚠️ 无法加载知识库。<br>请用 <b>start.bat</b> 或 <code>python -m http.server</code> 启动后再访问。</div>';
    console.error(e);
    return;
  }
  renderChips();
  renderHot();
}

// ---------- 打分检索：问题 > 关键词 > 答案 ----------
function score(item, tokens) {
  let s = 0;
  const q = item.question.toLowerCase();
  const kw = (item.keywords || []).map(k => k.toLowerCase());
  const ans = item.answer.toLowerCase();
  for (const t of tokens) {
    if (q.includes(t)) s += 10;                 // 标题命中权重最高
    if (kw.some(k => k.includes(t) || t.includes(k))) s += 6;
    if (ans.includes(t)) s += 1;
  }
  return s;
}

function search(query) {
  const tokens = query.toLowerCase().split(/[\s，。？?!,、]+/).filter(Boolean);
  if (!tokens.length) return [];
  return state.qa
    .map(item => ({ item, s: score(item, tokens) }))
    .filter(x => x.s > 0)
    .sort((a, b) => b.s - a.s)
    .slice(0, 6)
    .map(x => x.item);
}

// ---------- 渲染 ----------
function cardHTML(item) {
  const badge = item.answer.includes("[待核实]")
    ? ' <span style="color:#d48806">⚠含待核实</span>' : "";
  return `<div class="card">
    <span class="score">相关度 ${item._score || ""}</span>
    <span class="cat">${item.category || "未分类"}</span>${badge}
    <h3>${item.question}</h3>
    <pre>${item.answer}</pre>
    <div class="src">📎 来源：${item.source || "—"} · ID:${item.id}</div>
  </div>`;
}

function renderList(items, headerHTML) {
  const box = document.getElementById("results");
  box.innerHTML = (headerHTML || "") +
    (items.length ? items.map(cardHTML).join("")
                  : '<div class="empty">没查到…换个说法试试，或到「反馈」里提交新问题~</div>');
}

function renderHot() {
  // 默认展示前 5 条热门问题
  renderList(state.qa.slice(0, 5),
    '<div class="card mascot-say"><h3>🌸 深小技悄悄说</h3><pre>这些是同学们最常问的问题，点分类可以筛选哦！</pre></div>');
}

function renderChips() {
  const cats = [...new Set(state.qa.map(i => i.category).filter(Boolean))];
  const box = document.getElementById("chips");
  box.innerHTML = cats.map(c => `<span class="chip" data-cat="${c}">${c}</span>`).join("");
  box.addEventListener("click", e => {
    const cat = e.target.dataset.cat;
    if (!cat) return;
    renderList(state.qa.filter(i => i.category === cat),
      `<div class="card mascot-say"><h3>📂 分类：${cat}</h3></div>`);
  });
}

// ---------- 事件 ----------
document.getElementById("ask").addEventListener("click", doSearch);
document.getElementById("q").addEventListener("keydown", e => {
  if (e.key === "Enter") doSearch();
});

function doSearch() {
  const query = document.getElementById("q").value.trim();
  if (!query) return renderHot();
  const scored = searchAll(query);
  renderList(scored, `<div class="card mascot-say"><h3>🔍 为你找到 ${scored.length} 条</h3><pre>没有命中时，可以接入校内 AI 模型兜底（见 app.js 的 aiFallback，仅上课当晚接口开放时可用）。</pre></div>`);
}

function searchAll(query) {
  const tokens = query.toLowerCase().split(/[\s，。？?!,、]+/).filter(Boolean);
  return state.qa
    .map(item => ({ ...item, _score: score(item, tokens) }))
    .filter(i => i._score > 0)
    .sort((a, b) => b._score - a._score)
    .slice(0, 6);
}

// ---------- AI 增强占位（第 5 周报告接入） ----------
// 校内模型接口仅上课当天晚上开放：这里留好"检索失败 → 调用 LLM 总结知识库片段"的钩子。
async function aiFallback(query, contextItems) {
  // TODO: fetch(校内模型接口, { method: "POST", body: JSON.stringify({ prompt: buildPrompt(query, contextItems) }) })
  // Prompt 模板：你是深圳技术大学校园助手"深小技"，请仅依据以下资料回答，资料没有的说明去哪里核实：
  // + contextItems.map(i => i.question + "\n" + i.answer).join("\n---\n")
  console.log("AI 兜底预留，检索上下文：", contextItems.length, "条");
  return null;
}

loadQA();
