// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
// Parts of this software were developed with the assistance of
// Claude (claude.ai), an AI assistant by Anthropic.

/*
 * tower_fanctl.c — temperature-based fan controller for Waveshare PI4B Mini Tower
 *
 * Daemon mode (no args): drives GPIO with software PWM based on CPU temperature.
 * Command mode:  tower_fanctl auto       — return to automatic temperature control
 *                tower_fanctl off        — stop fan (manual 0 %)
 *                tower_fanctl on         — full speed (manual 100 %)
 *                tower_fanctl <0-100>    — fixed duty cycle in percent
 *
 * State file (read/written by daemon, written by commands):
 *   /mnt/data/supervisor/share/tower_control/tower_fan_state.json
 *   {"mode":"auto","duty":45,"temp":58300,"manual_duty":-1}
 *
 * Environment variables (daemon mode, all optional):
 *   TOWER_FAN_GPIO      GPIO pin              (default: 14)
 *   TOWER_FAN_OFF_TEMP  fan-off threshold °C  (default: 40)
 *   TOWER_FAN_MIN_TEMP  ramp start °C         (default: 45)
 *   TOWER_FAN_MAX_TEMP  full speed °C         (default: 75)
 *   TOWER_FAN_MIN_DUTY  minimum duty % [1-99] (default: 25)
 *   TOWER_FAN_PWM_HZ    PWM frequency         (default: 25)
 */

#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

/* --- State file -------------------------------------------------------- */

#define STATE_DIR  "/mnt/data/supervisor/share/tower_control"
#define STATE_FILE STATE_DIR "/tower_fan_state.json"

static void ensure_dir(void) { mkdir(STATE_DIR, 0755); }

static void save_fan_state(const char *mode, int duty, long temp_mc, int manual_duty) {
    ensure_dir();
    FILE *f = fopen(STATE_FILE, "w");
    if (!f) return;
    fprintf(f, "{\"mode\":\"%s\",\"duty\":%d,\"temp\":%ld,\"manual_duty\":%d}\n",
            mode, duty, temp_mc, manual_duty);
    fclose(f);
}

static int load_manual_duty(void) {
    FILE *f = fopen(STATE_FILE, "r");
    if (!f) return -1;
    char buf[256];
    size_t n = fread(buf, 1, sizeof(buf) - 1, f);
    fclose(f);
    buf[n] = 0;
    char *p = strstr(buf, "\"manual_duty\":");
    if (!p) return -1;
    return atoi(p + 14);
}

/* --- GPIO via /dev/gpiomem -------------------------------------------- */

#define GPIO_MAP_LEN  0xB4
#define GPSET0        (0x1C / 4)
#define GPCLR0        (0x28 / 4)

static volatile uint32_t *gpio_regs;

