# Visual Story Production · 动态叙事制作方法

把内容变成画面、把参考变成可执行方法、把检查结果变成下一轮决策。

这是一个可移植技能包，面向新闻纪实、教学科普、产品与工艺、软件演示、数据故事和社交视频。它总结的是研究、判断、制作与验收方法，不绑定某一条影片、品牌、模型、操作系统或动画框架。

**第一次使用，读 [START-HERE.md](START-HERE.md)。** 把整个目录或ZIP交给另一台电脑上的代理即可；无需访问原会话。支持 Agent Skills 的环境使用 [SKILL.md](SKILL.md)，普通harness按同一文件手动读取。只支持一个文本附件时，使用 [完整手册](FULL-GUIDE.md)；它包含方法正文和模板，执行脚本仍以完整包为准。

## 包含什么

- 19章方法：读稿、全量素材审阅、参考研究、骨架、节奏、GIS、引语、声音、复合运动、分镜、工程、检查与续做。
- 3个跨题材示例与失败诊断，不携带原影片的新闻稿、人物照、音频和第三方视频。
- 项目/镜头/素材/参考/证据/交接模板；一个不覆盖已有目录的初始化工具。
- 可直接运行的时钟与裁切配方、结构检查与自动化测试；另附[12个迁移行为检查题](tests/behavioral-cases.md)。
- [迁移说明](PORTABILITY.md)、[方法来源](PROVENANCE.md)、[交付审计](ACCEPTANCE.md)。

## 开始使用

对代理说：

> 读取这个目录的 START-HERE.md 和 SKILL.md，按其中的方法处理我给你的任务与材料；继承当前要求，实际看参考、先画分镜，再实现和检查，保存可继续的工程状态。

这句话只是入口，不要求用户为每个项目重新编写长提示词。

可选命令（Python 3.10+，仅标准库）：

```sh
python scripts/project.py init ../my-story
python scripts/project.py check ../my-story
python -m unittest discover -s tests -v
python scripts/validate_bundle.py
```

新建项目尚未填写内容，`check` 应报告未就绪，这是预期行为。详细字段和实际示例见[模板说明](templates/README.md)。

## 能迁移与不能打包的部分

可以迁移：完整的决策流程、失败经验、技术配方、检查边界、记录结构和继续工作的方式。

需要目标环境提供：文件操作、实际图像/运动/音频观察、浏览器或编辑器能力，以及新项目素材。技能本身不能授予权限、购买插件、解锁课程或保证不同模型具有相同视觉判断。缺失能力须明确记录，但继续推进不依赖它的工作。

## GitHub 使用

本目录可作为仓库根目录。`SKILL.md` 保持在名为 `visual-story-production` 的目录中；克隆到其他目录名时，安装为技能前重命名对应文件夹。仓库只包含方法、模板、原创示例和脚本。

公开仓库：[rutther/visual-story-production](https://github.com/rutther/visual-story-production)。已提供忽略规则、跨平台文件完整性设置和 GitHub Actions 检查工作流。

本仓库原创的方法文档、提示词、模板、示例和脚本采用 [MIT 许可证](LICENSE)，允许使用、修改、分发和商用，须保留版权及许可声明。外部资料的权利边界见[许可说明](LICENSE-NOTICE.md)。

版本：2.0.0 · 2026-10-18。官方格式依据：[Agent Skills specification](https://agentskills.io/specification)。实现工具是可替换选项，使用前核对维护者当前文档。
