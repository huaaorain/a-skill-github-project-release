<p align="center">
  <img src="docs/assets/readme-banner.svg" alt="GitHub Project Release skill" width="100%">
</p>

<h1 align="center">GitHub Project Release</h1>

<p align="center">
  <strong>把一个完成的项目整理成可发布、可追溯、可恢复的 GitHub 仓库与版本。</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-ff7a45?style=flat-square" alt="Version 0.1.0">
  <img src="https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/platform-GitHub-111816?style=flat-square&logo=github&logoColor=white" alt="GitHub">
  <img src="https://img.shields.io/badge/policy-release--only-c5f36b?style=flat-square" alt="Release-only">
</p>

<p align="center">
  <a href="README.en.md">English</a>
  ·
  <strong>简体中文</strong>
  ·
  <a href="README.zh-TW.md">繁體中文</a>
</p>

<p align="center">
  <a href="https://github.com/huaaorain/github-project-release/releases/latest"><strong>下载最新版本</strong></a>
  ·
  <a href="#核心能力">核心能力</a>
  ·
  <a href="#安装">安装</a>
  ·
  <a href="#使用方式">使用方式</a>
  ·
  <a href="#所有版本">所有版本</a>
  ·
  <a href="https://github.com/huaaorain/github-project-release/issues">反馈问题</a>
</p>

---

## 解决的问题

项目开发完成后，发布通常分散在 Git 提交、构建产物、Release 附件、README、版本说明和历史下载目录等多个步骤中。手动执行容易出现：

- 源码与构建产物混入同一个仓库；
- 标签、Release 和实际 commit 不一致；
- 更新说明漏掉兼容性变化；
- 用户无法判断每个附件是什么；
- 历史版本下载入口逐渐失效；
- 多语言 README 在版本发布后失去同步。

**GitHub Project Release** 把这些步骤组织成一套受控工作流，默认采用“源码进入 Git，可执行程序与分发文件只进入 Release”的策略。

## 核心能力

<table>
  <thead>
    <tr>
      <th>模块</th>
      <th>功能说明</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>首&#8239;次&#8239;发&#8239;布</strong></td>
      <td>检查项目、生成发布配置、创建 GitHub 仓库，并在确认后推送源码。</td>
    </tr>
    <tr>
      <td><strong>版&#8239;本&#8239;发&#8239;布</strong></td>
      <td>基于确定 commit 生成标签、Draft Release、版本说明和下载附件。</td>
    </tr>
    <tr>
      <td><strong>文&#8239;件&#8239;清&#8239;单</strong></td>
      <td>为每个附件生成用途、大小、类型与 SHA-256，并输出机器与人类可读清单。</td>
    </tr>
    <tr>
      <td><strong>项&#8239;目&#8239;主&#8239;页</strong></td>
      <td>按照可配置模板生成功能介绍、真实图片、安装说明、限制和版本目录。</td>
    </tr>
    <tr>
      <td><strong>多&#8239;语&#8239;言</strong></td>
      <td>同步维护多个完整 README、语言切换入口和各自的本地化发布目录。</td>
    </tr>
    <tr>
      <td><strong>失&#8239;败&#8239;恢&#8239;复</strong></td>
      <td>Draft Release 上传失败后可继续上传；禁止覆盖标签、强制推送或伪造成功。</td>
    </tr>
  </tbody>
</table>

## 发布流程

![GitHub Project Release workflow](docs/assets/release-flow.svg)

_上图描述项目的实际发布流程，不是软件界面截图。_

每个版本都经过“构建与测试 → 文档与图片 → 文件清单 → 预检 → Draft Release → 验证 → 发布 → 版本目录刷新”。失败时停在可检查状态，不通过删除标签或覆盖已有版本来恢复。

## 安装

### 方式一：复制到 Codex skills 目录

将本仓库克隆或解压到：

```text
${CODEX_HOME}/skills/github-project-release
```

Windows 默认位置通常是：

```text
C:\Users\<USER>\.codex\skills\github-project-release
```

重新打开 Codex 后，可显式调用：

```text
$github-project-release
```

### 方式二：使用发布包

从 Releases 下载 `github-project-release.zip`，解压后将 `github-project-release/` 整个目录放入 skills 路径。不要只复制 `SKILL.md`，脚本、模板和参考文档都是工作流的一部分。

## 使用方式

在项目中完成代码、测试和构建后，对 Codex 说：

```text
使用 $github-project-release 把这个项目发布到 GitHub。
```

或指定场景：

```text
使用 $github-project-release 为 v1.2.0 生成 Draft Release。
使用 $github-project-release 更新 README 和三语版本目录。
使用 $github-project-release 只优化已有 Release 的说明，不修改附件。
```

## 安全边界

- 创建仓库、推送提交、发布 Release 前分别取得授权。
- 默认创建 Draft Release，验证后才公开。
- 可执行文件、压缩包、运行时和扩展包只进入 Release。
- Release 清单记录 commit、标签、文件用途、大小和校验值。
- 不打印或写入 GitHub Token，不把凭据放进 remote URL。
- 不强制推送，不移动已发布标签，不覆盖已有 Release。
- 没有真实界面截图时使用明确标注的流程图，不把示意图伪装成截图。

## 要求

- Python 3.10 或更高版本
- Git
- GitHub 仓库写权限
- `GITHUB_TOKEN` 或 `GH_TOKEN`，用于建库、Release 和仓库元数据操作
- 项目自身的构建、测试和截图环境

运行内置测试：

```powershell
python .\scripts\test_release_manager.py
```

查看命令：

```powershell
python .\scripts\release_manager.py --help
```

## 项目结构

```text
github-project-release/
├─ SKILL.md
├─ agents/
├─ assets/
├─ references/
└─ scripts/
   ├─ release_manager.py
   └─ test_release_manager.py
```

`SKILL.md` 保留核心决策与安全边界；详细流程、README 规则、截图要求和发布说明契约按需加载。`release_manager.py` 使用 Python 标准库、Git 和 GitHub API，不依赖 GitHub CLI。

## 已知限制

- GitHub README 不支持 JavaScript，语言切换会打开对应语言文件。
- 自动截图取决于项目是否提供可安全运行的演示模式。
- 无法根据代码 diff 完全推断产品影响，发布说明仍需一次人工审核。
- GitHub 单个 Release 附件通常不能超过 2 GiB。
- 当前仓库尚未声明开源许可证。

## 更新记录

- [0.1.0：首个公开版本](docs/releases/v0.1.0.md)

## 所有版本

<!-- release-catalog:start -->
版本目录将在首次 Release 发布后生成。
<!-- release-catalog:end -->

## 致谢

- [GitHub REST API](https://docs.github.com/rest)
- [Best-README-Template](https://github.com/othneildrew/Best-README-Template)
- [awesome-readme-template](https://github.com/Louis3797/awesome-readme-template)
- [Standard Readme](https://github.com/RichardLitt/standard-readme)

## License

当前仓库尚未指定开源许可证。在添加许可证前，请勿直接将此 skill 作为商业或再分发项目的一部分使用。
