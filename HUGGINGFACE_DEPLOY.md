# Deploy ScamShield AI to Hugging Face Spaces

Your project is already set up for Hugging Face (Dockerfile uses port 7860; README has `sdk: docker`). Use one of the options below to push and deploy.

---

## Option 1: Push via Git (recommended)

### 1. Create a Space on Hugging Face

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. Set **Space name** (e.g. `scamshield-ai`).
3. Choose **SDK**: **Docker**.
4. Choose **Space hardware** (e.g. CPU basic; upgrade if you need more).
5. Set visibility (Public/Private) and click **Create Space**.

### 2. Clone the Space repo and push your code

From your project folder (where your code already lives):

```bash
# Add Hugging Face as a remote (replace YOUR_USERNAME and YOUR_SPACE_NAME)
git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME

# Push your branch (e.g. main)
git push huggingface main
```

If the Space was just created and is empty, you can force-push your local repo into it:

```bash
git push huggingface main --force
```

**Using a Hugging Face token (HTTPS):**

1. Create a token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) with **write** access.
2. When prompted for password, paste the token:
   ```bash
   git push huggingface main
   # Username: YOUR_HF_USERNAME
   # Password: YOUR_HF_TOKEN
   ```

**Using SSH (if you use SSH keys with HF):**

```bash
git remote add huggingface git@hf.co:spaces/YOUR_USERNAME/YOUR_SPACE_NAME
git push huggingface main
```

### 3. Set secrets (required for the app)

In the Space page: **Settings** → **Repository secrets**. Add:

| Secret name     | Description                          |
|----------------|--------------------------------------|
| `GROQ_API_KEY` | Your Groq API key (LLM)              |
| `API_KEY`      | API key for `/honeypot/engage` (e.g. `dev-key-12345` for testing) |
| `HUGGINGFACE_TOKEN` | Optional; for gated IndicBERT if needed |

Then trigger a **Restart** (or push a small commit) so the Space rebuilds with the new secrets.

### 4. Open the Space

After the build finishes, open the Space URL:  
`https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`  
The UI is served at the root; API is at `/api/v1/...` (relative URLs work).

---

## Option 2: Connect a GitHub repo

1. Create the Space as in Option 1 (Docker, port 7860).
2. In the Space: **Settings** → **Repository** → **Connect to GitHub**.
3. Select the GitHub repo and branch that contains your ScamShield code.
4. Hugging Face will sync from GitHub. Set **Repository secrets** as in Option 1.

---

## Option 3: Upload files in the browser

1. Create the Space (Docker).
2. In the Space, upload or paste:
   - `Dockerfile`
   - `requirements.txt`
   - `README.md` (with the YAML block)
   - `app/` (all files)
   - `ui/` (all files)
   - `scripts/` (if the app needs them)
3. Add secrets and restart as in Option 1.

---

## Checklist

- [ ] Space created with **SDK: Docker**.
- [ ] Code pushed (Git, GitHub, or upload).
- [ ] Secrets set: `GROQ_API_KEY`, `API_KEY` (and `HUGGINGFACE_TOKEN` if needed).
- [ ] Space restarted / rebuild finished.
- [ ] App loads at the Space URL; no `ERR_CONNECTION_REFUSED` (relative URLs are used).

---

## Troubleshooting

- **Build fails**: Check the **Logs** tab; often missing dependency or wrong path. Ensure `Dockerfile` and `requirements.txt` are at repo root.
- **App starts but API 401**: Set the `API_KEY` secret and send `x-api-key` with value matching `API_KEY` (or use the value from your env, e.g. `dev-key-12345`).
- **IndicBERT / gated model**: Set `HUGGINGFACE_TOKEN` and accept the model’s terms on the model page.
