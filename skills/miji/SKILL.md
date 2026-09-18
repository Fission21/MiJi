---
name: MiJi
description: 书/视频/PDF/JAR 蒸馏成skill或入库知识库时用。MinerU/jadx解析→通读→提炼，多源融合。
version: 2.0.0
author: CC
tags: [book, skill, 读书, pdf, video, 提炼, workflow, 多源融合, jar, jadx, 反编译]
---

# 读书蒸馏流程（skill 与知识库双出口 · Hermes 专属）

> 2026-08-27 实测跑通：主人发《Refactoring UI》PDF → 封装成 `refactoring-ui-principles` skill。
> 2026-08-27 新增**视频模式**：yt-dlp 下载 → ffmpeg 抽音频 → faster-whisper 转写 → 同一蒸馏流程。
> 2026-09-09 新增**JAR 模式**：jadx 反编译 → jar_to_md.py 类索引 md → 同一蒸馏流程（书/视频/字节码三源归一）。
> 2026-09-17 新增**本地模型模式**：本地 llama.cpp（Qwen3.6-35B-A3B）逐章 map + 全书 reduce，零 API 成本蒸馏（DDIA 491 页英文书实战）。
> 2026-09-18 **v2.0 产出配方**：6 种产出模式 × 三问菜单（给谁看/什么语言/什么形态）——AI 侧（skill/知识库）+ 人侧（全书翻译/双语对照/人类导读）+ 综合套餐；翻译样式可选（纯译 / 一行原文一行译文）。
> 本 skill 固化整条流程，后续「读书/看视频/反编译 jar → 封装 skill」照此执行。

## 触发条件

- 主人发来 PDF/EPUB/长文档，说「封装成 skill」「提炼成 skill」「读书」「做成 skill」
- 主人发 B站/抖音/YouTube/小红书**视频链接**，说「把这个视频蒸馏成 skill」「提取视频内容」
- 主人说「**入库**」「存进知识库」「建知识库」「多端蒸馏到一起」→ 知识库形态：`python3 ~/demo/scripts/kb.py add <主题> <文件...>`，库根 `~/demo/knowledge-base/`（详见下方「知识库形态」与 相关/kb.py）
- 主人发来 `.jar`/`.apk`，说「蒸馏这个 jar」「把 jar 入库」「分析这个包」→ JAR 模式（Step 1d）
- 主人要求把一本书/一段视频的方法论固化成可复用的 agent 技能

## 内容来源（三条路径）

| 来源 | 工具链 | 产出 |
|------|--------|------|
| **PDF/扫描件** | MinerU（见 mineru-pdf-parser）| 完整 markdown |
| **视频/播客** | yt-dlp + ffmpeg + faster-whisper（见下）| transcript.txt 转写文本 |
| **JAR/APK**（Java/Kotlin 字节码） | jadx 反编译 + scripts/jar_to_md.py（见 Step 1d）| 带类索引的反编译源码 md |

**解析路由总表**（OCR 只该花在「像素里的字」上——判断依据是文本层，不是文件格式）：

| 格式 | OCR? | 走法 |
|------|:---:|------|
| Word/TXT/MD/HTML/EPUB | ❌ | 直接读，不进 MinerU（OCR 原生文本反而引入识别错误） |
| PDF 文字版 | ❌（不用 OCR 兵底，但**也别直抽了事**） | **统一走 MinerU**（2026-09-18 主人纠正）：实测 491 页文字版 MinerU 10 分钟 → 完整标题层级（549 标题）+ 98 处插图引用 + 108 张图；pypdfium2 直抽只有 13 个标题、0 图。直抽仅无 MinerU 环境时兵底，作字符级对照可另存一份 |
| PDF 扫描版/图片型 | ✅ | 必须走 OCR：本地 MinerU 或云端 VLM（luna）二选一 |
| 视频/音频 | ASR 而非 OCR | YouTube 等先抓官方字幕（`--write-subs`/页面 transcript，零 ASR），无字幕才 whisper |
| JAR/APK（.class 字节码） | ❌（OCR 无意义） | jadx 反编译出 .java 后按文本路径走；资源文件从 jadx 的 resources/ 单独提取 |

两条路径的产出都是**纯文本**，之后走同一条蒸馏流程（Step 2 起）。

## 完整流程（6 步）

### Step 1 — 解析文档为 Markdown

**PDF/扫描件**：用 MinerU（先加载 `mineru-pdf-parser` skill 看环境与坑）：

```bash
unset PYTHONPATH
export MINERU_PROCESSING_WINDOW_SIZE=32   # 长文档防 MPS 崩溃，关键！
~/demo/ai-tools/mineru-venv/bin/mineru -p "输入.pdf" -o 输出目录 -b pipeline
```

