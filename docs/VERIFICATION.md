# Build verification

Built and checked on October 14, 2026. Business snapshot: September 30, 2026. Runtime timestamps are UTC; business dates are fixed for reproducibility.

## Completed local checks

- Executed the complete generator → validation → transactional SQLite pipeline → evaluation → reporting export on the delivered seed-42 dataset.
- Reconciled 300 customers, 300 loans, 900 payment observations, and 18,219 valid transactions; quarantined five intentional transaction defects.
- Ran the automated suite: **33 passed; 1 skipped**. The skipped check is the live MySQL integration test, which is enabled by the included MySQL CI job.
- Ran real loopback HTTP integration checks against an isolated database: overview, request protections, saved decisions/audit, offline summary, threshold preview and export allowlist.
- Used the dashboard in a browser: overview, queue navigation, credit evidence, saved Investigating decision/history, offline summary, benchmark/scenario view and data quality. Screenshots are in docs/images.
- Recalculated the Excel workbook with the artifact engine; scanned for formula errors; compared all 300 default credit scores to Python; changed the credit threshold and confirmed the summary count changed; restored it.
- Rendered and visually inspected all seven workbook sheets. Verified the exposure/monthly-monitoring charts and exported file contents.
- Syntax-checked Python, dashboard JavaScript and the Windows Excel connection helper.

## Publication checks

- Verified the repository contains all files in the checksummed inventory, with no extra published files.
- Checked all README local links and image targets. Captured the main application views and all seven Excel sheets, including a flagged transaction excerpt.
- Regenerated all six raw input files and four reporting exports in an isolated in-memory database; all matched the delivered files byte for byte, confirming their synthetic origin.

## Integration limits

- **OpenAI/Ollama:** adapter contracts, structured responses, refusals and fallback paths were tested with mocked provider responses. No paid API key or local language model was available for a live model call. Live use requires user configuration and checking actual generated explanations.
- **MySQL:** the live MySQL 8.4 integration job passed in GitHub Actions, exercising generation, pipeline, saved review, native audit trigger, rerun persistence, evaluation and reporting export. No local MySQL service was used.
- **Native Excel:** the workbook itself was generated, recalculated, exported and visually checked. Power Query connection and native PivotTable creation depend on the user's Excel installation; the helper was syntax-checked but not executed in desktop Excel. Check query refresh and formula calculation locally.
- **GitHub:** all project files were published and matched local file bytes. [Workflow run 38668738260](https://github.com/DaniyalHayat/riskflow-credit-fraud/actions/runs/38668738260) passed all five jobs on commit `cf370e6d1cafcf01c1e2f0b5748e9fffbd1b0bb8`: Python 3.11/3.12 on Ubuntu and Windows, plus live MySQL 8.4. Subsequent guide/verification edits do not change runtime code.

## Interpreting the results

All data and labels are synthetic. The benchmark measures fixed illustrative rules on that generated dataset. It establishes reproducibility and visible tradeoffs, not real-world accuracy, prevented loss, analyst time saved, fairness validation or production readiness.
