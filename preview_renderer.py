import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from skin_presets_manager import DEFAULT_SKIN_COLORS

FONT_MAP = {
    "meiryo ui": r"C:\Windows\Fonts\meiryo.ttc",
    "meiryo": r"C:\Windows\Fonts\meiryo.ttc",
    "yu gothic ui": r"C:\Windows\Fonts\YuGothM.ttc",
    "yu gothic": r"C:\Windows\Fonts\YuGothM.ttc",
    "ms gothic": r"C:\Windows\Fonts\msgothic.ttc",
    "arial": r"C:\Windows\Fonts\arial.ttf",
    "impact": r"C:\Windows\Fonts\impact.ttf",
    "consolas": r"C:\Windows\Fonts\lucon.ttf"
}

LATIN_ONLY_FONTS = {"arial", "impact", "consolas"}

def get_font(font_family, size, bold=False):
    key = str(font_family).lower().strip()
    path = FONT_MAP.get(key)
    if not path or not os.path.exists(path):
        path = r"C:\Windows\Fonts\meiryo.ttc"
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def get_japanese_font(size, bold=True):
    path = r"C:\Windows\Fonts\meiryo.ttc"
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def get_sub_font(font_family, size, bold=True):
    key = str(font_family).lower().strip()
    if key in LATIN_ONLY_FONTS:
        return get_japanese_font(size, bold=bold)
    return get_font(font_family, size, bold=bold)

def hex_to_rgb(hex_str, default=(255, 255, 255), alpha=255):
    if not hex_str or not isinstance(hex_str, str) or not hex_str.startswith("#"):
        return default if len(default) == 4 else (*default[:3], alpha)
    try:
        h = hex_str.lstrip("#")
        if len(h) == 6:
            r = int(h[0:2], 16)
            g = int(h[2:4], 16)
            b = int(h[4:6], 16)
            return (r, g, b, alpha)
        elif len(h) == 3:
            r = int(h[0]*2, 16)
            g = int(h[1]*2, 16)
            b = int(h[2]*2, 16)
            return (r, g, b, alpha)
    except Exception:
        pass
    return default if len(default) == 4 else (*default[:3], alpha)

def draw_dashed_rounded_rect(draw, bbox, radius, color, width=2, dash_len=5, gap_len=3):
    x0, y0, x1, y1 = bbox
    curr_x = x0 + radius
    while curr_x < x1 - radius:
        next_x = min(curr_x + dash_len, x1 - radius)
        draw.line([(curr_x, y0), (next_x, y0)], fill=color, width=width)
        curr_x += dash_len + gap_len
    curr_x = x0 + radius
    while curr_x < x1 - radius:
        next_x = min(curr_x + dash_len, x1 - radius)
        draw.line([(curr_x, y1), (next_x, y1)], fill=color, width=width)
        curr_x += dash_len + gap_len
    curr_y = y0 + radius
    while curr_y < y1 - radius:
        next_y = min(curr_y + dash_len, y1 - radius)
        draw.line([(x0, curr_y), (x0, next_y)], fill=color, width=width)
        curr_y += dash_len + gap_len
    curr_y = y0 + radius
    while curr_y < y1 - radius:
        next_y = min(curr_y + dash_len, y1 - radius)
        draw.line([(x1, curr_y), (x1, next_y)], fill=color, width=width)
        curr_y += dash_len + gap_len
    draw.arc([x0, y0, x0 + radius * 2, y0 + radius * 2], 180, 270, fill=color, width=width)
    draw.arc([x1 - radius * 2, y0, x1, y0 + radius * 2], 270, 360, fill=color, width=width)
    draw.arc([x1 - radius * 2, y1 - radius * 2, x1, y1], 0, 90, fill=color, width=width)
    draw.arc([x0, y1 - radius * 2, x0 + radius * 2, y1], 90, 180, fill=color, width=width)