- 输出在 `输出目录/<文件名>/auto/*.md`（161KB 级别的完整 markdown）
- 252 页书约 4-6 分钟；**扫描版走 OCR 慢 3-4 倍**（484 页扫描书 >20 分钟，正常不是卡死，见 mineru skill 时间校准）；跑完检查 `EXIT=0` 且 md 非空
- **已是 md/txt 的**：跳过 MinerU，直接读源文件

### Step 1b — 视频/播客 → 转写文本（视频模式）

**AI 能力清单（此步需要提前准备）**：

| 能力 | 用在哪 | 最低要求 | 无此能力时 |
|------|--------|---------|-----------|
| **LLM API**（OpenAI 兼容）| ① 从标题/简介自动生成转写提示词 ② 转写稿纠错 | 任一兼容端点+key（deepseek/glm/kimi/本地 ollama 均可）| 提示词需人工手写；跳过纠错（转写质量下降）|
| **语音识别** | 音频→文本 | faster-whisper（CPU 可跑）或 openai-whisper CLI | 无法处理无字幕视频 |
| **yt-dlp** | 平台视频下载 | 最新版（B站/YouTube/小红书通用）| 无法获取视频 |
| **ffmpeg** | 抽音频 | 系统自带或 brew/apt 安装 | — |

> 字幕优先级最高：`yt-dlp --write-subs --sub-langs "zh,en"` 拿到字幕就**完全不需要** ASR 和 LLM 纠错，直接 Step 2。

```bash
# 0. 准备：安装依赖（任选其一装 whisper）
pip install yt-dlp faster-whisper        # 推荐 faster-whisper（快4倍）
# 或 pip install yt-dlp openai-whisper
# ffmpeg: macOS `brew install ffmpeg` / Ubuntu `apt install ffmpeg`

# ① 下载音频
yt-dlp --proxy <代理地址,如有> -f "ba" -x --audio-format wav \
  -o "video.%(ext)s" "<视频链接>"         # 只要音频用 -f "ba"，比带视频快得多

# ② 【AI-1】让 LLM 从标题/简介自动生成 initial_prompt（无需人工懂视频内容）
#    实测有效：标题里的「MiniMax H3越狱」进 prompt 后转写命中从 0 → 4+
python3 transcribe_prompt_gen.py "<视频标题>" "<简介关键句>"
#   输出形如: 下面是关于MiniMax H3越狱模型的教程。MiniMax H3, 越狱模型, 开源, ...
#   没有 LLM 时: 自己看一眼标题，把专有名词手动列成一行也可

# ③ faster-whisper 转写（⚠️ 中文必须带 initial_prompt，实测同音字错误大幅减少）
python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
prompt = '<②生成的提示词>'
segments, info = model.transcribe('video.wav', language='zh', beam_size=5, initial_prompt=prompt)
open('transcript.txt','w').write('\n'.join(f'[{s.start:.1f}-{s.end:.1f}] {s.text.strip()}' for s in segments))
"

# ④ 【AI-2】LLM 二次纠错（修 ASR 层面无解的英文品牌名等，见下方数据表）
python3 llm_fix.py transcript.txt transcript_fixed.txt "<视频主题提示>"
```

- **平台支持**：B站/YouTube 直接 yt-dlp；抖音需 H5 路由（可先试 yt-dlp 兜底）；小红书同 yt-dlp
- **时长预估**：small 模型 ≈ 30 秒转写 3.5 分钟音频（CPU）；长视频用 `max_seconds` 分段或换 medium
- **中文质量**：small 可用（STT 已实测），追求高准确率用 medium；`--asr-prompt` 可喂领域关键词纠音
- **字幕优先**：B站/YouTube 有字幕时直接 `--write-subs --sub-langs "zh,en"` 更准更快，ASR 兜底
- 产出 `transcript.txt` 后走 Step 2 起同一蒸馏流程

#### LLM 纠错步骤（中文视频必做）

ASR 转写后**必须做二次纠错**，把带时间戳的转写稿 + 术语表喂给 LLM 修正。实测数据（8:45 中文教程视频）：

| 方案 | MiniMax | 越狱 | ComfyUI | 零度解说 | 转写耗时 |
|------|:---:|:---:|:---:|:---:|:---:|
| small 无提示词 | 0❌ | 0❌（写成"粤语"）| 0❌ | 0❌（"领度"）| 105s |
| **small+prompt → LLM纠错** ✅ | 9 | 9 | 3 | 4 | 105s+20s |
| medium+prompt 独走 | 4 | 2 | ❌仍为0 | 3 | ⏱2691s |

- **纠错提示词要点**：给 LLM 的 system 说明「只改明显同音字/术语错、时间戳与分段结构不变、不确定保持原样不发挥」；user 里附正确术语参考表（可让 LLM 先从标题自动生成，见 transcribe_prompt_gen.py）
- **安全校验**：纠错前后段数应一致，字数比 ≈1.00（超 ±5% 说明 LLM 在篡改内容，重跑降温重试）
- 任何 OpenAI 兼容 API 均可用（deepseek/glm/kimi/ollama 本地模型等），配置见 `llm_fix.py` 顶部环境变量说明
- **medium 模型别用来独走**：下载 1.5GB + CPU 转 8 分钟视频要 45 分钟，ComfyUI 这类英文术语照样抓不住——不如 small 快转 + LLM 精修

