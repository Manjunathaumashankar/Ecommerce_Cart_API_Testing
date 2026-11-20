param (
    [string]$BaseUrl = "http://127.0.0.1:5000",
    [string]$TestSuite = "",
    [string]$ReportDir = "reports\soapui",
    [string]$SoapUIPath = "C:\Program Files\SmartBear\SoapUI-5.10.0\bin\testrunner.bat"
)

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  E-Commerce Cart API - SoapUI Automated Test Runner  " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# Locate testrunner.bat
if (-not (Test-Path $SoapUIPath)) {
    if ($env:SOAPUI_HOME -and (Test-Path "$($env:SOAPUI_HOME)\bin\testrunner.bat")) {
        $SoapUIPath = "$($env:SOAPUI_HOME)\bin\testrunner.bat"
    } else {
        Write-Error "SoapUI testrunner not found at $SoapUIPath. Set SOAPUI_HOME or pass -SoapUIPath."
        exit 1
    }
}

$ProjectXml = "soapui\Ecommerce-Cart-SoapUI-Project.xml"
if (-not (Test-Path $ProjectXml)) {
    Write-Error "SoapUI project XML file not found at $ProjectXml"
    exit 1
}

# Create report directory if missing
if (-not (Test-Path $ReportDir)) {
    New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
}

$argsList = @("-r", "-a", "-j", "-f", $ReportDir, "-PbaseUrl=$BaseUrl")
if ($TestSuite) {
    $argsList += @("-s", $TestSuite)
}
$argsList += $ProjectXml

Write-Host "Runner:    $SoapUIPath" -ForegroundColor DarkGray
Write-Host "Project:   $ProjectXml" -ForegroundColor DarkGray
Write-Host "Base URL:  $BaseUrl" -ForegroundColor DarkGray
Write-Host "Reports:   $ReportDir" -ForegroundColor DarkGray
if ($TestSuite) {
    Write-Host "Suite:     $TestSuite" -ForegroundColor Yellow
}
Write-Host ""

& $SoapUIPath $argsList
$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "[SUCCESS] SoapUI Test Execution Completed with 0 Failures!" -ForegroundColor Green
} else {
    Write-Host "[FAILURE] SoapUI Test Execution Encountered Failures (Exit Code: $exitCode)" -ForegroundColor Red
}

exit $exitCode
