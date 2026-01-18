# HuggingFace 整合指南 (輕量化方案)

> **哲學**: 保持 Boring Core 輕量，利用 HuggingFace 的各項工具 (`git`, `git-lfs`) 進行免費的雲端儲存。

此指南說明如何將您的「大腦」(`.boring-brain`) 備份並分享到 HuggingFace Datasets。

## 為什麼選擇 HuggingFace?
- **免費**: 無限的公開 Dataset 儲存空間。
- **Git 原生**: 完美契合 Boring 的 GitOps 哲學。
- **LFS 支援**: 對大檔案 (向量資料庫) 支援極佳。

## 前置準備
1. 註冊 [HuggingFace 帳號](https://huggingface.co/join)。
2. 安裝 Git LFS: `git lfs install`。
3. 設定 SSH Key 或 Access Token。

## 工作流 (Workflow)

### 1. 匯出大腦
首先，將您的 Agent 知識匯出為單一檔案：

```bash
boring brain export --output my-knowledge.boring-brain
```

### 2. 建立 HuggingFace Dataset
1. 前往 [HuggingFace New Dataset](https://huggingface.co/new-dataset).
2. 設定名稱 (例如 `my-username/boring-knowledge`).
3. 建立 Repository (Create Dataset).

### 3. 上傳 (Git LFS)

```bash
# 1. Clone 剛剛建立的 Repo
git clone https://huggingface.co/datasets/my-username/boring-knowledge
cd boring-knowledge

# 2. 啟用 LFS 追蹤 .boring-brain 檔案
git lfs install
git lfs track "*.boring-brain"
git add .gitattributes

# 3. 複製並提交檔案
cp ../my-knowledge.boring-brain .
git add my-knowledge.boring-brain
git commit -m "feat: update brain knowledge dump"

# 4. 推送
git push
```

### 4. 下載與匯入 (隊友視角)

您的隊友現在可以輕鬆取得知識：

```bash
# 下載
wget https://huggingface.co/datasets/my-username/boring-knowledge/resolve/main/my-knowledge.boring-brain

# 匯入 (合併模式)
boring brain import my-knowledge.boring-brain
```

## 自動化建議
您可以將上述步驟寫成一個簡單的 Shell Script (`upload_brain.sh`)，放在您的專案中。

```bash
#!/bin/bash
boring brain export -o latest.boring-brain
cd boring-knowledge-repo
mv ../latest.boring-brain .
git add latest.boring-brain
git commit -m "Auto-backup"
git push
```
