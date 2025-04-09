#!/bin/bash
set -e

# AutoGrader Deployment Script
echo "Starting AutoGrader deployment on AWS EC2..."

# Update system packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker and Docker Compose
echo "Installing Docker and Docker Compose..."
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add current user to docker group to avoid using sudo
sudo usermod -aG docker $USER
echo "You may need to log out and back in for docker group changes to take effect"

# Create environment variables file if not exists
if [ ! -f .env ]; then
    echo "Creating environment variables file..."
    cat > .env << 'EOL'
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_EC2_IP
EOL
    echo "Please edit the .env file and replace 'YOUR_EC2_IP' with your actual EC2 IP address"
fi

# Make setup-ollama-models.sh executable
chmod +x setup-ollama-models.sh

# Create necessary directories if they don't exist
mkdir -p static media submissions

# Pull the Ollama model in advance
echo "Pulling Ollama model (this may take some time)..."
docker pull ollama/ollama:latest
docker run --rm -d --name ollama-temp ollama/ollama
sleep 10  # Wait for Ollama to start
docker exec ollama-temp ollama pull qwen2.5:1.5b
docker stop ollama-temp

echo "Starting the application..."
docker-compose up -d

echo "Running initial database migrations..."
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput

echo "Deployment complete! The application should be running at http://YOUR_EC2_IP"
echo "Please allow a few minutes for the application to fully initialize."