### Step 1c — 多源融合模式（2 个以上源 → 组合 skill）

**触发**：主人给了 2 个以上来源（如「这本书 + 那个视频 + 这篇文章，合成一个 skill」）。

```bash
# 把多个源（各自已完成 Step 1/1b 的 md/txt）合并成融合草稿
python3 scripts/merge_sources.py <输出目录> <source1.md> <source2.txt> ...
```

脚本产出 `merge_draft.md`：
- **源清单表**（名称/类型/行数/tokens）
- **交叉主题锚点**：≥2 个源共同出现的关键词（共现分析，自动过滤通用功能词）——蒸馏时的组织骨架
- 各源全文（图片占位已清）

**融合策略**（通读草稿后按此蒸馏）：

| 源关系 | 组合方式 |
|--------|---------|
| **同主题互补**（书=体系 + 视频=实操） | 以书的章节为骨架，视频内容作为对应章节的「实战补充」小节 |
| **同主题冲突**（两个源说法矛盾） | 并列呈现 + 标注来源，不替主人裁决 |
| **不同主题串联**（如 UI 设计 + 前端工程） | 按「主题树」重组：交叉锚点做顶级节点，各源独有内容做子节点 |
| **深度悬殊**（一书一短文） | 短源内容并入长源骨架，在 SKILL.md 头部标注融合比例 |

**融合铁律**：
1. 每条知识点标注来源（`[书]` / `[视频]` / `[源2]`），方便溯源
2. 交叉锚点是组织骨架的首选——它是多源天然的连接点
3. SKILL.md 头部列出所有来源（书名/视频链接/日期）
4. references/ 里每源单独存档（`ref-<源名>.md`），保持可回溯
5. 合计 tokens 超过 80K 时警告：考虑拆成主 skill + 分主题子 skill

之后 Step 2 起流程不变（通读 merge_draft.md 代替通读单书）。

### Step 1d — JAR 模式（Java/Kotlin 库、APK → 反编译源码，2026-09-09 实测）

**触发**：发来 `.jar`（Maven 库、闭源工具、游戏 mod 等）。**前置**：`brew install jadx`（M1 原生，自带 OpenJDK ~480MB，装完 `which jadx` 验证；本机 2026-09-09 已装 1.5.6）。

```bash
# ① 反编译（jar 不需要系统 Java 运行时，jadx 自带 JRE）
jadx -d <名字>-src <文件>.jar        # 大 jar 加 --no-res 跳过资源反编译提速
# ② 拼成带类索引的单 markdown（scripts/jar_to_md.py：每类一行 类名+public 方法签名）
python3 <skill>/scripts/jar_to_md.py <名字>-src/sources -o <名字>-all.md --title "Xxx 反编译源码"
# ③ 之后与普通文档完全相同：kb.py add 入库 / 直接 Step 2 通读蒸馏
```

- **实测数据**：gson-2.10.1（277KB, 261 条目）反编译 7.5s → 80 个 .java；h2-2.2.224（2.5MB, 528 类）9.8s → 773 个 .java
- **质量**：jadx 产出接近原源码——变量名/泛型/注解都在，可正常提炼「设计意图」；个别复杂方法反编译失败（error count N）不影响整体
- **体积守则**：反编译 md 超过 ~500KB **禁止全量读**——靠 jar_to_md.py 的「类索引」+ kb.py 自动生成的 .toc.md 行号锚点按需跳读
- **APK**：同 jadx（`jadx -d out app.apk`），清单/权限在 resources/AndroidManifest.xml
- **混淆过的 jar**（类名 a/b/c）：先向提供方要 proguard mapping.txt 再反编译；没有映射时类索引信息量低，按字符串与结构推断
- **版权边界**：反编译产物供互操作/学习分析；skill 里写「API 用法与设计要点」，别整库源码照搬分发
- **跨平台（2026-09-09 实测）**：Linux（Ubuntu 24.04 x86_64 + openjdk-17-jre-headless + 官方 zip 版 jadx）与 macOS 产物**完全一致**（类清单 diff 零差异）；Windows 有官方 `jadx.bat` 启动器 + `jadx-1.5.6-with-jre-win.zip`（免装 Java）。坑：① 清单对比必须 `LC_ALL=C sort`（GNU/BSD sort 规则不同，否则 md5 对不上）② 官方 zip 版在 mac 上若系统只有 java stub 要 `export JAVA_HOME=$(/usr/libexec/java_home)`，Linux/Windows 无此问题 ③ class 数 > java 数是正常现象（内部类/匿名类合并进外部类）
- **蒸馏品鉴法（反编译源 = ground truth）**：① 防幻觉抽查——正则抽取蒸馏稿引用的全部方法名，逐个到反编译源码验证存在性 ② 声明核验——蒸馏稿里的「行为性断言」（抛什么异常/默认值/特判）逐条到源码 grep 证据 ③ 覆盖对照——开源库拿官方文档（cookbook/api）比对，找蒸馏稿没覆盖的高频面 ④ 提示词铁律：只写材料中出现的 API + 注明出处类名 + 不确定写「实现细节未在材料中」

