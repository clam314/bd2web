# 项目交接文档（给下一个 AI 看）

**项目**：BD2 (Brown Dust 2) 角色 Spine 动画播放器，纯静态网站
**仓库**：https://github.com/clam314/bd2web （public）
**线上**：https://clam314.github.io/bd2web/
**主分支**：`main`，Pages 自动从 `main` 部署，GitHub Actions 每周六自动同步上游素材

先读这份，再读 [README.md](README.md) 和 [OPTIMIZATION.md](OPTIMIZATION.md)。

---

## 项目结构

```
bd2web/
├── index.html              单页应用，全部 UI/逻辑在这里（无构建步骤）
├── vendor/                 spine-player 4.1.56 已本地化（断网可用）
├── data/
│   ├── roster.json         角色清单（gen_roster.py 自动生成，勿手改）
│   ├── zh.json             官方中文名（fetch_zh_names.py 抓取）
│   └── cutscene_shots.json 每个角色 cutscene 的真实运镜/Bg 切换/调色关键帧（extract_cutscene_shots.py 解 APK Timeline 出，1.6M / 154 角色）
├── upstream/               [.gitignored] sparse clone myssal/Brown-Dust-2-Asset 的 spine/
├── bg/                     [.gitignored] APK 提取的技能动画背景图（55M，82 张）
├── tools/
│   ├── sync.sh             同步上游 + 重建 roster
│   ├── gen_roster.py       扫描 upstream + bg 生成 data/roster.json
│   ├── fetch_zh_names.py   从 gamekee 抓官方中文名
│   ├── extract_bgs.py      从 APK 备份解 cutscene 背景到 bg/
│   └── extract_cutscene_shots.py  从 APK 备份解 Timeline 运镜/调色关键帧（增量提取，--force 全量重跑）
├── .github/workflows/sync.yml   每周自动同步
├── docker-compose.yml      家庭主机部署（nginx）
├── README.md               部署说明
└── OPTIMIZATION.md         后续优化清单（运镜/逐角色取景/粒子等）
```

**外部备份**：`/Users/woods/bd2_gamedata_backup/`（13G，1703 个 Unity bundle + catalog + 解析说明），是这台 Mac 上的本地资源，不在仓库里。所有 APK 派生的数据（背景、Timeline、机位）都从这里挖。带 README.txt 记录解析方法。

---

## 两种部署形态（同一份代码）

代码顶部 `ASSET_BASE` 自动检测运行环境：

| 部署 | 素材来源 | 背景图 |
|---|---|---|
| **GitHub Pages** | jsDelivr 引 `myssal/Brown-Dust-2-Asset@<UPSTREAM_COMMIT>`（commit 钉死在 index.html）；**启动时多镜像探测**，见下 | **目前没有**（bg/ 在 .gitignore） |
| **家庭主机 / 本地** | `./upstream/`（sync.sh sparse clone 到 ~2.8GB） | `./bg/`（extract_bgs.py 从 APK 备份生成） |

本地开发：`python3 -m http.server 8080`，访问 `http://localhost:8080/?v=N` 避开缓存。
本地模拟 Pages 的 CDN 探测：加 `?cdn=1`（会跑 resolveAssetBase 选镜像，抽屉底部「素材源」显示选中域名）。

**CDN 多镜像探测（2026-06-17 加，解决国内「CORS 报错」）**：`cdn.jsdelivr.net` 在国内常被 DNS 污染——
请求落到错误服务器、返回无 CORS 头的页面，浏览器报 `blocked by CORS policy`（看着像 CORS bug，其实是被墙）。
index.html 顶部 `CDN_HOSTS` 列了 5 个 jsDelivr 同源镜像（fastly / b-cdn / gcore / testingcf / cdn 官方兜底），
`resolveAssetBase()` 启动时并行 fetch 一个小文件探测（校验返回内容防污染假响应），用 `Promise.any` 取第一个真可达的
写进 `ASSET_BASE`。全挂则提示「可能被墙，建议家庭主机部署」。要换/加镜像改 `CDN_HOSTS` 即可。

---

## 关键认知（已花费大量额度搞清楚的）

### 数据来源 = 3 个

1. **myssal/Brown-Dust-2-Asset**（GitHub 公开仓库）：194 个角色的 spine 三件套（skel/atlas/png），按服装编号命名，覆盖 idle 和 cutscene。这是核心素材来源，每周由 Actions 跟随。
2. **gamekee.com**（中文 wiki）：官方中文角色名/服装名。fetch_zh_names.py 抓 `https://www.gamekee.com/v1/wiki/entry` 的 5/4/3 星目录，逐页解析 `content/<id>.json`。**注意防盗链**（必须带 `Referer: https://www.gamekee.com/`）。
3. **APK 解包**（手机 → adb pull → UnityPy）：取景框、技能 Timeline、后期参数、场景背景。一次性挖了备份在 `/Users/woods/bd2_gamedata_backup/`，以后不用再连手机。
   - **2026-06-17 突破**：StreamedClip 二进制可以手解（按 AssetStudio 格式 4 字节 time + 4 字节 keyCount + N×20 字节 key），`tools/extract_cutscene_shots.py` 已经把 154 个角色的运镜/Bg 切换/PostProcessVolume 调色全部解出，存 `data/cutscene_shots.json`。脚本按 file.json 里的 bundle hash 做增量。

### ⚠️ 2026-06-23 重大方向转变：技能动画放弃"还原游戏演出"，改 gamekee 风格朴素展示

**背景**：花了 N 轮想还原游戏 cutscene 的完整演出（schedule 串接 / 多 skel 多实例叠播 /
程序化相机跟随 / 变身光罩 flash / 运镜推拉 / 调色切换），用户逐帧对照游戏录屏
（`skill_demo/lathel-skill.mp4`，已 gitignore）后确认**全都不像**。根本原因已查清：
游戏的"技能动画"= spine 骨骼动画 + Unity 相机剧烈运镜（怼脸特写）+ ParticleSystem
粒子（泡泡/星星/光线）+ 后处理（强 bloom 把变身瞬间散开的半成品身体盖住）。**网页
只有 spine 这一层，拿不到那 80% 的 Unity 演出层**——粒子/后处理/相机系统是 spine 网页
播放器架构上无法复刻的（浏览器跑 Unity 也不行：只有提取的资源 bundle，没有游戏私有
C# 脚本程序集，无法重建 Timeline 驱动）。

