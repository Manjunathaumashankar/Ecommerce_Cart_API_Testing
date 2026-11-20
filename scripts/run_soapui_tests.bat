@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo   E-Commerce Shopping Cart API - SoapUI Test Runner
echo =======================================================

:: Define default SoapUI locations
set "SOAPUI_RUNNER=C:\Program Files\SmartBear\SoapUI-5.10.0\bin\testrunner.bat"
if not exist "!SOAPUI_RUNNER!" (
    if defined SOAPUI_HOME (
        set "SOAPUI_RUNNER=%SOAPUI_HOME%\bin\testrunner.bat"
    )
)

if not exist "!SOAPUI_RUNNER!" (
    echo [ERROR] SoapUI testrunner.bat not found!
    echo Please install SoapUI or set SOAPUI_HOME environment variable.
    exit /b 1
)

set "PROJECT_XML=soapui\Ecommerce-Cart-SoapUI-Project.xml"
set "REPORT_DIR=reports\soapui"

if not exist "!REPORT_DIR!" mkdir "!REPORT_DIR!"

echo SoapUI Runner: "!SOAPUI_RUNNER!"
echo Project XML:   "!PROJECT_XML!"
echo Report Folder: "!REPORT_DIR!"
echo.

:: Execute SoapUI CLI testrunner
"!SOAPUI_RUNNER!" -r -a -j -f "!REPORT_DIR!" "!PROJECT_XML!"

set TEST_EXIT_CODE=%ERRORLEVEL%
echo.
if %TEST_EXIT_CODE% equ 0 (
    echo [SUCCESS] All SoapUI TestSuites passed successfully!
) else (
    echo [FAILURE] SoapUI tests failed with exit code %TEST_EXIT_CODE%.
)

exit /b %TEST_EXIT_CODE%
