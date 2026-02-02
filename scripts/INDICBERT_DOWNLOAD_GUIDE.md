# IndicBERT Download Guide - Alternative Methods

Since you're having issues with transformers library, here are **3 alternative methods** to download IndicBERT:

---

## 🚀 Method 1: Using `huggingface_hub` (RECOMMENDED - Lightest)

**This is the SIMPLEST and LIGHTEST method - no transformers needed!**

### Step 1: Install huggingface_hub
```powershell
pip install huggingface_hub
```

### Step 2: Run the simple download script
```powershell
# Option A: Pass token as argument
python scripts/download_indicbert_simple.py your_token_here

# Option B: Set environment variable first
set HUGGINGFACE_TOKEN=your_token_here
python scripts/download_indicbert_simple.py
```

**That's it!** This will download the model files to your cache directory.

---

## 🔧 Method 2: Using Git LFS

If you have Git and Git LFS installed:

```powershell
# Install git-lfs (if not installed)
# Windows: Download from https://git-lfs.github.com/
# Then:
git lfs install
git clone https://your_token@huggingface.co/ai4bharat/indic-bert ./models/indic-bert
cd ./models/indic-bert
git lfs pull
```

---

## 🌐 Method 3: Direct API Download

Uses Python requests library to download files directly:

```powershell
python scripts/download_indicbert_alternative.py your_token_here
```

This script tries all 3 methods automatically.

---

## 📋 What You Need to Provide

1. **Your HuggingFace Token**
   - Get it from: https://huggingface.co/settings/tokens
   - Should start with `hf_`
   - Make sure it has "Read" permissions

2. **Model Access**
   - Request access at: https://huggingface.co/ai4bharat/indic-bert
   - Click "Agree and access repository"
   - Wait for approval (usually instant)

---

## ✅ Quick Test

Once you have your token, test it:

```powershell
# Install the lightweight library
pip install huggingface_hub

# Test download
python scripts/download_indicbert_simple.py your_token_here
```

---

## 🐛 Troubleshooting

### Error: "401 Unauthorized"
- **Fix**: Check your token is correct
- **Fix**: Make sure you've requested access to the model

### Error: "Gated repository"
- **Fix**: Request access at https://huggingface.co/ai4bharat/indic-bert
- **Fix**: Wait for approval, then try again

### Error: "huggingface_hub not found"
- **Fix**: `pip install huggingface_hub`

### Error: "Model not found"
- **Fix**: Check model ID: `ai4bharat/indic-bert`
- **Fix**: Verify it exists at HuggingFace

---

## 📍 Model Location After Download

After successful download, the model will be cached at:
- **Windows**: `C:\Users\<username>\.cache\huggingface\hub\models--ai4bharat--indic-bert`
- **Linux/Mac**: `~/.cache/huggingface/hub/models--ai4bharat--indic-bert`

You can use it later with:
```python
from transformers import AutoModel
model = AutoModel.from_pretrained("ai4bharat/indic-bert", token="your_token")
```

---

## 🎯 Recommended Approach

**Use Method 1 (huggingface_hub)** - it's the simplest and doesn't require transformers!

```powershell
pip install huggingface_hub
python scripts/download_indicbert_simple.py your_token_here
```
