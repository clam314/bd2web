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

## 2026-06-18 心契18 gyro 重复播放修复

- 进一步解析 18 的 `_destinations` 指针后确认：四个重复 gyro 点都各自指向两个独立的 `InteractionPointDestination` MonoBehaviour，对应名称后缀 `_0` / `_1`。
- 两个 destination 的 RectTransform 位于相反方向，例如：
  - `interactionDestination1_14_0.x = 1554`，`interactionDestination1_14_1.x = -1909`。
  - `interactionDestination2_10_0.x = -2187`，`interactionDestination2_10_1.x = 2002`。
  - `interactionDestination6_42_0.x = 2006`，`interactionDestination6_42_1.x = -2242`。
  - `interactionDestination7_13_0.x = -2010`，`interactionDestination7_13_1.x = 2003`。
- 这证明重复 `_playMotionNames` 是按 destination 索引对齐：两个方向各有一个 motion 条目；网页此前把整个数组连续播放，错误地把一次动作播了两遍。
- `dating.html` 只给这四个 gyro 点增加 `destinationIndexed: true`。当前网页的一次点击代表一次完成的 gyro 触发，因此 `prefabActionSequence()` 只消费一个 destination 对应的 motion。
- 没有对所有动作做通用去重；drag/touch/gauge 以及其它资源的重复动画仍按 prefab 原数据处理，避免误删可能有意义的重复步骤。
- 后续实现真实 gyro 方向时，应根据摇晃/移动方向选择 destination index；当前两个索引里的 motion 名相同，所以先取第一个不会造成动画分支丢失。

## 2026-06-18 心契18 七阶段状态图确认

证据来源：

- Unity bundle `common-char-datingillust_assets_all.bundle` 中 `illust_dating18` prefab 的默认待机、推进点、热区坐标和 `ForceIdleWhenNextState`。
- 本地逐个播放 Spine 的 `idle1` 到 `idle7`，对比每个画面的视角和丝袜状态。
- GameKee《满好感角色互动攻略》中“致胜王牌 -莎拉（尊爵不凡）”一节：
  <https://www.gamekee.com/zsca2/644053.html>。文章明确说明先在背后视角撕开丝袜，再转到桌下视角分别处理左右腿，完成后进入二阶段。

已确认状态：

| 阶段 | 默认动画 | 画面状态 | 进入/离开关系 |
|---|---|---|---|
| 1 | `idle1` | 一阶段桌下视角，丝袜完整 | `1_14_14` 切到阶段2 |
| 2 | `idle2` | 一阶段背后视角，丝袜完整 | `2_10_14` 回阶段1；`2_11_0` 或 `2_12_0` 撕开后进阶段3 |
| 3 | `idle3` | 回到桌下视角，左右腿丝袜等待分别去除 | 左侧热区 `3_1_0` 进阶段4；右侧热区 `3_2_0` 进阶段5 |
| 4 | `idle4` | 画面左腿已完成，右腿仍有丝袜 | 右侧热区 `4_1_0` 进阶段6 |
| 5 | `idle5` | 画面右腿已完成，左腿仍有丝袜 | 左侧热区 `5_1_0` 进阶段6 |
| 6 | `idle6` | 二阶段桌下视角，左右丝袜均已去除 | `6_42_14` 切到阶段7 |
| 7 | `idle7` | 二阶段背后视角，丝袜已去除 | `7_13_14` 回阶段6 |

```text
阶段1（桌下/完整） <----> 阶段2（背后/完整）
                              |
                         撕开丝袜
                              v
                    阶段3（桌下/双腿待处理）
                       /                 \
                  先处理左腿           先处理右腿
                     v                     v
                 阶段4                  阶段5
                       \                 /
                        完成另一侧
                              v
阶段6（二阶段桌下/完成） <----> 阶段7（二阶段背后/完成）
```

热区左右也有 prefab 坐标和最终画面双重证据：

- 阶段3 的 `3_1_0` 中心 x 为 `-166.5`，进入阶段4；`idle4` 显示画面左腿已完成。
- 阶段3 的 `3_2_0` 中心 x 为 `168.8`，进入阶段5；`idle5` 显示画面右腿已完成。
- 阶段4 仅剩右侧 `4_1_0`；阶段5 仅剩左侧 `5_1_0`，两者完成后都汇合到阶段6。

页面改动：

- 只为 `illust_dating18` 增加有证据的阶段名称和推进动作名称，阶段按钮会显示“阶段1 · 一阶段·桌下”等说明。
- 互动按钮不再显示无意义的“拖拽1/晃动1”，改为“切到背后视角”“背后撕开丝袜”“去掉画面左腿丝袜”等与实际状态变化一致的文字。
- 本次没有把 drag/gyro 强行改成自制手势判定。prefab 的 destination、长按阈值和方向完成条件尚未全部确认；在找到字段证据前，页面仍保留点击触发的调试行为。

## 2026-06-18 心契18 解锁长按逻辑

重新读取原始 Unity prefab 的完整 MonoBehaviour typetree 后，确认阶段2到阶段6的六个推进点不是普通单击：

- `_interactionActionType = 1`，资源节点本身是 drag 类型。
- `_longPressSettingData.ActionType = 2`。
- `_longPressSettingData.ThresholdTime = 1.0`，六个点完全一致。
- 每个点都明确提供：
  - `LoopMixAnimationName`：按住期间的循环动画，例如 `mix3_1_loop`。
  - `FailMixAnimationName`：未达到阈值释放时的回退动画，例如 `mix3_1_2`。
  - `SuccessMixAnimationName`：达到阈值后的成功动画，例如 `motion3_1`。
- GameKee 攻略同样明确写的是长按撕开、长按左右腿去除，因此本轮把 long-press 作为解锁条件，不要求用户必须拖到 destination。

六个点的原始规则：

| prefab key | 阈值 | 循环 | 失败 | 成功 | 下一阶段 |
|---|---:|---|---|---|---:|
| `2_11_0` | 1秒 | `mix2_11_loop` | `mix2_11_2` | `motion2_12` | 3 |
| `2_12_0` | 1秒 | `mix2_12_loop` | `mix2_12_2` | `motion2_12` | 3 |
| `3_1_0` | 1秒 | `mix3_1_loop` | `mix3_1_2` | `motion3_1` | 4 |
| `3_2_0` | 1秒 | `mix3_2_loop` | `mix3_2_2` | `motion3_2` | 5 |
| `4_1_0` | 1秒 | `mix4_1_loop` | `mix4_1_2` | `motion4_1` | 6 |
| `5_1_0` | 1秒 | `mix5_1_loop` | `mix5_1_2` | `motion5_1` | 6 |

实现范围：

- 18 的上述画面热区改为 Pointer Events 长按，鼠标和触摸共用同一套逻辑。
- 按下先播放 `PlayMixAnimNames` 的第一段，再循环 prefab 指定的 `LoopMixAnimationName`。
- 1 秒内释放播放 `FailMixAnimationName`，随后恢复当前阶段待机，不推进。
- 按满 1 秒播放 `SuccessMixAnimationName`；成功动画结束后才进入 prefab 指定阶段。
- 热区显示“按住”，按压期间有高亮反馈；设置 `touch-action: none`，避免手机浏览器把长按识别成滚动手势。
- 左侧互动按钮仍是分析/调试直达按钮，真实长按操作位于画面热区。

destination 方向证据保留给后续普通拖拽动作：

- `2_11_0` destination `(870, 0)`，向画面右侧。
- `2_12_0` destination `(-846, 0)`，向画面左侧。
- `3_1_0` destination `(-914, 19)`，向画面左侧。
- `3_2_0` destination `(846, -4)`，向画面右侧。
- `4_1_0` 从 `(-168, 212)` 到 `(740, 208)`，向画面右侧。
- `5_1_0` 从 `(-1, 0)` 到 `(-15, -879)`，主要向下。

这些 destination 证明资源还支持方向性拖动，但没有证据表明解锁必须同时满足“拖到 destination”和“长按 1 秒”。攻略与 long-press 字段已足以确认当前解锁方式，因此暂不附加自创距离阈值。

浏览器验证：

- 阶段2短按热区后仍停留阶段2。
- 阶段2按满1秒后进入阶段3。
- `3 -> 4 -> 6` 和 `3 -> 5 -> 6` 两条顺序均完整通过。
- 验证过程无控制台 error/warning。

## 2026-06-18 心契18 视角倾斜/移动逻辑

四个视角切换点的完整 prefab 字段一致：

| prefab key | gyro action | move threshold | sensitivity | destinations | 下一阶段 |
|---|---:|---:|---:|---:|---:|
| `1_14_14` | 1 | 18 | 1500 | 左右各1个 | 2 |
| `2_10_14` | 1 | 18 | 1500 | 左右各1个 | 1 |
| `6_42_14` | 1 | 18 | 1500 | 左右各1个 | 7 |
| `7_13_14` | 1 | 18 | 1500 | 左右各1个 | 6 |

补充对照整个 dating prefab：

- gyro `_actionType=0` 的点没有 destination，使用 `_shakingThreshold` / `_shakingHoldTime`，更接近原地摇晃。
- gyro `_actionType=1` 的点使用 `_movePointThreshold` / `_movePointSensitivity`；18 的四个点额外提供左右 destination，明确是方向移动类交互。
- 四个点的左右 destination 大约位于 `x=-1900~-2240` 和 `x=1550~2006`，说明左右两个方向都可完成视角切换。

官方 UI 资源证据：

- 从 `common-ui-atlas_assets_ui/atlas/interactiongui.spriteatlasv2.bundle` 的 `InteractionGUI` SpriteAtlas 读取到：
  - `icon_interaction_toolbar_14` 是一个特殊角色/工具图标，并非通用陀螺仪图标。
  - `icon_interaction_toolbar_15` 才是标准陀螺仪图标。
- 因此 `point*_gyro_tool14` 的含义是“选中 tool14 后执行 gyro 移动动作”，不能把 tool14 本身直接命名成陀螺仪。
- 目前没有文本资源能证明 tool14 的正式中文名称，页面继续保留“道具14”，不凭图标猜名字。

实现：

- 四个 gyro 热区不再单击触发，热区提示改为“左右倾斜”。
- 手机选择 `道具14` 后启用 `DeviceOrientationEvent`：
  - 竖屏使用 `gamma`，横屏使用 `beta`。
  - 以进入当前阶段后的第一次方向值为基线，变化达到 prefab 的 `moveThreshold=18` 时触发。
  - iOS 会在点击道具14时请求方向传感器权限；拒绝后仍可使用画面拖动。
- 桌面端没有设备方向传感器，增加按住热区水平拖动模拟：
  - 拖动距离达到画面宽度的18%时触发。
  - 18%是浏览器端对 prefab 数值18的明确适配，不声称 Unity 原单位是百分比。
- 左右方向会选择对应 destination index；当前两侧绑定的 motion 名相同，但不再固定消费第一个索引，为以后出现不同方向动画保留正确结构。
- 长按热区位于 gyro 大热区上层，仍可正常完成阶段2到阶段6的解锁，不会被视角拖动抢走。

浏览器验证：

- 阶段1单击 gyro 热区后仍停留阶段1。
- 水平拖动可完成 `阶段1 -> 阶段2 -> 阶段1`。
- 水平拖动可完成 `阶段6 -> 阶段7 -> 阶段6`。
- 四次切换均只播放一次 motion，控制台无 error/warning。

## 2026-06-18 心契18 普通互动第一批（阶段1/2）

本轮开始接入攻略中缺失的普通互动，只覆盖一阶段正面与背面，不提前拼装阶段6牌局。

证据来源：

- Unity prefab 中 `Illust_dating18` 下的 92 个互动 MonoBehaviour。
- prefab 的 `_interactionActionType`、`PlayMixAnimNames`、`_longPressSettingData` 和 RectTransform。
- `illust_dating18.skel` 中每段 mix 动画实际修改的 slot/attachment 名称。
- 巴哈姆特文章 `https://m.gamer.com.tw/forum/C.php?bsn=76207&snA=10163` 的操作说明。

阶段1新增13个普通点：

| prefab point | 已确认对象 | 操作 |
|---|---|---|
| `1_1` | 左胸 | 点击；长按1秒播放 `mix1_1_long` |
| `1_2` | 右胸衣物 | 拖动/长按，含 loop、失败、成功动画 |
| `1_3` | 腹部 | 点击 |
| `1_4` | 泳装下部/润滑 | 点击 |
| `1_5` | 画面右侧大腿 | 拖动/长按 |
| `1_6` | 画面左侧大腿 | 拖动/长按 |
| `1_7` | 画面左侧脚部 | 拖动/长按 |
| `1_8` | 画面右侧脚部 | 点击；长按1秒 |
| `1_9` | 画面左侧高跟鞋 | 点击 |
| `1_10` | 画面右侧高跟鞋 | 点击 |
| `1_11` | 上方中部点 | 点击；身体部位名称暂不猜 |
| `1_12` | 画面左上点 | 点击；身体部位名称暂不猜 |
| `1_13` | 画面右上点 | 点击；身体部位名称暂不猜 |

阶段2新增9个普通点：

| prefab point | 已确认对象 | 操作 |
|---|---|---|
| `2_1` | 脸部亲吻 | 点击 |
| `2_2` | 画面左侧手 | 拖动/长按 |
| `2_3` | 画面右侧手 | 拖动/长按 |
| `2_4` | 胸部 | 点击/长按 |
| `2_5` | 背部 | 点击/长按 |
| `2_6` | 臀部 | 点击/长按 |
| `2_7` | 泳装下部 | 拖动/长按 |
| `2_8` | 按摩椅 | 点击 |
| `2_9` | 小尤里 | 点击 |

实现说明：

- 普通点热区坐标来自 prefab RectTransform，并按 SkeletonGraphic 的 `0.25` 缩放换算到现有游戏窗口坐标。
- 身体热区层级高于覆盖全画面的视角 gyro 区，防止普通点被视角切换区挡住。
- 热区文字优先显示已确认对象，不再只显示无意义的序号。
- long press `ActionType=1`：
  - 短按重新播放普通 mix。
  - 按满1秒播放 success mix。
- long press `ActionType=2`：
  - 按下播放开始 mix 和 loop。
  - 提前释放播放 prefab 的 fail mix。
  - 按满1秒播放 success mix。
- 本轮没有自行补拖动方向阈值。资源虽有 destination，但在完整方向完成条件实现前，仍以 prefab 已明确的1秒长按规则触发特殊分支。

验证：

- 页面内联脚本通过 Node 语法检查。
- `git diff --check` 通过。
- 本轮新增的阶段1/2所有 mix、loop、long 名称均在 `illust_dating18.skel` 中存在。
- 当前受限运行环境禁止监听本地端口，且内置浏览器安全策略不允许打开 `file://`，因此本轮未能进行实际画面点击验证。需在已有本地服务中刷新 `dating.html?v=<新时间戳>` 后继续视觉校准。

## 2026-06-18 心契18 普通互动第二批（阶段6/7）

本轮补齐二阶段桌下与背后视角的普通互动。仍然只接入 Unity prefab 和 Spine 动画能够直接证明的内容，不把阶段6的扑克牌玩法混入普通点击逻辑。

证据来源：

- Unity prefab 中阶段6/7互动点的 `_interactionActionType`、`PlayMixAnimNames`、`_longPressSettingData` 和 RectTransform。
- `illust_dating18.skel` 中对应 mix 动画修改的 slot/attachment。
- 阶段1/2与阶段6/7复用的精确世界坐标。
- 巴哈姆特攻略对阶段7“小尤里头部”等互动的操作说明。

阶段6新增13个普通点：

| prefab point | 已确认对象 | 操作 |
|---|---|---|
| `6_1` | 画面右侧腿部 | 点击；长按1秒 |
| `6_2` | 画面左侧腿部 | 点击；长按1秒 |
| `6_3` | 画面右侧脚部 | 拖动/长按 |
| `6_4` | 画面左侧脚部 | 拖动/长按 |
| `6_5` | 画面右侧高跟鞋 | 点击 |
| `6_6` | 画面左侧高跟鞋 | 点击 |
| `6_35` | 左胸 | 点击；长按1秒 |
| `6_36` | 右胸衣物 | 拖动/长按 |
| `6_37` | 腹部 | 点击 |
| `6_38` | 泳装下部/润滑 | 点击 |
| `6_39` | 上方中部点 | 点击；具体身体含义不猜 |
| `6_40` | 画面左上点 | 点击；具体身体含义不猜 |
| `6_41` | 画面右上点 | 点击；具体身体含义不猜 |

阶段7新增12个普通点：

| prefab point | 已确认对象 | 操作 |
|---|---|---|
| `7_1` | 臀部 | 点击；长按1秒 |
| `7_2` | 画面右侧臀部 | 拖动/长按 |
| `7_3` | 画面左侧臀部 | 拖动/长按 |
| `7_4` | 泳装下部 | 拖动/长按 |
| `7_5` | 小尤里身体 | 点击 |
| `7_6` | 脸部亲吻 | 点击 |
| `7_7` | 画面左侧手 | 拖动/长按 |
| `7_8` | 画面右侧手 | 拖动/长按 |
| `7_9` | 胸部 | 点击；长按1秒 |
| `7_10` | 背部 | 点击；长按1秒 |
| `7_11` | 按摩椅 | 点击 |
| `7_12` | 小尤里头部 | 点击 |

坐标与命名说明：

- 普通点热区继续使用 prefab RectTransform，并按 SkeletonGraphic `0.25` 缩放换算到游戏窗口。
- 阶段6的 `6_35` 到 `6_41` 分别与阶段1的 `1_1` 到 `1_4`、`1_11` 到 `1_13` 复用同一身体区域。
- 阶段7的脸、手、胸、背、臀、泳装、按摩椅和小尤里身体与阶段2对应点复用相同或近似坐标。
- `7_12` 是阶段7独有的小尤里头部点，攻略文字与 prefab 坐标相互印证。

阶段6牌局边界：

- `6_7_0` 是发牌/重发入口，prefab 标记 `IsPlayRandomMixAnim=1`，会在 `mix6_7_1` 到 `mix6_7_6` 六种牌面中随机选择。
- `6_8` 到 `6_34` 包含三张牌的分支、同花/不同花结果、三种梅花特殊反应和结束动作。
- 这些点需要“当前牌面、可点击牌、结果动画、20秒特殊动画、结束动作”的独立状态机。本轮明确不接入，避免把随机牌局错误实现成常驻普通热区。

验证：

- 页面内联脚本通过 Node 语法检查。
- `git diff --check` 通过。
- 阶段6/7共27个动作键与27个热区键完全对应，无缺失或多余热区。
- 本轮新增的57个阶段6/7普通互动动画引用全部能在 `illust_dating18.skel` 二进制中找到。
- 既有视角点引用的 `mix6_42_1`、`mix7_13_1` 不在 Spine 中，页面会按原逻辑跳过不存在的 mix 并播放 motion；这不是本轮新增。
- 当前环境仍禁止监听本地端口，内置浏览器也未能连接本地服务，因此尚未完成实际画面点击校准。需要在用户已启动的服务中刷新 `dating.html?v=<新时间戳>`，重点检查阶段6脚/鞋热区与阶段7小尤里头部热区的位置。

