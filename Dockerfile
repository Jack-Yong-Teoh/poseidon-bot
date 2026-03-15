FROM python:3.13-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation for faster startups
ENV UV_COMPILE_BYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy only the files needed for dependency installation first (caching)
COPY pyproject.toml ./

# Install dependencies using uv (no-install-project skips installing the current folder as a package)
RUN uv sync --no-install-project --no-dev

# Copy the rest of the code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Run the bot
CMD ["uv", "run", "python", "src/bot.py"]