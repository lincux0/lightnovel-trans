# -*- coding: utf-8 -*-
"""校验日文/中文章节 Markdown 的非空行结构对应（1:1）。

用法: python verify_alignment.py <jp_dir> <cn_dir> [章节名 ...] [--separator TEXT]
标题文字可不同，但标题级别、分隔符及 ![illust](...) 路径必须对应。
报错位置同时给出物理行号和非空段号。
退出码: 0 = 全部通过; 1 = 章节集合、内容结构或参数有问题。
"""
import argparse
import os
import re
import sys

ILL = re.compile(r'!\[illust\]\(([^)]+)\)')
HEADING = re.compile(r'^(#+)(?:\s|$)')


def load(path):
    with open(path, encoding='utf-8-sig') as f:
        return [(line_no, line.rstrip('\r\n'))
                for line_no, line in enumerate(f, 1) if line.strip()]


def heading_level(line):
    match = HEADING.match(line)
    return len(match.group(1)) if match else 0


def check_file(jp_path, cn_path, separators=None):
    separators = {'◆◆◆', *(separators or [])}
    jp, cn = load(jp_path), load(cn_path)
    problems = []
    if len(jp) != len(cn):
        problems.append(f'非空段数不一致: jp={len(jp)} cn={len(cn)}')
        return problems
    if not jp:
        problems.append('日文和中文文件均无非空段落')
        return problems
    for index, ((jp_line_no, a), (cn_line_no, b)) in enumerate(zip(jp, cn), 1):
        context = f'非空段 {index} (jp物理行 {jp_line_no}, cn物理行 {cn_line_no})'
        if heading_level(a) != heading_level(b):
            problems.append(f'{context}: 标题级别不一致')
        jp_sep, cn_sep = a.strip(), b.strip()
        if (jp_sep in separators) != (cn_sep in separators) or (jp_sep in separators and jp_sep != cn_sep):
            problems.append(f'{context}: 分隔符位置或内容不一致')
        if ILL.findall(a) != ILL.findall(b):
            problems.append(f'{context}: 插图标记路径不一致')
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description='校验日中章节 Markdown 的结构对应')
    ap.add_argument('jp_dir')
    ap.add_argument('cn_dir')
    ap.add_argument('chapters', nargs='*', help='可选章节文件名或不含扩展名的 stem')
    ap.add_argument('--separator', action='append', default=None, metavar='TEXT', help='其他分隔行，可重复；默认 ◆◆◆')
    args = ap.parse_args(argv)
    try:
        if not os.path.isdir(args.jp_dir) or not os.path.isdir(args.cn_dir):
            raise ValueError('日文和中文路径都必须是存在的目录')
        jp_names = {n for n in os.listdir(args.jp_dir) if n.lower().endswith('.md') and os.path.isfile(os.path.join(args.jp_dir, n))}
        cn_names = {n for n in os.listdir(args.cn_dir) if n.lower().endswith('.md') and os.path.isfile(os.path.join(args.cn_dir, n))}
        if args.chapters:
            requested = set()
            for chapter in args.chapters:
                requested.add(chapter if chapter.lower().endswith('.md') else chapter + '.md')
            unknown = requested - jp_names - cn_names
            if unknown:
                raise ValueError('指定章节在日中目录中都不存在: ' + ', '.join(sorted(unknown)))
            names = sorted(requested)
        else:
            names = sorted(jp_names | cn_names)
        if not names:
            raise ValueError('没有可校验的章节文件')

        missing_jp = sorted(set(names) - jp_names)
        missing_cn = sorted(set(names) - cn_names)
        bad = 0
        for name in missing_jp:
            print(f'[FAIL] {name}: 日文文件不存在')
            bad += 1
        for name in missing_cn:
            print(f'[FAIL] {name}: 中文文件不存在')
            bad += 1
        total = 0
        for name in names:
            if name not in jp_names or name not in cn_names:
                continue
            total += 1
            problems = check_file(os.path.join(args.jp_dir, name), os.path.join(args.cn_dir, name), args.separator)
            if problems:
                bad += 1
                print(f'[FAIL] {name}')
                for problem in problems[:10]:
                    print('   -', problem)
            else:
                print(f'[ok] {name}: {len(load(os.path.join(args.jp_dir, name)))} 段结构对应')
        print(f'--- 共检查 {total} 对章节，失败 {bad} ---')
        return 1 if bad else 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f'[ERROR] {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