## 2026-06-18 心契18 阶段6扑克牌状态机

本轮实现阶段6牌局，不把 `6_7` 到 `6_34` 当作同时存在的普通热区，而是按照 Spine 时间轴逐步开放当前可操作点。

### 原始资源证据

- `point6_7_touch` 的 prefab 字段 `IsPlayRandomMixAnim=1`，随机播放 `mix6_7_1` 到 `mix6_7_6`。
- 六段发牌动画的 TranslateTimeline 分别只驱动一个牌堆点和三张牌：

| 发牌动画 | 牌堆/重发点 | 三张可选牌 |
|---|---:|---|
| `mix6_7_1` | `6_8` | `6_14`、`6_20`、`6_21` |
| `mix6_7_2` | `6_9` | `6_22`、`6_29`、`6_15` |
| `mix6_7_3` | `6_10` | `6_23`、`6_24`、`6_16` |
| `mix6_7_4` | `6_11` | `6_30`、`6_17`、`6_25` |
| `mix6_7_5` | `6_12` | `6_26`、`6_27`、`6_18` |
| `mix6_7_6` | `6_13` | `6_28`、`6_19`、`6_31` |

- 牌的后续结果同样由动画中的互动骨骼直接证明：
  - `6_14` 到 `6_19` 的动画开放 `point6_32_touch_shake`。
  - `6_20` 到 `6_28` 的动画开放 `point6_33_touch_shake`。
  - `6_29`、`6_30`、`6_31` 是三种独立特殊反应，不开放32/33。
  - `mix6_32_1` 与 `mix6_33_1` 都会在后段开放 `point6_34_touch`。
- 所有 `mix6_7_1` 到 `mix6_34_1` 动画名称均在 `illust_dating18.skel` 中存在。

### 动态热区位置

牌局点的 prefab RectTransform 初始位置在画面外，不能沿用普通身体热区的静态坐标。Unity 的 `SkeletonUtilityBone` 明确将每个点绑定到同名 Spine 骨骼，因此本轮直接读取动画中段的骨骼世界坐标，再乘 SkeletonGraphic `0.25` 缩放生成热区。

六种牌面的布局一致：

- 最左侧是当前牌面的牌堆/重发点。
- 其右侧依次是三张可选牌。
- 每个点沿用 prefab 的 `350 x 350` 尺寸，网页换算为 `87.5 x 87.5`。

### 时间窗口

互动窗口来自逐帧采样 Spine 骨骼何时进入游戏 viewport：

- 发牌动画长约 `8.667` 秒，牌堆和三张牌仅在约 `2.7s ~ 7.0s` 位于画面中；网页只在这段时间开放4个牌局热区。
- 点击普通牌后：
  - 结果32约在动画 `1.05s ~ 2.03s` 开放。
  - 结果33约在动画 `1.00s ~ 2.17s` 开放。
- 触发结果32/33后播放约20秒长演出：
  - 结果32的结束点34约在 `15.72s ~ 18.93s` 开放。
  - 结果33的结束点34约在 `15.02s ~ 18.43s` 开放。
- 错过窗口时热区会关闭，动画自然完成并恢复 `idle6`；页面不保留已经离开画面的透明点击区。

### 页面行为

1. 阶段6点击牌堆 `6_7`，从六种真实牌面中随机发牌。
2. 牌面进入画面后，可点击最左牌堆收回本轮，或选择三张牌之一。
3. 普通结果会在动画中短暂开放全画面结果热区；在窗口内点击后进入 `mix6_32_1` 或 `mix6_33_1`。
4. 长演出后段开放结束热区，点击播放 `mix6_34_1` 并回到 `idle6`。
5. `6_29`、`6_30`、`6_31` 直接播放各自特殊反应，结束后回到 `idle6`。
6. 牌局进行时暂时隐藏身体互动和视角热区，避免操作串线；回到待机后全部恢复。

验证：

- 页面内联脚本通过 Node 语法检查。
- `git diff --check` 通过。
- 自动读取 Spine Timeline 验证页面配置：6种发牌分支、18个选牌结果、结果32/33到结束点34全部一致。
- 当前 Codex 环境仍不能监听本地端口，本轮未做实际画面点击验证。用户本地刷新后应重点确认：发牌后约3秒热区出现、点普通牌后约1秒可点全画面、长演出约15秒后可结束。

## 2026-06-19 心契18 牌局第二击状态修正

参考证据：

- PTT《莎拉 尊爵不凡造型 特殊互动 GIF》明确记录真实操作顺序：
  “抽牌” → “选跟莎拉相同的花色” → “这时候再点一次画面” → 特殊动画；
  选错花色同样要在莎拉生气后“再点一次”才进入另一分支。
- 巴哈姆特互动整理也将普通牌分为“让莎拉赢 / 让莎拉输”，并注明最后再次点击画面才有特殊动画；梅花仍是三种独立电击反应。
- 复查网页代码发现，全局 Spine `complete` 监听器会在选牌动画结束时调用 `playIdle()`；
  而 `playIdle()` 会重置 `cardGameState`。因此此前第二击只在动画中段约 1 秒的计时窗口有效，
  动画一结束就失效，和游戏“看完结果后再点画面”的操作不一致。

修正：

- 牌局动画增加独立完成策略，进行中的牌局不再被通用动画完成监听器提前重置。
- 普通牌在约 1 秒后开放整幅画面点击，并持续等待用户第二击；不再于约 2 秒时强制关闭。
- 第二击提示改为“再点一次画面”，点击后才播放 `mix6_32_1` / `mix6_33_1` 长演出。
- 六副手牌中每副都恰好有一张 `6_14` 到 `6_19`，这些牌全部进入结果32，对应攻略的“与莎拉同花色”；
  `6_20` 到 `6_28` 对应不同花色结果33；`6_29` 到 `6_31` 对应三种特殊梅花。
  调试热区据此显示“同花色 / 其他花色 / 梅花”，不再只显示无含义的“牌1/牌2/牌3”。
- 牌堆收回、三种梅花反应和 `mix6_34_1` 结束动作仍在各自动画完成后恢复 `idle6`。
- 发牌后若错过选牌时间窗，仍按原逻辑在发牌动画完成后恢复待机。

本地浏览器验证：

- 选择 `point6_14`（同花色）后等待选牌动画完整结束 3.5 秒，整幅画面的第二击入口仍然存在。
- 第二击正确进入 `mix6_32_1`，约 15 秒后开放 `point6_34` 结束入口。
- 选择 `point6_25`（不同花色）后等待 3.5 秒，仍持续显示“不同花色 · 再点一次画面”，并指向结果33。
- 页面控制台没有项目脚本 error/warning；仅见 Chrome 扩展自身的连接提示，与页面逻辑无关。

## 2026-06-19 心契18 热区坐标投影修正

问题证据：

- `illust_dating18` 的 Unity `SkeletonGraphic` 使用 `0.25` 导入尺度；页面中的 prefab 热区坐标也已经是乘过
  `0.25` 的 Unity 空间值，但 Spine Web 加载二进制时仍暴露原始 skeleton 世界坐标。
- 逐点读取 `idle6` 骨骼真值确认所有普通点严格相差四倍。例如：
  - `point6_5_touch` Spine 世界坐标约 `(-764.8, -2076.0)`；
    页面热区中心约为其 `0.25` 倍。
  - `point6_7_touch` Spine 世界坐标约 `(-870.8, 530.5)`；
    页面牌堆中心同样约为其 `0.25` 倍。
- 原实现直接按整个浏览器窗口百分比换算热区，没有使用 SpinePlayer 的相机 zoom 和居中扩展区域。
  当浏览器不是16:9时，Spine 内容与窗口坐标会再次产生系统性偏移。

修正：

- 为 `illust_dating18` 增加 `HOTZONE_WORLD_SCALES = 4`，在投影前将 Unity 0.25 空间恢复为 Spine 原始世界坐标。
- `hotzoneToScreenBox()` 改为读取当前 `player.viewport`、canvas 实际像素尺寸、device pixel ratio 和 SpinePlayer
  同款相机 zoom 公式，将世界矩形投影到画布 CSS 坐标。
- 普通身体点、长按大矩形、gyro 区和扑克牌共用同一套投影，不再分别依赖窗口百分比。
- “再次点击画面”和结束入口使用 canvas 的实际矩形，不覆盖画布之外的黑边。
- 窗口缩放和全屏切换后重新计算热区投影。

本地超宽窗口验证：

- 阶段6胸、腹、腿和脚部热区从原先聚集在角色腰/膝附近，移动到对应身体区域。
- 牌堆从错误的画面中央附近移动到角色手中牌堆位置。
- 发牌分支 `point6_8 / 6_14 / 6_20 / 6_21` 四个热区按真实 Spine 骨骼间距排列，
  不再受到右侧黑边导致的横向偏移。

## 2026-06-19 默认沉浸互动与热区显示开关

- 心契页面默认隐藏热区边框、底色和文字标签，但热区按钮仍保留 `pointer-events`，进入页面即可直接互动。
- 左侧菜单顶部新增“显示热区 / 隐藏热区”开关，只控制调试标记的可见性，不重建播放器、不改变阶段、
  道具、长按、拖动、扑克牌或其它互动状态。
- 每次重新进入页面默认恢复沉浸模式（隐藏热区），避免调试显示状态误留到正常体验。

## 2026-06-20 首次进入即可互动

- 修复首次加载角色后必须手动点击一次“待机”按钮，隐藏热区才会开始响应的问题。
- 根因是 `renderStageControls()` 先投影热区、后调用 `player.setAnimation()`；即使交换调用顺序，SpinePlayer
  仍要到下一次绘制帧才完成 canvas 尺寸和相机 zoom。过早投影会生成落在左上角的 26px 最小按钮。
- 现在 `playIdle()` 设置待机动画后标记热区待投影，由 SpinePlayer 自身的 `frame` 回调在有效 viewport 和
  canvas 尺寸出现后生成当前阶段热区。首次进入角色、切换阶段、后台标签页和自动恢复待机都不再依赖
  猜测延迟时间，也不需要额外操作菜单。

## 2026-06-22 心契音频资源分析与通用接入方案（后续已实现）

本节记录 dating18 的已确认结论，以及后续所有心契角色可复用的音频提取和播放方案。
实现结果见后面的 2026-06-23 语音与 SFX 接入记录。

### 身份与版本真值

- `dating18` 是【尊爵不凡】致胜王牌莎赫拉查德（莎拉），资源编号 `char000396`。
- **不是**温泉修行者，也不是 `char067004`。
- dating18 prefab 内有两个指向 `Char067004` 的 Gauge 音频字段，但 `_GaugeSettingData.IsOn = 0`，
  属于复制 prefab 后遗留的禁用配置，不能用来判断角色身份或动作音频归属。
- 本地旧备份 `/Users/woods/bd2_gamedata_backup` 的 Addressables 版本是 `20260602132141`。
- 手机当前 `file.json` 版本是 `20260616170924`，SoundData catalog 版本是 `20260616081003`，
  属于 2026-06-18 游戏更新后的资源。
- `interaction_char000396` 和旧名 `visual_interaction_sfx` 的 UnityCache bundle 新旧字节一致，
  但 SoundMaster 已更新，事件路径和真实 SFX bank 归属已经变化。

以后查音频时，资源优先级固定为：

1. 手机当前 `/files/SoundData/Patched/`
2. 手机当前 SoundMaster / catalog
3. 手机当前 UnityCache
4. `/Users/woods/bd2_gamedata_backup`

必须比较文件 SHA256、BNKI bank GUID 和事件 GUID，不能只看 readableName 或旧 catalog hash。

### 莎拉心契语音 bank

资源为 `common-interactionvoice.../interaction_char000396.bytes`。解出的 FMOD bank 有 98 个事件、
100 个 sample：

- 49 个韩语事件有内容。
- 同名的 49 个日语事件在这份 bank 中为空。
- 25 组情绪语音，每组通常有 4 个变体：
  `Annoy1/2`、`Embarrass1/2`、`Endure1/2`、`Neutral1/2`、`Pain1/2`、
  `Shy1/2/3/4`、`Sigh1/2/3`、`Smile1/2/3`、`Surprise1/2/3/4/5`。
- 另外有 24 个动作 selector 事件，负责按原游戏权重从一个或多个情绪池中选语音。

FMOD 关系已经还原为：

```text
EVNT → TMLN → MUIT / WAIT → WAV
```

不能在网页里自行猜“身体部位对应哪种情绪”；必须从动作 selector 自动导出精确 sample、重复项和权重。

| 动作 | 语音池 |
|---|---|
| `mix1_10_1` | Surprise1 |
| `mix1_2_long` | Annoy1 + Surprise2 |
| `mix1_4_1` | Annoy1 + Surprise2 |
| `mix1_8_long` | Shy3 |
| `mix1_9_1` | Annoy1 + Surprise2 |
| `mix2_2_long` | Shy3 + Surprise2 |
| `mix2_6_long` | Shy3 + Surprise2 |
| `mix2_9_1` | Sigh2 |
| `mix6_14_1` | Smile3 + Surprise1（7 个加权候选） |
| `mix6_20_1` | Annoy1 + Embarrass1（6 个候选） |
| `mix6_29_1` | Embarrass1 + Endure2 |
| `mix6_2_long` | Embarrass1 + Shy4 |
| `mix6_30_1` | Embarrass1 + Endure2 + Pain1（11 个候选） |
| `mix6_31_1` | Embarrass1 + Endure2 + Sigh1（12 个候选） |
| `mix6_32_1` | Endure1 + Pain1 + Shy1 + Shy4 + Sigh1 + Surprise3 + Surprise5（27 个候选） |
| `mix6_33_1` | Endure1 + Endure2 + Shy1 + Shy4 + Sigh1 + Surprise4 + Surprise5（28 个候选） |
| `mix6_3_long` | Endure2 + Surprise2 |
| `mix6_4_long` | Annoy1 + Surprise2 |
| `mix6_7_1` | Neutral1 + Smile1 + Surprise1（10 个候选） |
| `mix6_8_1` | Neutral1（只使用 2 个变体） |
| `mix7_1_long` | Shy1 + Surprise4 |
| `mix7_2_long` | Shy1 + Surprise4 |
| `mix7_4_long` | Pain1 + Shy1 |
| `mix7_5_1` | Annoy2（只使用 2 个变体） |

上表只说明池关系，不能代替工具生成的精确权重数据。

### 莎拉心契动作 SFX bank

2026-06-18 更新后的真实文件位于手机：

```text
/sdcard/Android/data/com.neowizgames.game.browndust2/files/SoundData/Patched/Sound/
342271E9887477BD308B35108B7346D60DDED17E
```

- 大小：59,921,920 bytes
- SHA256：`0f6cd82848391943e1bcc974c538396f63ec4e7e01df2983d6d20b432e93b7f1`
- BNKI GUID：`bcbf2950f645bb4bbd33ad593e44c248`
- 路径：`bank:/BundleCommon/Sound/Visual_Novel_SFX`
- 716 个事件，429 个 sample

旧备份中的 `bank:/BundleCommon/Sound/Visual_Interaction_SFX` 只含 12 个早期角色，没有
`Char000396`。两个名称相近但不是同一份内容，这是最重要的版本陷阱之一。

更新后的 Master.strings 中已找到 `Char000396` 的 98 条心契语音路径和 112 条
Cinematic / Visual_Novel 心契 SFX 路径。112 个 SFX 事件共引用 127 个不同 sample，其中
10 个是莎拉专属：

```text
Char000396_Card_01
Char000396_Card_02
Char000396_Card_03
Char000396_Metal_Rattle_01
Char000396_Shoes_Drop_01
Char000396_Shoes_Drop_02
Char000396_Shoes_Drop_03
Char000396_mix6_32_1
Char000396_mix6_33_1
Char000396_motion1_14
```

其余事件会复用公共衣料、碰撞、液体、挥动等音效。

SFX 事件可能包含时间轴延迟、随机权重、多段串联和循环，不能把事件引用的所有 sample 同时播放。
正确方案二选一：

1. 解析 FMOD event 的 timing/random/loop，在浏览器按 schedule 播放。
2. 离线按原事件结构渲染为 OGG；循环事件另外保存 start/loop/stop 语义。

`Char000396_mix6_32_1`、`Char000396_mix6_33_1` 这类预混长轨可优先直接使用。

### 格式与转换结论

- FSB5 codec `0x10`（16）是 **FMOD FADPCM**，不是 FMOD Opus；Opus 是 `0x11`（17）。
- 游戏 FMOD runtime 版本是 **2.03.12**。
- GitHub 上现成的 vgmstream macOS release 是 arm64，本机是 Intel x86_64，不能直接运行。
- 已验证官方开源 vgmstream 稳定 tag `r2117` 可在本机编译，FADPCM 无需额外 codec 依赖。
- 网页资源建议转成 48 kHz OGG Vorbis，并保持原 mono/stereo。
- 实测 `Char000396_Int_Shy4_1` 为 1.152 秒 mono，OGG 约 13.9 KB；
  `Char000396_mix6_32_1` 为 12.981 秒 stereo，OGG 约 202 KB。

### 后续角色统一提取流水线

1. 从正式 dating/角色数据确认 `datingId → char/costumeId`，忽略 prefab 中禁用的残留引用。
2. 拉当前 `file.json`、SoundData catalog、SoundMaster 和相关 patched bank，记录版本、SHA256、BNKI GUID。
3. 用游戏自带 `libfmodstudio.so` 和 Master.strings 导出 GUID → event path。
   当前已验证 Android `app_process` + 游戏 APK classpath + JavaVM/NativeActivity 环境可行，后续应封装成脚本。
4. 用事件 GUID 反查真正包含它的 bank；catalog 名称含糊时，以 bank 内 GUID 为最终证据。
5. 解析 FEV 图：
   - 语音生成 selector → sample 池、重复项和权重。
   - SFX 生成 timeline、随机分支、loop 和 WAV 引用。
6. 定位 FSB5，按 name table/stream index 用 vgmstream 解码，再用 FFmpeg 转 OGG。
7. 自动生成项目数据和资源，不在 `index.html` 里维护巨型手写映射。
8. 核对路径、bank GUID、sample index/name、时长，再与 Spine 动画逐动作验证。

建议结构：

```text
audio/dating/<datingId>/voice/*.ogg
audio/dating/<datingId>/sfx/*.ogg
data/dating_audio.json
```

`dating_audio.json` 至少保存 charId、源版本、bank GUID/SHA256、动作原名、规范化名称、语音权重池、
SFX 时间表和循环停止条件。动作名存在大小写与补零差异（如 `mix1_01_1` / `mix1_1_1` / `Idle1`），
必须受控规范化并保留原名，不能靠宽松正则猜测。

### 前端播放逻辑

统一入口建议为：

```js
playDatingActionAudio(datingId, stage, animationName, phase)
```

