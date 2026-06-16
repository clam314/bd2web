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
│   └── zh.json             官方中文名（fetch_zh_names.py 抓取）
├── upstream/               [.gitignored] sparse clone myssal/Brown-Dust-2-Asset 的 spine/
├── bg/                     [.gitignored] APK 提取的技能动画背景图（55M，82 张）
├── tools/
│   ├── sync.sh             同步上游 + 重建 roster
│   ├── gen_roster.py       扫描 upstream + bg 生成 data/roster.json
│   ├── fetch_zh_names.py   从 gamekee 抓官方中文名
│   └── extract_bgs.py      从 APK 备份解 cutscene 背景到 bg/
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

### 已固化的"游戏化"效果

| 效果 | 实现 | 数据来源 |
|---|---|---|
| 立绘形态 | 整套动作锁定到待机包围盒的固定取景（见下「立绘取景锁定」）| spine 包围盒 |
| 技能动画串联 | `A_cut → B_cut → loop` 真实序列 | APK Timeline `CharXXXXXX_Skill` |
| 横屏取景 | 固定窗口 1600 骨骼单位、原点居中略上移 | APK RectTransform 1600×720 + SkeletonGraphic scale=1 |
| 后期效果 | CSS 暗角 + brightness/contrast/saturate | APK Volume Profile（ACES + ColorAdjustments + Bloom） |
| 场景背景 | 同一镜头共享，按动作切换 bg[idx] | APK `char<id>_back<N>.png` 提取 |
| 中文名 | 角色 + 服装名 | gamekee `/v1/wiki/entry` |
| 服装合并 | 一套服装 = 立绘 + 技能动画（gamekee 风格） | gen_roster.py 按 costumeId 合并 |
| 动作命名 | 立绘"待机/对话/互动"，技能"动作1/动作2" | 启发式 |

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
