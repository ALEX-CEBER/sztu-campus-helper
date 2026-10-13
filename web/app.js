/* 校园办事万事屋 —— 前端逻辑（离线优先，AI 增强预留）
   数据优先级：内嵌 window.QA_DATA(由 build_index.py 生成) > fetch ../data/qa.json
   —— 这样双击打开、本地服务器、预览面板三种方式都能用。
*/
const state = { qa: [], query: "" };

async function loadQA() {
  // 1) 优先用内嵌数据（data/qa.js），file:// 直接打开也不怕
  if (window.QA_DATA && window.QA_DATA.length) {
    state.qa = window.QA_DATA;
  } else {
    // 2) 退而求其次：尝试 fetch
    for (const url of ["../data/qa.json", "./data/qa.json"]) {
      try {
        const res = await fetch(url);
        if (res.ok) { state.qa = await res.json(); break; }
      } catch (e) { /* 继续尝试下一个路径 */ }
    }
  }
  if (!state.qa.length) {
    document.getElementById("results").innerHTML =
      '<div class="empty">⚠️ 知识库没加载到。<br>请在项目根目录运行 <code>python scripts/build_index.py</code> 生成 data/qa.js 后刷新。</div>';
    return;
  }
  renderChips();
  renderHot();
}

// ---------- 渲染 ----------
function esc(s) {
  return String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

function cardHTML(item) {
  const mark = item.answer.includes("[待核实]")
    ? ' <span class="warn-tag">⚠ 含待核实内容</span>' : "";
  return `<div class="card">
    <span class="score">相关度 ${item._score}</span>
    <span class="cat">${esc(item.category || "未分类")}</span>${mark}
    <h3>${esc(item.question)}</h3>
    <pre>${esc(item.answer)}</pre>
    <div class="src">📎 来源：${esc(item.source || "—")} · ID:${item.id}</div>
  </div>`;
}

function renderList(items, headerHTML) {
  const box = document.getElementById("results");
  box.innerHTML = (headerHTML || "") +
    (items.length ? items.map(cardHTML).join("") : emptyHTML());
}

function emptyHTML() {
  const hot = state.qa.slice(0, 4).map(i => `<span class="chip" data-q="${esc(i.question)}">${esc(i.question)}</span>`).join(" ");
  return `<div class="empty">
    <p>（；′д｀）ゞ 深小技没查到…换个说法试试？</p>
    <div class="chips" style="justify-content:center;margin-top:10px">${hot}</div>
  </div>`;
}

function renderHot() {
  if (window.Mascot) Mascot.say("下面是同学们最常问的问题～", 2400);
  renderList(state.qa.slice(0, 5).map(i => ({ ...i, _score: "—" })),
    '<div class="card mascot-say"><h3>🌸 深小技悄悄说</h3><pre>下面是同学们最常问的问题～也可以直接在上面搜索框提问，支持整句话哦！</pre></div>');
}

function renderChips() {
  const cats = [...new Set(state.qa.map(i => i.category).filter(Boolean))];
  const box = document.getElementById("chips");
  box.innerHTML = '<span class="chip static">分类：</span>' +
    cats.map(c => `<span class="chip" data-cat="${esc(c)}">${esc(c)}</span>`).join("");
}

// ---------- 事件（事件委托：分类、热门问题都能点） ----------
document.addEventListener("click", e => {
  const el = e.target.closest(".chip");
  if (!el) return;
  if (el.dataset.q) {
    document.getElementById("q").value = el.dataset.q;
    return doSearch();
  }
  const cat = el.dataset.cat;
  if (!cat) return;
  renderList(state.qa.filter(i => i.category === cat).map(i => ({ ...i, _score: "—" })),
    `<div class="card mascot-say"><h3>📂 分类：${esc(cat)}</h3></div>`);
});

document.getElementById("ask").addEventListener("click", doSearch);
document.getElementById("q").addEventListener("keydown", e => {
  if (e.key === "Enter") doSearch();
});

function doSearch() {
  const query = document.getElementById("q").value.trim();
  if (!query) return renderHot();
  const hits = searchAll(state.qa, query);   // 来自 web/search-core.js
  if (window.Mascot) {
    Mascot.say(hits.length ? `找到 ${hits.length} 条，往下看 ↓` : "（；′д｀）ゞ 没查到，换个说法？");
  }
  renderList(hits, `<div class="card mascot-say"><h3>🔍 关于「${esc(query)}」找到 ${hits.length} 条</h3>
    <pre>${hits.length ? "" : "提示：知识库目前主要覆盖教务/宿舍/图书馆/校园卡/奖助/新生六类。"}</pre></div>`);
}

// ---------- AI 增强占位（第 5 周报告接入） ----------
// 校内模型接口仅上课当天晚上开放：这里留好"检索失败 → 调用 LLM 总结知识库片段"的钩子。
async function aiFallback(query, contextItems) {
  // TODO: fetch(校内模型接口, { method:"POST", body: JSON.stringify({ prompt: buildPrompt(query, contextItems) }) })
  // Prompt 模板：你是深圳技术大学校园助手"深小技"，仅依据以下资料回答；资料没有的内容请说明去哪里核实：
  // + contextItems.map(i => i.question + "\n" + i.answer).join("\n---\n")
  console.log("AI 兜底预留，检索上下文：", contextItems.length, "条");
  return null;
}

loadQA();
