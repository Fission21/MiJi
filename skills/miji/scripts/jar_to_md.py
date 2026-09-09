#!/usr/bin/env python3
"""jar_to_md.py — 把 jadx 反编译产物（sources 目录）拼成带类索引的单 markdown。

用途：MiJi JAR 蒸馏模式 Step 2（反编译之后、蒸馏/入库之前）。
产出结构：
  # <标题>
  ## 类索引           ← 每类一行：全限定类名 + public 方法签名（蒸馏/检索的锚点）
  ## <包/类路径>      ← 每类一节，java 源码全文

用法:
  python3 jar_to_md.py <jadx输出>/sources -o all.md [--title "Xxx 1.0 反编译源码"]
  # 典型全流程:
  #   jadx -d foo-src foo.jar
  #   python3 jar_to_md.py foo-src/sources -o foo-all.md
  #   KB_ROOT=... kb.py add <主题> foo-all.md --type article
"""
import argparse
import os
import re
import sys


def collect(sources_dir: str):
    """返回 [(rel_path_without_ext, source_text)]，按路径排序。"""
    items = []
    for root, _dirs, files in os.walk(sources_dir):
        for fn in sorted(files):
            if fn.endswith(".java"):
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, sources_dir)[:-5]  # 去 .java
                try:
                    text = open(full, encoding="utf-8", errors="replace").read()
                except OSError as e:
                    print(f"⚠️ 读取失败 {full}: {e}", file=sys.stderr)
                    continue
                items.append((rel.replace(os.sep, "/"), text))
    items.sort()
    return items


# public 方法/构造器签名（4 空格缩进一级，jadx 常规输出）
SIG_RE = re.compile(r"^\s{4}public (?:[\w<>\[\],.? ]+ )?(\w+)\(", re.M)
# Kotlin/scala 风格或特殊缩进兜底：任意缩进的 public 方法
SIG_RE_LOOSE = re.compile(r"^\s*public (?:[\w<>\[\],.? ]+ )?(\w+)\(", re.M)


def class_index_line(rel: str, src: str) -> str:
    sigs = SIG_RE.findall(src) or SIG_RE_LOOSE.findall(src)
    # 去重保序，过滤纯类名（构造器重复无信息量）
    seen, names = set(), []
    cls_simple = rel.rsplit("/", 1)[-1]
    for s in sigs:
        if s not in seen and s != cls_simple:
            seen.add(s)
            names.append(s)
    if not names:
        return f"- **{rel}**"
    return f"- **{rel}**: {', '.join(names[:25])}" + (" …" if len(names) > 25 else "")


def main():
    ap = argparse.ArgumentParser(description="jadx sources → 单 md（类索引 + 全文）")
    ap.add_argument("sources", help="jadx 输出的 sources 目录")
    ap.add_argument("-o", "--out", required=True, help="输出 .md 路径")
    ap.add_argument("--title", default=None, help="文档标题（默认取目录名）")
    args = ap.parse_args()

    items = collect(args.sources)
    if not items:
        sys.exit(f"错误: {args.sources} 下没有 .java 文件（确认 jadx -d 输出目录）")

    title = args.title or f"{os.path.basename(os.path.normpath(args.sources))} 反编译源码"
    index_lines = [class_index_line(rel, src) for rel, src in items]
    parts = [f"# {title}\n", "## 类索引\n", "\n".join(index_lines)]
    for rel, src in items:
        parts.append(f"\n\n## {rel}\n\n```java\n{src}\n```")

    doc = "".join(parts)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(doc)

    kb = len(doc) / 1024
    print(f"✅ {args.out}: {len(items)} 个类, {kb:.0f} KB")
    if kb > 1500:
        print("⚠️ 超过 1.5MB：kb.py 会自动生成 .toc.md 行号锚点（禁止全量读，按锚点跳读）")


if __name__ == "__main__":
    main()