**决定**：对照 gamekee 角色图鉴（`live2d-img.gamekee.com` 用 spine-player 4.1 播
`cutscene_charXXXXXX.skel.json`）发现——**gamekee 也没还原演出，就是朴素 setAnimation
循环播 cutscene spine 的单个主动作**（`A_cut`/`B_cut` 或 `cut_A`/`cut_B`），spine 默认
自适应取景。于是技能动画改成同款（commit 1d106ef，净删 245 行）。

**现状（已固化）**：

| 效果 | 实现 | 数据来源 |
|---|---|---|
| 立绘形态 | 整套动作锁定到待机包围盒的固定取景（见下「立绘取景锁定」）；动作=待机(idle)/互动(motion) | spine 包围盒 |
| 技能动画形态 | **gamekee 风格**：列出 cutscene spine 的主动作（`cut_*`/`[A-Z]_cut`/`loop*`，正则 `CUT_MAIN`）各自一个按钮「动作1/2/3/4」，点击 `setAnimation(name, loop=true)` 循环播单个动画 + 显示对应背景。**不串接、不叠层、不还原演出**（见 index.html `renderEntries` cutscene 分支 + `playSeq`） | cutscene spine 自带的主动作 |
| 背景 | cutscene 选动作时显示 `costume.bg[entryIdx]`（bg/ 里的 `<id>_<N>.png`），spine-player `backgroundImage` 铺在 viewport 内 | roster `costume.bg` |
| 取景 | 立绘和技能动画**都全屏自适应**（padding 5%，spine 默认按动画包围盒 fit，角色居中铺满）。不再 letterbox 锁 1600:720 | spine 默认取景 |
| Spine 特效叠加（立绘） | 立绘 motion 偶有光效部件，按前缀配对叠 track 2+（`overlayTarget`/`scheduleOverlaysFor`）；**cutscene 不用** | skel 动画命名 |

**已删除的复杂代码**（commit 1d106ef，别再重建）：`SKILL_SCHEDULES`、`playScheduledSkill`、
`cameraFollow`（程序化相机跟随）、`#flash` 变身光罩、`applyTimelineAt`/`startTimeline`/
`stopTimeline`、`sampleTrack`/`lastEventState`、`CUT_W/H` letterbox、多 skel 多实例叠播。
`data/cutscene_shots.json` 和 `extract_cutscene_shots.py` 不再被前端用（运镜数据字段错位
不可信，留着仅作历史参考，可删）。

下面这些是**历史记录**（已废弃的还原尝试），保留是为了让后人别重蹈覆辙——不要再去做
schedule 串接 / 多 skel 叠播 / 相机跟随 / 变身光罩。
| 后期效果 | CSS 暗角 + brightness/contrast/saturate | APK Volume Profile（ACES + ColorAdjustments + Bloom） |
| 场景背景 | 同一镜头共享，按动作切换 bg[idx] | APK `char<id>_back<N>.png` 提取 |
| 中文名 | 角色 + 服装名 | gamekee `/v1/wiki/entry` |
| 服装合并 | 一套服装 = 立绘 + 技能动画（gamekee 风格） | gen_roster.py 按 costumeId 合并 |
| 动作命名 | 立绘"待机/对话/互动"，技能"动作1/动作2" | 启发式 |
| 表情菜单 | 可折叠分组 + 紧凑编号网格（`_faceN`→「表情」、`_faceN_talk`→「说话版」），多于 10 个默认折叠 | `.face-group`，2026-06-17 |

#### 立绘取景锁定（2026-06-16 修，解决「互动比例过小」）

- **现象**：立绘形态点「互动」(motion 动画) 时人物被缩成一个小点（用户以奇迹玫瑰/黎维塔 char003803 为例）。
- **根因**：spine-player 的自动取景 (`calculateAnimationViewport`, vendor 约 14123 行) 是对**整段动画 100 帧采样取包围盒并集**。
  互动动画里有特效/锚点骨骼会甩到 ±4000 骨骼单位外（实测奇迹玫瑰：motion 框 **w=8144 h=8216**，待机才 **w=377 h=1073**），
  并集框暴涨 21 倍 → 人物只占画面约 4.6%。待机/对话包围盒稳定所以一直正常。
- **修法**（[index.html](index.html) success 回调里 `part === "idle"` 分支）：立绘加载后用 `p.calculateAnimationViewport(rest, box)`
  算出**待机(idle)/静止动画**的包围盒，写进 `p.config.viewport` 的 x/y/w/h。spine-player 一旦 viewport 设了 x/y/w/h
  就对**所有**动画都用这个固定框 (setViewport, 约 14087 行)，于是待机/对话/互动同比例同机位 = 游戏里立绘的固定机位。
- **作用域**：只动立绘形态。技能动画形态本就用固定 1600 窗口 (`cutsceneViewport`)，串联用 `animationState.addAnimation`
  绕过 setViewport，均不受影响。fallback：取不到 idle 动画就退回原逐动画自动框（try/catch）。
- **影响面（全量 190 套立绘扫了一遍 motion/idle 包围盒比值）**：严重(≥2×)4 套——char003803 奇迹玫瑰、
  char004202 英格利得·卡迪斯的子弹(7.6×)、char067803 马莫尼勒·奇迹海洋(4.5×)、char000206 悠丝缇亚·泳池派对；
  轻微(1.5–2×)4 套——char000202 / char067701 / char000296 / char003604；其余 180 套 ~1×（motion 本就在待机框内）。
  修法是**通用**的：对 180 套正常的等于无操作（motion 框≈待机框），对 8 套问题套全部修正。已视觉验证 003803、004202。
  （扫描发现 char065103 / char067003 两套 skel 二进制头解析异常 "Offset out of DataView"，与本次无关，疑似导出格式差异，留给后续排查。）
