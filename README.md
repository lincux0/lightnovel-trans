# lightnovel-trans

面向 AI Agent 的日文轻小说中文翻译工作流：按需完成输入提取、术语与人物语感维护、逐场景翻译、审核修订和 EPUB 交付。默认简体，也可遵循用户的繁体与地区用语要求。

这是**工作流型 skill**，不是自动翻译服务或全格式转换器。它提供三项 Python 辅助脚本，EPUB/DOCX/PDF 的提取与打包需使用目标项目已有工具或自行适配。只读审核不会自动改稿或打包。

## 适用范围

| 场景 | 支持方式 |
|---|---|
| 文字型、可重排 EPUB | 按真实包结构适配提取与回写，不绑定出版社模板。 |
| TXT | 附带切章脚本；编码、章节规则与硬换行先抽样确认。 |
| 有/无可靠中译对照 | 按需建立 TM 或从原文建立术语与风格基线。 |
| 译稿、对照文本、只读审核、授权修订 | 根据用户范围执行，EPUB 不是强制产物。 |
| DOCX/HTML 等可提取来源 | 有流程指引，需额外适配及内容覆盖核对。 |
| 固定版式、PDF/OCR、复杂图文与语义 ruby | 先评估和校对输入，不承诺通用自动转换。 |

翻译判断仍依赖 Agent 的日语理解与人工审核，脚本通过不能证明语义正确。详细适用性评估见 [docs/skill-review.md](docs/skill-review.md)。

## 安装与使用

将本目录复制到支持 `SKILL.md` 的 Agent 的技能目录，并保留 `references/` 和 `scripts/`。例如 Codex 可放在用户技能目录 `~/.codex/skills/lightnovel-trans/`；Windows 对应 `%USERPROFILE%\.codex\skills\lightnovel-trans\`。以实际 Agent 的发现规则为准。

安装后可明确调用 `$lightnovel-trans`，例如：

> 使用 $lightnovel-trans 翻译 sources 下的日文小说，先建立本作品术语，交付简体译稿，不制作 EPUB。

> 使用 $lightnovel-trans 只读审核日中译稿，逐段核对语义并输出问题清单，不修改文件。

入口见 [SKILL.md](SKILL.md)。此包不包含模型、API 密钥或调用服务配置。

## 脚本

三个脚本只用 Python 标准库。示例按项目工作目录运行，路径替换为本包实际位置；每个脚本均支持 `--help`：

```sh
# 转换前确认编码和标题规则；输出目录必须为空或不存在
python /path/to/lightnovel-trans/scripts/txt_to_md.py sources/volume.txt work/extracted/volume-jp --encoding utf-8

# 默认 1:1 结构检查；返回非零表示失败或输入错误
python /path/to/lightnovel-trans/scripts/verify_alignment.py work/extracted/volume-jp/chapters work/volume-cn/chapters

# 假名扫描；按本作品配置原文保留词和原文保留文件
python /path/to/lightnovel-trans/scripts/check_kana.py work/volume-cn/chapters --exclude colophon --allow "原文保留的名字"
```

TXT 脚本仅生成 `chapters/*.md` 和 `toc.md`，不生成完整 EPUB；`--paragraph-mode blank` 用于已确认的硬换行来源。其他分隔行可通过重复 `--separator` 指定；不要用简单自动检测替代来源核对。

## 维护验证

在本仓库目录运行无需额外依赖的回归测试：

```sh
python -B -m unittest discover -s tests -v
```

参考资料与脚本均按需加载，无需建立不存在的空资料库或先安装整个翻译工具链。

## 许可证与发布范围

本仓库的技能说明、辅助脚本和测试采用 [MIT License](LICENSE)。许可证不覆盖用户处理的小说、插图、官方译文或 TM 语料；这些材料不随本包发布。

目标仓库：[lincux0/lightnovel-trans](https://github.com/lincux0/lightnovel-trans)。
