# 交接文档（HANDOFF）

> 写给下一台电脑上的 Claude Code / 开发者。先读这份，再读 [README.md](README.md)。
> 最后更新：2026-06-12

## 项目一句话

纯静态网站：用 Spine 官方 Web Player 在浏览器实时渲染《棕色尘埃2》角色骨骼动画。
全屏沉浸式播放，左缘滑出菜单。无构建步骤、无框架、无后端，核心就一个 [index.html](index.html)。

## 分支与部署状态

| 分支 | 状态 |
|---|---|
| `main` | 线上版（用户确认过）。GitHub Pages 自动部署到 https://clam314.github.io/bd2web/ |
| `wip/costume-merge` | **进行中的重构**（见下），本地已验证、用户尚未视觉确认。继续开发在这个分支上做，用户确认后合入 main |

部署形态有两种，同一份代码自动适配（见 index.html 顶部 `ASSET_BASE`）：
- **GitHub Pages**：素材走 jsDelivr 引 myssal 仓库（钉 commit，常量 `UPSTREAM_COMMIT`）；每周六 GitHub Actions 自动同步上游并重建 roster（[.github/workflows/sync.yml](.github/workflows/sync.yml)）
- **家庭主机**：`./tools/sync.sh`（sparse clone 上游 spine/ 约 2.8GB 到 `upstream/`）+ `docker compose up -d`，端口 8080

本地开发：`python3 -m http.server 8080`，浏览器开 `http://localhost:8080`。
加 `?cdn=1` 可在本地模拟 Pages 的 jsDelivr 素材路径。

## wip/costume-merge 分支做了什么（已完成、待用户确认）

参照 gamekee 服装拆解结构（每套服装 = 立绘 + 技能动画）重构：

- roster 结构变更：原来立绘和 cutscene 是两个并列"服装"条目，现合并为
  `{label, idle:{skeleton,atlas}, cutscene:{skeleton,atlas}|null}`（343 条 → 192 套）
- 菜单：角色 → 服装（一套一条）→ [立绘|技能动画] 形态切换 → 动作条目
- 动作命名：立绘的 idle/idle_talk/motion → 待机/对话/互动；技能动画条目编号"动作1（N段连播）/动作2…"，悬停 title 显示原始动画名
- 串联播放（用户选定的 B 方案）：cut_1→cut_2→cut_3→loop 自动连播；同名配对（cut_1→cut_1_idle）优先；`_ef` 特效片段不串入；高亮跟随当前片段
- 表情 `_face*` 仅立绘形态显示，轨道1叠加、可开关

## 进行中/未做的任务（按用户优先级）

### 1. 中文角色名/服装名（官方中文，来源 gamekee）— 调研完成，待实现

数据通路已验证：

- 词条列表 API：`GET https://www.gamekee.com/v1/wiki/entry`，请求头要带
  `Referer: https://www.gamekee.com/zsca2/` 和 `game-alias: zsca2`。返回里有角色页 id 和中文标题（结构还没完全摸清，data 下有 new_update_list 等多个 list，需要找全量目录字段）
- 单页内容：`GET https://api-cdn.gamekee.com/wiki2.0/pro/50118/content/<页面ID>.json`（带 gamekee Referer）。
  content 字段是嵌套 JSON 字符串，里面 `type:"live2d"` 模块带 `json/atlas` 文件名（含 charXXXXYY，可反推 costumeId）,
  相邻 `type:"text"` 节点是"立绘live 2d / 技能动画1 live 2d / 互动动画live 2d / 剧情动画live 2d"等标签，
  模块所在的服装分组标题就是**官方中文服装名**（这一层的解析还没写）
- 解析示例代码在 git 历史和 tools/ 里没有，参考本文档底部"调研记录"
- 产出设计：`tools/fetch_zh_names.py` → `data/zh.json`（charId→中文名、costumeId→中文服装名），
  gen_roster.py 优先用 zh.json，回退英文 CharInfo，再回退编号

### 2. 技能动画背景图 — 来源已找到，待实现

- 游戏原生背景在 myssal 仓库：`ui/idcard/bg/cutscene/bg_idcard_bg_cutscene_<costumeId>[_N].png`（共 278 张）
  `_2` 后缀对应第二段技能动画（命名有少量不一致，如 067504 只有 `_1`/`_2` 没有无后缀版）