- **可选精修（未做）**：当前固定框 = 待机包围盒 + 4% padding，已是干净的全身居中立绘。若要像 cutscene 那样**像素级**
  对齐游戏内立绘机位，需照 CUT_WIN 的做法从 APK 角色详情界面 prefab 的 RectTransform + SkeletonGraphic scale 挖真值。优先级低。

#### 多 skel + 多实例 叠播 cutscene（2026-06-18 诊断，**未修；之前的修复尝试已部分接入，但方向错，待重做**）

- **现象**：char003803 黎维塔奇迹玫瑰技能动画 cut_B 阶段（wall t≈3.367~4.867s）缺胳膊、缺裙摆、武器尾段消失。用户截图证实。
- **历经两轮挖掘**才搞清楚真实结构（dump 工具：`/tmp/dump_full.py`、`/tmp/dump_skill_scene.py`）：

  **第 1 轮（错的）**：以为是"1 主 skel + 1 副 skel"，副 skel `cutscene_char003803_1` 内的 cut_B_B + cut_B_F 两个动画填补主 skel 抠空的部件。按这个做了：单副 player，cut_B_B 在 track 0、cut_B_F 在 track 1。**结果**：cut_B_F 的 attachment 覆盖了 cut_B_B → 鬼影乱叠；setup pose 默认 attachment 可见 → cut_A 阶段就有飘浮鬼手。

  **第 2 轮（真值）**：dump 了 `Char003803_Skill` Timeline 所在场景 `/CutScene_Char003803_Set/SpineRoot/CutScene/Anchors/object/` 下的 sibling 顺序 + PlayableDirector binding，得出**共 4 个 SkeletonGraphic 实例**：

  | sibling | GameObject 名 | skel 文件 | role | Spine Track | 动画 |
  |---|---|---|---|---|---|
  | [7]  | SkeletonGraphic (cutscene_char003803_1) | `_1.skel` (副) | **back** 背景层 | Spine Track (2)  | `cut_B_B` (t=3.367, 1.5s) |
  | [8]  | SkeletonGraphic (cutscene_char003803) | `.skel` (主) | **main** 主体 | Spine Track     | `cut_A` (t=0, 3.367s) / `cut_B` (t=3.367, 3.133s) / `cut_B` slo×2 |
  | [9]  | SkeletonGraphic (cutscene_char003803) (1) | `.skel` (主) | **fx** 特效 | Spine Track (1) | `cut_A_fx` (t=0, 3.317s) |
  | [10] | SkeletonGraphic (cutscene_char003803_1) | `_1.skel` (副) | **front** 前景层 | Spine Track (4) | `cut_B_F` (t=3.367, 1.5s) |

  Unity UI 按 sibling 顺序绘制（先画在底层），所以 z-order 从下到上 = `back < main < fx < front`，对应 cut_B_B 在角色背后、cut_A_fx 叠在主体之上但在 cut_B_F 之下、cut_B_F 在最前。

  **关键洞察**：每个 SkeletonGraphic 内部就是一个 spine 实例、只播一条 spine track。游戏没有"同一 skel 上多 spine track"的设计——多动画叠播都靠**多 SkeletonGraphic 实例**（即多 spine player 实例）+ sibling z-order 实现。原因：同 spine 实例上多 AttachmentTimeline 互相覆盖（attachment 是 slot 级独占字段，不能 alpha 混合）。这也解释了为什么 cut_A 主体和 cut_A_fx 特效一定要分两个主 skel 实例——cut_A_fx 显示武器/光效用的 attachment 会盖掉 cut_A 的角色身体 attachment。

- **资源都在**：`upstream/spine/cutscenes/cutscene_char003803_1/cutscene_char003803_1.{skel,atlas,png}` 完整（1.6MB skel，含 `cut_B_B` / `cut_B_F` 两个动画）。
- **复现**：本地 `python3 -m http.server 8081`，开 `http://localhost:8081/?v=N` → 黎维塔 → 奇迹玫瑰 → 技能动画 → 动作1 → 看 t≈3.5s。**当前**（commit `e75b372`）能看到主角，但缺件 + 飘浮鬼影 + 镜头偏远（因为主+副共用一个统一并集 viewport 强求对齐导致 cut_A 阶段也用大框）。
- **真正的修复方向**（待做，下一轮要按这个来）：
  1. `roster.json` 里 `cutscene` 改成或扩展为 `cutscene.layers: [{skeleton, atlas, role}, ...]`，按 z-order 由低到高列。role 取值 `back / main / fx / front`（或更通用的数字 index）
  2. [index.html](index.html) `loadPart` 按 layers 顺序在 #stage 下挂 N 个绝对定位 div + 创建 N 个 `spine.SpinePlayer`，自然 z-order 由 DOM 顺序决定（用 `.cut-layer` class，`pointer-events:none`）
  3. 每个 player **只用 track 0**（不在同 skeleton 上叠 Spine track，避免 attachment 冲突）
  4. `SKILL_SCHEDULES` 每条 schedule track 改成 `{layerIdx, clips: [...]}`，每个 player 内部只播自己 layer 的一条 spine 轨
  5. 各 layer player 的 viewport 设为**完全相同的固定框**——主 skel 的 cut_A + cut_B 包围盒并集（不掺副 skel 那种巨大特效 bbox，否则 cut_A 阶段人物太小）。两个副 skel 的世界坐标系与主同（Unity 同 RectTransform 父级），共用主算出来的框即可对齐
  6. layer 起播前要把这个 player 的 skeleton 所有 slot.attachment 设 null（避免 setup pose 默认 attachment 在 wait 阶段画出"鬼影"）；动画实际起播时 spine 的 AttachmentTimeline 会把要显示的 attachment 设回去
  7. dump 工具按 Anchors/object/ 下 sibling 顺序自动识别 layers + 各 Spine Track binding → 各 layer 对应的 SkeletonGraphic GameObject pathID，生成 schedule
