# Deploying to Railway.app

Railway is a modern deployment platform designed for simplicity. Your Portfolio Dashboard will be live in minutes.

## Prerequisites

- GitHub account (already have)
- Railway account (free tier available)
- Code pushed to GitHub (done)

## Step 1: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub (one-click)
3. Authorize Railway to access your GitHub account

## Step 2: Create New Project

1. Click "New Project" on Railway dashboard
2. Select "Deploy from GitHub repo"
3. Find and select `vipinsindhu/portfolio-dashboard`
4. Click "Deploy Now"

## Step 3: Wait for Deployment (2-3 minutes)

Railway will:
- Detect Python project from `requirements.txt`
- Install dependencies
- Start app using `Procfile` command
- Assign a public URL automatically

## Step 4: Get Your URL

After deployment completes:
1. Click on your project in Railway
2. Go to "Deployments" tab
3. Copy the public URL (looks like: `https://portfolio-dashboard-production.up.railway.app`)

## Step 5: Test Your App

Test the health endpoint:
```bash
curl https://[your-railway-url]/api/health
```

You should see:
```json
{
  "status": "ok",
  "timestamp": "2026-06-07T..."
}
```

Test macro data:
```bash
curl https://[your-railway-url]/api/macro
```

## Environment Variables (Optional)

If you need to set environment variables:
1. In Railway project settings
2. Go to "Variables" section
3. Add any needed env vars

Currently, the app doesn't need any additional environment variables.

## Monitoring & Logs

In Railway dashboard:
1. Click your project
2. Go to "Deployments" → Active deployment
3. View logs in real-time

## Auto-Deploys

Once connected to GitHub, Railway will automatically redeploy when you push to `main` branch.

## Cost

- **Free tier**: Includes $5/month credit (more than enough for this app)
- **Pay-as-you-go**: After free credits, standard rates apply
- **Typical cost**: $0-5/month for a small Python app

## Troubleshooting

### App won't start
- Check Procfile format (must be `web: <command>`)
- Check logs in Railway dashboard
- Ensure `requirements.txt` has all dependencies

### 404 errors on endpoints
- Make sure Flask app is running (check logs)
- Verify endpoint paths in Flask app
- Check that PORT environment variable is being used

### Port issues
- Railway automatically sets `$PORT` environment variable
- Procfile uses it: `--bind 0.0.0.0:$PORT`
- App listens on whatever port Railway assigns

## Next Steps

1. Go to https://railway.app and sign up
2. Create new project and connect GitHub repo
3. Wait 2-3 minutes for deployment
4. Test endpoints
5. Share your URL!

---

**That's it!** No Docker configuration, no complex CI/CD, no build environment issues. Just push code and it deploys.
