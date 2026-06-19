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