- Pages 直接 jsDelivr 引用即可；家庭主机需 `cd upstream && git sparse-checkout add ui/idcard/bg/cutscene`
  （已尝试，当时 GitHub 网络中断未完成，**新机器上需要重跑**）
- 渲染方案建议：技能动画形态时给 #stage 设 CSS background（center/cover），bg 编号与动作条目编号对应，没有对应编号就用第一张；立绘形态无背景
- gen_roster 需要把每套服装的 bg 文件列表写进 roster（用目录扫描/ls-tree）

### 3. 互动动画 / 剧情动画（未开始）

gamekee 页面还有"互动动画"（约会，`spine/illust/illust_dating*`）和"剧情动画"（`spine/illust/illust_special*`），
upstream 的 spine/illust/ 里有素材。可作为服装之外的第三类形态加进菜单。注意社区查看器
（Jelosus2/BD2-L2D-Viewer，src/components/SpineViewer.vue）对约会动画用 idleN(轨0)+动画(轨1) 双轨播放，照抄它的逻辑。

## 已知坑（重要，新会话务必先读）

1. **gamekee CDN 有 Referer 防盗链**：浏览器热链会 567。脚本下载带 `Referer: https://www.gamekee.com/` 即可。网页里永远不要直接引 gamekee 资源。
2. **贴图 alpha 模式**：gamekee 素材是 pma，myssal 是直通。已实现自动检测（加载完成后读播放器解析的 atlas 页 pma 标记，见 index.html success 回调）。别再写死。
3. **Spine 版本**：素材 4.1.x，运行时必须 4.1（vendor/ 已本地化 4.1.56）。不能升 4.2。
4. **测试环境陷阱**：Chrome 标签页被完全遮挡时 rAF 不跑、fetch/定时器可能冻结——表现为黑屏、骨骼不构建、长脚本把 CDP 卡死。这不是代码 bug！自动化验证技巧：`window.dispatchEvent(new Event('resize'))` 可强制同步渲染一帧；诊断脚本要短、避免 setTimeout/setInterval。
5. **Pages CDN 缓存约 10 分钟**：部署后用户看到旧页面是正常的。抽屉底部有"页面版本"时间戳（document.lastModified）用于辨别新旧；无痕窗口是最可靠的验证方式。
6. **网络会抽风**（GitHub/jsDelivr 间歇不通）：失败最多重试一次，然后转后台任务或换路，不要死磕（用户明确要求，省额度）。
7. **gen_roster 的 CharInfo 修复**：上游 `CharInfo(Dropped).json` 有缺逗号的语法错误，gen_roster.py 里有正则容错，别直接 json.loads。

## 在新电脑上接手的步骤

```bash
git clone https://github.com/clam314/bd2web.git && cd bd2web
git checkout wip/costume-merge
./tools/sync.sh                 # 拉素材 2.8GB + 重建 roster（必须，页面才有东西可播）
cd upstream && git sparse-checkout add ui/idcard/bg/cutscene && cd ..   # 任务2需要的背景图
python3 -m http.server 8080     # 浏览器开 localhost:8080 确认能跑
```

然后对 Claude Code 说："读 HANDOFF.md，继续未完成的任务"。

## 调研记录（实现任务1/2时直接参考）

- gamekee 内容 JSON 解析（已验证可用）：
  ```python
  data = json.loads(open('content_<id>.json').read())   # {'content': '<嵌套JSON字符串>', ...}
  # 递归 walk，type=='live2d' 的 value 含 json/atlas/image/bg/animation 字段
  # bg 字段是 gamekee 编辑传的背景（我们不用它，用游戏原生 ui/idcard/bg/cutscene）
  # animation 字段揭示 gamekee 给"技能动画N"配的默认动画（loop / loop_2 / cut_b 等）
  ```
- 社区参考实现：Jelosus2/BD2-L2D-Viewer（271★）。动画平铺不串联；约5个特殊角色用
  `src/utils/cutscene_mappings.ts` 手工映射多轨合成。我们将来遇到串错的角色，照这个思路在 roster 里加 per-costume 覆盖。
- 卢班希亚 = Luvencia = charId 0675，常用来当测试角色（服装 02/03/04，cutscene 全有）。
