# Demo 6 品鉴样品：jsoup 1.17.2 JAR 蒸馏

本目录是 JAR 蒸馏模式的**实际产出样品**，供评估蒸馏质量时对照阅读。

- `jsoup-distill.md` — 10108 字《jsoup API 速查》，由 LLM 从「类索引 + 7 个关键类反编译源码」蒸馏生成，供 AI agent 直接使用
- 来源 jar：`org/jsoup/jsoup:1.17.2`（Maven Central，MIT 协议）

## 品鉴结果（2026-09-09 实测）

| 工序 | 方法 | 结果 |
|------|------|------|
| 防幻觉抽查 | 正则抽取蒸馏稿引用的全部 43 个方法名，逐个到反编译源码验证存在性 | **43/43 真实存在** |
| 行为断言核验 | 8 条行为性断言（抛什么异常/默认值/特判）逐条 grep 反编译源码 | **8/8 属实** |
| 覆盖对照 | 与官方文档 jsoup.org/cookbook 比对 | 覆盖连接与选择器两大核心面；CSS 语法表属字符串解析器（不在字节码语义内），蒸馏稿正确地未写 |

核验细节（反编译源 = ground truth）：

- `Safelist.addTags("noscript")` 抛 `IllegalArgumentException`（源码注释：解析器 script-mode 兼容性问题，明确禁止）
- `Element.val()` 对 `textarea` 特判返回 `text()` 而非 value 属性
- `Jsoup.parse(File, charset)` 用 `file.getAbsolutePath()` 作 baseUri
- `Connection.auth()` 默认抛 `UnsupportedOperationException`；`Document.connection()` 无连接时返回 `Jsoup.newSession()`

## 复现

```bash
# ① 反编译
jadx --no-res -d jsoup-src jsoup-1.17.2.jar
# ② 类索引 md
python3 skills/miji/scripts/jar_to_md.py jsoup-src/sources -o jsoup-all.md --title "jsoup 反编译源码（jadx）"
# ③ 入库（可选）+ 选关键类喂 LLM 蒸馏（提示词铁律见 SKILL.md Step 1d「蒸馏品鉴法」）
python3 tools/kb.py add jsoup jsoup-all.md
```

> ⚠️ 本样品仅用于学习/互操作分析演示；jsoup 官方源码在 github.com/jhy/jsoup，生产环境请直接用官方库与文档。
