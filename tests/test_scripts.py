import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
PYTHON = [sys.executable, '-X', 'utf8', '-B']


def run_script(name, *args):
    return subprocess.run(PYTHON + [str(SCRIPTS / name), *map(str, args)],
                          capture_output=True, text=True, encoding='utf-8')


class ScriptTests(unittest.TestCase):
    def test_check_kana_ranges_titles_recursion_and_allowlist(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            nested = root / 'nested'
            nested.mkdir()
            (root / '01.md').write_text('# カタカナㇰ\n半角ｶﾅ\n変体仮名𛀁\n', encoding='utf-8')
            (nested / 'name.md').write_text('平つくね\n・\n', encoding='utf-8')
            result = run_script('check_kana.py', root, '--allow', '平つくね')
            self.assertEqual(result.returncode, 1)
            self.assertIn('カタカナㇰ', result.stdout)
            self.assertIn('半角ｶﾅ', result.stdout)
            self.assertIn('変体仮名𛀁', result.stdout)
            allowed = run_script('check_kana.py', nested, '--allow', '平つくね')
            self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
            missing = run_script('check_kana.py', root / 'missing')
            self.assertEqual(missing.returncode, 1)

    def test_check_kana_exact_exclude_and_zero_files_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / 'colophon.md').write_text('カナ', encoding='utf-8')
            (root / 'not-colophon.md').write_text('かな', encoding='utf-8')
            result = run_script('check_kana.py', root, '--exclude', 'colophon')
            self.assertEqual(result.returncode, 1)
            self.assertIn('not-colophon.md', result.stdout)
            empty = root / 'empty'
            empty.mkdir()
            result = run_script('check_kana.py', empty)
            self.assertEqual(result.returncode, 1)
            self.assertIn('没有可扫描', result.stderr)

    def test_alignment_detects_file_set_and_unknown_chapter(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            jp, cn = root / 'jp', root / 'cn'
            jp.mkdir(); cn.mkdir()
            (jp / '01.md').write_text('# 第一章\n正文\n', encoding='utf-8')
            self.assertEqual(run_script('verify_alignment.py', jp, cn).returncode, 1)
            (cn / '01.md').write_text('# 第一章\n正文\n', encoding='utf-8')
            (cn / '02.md').write_text('# 多余\n内容\n', encoding='utf-8')
            result = run_script('verify_alignment.py', jp, cn)
            self.assertEqual(result.returncode, 1)
            self.assertIn('02.md', result.stdout)
            result = run_script('verify_alignment.py', jp, cn, 'absent')
            self.assertEqual(result.returncode, 1)
            self.assertIn('absent.md', result.stderr)
            (jp / '01.md').unlink(); (cn / '01.md').unlink(); (cn / '02.md').unlink()
            self.assertEqual(run_script('verify_alignment.py', jp, cn).returncode, 1)

    def test_alignment_rejects_two_blank_chapters(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            jp, cn = root / 'jp', root / 'cn'
            jp.mkdir(); cn.mkdir()
            (jp / '01.md').write_text('\n  \n', encoding='utf-8')
            (cn / '01.md').write_text('\n\n', encoding='utf-8')
            result = run_script('verify_alignment.py', jp, cn)
            self.assertEqual(result.returncode, 1)
            self.assertIn('无非空段落', result.stdout)

    def test_alignment_heading_level_separator_and_illustration_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            jp, cn = root / 'jp', root / 'cn'
            jp.mkdir(); cn.mkdir()
            (jp / '01.md').write_text('# 第一章\n◆◆◆\n![illust](images/a.jpg)\n本文\n', encoding='utf-8')
            (cn / '01.md').write_text('# 第一章（译）\n◆◆◆\n![illust](images/b.jpg)\n正文\n', encoding='utf-8')
            result = run_script('verify_alignment.py', jp, cn)
            self.assertEqual(result.returncode, 1)
            self.assertIn('插图标记路径不一致', result.stdout)
            (cn / '01.md').write_text('## 第一章（译）\n◆◆◆\n![illust](images/a.jpg)\n正文\n', encoding='utf-8')
            result = run_script('verify_alignment.py', jp, cn)
            self.assertEqual(result.returncode, 1)
            self.assertIn('标题级别不一致', result.stdout)
            (jp / '01.md').write_text('# 第一章\n＊＊＊\n正文\n', encoding='utf-8')
            (cn / '01.md').write_text('# 第一章（译）\n＊＊＊\n正文\n', encoding='utf-8')
            self.assertEqual(run_script('verify_alignment.py', jp, cn, '--separator', '＊＊＊').returncode, 0)

    def test_txt_rejects_empty_input_output_collision_and_negative_threshold(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source = root / 'source.txt'
            source.write_text('', encoding='utf-8')
            output = root / 'out'
            result = run_script('txt_to_md.py', source, output)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(output.exists())
            source.write_text('第1章\n正文\n', encoding='utf-8')
            self.assertEqual(run_script('txt_to_md.py', source, root).returncode, 1)
            self.assertEqual(run_script('txt_to_md.py', source, output, '--min-chapter-lines', '-1').returncode, 2)

    def test_txt_short_chapter_is_kept_and_rerun_is_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source = root / 'source.txt'
            output = root / 'out'
            source.write_text('第1章\n一段\n第2章\n', encoding='utf-8')
            result = run_script('txt_to_md.py', source, output, '--min-chapter-lines', '3')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('仍保留', result.stdout)
            self.assertTrue((output / 'chapters' / '0001.md').exists())
            source.write_text('第1章\n只有一章\n', encoding='utf-8')
            rerun = run_script('txt_to_md.py', source, output)
            self.assertEqual(rerun.returncode, 1)
            self.assertTrue((output / 'chapters' / '0001.md').exists())

    def test_txt_blank_mode_keeps_indent_and_separates_markers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source = root / 'source.txt'
            output = root / 'out'
            source.write_text('第1章\n\n　台詞\n続き\n＊＊＊\n![illust](images/a.jpg)\n本文\n', encoding='utf-8')
            result = run_script('txt_to_md.py', source, output, '--paragraph-mode', 'blank', '--separator', '＊＊＊')
            self.assertEqual(result.returncode, 0, result.stderr)
            body = (output / 'chapters' / '0000.md').read_text(encoding='utf-8')
            self.assertIn('　台詞 続き', body)
            self.assertIn('\n\n＊＊＊\n\n![illust](images/a.jpg)\n\n本文', body)


if __name__ == '__main__':
    unittest.main()
