<#
One-time Windows Excel desktop helper. Creates a NEW connected copy.
No downloads, external uploads, or changes to the delivered baseline workbook.
Requires Microsoft Excel with Power Query / Microsoft.Mashup.OleDb.1.
#>
param(
    [string]$WorkbookPath = (Join-Path $PSScriptRoot 'RiskFlow_Analytics.xlsx'),
    [string]$ReportsPath = (Join-Path $PSScriptRoot '..\reports'),
    [string]$OutputPath = (Join-Path $PSScriptRoot 'RiskFlow_Analytics_Connected.xlsx')
)
$ErrorActionPreference = 'Stop'
$sourceFile = (Resolve-Path -LiteralPath $WorkbookPath).Path
$reportFolder = (Resolve-Path -LiteralPath $ReportsPath).Path
$destinationFile = [IO.Path]::GetFullPath($OutputPath)
if ($sourceFile -eq $destinationFile -or (Test-Path -LiteralPath $destinationFile)) {
    throw 'Choose a NEW OutputPath; this helper does not overwrite existing workbooks.'
}
foreach ($name in @('credit_assessments.csv','fraud_assessments.csv','daily_monitoring.csv','case_queue.csv')) {
    if (-not (Test-Path -LiteralPath (Join-Path $reportFolder $name))) { throw "Missing reporting feed: $name. Run python -m riskflow export first." }
}
Copy-Item -LiteralPath $sourceFile -Destination $destinationFile
$excelApp = $null
$book = $null
try {
    $excelApp = New-Object -ComObject Excel.Application
    $excelApp.Visible = $false
    $excelApp.DisplayAlerts = $false
    $book = $excelApp.Workbooks.Open($destinationFile)
    # Power Query strings double embedded quotation marks; backslashes are literal in M.
    $mPath = $reportFolder.Replace('"','""')
    $null = $book.Queries.Add('ReportsFolder', ('let Source = "{0}" in Source' -f $mPath))
    $mappings = @(
        @{Query='CreditSourceQuery'; Script='CreditSource.pq'; Sheet='Credit Source'; Table='CreditSource'},
        @{Query='FraudSourceQuery'; Script='FraudSource.pq'; Sheet='Fraud Detail'; Table='FraudSource'},
        @{Query='DailySourceQuery'; Script='DailySource.pq'; Sheet='Daily Source'; Table='DailySource'},
        @{Query='CaseSourceQuery'; Script='CaseSource.pq'; Sheet='Review Queue'; Table='CaseSource'}
    )
    foreach ($mapping in $mappings) {
        $formula = Get-Content -LiteralPath (Join-Path $PSScriptRoot ('power_query\' + $mapping.Script)) -Raw
        $null = $book.Queries.Add($mapping.Query, $formula)
        $sheet = $book.Worksheets.Item($mapping.Sheet)
        $old = $sheet.ListObjects.Item($mapping.Table)
        $oldRange = $old.Range
        $old.Unlist()
        $oldRange.Clear()
        $connection = 'OLEDB;Provider=Microsoft.Mashup.OleDb.1;Data Source=$Workbook$;Location={0};Extended Properties=""' -f $mapping.Query
        $table = $sheet.ListObjects.Add(0, $connection, $true, 1, $sheet.Range('A1'))
        $table.Name = $mapping.Table
        $table.TableStyle = 'TableStyleMedium2'
        $table.QueryTable.CommandType = 2
        $table.QueryTable.CommandText = 'SELECT * FROM [{0}]' -f $mapping.Query
        $table.QueryTable.BackgroundQuery = $false
        $null = $table.QueryTable.Refresh($false)
    }
    $excelApp.CalculateUntilAsyncQueriesDone()
    $creditSheet = $book.Worksheets.Item('Credit Source')
    $creditRows = $creditSheet.ListObjects.Item('CreditSource').ListRows.Count
    $fraudRows = $book.Worksheets.Item('Fraud Detail').ListObjects.Item('FraudSource').ListRows.Count
    $queueRows = $book.Worksheets.Item('Review Queue').ListObjects.Item('CaseSource').ListRows.Count
    $dailyRows = $book.Worksheets.Item('Daily Source').ListObjects.Item('DailySource').ListRows.Count
    if ($creditRows -lt 1 -or $fraudRows -lt 1) { throw 'Credit/fraud queries returned no usable rows.' }
    $last = $creditRows + 6
    $build = $book.Worksheets.Item('Credit Review')
    $oldLast = $build.UsedRange.Rows.Count
    if ($oldLast -gt $last) { $build.Range("A$($last+1):L$oldLast").Clear() }
    if ($creditRows -gt 1) { $build.Range('A7:L7').AutoFill($build.Range("A7:L$last"), 0) }
    $dashboard = $book.Worksheets.Item('Dashboard')
    $dashboard.Range('B7').Formula = "=SUM('Credit Review'!F7:F$last)"
    $dashboard.Range('B8').Formula = "=COUNTA('Credit Source'!A2:A$($creditRows+1))"
    $dashboard.Range('B9').Formula = "=COUNTIF('Credit Review'!K7:K$last,"">=""&Controls!B7)"
    $dashboard.Range('B10').Formula = "=COUNTA('Fraud Detail'!A2:A$($fraudRows+1))"
    $dashboard.Range('B11').Formula = "=COUNTIF('Fraud Detail'!I2:I$($fraudRows+1),"">=""&Controls!B9)"
    $queueEnd = [Math]::Max(2, $queueRows + 1)
    $dashboard.Range('B13').Formula = "=COUNTIF('Review Queue'!G2:G$queueEnd,""Open"")+COUNTIF('Review Queue'!G2:G$queueEnd,""Investigating"")+COUNTIF('Review Queue'!G2:G$queueEnd,""Escalated"")"
    for ($row = 17; $row -le 19; $row++) {
        $dashboard.Range("B$row").Formula = "=COUNTIF('Credit Review'!L7:L$last,A$row)"
        $dashboard.Range("C$row").Formula = "=SUMIF('Credit Review'!L7:L$last,A$row,'Credit Review'!F7:F$last)"
    }
    # The baseline shows three months. Preserve that display and refresh its ranges.
    for ($row = 23; $row -le 25; $row++) {
        foreach ($pair in @(@('B','B'),@('C','C'),@('D','D'))) {
            $dashboard.Range("$($pair[0])$row").Formula = "=SUMIF('Daily Source'!F2:F$($dailyRows+1),A$row,'Daily Source'!$($pair[1])2:$($pair[1])$($dailyRows+1))"
        }
    }
    $book.Worksheets.Item('Controls').Range('B28').Value2 = $reportFolder
    $excelApp.CalculateFull()
    # Add a genuine native Excel PivotTable over the pipeline's saved credit bands.
    $sourceReference = "'Credit Source'!R1C1:R$($creditRows+1)C10"
    $cache = $book.PivotCaches().Create(1, $sourceReference)
    $pivot = $cache.CreatePivotTable($dashboard.Range('A34'), 'CreditExposurePivot')
    $pivot.PivotFields('pipeline_band').Orientation = 1
    $pivot.PivotFields('pipeline_band').Position = 1
    $valueField = $pivot.AddDataField($pivot.PivotFields('exposure_usd'), 'Saved loan exposure (USD)', -4157)
    $valueField.NumberFormat = '$#,##0'
    $pivot.TableStyle2 = 'PivotStyleMedium9'
    $dashboard.Range('A32').Value2 = 'PivotTable uses saved pipeline bands; Controls affect the formula-based scenario above.'
    $book.Save()
    Write-Output "Connected workbook created: $destinationFile"
    Write-Output 'Open it in Excel. After exporting new CSVs, use Data > Refresh All.'
} catch {
    Write-Error "Excel connection failed: $($_.Exception.Message). The baseline workbook is unchanged. A copied file may remain at $destinationFile."
} finally {
    if ($book) { $book.Close($false) }
    if ($excelApp) { $excelApp.Quit() }
    if ($book) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($book) }
    if ($excelApp) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excelApp) }
}
