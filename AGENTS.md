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

### Data 表解密进度（2026-06-25，静态逆向拿到 DB 密钥）

目标：拿 `SpineInteractionPointTable`（Nebris 等情绪角色的 动作→语音 映射）。

**✅ DB 密钥已确定（从 libil2cpp.so 反汇编读出，已验证代码路径）：**
```
passphrase = SHA1(UTF8("spdhdnlwmrpavmtm")) → BitConverter.ToString → Replace("-","")
           = "67E939EAAE0F44ED3C1091B176A32F5CDC6D3E49"  (40位大写hex)
经标准 sqlite3_key 设入。存档库(CreateLocalDB)和母表(ConnectDB)用同一把 key。
```
代码地址：取key `@0x6cd56b8`(加载字面量 spdhdnlwmrpavmtm)、转换 `@0x6cd53c8`(SHA1+BitConverter+Replace)、
SetKey `@0x6cd547c` 与母表 SetKey `@0x611c018` 都调它 → `sqlite3_key`@0x7cfe768。

**逆向方法（免 Ghidra，关键技巧）：** il2cpp 的字符串/方法引用走 0xbf 区 usage 槽位间接层，
`script.json` 的 ScriptString(0xc6)/ScriptMetadata(0xc5) 是数据地址、代码不直接 adrp 到那。
解法：用 `objdump -R` 导出 **ELF 重定位表**(1.39M 条 R_AARCH64_RELATIVE)建"槽位→目标"映射，
叠加 `strmap`(ScriptString) / `methmap`(ScriptMethod) 即可解析任意函数的字符串和调用。
工具脚本在 `/tmp/`：`annot2.py`(反汇编+reloc注释单函数)、`xref.py`(扫引用某槽位的代码)、
`strmap.json`/`methmap.json`/`relocs.txt`(派生数据)。llvm-objdump 用 `xcrun -f llvm-objdump`。

**⚠️ 但仍读不出表 —— 卡在"外层 + 文件落地"：**
- 这把 key **打不开** `local_device_cache/.../Data/<hash>` 文件（手动 SQLCipher4/3 + openssl AES
  全试过；也不是 "UnityFS"/"SQLite" 明文）。因为 `Data/<hash>`(b3d5固定头、全随机熵)是**加密的
  Unity Addressables 内容**，不是 SQLCipher db 本身。
- 真实流程：`DBLoadAsset`协程(@0x612805c) 从 addressable 取字节 → `CreateDBFileFromBytes`
  写出 SQLCipher db → `ConnectDB`(@0x611d040) 用上面的 key 打开。写出的 db 不在可访问的
  `/sdcard/Android/data/<pkg>/files/DBFiles/`（启动时该目录为空，可能解到内存或内部存储）。
- 外层 Unity bundle 加密的 key 尚未找到（无 `SetAssetBundleDecryptKey`）。

**下一步（缺的是"文件"不是"密钥"）：**
1. **抓运行时 db**：DBFiles 在数据"首次/更新"处理时才会被写。设法触发重新处理（清 app 缓存有风险，
   需用户同意）再轮询 `files/DBFiles/` 抓 `.db`，拿到后用上面 key 直接开。
2. **root / frida**：root 后从内部存储拿 db，或 frida hook `sqlite3_open` 拿明文（用户当前无 root）。
3. **破外层**：逆 `DBLoadAsset`/addressable 加载，找 Unity bundle 解密 key，离线解 `Data/<hash>`
   → 取内层 TextAsset(=SQLCipher db) → 用已知 key 开。

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

### 运行态提取尝试 + 结论（2026-06-25，frida-gadget 全流程，最终卡死）

目标仍是读出 `SpineInteractionPointTable`。静态解密卡在自定义 SQLCipher（见上），转运行态 frida。
**整套流程跑通了，但被多重墙堵死，最终没拿到数据。如实记录供下次（尤其有 root 时）复用。**

**关键技术结论：**
- **`Data/<hash>` 是通过自定义 SQLite VFS 边读边解密的**，磁盘上没有明文 db。游戏启动期就 open
  `files/Data/t/<hash>`(fd 复用) 读取解密到内存。固定头 b3d5 + stock sqlcipher 打不开 = 自定义
  VFS/编译。**所以离线 stock sqlcipher 这条死路确认。**
