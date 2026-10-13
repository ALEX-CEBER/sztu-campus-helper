/* 检索命中率测试（R4 报告素材）
   用法：node scripts/test_search.js
*/
const path = require("path");
const fs = require("fs");
const { searchAll } = require(path.join(__dirname, "..", "web", "search-core.js"));

const items = JSON.parse(
  fs.readFileSync(path.join(__dirname, "..", "data", "qa.json"), "utf-8")
);

const CASES = [
  "校园卡丢了怎么办", "图书馆几点开门", "怎么借书", "宿舍可以用电磁炉吗",
  "挂科了能补考吗", "选修课什么时候选", "校园网怎么连", "密码忘了怎么办",
  "奖学金什么时候评", "助学金怎么申请", "医保怎么报销", "心理咨询怎么预约",
  "报道要带什么", "军训多久", "图书馆座位怎么预约", "宿舍报修",
  "转专业需要什么条件", "GPA怎么算", "缓考怎么申请", "成绩有异议怎么办",
];

let hit = 0;
console.log("查询".padEnd(16), "命中", " 首条结果");
console.log("-".repeat(70));
for (const q of CASES) {
  const r = searchAll(items, q, 3);
  if (r.length) hit++;
  console.log(
    q.padEnd(14, "　"),
    String(r.length).padStart(2),
    "  ",
    r.length ? `${r[0].question} (${r[0]._score})` : "❌ 未命中"
  );
}
console.log("-".repeat(70));
console.log(`命中率：${hit}/${CASES.length} = ${Math.round((hit / CASES.length) * 100)}%`);
