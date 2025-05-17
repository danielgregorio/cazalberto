# Cazalberto Docker Guide

Here's a quick guide on how to run Cazalberto using Docker:

## Prerequisites

- Docker installed
- Docker Compose installed
- Discord bot token

## Running the Bot

### On Windows:

1. Double-click `start-docker.bat`
2. Follow the on-screen instructions

### On Linux/Mac:

1. Make the script executable: `chmod +x start-docker.sh`
2. Run the script: `./start-docker.sh`
3. Follow the on-screen instructions

## Configuration

The bot uses the following configuration files:

- `.env` - Contains the Discord token
- `commands.json` - Stores command mappings
- `playlists.json` - Stores playlist data

## Docker Commands

- Start: `docker-compose up -d`
- Stop: `docker-compose down`
- View logs: `docker-compose logs -f`
- Restart: `docker-compose restart`

## Updating

To update to the latest version:

```
git pull
docker-compose down
docker-compose up -d --build
```

## Troubleshooting

If the bot doesn't start:

1. Check if the Docker daemon is running
2. Verify the token in the `.env` file
3. Check logs: `docker-compose logs`

For more detailed instructions, see `DOCKER.md`.
