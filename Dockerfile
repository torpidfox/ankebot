FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv from pyproject.toml
RUN uv pip install --system --no-cache -e .

# Copy application code
COPY bot.py ./

# Set environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "bot.py"]