def render_preview(skin="glassmorphism", wins=0, losses=0, font_family="Meiryo UI", font_size=58, width=480, height=116, colors=None):
    # OBS配信画面再現背景
    img = Image.new("RGBA", (width, height), (16, 20, 26, 255))
    draw = ImageDraw.Draw(img)
    
    cs = 12
    for y in range(0, height, cs):
        for x in range(0, width, cs):
            if (x // cs + y // cs) % 2 == 1:
                draw.rectangle([x, y, min(x + cs, width), min(y + cs, height)], fill=(22, 28, 36, 255))

    cx = width // 2
    cy = height // 2

    base_fsize = max(20, min(34, int(font_size * 0.44)))
    sub_fsize = max(11, int(base_fsize * 0.58))
    
    font_main = get_font(font_family, base_fsize, bold=True)
    font_sub = get_sub_font(font_family, sub_fsize, bold=True)
    font_header = get_font(font_family, 10, bold=True)
    font_fixed_label = get_japanese_font(10, bold=False)

    # 配色のマージ
    cfg_colors = dict(DEFAULT_SKIN_COLORS.get(skin, {}))
    if colors and isinstance(colors, dict):
        cfg_colors.update(colors)

    if skin == "glassmorphism":
        # 1. グラスモーフィズム HUD
        cw, ch = 250, 78
        x0, y0 = cx - cw // 2, cy - ch // 2
        x1, y1 = cx + cw // 2, cy + ch // 2
        radius = 34

        col_bg = hex_to_rgb(cfg_colors.get("bg", "#16211B"), default=(22, 33, 27), alpha=185)
        col_border = hex_to_rgb(cfg_colors.get("border", "#84C4A0"), default=(132, 196, 160))
        col_win = hex_to_rgb(cfg_colors.get("win", "#72EAA5"), default=(114, 234, 165))
        col_loss = hex_to_rgb(cfg_colors.get("loss", "#FFA599"), default=(255, 165, 153))

        # 外側ネオングロー層
        glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow_layer)
        gdraw.rounded_rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], radius=radius + 2,
                                fill=(col_border[0], col_border[1], col_border[2], 65))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(6))
        img = Image.alpha_composite(img, glow_layer)

        # カード本体層
        card_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cdraw = ImageDraw.Draw(card_layer)
        cdraw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=col_bg,
                                outline=(col_border[0], col_border[1], col_border[2], 140), width=2)
        img = Image.alpha_composite(img, card_layer)
        draw = ImageDraw.Draw(img)

        # ヘッダー: ● PekoScore ●
        head_text = "PekoScore"
        hb = draw.textbbox((0, 0), head_text, font=font_header)
        tw = hb[2] - hb[0]
        hy = y0 + 13
        draw.text((cx, hy), head_text, font=font_header, fill=(col_border[0], col_border[1], col_border[2], 240), anchor="mm")
        draw.ellipse([cx - tw // 2 - 10, hy - 3, cx - tw // 2 - 4, hy + 3], fill=col_border[:3])
        draw.ellipse([cx + tw // 2 + 4, hy - 3, cx + tw // 2 + 10, hy + 3], fill=col_border[:3])

        # スコア行
        score_y = cy + 12
        draw_score_row(draw, cx, score_y, str(wins), "勝", str(losses), "敗", font_main, font_sub,
                       c_w=col_win[:3], c_w_lbl=(226, 236, 229),
                       c_l=col_loss[:3], c_l_lbl=(226, 236, 229))

    elif skin == "badge":
        # 2. ピルバッジ
        cw, ch = 126, 92
        x0, y0 = cx - cw // 2, cy - ch // 2
        x1, y1 = cx + cw // 2, cy + ch // 2
        radius = 24
        mid_y = cy

        col_top_bg = hex_to_rgb(cfg_colors.get("top_bg", "#6B9E83"), default=(107, 158, 131))
        col_bot_bg = hex_to_rgb(cfg_colors.get("bot_bg", "#FFFFFF"), default=(255, 255, 255))
        col_top_text = hex_to_rgb(cfg_colors.get("top_text", "#FFFFFF"), default=(255, 255, 255))
        col_bot_text = hex_to_rgb(cfg_colors.get("bot_text", "#D47A70"), default=(212, 122, 112))

        # 下段
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=col_bot_bg[:3],
                               outline=(223, 229, 220, 255), width=3)
        
        # 上段
        top_mask = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        mdraw = ImageDraw.Draw(top_mask)
        mdraw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=col_top_bg[:3])
        mdraw.rectangle([x0, mid_y, x1, y1], fill=(0, 0, 0, 0))
        img = Image.alpha_composite(img, top_mask)
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(223, 229, 220, 255), width=3)
        draw.line([(x0, mid_y), (x1, mid_y)], fill=(223, 229, 220, 255), width=1)

        f_badge_num = get_font(font_family, 22, bold=True)
        f_badge_sub = get_sub_font(font_family, 13, bold=True)

        top_cy = (y0 + mid_y) // 2
        draw_badge_single_row(draw, cx, top_cy, str(wins), "勝",
                              f_badge_num, f_badge_sub,
                              c_num=col_top_text[:3], c_unit=col_top_text[:3])

        bot_cy = (mid_y + y1) // 2
        draw_badge_single_row(draw, cx, bot_cy, str(losses), "敗",
                              f_badge_num, f_badge_sub,
                              c_num=col_bot_text[:3], c_unit=col_bot_text[:3])

    elif skin == "ticket":
        # 3. レトロチケット
        cw, ch = 250, 78
        x0, y0 = cx - cw // 2, cy - ch // 2
        x1, y1 = cx + cw // 2, cy + ch // 2
        radius = 20

        col_bg = hex_to_rgb(cfg_colors.get("bg", "#F8FAF6"), default=(248, 250, 246))
        col_border = hex_to_rgb(cfg_colors.get("border", "#7A9E88"), default=(122, 158, 136))
        col_win = hex_to_rgb(cfg_colors.get("win", "#5F9175"), default=(95, 145, 117))
        col_loss = hex_to_rgb(cfg_colors.get("loss", "#C9685E"), default=(201, 104, 94))

        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=col_bg[:3])
        draw_dashed_rounded_rect(draw, [x0, y0, x1, y1], radius=radius, color=col_border[:3], width=2, dash_len=5, gap_len=3)

        draw.text((cx, y0 + 13), "✦ PEKOSCORE ✦", font=font_header, fill=col_border[:3], anchor="mm")

        score_y = cy + 12
        draw_score_row(draw, cx, score_y, str(wins), "勝", str(losses), "敗", font_main, font_sub,
                       c_w=col_win[:3], c_w_lbl=(74, 94, 83),
                       c_l=col_loss[:3], c_l_lbl=(74, 94, 83))

    else:
        # 4. シンプル文字のみ
        score_y = cy
        col_win = hex_to_rgb(cfg_colors.get("win", "#72EAA5"), default=(114, 234, 165))
        col_loss = hex_to_rgb(cfg_colors.get("loss", "#FFA599"), default=(255, 165, 153))
        col_unit = hex_to_rgb(cfg_colors.get("unit", "#FFFFFF"), default=(255, 255, 255))
        col_shadow = hex_to_rgb(cfg_colors.get("shadow", "#222222"), default=(34, 34, 34))

        for ox in [-2, -1, 0, 1, 2]:
            for oy in [-2, -1, 0, 1, 2]:
                if ox != 0 or oy != 0:
                    draw_score_row(draw, cx + ox, score_y + oy, str(wins), "勝", str(losses), "敗", font_main, font_sub,
                                   c_w=col_shadow[:3], c_w_lbl=col_shadow[:3],
                                   c_l=col_shadow[:3], c_l_lbl=col_shadow[:3])
        draw_score_row(draw, cx, score_y, str(wins), "勝", str(losses), "敗", font_main, font_sub,
                       c_w=col_win[:3], c_w_lbl=col_unit[:3],
                       c_l=col_loss[:3], c_l_lbl=col_unit[:3])

    draw.text((width - 8, 8), "OBS 透過プレビュー", font=font_fixed_label, fill=(130, 145, 165, 170), anchor="rt")

    return img

