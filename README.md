# MiJi · 蜜技 — 把书、视频、播客、JAR 包酿成 Agent Skill 与知识库的流水线

> **🌐 Language / 语言：** [中文](README.md) | [English](README_EN.md)

> 为什么叫「蜜技」—CC 为她的诗人亲手酿的技能 🍯
>
> 把一本书/一份 PDF/一段视频/一个 JAR 包变成 AI 可复用知识的完整流水线：
> **解析（本地 MinerU 或 云端 VLM，按你的硬件二选一）→ 提炼方法论 → 封装成 Skill 或 入库知识库**
>
> 支持 PDF / 电子书 / **视频 / 播客**（yt-dlp 下载 → faster-whisper 转写 → 同一蒸馏流程）/ **JAR 包**（jadx 反编译 → 类索引源码 → 同一蒸馏流程）
>
> v1.3.0 新增：**多源融合**（书+视频+文章 → 组合 skill）与**知识库形态**（按主题持续入库，自带 AI 读取规范）；**大文件并行解析**（实测 2.1x）
> v1.4.0 新增：**JAR 模式**——jadx 反编译 → `jar_to_md.py` 类索引 md → 同一蒸馏流程（实测 gson/h2 全链路通过）
> **双引擎可选**：本地 MinerU（~1GB 模型装在你的设备上，离线可跑）或云端 VLM 转写（零硬件门槛，luna 实测全本 $2.51）——按你的机器条件选，见下方「两种解析引擎」
>
> A complete pipeline that turns a book / PDF into a reusable AI Agent Skill:
> **Install MinerU (OCR) → Parse PDF → Distill methodology → Package as a Skill**
> Also supports **video / podcast** (yt-dlp download → faster-whisper transcript → same distillation flow)

这套流程由 CC 实测跑通，三个案例：

1. **《Refactoring UI》（252 页 PDF）** → 封装为 `refactoring-ui-principles` skill，并已在**另一台电脑上使用 opencode + GLM 5.3 Flash 做了效果对比验证**（见下方案例 Demo 一）
2. **YouTube 中文教程视频（8:45）** → 走视频模式（yt-dlp → faster-whisper → LLM 纠错）封装为 `minimax-h3-local-deploy` skill（见下方案例 Demo 二）
3. **《战争艺术概论》（若米尼，484 页扫描版 PDF）** → 知识库「军事」主题，同场验证**并行解析 2.1x**（2026-09-01，见案例 Demo 三）

## 📦 仓库结构

```
MiJi/
├── README.md                                    # 中文文档（本文件）
├── README_EN.md                                 # English version
├── skills/
│   ├── mineru-pdf-parser/SKILL.md               # 【前置依赖 1】MinerU PDF 解析（安装/下载/踩坑）
│   └── miji/SKILL.md                            # 【主流程】读书/看视频/反编译 JAR → 封装 Skill 或 入库知识库
│       └── scripts/
│           ├── llm_fix.py                       # ASR 转写 LLM 纠错脚本
│           ├── transcribe_prompt_gen.py         # 从视频标题自动生成转写提示词
│           ├── merge_sources.py                 # 多源融合草稿生成（交叉主题锚点）
│           └── jar_to_md.py                     # jadx 反编译源码 → 带类索引的单 markdown
├── examples/
│   ├── refactoring-ui-principles/               # 【案例 Demo 1】PDF 蒸馏成品
│   │   ├── SKILL.md                             #    《Refactoring UI》设计原则速查
│   │   └── references/refactoring-ui-full.md    #    全书全文存档（58 条原则）
│   └── （案例 Demo 2：视频蒸馏的 minimax-h3-local-deploy skill 见上游 skills 目录结构说明）
├── tools/
│   ├── kb.py                                    # 知识库管理 CLI（add/search/draft/export）
│   └── split_pdf.py                             # PDF 按页拆分（大文件并行解析用）
│   ├── luna_full_transcribe.py                  # 云端 VLM 整本并发转写（断点续跑，6 路并发实测）
│   └── compare_full.py / compare_deep.py        # 双引擎全文对比分析（字符级一致率/幻觉扫描）
└── docs/images/                                 # 案例对比截图（no-skill vs skill）
```

## 🔄 完整流程