- **波及范围**：003803 这套设计估计是 cutscene 通用模式——绝大多数有"前/后景叠层"或"召唤物"的角色都会用 N 个 SkeletonGraphic 实例。挖一遍所有 154 个 cutscene bundle 就知道。命名规律：主 skel 实例命名 `SkeletonGraphic (cutscene_charXXXXXX)`、`(cutscene_charXXXXXX) (1)`、`(2)`...；副 skel 实例命名 `SkeletonGraphic (cutscene_charXXXXXX_1)`、同名多实例靠 path_id 区分。
- **失败的前几轮**（commit 历史里能看到，留作教训）：
  - `2927a7b` 单副 player 多 track：attachment 冲突 → 鬼影
  - `dd1f7fc` per-animation viewport：主+副 各自 fit 自己 bbox → 错位重叠
  - `e75b372` 统一并集 viewport：解了错位，但 cut_A 阶段镜头偏远 + 副 player setup pose 飘鬼影没解决

### 还没做的（见 OPTIMIZATION.md）

1. **运镜曲线**（缩放/平移）—— Timeline 的 Animation Track 数据在压缩二进制里，UnityPy typetree 读不到，需要解 streamed clip 格式或读 il2cpp 类型信息。**用户已要求列入待办，优先级中**。
2. **粒子特效**（水花/光线）—— Unity 原生 ParticleSystem，spine 播放器放不了。除非用 WebGL 粒子另写，**投入产出比低**。
3. **Pages 背景托管** —— bg/ 当前不进仓库，所以线上看不到背景。要么提交进仓库，要么走外部 CDN。
4. **逐角色取景精修** —— 当前所有角色用同一窗口/中心，少数角色可能要单独偏移。

---

## 已知坑（务必先读）

1. **gamekee CDN 有 Referer 防盗链**：浏览器直接热链会 567。脚本下载带 `Referer: https://www.gamekee.com/` 即可，网页里永远不要直接引 gamekee 资源。
2. **贴图 alpha 模式**：gamekee 是 pma，myssal 是直通。播放器在 success 回调里读 atlas 的 pma 标记自动适配，**别再写死** `premultipliedAlpha`。
3. **Spine 版本**：素材 4.1.x，运行时必须 4.1（vendor/ 已本地化 4.1.56）。不能升 4.2。
4. **测试环境陷阱**：用 mcp__Claude_in_Chrome 自动化时，标签页被遮挡 → 浏览器节流 → rAF 不跑 → 黑屏。这不是 bug！可以 `window.dispatchEvent(new Event('resize'))` 或 `player.drawFrame(false)` 强制画一帧。诊断脚本要短，避免 setTimeout/setInterval 把 CDP 卡死。**真实效果用户自己浏览器里看**才准。
5. **本地 http.server 缓存**：浏览器会缓存 index.html 和 roster.json。验证时用 `?v=<timestamp>` 绕过，否则会一直看到旧逻辑。
6. **Pages CDN 缓存 ~10 分钟**：部署后用户看到旧页面正常。抽屉底部有"页面版本"时间戳（document.lastModified），无痕窗口最可靠。
7. **不要死磕失败的命令**：用户明确要求遇到网络/环境失败最多重试一次，然后改后台或换路，省额度（[memory:dont-grind-on-failures](~/.claude/projects/-Users-woods-bd2web/memory/dont-grind-on-failures.md)）。
8. **CharInfo(Dropped).json 有语法错误**：上游 CharInfo 有缺逗号的行，gen_roster.py 已用正则容错，**别直接 json.loads**。
9. **APK bundle Unity 版本被抹**：UnityPy 解析必须设 `UnityPy.config.FALLBACK_UNITY_VERSION = "2021.3.40f1"`。
10. **bg/ 在仓库根，不是 upstream/ 下**：index.html 里 bg 用 `"./" + bg` 而不是 `ASSET_BASE + bg`。
11. **背景是可选的、缺失不致命**（2026-06-17 修）：Pages 没部署 bg/、本地未解包时 `./bg/xxx.png` 会 404。
    背景**不再作为播放器必需资源**（曾经 `config.backgroundImage` 是必需资源，404 会让整套技能动画报
    「Assets could not be loaded」）。现在在 success 里异步加载（`p.applyBg` / `p._bgLoaded` / `p._bgWant`），
    加载成功才挂上，失败就没背景照常播。要让 Pages 有背景＝把 bg 托管到 CDN（见 OPTIMIZATION.md 任务3）。

---

## il2cpp 静态分析 / dump（2026-06-24 加）

想看游戏 C# 逻辑、数值表、类结构时，从 APK 的 il2cpp 里 dump。

- **别用 Cpp2IL**（`2022.1.0-pre-release.21`）：它解析不了本作的 metadata v31，binary init
  阶段读 registration 指针数组越界直接崩。换 **Il2CppDumper**（Perfare），自带搜索回退，能过。
- 工具装在**仓库外** `~/tools/Il2CppDumper`（不进 git）；本机只有 .NET 10 运行时，csproj 是
  `net6;net8`，所以要 roll-forward：

  ```bash
  cd ~/tools/Il2CppDumper/Il2CppDumper && \
  DOTNET_ROLL_FORWARD=Major dotnet run -c Release -f net8.0 -- \
    <libil2cpp.so> <global-metadata.dat> <输出目录>
  ```

  输入取自 `local_device_cache/apk_20260624/`：
  `lib/arm64-v8a/libil2cpp.so` + `assets/bin/Data/Managed/Metadata/global-metadata.dat`。
- 输出在 `local_device_cache/cpp2il_dump/`（**已被 gitignore**）：`dump.cs`(97M/273万行)、
  `il2cpp.h`、`script.json`(喂 IDA 的 `il2cpp.py`)、`stringliteral.json`、`DummyDll/`。
- 游戏主逻辑看 `DummyDll/Assembly-CSharp.dll`（拖 ILSpy/dnSpy），比啃 `dump.cs` 舒服。
- 跑时会打印 `ERROR: This file may be protected` —— 只是警告，后续 `Searching...` 自动搜出
  正确 `CodeRegistration` 照样 dump 成功，看到结尾 `Done!` 即 OK。

