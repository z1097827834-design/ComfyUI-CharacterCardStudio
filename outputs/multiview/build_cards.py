# -*- coding: utf-8 -*-
"""用仓库自带的 asset_composer / templates 把多视图素材拼成角色卡。

运行： python3 outputs/multiview/build_cards.py
输出： outputs/multiview/card_school_ref.png    （十格·设定集，一张整卡）
       outputs/multiview/card_head_body_6.png   （六格·三视图）
       outputs/multiview/card_fiveref.png       （五格·正反）

说明：fit_mode 用“完整显示”（contain），保证每个画格里的全身从头顶到鞋底都不被裁切；
画格坐标、数量、画格比例全部取自 templates.py，取用规则来自 asset_composer.compose_role_card()。
"""

from __future__ import annotations

import copy
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if "ccs" not in sys.modules:
    pkg = types.ModuleType("ccs")
    pkg.__path__ = [str(ROOT)]  # 让仓库在没有 ComfyUI 环境时也能作为包导入
    sys.modules["ccs"] = pkg

import numpy as np  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from ccs.asset_composer import compose_role_card  # noqa: E402
from ccs.templates import get_template  # noqa: E402

HERE = Path(__file__).resolve().parent
VIEWS = HERE / "views"


def _trim_dark_border(image: Image.Image, max_px: int = 10, threshold: float = 40.0) -> Image.Image:
    """个别素材顶部会带 1~2 行近黑的导出边，先切掉，免得拼进画格里变成黑线。"""
    arr = np.asarray(image.convert("RGB")).astype(float)
    height, width, _ = arr.shape
    top = bottom = left = right = 0
    while top < max_px and arr[top].mean() < threshold:
        top += 1
    while bottom < max_px and arr[height - 1 - bottom].mean() < threshold:
        bottom += 1
    while left < max_px and arr[:, left].mean() < threshold:
        left += 1
    while right < max_px and arr[:, width - 1 - right].mean() < threshold:
        right += 1
    if top or bottom or left or right:
        image = image.crop((left, top, width - right, height - bottom))
    return image


def crop_sides_to(image: Image.Image, aspect: float, min_keep: float = 0.6) -> Image.Image:
    """只裁两侧背景、绝不动上下：素材比画格更“高”时，用它把两侧多余背景裁掉，
    这样全身和头像在画格里能占满，同时头顶鞋底依然完整。"""
    width, height = image.size
    current = width / height
    if aspect >= current:
        return image
    target_w = int(round(height * aspect))
    if target_w < width * min_keep:  # 裁太多会切到人，宁可有留白
        return image
    left = (width - target_w) // 2
    return image.crop((left, 0, left + target_w, height))


def load(name: str) -> Image.Image:
    return _trim_dark_border(Image.open(VIEWS / name).convert("RGB"))


front = load("00_reference_front.png")
side = load("01_body_side.png")
back = load("02_body_back.png")
three_quarter = load("03_body_three_quarter.png")
headshot = load("04_head_portrait.png")
smile = load("05_expression_smile.png")
fabric = load("06_detail_fabric.png")
thinking = load("07_expression_thinking.png")
surprised = load("08_expression_surprised.png")
shoes = load("09_detail_shoes.png")
collar = load("10_detail_collar.png")
serious = load("11_expression_serious.png")
eye = load("12_detail_eye.png")

CELL = 512


def grid(rows: int, cols: int, slots: dict[tuple[int, int], Image.Image], fallback: Image.Image, crop=None):
    """按行优先顺序铺格子：asset_composer 的 crop_equal_grid 也是行优先，
    所以 slots 里的 (row, col) 就是它取用时的下标 row*cols+col。"""
    sheet = Image.new("RGB", (cols * CELL, rows * CELL), "#f2f2f2")
    fallback_piece = ImageOps.fit(fallback, (CELL, CELL), Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    for row in range(rows):
        for col in range(cols):
            piece = slots.get((row, col))
            if piece is None:
                sheet.paste(fallback_piece, (col * CELL, row * CELL))
                continue
            if crop:
                piece = ImageOps.fit(piece, crop, Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            sheet.paste(ImageOps.fit(piece, (CELL, CELL), Image.Resampling.LANCZOS, centering=(0.5, 0.3)),
                        (col * CELL, row * CELL))
    return sheet


# 表情素材表 2×3（行优先）：下标 1=微笑、2=蹙眉清冷、4=惊讶、5=沉思
expression_sheet = grid(
    2,
    3,
    {(0, 1): smile, (0, 2): serious, (1, 1): surprised, (1, 2): thinking},
    fallback=headshot,
)

# 细节素材表 3×3（行优先）：下标 0=眼部、2=面料、4=鞋履、5=领口
DETAIL_SLOTS = {(0, 0): eye, (0, 2): fabric, (1, 1): shoes, (1, 2): collar}
# 十格·设定集的细节格是横向画格，先裁横构图；十四格·全图鉴的细节格偏竖，用方图
detail_sheet_wide = grid(3, 3, DETAIL_SLOTS, fallback=fabric, crop=(CELL * 3 // 2, CELL))
detail_sheet_square = grid(3, 3, DETAIL_SLOTS, fallback=fabric)

# 每个卡版画格比例不同：素材比画格“更高”时先裁掉两侧背景，画格里就不会大片留白。
# 键是 (全身/主角, 头像) 的目标比例；None 表示不裁。
ASPECT_PREP = {
    "xianxia_ref": (0.125 * 2200 / (0.42 * 1300), 0.15 * 2200 / (0.43 * 1300)),
    "school_ref": (0.3 * 2000 / (0.86 * 1400), None),  # 这一版只有主立绘格偏窄
}

TARGETS = [
    ("xianxia_ref", "card_xianxia_ref.png", "十四格·全图鉴", "square"),
    ("school_ref", "card_school_ref.png", "十格·设定集", "wide"),
    ("head_body_6", "card_head_body_6.png", "六格·三视图", "wide"),
    ("fiveref", "card_fiveref.png", "五格·正反", "wide"),
]

reports: dict[str, dict] = {}
for template_id, filename, label, detail_mode in TARGETS:
    detail_sheet = detail_sheet_wide if detail_mode == "wide" else detail_sheet_square
    body_aspect, head_aspect = ASPECT_PREP.get(template_id, (None, None))
    prep = (lambda img, a: crop_sides_to(img, a) if a else img)
    template = copy.deepcopy(get_template(template_id))
    canvas, _assets, report = compose_role_card(
        full_front=prep(front, body_aspect),
        full_profile=prep(side, body_aspect),
        full_back=prep(back, body_aspect),
        action_a=prep(three_quarter, body_aspect),  # school_ref 的主立绘也走 action_a，用斜侧全身当主视觉
        action_b=prep(three_quarter, body_aspect),
        headshot=prep(headshot, head_aspect),
        expression_sheet=expression_sheet,
        detail_sheet=detail_sheet,
        template=template,
        panel_order="",
        fit_mode="完整显示",
        show_labels=False,
    )
    canvas.save(HERE / filename)
    reports[template_id] = report
    print("saved", filename, label, canvas.size)

(HERE / "compose_report.json").write_text(
    json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
)