- 第一次用户点击/触摸时创建或恢复 `AudioContext`，满足浏览器自动播放限制。
- Spine 动画真正开始时读取对应 FMOD event。一个 event 可以有多个时间触发点；每个触发点再按自己的
  selector 权重选一个 sample。不能把长动作误做成“动作开头只随机播放一句”。
- SFX 按时间表播放；预混长轨直接播放；循环音登记停止条件。
- 动作结束、切动作、切角色或退出心契时，停止/短淡出旧音频，清除循环和待触发任务。
- 使用 generation/token，防止上一个动作的异步音频串进新动作。
- 语音与 SFX 分开控制音量，只预载当前角色资源。
- 音频缺失必须静默降级，不能影响 Spine 互动。

### 实施顺序

1. 莎拉全部 100 个语音 sample + 24 个动作 selector 精确权重。
2. 10 个 `Char000396_*` 专属 SFX，优先预混长轨和强绑定动作。
3. 公共 SFX 的 timeline/random/loop。
4. 把身份识别、Master.strings、bank 定位、FEV、FSB 和 JSON 生成整合成通用工具，再批量扩展角色。

### 托管决定

用户于 2026-06-23 明确决定允许网页转码音频进入公开 GitHub 仓库。当前只提交页面实际引用的
OGG，不提交原始 Unity bundle、FEV bank 或 FSB；dating18 的 227 个 OGG 合计约 4.9 MB，
由 GitHub Pages 与网页同源发布。`audio/dating/` 已从 `.gitignore` 移除。

### 语言策略（2026-06-23 最终决定）

- 心契音频统一使用**韩语（KR）**。
- 不开发语言切换菜单，也不同时维护 KR/JP 多套资源。
- 原因是 common interaction bank 中 KR 事件、Timeline、selector 和 100 个 waveform 完整闭合；
  当前客户端的 JP 事件只是空壳，独立 JP bank 中也没有莎拉心契 waveform。
- 这里的“没有 JP”只限定于手机当前资源版本 `20260616170924`，不代表官方未来不会补发，
  也不代表其他心契角色一定没有日配。
- `data/dating_audio.json` 每个角色只保存一套 KR 数据。
- 后续扩展其他角色优先使用同样完整、可验证的 KR interaction bank，不再为多语言增加复杂度。
- `tools/audit_dating_jp_audio.py` 保留，未来游戏更新后仍可复查日配是否新增，但不会影响当前 KR 主线。

## 2026-06-23 dating18 莎拉语音第一阶段接入

> 语言说明：本节 KR 数据既是解析验证样本，也是当前项目正式采用的唯一语音语言。

### 新增通用生成工具

新增 `tools/extract_dating_audio.py`，输入：

- interaction voice Unity bundle
- 其内嵌的 FSB5
- 当前 Master.strings 导出的 `GUID<TAB>event path`

自动完成：

1. Unity TextAsset 提取 RIFF FEV bank。
2. 解析 `EVNT → TMLN → MUIT/WAIT → WAV`。
3. 保留每个 Timeline instrument 的起始 tick、持续 tick、随机候选和权重。
4. 用 vgmstream 读取 FSB stream name、采样率、声道、时长。
5. 用 vgmstream + FFmpeg 转为 48 kHz OGG Vorbis。
6. 合并生成 `data/dating_audio.json`。

这套工具没有写死莎拉的情绪表，可复用于后续角色。

### 修正此前对 selector 的简化理解

动作语音 event 不是都在动作开头随机选一句。长动作的 TMLN 会排列多个 MUIT，每个 MUIT 都有自己的
时间和随机池。

例如 `mix6_32_1` 有 7 个语音触发点：

| 时间（秒） | 随机池 |
|---:|---|
| 0.999833 | Sigh1 |
| 2.000021 | Surprise5 |
| 4.500479 | Endure1 |
| 6.700437 | Pain1（只取 1/2/4） |
| 7.999875 | Shy4 |
| 10.500187 | Surprise3 |
| 14.499896 | Shy1 |

工具现在会逐触发点保存 `at`、`window` 和精确 choices/weight，前端按原时间轴调度。

### 生成结果

- `data/dating_audio.json`
  - 49 个有内容的 KR 事件
  - 81 个时间触发点
  - 24 个动作事件映射
  - 100 个 sample 元数据
- 本地 `audio/dating/illust_dating18/voice/`
  - 100 个 OGG
  - 总计约 1.5 MB
  - 随站点进入公开仓库
  - 当前为正式采用的 KR 资源

数据记录了当前资源的校验值：

```text
sourceVersion  20260616170924
voice bank GUID da8d214b81a44e4aac792556ee6b57ff
bundle SHA256  a5b7c3b8eddd13b6f1c82b8e26c1224dffb2c76852b202f3cb662cdffabeb596
bank SHA256    5af9818050d2c6cc544ac5e1eb765946ab03637a2891c75db159d7af2f5c6efa
FSB SHA256     8c97172af4faa7625375bb80b1aba331b62ea372ee4b89b64894fb5993c6dd00
```

ADB 复核手机当前 `file.json` 仍是 `20260616170924`；更新后的 Visual_Novel_SFX 文件仍为
59,921,920 bytes，SHA256 仍是
`0f6cd82848391943e1bcc974c538396f63ec4e7e01df2983d6d20b432e93b7f1`。

### 前端实现

`dating.html` 新增通用 `DatingAudioController`：

- 切换到有音频数据的角色时先探测一条资源；404 时静默禁用，避免 Pages 连续请求 100 个不存在文件。
- 探测成功后并发预解码当前角色的全部语音；莎拉总量约 1.5 MB。
- 监听 Spine AnimationState 的 `start`，队列动画到真正起播时才调度对应 event。
- 每个 FMOD trigger 按原权重随机选择 sample，并按 `at/window` 在 Web Audio 时间轴播放。
- 快速切动作、恢复待机、切阶段或切角色时，generation 变化并停止全部旧 source。
- `AudioContext.resume()` 不阻塞调度：后台浏览器可能一直 suspended，但声音仍先排入时间轴；
  下一次有效用户手势恢复 context 后即可播放。
- `?audioDebug=1` 时才在 `<html>` data 属性和 console 输出当前动画/sample，普通访问无调试状态。
- 新增 `?dating=18` 直达参数，方便逐角色测试。
- dating18 列表身份修正为“莎拉 / 尊爵不凡·致胜王牌”。

### 本地验证

- 100 个 OGG 全部存在，均可由 ffprobe 识别为 Vorbis；抽查为 48 kHz mono。
- 本地浏览器实际请求 100 个文件全部返回 200。
- 点击 `mix1_4_1`：
  - Spine start 事件正确识别动画名。
  - 一次排入两个语音 source，对应 t=0 和 t=1.696375 的两个 FMOD trigger。
- 随即切到没有语音 event 的 `mix1_3_1`：
  - 已排入的旧 source 立即从 2 变为 0。
- 页面内联 JavaScript 语法检查、Python 编译检查和 `git diff --check` 均通过。

### 日语资源定位现状

- `interaction_char000396` 同时登记了 49 个 JP event path，但对应 Timeline 均为空，不含日语 waveform。
- 手机已下载独立的日语资源：
  - `SoundData/Patched/LocalVoice_JP/`
  - `SoundData/Patched/LocalVisualNovel_JP/`
- 已拉取并检查当前 `LocalVisualNovel_JP` 下 4 个 bank；其中均未包含莎拉心契的 JP event GUID，
  因此莎拉日语语音更可能位于数量较多的 `LocalVoice_JP` bank 中。
- 下一步只围绕 JP 做定位：
  1. 扫描 `LocalVoice_JP` bank 的 event/WAV/sample。
  2. 找到与 `Char000396_Int_*_JP` 对应的 waveform。
  3. 复用已解析的动作 Timeline/selector 结构，替换为 JP sample。
  4. 重新生成 OGG 和 `data/dating_audio.json`。
  5. 若未来正式补发完整 JP，再与 KR 逐事件比较后决定是否调整；当前不切换。

## 2026-06-23 dating18 日语语音全量审计结论

### 结论

当前手机资源版本 `20260616170924` **没有发布莎拉 `char000396` 的心契专用日语语音**。

这不是路径尚未找到，而是经过当前已下载的 JP bank、事件 GUID、FSB stream name 和 Addressables
catalog 四层交叉验证后的结论。

### 审计范围与证据

- 从手机拉取 `SoundData/Patched/LocalVoice_JP/`：
  - 86 个 bank
  - 合计约 232 MB
- 加上手机当前 `LocalVisualNovel_JP` 的 4 个 bank，共扫描 90 个日语 bank。
- 对照 Master.strings 中 `Char000396/Interaction/*_JP` 的 49 个目标 event GUID：
  - bank 命中数：0
- 扫描全部 FSB stream name：
  - 心契特征 sample（`Int_` / `Interaction` / `Shy1` 等）：0
- 当前 Addressables catalog 的 `localvisualnovel_jp` 条目：
  - 13 条
  - `local_char000396_jp`：0 条
- `LocalVoice_JP/8B418A01190FC504AF0C1CA1647BB81721DA0EA8` 确实包含莎拉日语：
  - bank 共 165 个 stream
  - 其中莎拉 26 个
  - 内容仅为 `Admire`、`BattleReady`、`Damage`、`Smile`、`Worry` 等普通战斗/档案语音
  - 没有心契互动语音

`interaction_char000396` common bank 中虽然登记了 49 个 JP event path，但它们的 Timeline 全为空；
同 bank 的 49 个 KR event 才引用 100 个心契 sample。JP event 是预留空壳，不代表日配已经随资源发布。

### 项目处理

- 不用 26 条普通角色日语语音冒充心契语音。
- 项目恢复并统一使用完整的 KR 心契语音。
- `data/dating_audio.json` 使用 `defaultLanguage: "KR"`，莎拉保留 49 个事件、81 个触发点和
  100 个 sample。
- JP 审计证据保存在 `jpAudit.illust_dating18`，只用于说明当前版本未采用 JP 的原因。
- 若未来更新发布完整 JP，可用审计工具发现；当前不因此增加语言切换功能。

### 新增更新审计工具

新增 `tools/audit_dating_jp_audio.py`，用于游戏更新后重新检查：

1. JP interaction event GUID 是否出现在任一 bank。
2. FSB 是否出现目标角色 sample。
3. 是否出现心契特征 sample。
4. catalog 是否新增 `local_charXXXXXX_jp`。

本次报告结果：

```text
target JP events       49
JP banks scanned       90
event GUID hits         0
interaction sample hits 0
catalog char000396 hits 0
available              false
```

以后不用再次手工翻 bank；更新资源后重跑审计工具即可。

## 2026-06-23 dating18 莎拉角色专属 SFX 接入

### SFX Timeline 解析补全

`Visual_Novel_SFX` 使用的 TLNB 比 interaction voice bank 多一个 2 字节类型字段：

```text
voice: GUID + count:u16 + width:u16 + records
SFX:   GUID + type:u16 + count:u16 + width:u16 + records
```

空 Timeline 的 width 也可能是 9，而不是 voice bank 中常见的 1。`tools/extract_dating_audio.py`
现已同时兼容两种 FMOD 2.03.x 布局；更新后的 SFX bank 可完整解析：

- 716 个事件
- 716 个 Timeline
- 2,384 个 multi instrument
- 10,350 个 wave instrument
- 429 个 WAV/sample

### 新增 SFX 生成工具（先以专属 sample 验证）

新增 `tools/extract_dating_sfx.py`：

- 输入 Visual_Novel_SFX bank、FSB、Master.strings event path。
- 第一轮只提取 `CharXXXXXX_*` 角色专属 sample；第三阶段已扩展为全部直接 Timeline sample。
- 保存 FMOD 的真实触发时间、窗口、随机候选和权重。
- 自动把 FMOD 补零名规范化为 Spine 名：
  - `mix6_07_1 → mix6_7_1`
  - `mix2_08_1 → mix2_8_1`
- 支持显式 alias；莎拉六种随机发牌动画 `mix6_7_1`～`mix6_7_6`
  共用同一个 FMOD 发牌事件。
- 转码为 48 kHz OGG，合并进 `data/dating_audio.json` 的 `character.sfx`。

### 已接入的 10 个莎拉专属 sample

```text
Char000396_Card_01
Char000396_Card_02
Char000396_Card_03
Char000396_Metal_Rattle_01
Char000396_Shoes_Drop_01
Char000396_Shoes_Drop_02
Char000396_Shoes_Drop_03
Char000396_mix6_32_1
Char000396_mix6_33_1
Char000396_motion1_14
```

生成结果：

- 10 个 sample
- 21 个 SFX event
- 29 个真实时间触发点
- 26 个 Spine 动画映射（含 5 个发牌 alias）
- OGG 合计约 564 KB

关键时序示例：

| 动作 | 专属 SFX |
|---|---|
| `mix1_10_1` / `mix6_6_1` | t=4.29s 从 3 个 Shoes_Drop 中随机选 1 个 |
| `motion1_14` | t=0.15s 播转场轨 |
| `motion2_10` | t=0.16625s 播转场轨 |
| `motion6_42` | t=0.12s 播转场轨 |
| `motion7_13` | t=0.1s 播转场轨 |
| `mix6_7_1`～`mix6_7_6` | t=0.132/1.065/1.598/7.362s 播 4 段牌声 |
| `mix6_32_1` | t=0 播 12.981333s 预混长轨 |
| `mix6_33_1` | t=0 播 15.754667s 预混长轨 |

### 前端

`DatingAudioController` 现在同时管理两条总线：

- voice gain：0.9
- SFX gain：0.82

语音与 SFX：

- 共用 Spine `start` 时刻和 Web Audio 时间基准。
- 各自从 voice/sfx event 选择 sample。
- 共用 generation 和 source 集合，因此切动作、回待机、切阶段或切角色时一起停止。
- 第一轮验证时预解码 100 条语音 + 10 条专属 SFX，总体积约 2 MB；
  完整阶段为 100 条语音 + 127 条 SFX，总体积约 4.9 MB。
- 音频缺失仍静默降级，不影响互动。

新增 `?stage=6` 直达阶段参数，可与 `?dating=18`、`?audioDebug=1` 组合做逐阶段验收。

### 本地验证

- 10 个 OGG 全部可被 ffprobe 识别；长轨时长分别为 12.981333s / 15.754667s。
- 浏览器实际请求 100 条 voice + 10 条 SFX，全部返回 200/304。
- 随机发牌得到 `mix6_7_3` 时：
  - 正确映射到 SFX event `mix6_7_1`
  - 调度 Card_01 / Card_02 / Card_03 / Card_01 四个时间点
  - 调试状态为 `channel=sfx`
- 发牌中途切换动作，待播/正在播放的 source 从 4 立即归零。
- JavaScript 语法、Python AST、JSON 数据断言和 `git diff --check` 全部通过。

### 第三阶段：完整公共 SFX（2026-06-23）

对 112 个莎拉 SFX event 的 Timeline 做了逐 instrument 审计：

- 670 个 Timeline 触发记录，670 个 instrument GUID 均可解释。
- 525 个为 multi instrument（MUIT），145 个为直接 wave instrument（WAIT）。
- 直接引用 127 个不同 sample；没有未知 instrument，也没有把递归后代声音粗暴地同时播放。
- vgmstream 检查 429 个 FSB stream 后确认没有内嵌无限循环点。名称带 `_loop` 的事件仍由有限
  sample 组成，切动作时沿用 generation/source 取消机制即可正确停止。

`tools/extract_dating_sfx.py` 已改为生成完整直接时间轴：

- 112 个 SFX event
- 670 个真实时间触发点
- 127 个 sample
- 117 个 Spine 动画映射（含 5 个发牌 alias）
- SFX OGG 约 3.4 MB

加上 100 条 KR voice，dating18 共 227 个 OGG、约 4.9 MB。所有 manifest 文件均存在，
音频只包含页面需要的 OGG 转码；原始 59.9 MB bank 和 56 MB FSB 不进入仓库。

最终验证：

- 本地浏览器实际请求 100 条 voice + 127 条 SFX，音频资源全部返回 200。
- 227 个文件全部通过 ffprobe，codec 均为 OGG Vorbis。
- JSON 断言确认 112 events / 670 triggers / 127 samples / 117 actions。
- 页面 JavaScript、三个 Python 工具和 `git diff --check` 全部通过。

## 2026-06-23 心契 Spine CDN 故障切换修复

线上曾出现主 jsDelivr 对 dating18 的 skel 和 11 张贴图集中返回 502。原备用链还有两个问题：

- `cdn.statically.io` 会重定向到 HTTP，被 GitHub Pages 的 HTTPS 页面按 Mixed Content 拦截。
- SpinePlayer 在素材只加载一部分时直接 `dispose()`，内部会对 null 资源调用 `dispose`，
  使备用 CDN 重试被二次异常打断。

`dating.html` 现已：

- 移除 statically，统一为 HTTPS；镜像顺序为 fastly、BunnyCDN、Gcore、Cloudflare testing、
  jsDelivr 主域和 raw.githubusercontent。
- 创建 SpinePlayer 前先读取 atlas，并用 HEAD 并行检查 skeleton 与 atlas 列出的全部贴图页。
  只有整套资源可用才创建播放器，避免半初始化实例。
- 预检遇到 403/404/502、超时或 CORS 错误时自动切换下一个镜像。
- 增加安全销毁、加载 generation 和单一 retry timer，旧角色/旧镜像的异步回调不能干扰新加载。

故障注入验证使用“首源固定 404、次源本地 upstream”：

- 自动切换后 dating18 成功进入阶段 6。
- 页面出现一个有效 canvas，阶段与互动控制正常生成。
- 控制台无 SpinePlayer 加载异常，也没有 null dispose 异常。

## 2026-06-24 Nebris / illust_dating1 prefab 交互补全

以第一个心契资源 `illust_dating1` 作为“普通三阶段心契”的样本，回到 Unity prefab
而不是靠 Spine 动画名猜测交互。

### 资源身份

- 页面资源：`illust_dating1`
- 角色：Nebris
- 对应服装：`char003303`（新进员工）
- 不对应隐藏资源 `char003392`

### prefab 结论

`common-char-datingillust_assets_all` 里的 `Illust_dating1` 是很干净的三阶段结构：

- 共 68 条 prefab 互动记录，去重后 64 个动作 key。
- 全部是手部工具 `toolId=0`，没有道具切换。
- 动作类型只有 touch / drag。
- 没有长按、计量条、陀螺仪、麦克风、随机牌局等特殊机制。
- 阶段推进只有两个点：
  - `1_18_0`：`mix1_18_1`、`mix1_18_2`、`motion1_18`，完成后进入阶段 2。
  - `2_22_0`：`mix2_22_1`、`mix2_22_2`、`motion2_22`，完成后进入阶段 3。
- 阶段 3 的 `3_6_0`、`3_7_0` 在 prefab 中属于隐藏点；当前页面不显示，避免把未确认触发条件的隐藏互动暴露出来。

### 前端实现

`dating.html` 的 `PREFAB_POINT_ACTIONS.illust_dating1` 已补齐 64 个 prefab key。

