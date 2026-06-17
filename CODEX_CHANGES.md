# Codex 改动说明

## 2026-06-16 心契之约资源页

- 新增 `dating.html`，用于单独展示 `upstream/spine/illust/illust_dating/` 下的心契之约 Spine 资源。
- 在 `index.html` 左侧菜单顶部新增“心契之约”入口，跳转到独立页面。
- 心契页复用本项目现有 Spine Web Player 4.1 本地运行时，不引入构建步骤或外部依赖。
- 此次改动没有修改 `tools/gen_roster.py`、`data/roster.json` 或任何 `upstream/` 资源文件。

## 2026-06-16 心契互动阶段模式

- `dating.html` 增加阶段模式，按 `idleN`、`pointN_*`、`motionN_*` 将心契动画组织为“阶段待机 → 当前阶段互动 → 推进下一阶段”。
- 当前实现先用按钮触发每阶段互动，不猜测游戏内点击坐标；后续可继续解析 Unity prefab 中的交互区域来叠加真实热区。

## 2026-06-16 心契资源取景修正

- `dating.html` 增加统一游戏取景配置，不再依赖 Spine Web Player 针对每个动画自动计算边界。
- 通过 Unity prefab 确认 18 个 `Illust_dating*` 根节点都是 `4096 x 4096` UI 画布；`VP_Illust_dating*` 主要保存 Bloom、Vignette、ColorAdjustments 等后处理参数，没有直接提供 Web 侧 viewport。
- 统一 viewport 可避免 `illust_dating6/7/9/12/13` 这类资源因超大动画边界显示过小，也能绕开 `illust_dating10` 播放 `idle1` 时的 `Animation bounds are invalid` 问题。
- 保留 `VIEWPORT_OVERRIDES` 作为后续兜底：如果个别资源仍有偏移或裁切，可以单独覆盖，不影响其它心契资源。
- `illust_dating10` 额外接入 Unity prefab 中的阶段默认 skin：阶段1 `idle1_1`、阶段2 `idle1_2`、阶段3 `idle3_1`，避免只播放动作但附件不可见导致黑屏。

## 2026-06-16 心契道具逻辑骨架

- `dating.html` 增加当前阶段的道具栏，数据来自 Unity prefab 中的 `InteractionToolGroupDatas` / `spineInteractionToolId`。
- 道具状态会影响当前阶段可见互动点，并在资源提供 skin 映射时切换阶段 skin。
- 已先接入 7、9、10、12、14、16、17、18 等资源的道具/skin 映射；后续可继续把真实热区坐标、计量条、隐藏点和语音事件接进同一套状态机。

## 2026-06-16 心契取景与屏幕比例

- 通过 Unity prefab 的 `Parent` RectTransform 提取每个 `illust_dating*` 的位置、尺寸和缩放，替换原先单一固定 viewport。
- `dating.html` 新增“画面：游戏 / 完整 / 填充”模式；默认“游戏”使用根画布中心的 `4096 x 2304` 横屏 16:9 裁切，更接近手机游戏画面。
- `Parent` 的位置、尺寸和缩放用于分析角色在根画布中的摆放；“完整”模式保留为调试用的容器完整展示，“填充”用于接近铺满窗口的特写效果。
- 当前会话里 ADB daemon 因本机权限被拦截，无法重新连接手机运行态；本次取景修正基于此前从手机缓存提取的 Unity bundle 数据。

## 2026-06-16 证据优先约束

- 后续分析心契资源时，不允许仅凭 Spine 动画命名或页面显示效果猜测游戏逻辑。
- 默认阶段、默认待机动画、skin、道具、互动点、计量条、隐藏点、取景和推进规则，必须优先从 Unity prefab、TextAsset、catalog、bundle 字段或手机运行态截图/日志中找证据。
- 如果暂时拿不到证据，必须明确标注为“假设/待验证”，不能把猜测写成结论或直接落代码。
- 已确认一次反例：`illust_dating18` 的 Unity prefab 指定阶段1默认动画为 `idle1`，页面先前把通用 `loop` 猜作阶段1待机是错误做法。

## 2026-06-16 心契默认阶段动画修复

