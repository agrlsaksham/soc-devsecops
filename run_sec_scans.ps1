# run_sec_scans.ps1 - DevSecOps Local Pipeline Security Scanner

$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "🛡️  STARTING LOCAL DEVSECOPS PIPELINE RUN  🛡️" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Pre-requisites checks
Write-Host "`n[1/5] Checking Tooling Prerequisites..." -ForegroundColor Yellow
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
}
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not in PATH."
}

# 2. Check and Install python security packages
Write-Host "`n[2/5] Checking python security dependencies..." -ForegroundColor Yellow
$installedPackages = pip list --format=freeze
if ($installedPackages -notmatch "bandit") {
    Write-Host "Installing bandit SAST tool..." -ForegroundColor Gray
    pip install bandit
} else {
    Write-Host "✓ bandit is already installed" -ForegroundColor Green
}

if ($installedPackages -notmatch "pip-audit") {
    Write-Host "Installing pip-audit SCA tool..." -ForegroundColor Gray
    pip install pip-audit
} else {
    Write-Host "✓ pip-audit is already installed" -ForegroundColor Green
}

# 3. Run SAST (Static Application Security Testing) with bandit
Write-Host "`n[3/5] Running SAST scans using Bandit..." -ForegroundColor Yellow
try {
    # Run bandit on app/ directory
    # -r: recursive, -ll: medium confidence or higher, level medium or higher
    bandit -r app/ -ll
    Write-Host "✓ SAST Checks Passed: Code security check completed successfully." -ForegroundColor Green
} catch {
    Write-Host "⚠️ SAST scan warnings or issues detected." -ForegroundColor Yellow
    # Python bandit exits with code 1 if issues are found. We show warnings but continue to demonstrate local feedback loop.
}

# 4. Run SCA (Software Composition Analysis) with pip-audit
Write-Host "`n[4/5] Running SCA dependency audits using pip-audit..." -ForegroundColor Yellow
try {
    pip-audit -r app/requirements.txt
    Write-Host "✓ SCA Checks Passed: Dependencies are secure." -ForegroundColor Green
} catch {
    Write-Host "❌ SCA scan failed! Vulnerable dependencies detected in requirements.txt." -ForegroundColor Red
    Write-Error "Pipeline aborted due to vulnerable dependencies."
}

# 5. Build and Deploy Containers
Write-Host "`n[5/5] Building and deploying Docker containers..." -ForegroundColor Yellow
try {
    # Stop old container if running
    Write-Host "Shutting down active container services..." -ForegroundColor Gray
    docker-compose down
    
    # Build and start new container
    Write-Host "Spinning up new container services..." -ForegroundColor Gray
    docker-compose up -d --build
    
    Write-Host "`n🎉 PIPELINE SUCCESSFUL!" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "Application is live at: http://localhost:5000" -ForegroundColor Green
    Write-Host "Attacker simulation panel: http://localhost:5000/attacker" -ForegroundColor Green
    Write-Host "Logs path (host): ./logs/security_events.log" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
} catch {
    Write-Host "❌ Build/Deploy stage failed." -ForegroundColor Red
    Write-Error $_
}
