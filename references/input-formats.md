# 输入形态适配：EPUB / TXT / Word / 其他

> 目标：**不论来源格式，先统一为规范化中间格式**，再进入翻译流程。中间格式与 EPUB 提取产物同构，这样后续的逐段对应、QA、打包全部照常工作。

## 规范化中间格式（必须一致）

- `chapters/*.md`：`# 标题` 首行；一行一段（保留行首全角空格与 ◆◆◆ 等分隔行）；插图位置 `![illust](images/xxx)`；段落之间空行。
- `chapters.json`：id / role / title / sources / 字数（无 sources 时记来源文件名）。
- `full.md`（全书顺序拼接）、`toc.md`（章节索引表）、`images/`（原字节复制）。
- 校验：章节数、段落数、插图引用数统计；与来源内容抽章核对。

## 1. EPUB（首选，信息最全）

- 见 [workflow.md](workflow.md) 第 1.1 节：按 spine + NCX/nav 切分；ruby/tcy 剥离；插图保留位置。
- 优点：章节结构与插图位置权威；可原样回写（见 [epub-packaging.md](epub-packaging.md)）。

## 2. TXT

- **编码**：日文 TXT 常见 Shift-JIS/cp932，其次 UTF-8（含 BOM）；按 utf-8-sig → utf-8 → cp932 → euc-jp 顺序尝试，失败再让用户确认。
- **章节切分**：正则匹配章节行，例如：
  - `^\s*(第[0-9一二三四五六七八九十百]+[章話回]|プロローグ|エピローグ|序章|終章|幕間|あとがき|特別短編).*$`
  - 不同作品格式差异大（有的用「◆」分隔、有的用空行+标题），先抽样 20-50 行确认再批量。
- **段落**：
  - 常见：一行一段（日文小说 TXT 多为此）。
  - 硬换行版：连续非空行合并为一段，空行分段（`--paragraph-mode blank`）。
- **插图**：TXT 无图。若附带图片目录：按文件名（001.jpg…）顺序在对应章节/位置插入 `![illust](images/xxx)`，位置需对照原书/网络版人工确认。
- **ruby 读音**：TXT 通常丢失。专名读音以官方资料/词典核对，记入 glossary（用于后续卷一致性）。
- 参考脚本：`scripts/txt_to_md.py`。

## 3. Word / docx

- **段落与标题**：解析 `word/document.xml` 的 `w:p`；标题样式（`Heading 1` / `見出し1` / `标题 1`）作章节切分点；无样式时按章节正则兜底（同 TXT）。
- **图片**：docx 本质是 zip：
  - 图片在 `word/media/`；
  - `word/_rels/document.xml.rels` 给出 r:embed → 文件映射；
  - `w:drawing`/`w:pict` 出现的位置即插图位置（插画页可近似处理）。
- **注音（ruby）**：Word 中通常已丢失或退化为「汉字（假名）」；不要强行恢复，按语境处理。
- **工具**：
  - `python-docx`（最省事）：`Document(path).paragraphs`，按 `paragraph.style.name` 判标题；
  - 无依赖：`zipfile` + `lxml` 解析 document.xml（与 EPUB 提取器同思路）。
- **表格/文本框**：小说正文一般无表格；文本框内容可能乱序，需按 XML 顺序核对。

## 4. 其他来源

| 来源 | 做法 |
|---|---|
| HTML / 网页 | 去标签转 md（保留标题层级与段落）；图片下载到 `images/`；注意分页导航与广告剔除 |
| azw3 / mobi | 先用 calibre `ebook-convert` 转 EPUB，再走 1.1 |
| PDF | 仅当无其他来源；优先文本层，扫描版需 OCR；段落结构需人工校对，风险高 |

## 5. 无原版 EPUB 的打包

来源不是 EPUB 时，没有可回写的底本 → 直接自建 EPUB（横排中文）。结构模板与要点见 [epub-packaging.md](epub-packaging.md) 的"无原版 EPUB 时：自建 EPUB"。