- `dating.html` 增加 `DEFAULT_STAGE_MOTIONS`，数据来自 Unity prefab 的 `_defaultSpineMotionByGroup.GroupDefaultSpineMotionName`。
- 阶段待机优先使用 prefab 指定的默认动画；`loop` 只在没有 prefab 证据的资源里作为兜底，不再抢占阶段1。
- 已验证 `illust_dating18` 初始为阶段1 `idle1`，推进后阶段2 `idle2`；抽查 `illust_dating1/7/9/10/13/18` 均从阶段1 `idle1` 起始且无报错。

## 2026-06-16 心契 prefab 推进互动首版

- 先以 `illust_dating18` 为样本，从 prefab 互动点脚本中接入 `PlayMixAnimNames`、`_playMotionNames`、`IsNextStateWhenActionEnd`、`ForceIdleWhenNextState`。
- 新增 `PREFAB_POINT_ACTIONS`，只覆盖 prefab 明确标记会推进阶段的 10 个互动点；普通点、计量条、隐藏点暂不猜测。
- 页面会为这些 prefab 推进点生成虚拟互动按钮，不再依赖 Spine 顶层动画名是否存在。
- 已验证 `illust_dating18`：阶段1选择道具14后触发 `point1_14` 进入阶段2；阶段2触发 `point2_11` 进入阶段3，均无报错。

## 2026-06-16 心契 prefab 推进互动扩展

- 从 `/private/tmp/bd2-adb-index/bundles/common-char-datingillust_assets_all.bundle` 只读导出 1257 条 prefab 互动脚本，筛出 43 条 `IsNextStateWhenActionEnd=1` 的推进点。
- `dating.html` 的 `PREFAB_POINT_ACTIONS` 扩展到 `illust_dating1` 到 `illust_dating18`，字段来自 prefab：`_interactionActionType`、`PlayMixAnimNames`、`_playMotionNames`、`spineInteractionToolId`、`ClickMaxCount`、`_gaugeSettingData.IsOn`、`ForceIdleWhenNextState`。
- 当 prefab 明确给出 `ForceIdleWhenNextState` 时，页面按该阶段跳转；当字段为 0 但 `IsNextStateWhenActionEnd=1` 时，页面用 `nextStage: "next"` 表示“动作结束进入下一状态”，目标只按已确认的默认阶段顺序推进。
- 计量条互动目前按“完成一次有效互动后推进”模拟；真实 gauge 累积分数、拖拽路径、隐藏点启停、热区坐标、语音和震动还未实现，不能视为已还原完整游戏逻辑。

## 2026-06-16 心契 prefab 静态热区首版

- 从 prefab 的 `_rectTransform` / `_interactionBoxZoneRectTransform` 沿 RectTransform 父链计算 43 条推进点的静态包围框，坐标经过父节点 anchoredPosition、rotation、scale 矩阵换算到 `Illust_dating*` 根画布。
- `dating.html` 新增画面热区层，只渲染当前阶段、当前道具可触发且与当前 viewport 相交的 prefab 推进热区；点击热区复用 `playPrefabAction`，与左侧 prefab 按钮走同一套状态机。
- 已确认 `illust_dating1` 阶段1热区 `1_18_0 · InteractionZone` 可点击推进到阶段2；`illust_dating18` 阶段1热区 `1_14_14 · interactionBoxZone1_14` 可点击推进到阶段2，并刷新出阶段2的 `2_10_14`、`2_11_0`、`2_12_0` 热区。
- 静态矩阵对部分 `*_follow` touch 点不可靠，已观察到 `illust_dating10/13/16/17` 等点会落到当前 16:9 viewport 外；这些点暂不画假热区，仍保留左侧按钮，后续需要结合 Spine 运行时 bone 坐标或手机运行态验证。

## 2026-06-17 Pages CDN 多源兜底

