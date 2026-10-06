# -*- coding: utf-8 -*-
"""将 TXT 轻小说切分为规范化 Markdown（一行一段），供翻译流程使用。

用法:
    python txt_to_md.py <input.txt> <out_dir>
        [--encoding auto]              # auto / utf-8-sig / utf-8 / cp932 / euc-jp
        [--pattern 正则]               # 章节标题行正则（默认见 DEFAULT_PATTERN）
        [--paragraph-mode line|blank]  # line=一行一段（默认）；blank=空行分段（合并硬换行）
        [--min-chapter-lines N]        # 过滤过短章节（默认 1）

输出:
    <out_dir>/chapters/NNNN.md   # 每章一个文件（`# 标题` 首行，段落空行分隔）
    <out_dir>/toc.md             # 章节索引表

说明:
    * 第一个章节标题之前的内容（如有）写入 0000.md（标题为「（开头）」）。
    * ◆◆◆ 等分隔行原样保留；行首全角空格保留。
    * 产出与 EPUB 提取产物同构，可直接进入翻译/校验流程。
"""
import argparse
import io
import os
import re
import sys

DEFAULT_PATTERN = (r'^\s*(?:第[0-9０-９一二三四五六七八九十百]+[章話回]'
                   r'|プロローグ|エピローグ|序章|終章|幕間|あとがき|特別短編).*$')
ENCODINGS = ['utf-8-sig', 'utf-8', 'cp932', 'shift_jis', 'euc-jp']


def read_text(path, encoding):
    raw = open(path, 'rb').read()
    if encoding != 'auto':
        return raw.decode(encoding)
    for enc in ENCODINGS:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise SystemExit('无法识别文件编码，请用 --encoding 指定')


def split_chapters(text, pattern):
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    rx = re.compile(pattern)
    chapters = []  # [(title, [lines])]
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


def paragraphs(lines, mode):
    if mode == 'line':
        return [l for l in lines if l.strip()]
    paras, buf = [], []          # blank 模式：连续非空行合并为一段
    for l in lines:
        if l.strip():
            buf.append(l.strip())
        elif buf:
            paras.append(' '.join(buf))
            buf = []
    if buf:
        paras.append(' '.join(buf))
    return paras


def main():
    ap = argparse.ArgumentParser(description='TXT → 规范化章节 Markdown')
    ap.add_argument('input')
    ap.add_argument('out_dir')
    ap.add_argument('--encoding', default='auto')
    ap.add_argument('--pattern', default=DEFAULT_PATTERN)
    ap.add_argument('--paragraph-mode', choices=['line', 'blank'], default='line')
    ap.add_argument('--min-chapter-lines', type=int, default=1)
    args = ap.parse_args()

    text = read_text(args.input, args.encoding)
    chapters = split_chapters(text, args.pattern)
    chapters = [(t, ls) for t, ls in chapters
                if len([l for l in ls if l.strip()]) >= args.min_chapter_lines]

    os.makedirs(os.path.join(args.out_dir, 'chapters'), exist_ok=True)
    toc = ['# 章节索引', '', '| 文件 | 标题 | 段落数 |', '|---|---|---|']
    idx = 0
    for title, lines in chapters:
        paras = paragraphs(lines, args.paragraph_mode)
        if not paras and title == '（开头）':
            continue
        name = f'{idx:04d}.md'
        with io.open(os.path.join(args.out_dir, 'chapters', name), 'w', encoding='utf-8') as fh:
            fh.write(f'# {title}\n\n')
            fh.write('\n\n'.join(paras))
            fh.write('\n')
        toc.append(f'| {name} | {title} | {len(paras)} |')
        idx += 1
    with io.open(os.path.join(args.out_dir, 'toc.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(toc) + '\n')
    print(f'[ok] {idx} 章 -> {args.out_dir}/chapters/, toc.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())
