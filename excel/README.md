# Excel reporting

`RiskFlow_Analytics.xlsx` is a populated, usable workbook. You can open it immediately, filter tables, change thresholds and inspect the formulas. It has seven sheets: Dashboard, Controls, Credit Review, Credit Source, Fraud Detail, Daily Source and Review Queue.

- Dashboard aggregates exposure, account counts, review volumes and monthly transaction monitoring.
- Credit Review calculates DTI/utilization and each rule's score contribution from the supplied financial inputs.
- Controls contains editable credit thresholds/weights and fraud review thresholds. Fraud scores themselves are calculated in Python.
- The source/detail tables contain all 300 accounts, all 18,219 valid transactions, daily totals and case snapshots.

The saved file contains native editable charts and filterable Excel tables. It does **not** have active local file connections because your extracted folder location is unknown. The connection helper adds Power Query connections and a genuine native credit-exposure PivotTable using your local Excel installation.

## One-time automatic connection on Windows

Requires desktop Excel with Power Query (Excel 2016 or newer / Microsoft 365) and its Mashup OLE DB provider. Close this workbook in Excel first. From PowerShell in the project folder:

```powershell
python -m riskflow export
powershell -NoProfile -File .\excel\connect_excel.ps1
```

This creates **RiskFlow_Analytics_Connected.xlsx** and leaves the delivered baseline unchanged. If your local execution policy blocks unsigned scripts, review the script and use the manual connection steps below or your organization's approved script-running process. The helper does not change execution policy.

If the output already exists, the helper stops. To make a fresh connected copy after changing account counts, specify a new file:

```powershell
powershell -NoProfile -File .\excel\connect_excel.ps1 -OutputPath .\excel\RiskFlow_Analytics_New.xlsx
```

The helper imports four typed queries, resizes the credit build and dashboard ranges, and creates the PivotTable. It is supplied for your local Excel installation; it was syntax-checked but was not executed in desktop Excel during this build.

## Regular refresh

1. Save analyst decisions in the web dashboard.
2. Click **Refresh reporting feeds** in the dashboard, or run `python -m riskflow export`.
3. In the connected Excel workbook choose **Data → Refresh All** and wait for the queries/pivot to finish.
4. Check that Dashboard counts agree with the web workspace and that query errors are absent.

The formula-based credit scenarios respond to Controls. Daily fraud alert counts and the PivotTable use the last saved Python assessment bands. Changing workbook controls alone does not change those historical pipeline classifications.

## Manual Power Query connection

For desktop Excel installations without script access:

1. Save a copy of the baseline workbook.
2. Under **Data → Get Data → From Other Sources → Blank Query**, open **Advanced Editor**.
3. Paste `power_query/ReportsFolder.pq`, replace its sample path with the full path to your extracted `reports` folder, and name the query **ReportsFolder**. Choose **Only Create Connection**.
4. Add another blank query for each supplied script: CreditSource.pq, FraudSource.pq, DailySource.pq and CaseSource.pq. Use names CreditSourceQuery, FraudSourceQuery, DailySourceQuery and CaseSourceQuery.
5. To replace a source table safely, select its table, use **Table Design → Convert to Range**, then clear its old data. Use **Close & Load To → Existing Worksheet** to load the matching query at A1 on Credit Source, Fraud Detail, Daily Source or Review Queue. Do not load over an existing table.
6. Keep headers in the exact supplied order. Rename the loaded tables to CreditSource, FraudSource, DailySource and CaseSource. Credit calculations link to source rows; changing column order breaks that contract.
7. For the delivered 300-account/92-day baseline, the existing calculation and summary ranges work. If row counts change, extend Credit Review formulas and Dashboard COUNTIF/SUMIF ranges; use the automatic helper to create a new correctly resized copy if available. The monthly chart is deliberately a July–September 2026 demo; update its month labels/ranges for another period.
8. For a PivotTable: select CreditSource → **Insert → PivotTable** → new worksheet; set pipeline_band to Rows and exposure_usd to Values (Sum). Refresh it after the query data refreshes.

Mac Excel feature availability varies; use Power Query if supported, otherwise import the reporting CSVs and follow the same column/range contract. The baseline remains usable without live queries.

## Verification

The generated workbook was recalculated, formula-error scanned, rendered and visually inspected. Its 300 credit scores matched Python exactly at default settings; changing the credit review cutoff changed the summary count and was then reset. Native Excel Power Query/PivotTable execution must be verified after you connect it locally. The template has no macros.
