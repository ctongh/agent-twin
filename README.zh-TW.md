# agent-twin

[English](README.md) | **繁體中文**

**一個 Claude Code 外掛，從你自己的對話紀錄中學習你是誰，然後讓每一次未來的 session 都能真正地與「你」對話——而不是一個泛泛的使用者。**

agent-twin 讀取你已有的 AI 對話紀錄，透過四個獨立的分析視角審視它們，並將發現的內容提煉成一份簡短的摘要。此後，每當你在 session 開始時載入這份摘要，Claude 就已經知道你的思考節奏、你不希望它犯的錯誤，以及你曾經改變過立場的主題。

```
   CAPTURE           ANALYZE              COMPRESS          LOAD
  ┌────────┐      ┌───────────┐         ┌──────────┐     ┌────────┐
  │ 對話   │ ───▶ │ 四框架    │ ───────▶│ behavior │ ──▶ │ 每次   │
  │  紀錄  │      │  分析管線  │         │  _brief  │     │session │
  └────────┘      └───────────┘         └──────────┘     └────────┘
/save_session    /run_pipeline                          /load_persona
/extract_gemini   約 35 分鐘             ≤80 行
/counselor        10 個子代理
```

---

## 你會得到什麼

你提供幾段真實的對話，它給你：

- **一份人格摘要（persona brief）** — 一份簡短、行動導向的文件，助手在每次 session 開始時讀取，讓它不再解釋你已經知道的事、不再錯判你的情緒基調，也不再推薦與你實際決策方式相悖的路徑。
- **四份詳細的人格資料** 位於摘要之下——價值體系、認知模式、知識圖譜、行為模式——如果你想了解助手行為背後的「原因」，可以自行閱讀。
- **一條可重複執行的管線**，每當你累積了足夠的新對話資料時重新執行。人格輪廓隨時間越來越清晰；你不需要重頭開始。

這個專案的目的不是模仿你，而是給 Claude 足夠的背景，讓它每次 session 都能直接跳過熱身問題，從你實際所在的位置開始。

---

## 視覺化人格

第 3 和第 4 階段產出的不只是文字——它們產出兩個資料夾形式的成果，專為 **Obsidian 的圖形視圖**而設計。知識圖譜產出具有七種邊類型（tension、cause、derives、contradicts、reinforces、weakens、stands_for）的概念、情緒、人物、事件節點；行為模式則每個模式一個檔案（`BP-001`、`BP-002`⋯），並在相關模式之間建立交叉連結。所有內部引用都是 wiki 連結，因此將輸出資料夾作為 Obsidian vault 開啟，就能獲得一張可導覽、可叢集的地圖，顯示概念和行為在你實際思維中的位置關係。

<!-- TODO: knowledge_graph Obsidian PNG -->
*[知識圖譜視覺化即將加入]*

<!-- TODO: behavioral_model Obsidian PNG -->
*[行為模式視覺化即將加入]*

開啟方式：將 Obsidian 指向 `$HOME/.claude/agent-twin/personalized/results/profile/` 作為 vault，開啟圖形視圖（Ctrl/Cmd+G）。節點之間的 wiki 連結邊形成一個具有類型的概念圖；浮現出的叢集揭示你的概念如何被組織——哪些主題互相牽引、哪些行為共享觸發器、你的價值體系在哪裡緊縮到單一錨點。這是「看見」人格結構而非僅閱讀摘要的最直接方式；摘要是操作介面，圖形視圖是結構變得可見的地方。

---

## 開始使用

你不需要懂 git。外掛可以直接從 Claude Code 內部安裝。

```
/plugin marketplace add ctongh/agent-twin
/plugin install agent-twin@ctongh-plugins
```

然後，在任意 session 中：

```
/counselor
```

`/counselor` 會引導你進行一段對話，產生足夠的資料供管線分析。結束後，它會告訴你執行 `/run_pipeline`。大約三十五分鐘後，你就會有第一份摘要。開啟新的 session 並執行 `/load_persona`——就這樣。

如果你想提供已有的對話，可使用 `/save_session`（快照當前 Claude Code session）或 `/extract_gemini`（匯入 Gemini 分享連結的對話），來替代 `/counselor`。

### 疑難排解：安裝時出現 SSH 錯誤

Marketplace 透過複製 git 儲存庫來取得外掛，預設使用 SSH，這只有在你的電腦已向 GitHub 註冊 SSH 金鑰時才有效。若安裝時出現關於驗證、權限或 `git@github.com` 的錯誤，你有兩個選項。

