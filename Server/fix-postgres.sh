#!/bin/bash
set -e

echo "=== PostgreSQL Authentication Troubleshooting ==="

# Step 1: Stop all containers
echo "Stopping all containers..."
docker-compose down

# Step 2: Remove PostgreSQL volume to start fresh
echo "Removing PostgreSQL data volume..."
docker volume rm server_postgres_data || true

# Step 3: Update settings.py with hardcoded credentials manually
echo "Updating Django settings.py with hardcoded credentials..."
# Find the settings.py file
SETTINGS_FILE="Server/settings.py"

if [ -f "$SETTINGS_FILE" ]; then
    # Create a backup
    cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak"
    
    # Add or replace the database settings
    cat > db_settings.tmp << 'EOL'

# Database configuration - hardcoded for Docker deployment
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'autogradepro',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db',
        'PORT': '5432',
    }
}
EOL

    # Check if DATABASES section already exists
    if grep -q "DATABASES = {" "$SETTINGS_FILE"; then
        # Replace the existing DATABASES block
        # This is a simplified approach; for complex files, a more robust method might be needed
        sed -i '/DATABASES = {/,/}/c\DATABASES = {}' "$SETTINGS_FILE"
        cat db_settings.tmp >> "$SETTINGS_FILE"
    else
        # Append to the end of the file
        cat db_settings.tmp >> "$SETTINGS_FILE"
    fi
    
    rm db_settings.tmp
    echo "Updated $SETTINGS_FILE with hardcoded database settings"
else
    echo "WARNING: Could not find settings.py at $SETTINGS_FILE"
    echo "You may need to update database settings manually"
fi

# Step 4: Start only the database container
echo "Starting PostgreSQL container..."
docker-compose up -d db

# Step 5: Wait for PostgreSQL to fully initialize
echo "Waiting for PostgreSQL to initialize (30 seconds)..."
sleep 30

# Step 6: Verify PostgreSQL is working and credentials are correct
echo "Testing PostgreSQL connection..."
docker-compose exec db psql -U postgres -c "SELECT 1 as test_connection;"

# Step 7: Create database if it doesn't exist
echo "Creating database if needed..."
docker-compose exec db psql -U postgres -c "CREATE DATABASE autogradepro WITH OWNER postgres;" || echo "Database already exists"

# Step 8: Verify database permissions
echo "Setting database permissions..."
docker-compose exec db psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';"
docker-compose exec db psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE autogradepro TO postgres;"

# Step 9: Start the web application and other services
echo "Starting remaining services..."
docker-compose up -d

echo "============================"
echo "Setup complete. Check logs for any remaining issues:"
echo "docker-compose logs web"