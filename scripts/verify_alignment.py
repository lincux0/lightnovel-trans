# -*- coding: utf-8 -*-
"""校验日文/中文章节 Markdown 的逐段结构对应（1:1）。

用法:
    python verify_alignment.py <jp_dir> <cn_dir> [章节名 ...]

对两个目录中同名的 .md 文件逐一检查:
  * 非空行数量一致（含标题行、◆◆◆ 分隔行、![illust] 插图标记行）
  * 标题行（#）位置一致
  * ◆◆◆ 分隔行位置一致
  * ![illust](...) 插图标记位置一致

退出码: 0 = 全部通过; 1 = 存在问题。
"""
import io
import os
import re
import sys

SEP = '\u25c6\u25c6\u25c6'
ILL = re.compile(r'!\[illust\]')


def load(path):
    return [l.rstrip('\n') for l in io.open(path, encoding='utf-8') if l.strip()]


def check_file(jp_path, cn_path):
    jp = load(jp_path)
    cn = load(cn_path)
    problems = []
    if len(jp) != len(cn):
        problems.append(f'段落数不一致: jp={len(jp)} cn={len(cn)}')
        return problems
    for i, (a, b) in enumerate(zip(jp, cn)):
        if a.startswith('#') != b.startswith('#'):
            problems.append(f'第 {i+1} 行: 标题标记不一致 | jp={a[:30]} | cn={b[:30]}')
        if (a.strip() == SEP) != (b.strip() == SEP):
            problems.append(f'第 {i+1} 行: ◆◆◆ 位置不一致')
        if bool(ILL.search(a)) != bool(ILL.search(b)):
            problems.append(f'第 {i+1} 行: 插图标记不一致')
    return problems


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    jp_dir, cn_dir = sys.argv[1], sys.argv[2]
    only = set(sys.argv[3:])
    names = sorted(n for n in os.listdir(jp_dir)
                   if n.endswith('.md') and (not only or n[:-3] in only or n in only))
    total = bad = 0
    for name in names:
        jp_path = os.path.join(jp_dir, name)
        cn_path = os.path.join(cn_dir, name)
        if not os.path.isfile(cn_path):
            print(f'[skip] {name}: 中文文件不存在')
            continue
        total += 1
        problems = check_file(jp_path, cn_path)
        if problems:
            bad += 1
            print(f'[FAIL] {name}')
            for p in problems[:10]:
                print('   -', p)
        else:
            jp = load(jp_path)
            print(f'[ok] {name}: {len(jp)} 行 1:1')
    print(f'--- 共 {total} 章, 失败 {bad} ---')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
