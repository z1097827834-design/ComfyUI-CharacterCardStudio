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


# 表情：2×3 → 下标 1=微笑、4=惊讶、5=沉思（其余格用平静头像占位，模板里不取用）
expression_sheet = grid(
    2,
    3,
    {(0, 1): smile, (1, 1): surprised, (1, 2): thinking},
    fallback=headshot,
)

# 细节：3×3 → 下标 2=面料、4=鞋履、5=领口；细节格是横向画格，先裁成横构图再铺
detail_sheet = grid(
    3,
    3,
    {(0, 2): fabric, (1, 1): shoes, (1, 2): collar},
    fallback=fabric,
    crop=(CELL * 3 // 2, CELL),
)

TARGETS = [
    ("school_ref", "card_school_ref.png", "十格·设定集"),
    ("head_body_6", "card_head_body_6.png", "六格·三视图"),
    ("fiveref", "card_fiveref.png", "五格·正反"),
]

reports: dict[str, dict] = {}
for template_id, filename, label in TARGETS:
    template = copy.deepcopy(get_template(template_id))
    canvas, _assets, report = compose_role_card(
        full_front=front,
        full_profile=side,
        full_back=back,
        action_a=three_quarter,  # school_ref 的主立绘也走 action_a，用斜侧全身当主视觉
        action_b=three_quarter,
        headshot=headshot,
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
