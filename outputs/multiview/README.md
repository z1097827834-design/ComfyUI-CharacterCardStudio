# 多视图角色卡产出 · 以 `2.webp` 为参考图

用本仓库的卡版数据（`templates.py`）+ 资产排版器（`asset_composer.py`）跑了一遍
“一张参考图 → 多视图 → 一张角色卡”的流水线。模型侧的出图由 Arena 的图像模型完成
（仓库原本是交给 ComfyUI 里的 Qwen-Image 2.1 出图，流程、画格比例、取用规则完全一致）。

## 主交付：`card_school_ref.png`（十格·设定集，2000×1400）

一张卡装完：左侧主立绘，右侧上排三视图全身、中排三表情、下排三细节。

| 画格 | 内容 | 素材 |
|---|---|---|
| 1 主立绘 | 四分之三斜侧全身 | `views/03_body_three_quarter.png` |
| 2 正面全身 | 正面站姿 | `views/00_reference_front.png` |
| 3 侧面全身 | 严格 90° 左侧面 | `views/01_body_side.png` |
| 4 背面全身 | 严格 180° 背面 | `views/02_body_back.png` |
| 5 甜美微笑 | 露齿笑表情 | `views/05_expression_smile.png` |
| 6 低头沉思 | 垂眼看下方 | `views/07_expression_thinking.png` |
| 7 惊讶张嘴 | 瞪眼张嘴 | `views/08_expression_surprised.png` |
| 8 服装细节 | 卫衣面料微距 | `views/06_detail_fabric.png` |
| 9 配饰细节 | 领口罗纹与肩缝（角色无配饰，用领口细节位） | `views/10_detail_collar.png` |
| 10 鞋履细节 | 小白鞋与裤脚 | `views/09_detail_shoes.png` |

## 其他卡版（同一批素材，换排版）

- `card_head_body_6.png` — 六格·三视图（1920×1280）：上排正面/侧面/后脑头肩，下排正面/侧面/背面全身
- `card_fiveref.png` — 五格·正反（1920×1200）：上排正面/四分之三头肩，下排正面/侧面/背面全身

## 视图素材（`views/`）

| 文件 | 内容 |
|---|---|
| `00_reference_front.png` | 原始参考图（正面全身） |
| `01_body_side.png` | 严格 90° 左侧面全身（人物朝画面右侧） |
| `02_body_back.png` | 严格 180° 背面全身 |
| `03_body_three_quarter.png` | 四分之三斜侧全身 |
| `04_head_portrait.png` | 正面头肩肖像 |
| `05_expression_smile.png` | 微笑表情 |
| `07_expression_thinking.png` | 低头沉思 |
| `08_expression_surprised.png` | 惊讶 |
| `06_detail_fabric.png` / `10_detail_collar.png` / `09_detail_shoes.png` | 面料 / 领口 / 鞋履 细节 |

生成时统一锁定的角色特征：约 5 岁东亚男孩、短黑发齐刘海、芥末黄圆领卫衣、
藏青休闲裤、白色魔术贴小白鞋、浅灰无缝影棚背景、柔和正面棚拍光；
每个视图都要求“头顶到鞋底完整入镜，不裁切、单人不拼贴”。

## 拼卡规则

- 画格坐标、数量、比例全部来自 `templates.py`，取用规则来自 `asset_composer.compose_role_card()`；
  `compose_report.json` 是“画格 ← 素材”的映射报告。
- `fit_mode="完整显示"`（contain），保证全身从头顶到鞋底都不被裁切。
- 表情/细节用 `crop_equal_grid` 的行优先下标贴进 2×3 / 3×3 素材表：
  表情下标 1=微笑、4=惊讶、5=沉思；细节下标 2=面料、4=鞋履、5=领口。

## 复现

```bash
pip install pillow numpy
python3 outputs/multiview/build_cards.py
```

脚本不需要 ComfyUI 环境（`folder_paths` 只在 `nodes.py` 里用到，这里没有导入它）。

## 顺带修的两个映射问题（`asset_composer.py`）

1. `_portrait_for_cell()` 里“四分之三”判断原本排在“侧面”之后，而四分之三的提示词本身带
   “斜侧/侧脸”，导致四分之三头像格永远拿到侧面头像 → 已把 `three_quarter` 判断提前。
2. 同一函数用 `"右侧"` 两个字判断“右侧面要镜像”，但“人物朝画面右侧”讲的是朝向，
   结果左侧面头像被镜像成朝左 → 改成按 `body_right` / “朝左·右半边脸·右耳”判断。

`tests/layout_contract.py`、`tests/smoke_renderer.py` 通过（`workflow_smoke.py` / `ui_smoke.py`
需要 playwright，本环境未安装）。
