# Codex 交接摘要

> 这份文件只记录当前仍有用的改动结论、坑位和下一步。  
> 详细流水/失败尝试已经从正文移除，避免继续误导；需要追溯细节时看 git 历史。  
> **当前完整事实以 `DATING_PIPELINE.md` 为准。**

---

## 0. 当前一句话结论

`dating.html` 的「有缘之客」已经进入数据化阶段：

- 19 个菜单编号与 `charId` 的权威映射已固定在 `data/dating_charid_map.json`。
- Spine 立绘资源 19/19 已可用。
- 热区/动作 JSON 已覆盖 `illust_dating1-17` 与 `illust_dating19`；`illust_dating18` 莎拉保留前端手写特殊逻辑。
- 语音素材 19/19 已登记；心契点→情绪语音母表覆盖 14 个心契角色。
- 动作 SFX 已大规模接入；仍有少量 `mix*_0_1` 阶段入口类缺口，不能硬 alias。
- 第三层 `mix/special` 动作语音仍有残留，需要设备侧继续补抽。

---

## 1. 必须遵守的前提

历史上最大事故就是编码/身份前提错，后续所有映射都会白搭。之后任何新增或修复都必须先过这几条：

1. `datingN -> charId` 只读 `data/dating_charid_map.json`。
2. FMOD event path 必须包含同一个 `CharXXXXXX`，否则不能写入正式数据。
3. `SpineInteractionPointTable.gid` **不是**菜单编号，只能通过 `charId` 反查。
4. sample 名不是防串依据；FMOD 会复用公共 sample，甚至 sample 名里可能出现其它角色编号。
5. `extract_dating_sfx.py` 会直接写 `data/dating_audio.json`，不要并行跑多个角色写同一个 JSON。
6. 别把 `mix*_0_1`、`*_end`、多候选动作硬 alias 成普通点位音效。
7. 莎拉 `dating18` 有手写特殊逻辑，新抽 prefab 与手写计数不完全一致，不能直接外部 JSON 覆盖。

---

## 2. 权威角色映射

| dating | charId | 当前身份/备注 |
|---|---|---|
| 1 | `char003303` | 内布利斯 |
| 2 | `char003402` | 墨菲亚 |
| 3 | `char003203` | 罗安 |
| 4 | `char001106` | 保健社泰瑞丝 |
| 5 | `char060802` | 代号O 爱丽洁 |
| 6 | `char067603` | 威廉明娜 |
| 7 | `char000296` | 悠丝缇亚尊爵 |
| 8 | `char001006` | 席比雅 |
| 9 | `char001197` | 奶牛泰瑞丝尊爵 |
| 10 | `char066403` | 安洁莉卡 |
| 11 | `char000706` | 伊柯利普斯 |
| 12 | `char061492` | 杰尼斯尊爵 |
| 13 | `char004102` | 提尔 |
| 14 | `char003892` | 黎维塔尊爵 |
| 15 | `char067004` | 班塔纳 |
| 16 | `char003604` | 奥利维耶；有 `mix` 动作语音线索 |
| 17 | `char004202` | 帕莱特 |
| 18 | `char000396` | 莎拉尊爵/赌场；手写特殊逻辑 |
| 19 | `char067104` | 格兰希特 |

---

## 3. 当前数据覆盖

### 3.1 热区与动作

- `data/dating_hotzones.json` / `data/dating_actions.json`
  - 已覆盖：`illust_dating1-17`、`illust_dating19`
  - 未外部化：`illust_dating18`
- `dating18` 莎拉仍走 `dating.html` 内的手写牌局/长按/gyro/阶段逻辑；不要直接用新抽 prefab 覆盖。

### 3.2 音频

`data/dating_audio.json` 当前包含 19 个角色节点。

| 类别 | 当前状态 |
|---|---|
| 情绪 voice bank | 19/19 有素材 |
| 心契点→语音母表 | 14 个心契角色；尊爵/莎拉非此类 |
| 动作 SFX | 已批量接入；`dating1` 的 SFX 仍标记 disabled 作为历史止血 |
| mix 动作语音 | 已确认只有 `dating16`、`dating18` 是重点；`dating18` 已做，`dating16` 待做 |

