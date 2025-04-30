# Cloudflare Deployment Guide

This guide explains how to deploy the AI Interview Preparation Platform to Cloudflare Pages.

## Prerequisites

- GitHub repository with your project code
- Cloudflare account
- PostgreSQL database (Neon, Supabase, etc.)
- Gemini API key

## Step 1: Configure Cloudflare Pages

1. Log in to your Cloudflare dashboard
2. Navigate to "Pages"
3. Click "Create a project" > "Connect to Git"
4. Select your GitHub repository
5. Configure your build settings:
   - Build command: Leave blank (we use wrangler.toml configuration)
   - Build output directory: `app/static`
   - Root directory: `/` (default)

## Step 2: Set Environment Variables

In the Cloudflare Pages dashboard, set these environment variables:

```
DATABASE_URL=postgresql://username:password@hostname:port/database_name
GEMINI_API_KEY=your_gemini_api_key
SESSION_SECRET=your_session_secret
FLASK_ENV=production
```

## Step 3: Deploy

1. Click "Save and Deploy"
2. Wait for the deployment to complete
3. Once deployed, your site will be available at `https://your-project-name.pages.dev`

## Step 4: Custom Domain (Optional)

1. In your project, go to "Custom domains"
2. Add your domain
3. Follow the DNS configuration steps

## Troubleshooting

If you encounter the `import.meta` error:
- The configuration in `wrangler.toml` has been updated to use ESM modules
- The workers-site directory has been configured to handle this error
- No additional action should be needed

If you encounter database connection issues:
- Check that your DATABASE_URL is correctly formatted
- Ensure the database is accessible from Cloudflare Workers
- Check if your database provider requires allowing Cloudflare IPs

## Maintaining Your Deployment

- Each push to your main branch will trigger a new deployment
- Environment variables can be updated in the Cloudflare dashboard
- Logs can be viewed in the Cloudflare dashboard