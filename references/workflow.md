# 详细工作流：提取 → 资料库 → 翻译 → QA → 回写 → 横排 → 验证

> 目录约定以 novel-translation 项目为参考实现；用于新作品/新工作区时沿用同样的目录结构与脚本设计，只替换卷号与路径。

## 0. 目录结构约定

```
项目根/
├─ books/ 或 sources/        # 原始来源（只读）：vXX-jp.epub / vXX-jp.txt / vXX-jp.docx；如有官方中译 vXX-cn.* 一并放这里
├─ knowledge/                # 长期资料库
│   ├─ glossary.md           # 术语表（人物/地名/组织/固定译法/符号）
│   ├─ characters.md         # 人物设定、语感、称呼总表
│   ├─ style-guide.md        # 文风指南
│   └─ dialogue/             # 角色对白分桶（README + voices.jsonl + 每角色 md）
├─ work/
│   ├─ extracted/vXX-jp/     # 提取结果（只读）：chapters.json、chapters/*.md、full.md、toc.md、images/
│   ├─ alignment/            # 日中对齐（段落级 + 句子级）
│   ├─ translation-memory.jsonl   # 人工译例库（JP→ZH，含 tags）
│   ├─ vXX-cn/chapters/*.md  # 译文（与日文 md 逐行对应）
│   ├─ vXX-progress.md       # 进度/术语备忘/日志
│   ├─ vXX-cn-vertical.epub  # 竖排备份（回写产物）
│   └─ scripts/              # 工作脚本
└─ output/vXX-cn.epub        # 成品（横排）
```

## 1. 输入适配与提取（目标：统一中间格式）

不论来源是什么格式，第一步都产出**同构的规范化中间格式**，后续翻译/校验/打包全部基于它：

- `chapters/*.md`：`# 标题` 首行；一行一段（保留行首全角空格与 ◆◆◆ 等分隔行）；插图位置 `![illust](images/xxx)`；空行维持节奏。
- `chapters.json`：id / role / title / sources / 字数。
- `full.md`（全书顺序拼接）、`toc.md`（章节索引表）、`images/`（原字节复制）。

### 1.1 EPUB（有原版）

- 读取 `mimetype`、`content.opf`（spine 顺序）、NCX/nav（目录切分依据）。
- 章节切分：按 spine 顺序归入 section，角色命名稳定（frontmatter / toc / prologue / ch01..chNN / interlude / epilogue / afterword / bonus1.. / illustration / colophon），保证多卷间可直接配对。
- 逐段输出：ruby/tcy 注音剥离为纯文本；插图以 `![illust]` 保留位置。
- 提取校验：段落数、图片引用数、文件清单与原件一致。

### 1.2 TXT（常见于网络流传版）

