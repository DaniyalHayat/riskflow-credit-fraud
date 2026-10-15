let
    Source = Csv.Document(File.Contents(ReportsFolder & "/credit_assessments.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"customer_id", type text}, {"monthly_income_cents", Int64.Type}, {"monthly_debt_cents", Int64.Type}, {"revolving_balance_cents", Int64.Type}, {"revolving_limit_cents", Int64.Type}, {"days_past_due", Int64.Type}, {"late_payment_rate", type number}, {"exposure_usd", type number}, {"score", Int64.Type}, {"band", type text}}, "en-US"),
    Income = Table.AddColumn(Typed, "monthly_income_usd", each [monthly_income_cents] / 100, type number),
    Debt = Table.AddColumn(Income, "monthly_debt_usd", each [monthly_debt_cents] / 100, type number),
    Balance = Table.AddColumn(Debt, "revolving_balance_usd", each [revolving_balance_cents] / 100, type number),
    Limit = Table.AddColumn(Balance, "revolving_limit_usd", each [revolving_limit_cents] / 100, type number),
    Renamed = Table.RenameColumns(Limit, {{"score", "pipeline_score"}, {"band", "pipeline_band"}}),
    Selected = Table.SelectColumns(Renamed, {"customer_id", "monthly_income_usd", "monthly_debt_usd", "revolving_balance_usd", "revolving_limit_usd", "days_past_due", "late_payment_rate", "exposure_usd", "pipeline_score", "pipeline_band"}),
    Sorted = Table.Sort(Selected, {{"customer_id", Order.Ascending}})
in
    Sorted
