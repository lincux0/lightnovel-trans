# EPUB 回写与横排转换（技术细节）

## 总原则

- 只替换 XHTML 中的**文本**；不改 CSS、图片（字节原样）、content.opf、目录结构、链接、元素属性（id/class/href）。
- 奥付（p-colophon / p-colophon2 / p-bookwalker）与版权声明不回写。
- 所有替换与转换都要能被"差异范围白名单"验证（见下）。

## 提取器（extract_epub.py）关键设计

- lxml 解析；`PARA_TAGS` 处理 p/h1-h6 等；`_inline` 抽取文本时剥离 ruby（取 rb/rt 文本、丢弃注音结构）、tcy、span。
- 图片：正文插图以 `![illust](images/xxx)` 作为独立条目；嵌在 ruby 内的外字（gaiji）图片随注音剥离。
- 段落一行一条；空段落以空行维持节奏；章节标题去重（正文首个标题与 section 标题一致时并入 md 的 `#` 标题行）。
- 回写脚本复用同一解析逻辑（WBExtractor），并断言"解析结果与提取器完全一致"，保证 1:1 映射可靠。

## 回写（writeback_epub*.py）

1. 载入译文 md：`title = lines[0]`，`body = lines[1:]`。
2. 对每个 section 的每个源文件：提取条目 → 过滤（空文本、首个与 section 同名标题去重）→ 与译文切片逐条对应 → `set_text(el, cn_text)`（清空子元素只设 text，从而移除 ruby/tcy）。
3. 图片条目、脚注条目保持原样；标题去重条目写为中文标题。
4. 断言：译文消费数 == md 段落总数；解析结果与提取器一致。
5. 特殊页：
   - `p-caution.xhtml`：版权提示三句（缩略图说明 / 排版说明 / 阅读器差异说明）；
   - `p-001.xhtml`：插画师署名（口絵・本文イラスト 平つくね → 彩页・正文插画 平つくね）；
   - `p-toc-002.xhtml`：目录链接文字（href → 中文标签映射）；
   - `nav.xhtml` / `toc.ncx`：导航标签映射（含 landmarks：封面/正文）。
6. 重建 zip：`mimetype` 首个且 STORED，其余 DEFLATED；未修改文件按原字节写入。
7. 输出竖排备份（如 `work/vXX-cn-vertical.epub`）。

## 横排转换（make_horizontal*.py）

- 目标：与既有中文版样式一致（横排、行距 1.3、2em 首行缩进、◆◆◆ 左移 3em、标题样式）。
- XHTML：`class="vrtl"`→`class="hltr"`；`xml:lang="ja"`→`"zh-CN"`；`<p>◆◆◆</p>`→`<p class="sep-break">◆◆◆</p>`。
- CSS：先扫描各 XHTML 的 `<link>` 统计，找到正文页引用的主 CSS（各卷文件名不同），在**末尾**追加覆盖块；JEPA 系 CSS 原生支持 `.hltr`。覆盖块要点：
  ```css
  html.hltr, .hltr { writing-mode: horizontal-tb; }
  .hltr body { margin-left:1%; margin-right:1%; line-height:1.3; text-align:justify; }
  .hltr body p { text-indent:2em; line-height:1.3; margin:0.4em 0; }
  .hltr p.font-1em30 { text-indent:0; text-align:left; font-weight:bold; font-size:1.2em;
                       margin:2em 0 2em 1.7em; }          /* 章节标题 */
  .hltr p.sep-break { margin-left:3em; }                   /* 场景分隔符（+2em 缩进） */
  .hltr .start-3em, .hltr .start-2em { margin-left:0; margin-top:0; }
  .hltr body.p-colophon p, .hltr body.p-colophon2 p { text-indent:0; }
  ```
- OPF：`primary-writing-mode` → horizontal-tb；spine `page-progression-direction` → ltr；`dc:language` → zh-CN（每处替换前断言出现次数=1）。
- 说明页：横排成品把 p-caution 的「本电子书采用竖排布局。」改为「横排布局」；竖排备份保留原说明。
- 输出：`output/vXX-cn.epub`。

## 验证脚本设计（validate_*.py）

