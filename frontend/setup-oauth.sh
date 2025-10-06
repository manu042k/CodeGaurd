#!/bin/bash

# CodeGuard Frontend OAuth Setup Script

echo "🔐 CodeGuard OAuth Configuration Setup"
echo "======================================"

# Check if .env.local exists
if [ -f .env.local ]; then
    echo "⚠️  .env.local already exists. Creating backup..."
    cp .env.local .env.local.backup
    echo "✅ Backup created as .env.local.backup"
fi

# Copy .env.example to .env.local
if [ -f .env.example ]; then
    cp .env.example .env.local
    echo "✅ Created .env.local from .env.example"
else
    echo "❌ .env.example not found. Creating from template..."
    cat > .env.local << 'EOF'
# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=

# GitHub OAuth Configuration
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
EOF
    echo "✅ Created .env.local template"
fi

# Generate NEXTAUTH_SECRET
echo ""
echo "🔑 Generating NEXTAUTH_SECRET..."
if command -v openssl >/dev/null 2>&1; then
    SECRET=$(openssl rand -base64 32)
    # Update NEXTAUTH_SECRET in .env.local
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/NEXTAUTH_SECRET=.*/NEXTAUTH_SECRET=${SECRET}/" .env.local
    else
        # Linux
        sed -i "s/NEXTAUTH_SECRET=.*/NEXTAUTH_SECRET=${SECRET}/" .env.local
    fi
    echo "✅ Generated and set NEXTAUTH_SECRET"
else
    echo "⚠️  openssl not found. Please manually generate a random string for NEXTAUTH_SECRET"
fi

echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Go to GitHub Settings → Developer settings → OAuth Apps"
echo "2. Create a new OAuth App with these settings:"
echo "   - Application name: CodeGuard Development"
echo "   - Homepage URL: http://localhost:3000"
echo "   - Authorization callback URL: http://localhost:3000/api/auth/callback/github"
echo ""
echo "3. Copy your Client ID and Client Secret to .env.local:"
echo "   - GITHUB_CLIENT_ID=your_client_id_here"
echo "   - GITHUB_CLIENT_SECRET=your_client_secret_here"
echo ""
echo "4. Start the development server:"
echo "   npm run dev"
echo ""
echo "🔗 For detailed instructions, see: OAUTH_SETUP.md"
echo ""
echo "✅ Setup complete! Don't forget to add your GitHub OAuth credentials."