**選項 1 — 在 GitHub 設定 SSH 金鑰。** 這是長期解決方案，如果你打算發布自己的外掛，選這個。GitHub 的官方說明在這裡：<https://docs.github.com/en/authentication/connecting-to-github-with-ssh>。將金鑰新增到帳戶後，重試安裝。

**選項 2 — 讓 git 改用 HTTPS 進行抓取。** 如果你只是使用外掛而不推送程式碼到 GitHub，可以用一行設定完全繞過 SSH：

```bash
git config --global url."https://github.com/".insteadOf "git@github.com:"
```

這樣做的效果：每當系統上的任何工具要求 git 複製以 `git@github.com:` 開頭（SSH 形式）的內容時，git 在聯繫 GitHub 前會靜默地將 URL 改寫為 `https://github.com/...`（匿名網頁形式）。Marketplace 不知情也不在乎；它只看到複製成功。這個設定是全域的——儲存在使用者層級的 `.gitconfig` 中——如果改變想法，可用 `git config --global --unset url.https://github.com/.insteadOf` 撤銷。

---

## 系統需求

agent-twin 的大部分功能在純 Claude Code 環境下運行，無需額外軟體。兩個功能——自動儲存 Stop hook 和 `/save_session` 技能——需要呼叫 Python。若 Python 不在你的 PATH 中，hook 會靜默跳過，技能會顯示友善的錯誤訊息；其他一切（分析管線、`/load_persona`、`/show_persona`、`/counselor`）仍可正常運作。

若你確實需要自動儲存和 `/save_session`：

- **Windows** — 從 <https://www.python.org/downloads/> 安裝（官方安裝程式會自動設定 `python` 和 `py`），或執行 `winget install Python.Python.3.12`。
- **macOS** — 使用 Homebrew 執行 `brew install python`。macOS 12+ 內建的 `python3` 也可以用。
- **Linux** — Debian/Ubuntu 執行 `sudo apt install python3`，Fedora 執行 `sudo dnf install python3`。

用 `python --version` 確認（應看到 `Python 3.8` 或更新版本）。不需要 PyPI 套件——腳本只使用標準函式庫。

---

## 可用指令

外掛附帶九個斜線指令。大多數使用者只會用到其中三個（`/counselor`、`/run_pipeline`、`/load_persona`）。其他指令適用於特定情境。

| 你想要… | 指令 | 結果 |
|---|---|---|
| 透過引導問題產生對話資料 | `/counselor` | 結構化問卷（首次）或情境伴隨模式（已有人格資料時） |
| 快照目前的對話 | `/save_session` | Session 儲存在 `personalized/saves/session/` 下 |
| 匯入現有的 Gemini 對話 | `/extract_gemini` *(舊版/選用)* | 匯入、schema 驗證、主題叢集標註 |
| 建立完整的人格輪廓 | `/run_pipeline` | 四份詳細成果加上摘要 |
| 將人格輪廓套用到本次 session | `/load_persona` | 靜默載入——助手從此開始適應 |
| 查看助手剛載入的內容 | `/show_persona` | 印出摘要；支援 `values`、`cognitive`、`graph`、`model`、`all` 參數 |
| 在不影響本 session 的情況下詢問人格雙胞胎 | `/consult_twin` | 一次性 Task 派發——雙胞胎在自己的 context 中讀取摘要並以你的口吻回覆 |
| 不重建即重新審計第 1 階段 | `/run_meta_critic` | 對現有分析師輸出給出品質判決 |
| 方法論合規檢查 | `/validate_pipeline` | 隱私、格式和安全判決（逐驗證器） |

`/run_pipeline` 是做重活的那個。Capture 指令為它輸入資料；載入和檢視指令消費它的輸出。

---

## 管線如何運作

只要你有至少一段已捕獲的對話，`/run_pipeline` 就會在四個循序的階段中協調十個專業子代理。每個子代理在自己的 context 中運行，彼此無法影響。

