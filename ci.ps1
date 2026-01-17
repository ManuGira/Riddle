#!/usr/bin/env pwsh
# CI checks script - runs all checks locally

Write-Host "🚀 Running CI checks..." -ForegroundColor Cyan
Write-Host ""

$failed = $false

# Run pytest
Write-Host "▶️  Running pytest..." -ForegroundColor Yellow
uv run pytest tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ pytest failed" -ForegroundColor Red
    $failed = $true
} else {
    Write-Host "✅ pytest passed" -ForegroundColor Green
}
Write-Host ""

# Run ruff check
Write-Host "▶️  Running ruff check..." -ForegroundColor Yellow
uv run ruff check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ruff check failed" -ForegroundColor Red
    $failed = $true
} else {
    Write-Host "✅ ruff check passed" -ForegroundColor Green
}
Write-Host ""

# Run ty check on riddle
Write-Host "▶️  Running ty check on riddle..." -ForegroundColor Yellow
uv run ty check .\src\riddle\
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ty check (riddle) failed" -ForegroundColor Red
    $failed = $true
} else {
    Write-Host "✅ ty check (riddle) passed" -ForegroundColor Green
}
Write-Host ""

# Run ty check on wordle
Write-Host "▶️  Running ty check on wordle..." -ForegroundColor Yellow
uv run ty check .\src\wordle\
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ty check (wordle) failed" -ForegroundColor Red
    $failed = $true
} else {
    Write-Host "✅ ty check (wordle) passed" -ForegroundColor Green
}
Write-Host ""

# Final result
if ($failed) {
    Write-Host "❌ CI checks failed!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✅ All CI checks passed!" -ForegroundColor Green
    exit 0
}