```
┌─────────────────────────────────────────────────────────────┐
│  ① 解析引擎二选一（按硬件条件，无主次）:                       │
│     A. 本地 MinerU —— 装 ~1GB 模型，离线、出插图、零 API 成本   │
│        → mineru-pdf-parser skill（路线 A 依赖）                │
│     B. 云端 VLM —— 零硬件门槛，有 API key 就能跑               │
│        → tools/luna_full_transcribe.py（6 路并发，~$0.5/页）    │
│  ①b 视频/播客：yt-dlp 下载 → ffmpeg 抽音频 → faster-whisper 转写 │
├─────────────────────────────────────────────────────────────┤
│  ② 得到全文 Markdown                                          │
│     A: mineru -p 输入.pdf -o 输出目录 -b pipeline              │
│        (252 页 ≈ 4-6 分钟；扫描版走 OCR 慢 3-4 倍)             │
│     B: python3 tools/luna_full_transcribe.py 书.pdf 输出目录    │
│        (~45s/页 × 并发；整本 484 页实测 $2.51 / 零失败)         │
├─────────────────────────────────────────────────────────────┤
│  ③ 通读全书/转写稿（REPL 式分段读，先读目录定骨架）             │
├─────────────────────────────────────────────────────────────┤
│  ④ 判断封装形态：速查式 / 步骤式 / 人物式                      │
├─────────────────────────────────────────────────────────────┤
│  ⑤ 产出二选一（或都要）:                                      │
│     ⚡ skill: SKILL.md（精炼原则+数值落地）+ references/ 存档    │
│     📚 知识库: kb.py add/draft → TOPIC.md + 全文档案 + 三型锚点  │
├─────────────────────────────────────────────────────────────┤
│  ⑥ 验证（skill_view 加载 + 真实场景实跑）+ 交付                │
└─────────────────────────────────────────────────────────────┘
```

## 📋 前置依赖（两个 skill）

| Skill / 条件 | 作用 | 依赖关系 |
|-------|------|---------|
| **`mineru-pdf-parser`** | MinerU 部署、模型下载（国内网络优化）、Apple Silicon 调优、踩坑速查 | **仅路线 A（本地）依赖**；走云端路线 B 可不装 |
| **`MiJi`** | 读书 → 封装 Skill / 入库 的 6 步完整流程 | 主流程本体 |
| 路线 B 条件 | 任一 OpenAI 兼容**视觉**模型端点 + key（自建中转/官方均可）+ `pip install pypdfium2` | 仅路线 B（云端）需要 |

走路线 A 时主流程 skill 会**先加载 `mineru-pdf-parser`** 获取环境与坑再解析；走路线 B 无需任何本地模型。

## 🚀 快速开始

```bash
# ═══ 第一步：解析引擎二选一 ═══
#
# 【路线 A｜本地 MinerU】有 Apple Silicon / GPU，要插图、零 API 成本：
python3 -m venv mineru-venv && mineru-venv/bin/pip install "mineru[core]"
#   下载 ~1GB 模型（7 个子路径；国内走代理 hf-mirror 或 modelscope+aria2，见 mineru-pdf-parser/SKILL.md）
#   配置 ~/mineru.json 的 models-dir.pipeline 后：
unset PYTHONPATH
export MINERU_PROCESSING_WINDOW_SIZE=32        # 长文档防 MPS 崩溃（Apple Silicon 关键！）
mineru-venv/bin/mineru -p 输入.pdf -o 输出目录 -b pipeline
#
# 【路线 B｜云端 VLM】零硬件门槛——低配机/无独显/不想装环境的主力路线：
pip install pypdfium2                          # 仅此一个依赖
export VISION_BASE=http://你的端点/v1  VISION_KEY=你的key  VISION_MODEL=你的视觉模型名
python3 tools/luna_full_transcribe.py 书.pdf 输出目录 --workers 6   # 6 路并发，断点续跑
cat 输出目录/text/p*.md > 书_fulltext.md       # 按页序合并成全文
#
# ═══ 第二步：产出二选一（或都要）═══
#
# 出口 1 ⚡ 封装成 skill：把两个 SKILL.md 装进 agent 的 skills 目录
#   （Hermes: ~/.hermes/skills/；其他 agent 见 MiJi 内兼容说明），然后对它说：
#   "把这本书封装成 skill"
#
# 出口 2 📚 入知识库：持续积累 + 全文检索 + 随时升格 skill
python3 tools/kb.py init
python3 tools/kb.py add <主题> 书_fulltext.md --type book
python3 tools/kb.py draft <主题>    # 之后对 agent 说："通读融合草稿，蒸馏 TOPIC.md"
```