- 编码识别：优先 utf-8-sig / utf-8，其次 cp932 / shift_jis（日文 TXT 常见），再试 euc-jp。
- 章节切分：用正则匹配章节行（第N章 / 第N話 / プロローグ / エピローグ / 幕間 / あとがき / 特別短編 等）；模式参数化，不同作品先抽样确认。
- 段落：默认一行一段（日文 TXT 通常已如此）；若是硬换行版式，用"空行分段"模式合并连续行。
- 插图：TXT 无内嵌图；如另有图片目录，按文件名顺序在对应位置插入 `![illust]` 标记（位置需人工确认）。
- 参考脚本：`scripts/txt_to_md.py`（编码回退 + 章节正则 + 一行一段，产出 chapters/*.md 与 toc.md）。

### 1.3 Word / docx

- 段落与标题：解析 `word/document.xml` 的 `w:p`；标题样式（Heading / 見出し / 标题 1 等）作为章节切分点；无样式时按章节正则兜底。
- 图片：docx 本质是 zip，图片在 `word/media/`；按 `document.xml.rels` 的 r:embed 关系把图插入到段落位置（插画页可近似）。
- 注音（ruby）：Word 通常丢失或退化为括号/双行文字——不要强行恢复；读音以官方资料或词典核对。
- 工具：`python-docx` 最省事；无依赖时用 zipfile + lxml 解析 document.xml。
- 产出必须与 1.1 同构（`# 标题` + 一行一段 + `![illust]`）。

### 1.4 其他来源

- HTML / 网页：去标签转 md（保留段落与标题层级），图片下载到 images/。
- azw3 / mobi：先用 calibre（ebook-convert）转 EPUB，再走 1.1。
- PDF：仅当无其他来源时考虑；优先文本层提取，扫描版需 OCR，质量风险高，段落结构需人工校对。

> 提取完成后做一次结构校验（章节数/段落数/插图数），产物存入 `work/extracted/vXX-jp/`（或来源同名目录）。

## 2. 资料库（两种条件分支）

### 有官方中译（首选）

- **对齐**：日文 × 官方中文做段落级 + 句子级对齐（相似度/DP）；低置信度不强行配对。
- **TM（translation-memory.jsonl）**：1:1 组 score≥0.60、合并组≥0.70 才收录（精度优先，宁缺勿滥）；条目含 `jp`/`zh`/`tags`（人物、术语、场景），便于按关键词检索。
- **glossary.md**：人物、地名、组织、固定译法、高频词、标点/符号处理；只收录经核对与复现的译法；官方译法明显冲突时以原文为准且不写入。
- **characters.md**：自称、称呼、语感、例句 + 称呼总表（说话人 × 对象，核对用）。
- **style-guide.md**：文风通则、称呼本地化、标点规则。
- **对白分桶（dialogue/）**：按角色归集对白（规则 + 说话人交替推断）；未归属宁可不用（宁缺勿滥）。

### 无官方中译（只有日文原版）

- **术语先行**：翻译前先通读/扫描原文，抽取高频专名、术语、称呼，定译并记入 glossary/characters，再开译（否则边翻边定会导致前後不一致）。
- **自建 TM**：把自己既往已交付的译本（同系列/同作者）按句子切分入库；后续每卷持续累积，风格越用越稳。
- **风格基线**：写一份 style-guide（文风、称呼、标点）；可参照同类出版译作定调，但仅作风格参考，不建 TM 条目。
- **对白分桶**：可直接从自己既往译本按角色归集（比从零推断更准）。
- 详细做法与检查清单见 [no-official-cn.md](no-official-cn.md)。

**维护原则**：新卷只添加经确认的新信息；与既有条目冲突时以既有条目/日文原文为准。

## 3. 翻译（逐场景）

- 场景划分：以 ◆◆◆、章节边界、时间/地点/视角转换为界；一次翻译一个完整场景或合理段落组（几十至一两百段），不一次翻整卷。
- 每个场景动笔前：按人物/术语/表达检索 TM（如 `show_term.py 关键词`），把相关人工译例作为风格参考（不是照抄）。
- 硬约束：标题/段落/分隔符/插图位置与日文 md **逐行对应**；不合并、不拆分、不增删段落。
- 行文：中文自然、符合轻小说阅读习惯；对白按角色语感（characters.md + dialogue/）；吐槽、敬语、口癖分别处理。
- 记录：每章完成更新 `work/vXX-progress.md`（状态表 + 术语备忘 + 日志）；新称呼/术语记入待并入清单，卷末并入 knowledge。

## 4. 自检与 QA

- 每章：结构 1:1 检查（段落数/标题/◆◆◆/插图位置）——立即做，别攒到最后。
- 全卷 QA：禁用表记、假名残留（允许作者/插画师名）、术语一致性计数、段落长度比（<0.25 或 >3 报警）、连续重复、Markdown 残留。
- 所有问题清零后才进入打包；不能以"大概没问题"跳过。

## 5. 打包（两种路径）

**路径 A：有原版 EPUB（回写，首选）**

- 以日文原版 EPUB 为底本，只替换 XHTML 文本；ruby/tcy 等行内标记随段落替换移除。
- 目录页 / NCX / nav 标签中文化；奥付与版权声明不回写（保留日文）。
- 输出竖排备份 `work/vXX-cn-vertical.epub`。

**路径 B：无原版 EPUB（自建）**

- 按 EPUB 3 结构模板自建：mimetype / META-INF/container.xml / content.opf / nav + toc.ncx / Styles / Text/*.xhtml / Images。
- 正文页直接生成横排（`hltr` + 中文样式），成品即 `output/vXX-cn.epub`；不需要"竖排备份 → 横排转换"两步。
- 模板、样式与验证要点见 [epub-packaging.md](epub-packaging.md) 的"无原版 EPUB 时：自建 EPUB"。

## 6. 横排转换（仅路径 A）

- 从竖排备份生成横排成品 `output/vXX-cn.epub`：`vrtl→hltr`、`xml:lang`、`sep-break`、CSS 覆盖块、OPF 3 处、说明页文案。
- 详细参数与覆盖块全文见 [epub-packaging.md](epub-packaging.md)。

## 7. 验证与交付

- **竖排验证**（vs 日文原版）：文件清单一致；仅"预期修改清单"文件变化、其余字节一致；XHTML 结构保留（p/img/a/id）；链接/锚点无悬空；目录标签已中文化；正文无假名残留；抽查关键译文句。
- **横排验证**（vs 竖排备份）：逐文件 diff 且变化文件"只能由白名单变换得到"；无 `vrtl` / `xml:lang="ja"` 残留；sep-break 计数与译文中 ◆◆◆ 数一致；OPF 方向/语言正确。
- **渲染抽查**：解包成品 → 本地 HTTP 服务（`python -m http.server`）→ Playwright 打开正文页截图 → 核对横排/缩进/分隔符/标题 → 关闭进程与标签页。
- **自建 EPUB（路径 B）验证**：无原版可 diff，改为——①EPUB 结构合法（mimetype/OPF/nav/链接/锚点）；②正文与译稿 md 段落映射一致（脚本重建或抽章核对）；③CSS 生效（渲染抽查）；④无假名残留；⑤如有旧版成品，与旧版逐文件 diff。
- 交付物：`output/vXX-cn.epub`（成品）、`work/vXX-cn-vertical.epub`（仅路径 A 的备份）、译文 md、进度文档。

## 8. 修订/审核回合

- 收到审核问题清单后：**逐项回原文核对**（不盲改；确认成立→对点修改，有异议→说明依据）。
- 只改必要行；改后重跑一级（结构）+ 二级（QA）。
- 重新打包（回写→横排），并与修复前**逐文件 diff** 确认只有预期文件变化。
- 汇报修改前后对照与验证结果；旧成品备份到临时目录供复核。
