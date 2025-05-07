FROM marketplace.gcr.io/google/ubuntu2204:latest

# Set the working directory
WORKDIR /usr/src/app

# We don't need the standalone Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV DISPLAY=:99
ENV SCREEN_RESOLUTION=1920x1000x16

# Install OS packages
RUN export DEBIAN_FRONTEND=noninteractive && apt-get update && apt-get install -yq --no-install-recommends \
    ca-certificates \
    dbus-x11 \
    fonts-liberation \
    gconf-service \
    gnupg \
    jq \
    libappindicator1 \
    libasound2 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    scrot \
    software-properties-common \
    wget \
    wget \
    x11-apps \
    x11-xkb-utils \
    x11vnc \
    xdg-utils \
    xdotool \
    xfce4 \
    xfce4-goodies \
    xfonts-100dpi \
    xfonts-75dpi \
    xfonts-scalable \
    xvfb

# Install Node.js
RUN mkdir -p /usr/local/nodejs \
    && wget -qO- https://nodejs.org/download/release/latest-v22.x/node-v22.15.0-linux-x64.tar.gz | tar xvz -C /usr/local/nodejs --strip-components=1 && \
    cp --symbolic-link /usr/local/nodejs/bin/* /usr/bin && \
    ln -s /usr/local/nodejs/include/node /usr/include/node && \
    ln -s /usr/local/nodejs/lib/node_modules /usr/lib/node_modules

# Install Chrome
RUN wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google-archive.gpg && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' && \
    apt-get update && \
    apt-get install google-chrome-stable -y --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy package.json and package-lock.json
COPY package*.json ./

# Install app dependencies
RUN npm ci

# Bundle app source code
COPY . .

# Build the typescript
RUN npm run build

# Remove dev dependencies
ENV NODE_ENV=production
RUN npm prune

# Add the run-command script to the $PATH
RUN ln -s /usr/src/app/run-command.sh /usr/bin/run-command

# Expose the port on which your app will run
EXPOSE 8080

# Start the application
ENTRYPOINT ["./entrypoint.sh"]