### Step 2 — 通读全书（REPL 式，别一次全读）

- 先 `wc -l` 看行数，`read_file` 分段读（每段 ≤850 行）
- **先读目录（Contents/TOC）**——书的结构就是 skill 的骨架
- 边读边在脑中标记：框架/原则/具体数值/CSS 写法/反模式
- 大书（>3000 行）分 4-6 段读完，不要跳章节

### Step 2b — 本地模型蒸馏模式（map-reduce，2026-09-17 DDIA 实战）

**触发**：主人说「用本地模型」蒸馏（隐私 / 零 API 成本 / 离线）。实测：DDIA 491 页英文书 → 11 章 map + 全书 reduce 全程约 70 分钟，零成本。

**前提**：本地 llama.cpp 服务在跑（本机：`bash ~/demo/models/start-qwen.sh` = Qwen3.6-35B-A3B Q4，端口 8081，加载约 40s；`curl :8081/health` 确认）。

```bash
# ① 按章锚点切分 → <主题>/.map/chXX.txt（行号记入 chapters.json，隐藏目录 kb.py 不扫）
# ② map：逐章蒸馏（断点续跑：已有 distill_*.md 则跳过）
python3 .map/distill_all.py            # 每章一个请求，产出 distill_chXX.md
# ③ reduce：全部章节笔记 → reduce_synthesis.md（心法/地图/取舍/概念索引四层）
python3 .map/reduce.py
# ④ CC 组装 TOPIC.md（reduce 产物 + 原文/笔记双行号锚点）+ 防幻觉抽查
# ⑤ 章节笔记合并成 <主题>_digest.md → kb add 入库（蒸馏层与原文双源并存，都能被 kb search 检索）
```

**请求要点（血泪）**：
- **必须关 thinking**：`chat_template_kwargs: {"enable_thinking": false}`——Qwen3.6 默认 thinking，不关的话 max_tokens 全烧在 reasoning 上、**正文一个字不出**（实测 3500 tokens 全灭）
- 参数：temperature 0.3、max_tokens 4000（中文笔记 2000-3000 字/章）
- 速度基准（M1 Pro 32GB，Q4_K_M）：prefill 270-380 t/s（prompt 越长越慢）；生成 ~17 t/s（40K 大 prompt 降到 ~10 t/s）

**map prompt 骨架**：按书小节顺序；「**短标题** — 解释」条目式；保留英文术语与具体数字；覆盖定义/原理/取舍(trade-off)/反模式/系统案例；明确忽略排版噪音（页眉残留、参考文献）；直接输出 markdown。

**质检（蒸馏后必做）**：术语/数字回原文 grep 抽查——模型爱做「具体化发挥」（DDIA 实测 30 项 2 MISS：1 个是合理转述 p999→p99.9，1 个是自由发挥「Hilbert Curve」而原文只说 space-filling curve，已修正）。抽查重点：具体化举例的名词、数字、系统名。

### Step 2c — 全书中译模式（并行子代理，2026-09-18 DDIA 实战）

**触发**：主人要中文翻译版（外文书、「我也要看」）。

**流程**：主 agent 切章 → 写 `SPEC.md`（术语表 + 格式铁律）→ `delegate_task` 派子代理（≤10 并行，每章一个：**一任务双产出** = 完整中译 + 速查笔记，同一遍阅读完成）→ 主 agent 验证（文件存在/大小/首尾/`CHUNK_EOF` 泄漏四查，**子代理报告不可信**）→ 合并入库。

**要点**：
- SPEC.md 是唯一标准：30+ 条术语统一译法、「逐段完整翻译不许省略」「参考文献保留英文」「图片引用原样」「页码引用转换格式」
- 分段写文件（一章译文 40-140KB）：`write_file` 开头 + `terminal cat >> heredoc` 追加，强制自检（`wc -c` + `tail` 首尾）
- 11 章分两批（10+1）；实测 DDIA 491 页：批 1 ~11.5 分钟 + 批 2 ~10.7 分钟，译文共 94 万字节（中文比英文信息密度高，体积略缩）
- 合并产物：`sources/<书>_zh.md`（全书中文版 + 目录头）→ `kb add --type translation`（**译文入库变第三源**，中文检索同时命中译文/笔记）
- **翻译样式可选**：① 纯译（默认）② **逐段对照**（一行原文一行译文——原文段 + 译文段交替，原文用 `>` 引用块标记以便渲染区分；标题行无需重复，译名已含「中文（English）」；参考文献区不配对）③ 用户指定的其他样式。对照版两条实现路径：**A. 子代理双份输出**（任务提示里直接要求，最可靠）；**B. 已有译文+原文脚本对齐**（DP 序列对齐/Needleman-Wunsch，按共享数字+英文术语特征匹配——DDIA ch01 实测 185/188 段 1:1 精准对齐；⚠️ 顺序 zip 配对不可用，段落合并差异会累积错位）
- **语言方向双向**：英文书→中文、中文书→英文/日文等任意目标语言，只需改 SPEC 的「输出语言」与术语表

