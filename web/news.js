/* 校园资讯 —— 优先读本地接口 /api/news（实时抓官网），拿不到就用内嵌快照
   约定见 docs/api.md。页面加载、切到资讯页、点刷新、从别的窗口切回来，都会重新拉一次。
*/
(function () {
  const panel = document.getElementById("newsPanel");
  if (!panel) return;

  const API = "/api/news?max=30";
  const state = {
    data: null,        // { items, updated_at, count, stale }
    cat: "全部",
    loading: true,
    live: false,       // 是否来自接口
    error: "",         // 接口错误提示
    errorCode: "",     // 接口错误码（HTTP_404 表示静态托管没有这个接口）
    warning: null,     // 接口返回的兜底警告
    refreshing: false, // 服务端正在后台刷新
    lastFetch: 0,
    pollLeft: 3
  };

  const esc = s => String(s == null ? "" : s)
    .replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function fmtTime(iso) {
    if (!iso) return "未知时间";
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    const p = n => String(n).padStart(2, "0");
    return `${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
  }

  function relDate(dateStr) {
    if (!dateStr) return "";
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const d = new Date(dateStr + "T00:00:00");
    if (isNaN(d.getTime())) return dateStr;
    const diff = Math.round((today - d) / 86400000);
    if (diff === 0) return "今天";
    if (diff === 1) return "昨天";
    if (diff > 1 && diff < 7) return `${diff} 天前`;
    return dateStr.slice(5);
  }

  // ---------- 数据 ----------
  function updateAside(d) {
    const main = document.getElementById("asideNews");
    const meta = document.getElementById("asideMeta");
    if (!main || !meta || !d || !d.items || !d.items.length) return;
    main.textContent = d.items[0].title;
    meta.textContent = `${fmtTime(d.updated_at)} · 共 ${d.count} 条 · ${d.items[0].category || "校园"}`;
  }

  function snapshot() {
    const s = window.NEWS_DATA;
    return s && Array.isArray(s.items) && s.items.length ? s : null;
  }

  async function callApi(force) {
    const res = await fetch(`${API}&force=${force ? 1 : 0}`, { cache: "no-store" });
    let body = null;
    try { body = await res.json(); } catch (e) { /* 非 JSON，下面统一报错 */ }
    if (!res.ok) {
      const msg = body && body.error ? body.error.message : `接口返回 HTTP ${res.status}`;
      const err = new Error(msg);
      err.code = body && body.error ? body.error.code : `HTTP_${res.status}`;
      throw err;
    }
    if (!body || body.ok === false) throw new Error("接口返回格式不对");
    return body;
  }

  async function load(opts) {
    const force = !!(opts && opts.force);
    const quiet = !!(opts && opts.quiet);
    if (!quiet) { state.loading = !state.data; render(); }

    try {
      const body = await callApi(force);
      state.data = {
        items: body.items || [],
        updated_at: body.updated_at,
        count: body.count || (body.items || []).length,
        stale: !!body.stale,
        rejected: body.rejected || []
      };
      state.live = true;
      state.error = "";
      state.errorCode = "";
      state.warning = body.warning || null;
      state.refreshing = !!body.refreshing;
      state.lastFetch = Date.now();
      state.pollLeft = 3;
    } catch (err) {
      state.error = err.message || "请求失败";
      state.errorCode = err.code || "";
      state.refreshing = false;
      if (!state.data) {
        const snap = snapshot();
        if (snap) {
          state.data = { items: snap.items, updated_at: snap.updated_at, count: snap.count || snap.items.length, stale: true, rejected: [] };
          state.live = false;
        }
      }
    }

    state.loading = false;
    if (state.data) updateAside(state.data);
    render();

    // 服务端说它在后台抓，过两秒再取一次，拿来就更新的
    if (state.refreshing && state.pollLeft > 0) {
      state.pollLeft -= 1;
      setTimeout(() => load({ quiet: true }), 2000);
    }
  }

  // ---------- 渲染 ----------
  function skeletonHTML() {
    const one = `<div class="sk-card">
        <div class="sk-line w40"></div>
        <div class="sk-line w85"></div>
        <div class="sk-line w60"></div>
      </div>`;
    return `<div class="news-head"><h2 class="news-title">校园资讯</h2>
        <p class="news-meta">正在向校园通取最新消息…</p></div>
      <div class="news-list">${one}${one}</div>`;
  }

  function bannerHTML() {
    if (state.error) {
      const snapTime = state.data ? fmtTime(state.data.updated_at) : "";
      // 静态打开（双击文件 / 静态托管）没有本地接口，这是预期行为，用中性提示即可
      const staticHost = location.protocol === "file:" || state.errorCode.startsWith("HTTP_4");
      if (staticHost && state.data) {
        return `<div class="news-banner info">
          当前是 ${esc(snapTime)} 的离线快照：静态版没有本地接口。用 start.bat 启动服务后，这里的资讯会随页面刷新。
        </div>`;
      }
      return `<div class="news-banner error">
        接口没连上：${esc(state.error)}。
        ${state.live ? "页面保留上一次拿到的数据。" : `当前显示 ${esc(snapTime)} 的离线快照，用 start.bat 启动本地服务即可实时更新。`}
      </div>`;
    }
    if (state.warning) {
      return `<div class="news-banner warn">${esc(state.warning.message)}（${esc(state.warning.code)}）</div>`;
    }
    if (state.refreshing) {
      return `<div class="news-banner info">服务端正在后台抓取，稍后自动更新…</div>`;
    }
    if (state.data && state.data.rejected && state.data.rejected.length) {
      const r = state.data.rejected[0];
      return `<div class="news-banner info">
        本次有 ${state.data.rejected.length} 条数据未通过字段校验，已跳过（例如：${esc(r.reason)}）。
      </div>`;
    }
    return "";
  }

  // 分类配色：同分类固定同一色，分类多了也不至于花
  function catClass(name) {
    let h = 0;
    for (const ch of String(name || "")) h = (h * 31 + ch.codePointAt(0)) % 997;
    return "c" + (h % 4);
  }

  function render() {
    if (state.loading) { panel.innerHTML = skeletonHTML(); return; }

    const d = state.data;
    if (!d || !d.items.length) {
      panel.innerHTML = `
        <div class="news-empty">
          <p>暂时没有拿到资讯</p>
          <p class="sub">${state.error ? esc(state.error) : "可以先去校园通看看"}</p>
          <a class="news-link-btn" href="https://nbw.sztu.edu.cn/" target="_blank" rel="noopener">打开校园通 ↗</a>
        </div>`;
      return;
    }

    const cats = ["全部", ...new Set(d.items.map(i => i.category).filter(Boolean))];
    const items = state.cat === "全部" ? d.items : d.items.filter(i => i.category === state.cat);
    const badge = !state.live
      ? `<span class="badge-live off"><i class="dot"></i>离线快照</span>`
      : (d.stale
          ? `<span class="badge-live off"><i class="dot"></i>缓存兜底</span>`
          : `<span class="badge-live"><i class="dot"></i>实时</span>`);

    panel.innerHTML = `
      <div class="news-head">
        <div class="news-head-row">
          <div>
            <h2 class="news-title">校园资讯 ${badge}</h2>
            <p class="news-meta">
              来源：深圳技术大学校园通 · 共 ${d.count} 条 · 更新于 ${fmtTime(d.updated_at)}
              ${d.rejected && d.rejected.length ? ` · 已跳过 ${d.rejected.length} 条不合规数据` : ""}
            </p>
          </div>
          <button class="news-refresh ${state.refreshing ? "busy" : ""}" id="newsRefresh" ${state.refreshing ? "disabled" : ""}>
            ${state.refreshing ? "刷新中" : "刷新"}
          </button>
        </div>
        ${bannerHTML()}
        <div class="chips news-chips" id="newsChips">
          ${cats.map(c => `<button class="chip ${c === state.cat ? "on" : ""}" data-cat="${esc(c)}">${esc(c)}</button>`).join("")}
        </div>
      </div>
      <div class="news-list">
        ${items.map(it => `
          <a class="news-card" href="${esc(it.url)}" target="_blank" rel="noopener noreferrer">
            <div class="news-card-top">
              <span class="news-badge ${catClass(it.category)}">${esc(it.category || "校园")}</span>
              <span class="news-date">${esc(relDate(it.date))}</span>
            </div>
            <h3>${esc(it.title)}</h3>
            ${it.summary
              ? `<p class="news-summary">${esc(it.summary)}</p>`
              : `<p class="news-summary is-empty">这条只抓到标题，正文请点原文</p>`}
            <span class="news-more">查看原文 ↗</span>
          </a>`).join("")}
      </div>
      <p class="news-foot">${items.length} / ${d.count} 条 · 只保存标题、时间、分类与摘要，正文请点原文阅读</p>`;

    panel.querySelector("#newsChips").addEventListener("click", e => {
      const btn = e.target.closest(".chip");
      if (!btn) return;
      state.cat = btn.dataset.cat;
      render();
    });
    panel.querySelector("#newsRefresh").addEventListener("click", () => load({ force: true }));
  }

  // ---------- 视图切换 ----------
  const resultsEl = document.getElementById("results");
  let current = "qa";

  function switchView(view) {
    current = view;
    document.querySelectorAll(".tab").forEach(t => {
      const on = t.dataset.view === view;
      t.classList.toggle("active", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
    });
    document.getElementById("view-qa").hidden = view !== "qa";
    if (resultsEl) resultsEl.hidden = view !== "qa";
    panel.hidden = view !== "news";
    if (view === "news" && location.hash !== "#news") history.replaceState(null, "", "#news");
    if (view === "qa" && location.hash === "#news") history.replaceState(null, "", location.pathname);
    // 每次切到资讯都重新拉一次（3 秒内不重复打接口）
    if (view === "news" && Date.now() - state.lastFetch > 3000) load({ force: false });
  }

  document.querySelectorAll(".tab").forEach(t =>
    t.addEventListener("click", () => switchView(t.dataset.view)));
  window.addEventListener("hashchange", () =>
    switchView(location.hash === "#news" ? "news" : "qa"));

  // 从别的窗口/标签切回来时也刷新一次
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && current === "news" && Date.now() - state.lastFetch > 30000) {
      load({ force: false });
    }
  });

  // 停在资讯页时，每 90 秒轮询一次，让消息不落后
  setInterval(() => {
    if (current === "news" && document.visibilityState === "visible") load({ quiet: true, force: false });
  }, 90000);

  window.News = {
    init: () => load({ force: false }),
    refresh: () => load({ force: true }),
    switchView,
    state
  };

  const wantNews = location.hash === "#news" ||
    new URLSearchParams(location.search).get("view") === "news";

  load({ force: false }).then(() => {
    if (wantNews) switchView("news");
  });
})();
