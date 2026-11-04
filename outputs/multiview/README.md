# 多视图产出 · 以 `2.webp` 为参考图

用本仓库的卡版数据（`templates.py`）+ 资产排版器（`asset_composer.py`）跑了一遍
“一张参考图 → 多视图角色卡”的流水线。这里的模型侧生成由 Arena 的图像模型完成
（仓库原本是交给 ComfyUI 里的 Qwen-Image 2.1 出图，流程和提示词结构一致）。

## 视图素材（`views/`）

| 文件 | 内容 | 对应卡版画格 |
|---|---|---|
| `00_reference_front.png` | 原始参考图（正面全身） | 正面全身 / 主立绘 |
| `01_body_side.png` | 严格 90° 左侧面全身（朝画面右侧） | 侧面全身 |
| `02_body_back.png` | 严格 180° 背面全身 | 背面全身 |
| `03_body_three_quarter.png` | 四分之三斜侧全身 | 斜侧 / 动作位 |
| `04_head_portrait.png` | 正面头肩肖像 | 正面头像 |
| `05_expression_smile.png` | 微笑表情头肩 | 表情格 |
| `06_detail_fabric.png` | 卫衣面料微距细节 | 细节格 |

生成时统一锁定的角色特征：约 5 岁东亚男孩、短黑发齐刘海、芥末黄圆领卫衣、
藏青休闲裤、白色魔术贴小白鞋、纯浅灰无缝影棚背景、柔和正面棚拍光。
每个视图都要求“头顶到鞋底完整入镜，不裁切、单人不拼贴”。

## 拼出来的卡（本目录根下）

- `card_head_body_6.png` — 六格·三视图：上排正面/侧面/后脑头肩，下排正面/侧面/背面全身（1920×1280）
- `card_fiveref.png` — 五格·正反：上排正面/四分之三头肩，下排正面/侧面/背面全身（1920×1200）

两张卡都使用 `fit_mode="完整显示"`（contain），保证全身从头顶到鞋底都不被裁切；
画格坐标、比例、边框全部来自 `templates.py`，没有另行排版。

## 复现

```bash
pip install pillow numpy
python3 outputs/multiview/build_cards.py
```

脚本用 `importlib` 之外的轻量方式把仓库当成 `ccs` 包加载，
所以不需要 ComfyUI 环境（`folder_paths` 等只在 `nodes.py` 里用到，这里没有导入它）。

`compose_report.json` 是每个画格取用了哪张素材的映射报告，便于核对。

## 顺带修的一个小问题

`asset_composer._portrait_for_cell()` 里“四分之三头像”的判断原本排在“侧面”判断之后，
而四分之三的提示词里本身就带“斜侧/侧脸/侧面”字样，导致 `四分之三头像` 格永远拿到侧面头像。
已把 `three_quarter` 判断提到前面，`tests/layout_contract.py`、`tests/smoke_renderer.py` 通过。

## 本轮没有做的

- `sixtilt_ref`（六格·主视觉）里“主立绘”和“动作全身”都走 `action_a`，
  没有独立动作图时会重复同一张，所以这张卡没有出。
- 表情只做了一张微笑（多格子需要 4~6 个不同表情），细节只做了面料。