### 3.3 SFX bank 分组

当前证据里，动作 SFX 主要来自两类 bank：

- `visual_interaction_sfx`
  - 早期/部分角色使用。
  - 已接入包括：2/3/4/5/6/7/8/9/10/11/12。
- `Visual_Novel_SFX`
  - 当前包中覆盖 13/14/15/16/17/18/19。
  - 当前确认：

```text
common-sound_assets_sound/visual_novel_sfx.bytes
bundleName=ae2d0048197fd9af691d991454050be2
hash=67087266740ce88580ec3bf3f84b8ff6
bankGuid=bcbf2950f645bb4bbd33ad593e44c248
```

---

## 4. 已修正/已推翻的历史误区

这些内容过去曾经写进流水或代码里，现在不要再沿用。

### 4.1 不能用 `gid == datingN`

`SpineInteractionPointTable.gid` 是母表组号，不是菜单编号。  
例如：

```text
dating13 = char004102 = gid10
dating19 = char067104 = gid14
dating14 = char003892 = 非心契，无 point table
```

### 4.2 Nebris SFX 误判

早期把 Nebris 的 SFX 自动接入后，用户听到类似战斗/机关枪的声音。后来确认：

- voice 没问题；
- 误感主要来自 SFX 自动播放链；
- 目前 `illust_dating1.sfx.disabled=true` 是刻意止血。

后续不要把“event path 看起来对”直接等价为“这个 SFX 就应该播放”。至少要同时看 timeline、sample、实际语义。

### 4.3 不要再按 sample 名判断串号

SFX sample 名中出现其它角色编号不一定是错，例如公共池复用。  
串号只看 FMOD event path 是否包含当前角色 `CharXXXXXX`。

### 4.4 旧结论 “13/14/19 不在 SFX bank” 已过时

真实结论：它们不在早期 `visual_interaction_sfx`，但在当前 `Visual_Novel_SFX`。

### 4.5 15/16/17 不是缺 prefab

当前已从 `common-char-datingillust_assets_all.bundle` 抽出 15/16/17 的热区和动作，并写入外部 JSON。  
旧的“先补 15/16/17/18 动作表”已经过时；现在只剩 `18` 暂不外部化。

### 4.6 不要直接覆盖莎拉

`dating18` 是特殊状态机：长按、gyro、牌局、阶段跳转、特殊热区都有手写逻辑。  
新抽 prefab 计数与当前手写逻辑不完全一致，所以现在策略是：

- 保留手写逻辑；
- 单独审计；
- 不用通用 JSON 直接覆盖。

---

## 5. 当前重要实现

### 5.1 数据化加载

前端优先读取：

- `data/dating_hotzones.json`
- `data/dating_actions.json`
- `data/dating_audio.json`

旧的 `PREFAB_HOTZONES` / `PREFAB_POINT_ACTIONS` 只作为兜底，尤其保留给莎拉等特殊逻辑。

### 5.2 点→语音兜底

心契点→语音已改成：

1. 先按完整 key 精确查；
2. 查不到时按同 `stage_id_*` 的变体兜底。

原因：母表语音本质按 `(stage,id)`，tool 只是前端点位变体；历史上 toolId 键方案不一致导致热区点击没声音。

### 5.3 热区命中层级

`dating.html` 的热区坐标和动作类型来自 prefab 抽取数据，但浏览器最终命中仍由 DOM 叠放顺序决定。
2026-07-02 用 `illust_dating2` 墨菲亚复核时确认：同一阶段/工具下存在大范围 `InteractionZone` 与多个小热区重叠，旧逻辑按 `pointId` 升序追加 DOM，导致后追加的大拖拽区抢走小热区事件。例如 stage1 的 `1_19_0` 会压过 `1_6_0`、`1_7_0`、`1_11_0`、`1_12_0`，stage2 的 `2_22_0` 也会压过小热区。

当前修法只调整前端命中层级，不改抽取坐标、不改拖拽距离阈值：渲染热区前按屏幕面积排序，大热区先铺，小热区后铺；面积接近时拖拽先铺、触摸后铺。浏览器 `elementFromPoint` 复测确认，大兜底拖拽区不再覆盖这些小热区。全量静态审计里，严重重叠对中“大热区压小热区”的情况为 `0/1301`。

