FROM python:{{cookiecutter.max_python_version}}-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy project files
COPY pyproject.toml uv.lock ./
COPY {{cookiecutter.project_slug}}/ ./{{cookiecutter.project_slug}}/

# Install dependencies
RUN uv sync --frozen --no-cache

# Expose port
EXPOSE 8000

# Set default command
CMD ["uv", "run", "python", "-m", "{{cookiecutter.project_slug}}"]
