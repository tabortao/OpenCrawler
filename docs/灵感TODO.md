
- 支持docker部署。
- 支持Skill，使用Skill调用Docker进行下载，就可以实现通过飞书指挥小龙虾机器人来下载文章了。
- token提升安全性，如果就内网调用他，可以不用实现先
- GitHub action生成docker
- Go写一个API项目，通过快捷指令调用，实现把内容传送给项目，然后项目再通过调用各种api、ai加工后把处理后内容发送到notion、飞书多维表格、memos等平台。结合自己的剪藏平台对内容剪藏。