# Base: slim Debian to keep image small
FROM debian:bullseye-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install base system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    gnupg \
    build-essential \
    libssl-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libffi-dev \
    liblzma-dev \
    zlib1g-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    uuid-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


# ---------------------------
# Install Python 3.9.22 from source
# ---------------------------
WORKDIR /usr/src

RUN wget https://www.python.org/ftp/python/3.9.22/Python-3.9.22.tgz && \
    tar xzf Python-3.9.22.tgz && \
    cd Python-3.9.22 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall && \
    ln -s /usr/local/bin/python3.9 /usr/local/bin/python && \
    ln -s /usr/local/bin/pip3.9 /usr/local/bin/pip

# ---------------------------
# Install Node.js 22.16.0
# ---------------------------
# RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
#     apt-get install -y nodejs && \
#     node -v && npm -v
RUN curl -fsSL https://nodejs.org/dist/v22.16.0/node-v22.16.0-linux-x64.tar.xz -o node.tar.xz && \
    tar -xf node.tar.xz && \
    mv node-v22.16.0-linux-x64 /usr/local/node && \
    ln -s /usr/local/node/bin/node /usr/local/bin/node && \
    ln -s /usr/local/node/bin/npm /usr/local/bin/npm && \
    ln -s /usr/local/node/bin/npx /usr/local/bin/npx && \
    rm node.tar.xz

# ---------------------------
# Set up project
# ---------------------------
# Set work directory
WORKDIR /app

# Copy Django dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . .

# Install frontend dependencies
WORKDIR /app/UI
RUN npm install

# # Global tool for concurrent processes (optional)
# RUN npm install -g npm-run-all

# Return to root app directory
WORKDIR /app

# Copy and configure start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose ports
EXPOSE 8000 5173 3000

CMD ["/start.sh"]