注意边界：小热区之间仍可能互相重叠，这不是本次修复目标。后续如果要继续细修，必须按角色/阶段结合游戏行为验证，不能直接扩大规则或改坐标。

### 5.4 SFX alias 规则

只允许：

- `mixN_x_1 -> motionN_x`，且目标 event 存在并有有效 sample；
- 同点 sibling fallback，例如 `mix3_2_2 -> mix3_2_1`，且目标 event 有效。

禁止：

- `mix*_1_1 -> *_end`
- 多候选强选一个
- 跨角色/跨点位猜测

---

## 5.5 【2026-07-02】热区动画"播错/时长不对"= 播放语义，不是资源

用户反馈拖拽热区播放动画不对、播放时长也不对，最初怀疑资源错或匹配错；静态分析和浏览器复测后结论是：
资源与 `(group,id,tool)` 匹配基本正确，真正的问题是前端把 `mix: [...]` 当成一次触发的顺序串播。

### ✅ 拖拽已修复

最新事实以 `DATING_PIPELINE.md` 的「2026-07-02 拖拽语义与跟手复现」为准：

- drag 是两阶段手势：`mix_1`=拖住/拉扯，`mix_2`=松手回弹。
- drag mix 走 track 1，idle/motion 留在 track 0。
- begin-drag 路径是 `SetSpineAnimationExternal(name, track=1, loop=false, onComplete)`，单次播放后停在末帧。
- `loop=true` 属于拖到 `_destinations` 后播放 `_playMotionNames[i]` 的另一条路径，不是普通拖住语义。
- 前端已实现点位骨骼跟手：用现有热区 `source` 找同名 SkeletonUtilityBone，拖住期间把点位骨骼钉到手指；松手/成功/取消时复位。
- 2026-07-02 追加修正：点位骨骼是 IK target，覆盖 target 后必须再跑一次完整 `updateWorldTransform`，否则被 IK 控制的丝袜/腿部骨骼不会同帧重算。dating2 墨菲亚三阶段 3/11 已经用浏览器实测有效。

### 🟡 本轮初步落地：touch 多段/随机

- `extract_dating_actions.py` 已补抽 `IsPlayRandomMixAnim`、`ContinuousClickResetTime`、`PlayMixAnimNameWhenActionStop`，
  输出为 `randomMix`、`clickReset`、`stopMix`。
- `dating.html` 已改为 touch 单次点击只播一段 mix；`clickMax` 在重置窗口内递进，停止连点后播 `stopMix`；
  `randomMix` 随机挑一段播放。
- 数据审计确认：除新增字段外，`data/dating_actions.json` 原有动作数据完全一致；新增字段覆盖 283 个 action。
- 待做：浏览器逐角色抽样复核手感后，再把 `DATING_PIPELINE.md` 里的 touch 项标成完成。

---

## 5.5.1 原始诊断(留档)

**资源和 (group,id,tool) 匹配基本没错**——`data/dating_actions.json` 里引用的动画名
99% 能在对应 skel 里找到（缺的 ~40 个主要是已知 `mixN_0_1` 阶段入口）。
**错的是前端把 `mix: [...]` 数组当"一次触发顺序串播"**（`prefabActionSequence` 返回
`[...mix, ...motions]` 全部 addAnimation 链播）。游戏里 `SpineInteractionPoint`
（il2cpp dump TypeDefIndex 5244，韩文 Header 注释可读）的真实语义按类型分三种：

1. **touch + ClickMaxCount=N（约 260 点）**：mix 是"逐次点击递进"——第 k 次点击播
   `mix[k-1]`，1 秒内（`ContinuousClickResetTime`）连点满 N 次才播 motion/进下一阶段，
   中途停下播 `PlayMixAnimNameWhenActionStop`（即 `mixN_x_end`）。prefab 里
   clickMax ≈ nMix 或 nMix+1 的强规律证实这一点。前端现在一次点击串播全部
   （最坏 dating9 `2_16_10` 一击串播 24 段）→ 动画错 + 时长爆炸。
   前端 `prepareActionPlayback` 的 clickMax 门控只对带 nextStage/setFlag/progressiveMix
   的动作生效，外部 JSON 里只有 1 条命中；提取器根本没输出 `progressiveMix`。