- **心契语音数据启动时不在内存**：启动期列读取 hook 只看到 ClientDbVersionInfoTable/服务器URL/
  本地化串，**没有任何 Char/voice**。`SpineInteractionPointTable` 要**进入心契功能**才连对应 db、
  才查。`RawDataManager.GetSpineInteractionPointTables(gid)` 在登录前/没进心契时对所有 gid(0~5000)
  返回空。
- **il2cpp 方法不能从 frida 主动调**：在游戏线程同步跑几千次 invoke → 卡白屏崩溃；在 frida 线程跑
  → GC 不同步直接崩。**只有被动 read-hook 安全**（`Interceptor.attach` 读寄存器/返回值，不 invoke）。
- **重打包客户端无法 Google 登录**（签名 SHA 变了，Google Sign-In/Play Integrity 校验失败）→ 进不去
  游戏 → 心契数据永远不加载。**这是没有 root 时的死结。**

**frida-gadget 注入流程（可复用，工具都在 `/tmp`，脚本在 `/tmp/il2build`）：**
1. `brew install` 不用；用 pip venv `/tmp/fridaenv` 装 frida-tools/objection；frida 17.15.3。
2. 合并 split APK：`java -jar /tmp/APKEditor.jar m -i <splitsdir> -o merged.apk`。
3. 注入 gadget（**比 objection/apktool 稳**，适合 530MB 大包）：lief 给 `lib/arm64-v8a/libmain.so`
   加 `DT_NEEDED libgadget.so`（`lib.add_library("libgadget.so")`），把 frida-gadget arm64 .so 放进
   `lib/arm64-v8a/libgadget.so`。`extractNativeLibs=true` 所以普通压缩条目即可。
4. gadget 配置 `lib/arm64-v8a/libgadget.config.so`(JSON)：`{"interaction":{"type":"script",
   "path":"/sdcard/Android/data/<pkg>/files/hook.js","on_change":"reload"}}` → 脚本放外部目录，改脚本
   只需 `adb push`(不重装)。注意：text 文件命名成 `.so` 才会被 installer 解压到 nativeLibraryDir。
5. 删 `META-INF/*` → `zipalign -f -p 4` → `apksigner sign`(debug.ks) → `adb install`。
6. 验证：logcat 出 `Frida: Listening on ... 27042` = gadget 加载成功；脚本 `console.log` 在 script 模式
   **无客户端时会被丢弃**，要写文件才看得到（`new File(path,"a")`）。
7. **frida 17 API 变更坑**：静态 `Module.findExportByName(null/name,...)` 被删，改用
   `Process.getModuleByName("libil2cpp.so").findExportByName(name)` 实例方法。

**frida-il2cpp-bridge（241 个 il2cpp_* 导出齐全，可用）**：`frida-compile` 需要编译失败的 frida 原生
模块 → 改用 **esbuild** 打包：`npm i esbuild --ignore-scripts` →
`node node_modules/esbuild/bin/esbuild agent.ts --bundle --format=iife -o hook.js`。bridge 能按真实类名
resolve（`RawDataManager`/`SpineInteractionPointTable` 没混淆）。agent 在 `/tmp/il2build/agent.ts`。
拿单例：`Il2Cpp.gc.choose(RDM)` 启动早期为空；可 hook `RawDataManager.GetSQLite`(RVA 0x5B18AE8) 存
`args[0]`(=this)。列文本读取方法 RVA `0x6CD45C4`（被动 hook 它 dump 所有查询出的字符串，安全）。

**下次怎么真正拿到（按可行性）：**
1. **root 设备**最省事：frida-server hook（无需重打包→能正常 Google 登录→进心契→被动 hook 抓），
   或直接从内部存储/内存拿解密 db。当前 Galaxy S25(SM-S931U1) bootloader 锁死不能 root。
2. 非 Google 登录（pmang/邮箱/游客）若可用，重打包客户端也许能进心契，被动 hook(`/tmp/hook_safe.js`,
   hook 0x6CD45C4 + 正则过滤 voice) 自动抓。
3. 被动抓 VFS 解密输出：启动期(登录前)游戏就读 `Data/<hash>` 并解密；若能 hook 到自定义 VFS 的
   解密输出/sqlite 页读取，可拿明文 db 页——但解密原语在无符号 native sqlcipher 里，需深挖。

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