### DB 解密(静态逆向拿到 key,但离线解表这条路已放弃 → 改走 frida getter-hook)

想直接解设计库 `Data/<hash>` 拿表的话,已挖到的durable 事实(留档,当前不用):

- **DB 密钥**(libil2cpp.so 反汇编读出,已验证):
  `SHA1(UTF8("spdhdnlwmrpavmtm")) → BitConverter.ToString → Replace("-","")` =
  `67E939EAAE0F44ED3C1091B176A32F5CDC6D3E49`(存档库 CreateLocalDB 和母表 ConnectDB 同一把 key)。
- **免 Ghidra 逆向技巧**:il2cpp 字符串/方法引用走 0xbf 区 usage 槽位间接层。用 `objdump -R` 导出 ELF
  重定位表(1.39M 条 R_AARCH64_RELATIVE)建"槽位→目标"映射,叠加 ScriptString/ScriptMethod 即可解析任意
  函数的字符串和调用。脚本 `/tmp/annot2.py`(反汇编+reloc 注释)、`xref.py`。
- **为何放弃**:这把 key 打不开磁盘上的 `Data/<hash>`——它是加密的 Unity Addressables 内容(b3d5 头、
  全随机熵),真实 SQLCipher db 是运行时 `DBLoadAsset → CreateDBFileFromBytes` 写出后才用 key 开,不落到
  可访问目录。外层 bundle 解密 key 未找到。**所以改走"进游戏 → 被动 hook 高层 getter 读返回对象"**(见下 ✅)。

### 代码层确认的两个结论（2026-06-24，从 dump 读出，回答"情绪语音/热区到底能不能做"）

**(1) 情绪语音映射 = `SpineInteractionPointTable`，无明文捷径。**
该 protobuf 行类（dump.cs `class SpineInteractionPointTable : IMessage`）的列里直接有：
`SoundVoiceName`(repeated，普通点击/动作语音)、`SoundMotionVoiceName`(动作动画语音)、
`LongPressSuccess/Fail/LoopVoiceName`、`SoundFXName/SoundMotionFXName`、键 `Id/GroupId/
InteractionGroupId`。运行时 `SpineInteractionPoint` 按 `(interactionGroupId,groupId,id)` 查表
拿 voice 事件名 → `PlayVoiceSFX(eventName)` 走 FMOD（对应 `Interaction_Char003303.bytes` bank）。
prefab 只给了 illust_dating15/18/19 这 3 个角色硬编码的 `VoiceSoundEventName`（dump.cs
`SpineInteractionGroupData.GaugeSettingData.MotionNameByScore` 旁 `public string VoiceSoundEventName`），
其余角色（含 Nebris）全靠查表。**结论：情绪语音能做，但唯一路径是解出这张表（= 当前后台任务）；
非 root 无运行时捷径。**

**(2) `*_follow` 热区不是"画不了"，是绑在 Spine 骨骼上的。**
Codex 卡在 illust_dating10/13/16/17 的 follow 点静态矩阵落在画面外。但 dump.cs
`class SpineInteractionPoint : MonoBehaviour`（TypeDefIndex 5244）有字段
`SkeletonUtilityBone`（`boneName`/`bone`/`mode`，见 `class SkeletonUtilityBone`：
`public string boneName`）——这些点是 Spine **骨骼跟随**，运行时坐标 = 该 bone 世界坐标，
不是静态 RectTransform。**可行路线（不依赖解密、纯 web 端）**：从 prefab bundle
`common-char-datingillust_assets_all.bundle` 抽每个 follow 点的 `boneName` → dating.html 里用
spine-ts `skeleton.findBone(name).worldX/worldY` 每帧定位热区。可单独立项，不必等解密。

### ✅ 已解决（2026-06-29）：在原生 arm 真机上 frida hook 高层 getter，拿到 `SpineInteractionPointTable`

**突破口**：不解密 db、不 Memory.scan，而是**被动 hook 高层 getter 读返回的 il2cpp 对象**。

- 设备：S25（原生 arm64）+ frida-gadget 重打包客户端（小号）。**Google 登录失效但游客/邮箱登录可用** →
  进得去游戏 → 进心契互动页 → 游戏自己查 `SpineInteractionPointTable`。
- agent：`tools/il2cpp-re/capture_interaction_agent.ts`。
  `Interceptor.attach(RawDataManager.GetSpineInteractionPointTables.virtualAddress,{onLeave})` →
  读返回 `List<SpineInteractionPointTable>`，逐行取
  `Id/GroupId/InteractionGroupId/SoundVoiceName(repeated)/SoundMotionVoiceName`。按 `(name,ig,count)` 去重。
- ⚠️ **致命坑**：别用 `method.implementation=fn` 里再 `method.invoke()` → 调到被替换的自己 → 无限递归卡死。
  读返回值就用 `Interceptor.attach + onLeave`，读取(invoke)跑在游戏线程上才安全（frida 线程异步读会 GC 崩）。
- 语音路径前缀 `Common/CharXXXXXX/Interaction/CharXXXXXX_Int_<情绪>`；每个点 `SoundVoiceName` 是
  repeated（多候选随机播）。

**✅ 统一全量方法（关键纠错）**：`SpineInteractionPointTable` 是**母表(静态设计数据,含所有角色)，不看账号拥有权**。
一开始以为"一个号只能拿一个"是错的——那只是因为游戏只查了当前角色。正解：进任意一个心契把母库连上后，
**在游戏线程里主动循环 `GetSpineInteractionPointTables(gid)` for gid=1..800 一次性 burst dump 全部**
（`capture_interaction_agent.ts` 即此版本：onEnter 抓 `this`，onLeave 里用 `bulking` 标志防重入、循环全 gid）。
一次拿到**全部 14 个情绪型角色，775 行，游戏不崩**。原始 `tools/il2cpp-re/all_interaction_tables_raw.log`，
解析 `data/dating_interaction_tables.json`。

