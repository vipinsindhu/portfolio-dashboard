# Deploying to Azure App Service (Python)

This guide deploys your Portfolio Dashboard to Azure App Service using native Python runtime (no Docker).

## Prerequisites

- Azure CLI installed and authenticated
- GitHub account with repository access
- Azure subscription with appropriate permissions

## Step-by-Step Deployment

### 1. Create Resource Group

```bash
az group create \
  --name portfolio-rg \
  --location eastus
```

### 2. Create App Service Plan

```bash
az appservice plan create \
  --name portfolio-plan \
  --resource-group portfolio-rg \
  --sku B1 \
  --is-linux
```

### 3. Create Web App

```bash
az webapp create \
  --resource-group portfolio-rg \
  --plan portfolio-plan \
  --name portfolio-dashboard-app \
  --runtime "PYTHON|3.11"
```

### 4. Configure Application Settings

```bash
# Set Flask environment
az webapp config appsettings set \
  --resource-group portfolio-rg \
  --name portfolio-dashboard-app \
  --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=false

# Add Anthropic API key (if needed for future features)
az webapp config appsettings set \
  --resource-group portfolio-rg \
  --name portfolio-dashboard-app \
  --settings ANTHROPIC_API_KEY="your-api-key-here"
```

### 5. Deploy from GitHub

Option A: Using GitHub Actions (Recommended)

```bash
az webapp deployment github-actions add \
  --repo-url https://github.com/vipinsindhu/portfolio-dashboard \
  --branch main \
  --resource-group portfolio-rg \
  --name portfolio-dashboard-app \
  --runtime "python" \
  --runtime-version "3.11"
```

Option B: Manual deployment

```bash
az webapp up \
  --resource-group portfolio-rg \
  --name portfolio-dashboard-app \
  --runtime "PYTHON|3.11"
```

### 6. Test the Deployment

After deployment, test the endpoints:

```bash
# Health check
curl https://portfolio-dashboard-app.azurewebsites.net/api/health

# Macro data
curl https://portfolio-dashboard-app.azurewebsites.net/api/macro

# Frontend (React)
curl https://portfolio-dashboard-app.azurewebsites.net/
```

## Monitoring

### View Logs

```bash
az webapp log stream \
  --resource-group portfolio-rg \
  --name portfolio-dashboard-app
```

### Check App Service Status

```bash
az webapp show \
  --resource-group portfolio-rg \
  --name portfolio-dashboard-app \
  --query "{ state: state, url: defaultHostName }"
```

## Troubleshooting

### Check startup logs
```bash
az webapp log download \
  --resource-group portfolio-rg \
  --name portfolio-dashboard-app \
  --log-file logs.zip
```

### SSH into the container (if needed)
```bash
az webapp remote-connection create \
  --resource-group portfolio-rg \
  --name portfolio-dashboard-app
```

## Costs

- **App Service Plan (B1)**: ~$12/month (Linux)
- **Data egress**: Minimal for internal use
- **Total estimated**: ~$12-15/month

## Next Steps

1. Push code to GitHub if not already done
2. Run the deployment commands above
3. Monitor logs during startup
4. Test all endpoints
5. Configure custom domain (optional)
6. Set up auto-scaling if needed

## GitHub Actions Auto-Deployment

Once configured, any push to `main` branch will automatically:
1. Build the application
2. Install dependencies from requirements.txt
3. Run Flask app via Gunicorn
4. Deploy to Azure App Service

No Docker layer = faster builds and simpler debugging!
