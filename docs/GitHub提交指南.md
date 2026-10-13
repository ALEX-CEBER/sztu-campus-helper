# 期末要交的「项目 GitHub 仓库」怎么搞

> 课程要求：交 zip 源码 + 演示视频 + 报告；登记表/大报告里通常还要填 **GitHub 仓库链接**。
> 本文档讲清楚：仓库怎么建、代码怎么传、线上访问链接（GitHub Pages）怎么开、期末填什么。

---

## 一、三步走（你只需做第 1 步，其余可交给 AI）

### 第 1 步：在 GitHub 上建一个空仓库（你亲自做，约 2 分钟）
1. 登录 [github.com](https://github.com) → 右上角 **+ → New repository**
2. Repository name 填：`sztu-campus-helper`（建议全小写英文）
3. 选 **Public**（公开，方便老师/同学打开）
4. **不要**勾选 "Add a README file"（本地已有，勾了会冲突）
5. 点 **Create repository**

### 第 2 步：告诉 AI 两样东西
把下面两项发给 WorkBuddy / CodeBuddy（**只用于配置本地 Git，不会写进任何文档**）：
- GitHub **用户名**（本机已配置：`ALEX-CEBER`）
- GitHub **注册邮箱**（本机已配置：`202600802020@stumail.sztu.edu.cn`；
  ⚠️ 需到 GitHub → Settings → Emails 点验证链接，否则提交不会计入贡献绿点）

AI 会替你执行（本机已完成）：
```bash
git config --global user.name "ALEX-CEBER"
git config --global user.email "202600802020@stumail.sztu.edu.cn"
git remote add origin https://github.com/ALEX-CEBER/sztu-campus-helper.git
git push -u origin main
```
首次 push 会弹浏览器授权窗口 → 点 **Sign in with your browser** 授权，之后免登录。

### 第 3 步：验证
刷新 GitHub 页面能看到代码 = 成功。之后每次改动：
```bash
git add -A && git commit -m "完善：……" && git push
```

---

## 一·补：本机已选用的通道 —— SSH over 443（推荐）

校园网常封 22 端口、且代理会破坏 HTTPS 证书校验，因此本机改成 **SSH 走 443 端口**：
`~/.ssh/config` 已写入：

```
Host github.com
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/id_ed25519
```

**你只需做两件事**（各 1 分钟）：

1. **建空仓库**：GitHub → New repository → `sztu-campus-helper` → Public → 不要勾 README
2. **添加 SSH 公钥**（只需一次）：
   GitHub 右上角头像 → **Settings → SSH and GPG keys → New SSH key**
   → Title 填 `My PC` → Key 粘贴下面这整行（`docs/SSH公钥.txt` 里也有）：

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIML860eZYdp8MMb7i9TqQjhZO79FTJhRgSdtoNEAsTbI 202600802020@stumail.sztu.edu.cn
```

完成后回来跟我说"公钥加好了"，我立刻把全部代码推送上去（你不用再操作）。
验证命令（出现 "Hi ALEX-CEBER! You've successfully authenticated" 即成功）：
```bash
ssh -T git@github.com
```

> 备选：不想用 SSH 就双击 `推送到GitHub.bat`（HTTPS + 浏览器授权），脚本内置了证书校验失败自动重试。

## 二、期末要填的链接是什么

| 表格里要填的 | 填什么 | 示例 |
|---|---|---|
| **项目仓库（源码）** | 仓库首页地址 | `https://github.com/用户名/sztu-campus-helper` |
| **部署链接 / 在线访问** | GitHub Pages 地址 | `https://用户名.github.io/sztu-campus-helper/` |
| **演示视频** | 另行录屏上传（mp4，720p） | 交 zip/网盘链接 |
| **源码 zip** | `git archive -o 交付.zip HEAD`（只含仓库内容） | 见第四节 |

> 课程要求"zip 只留纳入 git 仓库的、≤10MB"：本项目是纯文本 + 一张立绘，
> 目前仓库很小；`dist/` 与 `*.mp4` 已在 `.gitignore` 中排除，不会撑大体积。

---

## 三、开启 GitHub Pages（把网页变成能打开的网址）

1. 先生成部署版（在项目根目录执行，改了内容就要重跑一次）：
   ```bash
   python scripts/build_standalone.py --pages
   ```
   会生成 `docs/index.html`（单文件，含数据与立绘，2MB 左右）
2. 提交并推送：
   ```bash
   git add -A && git commit -m "部署：更新 Pages 版本" && git push
   ```
3. GitHub 仓库页 → **Settings → Pages**（左侧 Build and deployment）
   - Source 选 **Deploy from a branch**
   - Branch 选 **main**，文件夹选 **/docs** → Save
4. 等 1–2 分钟，访问 `https://用户名.github.io/sztu-campus-helper/` 即可打开。
   把这个地址填进"部署链接"。

> 备选：不想生成 docs 版，也可以 Branch 选 main、文件夹选 **/root**，
> 但需要仓库根目录有 index.html——本项目根目录没有，所以推荐 `/docs` 方案。

---

## 四、打包提交用的源码 zip

```bash
git status                       # 确认没有多余文件
git archive -o 交付.zip HEAD     # 只打包 git 仓库内的文件
```
检查体积：`ls -lh 交付.zip`（应远小于 10MB）。

---

## 五、常见坑

| 一键推送 | 双击项目根目录 **`推送到GitHub.bat`**（自动 push，证书校验失败的校园网会自动重试一次） |
| 提示 `schannel: CRYPT_E_NO_REVOCATION_CHECK` 或证书错误 | 校园网/代理拦截 HTTPS 导致 git 校验证书失败 → 脚本会自动以跳过校验重试；或手动 `git -c http.sslVerify=false push` |
| 现象 | 原因 / 解决 |
|---|---|
| push 时提示鉴权失败 | 用浏览器登录方式授权；或改用 SSH（见 `docs/Git使用说明.md`） |
| 提交没算进贡献（不显示绿点） | `user.email` 与 GitHub 注册邮箱不一致，改完用 `git commit --amend --reset-author` 修正 |
| Pages 404 | 文件夹选错（应选 `/docs`），或未推送 `docs/index.html` |
| 网页打不开/没数据 | 直接双击 `dist/SZTU校园办事万事屋.html` 用的是本地单文件版，与 Pages 无关 |
| GitHub 打不开 | 校园网波动，重试或换手机热点；本地 commit 后代码不会丢 |

---

## 六、AI 助手速记

给 WorkBuddy / CodeBuddy 的一句话指令：
> "按 `docs/GitHub提交指南.md` 与 `docs/Git使用说明.md`，把本仓库关联到
> `https://github.com/<用户名>/sztu-campus-helper.git` 并 push，
> 然后生成 Pages 版到 docs/index.html 再提交一次。"
