# 项目模板与检查器约定

用 `python scripts/project.py init <新目录>` 复制这些模板，或手工复制。初始化只创建记录，不会制作作品；拒绝覆盖已存在目录。

project.json 是本方法的最小记录模型，不要求改造已有编辑器的内部格式。已有工程可由适配器输出这一份检查清单。它不支持把多轨道重叠当作镜头重叠；多轨道放在一个叙事scene内部，用cues描述，或另外实现专门验证器。

| 字段 | 含义 |
|---|---|
| schemaVersion | 本包格式版本，当前1 |
| revision | 当前源工程版本标记，修改后更新，证据需匹配 |
| stage | research / storyboard / web / export |
| exportAuthorized | 本次是否授权编码；false不阻止Web检查 |
| source.path / sha256 | UTF-8正文文件、原始字节hash；不得为通过检查而自动改hash |
| assets | id、工程内相对路径、identity、purpose、provenance、license |
| speakers | id、name、identityAssetId（无图时null，使用中性图标） |
| scenes | id、start、duration、sourceRange、informationTask、status、keyframes、cues、quotes |
| evidence | id、scene、revision、mode、range、path、findings |

`sourceRange=[start,end]` 使用解码后Unicode码点索引，左闭右开，保留所有标点。Python字符串索引与此一致；JavaScript遇emoji等非BMP字符时应用 `Array.from(text)`，不能直接用UTF-16偏移混算。原稿有独立标题/附录时在项目中声明正文范围，不通过改动文字强行满足覆盖。

镜头时间以秒为单位，必须为有限非负数；duration大于0。总时长由实际声音或用户方案决定，允许durationSeconds为空的早期规划。检查器按scene在列表中的顺序检查，不自动排序，避免掩盖编排错误。没有源音频的示例时间只是设计时间。

keyframes 保存 `path/localTime/role`，文件需实际存在；三帧存在不证明同一构图、实际看过或先于代码创建，另用分镜记录与观察记录证明。smallFix=true仅用于明确的小改，不能为逃避分镜把重做标为小修。

quotes 保存 `text/sourceRange/speakerId`；直接引语逐字与正文切片匹配。术语、绰号和间接转述不要伪装成quotes。身份图片只作身份用途，未知归属按当前项目授权处理。

evidence mode 可为static、sampled-playback、continuous-motion、audio、technical、user-feedback。range是镜头内秒区间。检查器验证文件引用与版本，不验证证据内容真实；continuous-motion需实际具备并使用连续观察能力。

status 值：planned / storyboard / implemented / observed / accepted。observed必须有evidence记录以scene字段关联本镜头，但静帧证据不等于动态通过；accepted另外需要user-feedback记录。程序不代替用户做美术选择。

检查器不检查全文是否完整覆盖、文字实际是否可见、画幅合理性、三帧是否同场景、素材与引语是否真实对应。sourceRange只检查单段范围是否合法，不能用结构通过证明全篇无漏稿。以上仍需按方法正文进行内容与视觉检查。

机读空模板：[project.json](project.json)。人工记录：[工作表](项目工作表.md)、[分镜](STORYBOARD.md)、[参考](REFERENCE.md)、[观察](REVIEW.md)、[续做](STATE.md)、[方法增量](LESSON.md)。
