"""Generate a professional thumbnail for CrowdSafe project."""
from PIL import Image, ImageDraw, ImageFont
import math
import os

W, H = 1280, 640
BG = (10, 12, 16)
ACCENT = (79, 143, 247)
ACCENT_DIM = (79, 143, 247, 30)
WHITE = (255, 255, 255)
TEXT = (209, 213, 219)
TEXT_DIM = (107, 114, 128)
PANEL = (28, 31, 38)
BORDER = (42, 45, 53)
SUCCESS = (34, 197, 94)
WARNING = (245, 158, 11)
DANGER = (239, 68, 68)
PURPLE = (124, 58, 237)

img = Image.new('RGBA', (W, H), BG + (255,))
draw = ImageDraw.Draw(img, 'RGBA')

# --- Grid background ---
for x in range(0, W, 40):
    draw.line([(x, 0), (x, H)], fill=(79, 143, 247, 8), width=1)
for y in range(0, H, 40):
    draw.line([(0, y), (W, y)], fill=(79, 143, 247, 8), width=1)

# --- Radial glow center ---
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow, 'RGBA')
cx, cy = W // 2, H // 2
for r in range(350, 0, -1):
    alpha = int(25 * (1 - r / 350))
    glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(79, 143, 247, alpha))
img = Image.alpha_composite(img, glow)
draw = ImageDraw.Draw(img, 'RGBA')

# --- Corner accents (CCTV style) ---
corner_len = 30
corner_color = (79, 143, 247, 80)
for cx, cy, dx, dy in [(20, 20, 1, 1), (W - 20, 20, -1, 1), (20, H - 20, 1, -1), (W - 20, H - 20, -1, -1)]:
    draw.line([(cx, cy), (cx + corner_len * dx, cy)], fill=corner_color, width=2)
    draw.line([(cx, cy), (cx, cy + corner_len * dy)], fill=corner_color, width=2)

# --- Load fonts ---
try:
    font_bold_large = ImageFont.truetype("segoeui.ttf", 56)
    font_bold_med = ImageFont.truetype("segoeuib.ttf", 56)
    font_regular = ImageFont.truetype("segoeui.ttf", 18)
    font_small = ImageFont.truetype("segoeui.ttf", 13)
    font_tag = ImageFont.truetype("segoeuib.ttf", 12)
    font_metric_val = ImageFont.truetype("segoeuib.ttf", 28)
    font_metric_label = ImageFont.truetype("segoeui.ttf", 11)
    font_badge = ImageFont.truetype("segoeuib.ttf", 12)
    font_dash_title = ImageFont.truetype("segoeuib.ttf", 14)
    font_risk_badge = ImageFont.truetype("segoeuib.ttf", 11)
except:
    font_bold_large = ImageFont.load_default()
    font_bold_med = font_bold_large
    font_regular = font_bold_large
    font_small = font_bold_large
    font_tag = font_bold_large
    font_metric_val = font_bold_large
    font_metric_label = font_bold_large
    font_badge = font_bold_large
    font_dash_title = font_bold_large
    font_risk_badge = font_bold_large

# ===================== LEFT SIDE =====================

left_x = 70
base_y = 160

# --- Badge: "AI-POWERED MONITORING" ---
badge_text = "  AI-POWERED MONITORING"
bb = draw.textbbox((0, 0), badge_text, font=font_badge)
bw, bh = bb[2] - bb[0] + 28, bb[3] - bb[1] + 14
bx, by = left_x, base_y
# badge background
draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=14, fill=(79, 143, 247, 25), outline=(79, 143, 247, 60))
# dot
draw.ellipse([bx + 12, by + bh // 2 - 3, bx + 18, by + bh // 2 + 3], fill=ACCENT)
draw.text((bx + 14, by + 4), badge_text, fill=ACCENT, font=font_badge)

# --- Title: "CrowdSafe" ---
ty = base_y + 50
# "Crowd" in white
draw.text((left_x, ty), "Crowd", fill=WHITE, font=font_bold_med)
crowd_bb = draw.textbbox((left_x, ty), "Crowd", font=font_bold_med)
# "Safe" in gradient (approximate with accent)
draw.text((crowd_bb[2], ty), "Safe", fill=ACCENT, font=font_bold_med)

# --- Subtitle ---
sub_y = ty + 72
subtitle = "Real-time crowd density monitoring and\nstampede prevention using computer vision\nand machine learning."
draw.multiline_text((left_x, sub_y), subtitle, fill=TEXT_DIM, font=font_regular, spacing=6)

# --- Tech tags ---
tags = ["YOLOv11s", "BoT-SORT", "DBSCAN", "Flask", "OpenCV", "Socket.IO"]
tag_x = left_x
tag_y = sub_y + 90
for tag in tags:
    tb = draw.textbbox((0, 0), tag, font=font_tag)
    tw = tb[2] - tb[0] + 22
    th = tb[3] - tb[1] + 12
    draw.rounded_rectangle([tag_x, tag_y, tag_x + tw, tag_y + th], radius=6,
                           fill=(255, 255, 255, 12), outline=(255, 255, 255, 20))
    draw.text((tag_x + 11, tag_y + 4), tag, fill=(156, 163, 175), font=font_tag)
    tag_x += tw + 8

# ===================== RIGHT SIDE: MOCK DASHBOARD =====================

panel_x, panel_y = 750, 90
panel_w, panel_h = 440, 460
r = 16

# Panel background with shadow
shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
shadow_draw = ImageDraw.Draw(shadow, 'RGBA')
for i in range(20, 0, -1):
    alpha = int(8 * (20 - i) / 20)
    shadow_draw.rounded_rectangle(
        [panel_x - i, panel_y - i + 10, panel_x + panel_w + i, panel_y + panel_h + i + 10],
        radius=r + i, fill=(0, 0, 0, alpha)
    )
img = Image.alpha_composite(img, shadow)
draw = ImageDraw.Draw(img, 'RGBA')

# Panel
draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h],
                       radius=r, fill=PANEL + (220,), outline=(255, 255, 255, 15))