对这种已经有 prefab 阶段推进动作的资源，左侧菜单不再额外生成通用“推进到阶段 X”按钮，
避免出现一个真实 prefab 推进点和一个猜测推进按钮并存。隐藏 prefab 动作会在
`currentPrefabActions()` 里过滤掉。

### 本地验证

本地预览 `dating.html?dating=1`：

- 阶段 1 显示 `拖拽1`、`拖拽2`、`触摸3` 到 `触摸17`、`拖拽18 -> 阶段2`。
- 普通动作 `触摸10` 可播放，控制台无错误。
- 点击画面热区 `1_18_0 · InteractionZone` 后进入阶段 2，并刷新出阶段 2 的完整动作表。
- 阶段 2 显示 `拖拽1`、`触摸2` 到 `触摸21`、`拖拽22 -> 阶段3`。
- 点击画面热区 `2_22_0 · InteractionZone` 后进入阶段 3。
- 阶段 3 只显示 22 个可见动作；隐藏点 `3_6_0`、`3_7_0` 没有出现在左侧菜单。

### Nebris SFX 接入（2026-06-24）

Nebris 的动作 SFX 可以可靠接入，因为 `Visual_Interaction_SFX` 的 event path
直接使用 Spine 动画名：

```text
event:/Cinematic/Visual_Novel/Char003303/Interaction/idle1/mix1_17_2
event:/Cinematic/Visual_Novel/Char003303/Interaction/idle1/motion1_18
event:/Cinematic/Visual_Novel/Char003303/Interaction/idle2/motion2_22
...
```

生成流程：

- 从 `visual-eventdump-all.tsv` 过滤 `Char003303/Interaction/`，得到 88 个 SFX event path。
- 使用 `Visual_Interaction_SFX` 作为事件时间线 bank。
- 使用 `Visual_Novel_SFX` 内嵌 FSB5 作为 sample bank。
- `tools/extract_dating_sfx.py` 现在支持非莎拉角色，不再硬编码莎拉的
  `112 events / 670 triggers / 127 samples` 断言；如需验收断言，可传
  `--expect-events`、`--expect-triggers`、`--expect-samples`。
- `tools/extract_dating_audio.py` 对 SFX bank 中短/空 MUIT 容器做保守容错：
  未被 Timeline 引用的占位 MUIT 会跳过；如果实际引用到了，后续仍会以未知 instrument 报错。
- `tools/extract_dating_sfx.py` 现在可以创建 SFX-only 角色节点，适合 Nebris 这种
  SFX 已证实、voice 映射尚未证实的情况。

生成结果：

- `data/dating_audio.json` 新增 `characters.illust_dating1.sfx`
- `audio/dating/illust_dating1/sfx/` 新增 66 个 OGG
- 88 个 SFX event
- 324 个 Timeline 触发点
- 88 个动画映射

注意：SFX sample 名里会出现其他角色编号或公共音效名，例如 `Char004202_*`、
`Char000396_Card_02`、`Cloth_*`、`Mud_*`。这是 FMOD 时间线真实引用的公共 sample，
不是资源串错。

验证：

- 66 个 OGG 全部通过 ffprobe，codec 为 OGG Vorbis。
- `illust_dating18` 的既有 voice/SFX manifest 未被删除。
- SFX-only 节点可被前端 `DatingAudioController` 预载：没有 voice sample 时会以 sfx
  sample 作为探测资源。

### 尚未完成：Nebris voice

已确认旧备份里存在 `interaction_char003303.bytes`，TextAsset 名为
`Interaction_Char003303`，内部是 FEV/FSB5，能看到 `Char003303_Int_Joy*`、
`Char003303_Int_Smile*`、`Char003303_Int_Sigh*`、`Char003303_Int_Pain*`
等 42 个 sample 名称。进一步拆包结果：

- bank GUID：`c2629058281b854c8e3ec2f61ee269b1`
- 30 个 voice event
- 30 个 Timeline
- 15 条非空 Timeline
- 15 个 multi instrument
- 42 个 WAIT/WAV/sample

但 Nebris voice 和莎拉不同：莎拉已经从 SoundMaster 导出了完整 event path，能看到
`event:/Voices/Common/Char000396/Interaction/Char000396_Int_mix6_7_1_KR`
这类“动作名 voice event”；Nebris 目前只解析了 interaction voice bank 本体，能看到
`Joy1`、`Smile1`、`Sigh1`、`Pain1` 这类情绪 sample，但还没有拿到 Nebris voice bank
对应的 SoundMaster event path。prefab 的互动点脚本只包含 Spine 动作/SFX 信息，
没有发现“某个 point 对应某个情绪 voice”的字段。

所以当前不能把 voice 随机硬配到动作上，否则会出现“声音有了但语义不对”。后续要接 voice，
需要继续找游戏运行时的动作→情绪映射来源；找不到证据前只保留已证实的 SFX。

#### 2026-06-24 继续追 Nebris voice 映射：当前结论

为了绕开 `/private/tmp` 和 adb pull 的权限/稳定性问题，本地新增仓库内临时目录
`local_device_cache/`，并写入 `.gitignore`。手机缓存文件可以拉到这里做分析，但该目录不进 git。

已从当前手机缓存拉到：

- `com.unity.addressables/file.json`
- `com.unity.addressables/catalog_alpha.json`
- `SoundData/catalog_sound_hd.json`
- `Data/`
- `Neo/`

当前 `file.json` 显示版本/构建时间为：

- `version = 20260616170924`
- `buildTime = 2026-06-16T17:09:24Z`
- `bundles = 1891`

`file.json` 中确认 `interaction_char003303.bytes` 仍存在，且与旧备份中已分析的
Nebris interaction voice bank 对应：

```text
common-interactionvoice_assets_bundleinteractionvoice/interaction_char003303.bytes
bundleName = a95eeb8e3db465231e037bdca581ebe2
hash       = 77705eb8a0103dcb9b9982ebac3d2162
size       = 829109
```

这说明“音频资源本身缺失”不是问题；问题仍是缺少互动动作到情绪 voice 池的映射。

进一步查 IL2CPP metadata 得到更明确的映射字段位置：游戏代码中存在
`SpineInteractionPointTable`，并且该表有以下字段/访问器：

- `SoundVoiceName`
- `SoundMotionVoiceName`
- `LongPressFailVoiceName`
- `LongPressLoopVoiceName`
- `LongPressSuccessVoiceName`
- `InteractionDatingTextId`

`SpineInteractionTable` 里还存在：

- `HasSoundVoiceJP`
- `HasSoundVoiceKR`
- `SoundVoiceBankName`
- `SoundBGMName`
- `SoundAmbName`

因此 Nebris 的正确 voice 接法应当读 `SpineInteractionPointTable`，而不是从 FEV event
或 Spine 动画名反推。

当前手机 `Data/` 缓存共 78 个文件，全部表现为加密/封装数据：

- 文件大小均按 4096 字节页对齐。
- 所有文件前 16 字节相同：`b3 d5 0c 27 2f 43 ab d8 f9 cf f1 4f 9a 24 6c a9`。
- 从第 32 字节开始每个文件都不同。
- 普通 `sqlite3` 打开会报 `file is not a database`。
- 在 `Data/` 和 `Neo/` 中搜不到明文 `SpineInteractionPointTable`、
  `SoundVoiceName`、`Char003303`、`Joy1`、`Smile2` 等关键词。

metadata 中同时能看到 SQLCipher/SQLite 相关字符串，例如：

- `ConnectDB RawDataManager.Instance.SetSQLite completed`
- `ConnectDB new SQLiteDB => filePath : {0} / isEncrypted : {1}`
- `SQLite fail set key`
- `codec_key_derive: deriving key using AES256`

所以当前判断：`Data/` 很可能是 SQLCipher/加密 SQLite 表缓存，`SpineInteractionPointTable`
在里面，但需要数据库 key 或运行时解密结果才能读取。

已经排除的方向：

- `catalog_alpha.json` / `file.json`：只证明互动资源存在，不包含 point→voice 映射。
- Nebris interaction voice FEV/FSB：只有情绪事件池，没有动作点路径。
- `illust_dating1.skel`：只有 `point/mix/motion` 动画名，没有情绪 voice 名。
- Unity prefab 互动脚本：有 action/motion/hotzone/隐藏点信息，没有 voice 字段。
- Data 文件名：不是 `SpineInteractionPointTable` 等表名的常规 SHA1/MD5。
- IL2CPP 字符串字面量表：没有明文 `key` / `AES` / `sqlite` / `cipher` / `password` / `db`
  等可直接作为 SQLCipher 密钥的字符串。

补充排查：重新用 UnityPy 直接读取 6/02 备份中的
`common-char-datingillust_assets_all` typetree，确认 prefab 体系里确实存在
`VoiceSoundEventName` 字段，但只出现在部分资源的根配置
`_defaultSpineMotionByGroup[*]._GaugeSettingData.MotionNameByScoreList[*]` 中：

| 资源 | `VoiceSoundEventName` 数量 | 备注 |
|---|---:|---|
| `Illust_dating1` | 0 | Nebris，没有 voice 字段 |
| `Illust_dating15` | 2 | gauge 分数配置，值为 `Common/Char067004/Interaction/Char067004_Int_Shout1` |
| `Illust_dating16` | 1 | gauge 分数配置，值为空字符串 |
| `Illust_dating18` | 2 | gauge 分数配置，值为 `Common/Char067004/Interaction/Char067004_Int_Shout1` |

其余 `Illust_dating2` 到 `Illust_dating14`、`Illust_dating17` 均为 0。Nebris 的根配置
只有三段默认待机与空 gauge 设置；相关 `point1_18` / `point2_22` 等互动点 typetree 只有
`PlayMixAnimNames`、`PlayMotionName`、`_playMotionNames`、gauge/longPress/hidden/hotzone 等字段，
没有 `VoiceSoundEventName`、`SoundVoiceName` 或情绪 voice 名。

所以更准确的结论是：prefab 体系不是完全没有 voice 字段，但 Nebris / `Illust_dating1`
没有把 voice 映射写在 prefab 里；它仍应来自 `SpineInteractionPointTable` 或运行时代码/表。

#### 2026-06-24 横向审计：不要把 sample 名误判成工作量

当前 `file.json` 中共有 19 个 `common-interactionvoice.../interaction_charXXXXXX.bytes`
角色 bank。快速横扫这些 bank 的 FSB stream/sample 名发现：几乎所有 sample 都是
`CharXXXXXX_Int_Joy/Smile/Sigh/Pain/...` 这类情绪池命名；莎拉 `char000396` 也是如此。

这说明 sample 名本身不能判断是否可自动接入。莎拉之所以能自动，是因为 SoundMaster
里的 FMOD event path 额外提供了动作名，例如：

```text
event:/Voices/Common/Char000396/Interaction/Char000396_Int_mix6_30_1_KR
event:/Voices/Common/Char000396/Interaction/Char000396_Int_mix1_8_long_JP
```

因此后续新增角色的工作量不应按“每个 sample 都要人工听”估算，而应先批量导出
SoundMaster 的 `event GUID -> event path`：

- 如果某个角色有 `CharXXXXXX_Int_mix..._KR` / `CharXXXXXX_Int_motion..._KR`，
  这类 voice 可以像莎拉一样按动作名自动接入。
- 如果某个角色只有 `CharXXXXXX_Int_Joy..._KR` / `Smile..._KR` 这类情绪 event，
  才需要 `SpineInteractionPointTable` 或运行态表映射。

临时验证工具：

- 已在 `local_device_cache/` 下放置临时 UnityPy 依赖和 patched dump so，不进 git。
- 已把 `/data/local/tmp/bd2sound/` 临时工具目录推到设备，包括
  `libfmod.so`、`libfmodstudio.so`、`dumpfmod.jar`、patched `libdumpfmod.so` 和 `Master.strings`。
- patched so 将原本只过滤 `event:/Cin` 的条件放宽为 `event:/`，目标是一次 dump 出
  `event:/Voices/Common/...` 与 `event:/Cinematic/...` 两类路径。
- 当前卡点不是资源或脚本，而是 adb daemon 在 Codex 沙箱内无法重启；外部终端保持
  `adb start-server` 后即可继续运行。2026-06-24 复查时确认设备本身一直在线：
  `adb devices` 曾返回 `RFCY71DH3RW device`；失败发生在 daemon 不存在时，Codex 沙箱尝试
  启动 adb server 并绑定 smartsocket，被系统拒绝：
  `could not install *smartsocket* listener: Operation not permitted`。因此不要再把这类失败判断为
  “设备不在”，正确处理是让本机终端先启动/保持 adb daemon，然后 Codex 只复用连接。

```bash
CLASSPATH=/data/local/tmp/bd2sound/dumpfmod.jar app_process /data/local/tmp bd2.DumpFmod
```

另发现一个更轻量的旧验证工具：`/private/tmp/bd2-device-soundmaster/dump_fmod_strings`
是 ARM64 独立程序，硬编码过滤 `Char000396` 和
`/data/local/tmp/bd2sound/Master.strings`，不依赖 Java `app_process` / NativeActivity。
已在 `local_device_cache/bd2_current_20260624/dump_fmod_by_char/` 生成 19 个同长度角色号的
patched 版本，并准备了忽略目录内脚本：

```bash
./local_device_cache/bd2_current_20260624/run_dump_interaction_voice_paths.sh
```

用途：本地终端先执行 `adb start-server` 后，批量导出 19 个 interaction voice 角色的
`GUID -> event path` 到
`local_device_cache/bd2_current_20260624/voice_event_paths/CharXXXXXX.tsv`。该目录不进 git，
只作为 Nebris 与后续角色工作量评估的证据缓存。

2026-06-24 实测该轻量工具当前也不可用：用户本机运行已知应有输出的校准样本
`dump_fmod_strings_Char000396`，结果为：

```text
FMOD create failed: 28
EXIT:0
```

FMOD 结果码 28 对应 `FMOD_ERR_INTERNAL`，而且发生在
`FMOD_Studio_System_Create`，还没进入 `Master.strings` 加载或角色过滤。因此这次 19 个
`voice_event_paths/Char*.tsv` 全部 0 行不是“角色没有 voice 路径”，而是 FMOD runtime
初始化环境不满足。该路线不要继续作为证据使用；后续应改走：

- 重新复原当时成功的 `app_process + 游戏 APK classpath + JavaVM/NativeActivity` 上下文；
- 或直接静态解析 `Master.strings` 的 `STDT` 字符串/路径字典；
- 或在游戏进程运行态 hook `FMOD_Studio_Bank_GetStringInfo` / 数据表读取。

后续可行路线：

1. 反出游戏给 SQLite/SQLCipher 设置的 key，然后离线打开 `Data/` 表。
2. 在设备运行态 hook `sqlite3_key` / `sqlite3_key_v2` 或 RawDataManager 读表流程，直接拿 key
   或导出解密后的 `SpineInteractionPointTable`。
3. 如果 adb daemon 在当前沙箱内又无法启动，可让外部终端保持 adb server 运行后再继续；
   否则不要在这里反复重试 adb。

#### 2026-06-24 静态解析 `Master.strings/STDT` 的初步结论

`Master.strings` 的 RIFF/FEV 结构为：

```text
RIFF/FEV
  FMT
  LIST/PROJ
    BNKI
    LIST/IBSS ... LIST/WAVS 等空壳
    STDT  2,137,904 bytes
```

可用字符串都集中在 `STDT`。虽然还没完整还原 `GUID -> path` 的二进制索引，
但直接扫描 null-terminated 字符串已经能看到完整/半压缩的路径字典碎片：

- 通用前缀：`event:/`、`Voices`、`Common`、`Interaction`
- 莎拉：`Interaction/Char000396_Int_`，后面既有情绪名，也有 `mix...` 动作名
- Nebris：`Interaction/Char003303_Int_`，后面只有情绪名

Nebris (`Char003303`) 的 voice 片段为：

```text
Interaction/Char003303_Int_
Excitement1/2
Joy1/2
Negative1
Neutral1/2
Pain1
Positive1
Sigh1
Smile1/2
Surprise1/2/3
JP/KR
```

没有看到 `mix...`、`motion...`、`touch...` 这类可直接和 Spine 动作名对应的 voice event。
因此 Nebris 的问题不是“没有 voice bank”，而是 voice event 是情绪池命名；要接到具体点击/动作，
仍需要 `SpineInteractionPointTable`、运行态表映射，或手工/录屏辅助映射。

横向扫当前 19 个 interaction voice 角色，按 `STDT` 字符串片段粗分：

| 类型 | 角色 |
|---|---|
| 含动作型片段（`mix` / `motion` / `touch` 等） | `Char000396`, `Char000706`, `Char001006`, `Char001197`, `Char003604`, `Char003892`, `Char004102`, `Char061492`, `Char066403`, `Char067004`, `Char067104` |
| 只有情绪型片段 | `Char000296`, `Char001106`, `Char003203`, `Char003303`, `Char003402`, `Char060802`, `Char067603` |
| 当前 `STDT` 未找到 `Interaction/CharXXXXXX_Int_` 区段 | `Char004202` |

注意：这只是路径字典级别的分类，不等于已经生成了可用的 `GUID -> path` TSV。
但它足够判断工作量趋势：后续角色不会都像 Nebris 一样困难；有动作型片段的角色更接近莎拉，
可以优先走自动化。

#### M 系列 Mac 备选方案记录

如果后续换到 Apple Silicon / M 系列 Mac：

- 可以直接使用更多 **macOS arm64** 预编译工具，例如 vgmstream arm64 release；
  Intel Mac 上这些工具需要本地编译或找 x86_64 版本。
- 不能因为 CPU 都是 arm64 就直接运行 Android APK 里的 `dump_fmod_strings` /
  `libfmodstudio.so`：它们是 Android/Bionic ELF，不是 macOS Mach-O。M 系列 Mac 不能原生执行。
- M 系列更适合跑 arm64 Android Emulator 或相关虚拟化环境；如果要复原 FMOD Android 上下文，
  可以尝试在 Android arm64 emulator/真机里跑，而不是在 macOS 里直接跑 Android ELF。
- 对本项目最有价值的 M 系列路线仍是两条：
  1. 用 arm64 工具链更方便地编译/调试 Android 侧小工具或 Frida/hook 方案；
  2. 用 macOS arm64 原生音频/解码工具减少 vgmstream、ffmpeg 等依赖编译成本。

结论：M 系列 Mac 会让工具链更顺，不会自动解决 `FMOD_Studio_System_Create` 需要 Android
运行上下文的问题。

#### 2026-06-24 `067104` 战地医疗兵格兰希特：语音是否存在

`067104` 不是新角色，而是格兰希特 (`0671 / Granhildr`) 的新服装。当前 myssal 上游只同步到了
立绘：

```text
spine/char/char067104
```

因此网页能显示立绘，但没有技能动画；上游还没有：

```text
spine/cutscenes/cutscene_char067104
```

不过当前游戏 `catalog_alpha.json` 已经能看到 `cutscene_char067104` 的 skel/atlas/png 资源名，
说明游戏本体已具备技能动画资源，只是 myssal 公开素材仓库还没跟上。

语音方面，当前手机 `file.json` 明确登记了 interaction voice bank：

