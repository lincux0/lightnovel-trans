# -*- coding: utf-8 -*-
"""将 TXT 切分为 Markdown。auto 是按顺序尝试解码，不是可靠的编码识别。

用法: python txt_to_md.py <input.txt> <空输出目录> [--encoding auto|utf-8-sig|utf-8|cp932|euc-jp]
     [--pattern REGEX] [--paragraph-mode line|blank] [--min-chapter-lines N]
     [--separator TEXT ...]
章节标题切分可能因作品而异；批量处理前应先抽样确认。
"""
import argparse
import io
import os
import re
import sys

DEFAULT_PATTERN = (r'^\s*(?:第[0-9０-９一二三四五六七八九十百]+[章話回]'
                   r'|プロローグ|エピローグ|序章|終章|幕間|あとがき|特別短編).*$')
ENCODINGS = ['utf-8-sig', 'utf-8', 'cp932', 'euc-jp']
IMAGE = re.compile(r'^!\[illust\]\(')


def read_text(path, encoding):
    with open(path, 'rb') as f:
        raw = f.read()
    if encoding != 'auto':
        return raw.decode(encoding), encoding
    for candidate in ENCODINGS:
        try:
            return raw.decode(candidate), candidate
        except UnicodeDecodeError:
            continue
    raise ValueError('无法按 UTF-8/CP932/EUC-JP 解码，请检查原文并用 --encoding 指定')


def split_chapters(text, pattern):
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    rx = re.compile(pattern)
    chapters = []
    cur_title, cur_lines = None, []
    for line in lines:
        if rx.match(line):
            if cur_title is not None or any(l.strip() for l in cur_lines):
                chapters.append((cur_title or '（开头）', cur_lines))
            cur_title, cur_lines = line.strip(), []
        else:
            cur_lines.append(line.rstrip())
    if cur_title is not None or any(l.strip() for l in cur_lines):
        chapters.append((cur_title or '（开头）', cur_lines))
    return chapters


def is_separator(line, configured):
    text = line.strip()
    if not text:
        return False
    if text in configured:
        return True
    return len(text) >= 2 and len(set(text)) == 1 and not text.isalnum()


def paragraphs(lines, mode, separators=None):
    separators = set(separators or ['◆◆◆'])
    if mode == 'line':
        return [line for line in lines if line.strip()]
    paras, buf = [], []

    def flush():
        if buf:
            first = buf[0].rstrip()
            rest = [line.strip() for line in buf[1:]]
            paras.append(' '.join([first] + rest))
            buf.clear()

    for line in lines:
        if not line.strip():
            flush()
        elif is_separator(line, separators) or IMAGE.match(line.strip()):
            flush()
            paras.append(line.rstrip())
        else:
            buf.append(line)
    flush()
    return paras


def validate_paths(input_path, output_path):
    source = os.path.abspath(input_path)
    output = os.path.abspath(output_path)
    if not os.path.isfile(source):
        raise ValueError('输入必须是存在的普通文件')
    if os.path.exists(output) and not os.path.isdir(output):
        raise ValueError('输出路径已存在且不是目录')
    try:
        common = os.path.commonpath([source, output])
    except ValueError:
        common = None
    if common == output:
        raise ValueError('输出目录不能是输入文件的祖先目录')
    if os.path.dirname(source) == output:
        raise ValueError('输出目录不能与原文所在目录相同')
    if os.path.isdir(output) and os.listdir(output):
        raise ValueError('输出目录必须为空；为保护已有文件，拒绝覆盖')
    return source, output


def main(argv=None):
    ap = argparse.ArgumentParser(description='TXT → 规范化章节 Markdown')
    ap.add_argument('input')
    ap.add_argument('out_dir')
    ap.add_argument('--encoding', default='auto', choices=['auto', *ENCODINGS])
    ap.add_argument('--pattern', default=DEFAULT_PATTERN)
    ap.add_argument('--paragraph-mode', choices=['line', 'blank'], default='line')
    ap.add_argument('--min-chapter-lines', type=int, default=1,
                    help='低于此段数时只警告、不丢弃章节（默认 1）')
    ap.add_argument('--separator', action='append', default=None, metavar='TEXT',
                    help='blank 模式中额外的独立分隔行，可重复')
    args = ap.parse_args(argv)
    if args.min_chapter_lines < 0:
        ap.error('--min-chapter-lines 不能为负数')
    try:
        source, output = validate_paths(args.input, args.out_dir)
        text, encoding = read_text(source, args.encoding)
        if not text.strip():
            raise ValueError('输入文件为空或只包含空白字符')
        chapters = split_chapters(text, args.pattern)
        separators = {'◆◆◆', *(args.separator or [])}
        os.makedirs(output, exist_ok=True)
        os.makedirs(os.path.join(output, 'chapters'))
        toc = ['# 章节索引', '', '| 文件 | 标题 | 段落数 |', '|---|---|---|']
        written = 0
        for title, lines in chapters:
            paras = paragraphs(lines, args.paragraph_mode, separators)
            if title == '（开头）' and not paras:
                continue
            source_lines = sum(bool(line.strip()) for line in lines)
            if source_lines < args.min_chapter_lines:
                print(f'[WARN] {title}: {source_lines} 行，低于阈值 {args.min_chapter_lines}，仍保留')
            name = f'{written:04d}.md'
            with io.open(os.path.join(output, 'chapters', name), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(f'# {title}\n\n')
                fh.write('\n\n'.join(paras))
                fh.write('\n')
            toc.append(f'| {name} | {title} | {len(paras)} |')
            written += 1
        with io.open(os.path.join(output, 'toc.md'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(toc) + '\n')
        print(f'[info] 编码候选首个成功: {encoding}（auto 仅回退尝试，不保证识别正确）')
        print(f'[ok] {written} 章 -> {output}/chapters/, toc.md')
        return 0
    except (OSError, UnicodeError, ValueError, re.error) as exc:
        print(f'[ERROR] {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