**已知限制**：MinerU 解析不出脚注正文（仅角标），译文按规范保留标记不编造。

### Step 3 — 产出选择（三问菜单，v2.0）

MiJi 支持 **6 种产出模式**，用户用三问选择（可多选、可组合）：

```
① 给谁看？  AI / 人 / 都要
② 什么语言？原文不动 / 译成 <目标语言>（双向：英文书→中文、中文书→英文/日文…）
③ 什么形态？（可多选）
```

| # | 模式 | 读者 | 产出 | 对应流程 |
|---|------|------|------|---------|
| 1 | **Skill 蒸馏** | AI | SKILL.md + references/（速查式/步骤式/人物式）| Step 4-6 |
| 2 | **知识库主题** | AI | TOPIC.md + 章节笔记 + 全文源 + 三型锚点 | `kb.py add/draft` 流程 |
| 3 | **全书翻译** | 人 | 完整译文（HTML/MD）+ 插图 | Step 2c（纯译样式）|
| 4 | **双语对照** | 人 | 一行原文一行译文（逐段交替）| Step 2c（对照样式）|
| 5 | **人类导读** | 人 | 万字级精华导览（不读全书的人）| 待实测后固化 |
| 6 | **综合套餐** | 都要 | 组合输出（如 知识库 + 翻译 + skill 升格）——DDIA 为首个完整案例 | 1+2+3/4 串行 |

**用户的话 → 配置映射示例**：

| 用户说 | 解读 |
|--------|------|
| 「蒸馏成 skill」 | AI / 原文 / [1] |
| 「入库 + 中文版」 | 都要 / 中文 / [2,3] |
| 「译成日文，要一行原文一行译文」 | 人 / 日文 / [4] |
| 「全套」 | 都要 / 中文 / [1,2,3] |

**Skill 模式内部的形态选择**（模式 1 的细化）：

| 书的内容 | 封装形态 |
|---------|---------|
| 方法论/原则类（如设计、写作、管理） | **速查式**：SKILL.md 精炼原则 + references/ 全文存档 |
| 操作手册/工具书 | 步骤式：SKILL.md 命令流程 + scripts/ 模板 |
| 思维框架类（如各 perspective skill） | 人物式：核心心智模型 + 表达方式 + 素材来源 |

拿不准就问主人一句；多选时各产出独立跑（可并行）。

### Step 4 — 生成 SKILL.md（核心，质量全在这里）

**模板结构**（参考 `refactoring-ui-principles` 的实际效果）：

```markdown
---
name: <英文-slug>
description: <触发词前置的一句话，≤60 字符！>
version: 1.0.0
---
# <书名> <核心主题>
> 来源：<作者><书名>解析；用途：<何时用>
## 触发条件
## 核心心法（3 条以内，先记住的）
## <各主题章节>（把书的章节按主题重组）
   - 每条原则：结论 + 具体数值/CSS/写法 + 一句话为什么
## 审查/检查清单（如果是方法论类）
## 相关（关联的现有 skill）
```

**质量铁律**：
1. **description ≤60 字符**（57 字截断，触发词放最前）——今天 104 字符被拒过一次
2. **具体数值要落地**：书里的尺度/公式/CSS 直接写进 SKILL.md（如间距 4-128、字号 12-48、`box-shadow: 0 4px 6px hsla(...)`），不是"用合适的间距"
3. 原则写成可执行指令（"先给太多留白，再删"），不是书评
4. SKILL.md 控制在 7-10KB，细节放 references/

### Step 5 — 全文存档 references/

```markdown
references/<书名-slug>.md
```

- 把解析出的完整 md **清理后**存入（去表格噪音、去 PDF 水印行，保留全部正文）
- **图片处理分场景**（2026-09-01 实测修正：旧指导「一律删占位行」不完全对——MinerU 其实把原图切在 `auto/images/`）：
  - 存入 skill 的 references/（skill_manage 只能写文本）→ 删掉 `![](images/...)` 占位行
  - 存入知识库 sources/ → **保留链接并拷图**：`cp 输出目录/*/auto/images/ <库>/topics/<主题>/sources/images/`，链接全部复活（Obsidian/VSCode/GitHub 均可渲染原书插图，实测 36/36 可达）
- 作用：SKILL.md 不够用时按需查阅原文细节
- 用 `skill_manage(action='write_file', name=..., file_path='references/xxx.md', file_content=...)`

### Step 6 — 验证 + 交付