- `index.html` 和 `dating.html` 的 Pages/CDN 资源路径从单一 jsDelivr 改为多源候选：`cdn.jsdelivr.net`、`fastly.jsdelivr.net`、`gcore.jsdelivr.net`、`cdn.statically.io`、`raw.githubusercontent.com`。
- 本地默认仍使用 `./upstream/`；`*.github.io` 或 URL 带 `?cdn=1` 时启用 CDN 候选。
- 支持 URL 参数 `?asset_base=https://example.com/base/` 手动指定素材根路径；多个根路径可用英文逗号分隔，页面会按顺序失败切换。
- SpinePlayer 加载素材失败时会自动切换下一个素材源并重试当前资源，避免国内环境单个 CDN 域名不可用时直接黑屏。
- 当前环境不能写 `.git/FETCH_HEAD`，且无法连接 `github.com:443`，因此本次未能在沙箱内完成 `git pull` / `git push`；代码侧 CDN 改动已完成并通过内联脚本语法检查。

## 2026-06-17 心契功能边界与接手说明

### 当前页面里的“阶段”

- “阶段”不是游戏原 UI，而是调试/还原用状态机入口。
- 阶段列表来自 Spine 动画命名和 prefab 默认待机证据：`idleN`、`motionN_*`、`mixN_*`、`pointN_*`，并优先使用 Unity prefab 的 `_defaultSpineMotionByGroup.GroupDefaultSpineMotionName`。
- 点击阶段按钮会直接切到该阶段并播放该阶段默认待机，这是为了调试不同待机画面；真实游戏里阶段应由互动完成后逐步解锁，不应允许用户随意跳。
- 当前“推进到阶段N”按钮是调试按钮，播放当前阶段的 `motionN_*` 序列后进入下一阶段；不是游戏原始互动入口。

### 当前页面里的“道具”

- “道具”不是最终 UI，只是把 prefab 的 `spineInteractionToolId` 暴露出来，方便筛选当前阶段哪些互动点在某个工具状态下可触发。
- 道具会影响两件事：
  1. 当前阶段显示哪些 prefab 互动按钮/热区。
  2. 对少量已从 prefab 证实的资源切换 skin，例如 `illust_dating10`、`illust_dating14`、`illust_dating16`、`illust_dating18`。
- 目前道具名称仍是 `道具14` 这种占位名，没有从游戏文本/图标资源里还原真实名称或图标。
- “全部”是调试模式，会把当前阶段所有 toolId 的 prefab 推进点都显示出来；真实游戏不一定允许同时触发。

### 当前页面里的“热区”

- 热区层只针对 `PREFAB_POINT_ACTIONS` 里那些 prefab 明确标记 `IsNextStateWhenActionEnd=1` 的推进点，不覆盖 1257 条普通互动点。
- 热区坐标来自 prefab 的 `_rectTransform` 或 `_interactionBoxZoneRectTransform`，沿 RectTransform 父链计算静态矩阵，再投影到当前 `4096 x 2304` 游戏 viewport。
- 只有与当前 viewport 相交的静态热区才会显示；静态坐标明显落在画面外的点不会画假热区，仍保留左侧按钮。
- 热区点击目前等价于“触发这个 prefab 推进动作”，不区分真实手势。也就是说 `drag`、`gyro`、`touch`、`gauge` 现在都被简化成点击触发。
- 热区里的文字只是调试标签：
  - `拖` 表示 prefab `_interactionActionType` 是 drag。
  - `晃` 表示 gyro。
  - `计` 表示 gauge 开启。
  - 数字表示普通 touch 的序号。
- 这些文字不是游戏内文本，也不会改变触发行为；如果做正式体验，建议默认隐藏文字，只在 debug 模式显示。

### 当前已知问题

- `illust_dating18` 阶段切换有重复感：prefab 里部分动作本身 `_playMotionNames` 包含重复项，例如阶段1 `1_14_14` 记录为 `["motion1_14", "motion1_14"]`。当前页面按证据原样播放，因此会出现重复。下一步需要确认游戏运行时为什么重复记录：可能是两段目的地/循环步骤，也可能应按 destination 次数或 action end 条件处理，而不是简单顺序全播。
- `illust_dating17` 没有热区：当前静态矩阵算出的推进点 `1_26_0` 落在当前 16:9 viewport 外，属于 `*_follow`/bone 跟随类疑似动态坐标，不能直接画。后续要结合 Spine 运行时 bone 坐标或手机运行态验证。
- `illust_dating10/13/16/17` 等 `*_follow` touch 点也存在类似静态坐标异常，不能把 prefab 静态坐标当最终点击区域。
- `gauge` 目前只是“一次点击触发推进”的模拟，没有实现分数累积、阈值、衰减、范围限制。
- `drag` 目前没有拖拽路径、方向、持续时间判定。
- `gyro` 目前没有摇晃设备或鼠标模拟，只是点击触发。
- 隐藏点、普通点、语音、震动、道具图标、真实热区显示/隐藏条件还没有还原。