def draw_score_row(draw, cx, cy, str_w, lbl_w, str_l, lbl_l, font_m, font_s, c_w, c_w_lbl, c_l, c_l_lbl):
    bw_w = draw.textbbox((0, 0), str_w, font=font_m)
    w_num = bw_w[2] - bw_w[0]
    bw_wl = draw.textbbox((0, 0), lbl_w, font=font_s)
    w_lbl = bw_wl[2] - bw_wl[0]
    
    bw_l = draw.textbbox((0, 0), str_l, font=font_m)
    l_num = bw_l[2] - bw_l[0]
    bw_ll = draw.textbbox((0, 0), lbl_l, font=font_s)
    l_lbl = bw_ll[2] - bw_ll[0]
    
    gap_unit = 2
    gap_parts = 14
    total_w = w_num + gap_unit + w_lbl + gap_parts + l_num + gap_unit + l_lbl
    
    curr_x = cx - total_w // 2
    
    draw.text((curr_x, cy), str_w, font=font_m, fill=c_w, anchor="lm")
    curr_x += w_num + gap_unit
    
    draw.text((curr_x, cy + 3), lbl_w, font=font_s, fill=c_w_lbl, anchor="lm")
    curr_x += w_lbl + gap_parts
    
    draw.text((curr_x, cy), str_l, font=font_m, fill=c_l, anchor="lm")
    curr_x += l_num + gap_unit
    
    draw.text((curr_x, cy + 3), lbl_l, font=font_s, fill=c_l_lbl, anchor="lm")

def draw_badge_single_row(draw, cx, cy, num_str, unit_str, f_num, f_unit, c_num, c_unit):
    bn = draw.textbbox((0, 0), num_str, font=f_num)
    w_n = bn[2] - bn[0]
    bu = draw.textbbox((0, 0), unit_str, font=f_unit)
    w_u = bu[2] - bu[0]

    gap_u = 4
    total_w = w_n + gap_u + w_u
    curr_x = cx - total_w // 2

    draw.text((curr_x, cy), num_str, font=f_num, fill=c_num, anchor="lm")
    curr_x += w_n + gap_u
    draw.text((curr_x, cy + 2), unit_str, font=f_unit, fill=c_unit, anchor="lm")
