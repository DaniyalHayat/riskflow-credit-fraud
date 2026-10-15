let
    Source = Csv.Document(File.Contents(ReportsFolder & "/daily_monitoring.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"day", type date}, {"transactions", Int64.Type}, {"amount_usd", type number}, {"alerts", Int64.Type}, {"alert_rate", type number}}, "en-US"),
    Month = Table.AddColumn(Typed, "month", each Date.ToText([day], [Format="yyyy-MM", Culture="en-US"]), type text),
    Selected = Table.SelectColumns(Month, {"day", "transactions", "amount_usd", "alerts", "alert_rate", "month"}),
    Sorted = Table.Sort(Selected, {{"day", Order.Ascending}})
in
    Sorted
