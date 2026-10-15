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

## Integration limits

- **OpenAI/Ollama:** adapter contracts, structured responses, refusals and fallback paths were tested with mocked provider responses. No paid API key or local language model was available for a live model call. Live use requires user configuration and checking actual generated explanations.
- **MySQL:** schema/adapter/trigger and live test job are supplied. No running MySQL/Docker service was available locally. The live backend must be verified by running the provided workflow or dedicated local test database.
- **Native Excel:** the workbook itself was generated, recalculated, exported and visually checked. Power Query connection and native PivotTable creation depend on the user's Excel installation; the helper was syntax-checked but not executed in desktop Excel. Check query refresh and formula calculation locally.
- **GitHub:** public repository created at https://github.com/DaniyalHayat/riskflow-credit-fraud. Source publication and CI results are being verified; the local checks above remain the baseline until the workflow completes.

## Interpreting the results

All data and labels are synthetic. The benchmark measures fixed illustrative rules on that generated dataset. It establishes reproducibility and visible tradeoffs, not real-world accuracy, prevented loss, analyst time saved, fairness validation or production readiness.