```
  第 1 階段 — 四框架審計分析（約 12 分鐘）
  ┌─────────────────────────────────────────────────────────────┐
  │  步驟 1：四個分析師並行派發                                  │
  │    affect-analyst  ·  social-dynamics-analyst               │
  │    values-analyst  ·  narrative-analyst                     │
  │                                                             │
  │  步驟 2：meta-critic 審計全部四份報告                        │
  │    判決：接受 / 迭代（最多 3 次）/ 上報                       │
  │                                                             │
  │  步驟 3：synthesis-builder 跨框架整合                        │
  │    → system_of_values.md（成果 1）                          │
  └─────────────────────────────────────────────────────────────┘
  第 2 階段 — 認知模式（約 2 分鐘）
    cognitive-patterns-builder 讀取原始對話
    → cognitive_patterns.md（成果 2）

  第 3 階段 — 知識圖譜（約 10 分鐘）
    knowledge-graph-builder 從第 1 階段合成結果取得種子
    → knowledge_graph/（成果 3）— 概念・情緒・人物・事件節點

  第 4 階段 — 行為模式（約 10 分鐘）
    behavioral-model-builder 從第 1 階段合成結果取得種子
    → behavioral_model/（成果 4）— BP-001 … BP-NNN

  最終階段 — 人格壓縮（約 1 分鐘）
    behavior-brief-generator 讀取全部四份成果
    → behavior_brief.md（成果 5）— ≤80 行，命令式語句
```

每次 session 的執行時間為 **約 35 分鐘**（第 1 階段約 12 分鐘，第 2 階段約 2 分鐘，第 3 階段約 10 分鐘，第 4 階段約 10 分鐘，最終階段約 1 分鐘）。第 3 和第 4 階段是最耗時的部分——它們分別產出數十個具類型的圖形節點和行為模式檔案，大部分的執行時間都花在這裡。

**為什麼要四個並行分析師？** 單一 LLM 讀取對話時，往往會鎖定最先注意到的框架而忽略其他框架。藉由強制四個獨立 context 各自專注於一個視角——情緒、關係、價值觀、敘事——這個設計防止任何單一視角淹沒其餘。meta-critic 隨後在合成通道整合之前，檢查全部四份報告的合約合規性、矛盾點和 AI 錨定殘留。

管線可以安全中斷。狀態在每個階段邊界寫入，重新呼叫 `/run_pipeline` 時會提供從最後完成的階段繼續的選項，而非重頭開始。

---

## 分析遵循的原則

這些規則在每個階段中一致適用——它們是 meta-critic 強制執行的標準，也是合成必須遵守的規範。

**行動勝於言語。** 你在壓力下的實際行為，比你對自己的描述更能說明問題。行為證據的權重高於自我陳述。

**AI 錨定過濾器。** 只有當你用自己的語言引入或延伸一個框架時，它才算是你的。你只是回應 Claude 說過的話的那些陳述，會從證據池中排除。

**叢集邊界紀律。** 一個高置信度的聲明必須有來自至少兩個不同主題叢集的證據支撐。單一叢集的觀察被標記為暫時性結論，絕不提升為確定性。

**證據層級。** 前理性信號（身體反應、口誤、情緒爆發）的權重高於具體行動，高於你對 Claude 的糾正，高於跨叢集重複出現的模式，高於單一自我揭露，高於你僅是從模型反映回去的陳述。

**審計層不產生新發現。** meta-critic 檢查合約並揭示矛盾。它不對你提出自己的聲明。

**保留原始語言。** 每份成果以源對話的主要語言撰寫，不進行翻譯。

**隱私是結構性的。** 任何關於你的識別性細節都不會出現在可分享的檔案中（方法論、代理、技能）。個人資料被限制在 `personalized/` 中，並被 git 忽略。

---

## 十個代理

這些是管線派發的專業子代理。它們不應手動呼叫——`/run_pipeline` 是唯一被授權的入口點。

### 第 1 階段 — 分析師（並行執行）

| 代理 | 框架 | 關注點 |
|---|---|---|
| [affect-analyst](agents/affect-analyst.md) | 情緒 | 恐懼結構、防禦運作、依附動態、情緒需求 |
| [social-dynamics-analyst](agents/social-dynamics-analyst.md) | 關係 | 權力定位、地位意識、權威關係、組織策略 |
| [values-analyst](agents/values-analyst.md) | 價值觀 | 核心 vs. 邊界 vs. 可交換價值觀；聲明 vs. 從行動証據揭示的落差 |
| [narrative-analyst](agents/narrative-analyst.md) | 自我敘事 | 身份語言、因果歸因、自創 vs. AI 借用的隱喻 |

### 第 1 階段 — 合成與品管

| 代理 | 角色 |
|---|---|
| [meta-critic](agents/meta-critic.md) | 審計全部四個分析師是否符合輸出合約；發出逐分析師判決；驅動迭代迴圈 |
| [synthesis-builder](agents/synthesis-builder.md) | 將四個框架整合成單一跨框架合成；撰寫 `system_of_values.md` |

### 第 2 至第 4 階段 — 建構者