**心契母表 = `SpineInteractionPointTable`**,只含 14 个"情绪型"角色(gid 1-14)的点→情绪语音映射,全量已抓
→ `data/dating_interaction_tables.json`。顺带从 `SpineInteractionTable` 拿到 14 角色元数据
(`SoundVoiceBankName`、BGM、环境音、HasSoundVoiceKR/JP)→ `data/dating_interaction_meta.json`。

⚠️ **注意**:菜单里的 dating15/16/17/19 不在这 14 个心契 gid 里,曾被误判为"客串已删/无解",实际
**都在当前母包**(15=班塔纳067004 / 16=奥利维耶003604 / 17=帕莱特004202 / 19=格兰希特067104),
Spine/热区/动作/情绪语音均已抽到。**19 角色权威映射与状态一律以 `data/dating_charid_map.json` +
`DATING_PIPELINE.md` 为准**,不要再用旧的 gid==菜单号 假设。

**2026-07-01 · 心契点→语音 键不一致 bug 修复(前端,无改数据)**:
前端点热区用 `dating_actions.json` 的 `stage_id_tool` 键精确查 `interactionVoices`,但抽取工具对 toolId 键方案不一致
(尤其 dating19 的 iv 全键成 tool19/20、点击是 tool0 → 55/55 全哑)。修法:`dating.html` `scheduleInteractionVoice`
加 **(stage,id) 兜底**——精确键查不到时回退到同 `stage_id_*` 任一变体。依据:母表只按 (stage,id) 索引语音、与 tool 无关,
且同 (stage,id) 不同 tool 变体语音 0 冲突、每条 iv 语音都对应母表有语音的点 0 反例 → 安全不误触发。修后 14 角色可修复集残留全 0,
浏览器实测 dating19 各点出声、mix 未提取点正确静音。**第三类(mix/special 互动语音)已于 2026-07-03 全库修完归零:
根因是三层基础问题(空 tsv 推断、extract/apply 大小写不匹配、17 号 Char004102 前缀命名),全在本地 bank、
零新 OGG、未连设备;工具补了大小写规范与 char-alias,11 角色重跑,详见 `DATING_PIPELINE.md` 第 7 节任务 6。**

**通用 dump 技巧**：不知道表结构时，`dumpObj(o)` 遍历类的无参 `get_*`，对基础类型(Int/Bool/String 等)
直接取值、对 list(repeated) 取 count+items（见 explore 版 agent）。先 introspection 列 `RawDataManager`
所有 `Get*` 找候选表，再针对性 dump。要主动调表 getter 需先拿 `RawDataManager` 单例：hook 一个必被调的
getter(如 `GetSpineInteractionPointTables`)在 onEnter 取 `args[0]`(=this) 即可。

**houdini 模拟器为何不行**（Genymotion + ARM 翻译，2026-06-29 实测）：frida `Memory.scan`/读内存能用，但
`findModuleByName("libil2cpp.so")`=NULL、Interceptor 没法 hook 译码后的 arm64 → bridge 不可用；内存里也
**没有连续明文 SQLite 库**（自定义 VFS 分散页缓存）。**必须原生 arm 真机。**

**gadget 脚本重载坑**：`on_change:reload` 在 bulk 大量 invoke 后可能失效（reload 不触发）。最稳是
`am force-stop` + 重启游戏让 gadget 启动时重新加载 hook.js（introspection 类不需要进心契，启动即跑）。

---

### ✅ 资源(Spine 立绘)自抽管线 — 可脱离外部 GitHub 仓(2026-06-29 评估+PoC 通过)

**背景**：dating.html 的约会角色 Spine 素材原本从 `myssal/Brown-Dust-2-Asset`(GitHub via jsdelivr)
拉,会滞后(缺 char060804、缺 dating19)。结论：**源头就是游戏,可完全自抽,且永远最新**。

**关键事实(全部实测)**：
- 约会 Spine 全在一个 bundle：`common-char-datingillust_assets_all`(385MB)。设备缓存路径
  `files/UnityCache/Shared/<bundleName>/<hash>/__data`,bundleName 见 `com.unity.addressables/file.json`
  里 readableName。
- **bundle 是标准 UnityFS,无加密**(加密只在 `Data/` 设计库)。UnityPy 直解。版本号被抹成 0.0.0,
  需 `UnityPy.config.FALLBACK_UNITY_VERSION="2021.3.40f1"`。
- 每角色资产：TextAsset `illust_datingN.skel`(Spine 二进制,**版本 4.1.11**,兼容 vendored
  spine-player 4.1.56)、TextAsset `illust_datingN.atlas`、多个 Texture2D 贴图页(名字 = atlas 里
  `.png` 行去掉后缀)。
- **PoC 已验证**：抽出的 dating1 在 spine-player 里像素级完美渲染；抽出的 skel/atlas 与 myssal repo
  **逐字节一致**,贴图像素级等价(RGB 平均差<2/255)。即自抽产物 = 社区 repo 质量。
- bundle 里有 **19 个**约会角色(dating1-19),比 dating.html 的 18 还多 dating19。

**工具**：`tools/extract_dating_spine.py <bundle> [out_dir]` — 解 bundle,按 atlas 页名匹配贴图,
每角色输出到 `<out>/illust_datingN/`(默认 `upstream/spine/illust/illust_dating`,即 dating.html
`useCdn=false` 的本地回退路径)。已用它把全部 19 个抽到 `upstream/`。
依赖 `pip install UnityPy`(PIL 随附)。

**其它获取通道**：catalog 的远程模板
`{BDNetwork.CdnInfo.Info}/Android/{Resolution}/{Version}/<bundle>.bundle` → 解析出 `{Info}` 实际
域名(frida 读运行时属性/抓包)后可直接从官方 CDN 下任意 bundle,不依赖设备。

**同管线可抽一切**：所有角色 Spine/立绘/cutscene 都在各自 bundle(`file.json` 按 readableName 找),
同法 UnityPy 解。`tools/` 里已有 `extract_dating_hotzones.py`/`extract_dating_actions.py`/
`build_dating_character.py` 复用同一 prefab bundle 出热区/动作。