- **竖排验证**（vs 日文原版）：
  - zip 完整性 / mimetype 位置与压缩方式 / 文件清单一致；
  - 仅"预期修改清单"文件变化、其余字节一致（含 CSS/图片/OPF/奥付）；
  - XHTML 可解析且 p/img/a/id 结构保留（已知例外显式白名单，如外字图片移除）；
  - nav/NCX 链接集合一致、目标与锚点存在；目录标签已中文化；
  - 正文无假名残留（允许作者/插画师名）；抽查关键译文句。
- **横排验证**（vs 竖排备份）：
  - 逐文件 diff，且变化文件"只能由白名单变换得到"（vrtl→hltr、xml:lang、sep-break、CSS 追加、OPF 3 处、说明页文案）；
  - 无 `vrtl` / `xml:lang="ja"` 残留；sep-break 计数与译文中 ◆◆◆ 数一致；
  - 抽查段落数/图片数/链接；无假名残留。
- **渲染抽查**：解包 → `python -m http.server <port> --directory <解包目录>` → Playwright 打开正文页截图 → 核对横排/缩进/分隔符/标题 → 关闭进程与标签页（浏览器工具不支持 file://，需用 http）。

## 无原版 EPUB 时：自建 EPUB

来源是 TXT/Word 等、没有可回写的原版 EPUB 时，直接构建成品 EPUB（横排中文样式）。最小结构：

```
vXX-cn.epub
├─ mimetype                          # application/epub+zip（首个条目，STORED）
├─ META-INF/container.xml            # 指向 OEBPS/content.opf
└─ OEBPS/
    ├─ content.opf                   # 元数据、manifest、spine（ltr）
    ├─ nav.xhtml                     # EPUB3 导航（目录）
    ├─ toc.ncx                       # 兼容旧阅读器（可选但推荐）
    ├─ Styles/main.css               # 中文横排样式（见下）
    ├─ Text/p-001.xhtml …            # 每章一页；<html class="hltr" xml:lang="zh-CN">
    └─ Images/…                      # 插图（原字节）
```

要点：

- 正文页模板：`<body class="p-text"><div class="main"><h1 class="font-1em30">第X章 …</h1><p>…</p>…</div></body>`；段落一行一个 `<p>`；`◆◆◆` 用 `<p class="sep-break">◆◆◆</p>`；插图用 `<img>` 或 svg。
- CSS 基线：直接把上面的中文横排覆盖块作为主样式即可（行距 1.3、2em 首行缩进、sep-break margin-left 3em、标题样式、colophon 不缩进）。
- 目录 / NCX：与章节一一对应；标题中文化。
- 元数据：`dc:language=zh-CN`、`page-progression-direction=ltr`、`primary-writing-mode=horizontal-tb`；`dc:title` 用中文书名（自建时无"保留日文原名"约束，除非用户另有要求）。
- 生成方式：写一个 `build_epub.py`（生成全部 XHTML/OPF/导航后打包 zip）。"未改文件字节原样"不适用（全新构建），但要求**确定性**——同一输入重跑产出同一字节，便于版本间 diff。
- 验证：结构合法 + 正文与译稿 md 段落映射一致 + 渲染抽查 + 无假名残留（见 qa-checklist.md）。

## 常见技术坑

- **分隔符**：源 XHTML 可能是 `<p>　　　　◆◆◆</p>`（带全角空格），回写后归一为 `<p>◆◆◆</p>`；横排正则要匹配归一化后的形式。
- **外字（gaiji）**：`<img class="gaiji" ...>` 可能嵌在 ruby 内，随文本替换移除——属预期例外，图片文件仍保留在包内；验证脚本显式放行。
- **CSS 文件名逐卷不同**（flow0001/flow0006/flow0010/flow0012…）：不要写死；先扫描正文页的 `<link>` 决定追加目标。
- **OPF 标记写法可能因卷而异**：检查 `primary-writing-mode` / `page-progression-direction` / `dc:language` 的实际写法后再替换。
- **压缩确定性**：重建 zip 时未改文件保持原字节；重打包前后 diff 应只出现预期文件。
- **交付前检查**：`mimetype` 条目顺序与压缩方式、文件清单与原件一致、链接与锚点无悬空。