```text
common-interactionvoice_assets_bundleinteractionvoice/interaction_char067104.bytes
bundleName = 945a97e12197d928b1ecb0c8c9d84700
hash       = 8cc0e66f4cfed48b14c5e1d5f29dd40e
fileHash   = 3E1C183F72BFB20DA7CDA7D46EC7D865
size       = 1905334
```

同时 `Master.strings/STDT` 中存在：

```text
Interaction/Char067104_Int_
Angry1
Annoy1
Embarrass1/2/3
Endure1/2
Mix2_16_1
Mix2_24_1
Mix2_5_1
Mix2_6_1
Mix2_8_1
Mix2_30_1
motion1_18
Neutral1/2
Shy1/2
Sigh1/2/3
Smile1/2
Surprise1/2/3
Touch1
JP/KR
```

所以结论是：`067104` **不是没有互动语音**。它有 interaction voice bank，也有动作型
event 名（`Mix2...`、`motion1_18`、`Touch1`），比 Nebris 那种纯情绪池更接近莎拉，
理论上可以走较自动化的挂载路线。

当前限制：`/Users/woods/bd2_gamedata_backup/UnityCache/Shared/945a97e.../` 里只有旧的
`7ff5.../__data`，大小 1.4KB，不是当前 `file.json` 里的 1.9MB bank。因此要真正解码
`067104` 的 OGG，需要从当前手机缓存或 CDN 拉到 hash 为 `8cc0e66f...` 的 bundle。

#### 后续“自动挂载游戏语音”的可行方案

目标不是为每个角色手写映射，而是形成一条证据优先的流水线：

1. 从 `file.json` 自动发现 `common-interactionvoice.../interaction_charXXXXXX.bytes`。
2. 拉取对应 Unity bundle（优先手机 UnityCache；缺失时走游戏 CDN/当前设备缓存）。
3. 用 UnityPy 提取 RIFF FEV 和 FSB5。
4. 用现有 `tools/extract_dating_audio.py` 的 FEV 解析逻辑读取：
   - event GUID
   - timeline 触发点
   - random selector / weight
   - sample stream 名和时长
5. 解析 `Master.strings/STDT` 或通过可运行的 FMOD `GetStringInfo` 导出 `GUID -> event path`。
6. 对 KR event path 做规范化匹配：
   - `mix...` / `motion...` / `touch...`：优先自动映射到 Spine 动作名。
   - 只有 `Joy/Smile/Sigh/Pain/...` 的角色：标记为“需要 `SpineInteractionPointTable` / 运行态表映射”，不要硬配。
7. 用 vgmstream + ffmpeg 只转码网页实际引用的 KR OGG。
8. 生成/合并 `data/dating_audio.json`，前端统一用 `costumeId + animationName` 调度。

按这个分类，`067104` 属于“动作型片段存在，值得优先自动化”的角色；`003303` Nebris 属于
“纯情绪池，需要表映射”的角色。

#### 2026-06-24 全量 interaction voice bank 审计

当前 `file.json` 中登记的 `common-interactionvoice.../interaction_charXXXXXX.bytes`
共有 19 套；这不是全 192 套服装都有的资源，而是当前客户端实际下发的 interaction voice bank。

按 `Master.strings/STDT` 的路径字典片段分类：

| costumeId | 角色 | 服装 | 类型 | 证据 |
|---|---|---|---|---|
| `001197` | 泰瑞丝 |  | 动作型 | `mix` / `motion` |
| `000396` | 莎赫拉查德 |  | 动作型 | `mix` / `long` |
| `067004` | 班塔纳 | 温泉修行者 | 动作型 | `mix` |
| `061492` | 杰尼斯 |  | 动作型 | `mix` / `motion` |
| `067603` | 威廉明娜 | 水上乐园女王 | 情绪型 | 只有情绪名 |
| `066403` | 安洁莉卡 | 霓虹救星 | 动作型 | `mix` / `touch` |
| `001106` | 泰瑞丝 | 保健部 | 情绪型 | 只有情绪名 |
| `003604` | 奥利维尔 | 传奇退役 | 动作型 | `mix` / `motion` |
| `004202` | 英格利得 | 卡迪斯的子弹 | 未找到 STDT interaction 区段 | bank 存在，但 Master 字典未扫到 `Interaction/Char004202_Int_` |
| `003203` | 罗安 | 名人兔女郎 | 情绪型 | 只有情绪名 |
| `004102` | 提尔 | 澄心无邪兔女郎 | 动作型 | `mix` / `motion` / `touch` |
| `000296` | 悠丝缇亚 |  | 情绪型 | 只有情绪名 |
| `067104` | 格兰希特 | 战地医疗兵 | 动作型 | `mix` / `motion` / `touch` |
| `003892` | 黎维塔 |  | 动作型 | `mix` / `motion` |
| `003303` | 内布利斯 | 新进员工 | 情绪型 | 只有情绪名 |
| `000706` | 伊柯利普斯 | 恶梦兔女郎 | 动作型 | `touch` |
| `001006` | 席比雅 | 比基尼特工 | 动作型 | `mix` / `motion` |
| `003402` | 墨菲亚 | 白日梦兔女郎 | 情绪型 | 只有情绪名 |
| `060802` | 爱丽洁 | 代号O | 情绪型 | 只有情绪名 |

临时审计输出保存在忽略目录：

```text
local_device_cache/bd2_current_20260624/interaction_voice_audit.tsv
```

结论：

- 不能再按单个 Nebris 推断全局工作量；当前 19 套中约 12 套有动作型片段，可优先自动化。
- Nebris (`003303`) 确实有 interaction voice bank 和 15 个 KR voice event 名，但都是
  `Excitement/Joy/Negative/Neutral/Pain/Positive/Sigh/Smile/Surprise` 这类情绪名。
- 对动作型角色，自动化可以先用 `event path` 里的 `mix/motion/touch` 匹配 Spine 动作。
- 对情绪型角色，必须继续找 `SpineInteractionPointTable` 或运行态映射；否则硬配会语义错。

#### ADB 协作协议

Codex 当前沙箱经常无法启动 adb daemon（`smartsocket Operation not permitted`），但用户本机
终端可以正常运行 adb。后续遇到 adb 卡点时：

1. Codex 先给出最小可复现命令，不再反复尝试启动 daemon。
2. 用户在本机终端运行命令。
3. 用户把 stdout/stderr 或生成文件路径贴回。
4. Codex 继续解析结果。

优先需要用户协助拉取的当前资源示例：

```bash
adb pull \
  /sdcard/Android/data/com.neowizgames.game.browndust2/files/UnityCache/Shared/945a97e12197d928b1ecb0c8c9d84700/8cc0e66f4cfed48b14c5e1d5f29dd40e/__data \
  /Users/woods/bd2web/local_device_cache/bd2_current_20260624/interaction_char067104.bundle
```

如果路径不存在，先在设备上查：

```bash
adb shell 'find /sdcard/Android/data/com.neowizgames.game.browndust2/files -path "*945a97e12197d928b1ecb0c8c9d84700*" -o -path "*8cc0e66f4cfed48b14c5e1d5f29dd40e*"'
```

#### 2026-06-24 当前版本 dating prefab 复查

用户已从手机拉取当前版本：

```text
local_device_cache/bd2_current_20260624/common-char-datingillust_assets_all.bundle
size = 385,932,491
bundleName = f17229717fff2baf0b72e1eb98e19b91
hash = cf55f1e92adbc7dfe8e085fd5d4ac062
```

用 UnityPy 扫当前大包确认：

- 当前包有 19 个 `Illust_datingX` 根配置（`Illust_dating1` 到 `Illust_dating19`）。
- `Illust_dating1`（Nebris）当前版本根配置仍然没有 `VoiceSoundEventName`：

```text
InteractionPointGroupId = 1/2/3
GroupDefaultSpineMotionName = idle1 / idle2 / idle3
MotionNameByScoreList = []
```

- `Illust_dating19`（`067104` 战地医疗兵格兰希特）存在明确 prefab 级语音映射：

```text
MixAnimationName = mix1_14_1
VoiceSoundEventName = Common/Char067104/Interaction/Char067104_Int_Surprise2
SFXSoundEventName = event:/Cinematic/Visual_Novel/Char067104/Interaction/Idle1/mix1_14_1
```

- `Illust_dating15` / `Illust_dating18` 也仍有 `Char067004_Int_Shout1` 的 gauge 配置。

因此结论更精确：

- “prefab 层可能直接有 voice 映射”是真的，`067104` 已经是正例。
- 但 Nebris 的普通点击/动作 voice 映射不在 `Illust_dating1` 根配置中；它要么在
  `SpineInteractionPointTable`，要么在运行时代码按情绪/状态选择，要么在还没定位到的其他资源层。
- 这次 logcat 命中的是 `adbd service requested ... dump_fmod_strings_Char003303`，只是之前 shell
  命令的 adb 日志，不是游戏运行时播放语音的日志。

#### 2026-06-24 情绪型角色 prefab / point / Spine 复查

继续检查 Nebris 以及其他情绪型角色后，当前结论如下：

1. 全量扫描当前 `common-char-datingillust_assets_all.bundle` 的所有 `MonoBehaviour` typetree，
   `VoiceSoundEventName` 只出现在 4 个组件：
   - `Illust_dating15`：`Char067004_Int_Shout1`
   - `Illust_dating18`：`Char067004_Int_Shout1` 残留/复用配置
   - `Illust_dating19`：`Char067104_Int_Surprise2`
   - `Illust_dating16`：字段存在但值为空
2. 扫描 Nebris 与其他情绪型角色相关关键词：
   - `003303` Nebris
   - `003203`
   - `003402`
   - `060802`
   - `067603`
   - `001106`
   - `000296`

   没有发现 `VoiceSoundEventName` / `SoundVoiceName` / `SoundMotionVoiceName` 与这些角色的
   point 组件绑定；命中的 `000296` / `060802` / `067603` 只是 point GameObject、boneName
   或普通组件上下文，不是 voice 字段。
3. 扫描 `illust_dating1.skel`：
   - 能看到 `point1_18_drag_event`、`point2_22_drag_event` 等 Spine 事件/点名。
   - 没有 `Joy/Smile/Sigh/Pain/Excitement/Surprise` 等 voice event 名。
   - 其他 skel 中的 `Smile/Surprise` 命中多为表情/贴图 attachment 名，不是音频映射。

因此对情绪型角色的判断更稳了：它们不是“没声音”，而是 **当前可直接解包的 dating prefab、
point 组件、Spine skeleton 里都没有动作→情绪语音映射**。这类映射下一步最可能在：

- `SpineInteractionPointTable` / `SpineInteractionTable` 等加密 Data 表；
- 或游戏运行时根据 point/action 状态动态选择情绪 voice；
- 或还未定位到的其他配置资源层。

非 root 下一步可继续尝试：

```bash
adb logcat -c
# 在游戏里进入 Nebris 心契并点击一个确定动作
adb logcat -d | grep -i -E 'Char003303|InteractionVoice|SoundVoice|Joy1|Smile1|Sigh1|Surprise1|FMOD|SoundMgr'
```

如果 logcat 仍没有游戏自己的声音日志，就需要从“离线解 Data 表 / 非 root 动态插桩 / 黑盒音频指纹”
三条路线里选。

#### 2026-06-24 Nebris logcat 样本结论

用户提供了一份命令输出：

```bash
adb logcat -d | grep -i -E 'Char003303|InteractionVoice|SoundVoice|Joy1|Smile1|Sigh1|Surprise1|FMOD|SoundMgr'
```

样本共 293 行，结论：

- 没有任何真正的 `Char003303` / `003303` 命中；唯一命中来自第 1 行命令本身。
- 没有 `Joy1` / `Smile1` / `Sigh1` / `Surprise1` / `SoundVoiceName` / `SoundMgr` 播放事件日志。
- 有大量 `Internal FMOD Unload Back Completed`，说明这是 FMOD bank 生命周期日志，主要是卸载日志。
- 只看到一个交互语音 bank：

```text
BundleInteractionVoice/Interaction_Char061492.bytes
```

这不是 Nebris 的 `Interaction_Char003303.bytes`。

用户确认当时确实点击的是 Nebris。因此不能把 `Interaction_Char061492.bytes` 解释成“用户点了
061492”。更合理的解释是：logcat 窗口中混入了异步资源清理 / 旧场景 / 全局 FMOD bank
卸载日志；`Internal FMOD Unload Back Completed` 本身也不是播放事件，而是卸载完成回调。

因此这份 logcat 不能证明 Nebris 点击时触发了哪个情绪事件，也不能反推用户点错了角色；它只证明
当前过滤方式能看到 FMOD bank 的加载/卸载生命周期。后续如果继续用 logcat，需要抓“进入 Nebris
页面并点击某个点”前后的完整窗口，最好限制到游戏进程 PID 和明确时间段，且不要只 grep 情绪名，
否则游戏如果只输出 bank 名或内部 ID 会被过滤掉。

随后按更严格方式重抓：

```bash
adb logcat -c
adb shell pidof com.neowizgames.game.browndust2   # 13411
adb logcat -d --pid 13411 > local_device_cache/nebris_click_full.log
```

完整日志 453 行。能看到多次真实触摸输入：

```text
ViewPostIme pointer 0
ViewPostIme pointer 1
```

说明用户点击确实进入了游戏进程。但同一窗口内仍没有：

- `Char003303` / `003303`
- `Interaction_Char003303`
- `Joy` / `Smile` / `Sigh` / `Surprise` 等情绪事件
- `VoiceSoundEventName` / `SoundVoiceName`
- `FMOD` 播放事件或 bank 加载事件

该窗口只出现 Android/AAudio 音频流初始化、Unity 界面触摸、avatar duplicate load、
网络短暂断连等日志。由此可判定：**普通 logcat 无法直接看到 Nebris 心契点击触发的 voice event**。
继续在 logcat 里换关键词的收益很低；下一步应转向 Data 表解密/静态逆向，或黑盒录音指纹匹配。

下一步如果继续做 Nebris，应优先：

1. 找 Nebris 的 point/action → `Joy1` / `Smile1` / `Sigh1` 等 voice 事件映射。
2. 只把页面实际引用的 voice OGG 和 manifest 加进仓库。
3. 再考虑普通 touch 点的画面热区；目前只有两个推进点有 prefab 坐标，其他普通点建议走
   Spine 运行时 bone 坐标，不要直接用静态矩阵生成假热区。

#### 2026-06-24 Data 表 / IL2CPP 静态逆向阶段结论

用户已从设备拉取当前 APK：

```text
local_device_cache/apk_20260624/base.apk
local_device_cache/apk_20260624/split_base_assets.apk
local_device_cache/apk_20260624/split_config.arm64_v8a.apk
local_device_cache/apk_20260624/lib/arm64-v8a/libil2cpp.so
local_device_cache/apk_20260624/assets/bin/Data/Managed/Metadata/global-metadata.dat
```

当前能确认：

- `split_base_assets.apk` 内的 `assets/DefaultDB.db` 是合法 SQLite，但没有表结构，不能用于
  `SpineInteractionPointTable`。
- `global-metadata.dat` 明确包含交互表与字段：
  - `SpineInteractionPointTable`
  - `SpineInteractionTable`
  - `SoundVoiceName`
  - `SoundMotionVoiceName`
  - `LongPressFailVoiceName`
  - `LongPressLoopVoiceName`
  - `LongPressSuccessVoiceName`
- metadata 中还能看到直接 SQL：

```text
SELECT * FROM SpineInteractionPointTable WHERE interactionGroupId = {0}
SELECT * FROM SpineInteractionPointTable WHERE interactionGroupId = {0} AND groupId = {1}
SELECT * FROM SpineInteractionTable WHERE id = {0}
```

这进一步证明 Nebris 这类“情绪型 voice”的映射目标表就是
`SpineInteractionPointTable`，不是猜测。

当前 `Data/` 目录特征：

- 共有 78 个文件。
- 每个文件大小都是 4096 对齐。
- 每个文件前 16 字节完全相同：

```text
b3 d5 0c 27 2f 43 ab d8 f9 cf f1 4f 9a 24 6c a9
```

- 前 8KB 熵约 `7.97~7.98`，接近随机。
- 最大文件：

```text
local_device_cache/bd2_current_20260624/Data/t/9F251C63BC72551C681EE75D328FA090D56E444B
size = 77,307,904
sha1(content) = 4488809557D8AC343670AA1124ED6C891D931649
```

所以 `Data/` 很像多个加密 DB/表分片，不是 Unity bundle，也不是 gzip/protobuf 明文。
固定 16 字节头意味着它不是标准“每个 SQLCipher DB 随机 salt 不同”的裸格式；更可能是游戏封装过的
SQLCipher/加密页格式，或固定 header + 页级加密。

metadata 中有 SQLCipher/加密相关字符串：

```text
SQLite fail set key
SQLite success set
sqlite3_key: entered db={0} pKey={1} nKey={2}
codec_set_pass_key: entered db={0} nDb={1} cipher_name={2} nKey={3} for_ctx={4}
codec_key_derive: deriving key using AES256
```

这些字符串来自 `global-metadata.dat`，不是 `libil2cpp.so` 的明文符号。`libil2cpp.so` 本身没有
可直接用 `nm` 定位的 `sqlite3_key/sqlcipher` 符号；macOS 自带 `otool` 也不能直接解析 Android
ELF。因此需要 IL2CPP dump/反汇编才能从 `RawDataManager`、`SQLiteManager`、`AESDecrypt256`、
`GetGameDataFromStreamingAsset` 等方法继续追。

Neon 配置缓存：

```text
local_device_cache/bd2_current_20260624/Neo/Http/metadata.json
url = https://neon-file.akamaized.net/app/5063/config/android
contentLength = 368
```

对应 `Neo/Http/3` 是 368 字节高熵密文，不是 JSON 明文。它可能包含 CDN / GameData 配置，
但需要 Neon SDK 的解密逻辑，当前不能直接读。

已尝试但暂时不成立：

- 用 `common-dbdata.bin/info`、CDN URL、路径等常见字符串计算 SHA1/MD5/SHA256，未匹配
  `Data/` 文件名。
- 盲跑 SQLCipher key candidate 成本很高，且没有可靠 key 候选，暂时停止。
- 普通 logcat 看不到 `SoundVoiceName` 或具体 emotion voice 播放事件。
- 当前沙箱无法从 NuGet 拉 `Cpp2IL/Il2CppDumper`，本机 dotnet 可用但网络/配置受限。

下一步推荐路线：

1. **优先 IL2CPP dump**：在能联网/能装工具的环境用 `libil2cpp.so + global-metadata.dat`
   跑 Cpp2IL 或 Il2CppDumper，定位：
   - `RawDataManager.GetSQLite/SetSQLite`
   - `SQLiteManager.GetSQLiteAsync`
   - `AESDecrypt256/AESEncrypt256`
   - `GetGameDataFromStreamingAsset`
   - `PatchGameData`
   - `ServerGameData`
   然后找真正传给 SQLite/SQLCipher 的 key。
