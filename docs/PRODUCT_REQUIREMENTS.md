# Product requirements: RiskFlow

## Problem and user

I defined the product around one user problem: a risk operations analyst needs to find financial accounts and transactions that warrant review, understand the specific evidence, and record a decision consistently. A SQL flag alone does not provide a usable investigation workflow or show the tradeoff between review volume and detection.

**Primary user:** credit/fraud analyst at a hypothetical lender or fintech. **Secondary users:** risk manager monitoring exposure, data engineer maintaining the pipeline, and product manager evaluating review friction and coverage.

## MVP objective

My MVP goal was one local workspace where an analyst can inspect a prioritized case, trace the score to financial/transaction records, and save a disposition. Support two separate risk types in one interface. Use reproducible synthetic data so the demonstration is shareable.

## User stories and acceptance criteria

| User story | Acceptance criterion | Implemented artifact |
|---|---|---|
| Review portfolio exposure | Show total outstanding loan balances and credit band distribution | Dashboard, v_portfolio_risk, Excel |
| Find a case | Filter by risk type/status, search by account/case, paginate | Review queue |
| Understand a score | Display flag values, thresholds and point contributions | Case evidence cards |
| Inspect original observations | Display repayment records or recent transactions through the flagged time | Case source records |
| Record a decision | Require analyst, valid status, and meaningful notes; save history | case_decisions |
| Preserve a review on rerun | Identical inputs/rules retain the current status | Revision hashing and integration test |
| Reassess after change | Changed input/rules/assessment produces a new revision; stale decisions are rejected | Review locking/revision check |
| Explain with AI | On-demand summary cites supplied evidence; invalid output has a visible fallback | AI adapters |
| Trust the batch | Reject defects, reconcile accepted counts/cents before commit | Validation and load reconciliation |
| Understand tradeoffs | Show precision, recall, false-positive rate and threshold volume | Benchmark and scenario view |
| Report in Excel | Open a populated workbook and refresh local CSV feeds after one-time connection | Excel workbook/helper |

## Success metrics

- **Available now:** reconciliation differences; quarantined rows by reason; measured batch runtime; case counts; simulated precision/recall/false-positive rate; record counts at different thresholds.
- **Instrumentation available:** analyst decision timestamps, status transitions and revision history.
- **Needs a user study:** active time to review a case, abandonment rate, usability error rate and perceived explanation usefulness. Decision timestamps alone cannot establish time saved because they include idle time and have no measured baseline.

## Prioritization and tradeoffs

1. Data validity and explainable evidence precede AI. An explanation of an incorrect score would reduce trust.
2. Separate credit and fraud queues preserve distinct objectives and denominators.
3. SQLite provides a setup-free first run; MySQL provides the relational deployment path without separate scoring implementations.
4. AI is on demand to avoid unnecessary calls. It cannot set scores or decide credit eligibility.
5. A small batch design is easier to reproduce than a streaming stack. It does not demonstrate production streaming throughput.

## Non-goals

Identity/background checks, production financial decisions, automated account blocking, regulated credit ratings, identity-provider authentication, cloud infrastructure, or claimed real-customer loss reduction.

## Next iteration candidates

Use a permitted public or institution-approved dataset; reserve a temporal holdout before tuning; evaluate cost-sensitive thresholds; add a calibrated credit model separately from review priorities; run analyst usability sessions; add ingestion orchestration, role-based access and production observability if deploying. These are future extensions, not completed claims.
