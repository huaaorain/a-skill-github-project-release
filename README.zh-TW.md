<p align="center">
  <img src="docs/assets/readme-banner.svg" alt="GitHub Project Release skill" width="100%">
</p>

<h1 align="center">GitHub Project Release</h1>

<p align="center">
  <strong>把完成的專案整理成可發佈、可追溯、可恢復的 GitHub 倉庫與版本。</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-ff7a45?style=flat-square" alt="版本 0.1.0">
  <img src="https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/platform-GitHub-111816?style=flat-square&logo=github&logoColor=white" alt="GitHub">
  <img src="https://img.shields.io/badge/policy-release--only-c5f36b?style=flat-square" alt="僅限 Release">
</p>

<p align="center">
  <a href="README.en.md">English</a>
  ·
  <a href="README.md">简体中文</a>
  ·
  <strong>繁體中文</strong>
</p>

<p align="center">
  <a href="https://github.com/huaaorain/github-project-release/releases/latest"><strong>下載最新版本</strong></a>
  ·
  <a href="#核心能力">核心能力</a>
  ·
  <a href="#安裝">安裝</a>
  ·
  <a href="#使用方式">使用方式</a>
  ·
  <a href="#所有版本">所有版本</a>
  ·
  <a href="https://github.com/huaaorain/github-project-release/issues">回報問題</a>
</p>

---

## 解決的問題

專案完成後的發佈工作分散在 Git 提交、建置產物、Release 附件、README、版本說明與歷史下載目錄中。手動處理容易產生：

- 原始碼與建置產物混入同一個倉庫；
- 標籤、Release 與實際 commit 不一致；
- 更新說明漏掉相容性變更；
- 使用者無法判斷每個附件的用途；
- 歷史版本下載入口逐漸失效；
- 多語言 README 在版本發佈後失去同步。

**GitHub Project Release** 將這些步驟整理成受控流程，預設將原始碼放入 Git，而可執行檔與分發檔案只上傳到 Release。

## 核心能力

<table>
  <thead>
    <tr>
      <th>模組</th>
      <th>功能說明</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>首&#8239;次&#8239;發&#8239;佈</strong></td>
      <td>檢查專案、建立發佈設定與 GitHub 倉庫，並在確認後推送原始碼。</td>
    </tr>
    <tr>
      <td><strong>版&#8239;本&#8239;發&#8239;佈</strong></td>
      <td>根據確定的 commit 建立標籤、Draft Release、版本說明與下載附件。</td>
    </tr>
    <tr>
      <td><strong>文&#8239;件&#8239;清&#8239;單</strong></td>
      <td>為每個附件產生用途、類型、大小與 SHA-256，並輸出機器與人類可讀清單。</td>
    </tr>
    <tr>
      <td><strong>專&#8239;案&#8239;首&#8239;頁</strong></td>
      <td>依範本產生功能介紹、真實圖片、安裝說明、限制與版本目錄。</td>
    </tr>
    <tr>
      <td><strong>多&#8239;語&#8239;系</strong></td>
      <td>同步維護多份完整 README、語言切換入口與各自的版本目錄。</td>
    </tr>
    <tr>
      <td><strong>失&#8239;敗&#8239;恢&#8239;復</strong></td>
      <td>Draft 附件上傳失敗後可續傳；禁止覆蓋標籤、強制推送或偽造成功。</td>
    </tr>
  </tbody>
</table>

## 發佈流程

![GitHub Project Release workflow](docs/assets/release-flow.svg)

_上圖描述專案實際的發佈流程，不是軟體介面截圖。_

每個版本都經過「建置與測試 → 文件與圖片 → 文件清單 → 預檢 → Draft Release → 驗證 → 發佈 → 版本目錄更新」。失敗時停在可檢查狀態，不透過刪除標籤或覆蓋既有版本恢復。

## 安裝

將本倉庫複製或解壓到：

```text
${CODEX_HOME}/skills/github-project-release
```

Windows 預設位置通常是：

```text
C:\Users\<USER>\.codex\skills\github-project-release
```

重新開啟 Codex 後，可明確呼叫：

```text
$github-project-release
```

或從 Releases 下載 `github-project-release.zip`，解壓後將整個 `github-project-release/` 目錄放入 skills 路徑。不要只複製 `SKILL.md`，腳本、範本與參考文件都屬於工作流程的一部分。

