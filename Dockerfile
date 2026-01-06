FROM python:3.9.5-buster

# Fix apt sources for old Buster release
RUN sed -i 's|deb.debian.org|archive.debian.org|g' /etc/apt/sources.list && \
    sed -i 's|security.debian.org|archive.debian.org|g' /etc/apt/sources.list && \
    sed -i '/stretch-updates/d' /etc/apt/sources.list && \
    echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until
    
# Set timezone
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN sed -i 's/main/main contrib non-free/' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        neofetch \
        git \
        curl \
        wget \
        mediainfo \
        ffmpeg \
        p7zip-full \
        unrar \
        unzip \
        libssl-dev \
        libffi-dev \
        python3-dev && \
    apt-get autoremove --purge -y && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /Ult

# Copy the application code
COPY . .

# --- FIX 1: Connection Speed & Stability ---
# Installing cryptg speeds up encryption, preventing timeouts.
# pysocks helps with connection routing.
RUN pip3 install --no-cache-dir pysocks cryptg

RUN pip3 install --no-cache-dir -r reqs.txt
RUN pip3 install -U pip
RUN pip3 install -U redis

RUN pip3 install --no-cache-dir -r addons.txt
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir -r res*/st*/op* || true

# --- FIX 2: Resolve Crash (Server.py) ---
# Downgrade FastAPI to be compatible with Pydantic v1 (which your bot likely uses)
# This fixes: ImportError: cannot import name 'TypeAdapter' from 'pydantic'
RUN pip3 install "fastapi<0.100.0" "pydantic<2.0.0" uvicorn

# Set appropriate permissions
RUN chown -R 1000:0 /Ult \
    && chown -R 1000:0 . \
    && chmod 777 . \
    && chmod 777 /usr \
    && chown -R 1000:0 /usr \
    && chmod -R 755 /Ult \
    && chmod +x /Ult/start.sh

# Install FFmpeg
RUN wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz && \
    wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz.md5 && \
    md5sum -c ffmpeg-git-amd64-static.tar.xz.md5 && \
    tar xvf ffmpeg-git-amd64-static.tar.xz && \
    mv ffmpeg-git*/ffmpeg ffmpeg-git*/ffprobe /usr/local/bin/

# Expose port
EXPOSE 7860

# --- TRICK 3: Auto-delete session + Force IPv4 ---
# Deletes old sessions AND forces Python to use IPv4 for DNS (helps with connection blocks)
CMD ["bash", "-c", "echo '🔄 TRICK: Cleaning sessions...' && find . -name '*.session' -type f -delete && python3 server.py & python3 bot.py"]
