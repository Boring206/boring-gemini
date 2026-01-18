# HuggingFace Integration Guide (Lightweight)

> **Philosophy**: Keep Boring Core light using HuggingFace's standard tools (`git`, `git-lfs`) for free cloud storage.

This guide explains how to backup and share your `.boring-brain` files on HuggingFace Datasets.

## Why HuggingFace?
- **Free**: Unlimited storage for public datasets.
- **Git-Native**: Fits perfectly with Boring's GitOps philosophy.
- **LFS Support**: Excellent support for large files (Vector DBs).

## Prerequisites
1. Create a [HuggingFace Account](https://huggingface.co/join).
2. Install Git LFS: `git lfs install`.
3. Set up SSH Key or Access Token.

## Workflow

### 1. Export Brain
First, export your Agent's knowledge into a single file:

```bash
boring brain export --output my-knowledge.boring-brain
```

### 2. Create HuggingFace Dataset
1. Go to [HuggingFace New Dataset](https://huggingface.co/new-dataset).
2. Set a name (e.g., `my-username/boring-knowledge`).
3. Create Repository.

### 3. Upload (Git LFS)

```bash
# 1. Clone the repo you just created
git clone https://huggingface.co/datasets/my-username/boring-knowledge
cd boring-knowledge

# 2. Enable LFS tracking for .boring-brain files
git lfs install
git lfs track "*.boring-brain"
git add .gitattributes

# 3. Copy and Commit
cp ../my-knowledge.boring-brain .
git add my-knowledge.boring-brain
git commit -m "feat: update brain knowledge dump"

# 4. Push
git push
```

### 4. Download & Import (Teammate's View)

Your teammate can now easily fetch the knowledge:

```bash
# Download
wget https://huggingface.co/datasets/my-username/boring-knowledge/resolve/main/my-knowledge.boring-brain

# Import (Merge Mode)
boring brain import my-knowledge.boring-brain
```

## Automation Tip
You can wrap these steps into a simple Shell Script (`upload_brain.sh`) in your project.

```bash
#!/bin/bash
boring brain export -o latest.boring-brain
cd boring-knowledge-repo
mv ../latest.boring-brain .
git add latest.boring-brain
git commit -m "Auto-backup"
git push
```
