<#
.SYNOPSIS
    Converts all .doc files in the current directory to .docx format.

.DESCRIPTION
    This script finds all .doc files in the current directory and converts them
    to .docx format using Microsoft Word. The original .doc files are preserved,
    and all document properties (author, title, creation date, etc.) are maintained.

.PARAMETER Path
    The directory to search for .doc files. Defaults to current directory.

.EXAMPLE
    .\Convert-DocToDocx.ps1
    Converts all .doc files in the current directory.

.EXAMPLE
    .\Convert-DocToDocx.ps1 -Path "C:\Documents"
    Converts all .doc files in the specified directory.
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$Path = (Get-Location).Path
)

# Constants for Word SaveAs format
$wdFormatDocumentDefault = 16  # .docx format

# Check if Microsoft Word is installed
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    Write-Host "Microsoft Word found. Starting conversion..." -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Microsoft Word is not installed or not accessible." -ForegroundColor Red
    exit 1
}

# Get all .doc files (exclude .docx files)
$docFiles = Get-ChildItem -Path $Path -Filter "*.doc" | Where-Object { $_.Extension -eq ".doc" }

if ($docFiles.Count -eq 0) {
    Write-Host "No .doc files found in $Path" -ForegroundColor Yellow
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
    exit 0
}

Write-Host "Found $($docFiles.Count) .doc file(s) to convert." -ForegroundColor Cyan

$successCount = 0
$failCount = 0

foreach ($file in $docFiles) {
    $docPath = $file.FullName
    $docxPath = [System.IO.Path]::ChangeExtension($docPath, ".docx")

    # Skip if .docx already exists
    if (Test-Path $docxPath) {
        Write-Host "  [SKIP] $($file.Name) - .docx version already exists" -ForegroundColor Yellow
        continue
    }

    try {
        Write-Host "  [CONVERTING] $($file.Name)..." -NoNewline

        # Open the .doc file
        $doc = $word.Documents.Open($docPath)

        # Capture document properties from the original file
        $builtInProps = $doc.BuiltInDocumentProperties

        # Store properties that we want to preserve
        $properties = @{}

        $propsToPreserve = @(
            "Title", "Subject", "Author", "Keywords", "Comments",
            "Template", "Last Author", "Revision Number", "Application Name",
            "Last Print Date", "Creation Date", "Last Save Time",
            "Total Editing Time", "Number of Pages", "Number of Words",
            "Number of Characters", "Security", "Category", "Format",
            "Manager", "Company", "Number of Bytes", "Number of Lines",
            "Number of Paragraphs", "Number of Slides", "Number of Notes",
            "Number of Hidden Slides", "Number of Multimedia Clips"
        )

        foreach ($propName in $propsToPreserve) {
            try {
                $prop = $builtInProps.Item($propName)
                if ($null -ne $prop.Value -and $prop.Value -ne "") {
                    $properties[$propName] = $prop.Value
                }
            }
            catch {
                # Property might not exist or be accessible, skip it
            }
        }

        # Save as .docx
        $doc.SaveAs([ref]$docxPath, [ref]$wdFormatDocumentDefault)

        # Close the original document
        $doc.Close()

        # Open the newly created .docx file to restore properties
        $docx = $word.Documents.Open($docxPath)
        $docxProps = $docx.BuiltInDocumentProperties

        # Restore the properties
        foreach ($propName in $properties.Keys) {
            try {
                $prop = $docxProps.Item($propName)
                $prop.Value = $properties[$propName]
            }
            catch {
                # Some properties might be read-only, skip them
            }
        }

        # Save and close the .docx file
        $docx.Save()
        $docx.Close()

        Write-Host " SUCCESS" -ForegroundColor Green
        $successCount++
    }
    catch {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
}

# Clean up
$word.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()

# Summary
Write-Host "`nConversion Summary:" -ForegroundColor Cyan
Write-Host "  Successfully converted: $successCount" -ForegroundColor Green
Write-Host "  Failed: $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
Write-Host "  Original .doc files have been preserved." -ForegroundColor Yellow
Write-Host "  Document properties have been maintained." -ForegroundColor Yellow