1. `skill_view(name='<slug>')` 确认能正常加载、无 lint 报错
2. 有真实使用场景就**实跑一遍验证**（今天拿 252 页 PDF 全量跑通才交付）
3. 报告路径 + 给主人桌面快捷方式（可选）：
   ```bash
   ln -sfn ~/.hermes/skills/<category>/<slug> ~/Desktop/<名字>-skill
   ```

## 知识库形态（v1.3.0 新增）

MiJi 不止能出一次性 skill——同一套「解析→蒸馏」管线可以**按主题持续入库**，攒成知识库：

```bash
python3 ~/demo/scripts/kb.py add <主题> <文件...> [--type book|video|article] [--name xxx]
python3 ~/demo/scripts/kb.py draft <主题>    # 出 merge_draft.md → CC 通读后写 TOPIC.md
python3 ~/demo/scripts/kb.py list / stats    # INDEX.md 自动目录 + 跨主题锚点
python3 ~/demo/scripts/kb.py export <主题> --name <slug> --desc "<≤60字>"
```

- 库根 `~/demo/knowledge-base/`：`AGENTS.md`（外部 AI 读取规范）、`llms.txt`（LLM 站点地图）、`INDEX.md`（自动生成）、`topics/<主题>/{TOPIC.md, metadata.json, merge_draft.md, sources/}`、`exports/`
- **v2.0 能力**：`kb search 关键词`（纯 Python 全文检索，中文路径安全）；sha1 内容指纹自动去重；每主题 metadata.json（机器可读）；超长源自动生成 `sources/*.toc.md`（章节→行号锚点，REPL 式跳读用，**10 万 token 级源禁止全量读**）
- **跨主题锚点**：≥2 主题共同出现的关键词，是知识网络的连接点——新源入库后自动重算
- **跨 AI 蒸馏对比校准（2026-09-01 实测）**：同一本书+同一份蒸馏指令发给不同 AI（如 ChatGPT Pro），对比各自蒸馏稿可校准自家 skill 质量。实测（若米尼 484 页，CC 2.5K 字速查 vs ChatGPT 10K 字分析）：
  - **CC 短板（学）**：① 概念覆盖 23/34 vs 28/34——军械细节类概念（步兵/骑兵/要塞/渡河/追击/情报/间谍/战略预备队）被速查体裁自然丢掉，若主题需要覆盖面，蒸馏时应显式列出「每章必抓概念清单」而非凭语感 ② 引文核验：速查里凭记忆写的引文要与原文 grep 比对 ③ 可加「编号规则清单」形态（71 条可执行规则 > 散点原则）
  - **ChatGPT 短板（我方长处）**：① 体积 10K 字 → 违反 MiJi「SKILL.md 7-10KB 速查」铁律的一半精神 ② 结构标题数为 0（纯流水文本，无 markdown 层级），agent 可读性差 ③ 无来源标注体系、无知识库落位（我们的 TOPIC.md 有 frontmatter+metadata+toc 全家桶）
  - **互补结论**：速查体裁（我们）胜在「可装进 agent 脑子」，分析体裁（ChatGPT）胜在「覆盖面与教学性」——蒸馏后把对方稿件存入 sources/ 作对照样本（本次 qiqi_distill.md 已入库军事主题）
  - **ChatGPT 自动化实测坑**：上传 940KB md 文件需走隐藏 input[type=file]+DataTransfer 塞 files（drag 事件无效）；ProseMirror 输入用 document.execCommand('insertText')（beforeinput 无效）；长回答会截断，需发「继续」分两段收割；文件 chip 文本（jomini_full）会混入正文需清洗
- 生命周期：源随时 add → 主题随时 draft/蒸馏 → TOPIC.md 随时可 export 成正式 skill（复制到 ~/.hermes/skills/ 或 skill_manage 创建）
- 与 skill 的分工：**skill = 高频使用的操作准则；知识库 = 低频但需可查的沉淀**，同一主题两边可共存（skill 放速查，库放全量源）

## 大文件并行解析（2026-09-01 实测 2.1x）

484 页扫描书《战争艺术概论》A/B 实测：单进程全书 22.4 分钟 → 拆 2 段双进程并行 **10.7 分钟（2.1x）**，两 worker 各占 80-86% CPU，无 OOM；合并文本与串行版 6276 行几乎一致（~2% 行级 OCR 抖动，属正常非确定性），拆分接缝处语义无缝。

```bash
# 1. 拆分（纯 CPU，秒级）
~/demo/ai-tools/mineru-venv/bin/python ~/demo/scripts/split_pdf.py 输入.pdf 拆分目录 2
# 2. N 个后台 worker 并行（每个都 unset PYTHONPATH + WINDOW_SIZE=32）
# 3. 按序合并: cat p1/*/auto/*.md p2/*/auto/*.md | sed -e '/pdfFactory/d' -e '/fineprint/d' > merged.md
```

