# 多视图角色卡产出 · 以 `2.webp` 为参考图

用本仓库的卡版数据（`templates.py`）+ 资产排版器（`asset_composer.py`）跑了一遍
“一张参考图 → 多视图 → 一张角色卡”的流水线。模型侧的出图由 Arena 的图像模型完成
（仓库原本是交给 ComfyUI 里的 Qwen-Image 2.1 出图，流程、画格比例、取用规则一致）。

## 主交付：`card_xianxia_ref.png`（十四格·全图鉴，2200×1300）

左侧四张全身 + 三张头像，右侧四表情 + 三细节 + 一条面料。

| # | 画格 | 内容 | 素材 |
|---|---|---|---|
| 1 | 正面全身 | 正面站姿 | `views/00_reference_front.png` |
| 2 | 右侧面全身 | 镜像侧面（与第 4 格左右相反） | `views/01_body_side.png` 水平翻转 |
| 3 | 背面全身 | 严格 180° 背面 | `views/02_body_back.png` |
| 4 | 左侧面全身 | 严格 90° 侧面 | `views/01_body_side.png` |
| 5 | 正面头像 | 正面头肩 | `views/04_head_portrait.png` |
| 6 | 侧面头像 | 侧脸轮廓 | 由第 4 格素材自动裁头部 |
| 7 | 斜侧头像 | 四分之三斜侧 | 由 `views/03_body_three_quarter.png` 自动裁头部 |
| 8 | 温柔微笑 | 闭唇微笑 | `views/05_expression_smile.png` |
| 9 | 惊讶张嘴 | 瞪眼张嘴 | `views/08_expression_surprised.png` |
| 10 | 闭眼沉思 | 垂眼看下方 | `views/07_expression_thinking.png` |
| 11 | 蹙眉清冷 | 蹙眉冷峻直视 | `views/11_expression_serious.png` |
| 12 | 眼部细节 | 单眼微距（虹膜纹理） | `views/12_detail_eye.png` |
| 13 | 配饰细节 | 领口罗纹与肩缝（角色无配饰，占这一格） | `views/10_detail_collar.png` |
| 14 | 面料细节 | 卫衣面料横向微距 | `views/06_detail_fabric.png` |

## 其他卡版（同一批素材，换排版）

- `card_school_ref.png` — 十格·设定集（2000×1400）：左主立绘 + 三视图全身 + 三表情 + 三细节
- `card_head_body_6.png` — 六格·三视图（1920×1280）：上排正面/侧面/后脑头肩，下排三张全身
- `card_fiveref.png` — 五格·正反（1920×1200）：上排正面/四分之三头肩，下排三张全身

## 视图素材（`views/`）

| 文件 | 内容 |
|---|---|
| `00_reference_front.png` | 原始参考图（正面全身） |
| `01_body_side.png` | 严格 90° 侧面全身 |
| `02_body_back.png` | 严格 180° 背面全身 |
| `03_body_three_quarter.png` | 四分之三斜侧全身 |
| `04_head_portrait.png` | 正面头肩肖像 |
| `05_expression_smile.png` / `07_expression_thinking.png` / `08_expression_surprised.png` / `11_expression_serious.png` | 微笑 / 沉思 / 惊讶 / 蹙眉 |
| `06_detail_fabric.png` / `09_detail_shoes.png` / `10_detail_collar.png` / `12_detail_eye.png` | 面料 / 鞋履 / 领口 / 眼部 微距 |

生成时统一锁定的角色特征：约 5 岁东亚男孩、短黑发齐刘海、芥末黄圆领卫衣、
藏青休闲裤、白色魔术贴小白鞋、浅灰无缝影棚背景、柔和正面棚拍光；
每个视图都要求“头顶到鞋底完整入镜，不裁切、单人不拼贴”。

## 拼卡规则

- 画格坐标、数量、比例全部来自 `templates.py`，取用规则来自 `asset_composer.compose_role_card()`；
  `compose_report.json` 是“画格 ← 素材”的映射报告。
- `fit_mode="完整显示"`（contain），保证全身从头顶到鞋底都不被裁切。
- 素材比画格“更高”时，先只裁两侧背景（`crop_sides_to`），让全身在竖画格里占满，头顶和鞋底不动。
- 表情/细节按 `crop_equal_grid` 的行优先下标贴进 2×3 / 3×3 素材表：
  表情下标 1=微笑、2=蹙眉、4=惊讶、5=沉思；细节下标 0=眼部、2=面料、4=鞋履、5=领口。
  十格卡的细节格是横向画格，另做一份横构图素材表。

## 复现

```bash
pip3 install --break-system-packages pillow numpy
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
