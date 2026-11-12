# T-20261112-11 环依赖面同日不刷新 —— 修法证据（2026-11-12 20:0x @BigLife-OSLoop R2625）

## 缺陷实证
- 19:35 与 19:54 两批年轮落环（各 10 席）后，`round_daily.py --run` 对 8 个环依赖面全部报 `skipped-fresh`：
  `today / dossiers / gallery / relations / districts / ring_picks / ring_quality / ring_trend`
  实测 mtime 停在 19:04–19:19，早于新环落盘时间 → CEO 可见面比户籍库落后两批。
- 根因两层：①`DEPENDS` 只登记了 `gene_ledger` / `lexicon` 两面，环依赖面未登记；
  ②`_is_stale` 的 daily 档（`today`/`ring_trend`）根本不调 `_dep_mtime_stale`，日期粒度看不见同日源变更。
- 同类病根参见 T-20261112-09（同日源更新→面静默停更），本单是其「环族」缺口补完。

## 修法（`Tools/round_daily.py` v0.12）
1. `DEPENDS` 新增 8 个环依赖面，源=`state/evolve-cursor.json`（每批年轮必写）+ `census/registry`（新注册卡；目录 mtime 只反映增删，故 cursor 才是环落地主信号）。
2. daily 档 drift 链补 `_dep_mtime_stale`。
3. 新增 `DEPENDS_FLOOR_MIN = 60` 冷却：刚重建过的面 60 分钟内不再因下一批年轮重刷——年轮批约每轮一次，若不设下限，2.9MB 的 `resident-gallery.html` 将每 5 分钟重建并被提交（违 REPO-SLIM 律）。

## 验证
- 正负控 4/4 PASS（进程内合成件，不碰真件）：
  1. 产物旧 3h + 源新 → `dep-mtime:<源>`（判 stale，正控）
  2. 产物刚重建 + 源新 → `None`（冷却抑制）
  3. 源比产物旧 → `None`（无变更不刷）
  4. 未登记 key → `None`（不误伤）
- 全量体检 `python -X utf8 Tools/round_daily.py --check`：`stale=0 ran=0 failed=0 verdict: PASS`（20:0x 刚重建，冷却生效、零假阳性）
- 实弹补建（本轮手工）：`--run --all --only today,dossiers,gallery,ring_quality,ring_trend,relations,districts,ring_picks,index` → `ran=9 failed=0`，9 面 mtime 20:01。

## 残余风险
- 冷却窗内（≤60min）新环不进面属预期设计，非缺陷；跨轮次最多滞后 1 小时。
- `state/evolve-cursor.json` 在 `.gitignore`（state/），换机首轮若该档缺失则依赖信号为空 → 面按日期档照常跑，退化安全（不报错、不重建）。

## 追加·真实件正控（同日 20:0x 实弹）
- 对真件 census/export/city-ring-trend.html 造 61 分钟前 mtime → --check --only ring_trend 报 dep-mtime:state/evolve-cursor.json（stale=1，判据在真实路径上生效）；
- --run --only ring_trend 回补 → 再体检 resh（stale=0）——触发-重建-转绿闭环成立，无需等真实 60 分钟窗口。
