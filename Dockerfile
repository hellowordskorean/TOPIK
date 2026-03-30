# ── Synology NAS 호환 (AMD64 + ARM64 모두 지원) ──────────────
FROM python:3.11-slim

# 시스템 패키지 (FFmpeg + 나눔 폰트 포함)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-nanum \
    fonts-nanum-extra \
    fonts-dejavu-core \
    curl \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# supercronic (apt 패키지 아님 - curl로 직접 다운로드)
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64
RUN curl -fsSL "$SUPERCRONIC_URL" -o /usr/local/bin/supercronic \
    && chmod +x /usr/local/bin/supercronic

WORKDIR /app

# Python 패키지
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY *.py ./
COPY crontab ./

# 폴더 생성
RUN mkdir -p data logs output secrets assets

CMD ["supercronic", "/app/crontab"]
