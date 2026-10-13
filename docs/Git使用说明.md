# Git & GitHub 小白使用说明（供我和我的 AI 助手随时调用）

> 本项目：`C:\Users\you\WorkBuddy\2026-10-13-12-17-14\sztu-campus-helper`
> Git 已安装并配置完成（v2.55，配置见文末）。把本文件丢给 WorkBuddy / CodeBuddy，
> 说一句"按 docs/Git使用说明.md 操作"，AI 就知道怎么帮你提交。

---

## 一、10 分钟理解 Git

- **Git** = 给项目拍快照的工具。每次"提交(commit)"就是存一个可回滚的存档点（像游戏存档）。
- **GitHub** = 把这些存档放到云端的网站，课程要求交源码就是交 GitHub 仓库链接。
- **仓库(repository)** = 一个被 Git 管理的项目文件夹。
- 三步节奏：**改文件 → `git add`（选出要存档的改动）→ `git commit`（存档）**。

```
工作文件夹 ──git add──▶ 暂存区 ──git commit──▶ 本地仓库 ──git push──▶ GitHub 云端
```

## 二、日常只会用到的 6 条命令（在项目文件夹里打开终端）

```bash
git status                  # 看看改了什么（随时敲，无副作用）
git add -A                  # 把所有改动放入暂存区
git commit -m "新增：图书馆分类5条问答"   # 存档，引号里写这次改了什么
git log --oneline           # 查看历史存档
git push                    # 上传到 GitHub
git pull                    # 从 GitHub 拉取最新（换电脑/组队时先 pull）
```

**背口诀：status → add → commit → push。** 其他的交给 AI。

## 三、首次关联 GitHub（做一次就够）

1. 注册/登录 [github.com](https://github.com)，右上角 **+ → New repository**，
   名字填 `sztu-campus-helper`，**不要**勾选自动生成 README，点创建。
2. 在项目文件夹终端执行（`你的用户名` 换成自己的）：
   ```bash
   git remote add origin https://github.com/你的用户名/sztu-campus-helper.git
   git push -u origin main
   ```
3. 第一次 push 会弹出 Git Credential Manager 登录窗口 → 点 **Sign in with your browser**
   → 授权后以后 push 都不用再登录。
4. 刷新 GitHub 页面能看到代码即成功。

## 四、出事了怎么办（急救包）

| 状况 | 怎么办 |
|---|---|
| 改乱了想回到上次存档 | `git checkout -- 文件名`（丢弃单个文件改动）；不确定就先问 AI |
| commit 信息写错了 | 还没 push：`git commit --amend -m "新信息"` |
| 想回到某个历史版本 | **先 `git log --oneline` 复制哈希值，然后问 AI**，别自己 reset --hard |
| push 报错 rejected | 先 `git pull` 再 `git push` |
| 误删文件想找回 | `git checkout -- .` 或问 AI（只要 commit 过就丢不了） |

> 🤖 铁律：**任何你没把握的 Git 操作，把报错原样贴给 AI 再执行。**

## 五、AI 助手调用约定（写给 WorkBuddy / CodeBuddy）

- 每次会话开始可先 `git status` + `git log --oneline -5` 了解项目状态。
- 提交规范：中文一句话，前缀用 `新增：`/`修复：`/`完善：`/`文档：`。
- 禁止 `git push --force`、禁止修改 git 历史；大文件（mp4/zip）已被 .gitignore 排除，勿强行添加。
- 分支策略（本课单人/双人项目够用）：日常直接提交 main；大改前可 `git switch -c 分支名` 建分支试验。

## 六、本机已完成的环境配置清单

| 项目 | 状态 |
|---|---|
| Git for Windows v2.55 | ✅ 已安装 |
| `user.name` | ✅ `SZTU-Student`（**待改成你的真实姓名**，见下） |
| `user.email` | ✅ GitHub 匿名邮箱占位（**待改成你的 GitHub 注册邮箱**） |
| 默认分支 main / 换行符 / 长路径 / 中文文件名 | ✅ 已优化 |
| 凭据管理器 (credential.helper manager) | ✅ push 时弹浏览器登录一次即可 |
| SSH 密钥 `~/.ssh/id_ed25519` | ✅ 已生成（备用方案） |

**改署名（用你注册 GitHub 的邮箱，提交才会算进你的贡献绿点）：**
```bash
git config --global user.name "你的真实姓名"
git config --global user.email "你的GitHub注册邮箱"
```

**备用 SSH 方式（若校园网 https 不稳）：**
把 `C:\Users\you\.ssh\id_ed25519.pub` 文件内容整行复制到
GitHub → Settings → SSH and GPG keys → New SSH key，然后 remote 改用
`git@github.com:你的用户名/sztu-campus-helper.git`。

## 七、换电脑 / 组队时

1. 新电脑装 Git（[git-scm.com](https://git-scm.com) 一路下一步）。
2. `git clone https://github.com你的用户名/sztu-campus-helper.git` 即可拿到全部代码。
3. 队友提交后你先 `git pull` 再继续干活，能少 90% 冲突。
