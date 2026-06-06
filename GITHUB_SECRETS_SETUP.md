# GitHub Secrets Setup - Portfolio Dashboard Azure Deployment

## 🎯 Next Steps: Add These Secrets to GitHub

Your Azure resources are created! Now add these secrets to your GitHub repository.

### How to Add Secrets

1. Go to your repository: https://github.com/vipinsindhu/portfolio-dashboard
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each item below
4. Copy the name and value exactly as shown

---

## 📋 Secrets to Add (in order)

### 1️⃣ AZURE_CREDENTIALS
**Name:** `AZURE_CREDENTIALS`  
**Value:** (Copy the entire JSON block from your azure setup output)

```json
{
    "clientId": "[from azure setup]",
    "clientSecret": "[from azure setup]",
    "subscriptionId": "[from azure setup]",
    "tenantId": "[from azure setup]",
    "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
    "resourceManagerEndpointUrl": "https://management.azure.com/",
    "activeDirectoryGraphResourceId": "https://graph.windows.net/",
    "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
    "galleryEndpointUrl": "https://gallery.azure.com/",
    "managementEndpointUrl": "https://management.core.windows.net/"
}
```

**Note:** Use the actual JSON output from `az ad sp create-for-rbac`. The values above are placeholders.

---

### 2️⃣ AZURE_RESOURCE_GROUP
**Name:** `AZURE_RESOURCE_GROUP`  
**Value:** (from azure-setup.sh output)
```
portfolio-dashboard-rg
```

---

### 3️⃣ AZURE_REGISTRY_NAME
**Name:** `AZURE_REGISTRY_NAME`  
**Value:** (from azure-setup.sh output)
```
portfoliodashboard[xxxxx]
```

---

### 4️⃣ AZURE_REGISTRY_LOGIN_SERVER
**Name:** `AZURE_REGISTRY_LOGIN_SERVER`  
**Value:** (from azure-setup.sh output)
```
portfoliodashboard[xxxxx].azurecr.io
```

---

### 5️⃣ AZURE_REGISTRY_USERNAME
**Name:** `AZURE_REGISTRY_USERNAME`  
**Value:** (from azure-setup.sh output)
```
portfoliodashboard[xxxxx]
```

---

### 6️⃣ AZURE_REGISTRY_PASSWORD
**Name:** `AZURE_REGISTRY_PASSWORD`  
**Value:** (from azure-setup.sh output)
```
[long alphanumeric string from azure setup]
```

---

### 7️⃣ ANTHROPIC_API_KEY
**Name:** `ANTHROPIC_API_KEY`  
**Value:** (Your Claude API key - keep this private!)
```
[your Anthropic API key]
```

---

## ✅ Verification Checklist

After adding all 7 secrets:

- [ ] AZURE_CREDENTIALS - JSON block from azure setup
- [ ] AZURE_RESOURCE_GROUP - From azure setup
- [ ] AZURE_REGISTRY_NAME - From azure setup
- [ ] AZURE_REGISTRY_LOGIN_SERVER - From azure setup
- [ ] AZURE_REGISTRY_USERNAME - From azure setup
- [ ] AZURE_REGISTRY_PASSWORD - From azure setup
- [ ] ANTHROPIC_API_KEY - Your Claude API key

---

## 🚀 Deployment

Once all secrets are added and the GitHub Actions workflow runs, your app will be deployed to Azure Container Instances automatically.

---

## 📊 Monitoring Deployment

1. Go to your repo → **Actions** tab
2. Watch "Deploy to Azure Container Instances" workflow
3. Once complete, check logs for your frontend URL
4. Visit the URL in your browser! 🎉

---

## 🆘 Troubleshooting

**Workflow not triggering?**
- Push a new commit to main branch
- Or manually trigger via Actions tab

**Build fails?**
- Check Docker files build locally: `docker build ./backend` and `docker build ./frontend`
- Verify Dockerfile paths are correct

**Can't access deployed app?**
- Wait 2-3 minutes after deployment completes
- Check Azure portal for container status
- Look at container logs in Azure

---

## 📞 Support

- **Azure Docs:** https://learn.microsoft.com/azure/
- **GitHub Actions:** https://docs.github.com/en/actions
- **Deployment Guide:** See `AZURE_DEPLOYMENT_GUIDE.md`

---

**Your deployment is live!** 🎉
