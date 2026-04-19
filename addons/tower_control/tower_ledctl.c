// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
// Parts of this software were developed with the assistance of
// Claude (claude.ai), an AI assistant by Anthropic.

#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include <ws2811.h>

#define DEFAULT_LED_COUNT 8
#define MAX_LED_COUNT 1024
#define DEFAULT_LED_GPIO 18
#define DEFAULT_LED_DMA 10
#define DEFAULT_LED_BRIGHTNESS 255
#define LED_CHANNEL 0

#define STATE_DIR "/mnt/data/supervisor/share/tower_control"
#define STATE_FILE STATE_DIR "/tower_led_state.json"
#define PID_FILE   STATE_DIR "/tower_led_effect.pid"

/* runtime config, filled from env vars in main() */
static int cfg_count      = DEFAULT_LED_COUNT;
static int cfg_gpio       = DEFAULT_LED_GPIO;
static int cfg_dma        = DEFAULT_LED_DMA;
static int cfg_brightness = DEFAULT_LED_BRIGHTNESS;
static int cfg_strip_type; /* initialised in main() */

static int parse_strip_type(const char *s) {
    if (s) {
        if (strcmp(s, "RGB") == 0) return WS2811_STRIP_RGB;
        if (strcmp(s, "RBG") == 0) return WS2811_STRIP_RBG;
        if (strcmp(s, "GBR") == 0) return WS2811_STRIP_GBR;
        if (strcmp(s, "BRG") == 0) return WS2811_STRIP_BRG;
        if (strcmp(s, "BGR") == 0) return WS2811_STRIP_BGR;
    }
    return WS2811_STRIP_GRB;
}

static void read_env_config(void) {
    const char *v;
    if ((v = getenv("TOWER_LED_COUNT"))       && atoi(v) > 0)  cfg_count      = atoi(v);
    if ((v = getenv("TOWER_LED_GPIO"))       && atoi(v) >= 0) cfg_gpio       = atoi(v);
    if ((v = getenv("TOWER_LED_DMA"))        && atoi(v) >= 0) cfg_dma        = atoi(v);
    if ((v = getenv("TOWER_LED_BRIGHTNESS")) && atoi(v) >= 0) cfg_brightness = atoi(v);
    cfg_strip_type = parse_strip_type(getenv("TOWER_LED_STRIP_TYPE"));
}

typedef struct {
    int is_on;
    int r;
    int g;
    int b;
    int brightness;
    char effect[32];
} led_state_t;

static volatile sig_atomic_t keep_running = 1;

static void handle_signal(int sig) { (void)sig; keep_running = 0; }
static void ensure_dir(void) { mkdir(STATE_DIR, 0755); }

static uint8_t scale8(uint8_t v, uint8_t b) { return (uint8_t)((v * b) / 255); }

static uint32_t color_rgb(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness) {
    uint8_t sr = scale8(r, brightness);
    uint8_t sg = scale8(g, brightness);
    uint8_t sb = scale8(b, brightness);
    return ((uint32_t)sr << 16) | ((uint32_t)sg << 8) | sb;
}

static void default_state(led_state_t *st) {
    st->is_on = 0; st->r = 255; st->g = 228; st->b = 206; st->brightness = 200;
    strcpy(st->effect, "");
}

static int save_state(const led_state_t *st) {
    FILE *f = fopen(STATE_FILE, "w");
    if (!f) return -1;
    fprintf(f, "{\"is_on\":%s,\"r\":%d,\"g\":%d,\"b\":%d,\"brightness\":%d,\"effect\":\"%s\"}\n",
            st->is_on ? "true" : "false", st->r, st->g, st->b, st->brightness, st->effect);
    fclose(f);
    return 0;
}

static int load_state(led_state_t *st) {
    default_state(st);
    FILE *f = fopen(STATE_FILE, "r");
    if (!f) return -1;
    char buf[512];
    size_t n = fread(buf, 1, sizeof(buf)-1, f);
    fclose(f);
    buf[n] = 0;
    char *p;
    if (strstr(buf, "\"is_on\":true")) st->is_on = 1;
    if ((p = strstr(buf, "\"r\":"))) st->r = atoi(p + 4);
    if ((p = strstr(buf, "\"g\":"))) st->g = atoi(p + 4);
    if ((p = strstr(buf, "\"b\":"))) st->b = atoi(p + 4);
    if ((p = strstr(buf, "\"brightness\":"))) st->brightness = atoi(p + 13);
    if ((p = strstr(buf, "\"effect\":\""))) {
        p += 10;
        char *q = strchr(p, '"');
        if (q) {
            size_t len = (size_t)(q - p);
            if (len > sizeof(st->effect)-1) len = sizeof(st->effect)-1;
            memcpy(st->effect, p, len);
            st->effect[len] = 0;
        }
    }
    return 0;
}

