#!/bin/bash

# Portfolio Dashboard - Azure App Service Deployment Script
# Run this script to deploy to Azure App Service

RESOURCE_GROUP="${1:-portfolio-rg}"
APP_SERVICE_PLAN="${2:-portfolio-plan}"
APP_NAME="${3:-portfolio-dashboard-app}"
LOCATION="${4:-eastus}"
SKU_SIZE="${5:-B1}"

echo "Portfolio Dashboard - Azure App Service Deployment"
echo "=================================================="
echo ""

# Check if user is logged in to Azure
echo "Checking Azure authentication..."
if ! az account show &>/dev/null; then
    echo "Error: Not logged in to Azure. Please run: az login"
    exit 1
fi

USER=$(az account show --query "user.name" --output tsv)
echo "✓ Authenticated as: $USER"
echo ""

# Step 1: Create Resource Group
echo "Step 1: Creating resource group '$RESOURCE_GROUP'..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" > /dev/null
echo "✓ Resource group ready"
echo ""

# Step 2: Create App Service Plan
echo "Step 2: Creating App Service plan ($SKU_SIZE)..."
az appservice plan create \
    --name "$APP_SERVICE_PLAN" \
    --resource-group "$RESOURCE_GROUP" \
    --sku "$SKU_SIZE" \
    --is-linux > /dev/null
echo "✓ App Service plan created"
echo ""

# Step 3: Create Web App
echo "Step 3: Creating web app '$APP_NAME'..."
az webapp create \
    --resource-group "$RESOURCE_GROUP" \
    --plan "$APP_SERVICE_PLAN" \
    --name "$APP_NAME" \
    --runtime "PYTHON|3.11" > /dev/null
echo "✓ Web app created"
echo ""

# Step 4: Configure App Settings
echo "Step 4: Configuring application settings..."
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=false > /dev/null
echo "✓ Settings configured"
echo ""

# Step 5: Deployment info
APP_URL="https://$APP_NAME.azurewebsites.net"
echo "Step 5: Deployment Setup Complete!"
echo "✓ App will be available at: $APP_URL"
echo ""

echo "=================================================="
echo "Next steps:"
echo "1. Push code to GitHub: git push origin main"
echo "2. Enable GitHub Actions deployment:"
echo "   az webapp deployment github-actions add \\"
echo "     --repo-url https://github.com/vipinsindhu/portfolio-dashboard \\"
echo "     --branch main \\"
echo "     --resource-group $RESOURCE_GROUP \\"
echo "     --name $APP_NAME \\"
echo "     --runtime python \\"
echo "     --runtime-version 3.11"
echo ""
echo "3. Or manually deploy with:"
echo "   az webapp up --resource-group $RESOURCE_GROUP --name $APP_NAME --runtime 'PYTHON|3.11'"
echo ""
echo "4. View logs:"
echo "   az webapp log stream --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo ""
