# Deployment Guide for Render.com

## Prerequisites
- GitHub account
- Render account (free tier available at https://render.com)
- Your code pushed to a GitHub repository

## Step 1: Prepare Repository
Ensure all files are committed and pushed to GitHub:
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

## Step 2: Deploy on Render

### Option A: Using render.yaml (Recommended)
1. Go to https://render.com/dashboard
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Click "Apply" to create all services

### Option B: Manual Setup
1. Create PostgreSQL Database:
   - Click "New" → "PostgreSQL"
   - Name: `skyjo-db`
   - Plan: Free
   - Click "Create Database"
   - Copy the "Internal Database URL"

2. Create Web Service:
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - **Name**: skyjo-game
     - **Region**: Oregon (US West)
     - **Branch**: main
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn --config gunicorn_config.py run:app`
   
3. Add Environment Variables:
   - `FLASK_CONFIG` = `production`
   - `SECRET_KEY` = (click "Generate" for random key)
   - `DATABASE_URL` = (paste Internal Database URL from step 1)
   - `PYTHON_VERSION` = `3.11.0`

4. Click "Create Web Service"

## Step 3: Wait for Deployment
- Render will automatically build and deploy your app
- First deployment takes 5-10 minutes
- Watch the logs for any errors

## Step 4: Verify Deployment
Once deployed, your app will be available at:
- `https://skyjo-game.onrender.com` (or your chosen name)

Test the following:
- Homepage loads
- Create a game
- Join a game
- WebSocket connection works
- Database persists data

## Important Notes

### Free Tier Limitations
- Web service spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- Database limited to 1GB storage
- 750 hours/month of web service runtime

### Automatic Deployments
- Render automatically redeploys when you push to GitHub
- No manual deployment needed after initial setup

### Environment Variables
- Never commit `.env` file to GitHub
- Use Render's dashboard to manage environment variables
- SECRET_KEY should be a long random string

### Database
- PostgreSQL database is separate from web service
- Internal Database URL is only accessible from your Render services
- External Database URL can be used for remote access (but keep it secret)

### WebSocket Support
- gunicorn with eventlet worker handles WebSocket connections
- CORS is configured to allow all origins (adjust in production if needed)

### Logs
- View logs in Render dashboard under "Logs" tab
- Logs are real-time and show application output
- Useful for debugging issues

## Troubleshooting

### App won't start
- Check logs for Python/dependency errors
- Verify DATABASE_URL is correct
- Ensure FLASK_CONFIG=production

### Database connection errors
- Verify DATABASE_URL format: `postgresql://...`
- Check database is in same region as web service
- Wait for database to fully initialize

### WebSocket not connecting
- Check browser console for errors
- Verify gunicorn is using eventlet worker
- Test with simple socket.io connection

### Slow first load
- Normal for free tier (spin-down)
- Consider upgrading to paid tier for always-on

## Monitoring

### Health Check
Render automatically pings your app to keep it alive during active hours.

### Logs
Monitor application logs for:
- `[CLEANUP]` messages every 20 minutes
- WebSocket connection/disconnection events
- Database queries (in debug mode)

## Scaling

### Upgrade Options
If you need better performance:
- **Starter**: $7/month (no spin-down, more RAM)
- **Standard**: $25/month (better performance)
- **Database**: Upgrade for more storage/connections

### Horizontal Scaling
For multiple instances:
- Use external Redis for session management
- Configure load balancer
- Sync game state across instances

## Maintenance

### Database Backups
- Render takes automatic daily backups (7-day retention on free tier)
- Download backup from dashboard if needed

### Updates
Simply push to GitHub:
```bash
git add .
git commit -m "Update feature"
git push origin main
```

### Rollback
If something breaks:
- Go to Render dashboard
- Click "Manual Deploy" → Previous commit

## Security Checklist

- [x] SECRET_KEY is random and secure
- [x] DATABASE_URL is not in code
- [x] .env is in .gitignore
- [x] Debug mode is off in production
- [ ] Consider adding rate limiting
- [ ] Consider adding HTTPS-only cookies
- [ ] Consider restricting CORS origins

## Support

If you encounter issues:
- Check Render documentation: https://render.com/docs
- View Render status: https://status.render.com
- Check application logs in dashboard

---

**Your app is now live! 🎉**