static int read_pid(void) {
    FILE *f = fopen(PID_FILE, "r");
    if (!f) return -1;
    int pid = -1;
    fscanf(f, "%d", &pid);
    fclose(f);
    return pid;
}

static void write_pid(pid_t pid) {
    FILE *f = fopen(PID_FILE, "w");
    if (!f) return;
    fprintf(f, "%d\n", (int)pid);
    fclose(f);
}

static void stop_effect_daemon(void) {
    int pid = read_pid();
    if (pid > 0) kill(pid, SIGTERM);
    unlink(PID_FILE);
}

static ws2811_t make_ledstring(void) {
    ws2811_t ledstring;
    memset(&ledstring, 0, sizeof(ledstring));
    ledstring.freq = WS2811_TARGET_FREQ;
    ledstring.dmanum = cfg_dma;
    ledstring.channel[LED_CHANNEL].gpionum = cfg_gpio;
    ledstring.channel[LED_CHANNEL].count = cfg_count;
    ledstring.channel[LED_CHANNEL].invert = 0;
    ledstring.channel[LED_CHANNEL].brightness = cfg_brightness;
    ledstring.channel[LED_CHANNEL].strip_type = cfg_strip_type;
    ledstring.channel[1].gpionum = 0;
    ledstring.channel[1].count = 0;
    ledstring.channel[1].brightness = 0;
    return ledstring;
}

static void fill_all(ws2811_t *ledstring, uint32_t c) {
    for (int i = 0; i < cfg_count; i++) ledstring->channel[LED_CHANNEL].leds[i] = c;
}

static uint32_t wheel(uint8_t pos, uint8_t brightness) {
    pos = 255 - pos;
    if (pos < 85) return color_rgb(255 - pos * 3, 0, pos * 3, brightness);
    if (pos < 170) { pos -= 85; return color_rgb(0, pos * 3, 255 - pos * 3, brightness); }
    pos -= 170;
    return color_rgb(pos * 3, 255 - pos * 3, 0, brightness);
}

static int render_static(const led_state_t *st) {
    ws2811_t ledstring = make_ledstring();
    ws2811_return_t ret = ws2811_init(&ledstring);
    if (ret != WS2811_SUCCESS) {
        fprintf(stderr, "ws2811_init failed: %s\n", ws2811_get_return_t_str(ret));
        return 1;
    }
    if (!st->is_on) fill_all(&ledstring, 0);
    else fill_all(&ledstring, color_rgb((uint8_t)st->r, (uint8_t)st->g, (uint8_t)st->b, (uint8_t)st->brightness));
    ret = ws2811_render(&ledstring);
    if (ret != WS2811_SUCCESS) {
        fprintf(stderr, "ws2811_render failed: %s\n", ws2811_get_return_t_str(ret));
        ws2811_fini(&ledstring);
        return 1;
    }
    ws2811_fini(&ledstring);
    return 0;
}

