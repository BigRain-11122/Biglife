# VOICE-POOL —— 声纹池总契约 v1.0（四面数字生命·可听面）

> 溯源：CEO 定向开工令 2026-09-25「生命公司目前工作情况很不饱和，自己调研确立方向，全面开工！」（orders/O-20260925-1138-bm-c）；CODEX §十二 v3.9 T2 登记（否决窗至 2026-10-02）；方向调研件=docs/research/R-20260925-bl-saturation-direction.md。
> 定位：1 万居民的声音资产面——**声纹=确定性派生**（颜色即个性同律：参数即嗓音），与形象面（atlas_manifest）对称的「零个体文件、数据行制」生产制。
> 本地算力律合规（SILICON-LIFE 律三）：一切合成本地（SAPI）·**零云端 token**。

## 一、声纹派生律（确定性·md5(id)·禁 python hash()）

- **基音（v0）**：本机 SAPI `Microsoft Huihui Desktop - Chinese (Simplified)` 单声源。**诚实标注：v0=单基音+参数调制，全城听感同源**——参数分带提供物种/年龄/性别气质差，非真实多声源。
- **分带**（pitch=半音级偏移 ∈[-10,+10]·rate=语速百分比 ∈[-15,+25]·vol=[80,100]）：
  - 碳基·男：少年 [+5,+8]/[+10,+20]；青年 [0,+4]/[0,+10]；中年 [-4,0]/[-5,+5]；老年 [-8,-5]/[-15,-5]
  - 碳基·女：少年 [+8,+10]/[+10,+25]；青年 [+3,+7]/[0,+10]；中年 [0,+4]/[-5,+5]；老年 [-3,+1]/[-15,-5]
  - 硅基：男 [-10,-6]/[-5,+5]；女/无定 [-4,0]/[-5,+5]（机械感=偏低稳）
  - 像素灵：[+7,+10]/[+10,+25]（轻快光点感）
  - 带内抖动=md5(id) 定序（同 id 恒同参数）——**同一 id 双跑逐字节一致**（判据 2）。
- **kokoro 神经声（v1·2026-09-26 自裁决解锁）**：第三声源=**8 zh 基音真实多声源**（zf_xiaobei/xiaoni/xiaoxiao/xiaoyi 四女声 + zm_yunjian/yunxi/yunxia/yunyang 四男声·sid 45-52=k2-fsa 官方文档权威表）。派生律：性别→声池（女/无定→zf 池·男→zm 池）+ md5(id) 池内定选（同 id 恒同音色）+ rate 带→speed=100/(100+rate)（pilot 同律）——**kokoro 基音自带音高质感、无 pitch 调制参数（诚实标注：参数面=速度）**；多线程推理非逐字节确定（±ms 级尾样漂移·引擎音频面不作逐字节判据·同 §三 3 律）。
- **荣誉席 C-00001~03：blocked=true 不合成**（CEO 人设权保留面·CODEX §十——家人声音不出产线）。

## 二、产线件

| 件 | 面 | 级 |
|---|---|---|
| `Tools/voice_manifest.py` | 万人声纹参数 → `census/export/citizen-voice.jsonl`（10003 行·字段 id/name/species/gender/age/voice{base,pitch,rate,vol}/blocked） | **R3 再生面**（gitignored·消费前重生成·秒级） |
| `Tools/voice_synth.ps1` | 参数+台词文本 → SAPI SSML → WAV（`voice-cache/` 缓存 gitignored；`voice-samples/` 样例包 committed ≤12 片） | 按需调用面 |
| `Tools/kokoro_synth.py` | 8 zh 神经声合成（sherpa-onnx 1.13.8 CPU·本地零云端·`--pilot`/`--qc`/`--id` 单发·speed 派生同律） | 按需调用面 |
| 样例包 `census/export/voice-samples/` | v0=8 片锚民（三物种×两性×四年龄带×五城区覆盖）·文本=「{信条}」+报名句（creed≤40 字截断·导出面字段直读·确定性） | 交付面 |
| 试点包 `census/export/voice-pilot-kokoro/`（fp32）+ `voice-pilot-kokoro-int8/` | 8 锚民 A/B vs piper 同文本（2026-09-26·五音色分布） | 交付面 |

## 三、判据（机器可验·判据先行）

1. manifest rows=10003（QC 对齐）；物种/年龄/性别分带映射全在带内；荣誉席 3 行 blocked。
2. 同输入双跑逐字节一致（voice_manifest.py --qc 内建）。
3. 样例包：SSML 串=参数确定性拼装（引擎音频面=SAPI 出·不作逐字节判据·如实标注）；每片 ≤15 秒。
4. 诚实边界：台词文本=导出面字段直读（信条+名）零 LLM 零编造；blocked 席零产物。

## 四、升级路（M→部分实证·O-20260925-1416 加速令）

- **piper 通道已实证（2026-09-25 试点·census/export/voice-pilot-piper/ 8 片）**：zh_CN-huayan-medium 63MB 模型经 hf-mirror 断点续传落位 K:\Fluxgroup\.tools\piper-voices\（隔离 venv K:\Fluxgroup\.tools\tts-venv\ 零污染主环境）——**神经声质量显著优于 SAPI**（自然语速：顾阿凤同文本 SAPI 11.1s vs piper 3.7s=拼接停顿消除）；per-citizen length_scale=100/(100+rate) 派生自声纹 manifest（确定性）；坑=piper stdin 按 GBK locale 解码须 PYTHONUTF8=1。
- **kokoro 终解已解锁（2026-09-26 自裁决批·CEO 令「你自己科学决策」）**：HF 401 授权墙**不破解·换公开正源**——k2-fsa/sherpa-onnx Release（Apache 2.0·GitHub release-assets 直连）`kokoro-multi-lang-v1_0`（fp32 310MB）/`kokoro-int8-multi-lang-v1_0`（109MB）双包落位 K:\Fluxgroup\.tools\kokoro\，**包自带 voices.bin 26.9MB（全 53 声纹·含 8 zh 基音·sid 45-52）**——零账号零 token 全法合规；运行时=sherpa-onnx 1.13.8（tts-venv·CPU 零云端）；**下载通道判例=长连单流在本网络必僵死（--max-time 不救·received 冻结实证）→ 分块续传法（8MB 块·90s 超时·逐块落盘即验·HTTP 206）一次全过**；v1_1（103 声纹）=后续升级路待点单。
- 消费方：M4 参观端（居民语音气泡）/CityWatch（城市声景）/BigStream（内容素材引用走任务单）。

## 五、验收实录

- 2026-09-25（定向批·bm-c 交互会话）：voice_manifest.py 首跑 rows=10003 bad=0 blocked=3（见本批 commit·QC 输出随批）；样例包 8 片=C-00010/11/13/15/17/19/28/29（碳基老女/碳基老男/碳基青男/碳基中女/硅基无定/硅基男/像素灵×2）。
- 2026-09-26（自裁决批·bm-c 交互会话）：kokoro_synth.py --qc PASS（池律/md5 确定性/speed 律/sid 权威表/荣誉席守卫）；int8 试点 8/8（五音色分布·语速 3.43-5.46s 自然·speed 与 piper manifest 逐位同律）；fp32 试点 8/8（A/B 主面·语速 3.43-5.37s）；**引擎定谳=fp32 生产默认**（本机 onnxruntime CPU 实测 int8 动态量化反慢 2-3 倍：int8 gen 6.7-10.9s vs fp32 1.5-3.6s=量化开销负优化·质量与速度双胜）；HF gated 墙绕开定谳=sherpa 公开正源零账号零 token。