# Header
hx, hy = panel_x + 24, panel_y + 22
draw.text((hx, hy), "Live Analysis", fill=TEXT, font=font_dash_title)

# Risk badge
rb_text = "CRITICAL"
rb_bb = draw.textbbox((0, 0), rb_text, font=font_risk_badge)
rb_w = rb_bb[2] - rb_bb[0] + 18
rb_h = rb_bb[3] - rb_bb[1] + 10
rb_x = panel_x + panel_w - 24 - rb_w
rb_y = hy - 2
draw.rounded_rectangle([rb_x, rb_y, rb_x + rb_w, rb_y + rb_h], radius=4,
                       fill=(239, 68, 68, 35), outline=(239, 68, 68, 80))
draw.text((rb_x + 9, rb_y + 3), rb_text, fill=DANGER, font=font_risk_badge)

# --- 4 Metric cards ---
metrics = [
    ("PEOPLE", "247", ACCENT),
    ("DENSITY", "5.8 p/m\u00b2", WARNING),
    ("RISK SCORE", "82%", DANGER),
    ("FLOW", "0.73", SUCCESS),
]

card_gap = 12
card_w = (panel_w - 48 - card_gap) // 2
card_h = 80
card_start_y = hy + 40

for i, (label, value, color) in enumerate(metrics):
    col = i % 2
    row = i // 2
    cx = hx + col * (card_w + card_gap)
    cy = card_start_y + row * (card_h + card_gap)

    draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=10,
                           fill=(255, 255, 255, 8), outline=(255, 255, 255, 12))
    draw.text((cx + 14, cy + 12), label, fill=TEXT_DIM, font=font_metric_label)
    draw.text((cx + 14, cy + 32), value, fill=color, font=font_metric_val)

# --- Risk History bar chart ---
chart_y = card_start_y + 2 * (card_h + card_gap) + 16
draw.text((hx, chart_y), "Risk History", fill=TEXT, font=font_dash_title)

bar_base_y = chart_y + 110
bar_area_h = 80
bar_w = 18
bar_gap = 6
bars = [
    (0.20, SUCCESS), (0.25, SUCCESS), (0.18, SUCCESS),
    (0.35, WARNING), (0.42, WARNING), (0.38, WARNING),
    (0.55, (249, 115, 22)), (0.60, (249, 115, 22)), (0.52, (249, 115, 22)),
    (0.70, DANGER), (0.78, DANGER), (0.85, DANGER),
    (0.90, DANGER), (0.95, DANGER), (0.82, DANGER),
]

bar_start_x = hx
for i, (pct, color) in enumerate(bars):
    bx = bar_start_x + i * (bar_w + bar_gap)
    bh = int(bar_area_h * pct)
    by_top = bar_base_y - bh
    # bar with slight transparency
    draw.rounded_rectangle([bx, by_top, bx + bar_w, bar_base_y], radius=2,
                           fill=color + (160,))

# Chart labels
draw.text((hx, bar_base_y + 6), "15 min ago", fill=(75, 85, 99), font=font_small)
label_text = "Now"
lb = draw.textbbox((0, 0), label_text, font=font_small)
draw.text((hx + len(bars) * (bar_w + bar_gap) - (lb[2] - lb[0]) - bar_gap, bar_base_y + 6),
          label_text, fill=(75, 85, 99), font=font_small)

# --- Scan line at bottom ---
for x in range(W):
    dist_from_center = abs(x - W // 2) / (W // 2)
    alpha = int(100 * (1 - dist_from_center))
    draw.point((x, H - 2), fill=(79, 143, 247, alpha))
    draw.point((x, H - 1), fill=(79, 143, 247, alpha // 2))

# ===================== SAVE =====================
out = img.convert('RGB')
out_path = os.path.join(os.path.dirname(__file__), 'thumbnail.png')
out.save(out_path, 'PNG', quality=95)
print(f"Saved: {out_path}")
print(f"Size: {os.path.getsize(out_path) // 1024} KB")
