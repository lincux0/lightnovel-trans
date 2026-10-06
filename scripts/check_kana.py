# -*- coding: utf-8 -*-
"""检查 Markdown 中残留的日文假名。

用法: python check_kana.py <目录或文件> [--allow NAME] [--exclude FILE_OR_STEM]
目录会递归扫描 .md 文件。--allow 和 --exclude 均可重复。
退出码: 0 = 无残留且至少扫描一个文件; 1 = 有残留或参数/路径/扫描范围无效。
"""
import argparse
import os
import re
import sys

# Exclude the Japanese middle dot (U+30FB), but include standard, half-width,
# and supplementary kana blocks.
KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30fa\u30fc-\u30ff\u31f0-\u31ff\uff66-\uff9f\U0001aff0-\U0001afff\U0001b000-\U0001b16f]')


def check_text(text, allow):
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        t = line
        for allowed in allow:
            t = t.replace(allowed, '')
        if KANA.search(t):
            hits.append((i, line.strip()[:60]))
    return hits


def collect_files(paths, excludes):
    files = []
    for raw in paths:
        path = os.path.abspath(raw)
        if not os.path.exists(path):
            raise ValueError(f'路径不存在: {raw}')
        if os.path.isdir(path):
            for root, dirs, names in os.walk(path):
                dirs.sort()
                for name in sorted(names):
                    if name.lower().endswith('.md') and name not in excludes and os.path.splitext(name)[0] not in excludes:
                        files.append(os.path.join(root, name))
        elif os.path.isfile(path):
            if os.path.basename(path) not in excludes and os.path.splitext(os.path.basename(path))[0] not in excludes:
                files.append(path)
        else:
            raise ValueError(f'不是普通文件或目录: {raw}')
    files = sorted(set(files))
    if not files:
        raise ValueError('没有可扫描的 Markdown 文件')
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description='递归检查 Markdown 中残留的日文假名')
    ap.add_argument('paths', nargs='+', help='文件或目录')
    ap.add_argument('--allow', action='append', default=[], metavar='NAME', help='允许保留的专名/文本，可重复')
    ap.add_argument('--exclude', action='append', default=[], metavar='FILE_OR_STEM', help='按完整文件名或不含扩展名的文件名排除，可重复')
    args = ap.parse_args(argv)
    try:
        files = collect_files(args.paths, set(args.exclude))
        total_hits = 0
        for path in files:
            with open(path, encoding='utf-8-sig') as f:
                hits = check_text(f.read(), args.allow)
            if hits:
                total_hits += len(hits)
                print(f'[FAIL] {path}')
                for line_no, line in hits[:10]:
                    print(f'   {line_no}: {line}')
            else:
                print(f'[ok] {path}')
        print(f'--- 扫描 {len(files)} 个文件，残留 {total_hits} 行 ---')
        return 1 if total_hits else 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f'[ERROR] {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
