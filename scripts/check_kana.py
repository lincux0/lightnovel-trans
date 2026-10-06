# -*- coding: utf-8 -*-
"""检查中文译文中的残留日文假名。

用法:
    python check_kana.py <目录或文件> [--allow 平つくね] [--exclude colophon]

默认允许名单: 平つくね つくね 滝沢慧 滝沢（作者/插画师名等系列惯例）。
--exclude 按文件名子串排除（如奥付等保留日文的文件）。
退出码: 0 = 无残留; 1 = 有残留。
"""
import io
import os
import re
import sys

KANA = re.compile(r'[\u3040-\u309f\u30a0\u30fa\u30fc-\u30ff]')  # 排除 ・(U+30FB)
DEFAULT_ALLOW = ['平つくね', 'つくね', '滝沢慧', '滝沢']


def check_text(text, allow):
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        t = line
        for a in allow:
            t = t.replace(a, '')
        if KANA.search(t):
            hits.append((i, line.strip()[:60]))
    return hits


def main():
    args = sys.argv[1:]
    allow = list(DEFAULT_ALLOW)
    exclude = []
    paths = []
    i = 0
    while i < len(args):
        if args[i] == '--allow' and i + 1 < len(args):
            allow.append(args[i + 1]); i += 2
        elif args[i] == '--exclude' and i + 1 < len(args):
            exclude.append(args[i + 1]); i += 2
        else:
            paths.append(args[i]); i += 1
    if not paths:
        print(__doc__)
        return 1
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += [os.path.join(p, n) for n in sorted(os.listdir(p))
                      if n.endswith('.md') and not any(x in n for x in exclude)]
        else:
            files.append(p)
    total_hits = 0
    for f in files:
        text = io.open(f, encoding='utf-8').read()
        hits = check_text(text, allow)
        if hits:
            total_hits += len(hits)
            print(f'[FAIL] {f}')
            for n, line in hits[:10]:
                print(f'   {n}: {line}')
        else:
            print(f'[ok] {f}')
    print(f'--- 残留合计 {total_hits} 处 ---')
    return 1 if total_hits else 0


if __name__ == '__main__':
    sys.exit(main())
