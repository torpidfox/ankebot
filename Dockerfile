FROM python:3.14-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files and application code
COPY pyproject.toml bot.py README.md ./

# Sync dependencies using uv (creates .venv and installs all dependencies)
RUN uv sync

# Set environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1

# Run the bot using uv (automatically uses the synced environment)
CMD ["uv", "run", "python", "bot.py"]
