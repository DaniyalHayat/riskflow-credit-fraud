# Your completed RiskFlow project

This folder contains the project code, complete synthetic data, generated reports, dashboard, tests, Excel workbook and documentation. It is ready for a local demonstration.

## Run it

1. Extract the entire ZIP; do not open files from inside the ZIP.
2. Install Python 3.11+ from python.org (Windows: enable Add Python to PATH).
3. Double-click `start_windows.cmd`.
4. Visit http://127.0.0.1:8000. Keep the terminal open while using the app.
5. Open `excel/RiskFlow_Analytics.xlsx`.

If the launcher does not work, open PowerShell in this folder and run:

```powershell
python -m riskflow demo
python -m riskflow serve
```

If port 8000 is busy, run `python -m riskflow serve --port 8002` and visit http://127.0.0.1:8002. If Python is not recognized on Windows, try `py -3` or reinstall Python with Add Python to PATH selected.

## Publish it

Follow **docs/GITHUB_GUIDE.md**. The simplest route is GitHub Desktop → Add local repository → create one here if needed → Commit → Publish repository. Publish the project contents, not the ZIP alone.

## Learn it before an interview

Read README.md, then docs/DEMO_WALKTHROUGH.md. Run the tests and inspect one credit and one fraud case. The supplied resume wording is in docs/RESUME_AND_ROLE_GUIDE.md.

## Optional services

- The default works without a paid account or database installation.
- To demonstrate live AI, configure OpenAI credentials/model or install Ollama. Offline summaries are templates, not AI.
- To demonstrate MySQL, follow docs/MYSQL.md and verify the GitHub MySQL test job.
- To enable live Excel refresh/PivotTables, follow excel/README.md. Native Excel execution depends on your installed desktop version.

All customer and transaction records are synthetic. This is a portfolio demonstration with transparent limitations, not a production underwriting system.