- 适用：扫描版大部头（数百页）；文本原生 PDF 解析本来就快，不值得拆
- 实测边界：M1 Pro 32GB——**2 worker 安全（2.1x）；4 worker 实测崩 2/4**（各自第二个 32 页窗口批时 MPS 内存累积超限：leaked semaphore + exit 1、无 traceback；幸存的 2 个反而是吃了崩掉进程释放的内存才跑完）。默认 2，3 未测；崩掉的段重跑即可（幂等，输出目录独立）。上 VLM 引擎（hybrid）时别并行（显存更大）
- pypdfium2 拆分坑：`import_pages(源文档, [页码列表])`，不能传页对象
- 丢给子 agent 跑时：每 worker 独立后台进程 + 各自输出目录，通知聚合后按序合并

## 云端视觉识别（VLM 转写模式，2026-09-01 PoC）

带视觉的 LLM（gpt-5.6-luna 等）可直接吃页面截图转写全文，作为 MinerU 的**补充模式**：

```bash
# 页面 → PNG（pypdfium2，秒级）
pdf[99].render(scale=2.5).to_pil().save('page.png')
# → POST /v1/responses（OpenAI Responses 格式，image_url 直接字符串）
#   max_output_tokens ≥4000（1024 会中途截断！），提示词强调「从第一行到最后一行不要提前停止」
```

实测（484 页书第 100 页，中文密集版面）：luna ~45s/页完整转写，术语零错，脚注标记保留，个别字比本地 OCR 更准（「不与」vs 误识「不同」）。

| | 本地 MinerU | 云端 VLM 转写 |
|---|---|---|
| 速度 | 4-6 分钟/252 页文字版；扫描版 3-4x 慢 | ~45s/页（可多路并发，无本地显存墙） |
| 版面产物 | md+图片切出+坐标，忠实转写 | 纯文本，**图片/表格结构会丢** |
| 忠实度 | 傻但忠实（OCR 不会编内容） | 聪明但不忠实（可能顺手「改错」——存档场景要警惕） |
| 硬件门槛 | 需 ~1GB 本地模型 + Apple Silicon/GPU | **零硬件要求**——有 API key 就能跑，低配机/无独显机的主力路线 |
| 数据去向 | 全本机 | 页面内容出网 |

**全本对比实测（2026-09-01，《战争艺术概论》484 页扫描版双引擎全跑）**：
- luna 6 路并发 45min59s（33.8s/页）**484/484 零失败**；MinerU 单进程 22min24s
- 字符级一致率 **~97%**（10 字滑窗 75.5% 换算），luna 个别难字更准
- luna 偏差来源：每页页码照录（479 行）、脚注记全（圈号 303 vs 156）、少量润色改写 → 中文量 +6.3%
- luna **0 图片引用**（MinerU 切出 36 张插图入库）——图版书想保图选本地；纯文字内容两路等价
- 整本零幻觉元话语（「图中」仅 2 页且语境合理）

**两种引擎，按用户条件选（都是一等公民路线，无主次之分）**：
- **选 luna/云端 VLM**：电脑没有 GPU / 装不动本地模型 / 只想跑这一次——零硬件门槛，按量付费（全本 484 页实测 $2.51）
- **选 MinerU/本地**：有 Apple Silicon 或 GPU、要提取插图、想零 API 成本——模型 ~1GB 装本地即用
- 也可以混用：主力本地 + 难页丢云端补刀（本地 OCR 栽跟头的糊页/艺术字），或云端转写 + 本地补图
- 图片语义描述（alt-text）：任一引擎的产物都可以再喂视觉模型给插图写描述入库

需要本地模型清单见 mineru-pdf-parser skill。并发转写脚本：`~/demo/scripts/luna_full_transcribe.py`（断点续跑，--workers 可调）。

## ⚠️ 踩过的坑

