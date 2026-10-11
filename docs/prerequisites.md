# Prerequisites & Setup Checklist

> Send this to learners **at least 3 days before** delivery. The single biggest cause of a
> slow morning is unmet prerequisites. The recommended path (Codespaces / Dev Container)
> removes almost all of them.

---

## 1. Accounts (everyone)

- [ ] **GitHub account** with access to this repository.
- [ ] **GitHub Models access** — a fine-grained PAT with the **Models: read** permission
      (free). See [Lab 0 §0.2](../labs/lab-0-setup/README.md#02-get-an-inference-credential-free-path).
- [ ] **Azure subscription** with **Contributor** on at least one resource group.
      Free/MSDN/Visual Studio subscriptions are fine — labs use free/consumption SKUs.
      *(Optional for Labs 0–2; required to fully complete Labs 3–6.)*

> 💸 **Cost expectation:** Inference in class is **free** (GitHub Models). The Azure
> deploys in Labs 3–6 use consumption/free tiers and a daily Log Analytics cap; expect a
> few dollars at most if you **delete the resource group** at the end of the day.

---

## 2. Tooling

### Recommended: zero local install

- [ ] **GitHub Codespaces** — open the repo → *Code → Codespaces → Create codespace*.
      The dev container pins every tool. **This is the supported classroom path.**
- [ ] *or* **VS Code + Docker Desktop + Dev Containers extension** → *Reopen in Container*.

### Manual local install (only if not using the container)

| Tool | Version | Verify |
|---|---|---|
| Python | **3.12** | `python --version` |
| uv | latest | `uv --version` |
| .NET SDK | **9.0** | `dotnet --version` |
| Git | 2.40+ | `git --version` |
| GitHub CLI (`gh`) | latest | `gh --version` |
| Azure CLI (`az`) | latest | `az version` |
| Bicep | latest | `az bicep version` |
| VS Code (+ C#, Python, Bicep ext.) | latest | — |

> ⚠️ Use **Python 3.12**, not 3.13/3.14 — some Azure AI SDKs lack newer wheels. Every lab
> creates its venv with `uv venv --python 3.12`.

---

## 3. Pre-flight verification (run the day before)

```bash
# 1. Clone / open the repo (or create the Codespace)
git clone https://github.com/NikoMix/microhack-intelligent-automation.git
cd microhack-intelligent-automation

# 2. Confirm core tools
python --version        # 3.12.x
dotnet --version        # 9.0.x
az version
gh --version

# 3. Azure sign-in works and a subscription is visible
az login
az account show -o table

# 4. (Optional but ideal) pre-pull Python deps to save class time
cd src/inference/python && uv venv --python 3.12 && uv pip install -e ".[dev]" && cd ../../..

# 5. (Optional) pre-restore .NET
cd src/inference/dotnet && dotnet restore && cd ../../..
```

If all five steps succeed you are ready. If step 3 fails, sort Azure access **before**
class — it's the one thing that can't be fixed quickly on the day.

---

## 4. Network / firewall notes (corporate laptops)

Allow outbound HTTPS to:

- `github.com`, `*.githubusercontent.com`, `models.github.ai` (GitHub Models)
- `login.microsoftonline.com`, `*.azure.com`, `management.azure.com` (Azure + Entra)
- `*.openai.azure.com`, `*.services.ai.azure.com`, `*.cognitiveservices.azure.com` (Azure AI)
- `pypi.org`, `files.pythonhosted.org`, `api.nuget.org` (package feeds)

---

## 5. Trainer pre-flight (delivering this course)

- [ ] You personally completed **all** labs end-to-end at least once.
- [ ] You read the [facilitator guide](facilitator-guide.md) and the per-lab trainer notes.
- [ ] You created a throwaway **resource group** and confirmed the Bicep in
      `infra/bicep/core` deploys (`az deployment group create … core.bicep`).
- [ ] You have the [instructor `solutions` branch](facilitator-guide.md#instructor-solutions)
      checked out for reference answers.
- [ ] You decided your **flex plan** for Lab 6 (full hands-on vs guided demo).

➡️ Ready? Start with **[Lab 0](../labs/lab-0-setup/README.md)**.