2. **运行态 hook**：如果设备能 root 或能跑 frida-server，hook `sqlite3_key` / `sqlite3_key_v2`
   或 `codec_set_pass_key`，直接打印 key 与 DB path。非 root 普通设备暂时做不了。
3. **黑盒录音指纹**：作为最后兜底，对每个点击动作录音，与 15 个 Nebris emotion OGG 做声纹匹配。
   这能做，但自动化成本较高，而且只解决单角色，不如先攻 Data 表。

## 2026-06-29 Nebris / illust_dating1 情绪型互动语音接入完成

Claude 已通过 frida-il2cpp-bridge 抓到 `SpineInteractionPointTable` 全量母表，并生成：

```text
data/dating_interaction_tables.json
data/illust_dating1_interaction.json
tools/il2cpp-re/all_interaction_tables_raw.log
tools/il2cpp-re/char003303_table_raw.log
```

本轮在此基础上完成 Nebris (`illust_dating1` / `char003303`) 的 voice 接入。

### 资源定位

`file.json` 中 Nebris interaction voice bank：

```text
readableName = common-interactionvoice_assets_bundleinteractionvoice/interaction_char003303.bytes
bundleName   = a95eeb8e3db465231e037bdca581ebe2
hash         = 77705eb8a0103dcb9b9982ebac3d2162
fileHash     = 04D5B1622A98907260608FD5278A5882
size         = 829109
```

旧备份中已存在对应 UnityCache 文件，大小与 `file.json` 一致：

```text
/Users/woods/bd2_gamedata_backup/UnityCache/Shared/a95eeb8e3db465231e037bdca581ebe2/77705eb8a0103dcb9b9982ebac3d2162/__data
```

从该 bundle 解出：

```text
local_device_cache/bd2_current_20260624/interaction_char003303/interaction_char003303.bank
local_device_cache/bd2_current_20260624/interaction_char003303/interaction_char003303.fsb
```

FEV 解析结果：

```text
events = 30
timelines = 30
multiInstruments = 15
waits = 42
waves = 42
```

其中 KR 可用事件为 15 个，引用 42 个 sample。30 个 event 里另一半不是当前 KR 可播事件；
因此验收断言应是 `--expect-events 15 --expect-samples 42`，不是 30。

### 工具改动

`tools/extract_dating_audio.py` 新增：

- `--infer-event-paths-from-samples`
- `short_event_name_from_sample()`

用途：当 `GUID<TAB>event path` 文件为空或缺少目标角色路径时，从 FSB stream name 反推事件名。
Nebris 的 stream name 形如：

```text
Char003303_Int_Smile1_1
Char003303_Int_Surprise2_1
```

去掉 `Char003303_Int_` 前缀和末尾 sample 序号即可得到 manifest event key：

```text
Smile1
Surprise2
```

这只在显式传 `--infer-event-paths-from-samples` 时启用，不影响 dating18 莎拉已有的
SoundMaster event path 流程。

另外，当前 Homebrew `ffmpeg 8.1.2` 没有 `libvorbis` encoder。工具已改为：

1. 优先 `libvorbis`
2. 失败后 fallback 到内置 `vorbis`
3. 内置 vorbis 需要 `-strict -2`，且只支持 2 声道，因此 fallback 时加 `-ac 2`

### 生成命令

```bash
PYTHONPATH=/Users/woods/bd2web/local_device_cache/pydeps \
python3 tools/extract_dating_audio.py \
  --dating-id illust_dating1 \
  --char-id char003303 \
  --source-version 202606240959 \
  --bundle /Users/woods/bd2_gamedata_backup/UnityCache/Shared/a95eeb8e3db465231e037bdca581ebe2/77705eb8a0103dcb9b9982ebac3d2162/__data \
  --fsb local_device_cache/bd2_current_20260624/interaction_char003303/interaction_char003303.fsb \
  --event-paths local_device_cache/bd2_current_20260624/voice_event_paths/Char003303.tsv \
  --infer-event-paths-from-samples \
  --language KR \
  --decode \
  --expect-events 15 \
  --expect-samples 42
```

产物：

```text
audio/dating/illust_dating1/voice/*.ogg   # 42 条
data/dating_audio.json                    # illust_dating1.samples/events 已填充
```

### actions 映射生成

新增 `tools/apply_dating_interaction_voice_actions.py`，将
`tools/il2cpp-re/all_interaction_tables_raw.log` 中的 repeated voice/motion 映射合并到
`data/dating_audio.json.characters.illust_dating1.actions`。

生成命令：

```bash
python3 tools/apply_dating_interaction_voice_actions.py \
  --dating-id illust_dating1 \
  --char-id char003303 \
  --gid 1
```

结果：

```text
64 table rows -> 88 voice actions
```

映射规则：

- `SoundVoiceName` → `mix<groupId>_<id>_*`
- `SoundMotionVoiceName` → `motion<groupId>_<id>`
- raw log 中 repeated 字段的重复项保留为数组重复项；前端随机选数组里的一个 event，
  因此重复次数自然成为简易权重。

例子：

```json
"mix1_18_1": ["Surprise1", "Smile1", "Surprise1", "Smile1"],
"mix1_18_2": ["Surprise1", "Smile1", "Surprise1", "Smile1"],
"motion1_18": ["Surprise2"]
```

### 前端改动

`dating.html` 的 `DatingAudioController` 原本只支持：

```js
actions[animationName] = "Smile1"
```

现在兼容：

```js
actions[animationName] = ["Surprise1", "Smile1", "Surprise1", "Smile1"]
```

数组时随机选择一个已存在的 event；字符串路径保持原行为。这样不影响 dating18。

### 验证

已完成静态验证：

```text
node --check /tmp/dating-script.js                 # dating.html script 语法 OK
python3 -m json.tool data/dating_audio.json        # JSON OK
python3 -m json.tool data/dating_interaction_tables.json
python3 -m json.tool data/illust_dating1_interaction.json
```

manifest 引用检查：

```text
illust_dating1 bad voice refs = 0
illust_dating1 bad sfx refs   = 0
illust_dating18 bad voice refs = 0
illust_dating18 bad sfx refs   = 0
```

文件检查：

```text
audio/dating/illust_dating1/voice/*.ogg = 42
missing voice files = 0
audio/dating/illust_dating1/voice size ≈ 896 KB
```

本地 HTTP server 在 Codex 沙箱中出现端口连接异常（server 显示正常监听但 curl 连接失败），
未继续死磕。建议用户本机浏览器验证：

```text
http://localhost:8080/dating.html?dating=1&audioDebug=1&v=20260629
```

预期：Nebris 点击/拖拽互动时同时播放 SFX 和 KR emotion voice；`audioDebug=1` 下
`document.documentElement.dataset.datingAudioChannel` 会在 voice/sfx 间更新。

## 2026-06-29 纠偏：Nebris 语音从 animation-based 改为 point-based

用户实测反馈：Nebris / `illust_dating1` 的互动语音“都有声音但都对不上”。复查后确认上一版接法的核心问题是抽象层错了：

- `SpineInteractionPointTable` 的语义是“互动点 → 语音”：`(interactionGroupId, groupId, id)` 对应 `SoundVoiceName` / `SoundMotionVoiceName`。
- 上一版把它硬映射成 `actions[animationName]`，即 `mix<groupId>_<id>_*` / `motion<groupId>_<id>`。
- 这会带来两个问题：
  1. 页面按 Spine animation `start` 事件播 voice，连续动作 `mix -> motion` 时后一个 animation 会停止前一个音频，导致实际听到的很可能不是点击点的 `SoundVoiceName`。
  2. 游戏表本来绑定的是互动点，不是动画名；把点表挂到动画名上会让后续角色继续沿错抽象扩展。

### 修正方案

`tools/apply_dating_interaction_voice_actions.py` 改为默认生成 point-based 字段：

```json
"interactionVoices": {
  "1_18_0": {
    "voice": ["Surprise1", "Smile1", "Surprise1", "Smile1"],
    "motion": ["Surprise2"]
  }
}
```

字段约定：

- key = `<groupId>_<pointId>_<toolId>`，当前 Nebris 的表没有 tool 维度，因此写为 tool `0`，与 `PREFAB_POINT_ACTIONS` key 形状保持一致。
- `voice` 来自 `SoundVoiceName`，在用户点击该互动点时播放。
- `motion` 来自 `SoundMotionVoiceName`，在同一互动点后续的 motion 动画开始时播放。
- repeated voice 项继续保留重复，用作简单随机权重。

同时清空 `characters.illust_dating1.actions`，避免旧 animation-based voice 继续触发。莎拉 / `illust_dating18` 仍保留原本的 animation actions，不受影响。

### 前端修正

`dating.html` 的 `DatingAudioController` 改为分频道管理播放代次：

- voice 和 sfx 使用独立 generation，避免连续动画开始时 sfx 调度把 point voice 取消。
- `stop("voice")` 只停 voice，`stop("sfx")` 只停 sfx。
- 新增 `playInteractionVoice(datingId, pointKey, phase)`，直接按 `interactionVoices[pointKey].voice/motion` 播放。

互动入口调整：

- `playPoint(name, btn)` 从 `point<stage>_<id>...` 推导 pointKey，点击时播放 `voice`。
- `playPrefabAction(action, btn, key)` 接收 prefab key，点击时播放 `voice`。
- Spine track start 监听中，如果当前动画属于本次互动点的 `motions`，再播放该点的 `motion` voice。

### 当前验证

```text
python3 -m json.tool data/dating_audio.json                 OK
python3 -m json.tool data/dating_interaction_tables.json    OK
python3 -m json.tool data/illust_dating1_interaction.json   OK
node --check /tmp/dating-script.js                          OK
```

引用检查：

```text
illust_dating1 voice actions = 0
illust_dating1 interaction voices = 64
illust_dating1 bad voice refs = 0
illust_dating1 bad sfx refs = 0
illust_dating18 voice actions = 24
illust_dating18 bad voice refs = 0
illust_dating18 bad sfx refs = 0
illust_dating1 OGG = 42，missing referenced files = 0
```

浏览器验证建议：

```text
http://localhost:8080/dating.html?dating=1&audioDebug=1&v=20260629b
```

`audioDebug=1` 下，点击互动时应先看到 `datingAudioPhase=point:<key>:voice...`；推进 motion 开始时再看到 `point:<key>:motion...`。如果用户仍觉得语义不对，下一步不要再改音频管线，而要回到运行态：在真机上对同一个 point 点击抓 `SpineInteractionPointTable` 使用路径或 hook `PlayVoiceSFX(eventName)`，确认客户端实际传入的 eventName。

## 2026-06-29 再纠偏：Nebris SFX 误接导致“机关枪/战斗音效”

用户再次实测反馈：Nebris 点击后听到类似战斗/机关枪的声音，并且热区点击体验很差。复查 `data/dating_audio.json.characters.illust_dating1.sfx` 后确认：

- SFX 样本不是干净的 Nebris 心契互动音效，里面混有大量通用/其他角色/战斗感 sample，例如：
  - `Common_Punch_Mid_Hit_05`
  - `Char004202_Glitch_01`
  - `Char003604_motion1_2`
  - `Char067004_Blanket_Throw_01`
- 这些 SFX 事件虽然路径长得像 `event:/Cinematic/Visual_Novel/Char003303/Interaction/...`，但实际 choices 指向的 sample 池明显不可靠。
- 用户听到的“机关枪/战斗机关声”来自这条 SFX 自动播放链，而不是 Nebris voice OGG。

### 当前止血处理

在 `data/dating_audio.json` 中为 Nebris 增加：

```json
"sfx": {
  "disabled": true
}
```

`dating.html` 已识别该标记：

- `character.sfx.disabled === true` 时，不再预加载 SFX。
- `character.sfx.disabled === true` 时，不再按 animationName 自动播放 SFX。
- Nebris 仍保留 voice：42 个 voice OGG、15 个情绪事件、64 个 point-based `interactionVoices`。

### 验证

```text
python3 -m json.tool data/dating_audio.json   OK
node --check /tmp/dating-script.js            OK
illust_dating1 sfx.disabled = true
voice samples = 42
interactionVoices = 64
sfx samples 仍保留索引但不会播放 = 66
```

### 后续原则

Nebris / 情绪型角色后续不要自动接 SFX，除非能从运行态或更精确的 FMOD event graph 证明 choices 确实是该角色该互动点的音效。当前阶段应先只验证 voice。

热区问题单独看：Nebris 当前只有两个有坐标证据的推进热区 `1_18_0` / `2_22_0`，普通互动点主要通过左侧按钮触发；不要把“全身任意点击都可触发”当作已完成能力。

## 2026-06-29 修复：热区点击没有 voice，菜单点击才有

用户实测：禁用 Nebris 错误 SFX 后声音明显正常，但“点击热区没有声音，点击左侧菜单栏互动才有”。

根因：左侧菜单按钮调用：

```js
playPrefabAction(action, b, key)
```

会把 prefab point key（例如 `1_18_0`）传入，因此可以查到：

```js
interactionVoices["1_18_0"].voice
```

但热区渲染分支之前调用的是：

```js
playPrefabAction(item.action, null)
```

没有传 `item.key`，所以动画能播放，但 `playInteractionVoice()` 没有 pointKey，自然没有 voice。

### 修复

`renderHotzones()` 普通热区分支改为：

```js
b.onclick = () => playPrefabAction(item.action, null, item.key);
```

同时补齐同类交互：

- longPress 热区：`beginLongPress(item.action, b, event, item.key)`
- gyro drag 热区：`beginGyroDrag(item.action, b, event, item.key)`
- deviceorientation 触发：保留 `activeGyroPointKey`，倾斜触发时传给 `playGyroAction(..., pointKey)`

### 验证

```text
python3 -m json.tool data/dating_audio.json   OK
node --check /tmp/dating-script.js            OK
menu passes key                               True
hotzone passes key                            True
longpress receives key                        True
sfx disabled respected                        True
```

## 2026-06-29 热区坐标方案纠偏：撤回手猜 scale，改用 skeleton-space 导出

用户反馈：Nebris 热区已经有声音，但位置感觉对不上，怀疑和之前莎拉一样是图片/Spine 坐标和热区坐标没对上。

一开始曾按 `illust_dating1` 的 `Parent scale=0.5` 推断需要 `HOTZONE_WORLD_SCALES.illust_dating1 = 2`。
用户提醒这是通用问题，不能靠猜。该思路已撤回。

参考莎拉当时的成功方案，重新从 Unity prefab 做坐标证据链：

- 旧 `PREFAB_HOTZONES` 的 Nebris 数值是沿 RectTransform 父链算到 `Illust_dating1` 根画布的 root-space。
- 前端 `hotzoneToScreenBox()` 投影时使用的是 SpinePlayer 的 skeleton world 坐标。
- 两者不是同一个坐标系；直接投影 root-space 必然错位。
- 莎拉的 `HOTZONE_WORLD_SCALES=4` 本质是在把 root-space 恢复成 skeleton-space。

实测重新导出 Nebris `1_18_0`：

```text
box -> root:
  x=-509.1, y=-959.6, width=641.2, height=721.2

box -> SkeletonGraphic:
  x=-1018.1, y=-1319.1, width=1282.4, height=1442.4
```

前端旧值正是 `box -> root`，所以问题坐实。

### 通用修复

新增脚本：

```bash
PYTHONPATH=/Users/woods/bd2web/local_device_cache/pydeps \
python3 tools/extract_dating_hotzones.py
```

脚本读取 `common-char-datingillust_assets_all.bundle`，对所有 `IsNextStateWhenActionEnd=1` 的 prefab
推进热区，将 `_interactionBoxZoneRectTransform` 换算到对应 `SkeletonGraphic (illust_datingX)` 坐标系。

`dating.html` 调整：

- Nebris 两个推进热区替换为 skeleton-space：
  - `1_18_0`: `x=-1018.1, y=-1319.1, width=1282.4, height=1442.4`
  - `2_22_0`: `x=304.2, y=257.6, width=491.5, height=664.4`
- 新坐标增加 `space: "skeleton"`。
- `hotzoneToScreenBox()` 对 `space: "skeleton"` 的热区不再应用 `HOTZONE_WORLD_SCALES`。
- 莎拉既有已验证的普通身体点/牌局点暂不一刀切迁移，继续保留旧路径，避免破坏已还原好的行为。

### 验证

```text
node --check /tmp/dating-script.js                    OK
tools/extract_dating_hotzones.py 可导出 Nebris 2 点   OK
```

后续原则：新增/修复热区时优先生成 skeleton-space 坐标，不要手调 x/y，也不要仅凭 `scale` 字段猜补偿。

## 2026-06-29 Nebris 普通热区补全

在用户确认 Nebris 两个推进热区坐标已经对齐后，继续按同一条“莎拉方案”的证据链补齐普通互动热区。

### 方法

不手画、不按比例猜。使用：

```bash
PYTHONPATH=/Users/woods/bd2web/local_device_cache/pydeps \
python3 tools/extract_dating_hotzones.py
```

该脚本默认导出所有 prefab 互动点的 skeleton-space 热区；如只想审计阶段推进点，可加：

```bash
python3 tools/extract_dating_hotzones.py --only-advancing
```

### 本轮结果

`dating.html` 的 `PREFAB_HOTZONES.illust_dating1` 从只有 2 个推进热区扩展为 64 个 prefab action key：

```text
stage 1: 18
stage 2: 22
stage 3: 24
unique: 64
```

阶段 3 的 `3_6_0` / `3_7_0` 是 prefab hidden 点：坐标证据保留在 `PREFAB_HOTZONES` 中，但页面的
`currentPrefabActions()` 仍按 `action.hidden` 过滤，不会在正常交互中显示。

### 验证

```text
node --check /tmp/dating-script.js                     OK
illust_dating1 hotzone keys = 64
unique = 64
stage counts = {1:18, 2:22, 3:24}
--only-advancing illust_dating1 = [1_18_0, 2_22_0]
```

浏览器验证建议：打开 `dating.html?dating=1&audioDebug=1&v=20260629f`，打开“显示热区”检查普通点覆盖区域。

## 2026-06-29 单角色自动化接入工具

在 Nebris 路线验证后，新增 `tools/build_dating_character.py`，把单角色接入流程串成一个批处理入口。

### 能自动完成

1. 从 `common-char-datingillust_assets_all.bundle` 导出指定 `dating-id` 的 skeleton-space 热区 JSON。
2. 从 `interaction_charXXXXXX.bytes` Unity bundle 中提取 RIFF FEV bank，并从 bank 中切出 FSB5。
3. 调用 `tools/extract_dating_audio.py` 生成 voice manifest；可选 `--decode` 生成 OGG。
4. 调用 `tools/apply_dating_interaction_voice_actions.py`，用 `SpineInteractionPointTable` raw log 合并 point-based `interactionVoices`。
5. 默认写入 `sfx.disabled=true`，避免 Nebris 那类混杂 SFX 自动误播。
6. 校验 voice event 引用与 OGG 文件存在性。

### Nebris smoke test

