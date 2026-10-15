let
    Source = Csv.Document(File.Contents(ReportsFolder & "/case_queue.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"case_id", type text}, {"kind", type text}, {"customer_id", type text}, {"score", Int64.Type}, {"band", type text}, {"amount_usd", type number}, {"status", type text}, {"analyst", type text}, {"notes", type text}}, "en-US"),
    Selected = Table.SelectColumns(Typed, {"case_id", "kind", "customer_id", "score", "band", "amount_usd", "status", "analyst", "notes"})
in
    Selected
