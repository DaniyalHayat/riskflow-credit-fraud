# RiskFlow workflow walkthrough

I designed the application around the path from an incoming financial record to an auditable review decision. This walkthrough follows that path using the included synthetic snapshot.

## Start the workspace

Run `python -m riskflow demo`, then `python -m riskflow serve`. Open http://127.0.0.1:8000 and `excel/RiskFlow_Analytics.xlsx`.

## Portfolio overview

The overview contains 300 accounts and 18,219 accepted transactions. I separate outstanding loan exposure from transaction volume because they describe different financial quantities. Credit bands summarize the as-of loan snapshot; the activity chart shows fraud alerts over time.

## Credit assessment

Open `credit:C0005` from the queue. The evidence cards show debt-to-income, utilization, current days past due, and historical late payments. Expand Source records and Financial profile to inspect the inputs. I distinguish unpaid delinquency from fully paid installments that were late.

Enter an analyst name, select Investigating, and save a clearly identified synthetic review note. The decision appears in review history and creates a database audit event.

## Fraud investigation

Filter the queue to Fraud monitoring and search for `T0014426`. This case combines an amount spike, rapid activity, and repeated payments into an 85-point review score. Expand its recent source records to inspect the payment burst. The baseline uses only earlier observations; the alert remains a reason to investigate, not proof of fraud.

## Explanation and review history

Generate an Offline template summary to inspect the evidence-linked format without an AI service. For a live provider, follow [AI setup](AI_SETUP.md) and choose OpenAI or Local Ollama. I validate evidence references and numerical tokens, while leaving interpretation and decisions with the analyst.

An unchanged pipeline rerun preserves the current decision. Changed inputs or rules create a new revision and reopen the case while retaining history.

## Thresholds and Excel

Open Performance & scenarios to inspect synthetic precision, recall, false-positive rate, and workload at different cutoffs. Preview sliders do not overwrite stored rules.

In Excel, change the credit review threshold on Controls and inspect the updated Dashboard count. Restore the baseline value of 40 when finished. The [Excel guide](../excel/README.md) explains how to connect Power Query, refresh reporting feeds, and create a native PivotTable.

## Data quality

The quality view reconciles accepted counts and transaction amounts and shows five intentional defects in quarantine. Source and rule hashes identify the snapshot behind each run. I included these controls so the reports can be traced back to validated inputs.