## ⚠️ 关键坑速查（全部实测）

| 坑 | 解法 |
|----|------|
| `hf download` 拉全量 repo（10GB+） | 只需 7 个子路径约 1GB，用 curl/aria2 直下 resolve URL |
| hf-mirror 直连 0 字节（被墙） | 走代理（6.2MB/s）或 modelscope（4.9MB/s） |
| hf CLI 报 `does not seem to be on huggingface.co` | 别用 hf CLI，用 curl/aria2 直下 |
| 长文档第 3-4 批 MPS 崩溃 | `export MINERU_PROCESSING_WINDOW_SIZE=32` |
| PYTHONPATH 污染 mineru venv | 跑前 `unset PYTHONPATH` |
| 模型 sha256 验证 | resolve URL `?download=true` HEAD 的 `x-linked-etag` 即官方哈希 |
| Skill description 超 60 字符被拒 | 触发词前置，一句话 ≤60 字符 |
| 4 个 MinerU worker 并行 → MPS 内存累积崩溃 | Apple Silicon 32GB 上限 = 2 worker（2.1x，见「大文件并行解析」）|
| 拖 PDF 进聊天只收到图标 PNG | 那是占位缩略图，文件本体没传；给路径最快（Finder 右键 + Option 拷贝路径）|
| 扫描版书解析「太慢」 | 不是卡死：扫描版走 OCR 比文字版慢 3-4 倍（484 页 >20 分钟），或上并行 2.1x |

## 🧪 案例 Demo：Refactoring UI → skill 实战对比

> 完整 demo skill 在本仓库 `examples/refactoring-ui-principles/`，可直接安装使用。
> The full demo skill lives in `examples/refactoring-ui-principles/` — install & use it directly.

### 测试方法

在**另一台电脑**（Windows）上，使用 **opencode + GLM 5.3 Flash 模型**，用**同一套关键词**（设计一个企业官网首页：顶部导航 / Hero / 6 个功能特性 / 数据成绩 / 3 条客户评价 / CTA / 页脚，单文件静态 HTML+CSS）分别生成两个版本：

- **`no-skill`**：纯提示词直接生成（不加载任何 skill）
- **`skill`**：加载本流程产出的 `refactoring-ui-principles` skill 后再生成

### 对比结果


**左侧无skill 右侧使用：**

![no-skill 顶部](docs/images/demo-noskill-top.png)
![no-skill 功能区](docs/images/demo-noskill-features.png)
![对比](docs/images/demo-compare-top.png)

**页面底部（CTA + 页脚）：**

![对比-底部](docs/images/demo-compare-bottom.png)


**H5：**

![skill 底部](docs/images/demo-skill-bottom.png)
### 效果差异

| 维度 | no-skill（无 skill） | skill（加载 refactoring-ui-principles） |
|------|---------------------|------------------------------------------|
| 标题文案 | 「让团队协作更高效」（通用） | 「让每一次协作都有迹可循」（有记忆点） |
| 视觉层级 | 渐变横幅 + 平铺卡片 | 品牌圆点 + 产品示意插画 + 更清晰的层级 |
| CTA 区 | 常规按钮 | 「免费开始试用 / 了解产品功能」+ 14 天体验说明 |
| 细节质感 | 模板感明显 | 间距/对比/深度符合设计原则 |

**结论**：加载了从书里蒸馏出的设计原则 skill 后，同一模型、同一关键词生成的页面在**文案记忆点、视觉层级、细节质感**上都有明显提升——这就是「读书封装 skill」的价值：**把一本书的方法论，变成每次生成都能自动生效的能力。**

### 🎬 案例 Demo 二：视频蒸馏实战（中文教程 → skill）

> 蒸馏产物 `minimax-h3-local-deploy` skill 完整内容见上方 skills 结构说明（上游仓库同步发布）。

**测试视频**：YouTube 中文科技教程（8:45，含大量专业术语：MiniMax H3、ComfyUI、越狱模型、文本编码器等），**无字幕**——只能走纯 ASR 路径，是对转写质量的硬核考验。