```bash
PYTHONPATH=/Users/woods/bd2web/local_device_cache/pydeps \
python3 tools/build_dating_character.py \
  --dating-id illust_dating1 \
  --char-id char003303 \
  --gid 1 \
  --source-version 202606240959 \
  --voice-bundle /Users/woods/bd2_gamedata_backup/UnityCache/Shared/a95eeb8e3db465231e037bdca581ebe2/77705eb8a0103dcb9b9982ebac3d2162/__data \
  --expect-events 15 \
  --expect-samples 42 \
  --no-decode
```

输出摘要：

```text
hotzones illust_dating1: 64
完成：15 个 KR 事件，15 个时间触发点，0 个动作映射，42 个 sample
illust_dating1: 64 table rows -> 64 interaction voice points, 0 legacy actions
illust_dating1: sfx.disabled=true
verify illust_dating1: events=15, samples=42, interactionVoices=64, badVoiceRefs=0, missingFiles=0
```

### 当前边界

- 工具不会自动改 `dating.html` 的 `PREFAB_HOTZONES` 常量；它会把热区证据写到
  `local_device_cache/dating_build/dating_hotzones.json`。确认后再接入前端，后续可进一步改成页面读取外部 JSON。
- 对有 toolId 的角色，`apply_dating_interaction_voice_actions.py` 现在会读取 hotzone key，把同一 `groupId/id`
  映射到所有 `stage_point_tool` 变体，不再只写 `_0`。
- SFX 仍默认禁用。除非有运行态证据证明 SFX event graph 干净，否则不要自动接。

## 2026-06-29 前端改为读取外部热区 JSON

为进一步自动化新增角色，`dating.html` 已接入外部热区数据：

```text
data/dating_hotzones.json
```

当前该文件只包含已验证的 Nebris / `illust_dating1` 64 个 skeleton-space 热区，避免一次性覆盖莎拉等已调好的特殊角色。

### 前端行为

- 页面启动/切换心契时异步 fetch `./data/dating_hotzones.json`。
- `prefabHotzone(datingId, key)` 优先读取外部 JSON：
  1. `data/dating_hotzones.json[datingId][key]`
  2. 旧 `PREFAB_HOTZONES[datingId][key]` 兜底
- 外部 JSON 加载完成后会重新 schedule 热区投影。

### 自动化更新

`tools/build_dating_character.py` 新增：

```text
--update-hotzones-data
```

传入后会把本角色热区合并到 `data/dating_hotzones.json`。Nebris smoke test 已确认：

```text
/Users/woods/bd2web/data/dating_hotzones.json: updated illust_dating1 hotzones=64
verify illust_dating1: events=15, samples=42, interactionVoices=64, badVoiceRefs=0, missingFiles=0
```

后续新增普通情绪型角色的理想流程：跑 `build_dating_character.py --update-hotzones-data --decode`，确认页面效果后提交生成的 audio、manifest、hotzones JSON；除非角色有特殊交互，否则不再需要手改 `dating.html` 热区块。

## 2026-06-29 情绪型心契批量接入 1–14

在 Nebris 方案稳定后，继续把“互动动作、热区、语音”三张表全部数据化，验证能否批量接其他角色。

### 前端数据化

新增外部 action 数据：

```text
data/dating_actions.json
```

`dating.html` 行为：

- 切换心契时异步 fetch `./data/dating_actions.json`。
- `prefabActionsFor(datingId)` 优先读取外部 JSON，旧 `PREFAB_POINT_ACTIONS` 只作为兜底。
- 外部 action 加载完成后会重新渲染阶段按钮和热区。

这一步很关键：此前很多角色页面没自动出现完整互动，不是资源没有，而是 `dating.html` 里只手写了少量推进点。
现在 action 来自 `common-char-datingillust_assets_all.bundle`，普通触摸/拖拽/gyro/连点/hidden 等都能被导出。

### 新增工具

`tools/extract_dating_actions.py`：

```bash
PYTHONPATH=/Users/woods/bd2web/local_device_cache/pydeps \
python3 tools/extract_dating_actions.py --dating-id illust_dating1
```

输出与 `PREFAB_POINT_ACTIONS` 兼容，key 与热区/语音统一为：

```text
<groupId>_<interactionId>_<toolId>
```

`tools/build_dating_character.py` 新增：

```text
--update-actions-data
```

传入后会把本角色 action 合并到 `data/dating_actions.json`。

### FEV 兼容修正

批量到 Eris / `char060802` 时遇到 FEV playlist 中引用不存在的 WAIT 候选。复核后这些 GUID 既不是 WAIT，
也不是 WAV 或嵌套 instrument，更像 FMOD 随机池里的空/不可用候选。

`tools/extract_dating_audio.py` 已调整为：

- 跳过未知 WAIT / WAV 候选；
- 同一个触发点只要还有有效 choice 就保留；
- 没有有效 choice 的触发点不写；
- stderr 打 warning，方便后续审计。

不要把未知候选硬接成其它声音；这正是之前会错播战斗/机关枪声音的风险方向。

### 已批量完成

本轮实际解码 OGG，并完成 JSON/引用/文件校验：

```text
illust_dating1  char003303 gid=1   events=15 samples=42 files=42 voices=64
illust_dating2  char003402 gid=2   events= 7 samples=28 files=28 voices=55
illust_dating3  char003203 gid=3   events= 7 samples=24 files=24 voices=36
illust_dating4  char001106 gid=4   events=10 samples=40 files=40 voices=44
illust_dating5  char060802 gid=5   events=15 samples=60 files=60 voices=43
illust_dating6  char067603 gid=6   events=17 samples=68 files=68 voices=36
illust_dating7  char001006 gid=7   events=16 samples=64 files=64 voices=50
illust_dating8  char066403 gid=8   events=12 samples=48 files=48 voices=55
illust_dating9  char000706 gid=9   events=15 samples=60 files=60 voices=53
illust_dating10 char004102 gid=10  events=19 samples=76 files=76 voices=33
illust_dating11 char067004 gid=11  events=18 samples=72 files=72 voices=53
illust_dating12 char003604 gid=12  events=15 samples=60 files=60 voices=45
illust_dating13 char004202 gid=13  events=20 samples=80 files=80 voices=33
illust_dating14 char067104 gid=14  events=20 samples=79 files=79 voices=90
```

全部校验结果：

```text
badVoiceRefs=0
missingFiles=0
sfx.disabled=true
```

也就是说：写进 `data/dating_audio.json` 的 voice 引用都能找到真实 event，且对应 OGG 文件都已生成。
表里引用但 bank 不存在的 `Special*` / `Motion*` / `Mix*` 不会写入前端，相关点静默，不错播。

### 14 号补齐记录

`illust_dating14` / `char067104` 的 voice bundle 一开始在本地大包里缺当前 hash。catalog 记录：

```text
bundleName = 945a97e12197d928b1ecb0c8c9d84700
hash       = 8cc0e66f4cfed48b14c5e1d5f29dd40e
readable   = common-interactionvoice_assets_bundleinteractionvoice/interaction_char067104.bytes
size       = 1905334
```

已从设备 UnityCache 拉到：

```text
/Users/woods/bd2_gamedata_backup/UnityCache/Shared/945a97e12197d928b1ecb0c8c9d84700/8cc0e66f4cfed48b14c5e1d5f29dd40e/__data
```

然后用同一套 `build_dating_character.py` 跑通。校验：

```text
hotzones=128
actions=128
events=20
samples/files=79
interactionVoices=90
badVoiceRefs=0
missingFiles=0
```

注意：运行日志里出现过 ffmpeg `Unknown encoder 'libvorbis'` warning，但最终产物已用 `file` 验证为
`Ogg data, Vorbis audio, stereo, 48000 Hz`，79 个 OGG 均非空。

### 当前边界

- `illust_dating15–18` 不在这批 `SpineInteractionPointTable` 全量表里；莎拉 / `illust_dating18` 保留既有特殊实现。
- SFX 继续默认禁用。没有运行态证据前，不要自动接 SFX。

## 2026-06-29 保健社泰瑞丝互动链路还原

参考资料：

- GameKee「满好感角色互动攻略」保健社-泰瑞丝段落
- Bahamut「保健社泰瑞絲『大保健教學』」步骤图与文字说明

本轮先处理 `illust_dating4` / `char001106` / 保健社泰瑞丝。

### 阶段一进入阶段二

原本 `1_28_0` 可以直接点击进入阶段二，但教程与游戏流程是三步：

```text
拉开双腿间裙子 -> 点击药膏上药 -> 贴 OK 绷 -> 进入阶段二
```

前端已为泰瑞丝单独加状态门控：

- `1_26_0`：标记 `teresseSkirtOpened`
- `1_27_0`：要求已拉开裙子，成功后标记 `teresseOintmentApplied`
- `1_28_0`：要求已上药，才播放 `motion1_28` 并进入阶段二

如果跳步，会提示正确顺序，不会直接进阶段二。切回阶段一或重新加载角色会重置该临时互动状态。

### 阶段二互动命名

`data/dating_actions.json` 仍提供真实动作、语音和热区；`dating.html` 对泰瑞丝做局部覆盖，把教程里确认的阶段二重点点位改成更接近游戏含义的文案：

- 脸
- 胸部互动
- 左/右大腿
- 左/右脚与袜子
- 脚底搔痒
- 色笔人体彩绘
- 葛洛堤塞子
- 衣物上药

注意：这轮只还原了泰瑞丝最关键的阶段推进顺序与已知特殊点位命名/动作入口；阶段二若要做到游戏级“道具先后顺序/镜头移动后才可点”等细节，还需要继续逐点录屏对照。

## 2026-06-30 代号O爱丽洁互动链路还原

参考资料：

- Bahamut「代号O愛麗潔捕獲愛情好感度互動教學」

本轮处理 `illust_dating5` / `char060802` / Eris。

### 阶段一进入阶段二

文章说明进入二阶段顺序是：

```text
点绳子 -> 点大腿钥匙 -> 马上点锁
```

原本前端把 `1_18_0` 当作直接进入阶段二入口，导致可以跳过教程里的前置互动。现在改为爱丽洁专用状态门控：

- `1_13_0`：点绳子，标记 `erisRopePulled`
- `1_15_0`：取得大腿钥匙，要求已点绳子，标记 `erisKeyTaken`
- `1_18_0`：点击锁，要求已取得钥匙，播放 `motion1_18` 并进入阶段二

跳步会显示正确顺序；切回阶段一或重新加载角色会重置临时状态。

### 阶段二工具

为 `illust_dating5` 加了工具名覆盖：

- `0`：手
- `1`：笔
- `2`：按摩棒
- `3`：鞭子

阶段二重点点位按教程含义补了按钮文案：手拉衣带/绳子、笔在大腿/腿根互动、按摩棒腿侧/腿根、鞭子腿侧/腿根/绳边。

### 鞭子连击

`2_28_3` 是鞭子连续动作池，含 `mix2_28_1` 到 `mix2_28_10`，原先会一次点击把整个 mix 数组排队播完。前端新增 `progressiveMix`：

- 每次点击只播放当前进度的一段 mix；
- 点击次数保存在 `interactionState`；
- 只对显式声明 `progressiveMix: true` 的动作生效，避免影响其他角色。

当前素材/前端只识别出爱丽洁阶段1和阶段2，没有独立阶段3待机按钮。文章里的“继续打到腿放下来”先用 `2_28_3` 递进播放表现，不硬造不存在的阶段。

## 2026-06-30 保健社泰瑞丝阶段二托盘道具热区/动作映射修复

用户反馈：保健社泰瑞丝二阶段里，点击画面上的葛洛堤塞子、色笔等道具不会触发对应动画。

本轮对照 Bahamut「保健社泰瑞絲『大保健教學～❤』」确认：二阶段重点道具互动包含：

- `18. 葛洛堤塞子`
- `19. 色笔人体彩绘（红、黑笔）`

第一轮排查结论：

- `illust_dating4.skel` 里确实存在动作：`mix2_28_1`、`mix2_29_1`、`mix2_30_1`，不是动画资源缺失。
- `data/dating_actions.json` 里也有对应动作：
  - `2_28_0`：色笔人体彩绘
  - `2_29_0`：葛洛堤塞子
  - `2_30_0`：衣物上药
- 自动热区里 `2_28_0` / `2_29_0` 来自 `point2_28_touch_follow` / `point2_29_touch_follow`。尝试过把所有 `*_follow` 点直接改用 Spine 运行时同名 bone 中心，但这会破坏部分原本已对齐的身体热区：follow 点的 RectTransform 可能带本地偏移，不能简单等同于 bone 中心。
- 泰瑞丝的 `point2_29_touch_follow` 运行时 bone 坐标实测在反应/效果区域，不在托盘道具本体上；`point2_28_touch_follow` 对应的点也不适合作为可见托盘色笔本体热区。因此不能用“全局动态 follow”解决这两个道具点。

2026-06-30 关键纠错：

- 仅验证“点击触发 `mix2_29_1`”是不够的。离线用 `vendor/spine-player-4.1.56.js` 读取 `illust_dating4.skel`，把 `idle2` 作为基准，再 apply 动画采样对比 slot attachment 后确认：
  - `mix2_29_1` / `mix2_30_1` 在当前 `idle2` 状态下只切换 5 个画面外 A 阶段裙摆 slot：`1_16_A_Skirt2`、`1_18_A_Skirt4`、`1_19_A_Skirt5`、`1_20_A_Skirt6`、`1_28_A_Skirt14`。
  - 它们不改 `tray_*`、`Cupping_*`、脚、脸等可见 slot，所以用户点击“塞子”看起来没反应是必然结果，不是热区坐标或播放速度问题。
  - `mix2_28_1` 实际操作的是 `tray_Ointment*`，不是色笔。
  - 真正的托盘道具可见动作是：
    - `mix2_18_1`：`tray_Cupping` / 葛洛堤塞子相关。
    - `mix2_23_1` / `mix2_24_1`：黑笔相关，其中 `mix2_24_1` 会出现人体绘制附件。
    - `mix2_25_1` / `mix2_26_1`：红笔相关。
    - `mix2_28_1`：药膏相关。

最终修复：

- 2026-06-30 再纠错：托盘道具不是“点托盘直接播最终动作”，而是游戏里的“先选择道具，再点目标位置”。
  - 塞子：点托盘 `2_17_0` 选择葛洛堤塞子，然后显示 3 个咬咬目标：`2_18_0` / `2_20_0` / `2_21_0`，分别播放 `mix2_18_1` / `mix2_20_1` / `mix2_21_1`。
  - 笔：黑笔 `2_23_0` 先选择，目标 `2_24_0` 播 `mix2_24_1`；红笔 `2_25_0` 先选择，目标 `2_26_0` 播 `mix2_26_1`。用户确认红/黑笔都应点左大腿根部，目标热区已统一移到左大腿根部。
  - 药膏：先点 `2_27_0`（內褲向右拉）设置 `teressePantyPulled`，再显示并允许点击托盘药膏 `2_28_0` 播 `mix2_28_1`；未拉开前 `2_28_0` 不显示，并保留 `requires` 兜底防误播。
- `dating.html` 新增泰瑞丝阶段二局部状态 `teresseToolMode`：
  - 默认只显示普通身体点 + 托盘道具选择点。
  - 选择塞子/黑笔/红笔后，只显示对应目标点，目标播放后回到默认手。
- `dating.html` 新增 `HOTZONE_OVERRIDES`，只覆盖 `illust_dating4` 阶段二的托盘选择点和当前确认的目标点。
- `prefabHotzone()` 改为优先使用 `HOTZONE_OVERRIDES`，再回退 `data/dating_hotzones.json` 和旧内置 `PREFAB_HOTZONES`。
- `2_29_0` / `2_30_0` 暂时标记 `hidden: true`，因为当前网页状态下它们只影响画面外裙摆，不应暴露成可点击的“塞子/上药”热区。

本地验证：

- `http://localhost:8080/dating.html?dating=4&stage=2&v=<timestamp>`
- 默认可点托盘上的：
  - `选择葛洛堤塞子 · 2_17_0 · tray Glutti plug [Manual]`
  - `选择黑笔 · 2_23_0 · tray black pen [Manual]`
  - `选择红笔 · 2_25_0 · tray red pen [Manual]`
  - `內褲向右拉 · 2_27_0 · panty pull right [Manual]`
  - `药膏上药 · 2_28_0 · tray ointment [Manual]`
- 点塞子后显示 `咬咬·位置1/2/3`；点黑笔/红笔后分别显示对应的人体彩绘目标。
- 2026-06-30 追加修正：最初曾尝试对所有 follow 热区做运行时 bone 重投影，还一度持续重建 DOM，导致点击被吞、身体热区偏离人物。已撤回全局 follow 动态重投影和投影回调时序改动，只保留泰瑞丝托盘道具的局部 `HOTZONE_OVERRIDES`。
- 2026-06-30 追加修正 2：此前“给 `2_29_0` 加 `holdMs`”是错误方向；采样证明 `mix2_29_1` 本身没有当前画面内可见变化。已改为把可见托盘热区映射到真实 `tray_Cupping` / `tray_pen` / `tray_Ointment` 动作。
- 2026-06-30 追加修正 3：按用户截图确认“塞子/笔是先选道具再点位置”，已改成状态机，而不是直接托盘播放最终动作。三处咬咬目标坐标目前按 Spine 采样的 `tray_Cupping*` 放置点落位，后续可继续按攻略截图微调。
- 2026-06-30 追加修正 4：用户确认笔的最终目标不是脸部，而是左大腿根部；`2_24_0` / `2_26_0` 手动热区移到左大腿根部。药膏改为 `visibleWhen:["teressePantyPulled"]`，未完成“內褲向右拉”前不再显示药膏热区。

注意：这是一个“有证据的局部覆盖”，不是通用猜坐标。后续如果要批量修其它类似“点击画面道具本体”的点，需要优先找游戏里道具图标/托盘物件与互动 point 的绑定关系；不能把所有 `*_follow` 都当成道具本体。

## 2026-06-30 通用 drag 热区从点击改为拖动触发

用户反馈：`illust_dating2` / 白日梦兔女郎·墨菲亚里，明明是拖动点的位置，现在网页只是点击就触发。

排查结论：

- 数据层是对的。`data/dating_actions.json` 中墨菲亚多个点已是 `kind:"drag"`，例如：
  - 阶段1：`1_7_0`、`1_12_0`、`1_19_0`
  - 阶段2：`2_6_0`、`2_11_0`、`2_22_0`
  - 阶段3：`3_3_0`、`3_6_0`、`3_11_0`
- `data/dating_hotzones.json` 的 source 也能看到 `point*_drag*`。
- 问题在 `dating.html` 的通用热区层：除 longPress / gyro 特殊分支外，普通 action 都走 `onclick -> playPrefabAction()`，导致 `drag` 被简化成点击。

修复：

- `renderHotzones()` 新增普通 `action.kind === "drag"` 分支：
  - `pointerdown` 记录起点并 setPointerCapture；
  - `pointermove` 距离超过阈值后触发 `playPrefabAction()`；
  - `pointerup` / `pointercancel` 未达阈值则取消，不播放；
  - `click` 被 preventDefault，避免拖动后再触发一次点击。
