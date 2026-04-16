ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base:latest
FROM ${BUILD_FROM}

RUN apk add --no-cache \
    build-base \
    linux-headers \
    python3 \
    py3-pillow \
    freetype-dev \
    jpeg-dev \
    zlib-dev \
    git \
    scons

# Overpass Font
RUN git clone https://github.com/RedHatOfficial/Overpass.git /tmp/overpass

RUN find /tmp/overpass -name "*.ttf" 2>/dev/null || true

COPY gen_overpass_font.py /tmp/gen_overpass_font.py

RUN python3 /tmp/gen_overpass_font.py \
    --font "/tmp/overpass/fonts/ttf/Overpass-SemiBold.ttf" \
    --output /tmp/overpass_font.h

# OLED
COPY tower_oledctl.c /tmp/tower_oledctl.c

RUN cc -O2 -static -o /usr/local/bin/tower_oledctl \
    /tmp/tower_oledctl.c -lm

# WS2812 Library
RUN git clone https://github.com/jgarff/rpi_ws281x.git /tmp/rpi_ws281x && \
    cd /tmp/rpi_ws281x && \
    scons && \
    mkdir -p /usr/local/lib && \
    cp libws2811.a /usr/local/lib/libws2811.a

# LED
COPY tower_ledctl.c /tmp/tower_ledctl.c

RUN cc -O2 -static -o /usr/local/bin/tower_ledctl \
    -I/tmp/rpi_ws281x \
    /tmp/tower_ledctl.c \
    /usr/local/lib/libws2811.a \
    -lm -pthread

# Runtime
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
