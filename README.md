# German Word Telegram Bot

A Telegram bot that helps you learn German words by creating Anki flashcards with example sentences and translations using Google's Gemini API.

## Features

- Receive a German word via Telegram
- Automatically generate example sentences using Gemini API
- Generate translations for the example sentences
- Create Anki flashcards with the word, example sentence, and translation
- Export all collected cards as an `.apkg` file for Anki

## Setup

### 1. Install Dependencies

#### Using uv (Recommended)

This project uses `uv` for fast dependency management:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e .

# Or sync with lockfile (if available)
uv sync
```

#### Using pip (Alternative)

```bash
pip install -r requirements.txt
```

### 2. Get API Keys

1. **Telegram Bot Token:**
   - Talk to [@BotFather](https://t.me/BotFather) on Telegram
   - Create a new bot with `/newbot`
   - Copy the bot token

2. **Gemini API Key:**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the API key

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
ANKI_DECK_NAME=German Words
ANKI_MODEL_NAME=German Word Learning
```

**Note on ALLOWED_USER_IDS:**
- Comma-separated list of Telegram user IDs that are allowed to use the bot
- If empty or not set, all users can use the bot (no restrictions)
- To find your Telegram user ID, message [@userinfobot](https://t.me/userinfobot) on Telegram
- Example: `ALLOWED_USER_IDS=123456789,987654321,555555555`

### 4. Run the Bot

```bash
python bot.py
```

## Usage

1. Start the bot: `/start`
2. Send a German word (e.g., "Haus")
3. The bot will generate:
   - An example sentence in German
   - An English translation
   - An Anki card with all the information
4. Export cards: `/export` - Downloads an `.apkg` file
5. Clear cards: `/clear` - Removes all collected cards

## Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/export` - Export all collected cards as `.apkg` file
- `/clear` - Clear all collected cards from memory

## How to Import to Anki

1. Use `/export` command to download the `.apkg` file
2. Open Anki
3. Go to File → Import
4. Select the downloaded `.apkg` file
5. The cards will be imported into your Anki collection

## Card Format

For each German word, **two cards** are generated:

1. **Direct Translation (German → English)**
   - **Front:** German word + Example sentence
   - **Back:** English translation

2. **Reversed Translation (English → German)**
   - **Front:** English translation
   - **Back:** German word + Example sentence

This bidirectional approach helps with both recognition (reading German) and production (recalling German words from English).

## Docker / Container Registry

### Local Testing with Docker

#### Building the Docker Image

To build the Docker image locally:

```bash
# Build the image with a tag
docker build -t ankebot:latest .

# Or build with a specific tag
docker build -t ankebot:v1.0.0 .
```

The build process will:
- Use Python 3.12-slim as the base image
- Install `uv` for fast dependency management
- Install all required Python packages
- Copy the bot code into the container

#### Running the Docker Container Locally

Before running, make sure you have created a `.env` file with your API keys (see [Configure Environment Variables](#3-configure-environment-variables)).

**Basic run:**
```bash
docker run --env-file .env ankebot:latest
```

**Run with custom environment variables:**
```bash
docker run \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e GEMINI_API_KEY=your_key \
  ankebot:latest
```

**Run in detached mode (background):**
```bash
docker run -d --name ankebot --env-file .env ankebot:latest
```

**View logs:**
```bash
# If running in detached mode
docker logs ankebot

# Follow logs in real-time
docker logs -f ankebot
```

**Stop the container:**
```bash
docker stop ankebot
docker rm ankebot  # Remove after stopping
```

**Run with interactive terminal (for debugging):**
```bash
docker run -it --env-file .env ankebot:latest /bin/bash
```

### GitHub Container Registry (GHCR)

The project includes a GitHub Actions workflow that automatically builds and publishes Docker images to GitHub Container Registry.

**Automatic Publishing:**
- Images are automatically published on pushes to `main`/`master` branch
- Images are tagged with branch name, SHA, and semantic version tags (if using git tags)
- Pull requests build images but don't push them

**Using the Published Image:**

```bash
# Pull the image
docker pull ghcr.io/YOUR_USERNAME/ankebot:main

# Run the container
docker run --env-file .env ghcr.io/YOUR_USERNAME/ankebot:main
```

Replace `YOUR_USERNAME` with your GitHub username and `ankebot` with your repository name.

**Manual Publishing:**

1. Authenticate with GHCR:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
   ```

2. Build and tag:
   ```bash
   docker build -t ghcr.io/YOUR_USERNAME/ankebot:latest .
   ```

3. Push:
   ```bash
   docker push ghcr.io/YOUR_USERNAME/ankebot:latest
   ```

## Development

### Dependency Management

This project uses `uv` for dependency management with `pyproject.toml`:

- `pyproject.toml` - Project metadata and dependencies
- `requirements.txt` - Still available for pip users (generated from pyproject.toml)

To add a new dependency:
```bash
uv pip install package-name
# Then update pyproject.toml manually
```

### Dependabot

This project uses [Dependabot](https://github.com/dependabot) to automatically keep dependencies up to date.

**Configured Ecosystems:**
- **Python (pip)** - Monitors `pyproject.toml` and `requirements.txt`
- **Docker** - Monitors base image updates in `Dockerfile`
- **GitHub Actions** - Monitors action versions in `.github/workflows/`

**Update Schedule:**
- Weekly on Mondays at 09:00 UTC
- Pull requests are automatically created for available updates
- Minor and patch updates are grouped together for Python dependencies

Dependabot will:
- Create pull requests for dependency updates
- Label PRs with `dependencies` and the ecosystem name
- Group minor and patch updates to reduce PR noise
- Limit open PRs to prevent overwhelming the repository

To review or adjust Dependabot settings, see `.github/dependabot.yml`.

## Notes

- Cards are stored in memory during the bot session
- Use `/export` regularly to save your cards
- The bot uses Gemini Flash model for generating sentences and translations
