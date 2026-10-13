/* 看板娘「深小技」—— 眼神追踪 / 眨眼 / 点击对话 / 位置校准
   说明：眼睛位置用百分比描述，储存在 localStorage。
   若与你生成的立绘对不齐，打开 index.html?calibrate=1 拖动瞳孔对齐后保存即可。
*/
(function () {
  const wrap = document.getElementById("mascot");
  const bubble = document.getElementById("bubble");
  const eyes = [
    { el: document.getElementById("eyeL"), key: "l" },
    { el: document.getElementById("eyeR"), key: "r" },
  ].map(o => ({ ...o, pupil: o.el.querySelector(".pupil") }));

  const STORE_KEY = "mascot_eye_cfg";
  const DEFAULT = { lx: 44, ly: 31, rx: 56.5, ry: 31 };
  let cfg = (() => {
    try { return { ...DEFAULT, ...JSON.parse(localStorage.getItem(STORE_KEY) || "{}") }; }
    catch (e) { return { ...DEFAULT }; }
  })();

  function applyPos() {
    eyes[0].el.style.left = cfg.lx + "%";
    eyes[0].el.style.top = cfg.ly + "%";
    eyes[1].el.style.left = cfg.rx + "%";
    eyes[1].el.style.top = cfg.ry + "%";
  }
  applyPos();

  // ---------- 眼神追踪 ----------
  let target = null;   // 鼠标位置
  let current = null;  // 平滑后的位置
  function look() {
    if (target) {
      current = current ? {
        x: current.x + (target.x - current.x) * 0.18,
        y: current.y + (target.y - current.y) * 0.18,
      } : { ...target };
      for (const e of eyes) {
        const r = e.el.getBoundingClientRect();
        const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
        const dx = current.x - cx, dy = current.y - cy;
        const dist = Math.hypot(dx, dy) || 1;
        const max = r.width * 0.26;                 // 瞳孔最大偏移
        const k = Math.min(1, dist / 240);          // 距离越近偏移越小
        e.pupil.style.transform =
          `translate(calc(-50% + ${(dx / dist) * max * k}px), calc(-50% + ${(dy / dist) * max * k}px))`;
      }
      // 身体轻微视差
      const px = ((current.x / window.innerWidth) - 0.5) * 10;
      const py = ((current.y / window.innerHeight) - 0.5) * 6;
      wrap.style.transform = `translate(${px}px, ${py}px)`;
    }
    requestAnimationFrame(look);
  }
  requestAnimationFrame(look);

  window.addEventListener("mousemove", e => { target = { x: e.clientX, y: e.clientY }; });
  window.addEventListener("mouseleave", () => { target = null; });
  // 触屏：拖动时也能跟随
  window.addEventListener("touchmove", e => {
    const t = e.touches[0]; if (t) target = { x: t.clientX, y: t.clientY };
  }, { passive: true });

  // ---------- 眨眼 ----------
  function blink() {
    eyes.forEach(e => e.el.classList.add("blink"));
    setTimeout(() => eyes.forEach(e => e.el.classList.remove("blink")), 130);
    setTimeout(blink, 2600 + Math.random() * 4200);
  }
  setTimeout(blink, 1800);

  // ---------- 对话气泡 ----------
  let bubbleTimer = null;
  function say(text, ms = 2800) {
    if (!bubble) return;
    bubble.textContent = text;
    bubble.classList.add("show");
    clearTimeout(bubbleTimer);
    bubbleTimer = setTimeout(() => bubble.classList.remove("show"), ms);
  }

  const LINES = [
    "你好呀，我是深小技～", "有什么校园问题尽管问我！",
    "试试搜「校园卡丢了怎么办」", "数据还在补充，发现错误记得告诉我哦",
    "（；′д｀）ゞ 这个我还没学会…", "点分类也可以直接看答案哦",
  ];

  wrap.addEventListener("click", () => {
    wrap.animate(
      [{ transform: "scale(1)" }, { transform: "scale(1.07)" }, { transform: "scale(1)" }],
      { duration: 420, easing: "cubic-bezier(.4,0,.2,1)" }
    );
    say(LINES[Math.floor(Math.random() * LINES.length)]);
    blink();
  });

  const input = document.getElementById("q");
  if (input) input.addEventListener("focus", () => say("我在听～说吧！", 1800));

  // ---------- 校准模式：index.html?calibrate=1 ----------
  if (new URLSearchParams(location.search).get("calibrate") === "1") {
    const tip = document.createElement("div");
    tip.className = "calib-tip";
    tip.innerHTML = "拖动两只瞳孔到正确位置 → <button>保存</button>";
    document.body.appendChild(tip);
    tip.querySelector("button").onclick = () => {
      localStorage.setItem(STORE_KEY, JSON.stringify(cfg));
      location.href = location.pathname;
    };
    for (const e of eyes) {
      e.el.style.cursor = "grab";
      e.el.addEventListener("pointerdown", ev => {
        e.el.setPointerCapture(ev.pointerId);
        const move = ev2 => {
          const r = wrap.getBoundingClientRect();
          const x = ((ev2.clientX - r.left) / r.width) * 100;
          const y = ((ev2.clientY - r.top) / r.height) * 100;
          cfg[e.key + "x"] = Math.round(x * 10) / 10;
          cfg[e.key + "y"] = Math.round(y * 10) / 10;
          applyPos();
        };
        e.el.addEventListener("pointermove", move);
        e.el.addEventListener("pointerup", () => {
          e.el.removeEventListener("pointermove", move);
        }, { once: true });
      });
    }
  }

  window.Mascot = { say, LINES };
  say("你好呀，我是深小技～", 3200);
})();
