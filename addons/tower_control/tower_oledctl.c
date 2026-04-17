// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2025-2026 David Gippner <david@gippner.eu>
// Parts of this software were developed with the assistance of
// Claude (claude.ai), an AI assistant by Anthropic.

#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#define I2C_DEV "/dev/i2c-1"
#define OLED_ADDR 0x3C
#define WIDTH 128
#define HEIGHT 64
#define PAGES 8

#include "/tmp/overpass_font.h"

static int fd = -1;
static uint8_t framebuffer[WIDTH * PAGES];

static void write_cmd(uint8_t cmd) { uint8_t b[2] = {0x00, cmd}; (void)write(fd, b, 2); }

static void oled_render(void) {
    for (int page = 0; page < PAGES; page++) {
        write_cmd(0xB0 + page); write_cmd(0x00); write_cmd(0x10);
        uint8_t buffer[WIDTH + 1];
        buffer[0] = 0x40;
        memcpy(buffer + 1, &framebuffer[page * WIDTH], WIDTH);
        (void)write(fd, buffer, WIDTH + 1);
    }
}

static void oled_init(void) {
    write_cmd(0xAE);
    write_cmd(0x20); write_cmd(0x00);
    write_cmd(0xB0); write_cmd(0xC8);
    write_cmd(0x00); write_cmd(0x10);
    write_cmd(0x40);
    write_cmd(0x81); write_cmd(0x7F);
    write_cmd(0xA1); write_cmd(0xA6);
    write_cmd(0xA8); write_cmd(0x3F);
    write_cmd(0xA4);
    write_cmd(0xD3); write_cmd(0x00);
    write_cmd(0xD5); write_cmd(0xF0);
    write_cmd(0xD9); write_cmd(0x22);
    write_cmd(0xDA); write_cmd(0x12);
    write_cmd(0xDB); write_cmd(0x20);
    write_cmd(0x8D); write_cmd(0x14);
    write_cmd(0xAF);
}

static void fb_clear(void) { memset(framebuffer, 0, sizeof(framebuffer)); }

static void set_pixel(int x, int y, int on) {
    if (x < 0 || x >= WIDTH || y < 0 || y >= HEIGHT) return;
    int page = y / 8;
    int bit = y % 8;
    uint8_t *byte = &framebuffer[page * WIDTH + x];
    if (on) *byte |= (1u << bit); else *byte &= ~(1u << bit);
}

static int next_codepoint(const char **s) {
    const unsigned char *p = (const unsigned char *)*s;
    if (*p == 0) return -1;
    if (*p < 0x80) { (*s)++; return *p; }
    if ((p[0] & 0xE0) == 0xC0 && p[1]) { int cp = ((p[0] & 0x1F) << 6) | (p[1] & 0x3F); *s += 2; return cp; }
    if ((p[0] & 0xF0) == 0xE0 && p[1] && p[2]) { int cp = ((p[0] & 0x0F) << 12) | ((p[1] & 0x3F) << 6) | (p[2] & 0x3F); *s += 3; return cp; }
    (*s)++; return ' ';
}

static int codepoint_index(const overpass_font_t *font, int cp) {
    for (int i = 0; i < font->glyph_count; i++) if ((int)font->codepoints[i] == cp) return i;
    return 0;
}

static void draw_glyph_cp(const overpass_font_t *font, int x, int baseline_y, int cp) {
    int idx = codepoint_index(font, cp);
    const overpass_glyph_t *g = &font->glyphs[idx];
    if (g->width == 0 || g->height == 0) return;
    int bytes_per_row = (g->width + 7) / 8;
    const uint8_t *data = font->bitmap + g->data_offset;
    for (int row = 0; row < g->height; row++) {
        for (int col = 0; col < g->width; col++) {
            int byte_index = row * bytes_per_row + (col / 8);
            int bit_index = 7 - (col % 8);
            int on = (data[byte_index] >> bit_index) & 1;
            if (on) set_pixel(x + col + g->xoff, baseline_y + row - g->yoff, 1);
        }
    }
}

static int text_width_px(const overpass_font_t *font, const char *text) {
    int width = 0;
    const char *p = text;
    while (*p) {
        int cp = next_codepoint(&p);
        if (cp < 0) break;
        int idx = codepoint_index(font, cp);
        width += font->glyphs[idx].width + 1;
    }
    if (width > 0) width -= 1;
    return width;
}

static int centered_baseline_for_single(const overpass_font_t *font) {
    int total_height = font->ascent + font->descent;
    int y_top = (HEIGHT - total_height) / 2;
    return y_top + font->ascent;
}

static void draw_line_centered(const overpass_font_t *font, int baseline_y, const char *text) {
    int width = text_width_px(font, text);
    int x = (WIDTH - width) / 2;
    if (x < 0) x = 0;
    const char *p = text;
    while (*p) {
        int cp = next_codepoint(&p);
        if (cp < 0) break;
        int idx = codepoint_index(font, cp);
        const overpass_glyph_t *g = &font->glyphs[idx];
        draw_glyph_cp(font, x, baseline_y, cp);
        x += g->width + 1;
        if (x >= WIDTH) break;
    }
}

static void cmd_clear(void) { fb_clear(); oled_render(); }
static void cmd_text(const char *line) { fb_clear(); int baseline = centered_baseline_for_single(&font_large); draw_line_centered(&font_large, baseline, line); oled_render(); }
static void cmd_text2(const char *line1, const char *line2) { fb_clear(); int center = centered_baseline_for_single(&font_medium); draw_line_centered(&font_medium, center - (font_medium.line_height / 2), line1); draw_line_centered(&font_medium, center + (font_medium.line_height / 2), line2); oled_render(); }
static void cmd_text3(const char *line1, const char *line2, const char *line3) { fb_clear(); int center = centered_baseline_for_single(&font_small); int step = font_small.line_height; draw_line_centered(&font_small, center - step, line1); draw_line_centered(&font_small, center, line2); draw_line_centered(&font_small, center + step, line3); oled_render(); }

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    fd = open(I2C_DEV, O_RDWR);
    if (fd < 0) { perror("I2C open"); return 1; }
    if (ioctl(fd, I2C_SLAVE, OLED_ADDR) < 0) { perror("I2C addr"); close(fd); return 1; }
    oled_init();
    if (strcmp(argv[1], "clear") == 0) cmd_clear();
    else if (strcmp(argv[1], "text") == 0 && argc >= 3) cmd_text(argv[2]);
    else if (strcmp(argv[1], "text2") == 0 && argc >= 4) cmd_text2(argv[2], argv[3]);
    else if (strcmp(argv[1], "text3") == 0 && argc >= 5) cmd_text3(argv[2], argv[3], argv[4]);
    else { close(fd); return 2; }
    close(fd);
    return 0;
}