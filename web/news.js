/* 校园资讯模块 —— 渲染 data/news.js / news.json
   数据由 scripts/fetch_news.py 生成（构建时抓取，规避浏览器跨域限制）。
*/
(function () {
  const state = { data: null, cat: "全部", error: false };
  const panel = document.getElementById("newsPanel");
  if (!panel) return;

  const esc = s => String(s == null ? "" : s)
    .replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function fmtTime(iso) {
    if (!iso) return "未知";
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    const p = n => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
  }

  // 相对时间：今天 / 昨天 / N 天前 / 日期
  function relDate(dateStr) {
    if (!dateStr) return "";
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const d = new Date(dateStr + "T00:00:00");
    const diff = Math.round((today - d) / 86400000);
    if (diff === 0) return "今天";
    if (diff === 1) return "昨天";
    if (diff > 1 && diff < 7) return `${diff} 天前`;
    return dateStr.slice(5); // MM-DD
  }

  async function loadData() {
    if (window.NEWS_DATA && window.NEWS_DATA.items) return window.NEWS_DATA;
    for (const url of ["../data/news.json", "./data/news.json"]) {
      try {
        const res = await fetch(url + "?t=" + Date.now());
        if (res.ok) return await res.json();
      } catch (e) { /* 试下一个路径 */ }
    }
    return null;
  }

  function skeleton(text) {
    panel.innerHTML = `<div class="news-empty"><p>${text}</p></div>`;
  }

  function render() {
    const d = state.data;
    if (!d || !d.items || !d.items.length) {
      panel.innerHTML = `
        <div class="news-empty">
          <p>暂时获取不到资讯……</p>
          <p class="sub">可以直接去校园通查看：</p>
          <a class="news-link-btn" href="https://nbw.sztu.edu.cn/" target="_blank" rel="noopener">打开校园通 ↗</a>
        </div>`;
      return;
    }

    const cats = ["全部", ...new Set(d.items.map(i => i.category).filter(Boolean))];
    const items = state.cat === "全部" ? d.items : d.items.filter(i => i.category === state.cat);

    panel.innerHTML = `
      <div class="news-head">
        <div class="news-head-row">
          <div>
            <div class="news-title-row">
              <h2>校园资讯</h2>
              <span class="news-src">来源：深圳技术大学校园通</span>
            </div>
            <p class="news-meta">
              更新于 ${fmtTime(d.updated_at)} · 共 ${d.count} 条
              ${d.stale ? '<span class="news-stale">· 网络异常，以下为上次缓存</span>' : ""}
            </p>
          </div>
          <button class="news-refresh" id="newsRefresh" title="重新拉取">刷新</button>
        </div>
        <div class="chips news-chips" id="newsChips">
          ${cats.map(c => `<button class="chip ${c === state.cat ? "on" : ""}" data-cat="${esc(c)}">${esc(c)}</button>`).join("")}
        </div>
      </div>
      <div class="news-list">
        ${items.map(it => `
          <a class="news-card" href="${esc(it.url)}" target="_blank" rel="noopener noreferrer">
            <div class="news-card-top">
              <span class="news-badge">${esc(it.category || "通知")}</span>
              <span class="news-date">${esc(relDate(it.date))}</span>
            </div>
            <h3>${esc(it.title)}</h3>
            ${it.summary ? `<p class="news-summary">${esc(it.summary)}</p>` : ""}
            <span class="news-more">查看原文 ↗</span>
          </a>`).join("")}
      </div>
      <p class="news-foot">
        资讯版权归深圳技术大学所有，本页仅展示标题/摘要并跳转原文，用于课程学习。
        抓取频率受限（含 0.8s 请求间隔与本地缓存），如原站更新延迟请以官网为准。
      </p>`;

    panel.querySelector("#newsChips").addEventListener("click", e => {
      const btn = e.target.closest(".chip");
      if (!btn) return;
      state.cat = btn.dataset.cat;
      render();
    });
    const rf = panel.querySelector("#newsRefresh");
    if (rf) rf.addEventListener("click", refresh);
  }

  async function refresh() {
    const btn = panel.querySelector("#newsRefresh");
    if (btn) { btn.disabled = true; btn.textContent = "刷新中…"; }
    state.data = await loadData();
    render();
    if (state.data) {
      window.dispatchEvent(new CustomEvent("news:loaded", { detail: state.data.count }));
    }
  }

  async function init() {
    skeleton("正在获取校园资讯…");
    state.data = await loadData();
    render();
    if (window.Mascot && state.data) {
      // 与看板娘联动（若该版本启用了 mascot.js）
      Mascot.say && Mascot.say(`校园资讯已更新到 ${state.data.count} 条～`, 2600);
    }
  }

  // ---------- 视图切换（办事问答 / 校园资讯） ----------
  const resultsEl = document.getElementById("results");
  function switchView(view) {
    document.querySelectorAll(".tab").forEach(t =>
      t.classList.toggle("active", t.dataset.view === view));
    document.getElementById("view-qa").hidden = view !== "qa";
    if (resultsEl) resultsEl.hidden = view !== "qa";
    panel.hidden = view !== "news";
    // 支持 #news 直达（可分享链接给同学）
    if (view === "news" && location.hash !== "#news") history.replaceState(null, "", "#news");
    if (view === "qa" && location.hash === "#news") history.replaceState(null, "", location.pathname);
    if (view === "news" && !state.data) init();
  }
  document.querySelectorAll(".tab").forEach(t =>
    t.addEventListener("click", () => switchView(t.dataset.view)));
  window.addEventListener("hashchange", () =>
    switchView(location.hash === "#news" ? "news" : "qa"));

  window.News = { init, refresh, state, switchView };
  // 支持 #news 与 ?view=news 两种直达方式（file:// 下 hash 有时被忽略）
  const wantNews = location.hash === "#news" ||
    new URLSearchParams(location.search).get("view") === "news";
  if (wantNews) switchView("news");
})();
