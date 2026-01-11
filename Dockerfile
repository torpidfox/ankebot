FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv
RUN uv pip install --system --no-cache python-telegram-bot==20.7 google-generativeai==0.3.2 genanki==0.13.1 python-dotenv==1.0.0 "pydantic>=2.0.0"

# Copy application code
COPY bot.py ./

# Set environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "bot.py"]