2. **touch + IsPlayRandomMixAnim=1（约 18 点）**：多段 mix 随机挑一段播。提取器没抽这个字段。
3. **drag（152 点，几乎都恰好 2 段 mix）**：两阶段手势——`mixN_x_1`=拖住/拉扯
   （begin drag，`_follow` 热区跟随骨骼），`mixN_x_2`=松手回弹（end drag）。
   铁证：同类点的 LongPressSettingData 里 `fail=mixN_x_2`（提前松手→回弹）、
   `success=mixN_x_long`。前端在越过 32-96px 阈值瞬间把 `_1+_2` 连播 → 没有"拖住"
   阶段，观感动画错、时长错。另有 29 个拖拽点带 `_destinations`（拖到目的地才算成功，
   `OnDragEvent(point, bool, int)` 回调目的地索引），前端完全没实现。

**提取器缺口**（`extract_dating_actions.py` 没抽的决定性字段）：
`IsPlayRandomMixAnim`、`ContinuousClickResetTime`、`PlayMixAnimNameWhenActionStop`、
`_destinations`。修复应从补抽这些字段开始，再改 `dating.html` 的播放状态机
（点击递进/随机单段/拖拽两阶段），不要动热区坐标和 key 方案。

运行态确证（可选）：连 S25 用 frida hook Spine `AnimationState.SetAnimation`，
在游戏里做一次拖拽/连点对照实际动画序列；本次设备不在线，未做。

---

## 6. 仍需继续的工作

### 6.1 补第三层 mix/special 互动语音

母表里还有一些 `Char*_Int_Mix*` / `Special*` 类语音缺口。  
这不是 SFX，也不是普通情绪 voice，而是音频模型第③层。

当前 `DATING_PIPELINE.md` 里记录的残留：

```text
3=1, 5=3, 6=7, 8=7, 10=1, 11=2, 13=9,
15=12, 16=22, 17=20, 19=10
```

原则：

- 有证据在角色自己 `interaction_charXXXXXX` bank 的，重跑补抽；
- 不在自己 bank 的，先用 event GUID 反查宿主 bank；
- 不要猜。

### 6.2 dating16 的 mix 动作语音

`dating16 / char003604` 有 30 个 mix 动作语音线索，应该按莎拉那条管线继续做。  
做之前仍然先跑 charId/event path 审计。

### 6.3 SFX `mix*_0_1` 缺口

多个角色仍缺 `mixN_0_1`。当前判断更像阶段入口/默认动作事件。  
没有运行态证据前不要硬 alias 到其它普通点位。

### 6.4 dating18 外部化

莎拉外部化要单独立项。  
通用脚本能抽出数据，但不能直接替换现有手写逻辑。

---

## 7. 常用工具

| 工具 | 作用 |
|---|---|
| `tools/extract_dating_spine.py` | 从 dating bundle 抽 Spine |
| `tools/extract_dating_hotzones.py` | 从 prefab 抽 skeleton-space 热区 |
| `tools/extract_dating_actions.py` | 从 prefab 抽 mix/gyro/touch/action |
| `tools/extract_dating_audio.py` | 抽 interaction voice |
| `tools/extract_dating_sfx.py` | 抽动作 SFX |
| `tools/audit_dating_audio_integrity.py` | 防串审计 |
| `tools/apply_dating_interaction_voice_actions.py` | 落地心契点→语音 |
| `tools/il2cpp-re/capture_interaction_agent.ts` | frida 抓 `SpineInteractionPointTable` |

---

## 8. 最近提交脉络

```text
a7fd5b6 Add dating 15 16 17 interaction data and SFX
f0c080a Add visual novel SFX for dating 13 14 19
bdc7a6a Add dating SFX audit and batch mappings
aa0b16d 部分尊爵互动的映射抓取
```

如需看更早的详细流水，用 git 历史查看本文件旧版本；当前文件刻意只保留可执行的交接信息。