**自托管部署(2026-06-30,脱离 myssal CDN)**：dating.html 在 GitHub Pages(github.io)上原本走
`myssal/Brown-Dust-2-Asset` CDN,但自抽的 dating19 myssal 没有 → 404。已改为自托管:
- 素材仓 **`clam314/bd2web-assets`**(公开,jsdelivr 加速),含全部 19 个约会角色 Spine
  (`spine/illust/illust_dating/<id>/`,即 `extract_dating_spine.py` 的输出结构)。
- dating.html 的 `CDN_ASSET_BASES` 指向 `clam314/bd2web-assets@${ASSET_COMMIT}`
  (jsdelivr cdn/fastly/gcore/testingcf 多镜像 + raw.githubusercontent 兜底),`ASSET_COMMIT`
  钉 commit SHA 保证缓存稳定。本地 `useCdn=false` 仍回退 `./upstream/`。
- **更新素材流程**:重抽(`extract_dating_spine.py <bundle> <临时目录>`)→ push 到 bd2web-assets →
  把新 commit SHA 写进 dating.html 的 `ASSET_COMMIT`。新约会角色(dating20…)同理。
- 注:`index.html`(主角色册)仍走 myssal,sync.yml 只 pin index.html 的 `UPSTREAM_COMMIT`,
  与 dating.html 互不影响。

---

### frida-gadget 注入配方(可复用)

上面 ✅ 突破用的注入流程。工具在 `/tmp`,脚本在 `/tmp/il2build`:
1. venv 装 frida-tools(frida 17.15.3);split APK 合并 `java -jar APKEditor.jar m -i <dir> -o merged.apk`。
2. **注入 gadget(比 objection/apktool 稳,适合 530MB 大包)**:lief 给 `lib/arm64-v8a/libmain.so` 加
   `DT_NEEDED libgadget.so`,frida-gadget arm64 .so 放 `lib/arm64-v8a/libgadget.so`。
3. 配置 `libgadget.config.so`(JSON,命名成 `.so` 才会解压到 nativeLibraryDir):
   `{"interaction":{"type":"script","path":"/sdcard/.../files/hook.js","on_change":"reload"}}` →
   改脚本只需 `adb push`。删 `META-INF/*` → `zipalign -f -p 4` → `apksigner sign` → `adb install`。
   logcat 出 `Frida: Listening on ... 27042` = OK;script 模式 `console.log` 无客户端会丢,要写文件。
4. **frida 17 坑**:`Module.findExportByName` 被删,用 `Process.getModuleByName(name).findExportByName(...)`。
5. **il2cpp-bridge 打包用 esbuild**(frida-compile 编译失败):
   `esbuild agent.ts --bundle --format=iife -o hook.js`。bridge 能按真类名 resolve(未混淆)。
6. ⚠️ **只有被动 read-hook 安全**:`Interceptor.attach` 读返回值/寄存器;主动 `invoke` 在游戏线程卡崩、
   在 frida 线程 GC 不同步崩。重打包客户端 Google 登录失效,用**邮箱/游客登录**进心契。

### FMOD 语音/SFX 提取机制(可复用)

> 音频三层模型、每角色状态、第三类残留一律见 `DATING_PIPELINE.md`;这里只留可复用的提取机制。

- 19 个角色 interaction 语音 bundle 全在设备 UnityCache(`files/UnityCache/Shared/<bundleName>/<hash>/__data`,
  bundleName 按 readableName `common-interactionvoice.../interaction_charXXXXXX.bytes` 查)。
  ⚠️ adb 在 while-read 循环里吃 stdin,加 `</dev/null`。
- 本机解包:`extract_dating_audio.py` 的 `extract_bank()`(UnityPy)取 RIFF FEV → 找 `FSB5` magic 碾出 .fsb →
  `parse_fev()` 出 events/timelines/multiInstruments/waits/waves。vgmstream-cli 转 OGG。
  参数 `--bundle`+`--fsb`+`--event-paths`(GUID<TAB>event:/path)。
- **情绪事件名可从 FEV 内嵌 sample 名推导**(`CharXXXXXX_Int_Smile1_1`,`strings` 即可读),用
  `--infer-event-paths-from-samples`,免设备。
- **GUID→event path 全表** = `local_device_cache/bd2_current_20260624/all-fmod-event-paths.tsv`(56766 事件,
  Codex 从设备 dump)。这是音频映射总钥匙,mix/SFX 事件用它反查,**不用再跑设备 FMOD dump**(那条 error 28 死路已废)。

### ✅ dating 编号↔charId 已彻底定死 + 语音错配已修（2026-06-30）

