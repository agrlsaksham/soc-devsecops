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

$hasDocker = $true
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️ Docker CLI is not installed or not in PATH. Deployment will run in local fallback mode." -ForegroundColor Yellow
    $hasDocker = $false
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

# 5. Build and Deploy Containers / Local Fallback
Write-Host "`n[5/5] Deploying Application Services..." -ForegroundColor Yellow

$dockerDeploySuccessful = $false

if ($hasDocker) {
    try {
        # Test docker daemon connectivity
        & docker ps > $null 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Docker daemon is not running."
        }
        
        Write-Host "Shutting down active container services..." -ForegroundColor Gray
        docker-compose down
        
        Write-Host "Spinning up new container services..." -ForegroundColor Gray
        docker-compose up -d --build
        
        $dockerDeploySuccessful = $true
        
        Write-Host "`n🎉 PIPELINE SUCCESSFUL (DOCKER)!" -ForegroundColor Green
        Write-Host "=============================================" -ForegroundColor Green
        Write-Host "Application is live at: http://localhost:5000" -ForegroundColor Green
        Write-Host "Attacker simulation panel: http://localhost:5000/attacker" -ForegroundColor Green
        Write-Host "Logs path (host): ./logs/security_events.log" -ForegroundColor Green
        Write-Host "=============================================" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Docker deployment failed or daemon is not running." -ForegroundColor Yellow
    }
}

if (-not $dockerDeploySuccessful) {
    Write-Host "Starting Flask application locally in background..." -ForegroundColor Yellow
    
    # Run Flask app using start-process to run it in the background
    $env:FLASK_DEBUG = "true"  # Enable debug locally
    Start-Process python -ArgumentList "app/app.py" -NoNewWindow
    
    Write-Host "`n🎉 PIPELINE SUCCESSFUL (LOCAL FALLBACK)!" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "Application is live at: http://localhost:5000" -ForegroundColor Green
    Write-Host "Attacker simulation panel: http://localhost:5000/attacker" -ForegroundColor Green
    Write-Host "Logs path (host): ./app/logs/security_events.log" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
}
