let
    Source = Csv.Document(File.Contents(ReportsFolder & "/fraud_assessments.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, {"baseline_cents", "amount_ratio"}),
    Typed = Table.TransformColumnTypes(Nulls, {{"transaction_id", type text}, {"customer_id", type text}, {"occurred_at", type datetime}, {"amount_usd", type number}, {"baseline_cents", type number}, {"amount_ratio", type number}, {"velocity_10m", Int64.Type}, {"repeat_10m", Int64.Type}, {"score", Int64.Type}, {"band", type text}}, "en-US"),
    Baseline = Table.AddColumn(Typed, "baseline_usd", each if [baseline_cents] = null then null else [baseline_cents] / 100, type number),
    Selected = Table.SelectColumns(Baseline, {"transaction_id", "customer_id", "occurred_at", "amount_usd", "baseline_usd", "amount_ratio", "velocity_10m", "repeat_10m", "score", "band"}),
    Sorted = Table.Sort(Selected, {{"occurred_at", Order.Ascending}, {"transaction_id", Order.Ascending}})
in
    Sorted
