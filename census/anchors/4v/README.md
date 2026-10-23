# 4 视角身份锚包（census/anchors/4v/）

任务来源：`tasks/TASKS.md` **T-20261024-02**（研究条目=cph4/research/R-20261023-scan-silicon-city 条目 4·ELECT arXiv 2610.15555）。

## 是什么

一居民一文件 `<ID>.json`，内含 **4 个视角**（front 正 / half 半侧 45° / side 正侧 90° / back 背）的生成提示词，
供立绘链、FluxVerse 角色资产、MV/漫剧选角共用——同一居民跨项目同一张脸。

## 契约

| 项 | 规则 |
|---|---|
| 身份核 `identity_core` | species/gender/age/locale/profession/outfit/signature/creed 八项，四视角**逐字共享** |
| `identity_hash` | `md5(id::biglife-portrait-anchors-v1::身份核文本)[:16]`，同居民恒等式，漂移即可见 |
| 名字分离 | 姓名只在 `display_name` 单列登记；任何 `prompt_views[].prompt` 内**不出现姓名**（源文本里的姓名脱名为「本人」） |
| 一致性铁律 | 仅相机角度变化；禁换装/换发型/换配饰/改比例 |
| 荣誉席 | `faction=honored` 或 district 空 → `status=reserved`，零 prompt 零发明（CEO 人设权保留面） |
| 确定性 | 零 LLM、零随机；同输入双跑逐字节一致 |

## 生成 / 校验

```bash
python -X utf8 Tools/anchor_multiview.py                 # 20 位手写展示锚（原型样板）
python -X utf8 Tools/anchor_multiview.py --ids C-04868   # 指定居民
python -X utf8 Tools/anchor_multiview.py --limit 50      # 前 50 位可生成居民
python -X utf8 Tools/anchor_multiview.py --qc            # 只校验不写盘
```

QC 六项：①四视角齐备 ②身份核四视角逐字一致 ③姓名零泄漏 ④profession/outfit 必进 prompt
⑤双跑字节一致 ⑥保留面零 prompt。当前状态：**20/20 ok，identity_drift=0，name_leak=0，双跑一致**。

## 已接 / 未接

- 已接：规格级身份锚（文本面零漂移门），可直接进任何 prompt→图像流水线。
- 未接：图像级渲染与 aCCS 相似度实测（判据 `<0.833` 需渲染链，ELECT 参考 8.3s/帧·<20GB 显存）；
  该步待 GPU 空闲窗或云端配额（>500 积分须 CEO 真金亲批）。
- 判据进度：T-20261024-02「同框比对无身份漂移」的**规格级**部分已达成，**图像级**部分开放。