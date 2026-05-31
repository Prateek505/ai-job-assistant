$source = $PSScriptRoot
$destination = Join-Path $source "JOB_AI_Project.zip"
$tempDir = Join-Path $env:TEMP "temp_job_ai_zip"

# Remove existing temp dir and zip if any
if (Test-Path $tempDir) { Remove-Item -Path $tempDir -Recurse -Force }
if (Test-Path $destination) { Remove-Item -Path $destination -Force }

# Create fresh temp directory
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy everything from source to temp
Write-Host "Copying files to temporary directory..."
Copy-Item -Path "$source\*" -Destination $tempDir -Recurse -Force

# Clean up unwanted directories
Write-Host "Cleaning up unwanted folders..."
$foldersToRemove = @(
    "$tempDir\backend\venv",
    "$tempDir\backend\__pycache__",
    "$tempDir\frontend\node_modules",
    "$tempDir\.git"
)

foreach ($folder in $foldersToRemove) {
    if (Test-Path $folder) {
        Remove-Item -Path $folder -Recurse -Force
    }
}

# Remove all __pycache__, .pytest_cache, *.db, uploads content
Get-ChildItem -Path $tempDir -Include "__pycache__", ".pytest_cache" -Recurse -Force -Directory | Remove-Item -Recurse -Force
Get-ChildItem -Path $tempDir -Include "*.db" -Recurse -Force -File | Remove-Item -Force
Get-ChildItem -Path (Join-Path $tempDir "backend\uploads") -File -ErrorAction SilentlyContinue | Remove-Item -Force

# Remove the zip itself from the temp copy
$zipInTemp = Join-Path $tempDir "JOB_AI_Project.zip"
if (Test-Path $zipInTemp) { Remove-Item -Path $zipInTemp -Force }

# Compress the temp directory
Write-Host "Creating zip archive..."
Compress-Archive -Path "$tempDir\*" -DestinationPath $destination -Force

# Clean up temp directory
Remove-Item -Path $tempDir -Recurse -Force

Write-Host "Zip successfully created at $destination"
