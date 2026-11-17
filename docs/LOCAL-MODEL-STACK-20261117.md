# 本地模型技术底座 · 2026-11-17

> 本文记录本机（RTX 4070 SUPER 12G）的模型选型实测数据与显存治理定案，供后续复用，
> 避免再拿「感觉」选型。起因是一次显存压力排查：显卡长期被压到 89–94%
> （`state/vram-gate.jsonl` 全天记录），桌面没有余量，任何需要 GPU 渲染的客户端都会不稳定。

## 一、显存压力的诊断顺序

| 步骤 | 事实 | 取证手段 |
|---|---|---|
| 1 | 显卡总占用与空闲 | `nvidia-smi --query-gpu=memory.used,memory.free` |
| 2 | **按进程拆显存** | `Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory`（`Get-CimInstance`，免管理员） |
| 3 | 模型驻留与卸载时机 | `ollama ps`（看 `UNTIL` 与 `CONTEXT`） |
| 4 | 闸门历史与占用分布 | `state/vram-gate.jsonl` |

**坑**：`nvidia-smi --query-compute-apps` 在 WDDM 下对图形进程一律返回 `[N/A]`，不能用来找显存大户。

判据补充：GUI 进程「活着但窗口 `IsWindowVisible=False`」通常是渲染表面建不起来，不是进程假死。

## 二、模型选型实测（RTX 4070 SUPER 12G）

同一提示词、`think=false`、UTF-8 直传（PowerShell `ConvertTo-Json` + `Invoke-RestMethod` 会吃掉中文，必须 `[Text.Encoding]::UTF8.GetBytes()`）。

| 配置 | 显存净占 | 解码速度 | 中文质量 |
|---|---|---|---|
| 9B @16K 全 GPU | ~6.6 G | **60.8 tok/s** | 好（「他伫立在雨幕笼罩的渡口…」） |
| 9B @8K 全 GPU | ~6.1 G | 60+ tok/s | 好 |
| 9B @16K 28 层 GPU | — | 28.4 tok/s | 好 |
| 9B @16K 20 层 GPU | — | 14.1 tok/s | 好 |

**定案：`qwen3.5:9b`，全 GPU，`num_ctx=8192`。**
理由：部分层落内存掉速一半以上（28→14 tok/s），内存再充足也不划算；8K 足够容纳居民档案（2.3 KB）+ 体例 + prompt（实测 4939 字符）。

## 三、配置清单（已落地）

| 位置 | 键 | 值 | 作用 |
|---|---|---|---|
| `~/.codely-cli/settings.json` | `flashModel` | `qwen3.5:4b` | 后台杂活走轻量档，避免与生产/训练抢显存 |
| 用户环境变量 | `BIGLIFE_MODEL` | `qwen3.5:9b` | 居民内容生产主力 |
| 用户环境变量 | `BIGLIFE_LLM_URL` | `http://127.0.0.1:11434/v1/chat/completions` | 绕过已死的 `:8090`，直连 Ollama |
| 用户环境变量 | `BIGLIFE_VRAM_LIMIT` | `0.82` | 显存闸阈值，从 0.90 收紧，给桌面留 18% |

`Tools/evolve_citizen.py` 的 `vram_guard()` 改为读 `BIGLIFE_VRAM_LIMIT`（默认仍 0.90，向后兼容）。

## 四、让路守护

`Tools/wait_then_produce.py`（`pythonw` 静默，无窗口）：

1. 按命令行匹配 `*_train_network.py`，连续 3 轮（60 s/轮）无匹配 = 训练结束
2. 再等 120 s 让驱动回收显存
3. `memory.free < 6000 MiB` 则退避 10 分钟，最多 8 次（**不硬挤**）
4. 跑 `evolve_citizen.py --batch N`
5. 回执 `state/wait-produce.json`，日志 `state/wait-produce.log`

## 五、工作流验证（零 GPU 部分已过）

- `prompt_dryrun.py --selftest`：6/6 PASS（clean / repeat / ban-miss / ban-ok / ban-tail / ban-bug）
- 实际 prompt：4939 字符，自伤命中 0，verdict PASS，报告 `qa/PROMPT-DRYRUN-2026-11-17.md`
- prompt 内建硬约束：天气对齐（阴天禁晴系措辞）、风速量级（8.9 m/s 只能写「风挺大」）、时段（白天禁「今晚/深夜」）、禁机房贷台词、禁工作台词汇、反模板家族（同开场 ≥8 即硬线）

## 六、边界与风险

1. **训练期间不加载大模型**：`blocks_to_swap 26` 的 LoRA 训练已把自己压到临界，再加 6 GB 会让两边都降速。
2. **Ollama `keep_alive` 可被调用方覆盖**：环境变量 `OLLAMA_KEEP_ALIVE=5m` 管不住请求级 `Forever`；根因是调用方，不是服务端。
3. **`OLLAMA_MAX_LOADED_MODELS=1`**：9B 与 4B 会互挤，切换有 5–10 s 冷加载，属预期。
4. **不做跨模型并发**：实测单机并发不增吞吐（与 `LOCAL-CAPACITY` 结论一致）。

## 七、待办

- [ ] 训练结束 → 守护自动跑第一批 `--batch 6`，人眼验收质量
- [ ] 把 `wait_then_produce` 扩到其它产线（`build_city_voices` / `city_broadcast` / `build_rumors`）
- [ ] 考虑给 Ollama 加请求级 `keep_alive` 上限（网关侧改造，避免任何调用方永久驻留）