**权威映射 `data/dating_charid_map.json`(菜单#1-19 → charId)**。方法:frida `gc.choose(DatingFriendsScrollItem)`
读游戏内有缘之客列表项的 `_imageCostume` 纹理名 = `illust_inven_char<charId>_N`(**直接带 charId**)+
`_textName`(中文名),拿到 14 心契的权威 charId;5 个尊爵新装(#7/9/12/14/18)由用户游戏内目视确认。
**铁证:19 个菜单 charId == 游戏内 19 个 `interaction_char` 语音 bank,一一对应不多不少。**

完整映射:#1 char003303 / #2 003402 / #3 003203 / #4 001106 / #5 060802 / #6 067603 / **#7 000296** /
#8 001006 / **#9 001197** / #10 066403 / #11 000706 / **#12 061492** / #13 004102 / **#14 003892** /
#15 067004 / #16 003604 / #17 004202 / **#18 000396** / #19 067104。(★=尊爵=现有角色新皮肤,同基础码,
如 #9 奶牛泰瑞丝 001197 与 #4 保健泰瑞丝 001106 同 0011)。

**关键坑:`dating_audio.json` 原来错配** —— spine 菜单顺序 ≠ 心契列表(costumeTableId)顺序,旧数据按心契
顺序硬配 charId,导致 **#7-14 全部张冠李戴**(查看器播错人的声音)。已修:8 个心契语音是系统性平移,按正确
charId 重贴菜单号(539 文件 rename);4 个尊爵(000296/001197/061492/003892)需新扒。

**语音模型**:采样都是情绪命名 `Char<id>_Int_<情绪>_<take>`(不是 mix)。心契型有精确"点→语音"
(`SpineInteractionPointTable`,`interactionVoices`);动作/尊爵型走"动画→情绪事件→按权重随机播"
(`actions`+`events`,无精确 per 点映射)。**19 个角色全部有语音 bank,全可接。**

提取:`tools/extract_dating_audio.py --bundle <interaction_char的Unity bundle> --fsb <内嵌FSB5>
--infer-event-paths-from-samples --dating-id illust_datingN --char-id charXXXXXX --decode`
(vgmstream-cli 在 /usr/local/bin)。

---

## 在新机器上接手

```bash
git clone https://github.com/clam314/bd2web && cd bd2web
./tools/sync.sh                 # 拉 spine 素材 ~2.8G + 重建 roster
# bg/ 当前只在原作者 Mac 上有（从 APK 解出来的）。要 bg 的话：
#   1. 在原作者 Mac 上 cp -r /Users/woods/bd2_gamedata_backup ~/  到新机
#   2. 在新机上 /tmp/bd2venv/bin/python tools/extract_bgs.py
python3 -m http.server 8080     # 浏览器开 localhost:8080
```

对 AI 说："读 AGENTS.md，继续 OPTIMIZATION.md 里的任务"。

---

## 协作风格备忘（用户偏好，[memory](~/.claude/projects/-Users-woods-bd2web/memory/) 也有）

- 改完先**本地验证**，对的再 push。不要直接推
- 优化清单/待办用 OPTIMIZATION.md 维护，别塞进随机文件
- 大改前先讲清思路再动手；用户更想要"想清楚再做"
- 失败一次就换路，不死磕（额度宝贵）
- 重要决策（公开仓库、删除文件等）用 AskUserQuestion 确认
- 用户在国内，github.io/jsDelivr 间歇不通是正常的

### 心契接入的耐久教训(Nebris/dating1 踩出来的,适用所有情绪型角色)

1. **情绪 voice 按"互动点→语音"、不是"动画→语音"**:`SpineInteractionPointTable` 的语义是点→语音。
   存进 `interactionVoices[<groupId>_<pointId>_<toolId>]`(`voice`=`SoundVoiceName` 点击时播,
   `motion`=`SoundMotionVoiceName` 该点 motion 动画起播时播),**不要塞回 `actions[animationName]`**(会错位)。
   `apply_dating_interaction_voice_actions.py` 默认就走 point-based。
2. **pointKey 必须沿点击链路传到底**:菜单按钮和画面热区都要把 point key 传进 `playInteractionVoice`,
   否则"菜单有声、热区无声"。(2026-07-01 又发现抽取工具 toolId 键方案不一致,已在 `dating.html`
   `scheduleInteractionVoice` 加 (stage,id) 兜底,见上文 07-01 记录。)
3. **热区坐标用 `extract_dating_hotzones.py` 出 skeleton-space**(标 `space:"skeleton"`),
   **不要手调 x/y 或按 `1/scale` 猜**。前端优先读 `data/dating_hotzones.json`,旧 `PREFAB_HOTZONES` 只兜底。
4. **新情绪型角色默认禁用 SFX**(`sfx.disabled=true`):早期 SFX 的 sample choices 混了通用/战斗/别角色音效
   (`Common_Punch_*`、`Char004202_Glitch_*`),先把 voice 验证对,SFX 要运行态证据再开。
5. voice/sfx 分频道 generation,避免连续 `mix→motion` 时后一个动画取消前一个 voice。

### 情绪型心契批量接入 → 已成通用流程

action / hotzone / voice 全部外部数据驱动,前端优先读外部 JSON、旧 `PREFAB_*` 常量只兜底:
- `data/dating_actions.json`(`<groupId>_<interactionId>_<toolId>` keyed)、`data/dating_hotzones.json`(skeleton-space)。
- 工具:`extract_dating_actions.py` / `extract_dating_hotzones.py` / `build_dating_character.py`
  (`--update-hotzones-data --update-actions-data`,单角色接入入口)。
- FEV 解析:未知 WAIT/WAV 候选会被跳过并 warning,不要猜;表里有但 bank 里没有的 `Special*/Motion*/Mix*`
  静默跳过不错播(这批就是第三类残留,见 `DATING_PIPELINE.md` 第 7 节任务 6)。
- ffmpeg `Unknown encoder 'libvorbis'` warning 无害,最终 OGG 已验证是真 Vorbis。

⚠️ **每角色 charId / 覆盖度 / 状态一律以 `data/dating_charid_map.json`(权威映射)和 `DATING_PIPELINE.md`
(单一事实来源,含 19 角色状态矩阵)为准。** 早期按 gid 顺序硬配 charId 的表(dating7=char001006 那种)是错的,已删。

### 尊爵角色交互还原的低成本方法(2026-07-06,dating9 奶牛泰瑞丝首个跑通)

尊爵角色没有心契母表,但**skel 的 slot 命名本身就是语义**(泰瑞丝有 `paint_face/hip/belly`
印章落点、`Gauge*` 计量条、`swinsuit_yes_no`/`arm_L_yes` 猜错猜对、`table_bottle_fall` 打翻等)。
做法：浏览器里对每个点的 mix 动画取 AttachmentTimeline 中**真正设为非空 attachment** 的 slot
(排除置空关键帧;二阶段动画噪声大,先对全组取交集当基线再差分),再叠热区投影位置,即可零运行态
给全部点位标语义 + 按玩家攻略(PTT 等)加顺序门禁。门禁沿用 dating4 先例
(`MERGED_PREFAB_ACTION_IDS` + `PREFAB_POINT_ACTIONS` 的 requires/setFlag/visibleWhen/
hotzoneVisibleWhen);`visibleWhen` 已从 dating4-only 泛化到全角色。详见 `DATING_PIPELINE.md`
2026-07-06 修订说明(含遗留:猜瓶是否随机、印章是否每次重点,需运行态证据)。