## 使用方式

在專案完成程式碼、測試與建置後，對 Codex 說：

```text
使用 $github-project-release 把這個專案發佈到 GitHub。
```

也可以指定場景：

```text
使用 $github-project-release 為 v0.2.0 建立 Draft Release。
使用 $github-project-release 更新 README 與三語版本目錄。
使用 $github-project-release 只更新既有 Release 的說明，不修改附件。
```

## 安全邊界

- 建立倉庫、推送提交、發佈 Release 前分別取得授權。
- 預設建立 Draft Release，驗證後才公開。
- 可執行檔、壓縮包、執行環境與擴充包只進入 Release。
- Release 清單記錄 commit、標籤、檔案用途、大小與校驗值。
- 不輸出或寫入 GitHub Token，也不把憑證放入 remote URL。
- 不強制推送、不移動已發佈標籤、不覆蓋既有 Release。
- 沒有真實介面截圖時使用明確標示的流程圖，不把示意圖當成截圖。
- 專案首次公開發佈預設使用 `0.1.0`。

## 需求

- Python 3.10 或更新版本
- Git
- GitHub 倉庫寫入權限
- `GITHUB_TOKEN` 或 `GH_TOKEN`
- 專案自身的建置、測試與截圖環境

執行內建測試：

```powershell
python .\scripts\test_release_manager.py
```

查看命令：

```powershell
python .\scripts\release_manager.py --help
```

## 專案結構

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

`SKILL.md` 保留核心決策與安全邊界；詳細流程、README 規則、截圖要求與發佈說明契約依需要載入。`release_manager.py` 使用 Python 標準函式庫、Git 與 GitHub API，不依賴 GitHub CLI。

## 已知限制

- GitHub README 不執行 JavaScript，語言切換會開啟對應語言檔案。
- 自動截圖取決於專案是否提供可安全執行的展示模式。
- 無法只靠程式差異完整推斷使用者影響，版本說明仍需要一次人工檢查。
- GitHub 單一 Release 附件通常不能超過 2 GiB。
- 目前倉庫尚未宣告開源授權。

## 更新記錄

- [0.1.0：首個公開版本](docs/releases/v0.1.0.md)

## 所有版本

<!-- release-catalog:start -->
最新版本: [GitHub Project Release 0.1.0](https://github.com/huaaorain/github-project-release/releases/tag/v0.1.0)

| 版本 | 發佈時間 | 發佈說明 |
| --- | --- | --- |
| `v0.1.0` | 2026-10-27 | [開啟](https://github.com/huaaorain/github-project-release/releases/tag/v0.1.0) |

<details>
<summary><strong>全部版本下載</strong></summary>

### GitHub Project Release 0.1.0

發佈說明: [開啟](https://github.com/huaaorain/github-project-release/releases/tag/v0.1.0)

- [FILE_MANIFEST.md](https://github.com/huaaorain/github-project-release/releases/download/v0.1.0/FILE_MANIFEST.md) — 485 B
- [github-project-release.zip](https://github.com/huaaorain/github-project-release/releases/download/v0.1.0/github-project-release.zip) — 44.3 KB
- [release-manifest.json](https://github.com/huaaorain/github-project-release/releases/download/v0.1.0/release-manifest.json) — 729 B
- [SHA256SUMS.txt](https://github.com/huaaorain/github-project-release/releases/download/v0.1.0/SHA256SUMS.txt) — 93 B
- [原始碼（zip）](https://github.com/huaaorain/github-project-release/archive/refs/tags/v0.1.0.zip)
- [原始碼（tar.gz）](https://github.com/huaaorain/github-project-release/archive/refs/tags/v0.1.0.tar.gz)

</details>
<!-- release-catalog:end -->

## 致謝

- [GitHub REST API](https://docs.github.com/rest)
- [Best-README-Template](https://github.com/othneildrew/Best-README-Template)
- [awesome-readme-template](https://github.com/Louis3797/awesome-readme-template)
- [Standard Readme](https://github.com/RichardLitt/standard-readme)

## License

目前倉庫尚未指定開源授權。在加入授權前，請勿直接將此 skill 作為商業或再發佈專案的一部分使用。