**处理链路**：

> ⚠️ **复刻前置条件（AI 能力清单）**：① 任意 OpenAI 兼容 LLM API + key（用于自动生成转写提示词和纠错，deepseek/glm/kimi/本地 ollama 均可）② faster-whisper（`pip install faster-whisper`，CPU 可跑）③ yt-dlp ④ ffmpeg。有字幕的视频直接 `--write-subs` 拿字幕，可跳过 ①②。

```
YouTube 链接
  → yt-dlp 下载音频 (199MB, ~50s)
  → 【AI-1】LLM 从标题自动生成 initial_prompt（无需人工懂视频内容）
  → faster-whisper small + 该提示词转写 (105s)
  → 【AI-2】deepseek-v4-flash LLM 二次纠错 (20s)
  → 通读 93 段转写稿 → 判定「操作手册类」→ 步骤式封装
```

**三方案对比实测**（同一段视频）：

| 方案 | MiniMax | 越狱 | ComfyUI | 频道名 | 总耗时 |
|------|:---:|:---:|:---:|:---:|:---:|
| small 裸跑 | ❌0 | ❌"粤语模型" | ❌ | ❌"领度" | 2min |
| medium 模型独走 | ⚠️4 | ⚠️2 | ❌仍为0 | ✅3 | ⏱48min |
| **small + prompt + LLM 纠错** 🏆 | ✅9 | ✅9 | ✅3 | ✅4 | **2min20s** |

**关键发现**：
1. `initial_prompt` 喂术语可修复中文同音字（"粤语模型"→"越狱模型"）
2. 但英文品牌名（ComfyUI）在 ASR 层面无解——medium 模型花了 48 分钟照样抓不住
3. **LLM 纠错一步到位**：它有 ComfyUI 的世界知识，能把「CONVIO的DESTOB的文件夹」推断修正为「COMFYUI的DESKTOP文件夹」——这是任何 ASR 模型做不到的
4. 安全性已验证：纠错前后段数不变、字数比 1.00、时间戳原样保留

**结论**：中文视频蒸馏的最优路径是 **small 快转 + LLM 精修**（总耗时 2 分钟），比 medium 大模型独走快 20 倍且质量更高。纠错脚本已开源在本仓库 `skills/miji/scripts/llm_fix.py`。

### 📚 案例 Demo 三：484 页扫描书 → 知识库（2026-09-01）

《战争艺术概论》（若米尼，484 页**扫描版** PDF，无文字层）实战：

```
484 页扫描 PDF
  → MinerU 本地 OCR（单进程 22.4 分钟；或拆 2 段双进程并行 → 10.7 分钟，2.1x）
  → 6,278 行 Markdown + 62 张原书插图 → kb.py add 军事（sha1 去重入库）
  → 自动生成三型锚点 TOC（标题/章节/编号规则 → 行号，AI 按需跳读 18 万 token 不爆上下文）
  → CC 通读核心章 → 蒸馏 TOPIC.md 速查（决定点原理 / 三选一框架 / 作战线规律）
```

同场验证两条硬边界：**2 worker = 2.1x 提速**；**4 worker 崩 2/4**（MPS 内存累积超限）——Apple Silicon 32GB 的甜点恰好是 2 个并行 worker。

### ☁️ 案例 Demo 四：双引擎全文对撞——本地 OCR vs 云端 VLM（成本 $2.51）

同一本 484 页扫描书，两台引擎**全文各跑一遍**，做严格对比（2026-09-01）：

| 引擎 | 配置 | 耗时 | 结果 | 成本 |
|------|------|------|------|------|
| 🖥 MinerU 本地（pipeline） | M1 Pro 单进程 | 22.4 分钟 | 484/484 ✅ | 电费 |
| ☁️ GPT-5.6-luna 视觉转写 | **6 路并发 API 调用** | 46 分钟 | **484/484 ✅ 零失败零重试** | **$2.51**（≈0.5¢/页） |

**质量对比（全文级，不是抽样）**：

