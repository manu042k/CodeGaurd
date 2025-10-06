# OAuth Setup Guide

## GitHub OAuth App Configuration

To fix the "redirect URI mismatch" error, you need to properly configure your GitHub OAuth app:

### 1. Create or Update GitHub OAuth App

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Either create a new OAuth app or edit your existing one
3. Set the following values:

**For Development:**
- Application name: `CodeGuard Development`
- Homepage URL: `http://localhost:3000`
- Authorization callback URL: `http://localhost:3000/api/auth/callback/github`

**For Production:**
- Application name: `CodeGuard`
- Homepage URL: `https://yourdomain.com`
- Authorization callback URL: `https://yourdomain.com/api/auth/callback/github`

### 2. Environment Variables

1. Copy `.env.example` to `.env.local`:
   ```bash
   cp .env.example .env.local
   ```

2. Update `.env.local` with your GitHub OAuth app credentials:
   ```env
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=your-random-secret-string-here
   GITHUB_CLIENT_ID=your-github-client-id
   GITHUB_CLIENT_SECRET=your-github-client-secret
   ```

### 3. Generate NEXTAUTH_SECRET

Generate a secure random string for `NEXTAUTH_SECRET`:

```bash
openssl rand -base64 32
```

### 4. Important Notes

- The callback URL MUST match exactly what's configured in your GitHub OAuth app
- For development, use `http://localhost:3000/api/auth/callback/github`
- For production, use `https://yourdomain.com/api/auth/callback/github`
- Make sure port 3000 is correct for your development setup

### 5. Restart Development Server

After updating environment variables:
```bash
npm run dev
```

## Troubleshooting

### "redirect_uri_mismatch" Error
- Check that the callback URL in GitHub OAuth app matches exactly
- Ensure no trailing slashes in URLs
- Verify the port number matches your development server

### "OAuth callback was not verified" Error
- Check NEXTAUTH_SECRET is set and properly generated
- Verify NEXTAUTH_URL matches your current domain/port

### "Access denied" Error
- Make sure your GitHub account has access to the OAuth app
- Check if the app is configured for the correct organization (if applicable)