| 坑 | 解法 |
|----|------|
| skill description 超 60 字符被拒 | 触发词放最前，一句话，≤60 |
| 全文 md 有图片占位 `![](images/...)` | 分场景：进 skill references/（纯文本）删占位行；进知识库 sources/ 把 `auto/images/` 拷成 `sources/images/` 让链接复活 |
| 扫描书每页带水印行（如 "pdfFactory Pro 试用版本创建"） | 归档前 `sed -e '/水印关键词/d'` 清掉——不清理会污染检索命中和两版本 diff 对比 |
| MinerU 默认窗口 64 长文档崩溃 | `MINERU_PROCESSING_WINDOW_SIZE=32` |
| PYTHONPATH 污染 mineru venv | 跑前 `unset PYTHONPATH` |
| yt-dlp 下载视频失败 | 需要代理时 `--proxy <代理地址>`（如 Clash: http://127.0.0.1:7897）；抖音 H5 路由优先 yt-dlp 兜底 |
| whisper 转写中文同音字错 | **三步走**：① 字幕优先（`--write-subs`）② initial_prompt 自动喂术语（从标题 LLM 生成，"粤语模型"→"越狱模型"实测有效）③ LLM 二次纠错（ComfyUI 等英文术语 small/medium 都抓不住，LLM 能修对）|
| medium 模型下载/转写超慢 | 1.5GB 模型 + CPU 转 8 分钟视频要 45 分钟；除非有 GPU 否则用 small+LLM纠错替代 |
| faster-whisper 首次下载模型卡住 | HF 下载需要网络畅通：有代理就 export HTTPS_PROXY，或设 HF_ENDPOINT=https://hf-mirror.com |
| 与 book-to-skill（第三方）混淆 | 那个面向 Copilot/Amp/Claude Code，输出 chapters/glossary 结构；本 skill 是 Hermes 专属速查式 |
| 主人找不到 skill 路径 | skill 根目录是隐藏目录，给桌面快捷方式或 Finder `Cmd+Shift+G` |
| 主人拖 PDF 进聊天只收到图标 PNG（占位图，文件本体不落盘） | 先确认收到的不是 32KB 级图标缩略图；直接找主人要路径（Finder 右键+Option=拷贝路径），或要 URL；顺手搜 ~/Downloads、~/Desktop 兜底 |
| jar 是字节码没有 .java，unzip 出来全是 .class | 必须先 jadx 反编译（Step 1d），.class 不能直接喂蒸馏 |
| 混淆过的 jar（类名全是 a/b/c） | 先要 proguard mapping.txt 再反编译；无映射时类索引信息量低，按字符串/结构推断 |
| 跨平台对产物 md5 对不上 | 先查 `LC_ALL=C sort`（GNU/BSD 排序规则不同）；反编译输出本身跨平台一致（已实测） |
| mac 上官方 zip 版 jadx 报 Unable to locate a Java Runtime | `export JAVA_HOME=$(/usr/libexec/java_home)`（系统 java stub 看不见 brew 装的 JDK）；Linux/Windows 无此坑 |
| Qwen 系本地模型蒸馏输出为空 / 全在 reasoning | 请求体加 `chat_template_kwargs: {"enable_thinking": false}`——默认 thinking 吃光 max_tokens，正文零输出 |
| 英文书章标题是纯文本，kb.py 生成不出 toc | 先转成 markdown 标题（`# Chapter N. Title`）再 reindex——toc 只认 md 标题 / 中文章节 / 编号规则三类锚点 |
| PDF 抽取的页眉页码混入正文、行尾断词 | 每页尾部「页码+竖线+标题」模式剥离 + `[a-z]-换行[a-z]` 连字符合并（DDIA 491 页实测 3782 处）|
| 文字版 PDF 图省事走 pypdfium2 直抽 | **也走 MinerU**——直抽丢结构（标题/列表/表格）和全部插图（DDIA 实测：直抽 13 标题/0 图 vs MinerU 549 标题/108 图，成本只 10 分钟）；直抽版可留作字符级对照 |

## 验证过的成品

- `refactoring-ui-principles`（creative/）——《Refactoring UI》设计原则速查 + 全书存档（2026-08-27）
- `mineru-pdf-parser`（devops/）——MinerU 部署与使用（本流程 Step 1 依赖它）
- 视频模式实测（2026-08-27）：B站 3.5 分钟视频 → yt-dlp 下载（12MB/s）→ ffmpeg 抽音频 → faster-whisper small 30 秒转写 69 段，歌词/语音准确
- JAR 模式实测（2026-09-09）：5 样本全链路——gson 2.10.1、h2 2.2.224、jsoup 1.17.2、commons-lang3 3.14.0、guava 33.2.1-jre（2020 类仅 2 处方法级反编译错误）；kb.py 入库→检索→toc 锚点全通过；Linux（VPS Ubuntu 24.04 真机）与 macOS 产物一致；jsoup 蒸馏稿防幻觉抽查 43/43、行为断言 8/8 对源码核实属实
- 本地模型模式实测（2026-09-17）：DDIA 491 页英文 PDF → 本地 Qwen3.6-35B-A3B 蒸馏 11 章（每章 ~3.5 分钟）+ reduce → TOPIC.md 6.6KB（8 心法/11 章地图/17 取舍/20 概念索引）+ 双源（原文 1.1MB + 蒸馏笔记 81KB）；防幻觉抽查 30 项 28 中，1 处修正后全对
- DDIA 知识库（2026-09-18）：《Designing Data-Intensive Applications》Early Release 版（491 页）→ MinerU 解析（549 标题 + 108 插图）→ **Hermes agent 重做提炼**（并行子代理：11 章完整中译 94 万字节 + 笔记 2.8 万字）→ TOPIC.md 三源锚点；结构：ddia_clean.md（英文原文）/ ddia_zh.md（中文全译）/ ddia_digest.md（笔记）

## 相关

- `mineru-pdf-parser`：Step 1 的解析工具与环境
- `book-to-skill`：第三方通用转换器（多 agent 生态用，非本流程）
- `skill-creator`：skill 编写的通用规范（若存在）