- 新增 `activePrefabDrag` 状态和 `beginPrefabDrag()` / `movePrefabDrag()` / `cancelPrefabDrag()`。
- 切换角色、切换阶段、重绘热区时会取消未完成的 drag。

边界：

- 当前只判断拖动距离，不判断方向、路径或持续时间；但已解决“drag 只点一下就触发”的核心问题。
- longPress drag 和 gyro drag 仍走各自原有分支，不受本次普通 drag 修改影响。

## 2026-06-30 尊爵服装语音映射复现排查

目标：复现此前 `illust_dating18` / 莎拉跑通的 FMOD `SoundMaster GUID -> event path`
流程，继续补 4 个尊爵服装的动作型互动语音映射。

### 当前 4 个目标

来自 `data/dating_charid_map.json`：

- `illust_dating7`：`char000296`，悠丝缇亚 / 仲夏夜之梦·尊爵。
- `illust_dating9`：`char001197`，泰瑞丝 / 奶牛比基尼·尊爵。
- `illust_dating12`：`char061492`，杰尼斯 / 神秘兔女郎·尊爵。
- `illust_dating14`：`char003892`，黎维塔 / 享乐主义·尊爵。

### 已确认事实

- `data/dating_audio.json` 里这 4 个角色已经有 FEV/FSB 解析出的 sample/event 数据，但
  `actions` 仍为空或不完整。也就是说 OGG 与 bank 不是问题，缺的是“Spine 动画名 -> FMOD event GUID/path”
  这一层。
- 本地已拉到当前 `SoundMaster`：
  `local_device_cache/bd2_current_20260624/soundmaster_probe/Master.strings`。
- `Master.strings` 是 `RIFF/FEV`：

  ```text
  FMT
  LIST/PROJ
    BNKI
    多个空 LIST
    STDT
  ```

- `STDT` 不是普通完整路径列表，而是 FMOD 压缩字符串/索引结构。直接搜
  `Char001197_Int_mix1_12_1_KR` 搜不到，但能看到分片：
  `Interaction/Char001197_Int_`、`Mix`、`1_`、`12_1_`、`JP`、`KR`。
- 对目标角色的 `STDT` 分片扫描结果：
  - `char001197`：存在 `Mix1_12_1`、`Mix1_24_1`、`Mix2_10_1`、`Mix3_0_1`、
    `motion1_37` 等动作型片段。
  - `char061492`：存在 `Mix3_30_1`、`Mix4_0_1`、`motion1_32` 等动作型片段。
  - `char003892`：存在 `Mix1_21_1`、`Mix2_11_1`、`Mix3_8_1`、`motion1_22` 等动作型片段。
  - `char000296`：当前扫描只看到 `Special1..Special7` 等情绪/特殊池片段，暂未看到明确
    `mix...` 动作片段；它可能仍需要表映射或另一路特殊规则。

### 已排除的错误捷径

- 不能再使用 `local_device_cache/.../voice_event_paths/Char*.tsv` 里当前的空 TSV 作为“没有路径”的证据。
  这些 TSV 是旧 standalone dump 失败后的空结果。
- 旧的 ARM64 standalone 工具 `dump_fmod_strings_CharXXXXXX` 仍然失败：

  ```text
  FMOD create failed: 28
  ```

  失败发生在 `FMOD_Studio_System_Create`，还没加载 `Master.strings`。
- 2026-06-30 复现失败的真正原因已查清：不是设备、不是资源、也不是 `libdumpfmod.so` 本身不可用，
  而是 Java wrapper 写错了 native 参数。
  - `libdumpfmod.so` 的 `Java_bd2_DumpFmod_run` 只把 JNI 第三个参数传给内部 `run()`。
  - 反汇编确认内部 `run()` 开头会调用 `FMOD_Android_JNI_Init(JavaVM*, context)`。
  - 之前 wrapper 声明 `run(String filter)` 并传入 `"Char000396"` / `"event:/"`，导致 native 把
    Java 字符串当 Android `Context` 用，`FMOD.init OK` 后立刻 `EXIT:139`。
  - 修正为 `run(Object context)`，传 `ActivityThread.systemMain().getSystemContext()` 后，
    dump 正常输出：`FMOD JNI init: 0`、`FMOD version accepted: 0x00020312`、
    `string count: 57393 result=0`。
- 不能按 FEV `EVNT` 顺序或 SoundMaster 路径分片顺序猜映射。用莎拉现有成功数据校准后确认：
  - FEV `EVNT` 顺序按 GUID 字节序排列。
  - Master GUID 数组按 GUID 前 4 字节小端数值排列。
  - 两者都不是 `Interaction/Char000396_Int_...` 路径的字典序。
  - 因此“按顺序把 mix 名塞给 FEV event”会产生错误语音，禁止作为正式方案。

### 当前正确突破口

仍然应该拿到正式的 `GUID<TAB>event path` 表，再交给 `tools/extract_dating_audio.py`：

1. 首选还是 `app_process + dumpfmod.jar + libdumpfmod.so`，不需要 Frida：

   ```bash
   CLASSPATH=/data/local/tmp/bd2sound/dumpfmod.jar:<游戏base.apk> \
   LD_LIBRARY_PATH=/data/local/tmp/bd2sound \
   app_process /data/local/tmp bd2.DumpFmod
   ```

   Java wrapper 必须传 Android `Context` 给 native `run(context)`。
2. Frida 仍可作为备选，但本轮 `frida -U -p <pid>` 返回
   `unable to connect to remote frida-server: closed`，不要在这条路上反复空耗。
3. 若设备端完全不可用，再静态逆 `STDT` 的节点结构；目前只确认了 GUID 数组排序规则，还没有确认
   path leaf 到 GUID index 的链接字段，不能用作生成正式映射。

### 本轮产物与结果

- 已导出全量 SoundMaster 事件路径：
  `local_device_cache/bd2_current_20260624/all-fmod-event-paths.tsv`（临时文件，不进 git）。
- 已拆出目标角色路径：
  `local_device_cache/bd2_current_20260624/voice_event_paths/Char000296.tsv`
  / `Char001197.tsv` / `Char061492.tsv` / `Char003892.tsv` / `Char000396.tsv`。
- `tools/extract_dating_audio.py` 修复动作识别兼容：SoundMaster 中部分角色使用
  `Mix...` / `Motion...` 首字母大写，前端 Spine 动画名则是小写 `mix...` / `motion...`。
  工具现在只规范动作前缀大小写，不改情绪事件名。
- 重建 `data/dating_audio.json` 后结果：

  | dating | char | KR events | action mappings | samples | missing OGG |
  |---|---|---:|---:|---:|---:|
  | `illust_dating7` | `char000296` | 19 | 0 | 48 | 0 |
  | `illust_dating9` | `char001197` | 33 | 21 | 49 | 0 |
  | `illust_dating12` | `char061492` | 27 | 14 | 40 | 0 |
  | `illust_dating14` | `char003892` | 28 | 10 | 64 | 0 |

`illust_dating7 / char000296` 的 SoundMaster interaction voice 只有情绪/特殊池（如 `Special*`），
没有 `Mix...` / `Motion...` 动作型 voice event；它不能按莎拉的动作名自动接入，后续需要另找
表映射或确认是否只应使用情绪/特殊池。

额外核对 `data/dating_actions.json`：

- `illust_dating9`：21 个 audio action 全部能在 action 数据中找到同名 `mix/motion`。
- `illust_dating14`：10 个 audio action 全部能在 action 数据中找到同名 `mix/motion`。
- `illust_dating12`：14 个 audio action 中 13 个能在 action 数据中找到；`motion1_32` 当前
  没有直接触发点，先保留在 audio manifest 中但不会被现有热区自动触发。

## 2026-07-01 更正：dating7 / char000296 的动作音频不在角色 voice bank，而在全局 Visual Interaction SFX

前面“`char000296` 没有动作型片段”的结论只对 `interaction_char000296.bytes`
这个角色 interaction voice bank 成立，不能外推到全部音频资源。重新核对后确认：

- `interaction_char000296.bytes` 只含 `Char000296_Int_*` 情绪/特殊池事件，适合做 voice pool，
  但不包含 `mix1_*` / `mix2_*` 动作事件。
- `common-sound_assets_sound/visual_interaction_sfx.bytes` 才包含动作 SFX 事件：
  `event:/Cinematic/Visual_Novel/Char000296/Interaction/idle1/mix1_*`、
  `idle2/mix2_*`、以及 `motion1_32`。
- 用 `local_device_cache/bd2_current_20260624/all-fmod-event-paths.tsv` 的
  `GUID<TAB>event path` 反查 `visual_interaction_sfx` 的 FEV 图，命中
  `Char000296` 互动事件 75 个。这个结论来自 bank 内 event GUID，不是按名字猜。

本次生成：

```text
datingId        illust_dating7
charId          char000296
SFX bank        common-sound_assets_sound/visual_interaction_sfx.bytes
bank GUID       81f82b5b3c2b4045a860d128fd9f7cf5
bank SHA256     84c5bf041488e26c32f2c7c679c718685839ecce8aab018918428d69af7efb97
FSB SHA256      6a1c2c49a529f95a0ec396437959df31cafc7d934b61a4d86b9bdf202d314fda
events          75
triggers        411
samples         117
action mappings 76
```

产物：

- `data/dating_audio.json`
  - `characters.illust_dating7.sfx.events`：75 个 FMOD event 的真实 timeline。
  - `characters.illust_dating7.sfx.actions`：76 个 Spine 动画名映射。
  - `mix1_32_1` 在 SoundMaster/FEV 中没有同名事件，但同点存在 `motion1_32`，因此显式
    alias 为 `mix1_32_1 -> motion1_32`。
- `audio/dating/illust_dating7/sfx/`
  - 117 个 OGG，`ffprobe` 全部可读。

验证：

```text
data/dating_actions.json 需要的 illust_dating7 动画名：76 个
data/dating_audio.json 中 sfx action mappings：76 个
缺失映射：0
JSON 校验：OK
```

这条路线和情绪型 `SpineInteractionPointTable` 不是一回事：dating7 当前应按动作型 SFX
管线接入点击/拖动动作音频；角色 voice bank 中的 `Char000296_Int_*` 仍可保留，但不能拿它
直接推导动作点映射。

## 2026-07-01 音频防串审计门禁 + 首批 Visual Interaction SFX 扩展

### 防串规则固化

这轮开始新增硬门禁，避免再次出现“菜单编号 / gid / charId / event path”混用导致语音乱配：

1. 页面角色主键固定为 `illust_datingN -> charId`，只从 `data/dating_charid_map.json` 读取。
2. FMOD event path 必须含同一个 `CharXXXXXX`，否则不能写入 `data/dating_audio.json`。
3. `SpineInteractionPointTable.gid` 只能通过表内 charId 反查，不能当 `datingN`。
4. SFX 事件不能只看 SoundMaster path 是否存在，还必须检查 FMOD timeline 是否至少引用一个有效 FSB stream。
   空 wave GUID 不算可播放音频。

新增工具：

- `tools/audit_dating_audio_integrity.py`
  - 输入：
    - `data/dating_charid_map.json`
    - `data/dating_actions.json`
    - `data/dating_audio.json`
    - `data/dating_interaction_tables.json`
    - `data/dating_interaction_meta.json`
    - `local_device_cache/bd2_current_20260624/all-fmod-event-paths.tsv`
    - `local_device_cache/bd2_current_20260624/visual_interaction_sfx/visual_interaction_sfx.bank`
  - 输出：
    - `local_device_cache/dating_audio_integrity_audit.json`
    - `local_device_cache/dating_audio_integrity_audit.md`

本轮审计摘要：

```text
charactersInMap       19
manifestPathIssues    0
pointTableCharacters  14
gidNotDatingNumber    8
safeVisualSfx         5
needsAliasOrReview    7
needsOtherBank        3
missingActionTable    4
```

`gidNotDatingNumber=8` 是关键提醒：后续任何批处理都不能把 gid 直接当页面编号。

### `extract_dating_sfx.py` 容错修正

生成 `illust_dating2` 时发现：

```text
event:/Cinematic/Visual_Novel/Char003402/Interaction/idle1/mix1_18_1
```

其中一个 timeline choice 指向全 0 wave GUID。该 event 仍有其它有效 sample，因此正确处理是：

- 跳过空 wave GUID。
- 保留同一 event 中的有效 sample。
- 如果整条 event 没有任何有效 trigger，再不写入 manifest。

`tools/extract_dating_sfx.py` 已按这个规则处理。

另外，当前本机 `ffmpeg` 没有 `libvorbis` encoder，工具会 fallback 到原生 `vorbis`。命令输出里会先看到
`Unknown encoder 'libvorbis'`，但最终是否成功以 `ffprobe` 检查 OGG 为准。

### 本批接入结果

在 `visual_interaction_sfx.bytes` 中先接入高确定性、动作需求全覆盖的四个角色：

| dating | charId | SFX events | samples | required action missing | path char mismatch | bad OGG |
|---|---|---:|---:|---:|---:|---:|
| `illust_dating2` | `char003402` | 81 | 57 | 0 | 0 | 0 |
| `illust_dating3` | `char003203` | 70 | 63 | 0 | 0 | 0 |
| `illust_dating4` | `char001106` | 82 | 65 | 0 | 0 | 0 |
| `illust_dating9` | `char001197` | 128 | 140 | 0 | 0 | 0 |

产物：

- `data/dating_audio.json`
  - 新增/更新 `characters.illust_dating2.sfx`
  - 新增/更新 `characters.illust_dating3.sfx`
  - 新增/更新 `characters.illust_dating4.sfx`
  - 新增/更新 `characters.illust_dating9.sfx`
- 新增 OGG：
  - `audio/dating/illust_dating2/sfx/`：57 个
  - `audio/dating/illust_dating3/sfx/`：63 个
  - `audio/dating/illust_dating4/sfx/`：65 个
  - `audio/dating/illust_dating9/sfx/`：140 个

验证命令结论：

```text
illust_dating2 char003402 needed 79  sfxActions 81  missing 0  events 81   files 57   badOgg 0 wrongPath 0
illust_dating3 char003203 needed 67  sfxActions 70  missing 0  events 70   files 63   badOgg 0 wrongPath 0
illust_dating4 char001106 needed 77  sfxActions 82  missing 0  events 82   files 65   badOgg 0 wrongPath 0
illust_dating9 char001197 needed 123 sfxActions 128 missing 0  events 128  files 140  badOgg 0 wrongPath 0
```

### 下一步

1. `illust_dating5/6/8/10/11/12` 进入 alias/review 阶段，不能盲补。
2. `illust_dating13/14/19` 需要按 GUID 定位另一个 SFX bank；SoundMaster 有 path，但不在
   `visual_interaction_sfx`。
3. `illust_dating15/16/17/18` 当前缺 `data/dating_actions.json` 动作表，先补动作/热区再谈完整 SFX。

## 2026-07-01 继续：alias/review 组 SFX 接入

### alias 原则

本轮只接受两类 alias：

1. 同点 `mixN_x_1 -> motionN_x`，且目标 `motionN_x` 在同角色 FMOD event path 中存在并有有效 sample。
2. 同点 sibling fallback，例如同一个 point 的 `mix3_2_2 -> mix3_2_1`，且目标 event 有有效 sample。

明确禁止：

- 把 `mix*_1_1` 这类初始/循环动作 alias 到 `mix*_1_end`。这会把“结束音”提前播放，语义风险高。
- 多候选动作强选一个，例如同一个 `mix2_0_1` 同时关联 `motion2_1` / `motion2_2`。

### 完整补齐组

| dating | charId | alias | SFX events | samples | required missing | bad OGG |
|---|---|---|---:|---:|---:|---:|
| `illust_dating5` | `char060802` | `mix1_18_1=motion1_18` | 73 | 65 | 0 | 0 |
| `illust_dating8` | `char001006` | `mix1_35_1=motion1_35`; `mix2_1_1=motion2_1` | 69 | 75 | 0 | 0 |
| `illust_dating10` | `char066403` | `mix1_15_2=mix1_15_1`; `mix1_26_1=motion1_26`; `mix2_2_1=motion2_2` | 113 | 87 | 0 | 0 |

### 部分覆盖组

| dating | charId | alias | SFX events | samples | remaining missing | bad OGG |
|---|---|---|---:|---:|---|---:|
| `illust_dating6` | `char067603` | `mix2_3_1=motion2_3`; `mix3_3_1=motion3_3`; `mix5_2_1=motion5_2` | 59 | 83 | `mix2_1_1`, `mix3_1_1`, `mix4_1_1`, `mix5_1_1` | 0 |
| `illust_dating11` | `char000706` | `mix1_9_1=motion1_9`; `mix3_0_1=motion3_0`; `mix4_0_1=montion4_0` | 67 | 69 | `mix1_0_1`, `mix2_0_1` | 0 |
| `illust_dating12` | `char061492` | `mix2_1_1=motion2_1`; `mix3_2_2=mix3_2_1` | 128 | 145 | `mix1_0_1`, `mix1_35_1`, `mix2_0_1`, `mix3_0_1` | 0 |

`montion4_0` 是 FMOD event path 里的拼写，保留原样；manifest action alias 会从页面动作名
`mix4_0_1` 指向这个真实 event 名。

### 总体验证

截至本节，已有 SFX 的角色：

```text
illust_dating1   char003303 need= 86 actions= 88 missing= 0 events= 88 files= 66 bad=0 wrongPath=0
illust_dating2   char003402 need= 79 actions= 81 missing= 0 events= 81 files= 57 bad=0 wrongPath=0
illust_dating3   char003203 need= 67 actions= 70 missing= 0 events= 70 files= 63 bad=0 wrongPath=0
illust_dating4   char001106 need= 77 actions= 82 missing= 0 events= 82 files= 65 bad=0 wrongPath=0
illust_dating5   char060802 need= 72 actions= 74 missing= 0 events= 73 files= 65 bad=0 wrongPath=0
illust_dating6   char067603 need= 61 actions= 62 missing= 4 events= 59 files= 83 bad=0 wrongPath=0
illust_dating7   char000296 need= 75 actions= 76 missing= 0 events= 75 files=117 bad=0 wrongPath=0
illust_dating8   char001006 need= 64 actions= 71 missing= 0 events= 69 files= 75 bad=0 wrongPath=0
illust_dating9   char001197 need=123 actions=128 missing= 0 events=128 files=140 bad=0 wrongPath=0
illust_dating10  char066403 need=112 actions=116 missing= 0 events=113 files= 87 bad=0 wrongPath=0
illust_dating11  char000706 need= 63 actions= 70 missing= 2 events= 67 files= 69 bad=0 wrongPath=0
illust_dating12  char061492 need=129 actions=130 missing= 4 events=128 files=145 bad=0 wrongPath=0
illust_dating18  char000396 need=  0 actions=117 missing= 0 events=112 files=127 bad=0 wrongPath=0
```

`wrongPath=0` 表示没有发现 SFX event path 引用到其它角色的 `CharXXXXXX`。sample 名中仍可能出现公共音效或其它角色名，
这是 FMOD sample 复用，不作为串角色判断；串角色只看 event path 和 manifest charId。