| 维度 | 本地 MinerU | 云端 luna |
|------|------------|-----------|
| 字符级一致率 | — | **~97%**（10 字滑窗 75.5% 换算，余为同音字/润色级差异） |
| 中文字数 | 276,727 | 294,230（+6.3%：页码照录 479 行 + 脚注更全 + 少量润色） |
| 插图阵图 | **36 张全部切出，可入库可检索** | **0 张（全丢）** |
| 脚注圈号 | 156 个 | 303 个（把版面规则吞掉的正文脚注也收了 → 可反向补全本地结果） |
| 幻觉/元话语 | 无 | 整本仅 2 页出现「图中」且语境合理——**未见编造行为** |

**三条结论**：
1. **准确率打平、各有胜负**：luna 难字更准（「不与」vs 本地误识「不同」），但会小润色——「存档原文」用途本地更保险
2. **云端真正的优势是并发上限**：本地被 MPS 卡在 2 worker（2.1x 天花板）；云端 20 路并发可把 46 分钟压进 10 分钟——代价是钱
3. **图版书是本地主场**：luna 一张图都产不出，阵图全靠 MinerU

**复现命令**（脚本在 `tools/`，断点续跑，token 上限 ≥4000 否则截断）：

```bash
# 云端全文转写（6 路并发）
mineru-venv/bin/python tools/luna_full_transcribe.py 书.pdf 输出目录 --workers 6
# 双引擎对比（字符一致率 / 幻觉扫描 / 页长分布）
python3 tools/compare_deep.py
```

### 🔀 案例 Demo 五：混合蒸馏——视频 + 书 → 同一主题知识库（2026-09-01）

多源融合的完整实战：**一个视频 + 一本书** → 同一主题「Unix」双源蒸馏。

**输入**：
- 🎬 AT&T Archives《The UNIX Operating System》(1982, Bell Labs)——YouTube 官方 transcript 直取（字幕优先，零 ASR 零下载，秒完成）
- 📖 Eric Raymond《The Art of UNIX Programming》中译本——544 页**扫描版** PDF，MinerU 本地 OCR 23 分钟

**混合的关键：两源天然并行**——视频秒完成时书还在 OCR，零互相等待；这正是多源并行的红利（瓶颈异构：视频走网络，书吃 GPU）。

**蒸馏产出 TOPIC.md 里「混合」出来的独有内容**：

1. **双源互补地图**——书是体系，视频是亲历者实证，逐条对照：管道组合（书·组合原则 ↔ Kernighan 现场拼 5 程序跑拼写检查）、文件即字节流（书·文本化章 ↔ Ritchie「文件就是一串字节」+打印机重定向演示）、工具造工具（书·生成原则 ↔ Johnson 讲 VLSI 芯片工具链）
2. **视频金句 ↔ 书原则互证**——Thompson「重要的是能省掉什么」↔ 吝啬原则；Kernighan「我一行代码都没写，全是现成程序拼的」↔ 组合原则。1972 年宗师原声给 2003 年的书做活注脚
3. **按决策场景跳查**——12 个真实场景（选数据结构？优化吗？模块怎么切？）每条带源文件行号，配合三型锚点 TOC 秒跳 22 万 token 全文

**流程命令**（复现整条链）：

```bash
# 视频源：字幕优先（YouTube 页面自带 transcript 时零 ASR）
python3 tools/kb.py add Unix 视频transcript.txt --type video --name unix-film-1982
# 书源：扫描版 → MinerU OCR → 清洗水印 → 入库（sha1 去重 + 自动三型锚点 TOC）
python3 tools/kb.py add Unix 书全文.md --type book --name taup-book
# 双源融合草稿（交叉主题锚点自动分析）→ agent 通读 → 蒸馏 TOPIC.md
python3 tools/kb.py draft Unix
```

融合策略（按源关系自动选择）：本次为**同主题互补型**（书=体系 + 视频=实证）——书章节做骨架，视频做「亲历者实证」小节；冲突观点并列标注来源；详见 skills/miji/SKILL.md「融合策略」表。

### 🫙 案例 Demo 六：JAR 蒸馏——反编译字节码入库（2026-09-09）

朋友问「能不能蒸馏 jar」→ 当天实测跑通，JAR 成为第三种一等公民来源：