static int run_effect_daemon(void) {
    pid_t child = fork();
    if (child < 0) return 1;
    if (child > 0) { write_pid(child); return 0; }

    setsid();
    signal(SIGTERM, handle_signal);
    signal(SIGINT, handle_signal);

    ws2811_t ledstring = make_ledstring();
    ws2811_return_t ret = ws2811_init(&ledstring);
    if (ret != WS2811_SUCCESS) {
        fprintf(stderr, "ws2811_init failed: %s\n", ws2811_get_return_t_str(ret));
        _exit(2);
    }

    int offset = 0;
    while (keep_running) {
        led_state_t st;
        load_state(&st);

        if (strcmp(st.effect, "blink_slow") == 0 || strcmp(st.effect, "blink_fast") == 0) {
            int ms = strcmp(st.effect, "blink_fast") == 0 ? 180 : 600;
            fill_all(&ledstring, color_rgb((uint8_t)st.r, (uint8_t)st.g, (uint8_t)st.b, (uint8_t)st.brightness));
            ws2811_render(&ledstring);
            usleep(ms * 1000);
            fill_all(&ledstring, 0);
            ws2811_render(&ledstring);
            usleep(ms * 1000);
            continue;
        }

        if (strcmp(st.effect, "pulse") == 0) {
            for (int i = 20; keep_running && i <= st.brightness; i += 6) {
                fill_all(&ledstring, color_rgb((uint8_t)st.r, (uint8_t)st.g, (uint8_t)st.b, (uint8_t)i));
                ws2811_render(&ledstring);
                usleep(25000);
            }
            for (int i = st.brightness; keep_running && i >= 20; i -= 6) {
                fill_all(&ledstring, color_rgb((uint8_t)st.r, (uint8_t)st.g, (uint8_t)st.b, (uint8_t)i));
                ws2811_render(&ledstring);
                usleep(25000);
            }
            continue;
        }

        if (strcmp(st.effect, "rainbow") == 0) {
            for (int i = 0; i < cfg_count; i++) {
                ledstring.channel[LED_CHANNEL].leds[i] = wheel((uint8_t)((i * 256 / cfg_count + offset) & 255), (uint8_t)st.brightness);
            }
            ws2811_render(&ledstring);
            offset = (offset + 2) & 255;
            usleep(45000);
            continue;
        }

        if (strcmp(st.effect, "fire") == 0) {
            static uint8_t heat[MAX_LED_COUNT];
            /* cool down every cell a little */
            for (int i = 0; i < cfg_count; i++) {
                int cool = (rand() % ((55 * 10) / cfg_count + 2));
                heat[i] = (uint8_t)(heat[i] > cool ? heat[i] - cool : 0);
            }
            /* heat drifts upward */
            for (int i = cfg_count - 1; i >= 2; i--)
                heat[i] = (uint8_t)((heat[i - 1] + heat[i - 2] + heat[i - 2]) / 3);
            /* random spark near bottom */
            if ((rand() % 255) < 120) {
                int y = rand() % 3;
                int add = 160 + rand() % 95;
                heat[y] = (uint8_t)(heat[y] + add > 255 ? 255 : heat[y] + add);
            }
            /* heat -> color: black->red->orange->yellow->white */
            for (int i = 0; i < cfg_count; i++) {
                uint8_t h = heat[i];
                uint8_t r, g, b;
                if (h < 85)      { r = h * 3;       g = 0;           b = 0; }
                else if (h < 170){ r = 255;          g = (h-85)*3;    b = 0; }
                else             { r = 255;          g = 255;         b = (h-170)*3; }
                ledstring.channel[LED_CHANNEL].leds[i] = color_rgb(r, g, b, (uint8_t)st.brightness);
            }
            ws2811_render(&ledstring);
            usleep(55000);
            continue;
        }

        if (strcmp(st.effect, "color_wipe") == 0) {
            /* wipe in */
            for (int i = 0; keep_running && i < cfg_count; i++) {
                ledstring.channel[LED_CHANNEL].leds[i] = color_rgb((uint8_t)st.r, (uint8_t)st.g, (uint8_t)st.b, (uint8_t)st.brightness);
                ws2811_render(&ledstring);
                usleep(80000);
            }
            usleep(300000);
            /* wipe out */
            for (int i = 0; keep_running && i < cfg_count; i++) {
                ledstring.channel[LED_CHANNEL].leds[i] = 0;
                ws2811_render(&ledstring);
                usleep(80000);
            }
            usleep(300000);
            continue;
        }

        fill_all(&ledstring, color_rgb((uint8_t)st.r, (uint8_t)st.g, (uint8_t)st.b, (uint8_t)st.brightness));
        ws2811_render(&ledstring);
        usleep(100000);
    }

    fill_all(&ledstring, 0);
    ws2811_render(&ledstring);
    ws2811_fini(&ledstring);
    unlink(PID_FILE);
    _exit(0);
}

static void usage(const char *prog) {
    fprintf(stderr, "Usage:\n");
    fprintf(stderr, "  %s off\n", prog);
    fprintf(stderr, "  %s color R G B BRIGHTNESS\n", prog);
    fprintf(stderr, "  %s effect blink_slow|blink_fast|rainbow|pulse|fire|color_wipe\n", prog);
}

int main(int argc, char **argv) {
    read_env_config();
    ensure_dir();
    if (argc < 2) { usage(argv[0]); return 2; }

    led_state_t st;
    load_state(&st);

    if (strcmp(argv[1], "off") == 0) {
        stop_effect_daemon();
        st.is_on = 0; st.r = 0; st.g = 0; st.b = 0; st.brightness = 0; strcpy(st.effect, "");
        save_state(&st);
        return render_static(&st);
    }

    if (strcmp(argv[1], "color") == 0 && argc >= 6) {
        stop_effect_daemon();
        st.is_on = 1;
        st.r = atoi(argv[2]); st.g = atoi(argv[3]); st.b = atoi(argv[4]); st.brightness = atoi(argv[5]);
        if (st.brightness < 0) st.brightness = 0;
        if (st.brightness > 255) st.brightness = 255;
        strcpy(st.effect, "");
        save_state(&st);
        return render_static(&st);
    }

    if (strcmp(argv[1], "effect") == 0 && argc >= 3) {
        const char *name = argv[2];
        if (strcmp(name, "blink_slow") && strcmp(name, "blink_fast") && strcmp(name, "rainbow") && strcmp(name, "pulse") && strcmp(name, "fire") && strcmp(name, "color_wipe")) {
            usage(argv[0]); return 2;
        }
        stop_effect_daemon();
        st.is_on = 1;
        if (st.brightness <= 0) st.brightness = 180;
        strncpy(st.effect, name, sizeof(st.effect)-1);
        st.effect[sizeof(st.effect)-1] = 0;
        save_state(&st);
        return run_effect_daemon();
    }

    usage(argv[0]);
    return 2;
}