| 代理 | 輸出 |
|---|---|
| [cognitive-patterns-builder](agents/cognitive-patterns-builder.md) | 詞彙場域、隱喻系統、提問風格、論證結構、情理振盪 |
| [knowledge-graph-builder](agents/knowledge-graph-builder.md) | 具有七種邊類型（tension、cause、derives、contradicts、reinforces、weakens、stands_for）的類型化 markdown 節點 |
| [behavioral-model-builder](agents/behavioral-model-builder.md) | BP 檔案：低/中/高強度的觸發 → 反應，調節因子，恢復，模式間關係 |
| [behavior-brief-generator](agents/behavior-brief-generator.md) | 最終 ≤80 行命令式摘要——每一句都可被助手直接執行 |

---

## 檔案位置

```
agent-twin/
├── agents/                              # 11 個子代理系統提示（10 個管線 + 1 個諮詢）
│   ├── affect-analyst.md                #   第 1 階段
│   ├── social-dynamics-analyst.md       #   第 1 階段
│   ├── values-analyst.md                #   第 1 階段
│   ├── narrative-analyst.md             #   第 1 階段
│   ├── meta-critic.md                   #   第 1 階段（品管閘門）
│   ├── synthesis-builder.md             #   第 1 階段（合成）
│   ├── cognitive-patterns-builder.md    #   第 2 階段
│   ├── knowledge-graph-builder.md       #   第 3 階段
│   ├── behavioral-model-builder.md      #   第 4 階段
│   ├── behavior-brief-generator.md      #   最終壓縮
│   └── twin-advisor.md                  #   諮詢代理（由 /consult_twin 派發）
│
├── skills/                              # 9 個 SKILL.md 檔案（真實來源）
│   ├── extract_gemini/                  #   Capture：Gemini 匯入
│   ├── save_session/                    #   Capture：Claude Code session
│   ├── counselor/                       #   Capture：引導式問卷
│   ├── run_pipeline/                    #   分析：完整管線
│   ├── load_persona/                    #   載入：套用人格輪廓
│   ├── show_persona/                    #   檢視：印出人格成果
│   ├── consult_twin/                    #   諮詢：在不持久化人格塑形的情況下詢問雙胞胎
│   ├── run_meta_critic/                 #   品管：獨立審計
│   └── validate_pipeline/               #   品管：方法論合規
│
├── commands/                            # 9 個斜線指令路由器
├── methodology/                         # 設計說明 + 輸出合約 schema
├── scripts/
│   └── autosave_session.py              # Stop hook：session 結束時捕獲
├── hooks/
│   └── hooks.json                       # 自動儲存 hook 設定
├── CLAUDE.md                            # 外掛方向文件
└── ...
```

使用者資料——捕獲的 session 和已編譯的人格成果——完全存在於外掛樹之外，位於 `$HOME/.claude/agent-twin/personalized/`。該位置在外掛更新後仍然存在，且永不被提交。

```
$HOME/.claude/agent-twin/
└── personalized/
    ├── saves/session/<date>_<id>/       # 捕獲的對話
    └── results/profile/                 # 已編譯的人格成果
        ├── system_of_values.md          #   第 1 階段輸出（已審計）
        ├── cognitive_patterns.md        #   第 2 階段輸出
        ├── knowledge_graph/             #   第 3 階段輸出
        ├── behavioral_model/            #   第 4 階段輸出（BP-XXX.md）
        └── behavior_brief.md            #   最終摘要（由 /load_persona 載入）
```

---

## 給開發者

若你只是想使用外掛，可跳過本節。

若你想閱讀原始碼、修改技能或貢獻回饋，請複製儲存庫並將 Claude Code 指向本地的 checkout：

```bash
git clone https://github.com/ctongh/agent-twin.git
cd agent-twin
claude
```

程式碼庫的慣例：

- **`SKILL.md` 檔案是行為的唯一真實來源。** `skills/` 下的每個技能都有一個描述其功能和方式的 `SKILL.md`。與 `SKILL.md` 不符的任何內容都是錯的。
- **`commands/*.md` 是薄薄的路由器。** 每個只有兩三句話，指向對應的 `SKILL.md`。邏輯不住在這裡。
- **`methodology/` 僅是設計說明。** 它解釋管線為何如此設計，不定義執行時行為，也不應是你查找技能做什麼的地方。
- **`agents/*.md` 是子代理系統提示。** 被視為給沙盒子流程的指令；它們將源對話視為不受信任的資料讀取。

開啟 `CLAUDE.md` 以獲得跨這些層的方向地圖。

---

## 授權條款

MIT