static int gpio_open(void) {
    int fd = open("/dev/gpiomem", O_RDWR | O_SYNC);
    if (fd < 0) { perror("open /dev/gpiomem"); return -1; }
    gpio_regs = mmap(NULL, GPIO_MAP_LEN, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (gpio_regs == MAP_FAILED) { perror("mmap"); return -1; }
    return 0;
}

static void gpio_set_output(int pin) {
    int reg   = pin / 10;
    int shift = (pin % 10) * 3;
    gpio_regs[reg] = (gpio_regs[reg] & ~(7u << shift)) | (1u << shift);
}

static void gpio_write(int pin, int val) {
    if (val) gpio_regs[GPSET0] = 1u << pin;
    else     gpio_regs[GPCLR0] = 1u << pin;
}

/* --- Temperature ------------------------------------------------------- */

static long read_temp_mc(void) {
    FILE *f = fopen("/sys/class/thermal/thermal_zone0/temp", "r");
    if (!f) return 55000;
    long t = 55000;
    fscanf(f, "%ld", &t);
    fclose(f);
    return t;
}

/* --- Fan curve --------------------------------------------------------- */

static int calc_duty(long temp_mc, int prev_duty,
                     int off_c, int min_c, int max_c, int min_duty) {
    long off_mc = (long)off_c * 1000;
    long min_mc = (long)min_c * 1000;
    long max_mc = (long)max_c * 1000;

    if (temp_mc >= max_mc) return 100;

    if (temp_mc >= min_mc) {
        int d = min_duty + (int)((100 - min_duty) * (temp_mc - min_mc) / (max_mc - min_mc));
        return d;
    }

    if (temp_mc < off_mc) return 0;

    /* hysteresis zone [off_c, min_c): keep current state */
    return (prev_duty > 0) ? min_duty : 0;
}

/* --- Timing ------------------------------------------------------------ */

static void nsleep(long ns) {
    struct timespec ts = { ns / 1000000000L, ns % 1000000000L };
    nanosleep(&ts, NULL);
}

/* --- Signal handling --------------------------------------------------- */

static volatile sig_atomic_t running = 1;
static void on_signal(int s) { (void)s; running = 0; }

/* --- Main -------------------------------------------------------------- */

int main(int argc, char *argv[]) {

    /* Command mode */
    if (argc >= 2) {
        int manual_duty;
        if (strcmp(argv[1], "auto") == 0)      manual_duty = -1;
        else if (strcmp(argv[1], "off") == 0)  manual_duty = 0;
        else if (strcmp(argv[1], "on") == 0)   manual_duty = 100;
        else                                    manual_duty = atoi(argv[1]);

        if (manual_duty < -1 || manual_duty > 100) {
            fprintf(stderr, "Usage: tower_fanctl [auto|off|on|<0-100>]\n");
            return 1;
        }
        const char *mode = (manual_duty < 0) ? "auto" : "manual";
        save_fan_state(mode, manual_duty < 0 ? 0 : manual_duty, 0, manual_duty);
        fprintf(stdout, "Fan override: manual_duty=%d\n", manual_duty);
        return 0;
    }

    /* Daemon mode */
    int fan_gpio = 14;
    int off_temp = 40;
    int min_temp = 45;
    int max_temp = 75;
    int min_duty = 25;
    int pwm_hz   = 25;

    char *e;
    if ((e = getenv("TOWER_FAN_GPIO")))     fan_gpio = atoi(e);
    if ((e = getenv("TOWER_FAN_OFF_TEMP"))) off_temp = atoi(e);
    if ((e = getenv("TOWER_FAN_MIN_TEMP"))) min_temp = atoi(e);
    if ((e = getenv("TOWER_FAN_MAX_TEMP"))) max_temp = atoi(e);
    if ((e = getenv("TOWER_FAN_MIN_DUTY"))) min_duty = atoi(e);
    if ((e = getenv("TOWER_FAN_PWM_HZ")))   pwm_hz   = atoi(e);

    signal(SIGTERM, on_signal);
    signal(SIGINT,  on_signal);

    fprintf(stdout,
            "tower_fanctl: gpio=%d off=%d°C min=%d°C max=%d°C "
            "min_duty=%d%% pwm=%dHz\n",
            fan_gpio, off_temp, min_temp, max_temp, min_duty, pwm_hz);
    fflush(stdout);

    if (gpio_open() < 0) return 1;

    gpio_set_output(fan_gpio);
    gpio_write(fan_gpio, 0);

    long period_ns        = 1000000000L / pwm_hz;
    int  duty             = 0;
    int  manual_duty      = load_manual_duty();
    int  cycles_per_check = pwm_hz * 2;
    int  cycle            = cycles_per_check;
    long last_temp        = 0;

    while (running) {
        if (cycle >= cycles_per_check) {
            manual_duty = load_manual_duty();

            if (manual_duty >= 0) {
                duty = manual_duty;
                save_fan_state("manual", duty, last_temp, manual_duty);
            } else {
                last_temp = read_temp_mc();
                int new_duty = calc_duty(last_temp, duty, off_temp, min_temp, max_temp, min_duty);
                if (new_duty != duty) {
                    fprintf(stdout, "temp=%.1f°C duty=%d%%\n", last_temp / 1000.0, new_duty);
                    fflush(stdout);
                    duty = new_duty;
                }
                save_fan_state("auto", duty, last_temp, -1);
            }
            cycle = 0;
        }
        cycle++;

        if (duty <= 0) {
            gpio_write(fan_gpio, 0);
            nsleep(period_ns);
        } else if (duty >= 100) {
            gpio_write(fan_gpio, 1);
            nsleep(period_ns);
        } else {
            long on_ns  = period_ns * duty / 100;
            long off_ns = period_ns - on_ns;
            gpio_write(fan_gpio, 1);
            nsleep(on_ns);
            gpio_write(fan_gpio, 0);
            nsleep(off_ns);
        }
    }

    gpio_write(fan_gpio, 0);
    save_fan_state("auto", 0, last_temp, -1);
    munmap((void *)gpio_regs, GPIO_MAP_LEN);
    return 0;
}