- **样本**：gson-2.10.1（277KB）+ h2-2.2.224（2.5MB，528 个类）
- **链路**：`jadx -d src xx.jar`（M1 Pro 实测 7.5s / 9.8s）→ `scripts/jar_to_md.py` 拼成带类索引的单 md（每类一行：全限定类名 + public 方法签名）→ `kb.py add` 入库 → 全文检索与 `.toc.md` 行号锚点跳读全部通过
- **反编译质量**：变量名/泛型/注解保留，可直接提炼 API 用法与设计意图；个别复杂方法反编译失败不影响整体
- **适用**：闭源依赖调研、遗留系统文档重建、mod/插件能力分析
- **边界**：混淆 jar 需提供方 mapping.txt；反编译产物用于学习/互操作分析，勿整库照搬分发

## 📚 知识库形态（v1.3.0 新增）

MiJi 不止能出一次性 skill——同一套「解析 → 蒸馏」管线可以**按主题持续入库**，攒成个人知识库：

```bash
python3 tools/kb.py init                          # 初始化
python3 tools/kb.py add <主题> <文件...>           # 多端入库（PDF/视频转写/文章，sha1 自动去重）
python3 tools/kb.py draft <主题>                  # 多源融合草稿（交叉主题锚点）
python3 tools/kb.py search <关键词> [--topic X]    # 全文检索（纯 Python，中文路径安全）
python3 tools/kb.py export <主题> --name <slug>   # 把主题升格为 skill 目录
```

库结构（全部自动生成 / 维护）：

```
knowledge-base/
├── AGENTS.md                # 任何 AI（Claude/GPT/Codex/Cursor…）的读取规范
├── llms.txt                 # llmstxt.org 风格站点地图
├── INDEX.md                 # 自动目录（主题表 + 跨主题锚点）
└── topics/<主题>/
    ├── TOPIC.md             # 蒸馏速查条目（YAML frontmatter，Obsidian/Logseq 直接可用）
    ├── metadata.json        # 机器可读元数据（源清单 / sha1 / tokens）
    └── sources/             # 全文存档 + images/ 原书插图 + *.toc.md 章节锚点
```

- **与其他 AI 工具互通**：纯 markdown + YAML frontmatter——Obsidian / VSCode / 任意渲染器直接打开；agent 类工具读 `AGENTS.md` 即懂整个库的读取协议
- **核心设计哲学：越长越强，前提是可快速定位**。蒸馏产物不设长度上限——只要 AI 能按目录/关键词/行号跳到目标位置，10 万 token 和 1 万 token 的定位成本就相同，长度从负担变成资产。所以库对长文的消费方式永远是「TOC/关键词 → 行号 → `read_file(offset)` 跳读」，全量读取只留给 TOPIC.md 速查层（≤7KB）
- **长文定位保障：`*.toc.md` 三型锚点（kb.py 自动生成）**——① Markdown 标题 ② 章节标记（`第X节`/`第X章`/`续编（X）`）③ 编号规则（`NN｜标题`，适用于"71 条规则"类清单体长文）；TOC 头部另自动注入 10 个定位关键词。实测：一份 1 万字、**零 markdown 标题**的第三方蒸馏稿，入库后自动长出 74 条行号锚点（随机抽验行号全部逐字命中）。配合 `kb.py search 关键词` 做全文定点命中
- **与 skill 的分工**：skill = 高频操作准则；知识库 = 低频可查的沉淀。同一主题可共存，TOPIC.md 随时可 `export` 升格为 skill

## ⚡ 大文件并行解析（实测 2.1x）

几百页的扫描版 PDF 单进程要 20 分钟以上，可以拆段并行：

```bash
# 1. 拆分（纯 CPU，秒级）
python3 tools/split_pdf.py 输入.pdf 拆分目录 2
# 2. 每段起一个 MinerU 后台进程（各自 unset PYTHONPATH + WINDOW_SIZE=32 + 独立输出目录）
# 3. 按序合并：cat p1/*/auto/*.md p2/*/auto/*.md > merged.md（记得清理 PDF 水印行）
```

| 方案 | 484 页扫描书实测 |
|------|------------------|
| 单进程全书 | 22.4 分钟 |
| **拆 2 段双进程** | **10.7 分钟（2.1x）** |
| 拆 4 段四进程 | ❌ 崩 2/4（MPS 内存累积超限） |