### 建议下一步计划

1. 先修 `illust_dating18` 重复动作问题：不要直接删重复动画，先回到 prefab 证据，确认 `_destinations`、`_playMotionNames`、`ForceIdleWhenNextState`、action end 条件之间的关系。若重复 motion 对应多个 destination，应实现“按完成条件选择/截断”，并在文档里记录证据。
2. 给热区增加 debug 开关：默认不显示文字或半透明框；开启 debug 后显示 `拖/晃/计` 和 prefab key，避免用户误以为这是游戏文字。
3. 处理 `*_follow` 类热区：从 Spine Web runtime 读取当前 skeleton 的 bone/world transform，把 prefab point 绑定到对应 bone 后再投影到屏幕；无法绑定的继续不画，不能猜。
4. 将 `drag`、`gyro`、`gauge` 从“点击触发”拆成不同交互：
   - drag：鼠标/触摸拖动，至少记录起止点和距离。
   - gyro：桌面先提供 debug 按钮或 shake 模拟，手机可接 DeviceMotionEvent。
   - gauge：按 prefab `_gaugeSettingData.Scores` 和 `InteractableMinMaxRange` 做累积/阈值。
5. 扩展普通互动点前先导出完整 prefab 点表，按 `IsNextStateWhenActionEnd`、`IsPlayRandomMixAnim`、hidden/gauge/longPress 分组，不要从 Spine 动画名反推玩法。
6. 完成每一步都要在 `CODEX_CHANGES.md` 记录证据来源、实现范围、未实现边界；不确定的字段必须标为“待验证/假设”。

### 2026-06-17 复查：18 重复与 17 无热区

- `illust_dating18` 的重复主要出现在 gyro 工具推进点：
  - `point1_14_gyro_tool14 [Override]`：`PlayMixAnimNames=["mix1_14_1"]`，`_playMotionNames=["motion1_14","motion1_14"]`，`ForceIdleWhenNextState=2`。
  - `point2_10_gyro_tool14 [Override]`：`_playMotionNames=["motion2_10","motion2_10"]`，`ForceIdleWhenNextState=1`。
  - `point6_42_gyro_tool14 [Override]`：`_playMotionNames=["motion6_42","motion6_42"]`，`ForceIdleWhenNextState=7`。
  - `point7_13_gyro_tool14 [Override]`：`_playMotionNames=["motion7_13","motion7_13"]`，`ForceIdleWhenNextState=6`。
- 这说明重复不是 Spine 动画扫描误判，而是 prefab 字段里存在重复 motion。当前页面照字段顺序播放，所以会有重复感。
- 不要直接把重复 motion 去重后当结论。需要继续查 `_destinations`、gyro action end、Unity 运行时代码如何消费 `_playMotionNames`。一个合理假设是：重复 motion 可能对应两个 destination/两次 action end，而不是连续完整播放两遍。
- `illust_dating17` 的唯一推进点是 `point1_26_touch [Override]`：`stage=1`、`id=26`、`tool=0`、`PlayMixAnimNames=["mix1_26_1"]`、`_playMotionNames=["motion1_26"]`、`ForceIdleWhenNextState=0`。
- `illust_dating17` 该点没有 `_interactionBoxZoneRectTransform`，只能用自身 `_rectTransform`；它挂在 `Parent > SkeletonGraphic > SkeletonUtility-SkeletonRoot > root > A__ > ALL > 0aaa_ppppppppppppp2 > point1_26_touch [Override]`。
- 静态矩阵投影结果落在当前 16:9 viewport 外，因此页面不显示热区。这个点很可能依赖 Spine bone/运行时 follow 位置，下一步应读取当前 skeleton bone world transform，而不是硬用 prefab 静态坐标。
