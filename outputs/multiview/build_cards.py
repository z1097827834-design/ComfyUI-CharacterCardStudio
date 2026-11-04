# -*- coding: utf-8 -*-
"""用仓库自带的 asset_composer / templates 把多视图素材拼成角色卡。

运行： python3 outputs/multiview/build_cards.py
输出： outputs/multiview/card_head_body_6.png （六格·三视图）
       outputs/multiview/card_fiveref.png      （五格·正反）

说明：fit_mode 用“完整显示”（contain），保证每个画格里的全身从头顶到鞋底都不被裁切；
卡片底板沿用卡版默认白色，画格之间的留白就是排版留白。
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

from PIL import Image, ImageOps  # noqa: E402

from ccs.asset_composer import compose_role_card  # noqa: E402
from ccs.templates import get_template  # noqa: E402

HERE = Path(__file__).resolve().parent
VIEWS = HERE / "views"

front = Image.open(VIEWS / "00_reference_front.png").convert("RGB")
side = Image.open(VIEWS / "01_body_side.png").convert("RGB")
back = Image.open(VIEWS / "02_body_back.png").convert("RGB")
three_quarter = Image.open(VIEWS / "03_body_three_quarter.png").convert("RGB")
headshot = Image.open(VIEWS / "04_head_portrait.png").convert("RGB")

smile = Image.open(VIEWS / "05_expression_smile.png").convert("RGB")
fabric = Image.open(VIEWS / "06_detail_fabric.png").convert("RGB")


def tile(image: Image.Image, rows: int, cols: int, cell: int = 512) -> Image.Image:
    """把单张素材铺成 rows×cols 的九宫格/六宫格，供 asset_composer 按格裁切取用。"""
    sheet = Image.new("RGB", (cols * cell, rows * cell), "#f2f2f2")
    piece = ImageOps.fit(image, (cell, cell), Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    for row in range(rows):
        for col in range(cols):
            sheet.paste(piece, (col * cell, row * cell))
    return sheet


expression_sheet = tile(smile, 2, 3)
detail_sheet = tile(fabric, 3, 3)


BACKGROUND = "#ffffff"  # 沿用卡版默认白底：素材按“完整显示”居中，四周留白不裁切

TARGETS = [
    ("head_body_6", "card_head_body_6.png"),
    ("fiveref", "card_fiveref.png"),
]

reports: dict[str, dict] = {}
for template_id, filename in TARGETS:
    template = copy.deepcopy(get_template(template_id))
    template["defaults"]["background"] = BACKGROUND
    canvas, _assets, report = compose_role_card(
        full_front=front,
        full_profile=side,
        full_back=back,
        action_a=three_quarter,
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
    print("saved", filename, canvas.size)

(HERE / "compose_report.json").write_text(
    json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
)