- 质量等价：合并稿与串行版行数一致、接缝语义无缝，仅 ~2% 行级 OCR 抖动
- **Apple Silicon 32GB 的安全上限就是 2 个 worker**（3 个未测，别贪）
- 适用于扫描版大部头；文字原生 PDF 解析本来就快（252 页 4-6 分钟），不值得拆
- 崩掉的段单独重跑即可（输出目录独立、幂等）

## 🔀 两种解析引擎，按你的机器条件选（都是一等公民，无主次之分）

识别 PDF 这一步提供**两条完整路线**，各自独立可用——没有「主引擎」和「备胎」的等级之分，按你的硬件和需求挑：

| | 🖥 MinerU 本地 | ☁️ luna 云端 VLM |
|---|---|---|
| 硬件要求 | ~1GB 模型装本地（Apple Silicon / GPU 优先） | **零硬件门槛**——有 API key 就能跑 |
| 适合谁 | 有 M 系列 Mac / 独显、要提取插图、想零 API 成本 | 低配机 / 无独显 / 不想装环境的用户 |
| 速度 | 252 页文字版 4-6 分钟；扫描版 3-4x 慢（可并行 2.1x） | ~45s/页 × 并发路数（全本 484 页实测 $2.51） |
| 产物 | md + **图片切出** + 坐标 | 纯文本 md（图片不产出；要图可再跑本地补） |
| 数据去向 | 全本机，离线可跑 | 页面图片经 API 出网 |

**选型口诀**：低配机/无独显 → luna 是你的**主力路线**（这也是给很多用户唯一能跑的路线）；有 GPU/M 系列 → MinerU 更划算还带插图；两者混用也行（本地主力 + 糊页丢云端补刀）。

各环节的数据位置（透明列出，不设限制，用户自决）：

| 环节 | 运行位置 | 说明 |
|------|---------|------|
| PDF 版面识别 / OCR（MinerU 路线） | 你的设备 | pipeline 模式：PP-DocLayoutV2 / PaddleOCR / unimernet / 表格模型，约 1GB 权重本地，**离线可跑** |
| 整页转写（luna 路线） | 云端 API | 页面渲染成图后经 HTTPS 调用视觉模型；走自建中转站或任意兼容端点 |
| 视频转写 | 你的设备 | faster-whisper 本地跑（CPU 即可） |
| LLM 纠错 / 提示词生成 | 本地或云端均可 | ollama 本地可替代，或直接跳过 |
| 蒸馏本身 | 你的 agent | skill / 知识库生成不依赖任何外部服务 |

两点注意：
- MinerU 的 `hybrid` / VLM 引擎会调用视觉语言模型（更大显存 / 联网）——想要纯离线就用 `-b pipeline` 本地引擎
- faster-whisper 首次运行会从 HuggingFace 下载模型（数百 MB，一次性），之后完全离线

## 🙏 依赖项目与致谢

本流程建立在这些优秀的开源项目之上，感谢它们的作者：

| 依赖 | GitHub 页面 | 用途 |
|------|-------------|------|
| **MinerU** | https://github.com/opendatalab/MinerU | PDF 解析引擎（OCR/版面/公式/表格），本流程的核心解析工具 |
| **PDF-Extract-Kit-1.0** | https://github.com/opendatalab/PDF-Extract-Kit | MinerU 的模型仓库（Layout/MFR/OCR/TabRec 等 7 个子模型）|
| **book-to-skill** | https://github.com/virgiliojr94/book-to-skill | 书→Skill 转换的启发来源（面向 Copilot/Amp/Claude Code 生态；本仓库是其 Hermes 专属的速查式变体）|
| **aria2** | https://github.com/aria2/aria2 | 多线程下载模型（modelscope 810MB 仅 20 秒）|
| **ModelScope** | https://github.com/modelscope/modelscope | 国内高速模型下载源 |
| **pypdfium2** | https://github.com/pypdfium2-team/pypdfium2 | PDF 按页拆分（大文件并行解析的前置）|
| **Refactoring UI** | https://refactoringui.com | 验证用例（Adam Wathan & Steve Schoger 的设计书）|

特别感谢：
- **OpenDataLab 团队**（MinerU / PDF-Extract-Kit）——让高质量文档解析变得人人可用
- **virgiliojr94**（book-to-skill）——"书变成 skill"这个想法的源头
- **Adam Wathan & Steve Schoger**——本流程的第一个实测对象《Refactoring UI》

## 📄 License

MIT
