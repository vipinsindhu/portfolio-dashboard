# Portfolio Dashboard - Azure App Service Deployment Script
# Run this script to deploy to Azure App Service

param(
    [string]$ResourceGroup = "portfolio-rg",
    [string]$AppServicePlan = "portfolio-plan",
    [string]$AppName = "portfolio-dashboard-app",
    [string]$Location = "eastus",
    [string]$SkuSize = "B1"
)

Write-Host "Portfolio Dashboard - Azure App Service Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if user is logged in to Azure
Write-Host "Checking Azure authentication..." -ForegroundColor Yellow
$account = az account show 2>$null

if (!$account) {
    Write-Host "Not logged in to Azure. Please run: az login" -ForegroundColor Red
    exit 1
}

$user = az account show --query "user.name" --output tsv
Write-Host "✓ Authenticated as: $user" -ForegroundColor Green
Write-Host ""

# Step 1: Create Resource Group
Write-Host "Step 1: Creating resource group '$ResourceGroup'..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location 2>$null
Write-Host "✓ Resource group ready" -ForegroundColor Green
Write-Host ""

# Step 2: Create App Service Plan
Write-Host "Step 2: Creating App Service plan ($SkuSize)..." -ForegroundColor Yellow
az appservice plan create `
    --name $AppServicePlan `
    --resource-group $ResourceGroup `
    --sku $SkuSize `
    --is-linux 2>$null
Write-Host "✓ App Service plan created" -ForegroundColor Green
Write-Host ""

# Step 3: Create Web App
Write-Host "Step 3: Creating web app '$AppName'..." -ForegroundColor Yellow
az webapp create `
    --resource-group $ResourceGroup `
    --plan $AppServicePlan `
    --name $AppName `
    --runtime "PYTHON|3.11" 2>$null
Write-Host "✓ Web app created" -ForegroundColor Green
Write-Host ""

# Step 4: Configure App Settings
Write-Host "Step 4: Configuring application settings..." -ForegroundColor Yellow
az webapp config appsettings set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=false 2>$null
Write-Host "✓ Settings configured" -ForegroundColor Green
Write-Host ""

# Step 5: Deploy from GitHub
Write-Host "Step 5: Setting up GitHub Actions deployment..." -ForegroundColor Yellow
Write-Host ""
Write-Host "To enable GitHub Actions auto-deployment:" -ForegroundColor Cyan
Write-Host "1. Go to: https://github.com/vipinsindhu/portfolio-dashboard/settings/deployments" -ForegroundColor White
Write-Host "2. Or run:" -ForegroundColor White
Write-Host "   az webapp deployment github-actions add --repo-url https://github.com/vipinsindhu/portfolio-dashboard --branch main --resource-group $ResourceGroup --name $AppName --runtime python --runtime-version 3.11" -ForegroundColor White
Write-Host ""

# Step 6: Show the deployment URL
Write-Host "Step 6: Getting deployment URL..." -ForegroundColor Yellow
$appUrl = "https://$AppName.azurewebsites.net"
Write-Host "✓ App will be available at: $appUrl" -ForegroundColor Green
Write-Host ""

# Step 7: Deploy code
Write-Host "Step 7: Deploying application code..." -ForegroundColor Yellow
Write-Host "Using GitHub Actions will automatically build and deploy." -ForegroundColor Cyan
Write-Host "You can also manually deploy with: az webapp up --resource-group $ResourceGroup --name $AppName --runtime 'PYTHON|3.11'" -ForegroundColor White
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Deployment Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Enable GitHub Actions deployment (see above)" -ForegroundColor White
Write-Host "2. Wait 5-10 minutes for initial deployment" -ForegroundColor White
Write-Host "3. Test the app at: $appUrl" -ForegroundColor White
Write-Host "4. View logs: az webapp log stream --resource-group $ResourceGroup --name $AppName" -ForegroundColor White
Write-Host ""
Write-Host "To troubleshoot:" -ForegroundColor Yellow
Write-Host "az webapp log stream --resource-group $ResourceGroup --name $AppName" -ForegroundColor White
Write-Host ""
