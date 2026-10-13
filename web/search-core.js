/* 检索核心（可被浏览器与 Node 测试脚本共用）
   设计要点：
   1) 中文没有空格，整句直接 includes 必然匹配失败 → 用 2/3-gram 切分
   2) 不同命中位置权重不同：问题标题 > 关键词 > 答案正文
   3) 片段越短越"泛"，权重越低；过滤停用词减少噪声
   4) 低于阈值的结果不展示，避免"什么都搜到"
*/
const STOPWORDS = new Set([
  "的","了","吗","呢","啊","我","你","请","问","一下","怎么","怎样","如何","什么",
  "哪里","那里","哪个","可以","能不能","需要","要","有","是","在","和","或","吧","呀"
]);

// 疑问词/礼貌词：整句提问时先剥掉它们，剩下的才是真正的"实词"
const QUESTION_WORDS = [
  "怎么样","怎样","怎么","如何","什么","哪里","哪个","哪","吗","呢","啊","吧",
  "请","请问","我","可以","能不能","能否","需不需要","要不要","咋办","怎么办","咋"
];

// 提取实词片段：如 "缓考怎么申请" -> ["缓考","申请"]
function coreTerms(query) {
  let s = String(query).toLowerCase();
  for (const w of QUESTION_WORDS) s = s.split(w).join(" ");
  return s
    .split(/[\s，。？?!,、；：""''（）()]+/)
    .filter(t => t.length >= 2 && !STOPWORDS.has(t));
}

// 极简同义词表（R4 可继续扩充）
const SYNONYMS = {
  "几点":"时间","什么时候":"时间","开放":"时间","开门":"时间","关门":"时间",
  "怎么办":"流程","咋办":"流程","如何办理":"流程","挂了":"挂科","补考":"补考",
  "网费":"校园网","wifi":"校园网","无线":"校园网","寝室":"宿舍","住宿":"宿舍",
  "一卡通":"校园卡","图书证":"借书","借还":"借书","奖学金":"奖学金"
};

function expand(term) {
  const out = [term];
  for (const [k, v] of Object.entries(SYNONYMS)) {
    if (term.includes(k)) out.push(v);
  }
  return out;
}

// 把一句话拆成：整句 + 3-gram + 2-gram
function tokenize(query) {
  const parts = String(query)
    .toLowerCase()
    .split(/[\s，。？?!,、；：""''（）()]+/)
    .filter(Boolean);
  const tokens = [];
  for (const p of parts) {
    tokens.push(p);
    const n = p.length;
    if (n >= 4) for (let i = 0; i <= n - 3; i++) tokens.push(p.slice(i, i + 3));
    if (n >= 2) for (let i = 0; i <= n - 2; i++) tokens.push(p.slice(i, i + 2));
    if (n === 1) tokens.push(p);
  }
  const cleaned = tokens.filter(t => !STOPWORDS.has(t));
  const expanded = [];
  for (const t of cleaned) expanded.push(...expand(t));
  return [...new Set(expanded)];
}

// 片段长度权重：越长越具体
function lenWeight(len) {
  if (len >= 4) return 1;
  if (len === 3) return 0.6;
  return 0.25;
}

function scoreItem(item, tokens, cores = []) {
  const q = (item.question || "").toLowerCase();
  const kw = (item.keywords || []).map(k => String(k).toLowerCase());
  const ans = (item.answer || "").toLowerCase();
  let s = 0;
  // ① n-gram 泛匹配
  for (const t of tokens) {
    const w = lenWeight(t.length);
    if (q.includes(t)) { s += 10 * w; continue; }              // 标题命中
    if (kw.some(k => k.includes(t) || t.includes(k))) { s += 6 * w; continue; }
    if (ans.includes(t)) { s += 1 * w; }
  }
  // ② 实词强匹配：命中实词给高加成，修正 "缓考怎么申请" 之类被疑问词带偏的排序
  for (const c of cores) {
    if (q.includes(c)) { s += 14; continue; }
    if (kw.some(k => k.includes(c) || c.includes(k))) { s += 9; continue; }
    if (ans.includes(c)) { s += 2; }
  }
  return s;
}

const MIN_SCORE = 1.5;

function searchAll(items, query, limit = 6) {
  const tokens = tokenize(query);
  const cores = coreTerms(query);
  if (!tokens.length) return [];
  return items
    .map(item => ({ ...item, _score: Number(scoreItem(item, tokens, cores).toFixed(2)) }))
    .filter(i => i._score >= MIN_SCORE)
    .sort((a, b) => b._score - a._score)
    .slice(0, limit);
}

if (typeof module !== "undefined") {
  module.exports = { tokenize, scoreItem, searchAll, MIN_SCORE };
}
