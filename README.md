# mlx-whisper-stock

這個 Codex 技能使用 `mlx-whisper` 將股市與財經節目的音訊或影片轉成 `.srt` 字幕，並透過 `uv` 管理 Python 環境與相依套件。

## 功能

- 使用 `uv` 初始化工作區、建立虛擬環境，並安裝 `mlx-whisper` 與相依套件。
- 轉錄時要求中文使用繁體中文，並保留原音中的英文。
- 套用 `words.csv` 的字詞替換規則，移除語助詞並清理常見的字幕雜訊。
- 將每筆字幕重排為單行，最多 20 字元。超過上限時拆成數筆，按比例分配原本的時間區段。清理後為空或只剩 1 字元的字幕會刪除。

## 系統需求

- 搭載 Apple 晶片的 Mac。
- 安裝 `uv` 和 `ffmpeg`，並確認兩者都能從 `PATH` 執行。轉錄時會透過 `ffmpeg` 讀取媒體的音訊。
- 使用下方的 SSH 指令複製儲存庫時，需先設定 GitHub SSH 金鑰，且帳號需有存取權限。

## 儲存庫主要檔案

```text
mlx-whisper-stock/
├── README.md
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── bootstrap_workspace.sh
│   ├── transcribe_stock_srt.sh
│   └── reflow_srt_entries.py
├── tests/
│   └── test_reflow.py
├── words.csv
├── install.sh
└── LICENSE
```

## 安裝技能

```bash
git clone git@github.com:anson9417/mlx-whisper-stock.git
cd mlx-whisper-stock
./install.sh
```

技能會安裝到 `${CODEX_HOME:-$HOME/.codex}/skills/mlx-whisper-stock`。執行 `install.sh` 會覆蓋這個目錄，請先備份要保留的本機修改。

## 在 Codex 中使用

在 Codex 的訊息中提及 `$mlx-whisper-stock`，並指定工作區內的音訊或影片。例如「用 `$mlx-whisper-stock` 幫我把 `INPUT.mp4` 轉成繁體中文字幕，套用 `words.csv` 的字詞替換規則。」

## 直接執行腳本

以下範例從儲存庫根目錄執行。第一次使用時，以 `uv` 初始化目前的工作區。

```bash
./scripts/bootstrap_workspace.sh .
```

將影片轉錄為 `OUTPUT_NAME.srt`，並套用 `words.csv` 進行清理與重排。

```bash
./scripts/transcribe_stock_srt.sh INPUT.mp4 OUTPUT_NAME words.csv
```

預設使用 `mlx-community/whisper-large-v3-turbo` 模型，轉錄語言為中文（`zh`）。在第四個參數傳入 `auto` 即可啟用語言自動偵測。

```bash
./scripts/transcribe_stock_srt.sh INPUT.mp4 OUTPUT_NAME words.csv auto
```

已有字幕時，可以只執行清理與重排。指令會直接更新 `INPUT.srt`。

```bash
uv run python ./scripts/reflow_srt_entries.py INPUT.srt words.csv
```

## 測試

從儲存庫根目錄執行單元測試與功能測試：

```bash
uvx --with opencc pytest tests/
```

要刪除的語助詞清單（`WORDS_TO_DELETE`）和「那」開頭要保留的前綴（`KEEP_NA_PREFIXES`）都定義在 `scripts/reflow_srt_entries.py`，以腳本為準。要調整規則請直接修改腳本，`SKILL.md` 只提醒規則的位置。

## 本機自動更新

這台 Mac 已另外設定 `launchd` 排程，每天台灣時間 17:30 比對已安裝的技能與 GitHub 的 `main`。版本相同時略過，遠端有新提交且可快轉時自動更新。遇到本機修改、提交歷史分岔或連線失敗時，排程會保留本機版本並記錄原因。

執行紀錄會追加到 `~/Library/Logs/mlx-whisper-stock/update.log`。此排程是這台 Mac 的本機設定，需另外安裝與載入。

## 授權

本專案採用 MIT 授權，詳見 [LICENSE](LICENSE)。
