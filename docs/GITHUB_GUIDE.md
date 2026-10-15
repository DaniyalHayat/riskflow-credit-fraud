# Use and update your GitHub project

The project is already published at **https://github.com/DaniyalHayat/riskflow-credit-fraud**. You do not need to create another repository.

## Recommended: work with the existing repository

1. Open the repository link and choose **Code → Open with GitHub Desktop** (or **File → Clone repository** in GitHub Desktop and paste the URL). Choose a permanent local folder.
2. Open the downloaded folder. On Windows, double-click `start_windows.cmd`; open `excel/RiskFlow_Analytics.xlsx` for the workbook.
3. Edit your project files. In GitHub Desktop, inspect the Changes list and confirm that no keys or local database files are included.
4. Write a short change summary, select **Commit to main**, then **Push origin**.
5. Open the repository and its **Actions** tab to check the published change. Keep the local folder for future edits.

For a download without GitHub Desktop, choose **Code → Download ZIP**, then extract it. The README includes setup and a visual walkthrough of the application and all seven workbook sheets.

The instructions below explain publication from scratch if you later create a separate portfolio project.

# Publish a new copy from scratch

Publish the **riskflow-credit-fraud folder**, not your full Resume project and not the ZIP as a single file. Extract the ZIP first. The correct folder contains `README.md`, `riskflow`, `web`, `tests`, `excel`, and `.gitignore`.

## Easiest option: GitHub Desktop

1. Create/sign into your GitHub account and install [GitHub Desktop](https://desktop.github.com/).
2. Extract the downloaded ZIP to a permanent folder, such as `Documents\Projects\riskflow-credit-fraud`.
3. In GitHub Desktop choose **File → Add local repository** and select that folder.
4. If it says the folder is not a Git repository, click the link to **create a repository here**. Ensure the resulting path is the existing `riskflow-credit-fraud` folder, not another nested folder. Keep the included README, .gitignore and LICENSE; do not generate replacements.
5. If files appear under Changes, enter **Initial commit: credit risk and fraud analytics platform** and click **Commit to main**. Repository creation may already have made the initial commit; if Changes is empty, continue.
6. Click **Publish repository**. Use the name `riskflow-credit-fraud` and the description below. For a public portfolio, deselect **Keep this code private**. Click **Publish repository**.
7. Use **View on GitHub**. Confirm the README appears on the repository homepage with the screenshot and that code/data/Excel folders are present.
8. Open the **Actions** tab. The included workflow runs core tests on Windows/Linux and a live MySQL integration job. Check its actual result before claiming MySQL verification. If a job fails, open its log and address the displayed failure.

Suggested repository description:

> Credit risk and fraud analytics workspace with Python/SQL pipelines, analyst case review, evidence-based AI summaries, Excel reporting, and synthetic evaluation.

Suggested topics: `risk-analytics`, `credit-risk`, `fraud-detection`, `data-engineering`, `python`, `sql`, `mysql`, `excel`, `product-analytics`.

## Command-line option

Install [Git](https://git-scm.com/downloads). In PowerShell, navigate to the extracted project folder. Replace the example path with yours:

```powershell
cd "C:\Users\YOUR-NAME\Documents\Projects\riskflow-credit-fraud"
git init
git add .
git status
git commit -m "Build credit risk and fraud analytics platform"
git branch -M main
```

If Git asks for your name/email, set your identity locally for this repository, then retry the commit:

```powershell
git config user.name "Your Name"
git config user.email "YOUR-GITHUB-EMAIL-OR-NOREPLY-ADDRESS"
```

On GitHub, create a **new empty repository** named `riskflow-credit-fraud`. Leave “Add README,” .gitignore and license unchecked because the project already includes them. Copy the repository's HTTPS URL. Then run, replacing YOUR-USERNAME:

```powershell
git remote add origin https://github.com/YOUR-USERNAME/riskflow-credit-fraud.git
git push -u origin main
```

Complete Git's browser sign-in when prompted. An ordinary GitHub account password is not used for Git over HTTPS. If `origin` already exists, inspect `git remote -v` and use `git remote set-url origin YOUR-CORRECT-REPOSITORY-URL` for this project.

## Before publishing

- Run `python -m unittest discover -s tests -v` and `python -m riskflow demo` from this project folder.
- In `git status`, confirm `.env`, API keys, local `.db` files and unrelated resume/contact documents are absent.
- Synthetic `data/raw` files, report snapshots, screenshots, and the example Excel workbook are intended for publication.
- If you used your own real data or review notes, restore the synthetic demo inputs and reporting snapshots or exclude those personal files. `.gitignore` does not automatically classify CSVs as sensitive.
- If you accidentally commit a secret, remove it from history and rotate the credential; deleting the visible file alone is insufficient.

## After publishing

Pin the repository on your profile. Link it from your resume or LinkedIn Projects section. In interviews, follow `docs/DEMO_WALKTHROUGH.md` and be able to explain the scoring and limitations yourself. The project was generated with AI assistance; describe your own understanding, adaptations and work accurately.

For future changes: make and test the edit, review Changes in GitHub Desktop, commit, then **Push origin**. With the command line use `git add .`, `git commit -m "Describe the change"`, and `git push`.

GitHub hosts the repository and downloadable Excel example. GitHub Pages does not run this Python server; the dashboard is a local application unless you separately deploy a suitable backend.

Official instructions: [GitHub Desktop publishing](https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-an-existing-project-to-github-using-github-desktop), [command-line import](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).
