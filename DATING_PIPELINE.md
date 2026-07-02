# 有缘之客(BD2 Dating)复现 · 完整流程与状态

> 单一事实来源(single source of truth)。目标:在 `dating.html` 里复现游戏「有缘之客」互动
> = **立绘(Spine) + 交互点(热区/动作) + 音频(语音/音效)** 三大块。
> 工作量很大,按下面四个阶段 + 三层音频分层推进,逐角色补全。

---

## 0. 一句话总览

```
资源在游戏里 → 抽出来 → 前端 dating.html 组合渲染
             ├─ A 资源获取(bundle/表/bank,从设备缓存或官方CDN)
             ├─ B 资源组合(Spine 落 upstream/自托管仓,前端加载)
             ├─ C 交互复现(热区 hotzones + 动作 actions)
             └─ D 音频复现(三层:情绪voice / 动作SFX / mix动作语音)
```

---

## 1. 角色总表(19 个,权威映射)

菜单#(`illust_datingN`)↔ charId 已定死,见 `data/dating_charid_map.json`。
**注意:菜单顺序 ≠ 心契列表顺序 ≠ charId 顺序**,历史上错配过,以此表为准。

| # | 名字 | charId | 类别 | mix动作语音 |
|---|---|---|---|---|
| 1 | 新进员工·内布利斯 | char003303 | 心契 | — |
| 2 | 白日梦兔女郎·墨菲亚 | char003402 | 心契 | — |
| 3 | 名人兔女郎·罗安 | char003203 | 心契 | — |
| 4 | 保健·泰瑞丝 | char001106 | 心契 | — |
| 5 | 代号O·爱丽洁 | char060802 | 心契 | — |
| 6 | 水上女王·威廉明娜 | char067603 | 心契 | — |
| 7 | 仲夏夜之梦·悠丝缇亚【尊爵】 | char000296 | 尊爵皮肤 | — |
| 8 | 比基尼特工·席比雅 | char001006 | 心契 | — |
| 9 | 奶牛比基尼·泰瑞丝【尊爵】 | char001197 | 尊爵皮肤 | — |
| 10 | 霓虹救星·安洁莉卡 | char066403 | 心契 | — |
| 11 | 恶梦兔女郎·伊柯利普斯 | char000706 | 心契 | — |
| 12 | 神秘兔女郎·杰尼斯【尊爵】 | char061492 | 尊爵皮肤 | — |
| 13 | 兔女郎·提尔 | char004102 | 心契 | — |
| 14 | 享乐主义·黎维塔【尊爵】 | char003892 | 尊爵皮肤 | — |
| 15 | 温泉修行者·班塔纳 | char067004 | 心契 | — |
| 16 | 传奇退役·奥利维耶 | char003604 | 心契 | **★有(30事件)** |
| 17 | 奇迹紫罗兰·帕莱特 | char004202 | 心契 | — |
| 18 | 致胜王牌·莎拉 | char000396 | 尊爵(赌场) | **★有(48事件)** |
| 19 | 战地医疗兵·格兰希特 | char067104 | 心契 | — |

- **charId = illust_inven_char\<charId\>**(游戏内 DatingFriends 列表缩略图名),这是拿 charId 的权威方法。
- 尊爵皮肤 = 现有角色的付费新皮肤(同基础码,如 #9 char001**197** 与 #4 char001**106** 同 0011)。
- 19 个 charId **正好** == 游戏 19 个 `interaction_char` 语音 bank,一一对应。

---

## 2. 关键环境与母资源

### 设备
- **必须原生 arm 真机**(如 Galaxy S25)+ frida-gadget 重打包客户端(小号,防 ban)。
- ❌ houdini 模拟器(Genymotion)不行:frida `Memory.scan` 能用,但 `Interceptor` hook 不了译码的 arm64,
  il2cpp-bridge 不可用。
- 游客/邮箱登录可用(Google 登录因重打包签名失效)。

### 母资源清单(都在设备缓存 `files/UnityCache/Shared/<hash>/`,标准 UnityFS 无加密,UnityPy 直解)
| 资源 | 内容 | 定位 |
|---|---|---|
| `common-char-datingillust_assets_all.bundle`(385MB) | 全 19 角色 Spine(`illust_datingN.skel/.atlas/贴图`) | `file.json` readableName |
| `interaction_charXXXXXX.bytes` | 每角色**情绪 voice** bank(`Char_Int_<情绪>`) | 19 个,`common-interactionvoice` |
| `visual_interaction_sfx.bytes` / `visual_novel_sfx.bytes` + 其它 | **动作 SFX** bank | `common-sound_assets_sound` 等 |
| **`all-fmod-event-paths.tsv`**(56766 事件) | ⭐**全量 GUID→事件路径,音频映射的总钥匙** | `local_device_cache/bd2_current_20260624/` |
| `SpineInteractionPointTable`(母表) | 心契**点→情绪语音**映射(仅14心契) | frida 抓,见下 |
| `catalog_alpha.json` / `file.json` | 寻址目录 / bundle 清单 | `files/com.unity.addressables/` |
| dating prefab(在 datingillust bundle) | 热区/动作 prefab | 同 Spine bundle |

### `all-fmod-event-paths.tsv` 事件树(音频三层的来源)
```
event:/Voices/...        50019  ← 角色语音(情绪 Char_Int_<情绪> + 少数 mix 动作语音)
event:/Cinematic/Visual_Novel/CharXXXXXX/Interaction/idleN/mixN_x_x  ← 动作 SFX
event:/SFX /UISounds /BGM /Ambiences ...  ← 其它
```
**离线用这张表反查,不用再跑设备 FMOD dump(那条 error 28 死路已废弃)。**

---

## 3. 四阶段流程

### 阶段 A · 资源获取
1. 设备缓存里定位 bundle:`file.json` 按 readableName 找 → cache hash → `adb pull __data`。
2. 或官方 CDN 直下:catalog 模板 `{BDNetwork.CdnInfo.Info}/Android/{Resolution}/{Version}/<bundle>.bundle`
   (需解析出 `{Info}` 域名)。
3. UnityPy 解 bundle(`UnityPy.config.FALLBACK_UNITY_VERSION="2021.3.40f1"`,BD2 抹了版本号)。

### 阶段 B · 资源组合(Spine 立绘)
- 工具:`tools/extract_dating_spine.py <bundle> [out]` → 每角色 `.skel/.atlas/贴图页` 到
  `upstream/spine/illust/illust_dating/illust_datingN/`。
- Spine 版本 **4.1.11**,兼容 vendored `spine-player-4.1.56`。
- **自托管**:素材推到 `clam314/bd2web-assets`(jsdelivr),`dating.html` 的 `ASSET_COMMIT` 钉 commit。
  GitHub Pages(github.io)走这个仓,本地 `useCdn=false` 走 `./upstream/`。

### 阶段 C · 交互复现(热区 + 动作)
- 工具(输入 = datingillust prefab bundle):
  - `extract_dating_hotzones.py --dating-id illust_datingN` → skeleton-space 热区坐标 → `data/dating_hotzones.json`
  - `extract_dating_actions.py --dating-id illust_datingN` → 每点的 mix 动画 + gyro/touch/gauge → `data/dating_actions.json`
- 前端优先读这两个外部 JSON,`dating.html` 里旧的 `PREFAB_HOTZONES`/`PREFAB_POINT_ACTIONS` 只兜底。
- 还需:`DATING` 数组条目、`DEFAULT_STAGE_MOTIONS`(idle/阶段数)、视口(有 `DEFAULT_VIEWPORT` 兜底)。

### 阶段 D · 音频复现(见第 4 节三层)
- 审计门禁:`audit_dating_audio_integrity.py`。任何批量生成前先跑它,确认
  `illust_datingN -> charId -> FMOD event path` 三者一致；`SpineInteractionPointTable.gid`
  只做反查,**不能当菜单编号**。
- 工具:`extract_dating_audio.py`(情绪voice)、`extract_dating_sfx.py`(动作SFX)、
  `apply_dating_interaction_voice_actions.py`(心契点→语音)、`build_dating_character.py`(串联)。
- 都写进 `data/dating_audio.json` + `audio/dating/illust_datingN/{voice,sfx}/`。

---

## 4. 三层音频模型(关键)

| 层 | 是什么 | 源 | 触发方式 | 覆盖 |
|---|---|---|---|---|
| **① 情绪 voice** | 角色说的话 | `interaction_charXXXXXX` bank(`Char_Int_<情绪>`) | 心契:点→语音(`SpineInteractionPointTable`);其余:情绪池 | 19/19 有素材 |
| **② 动作 SFX** | 点击/拖动音效 | `visual_interaction_sfx` 等 bank(`Cinematic/.../Interaction/mixN`) | 动画名→SFX 事件(用 tsv 反查) | 19/19 有事件 |
| **③ mix 动作语音** | 动画绑定的专属语音(莎拉赌场那种) | `event:/Voices/.../Char_Int_mix` | 动画名→专属语音事件 | **仅 #16、#18** |

- **① 的"点→语音"精确映射只有 14 心契有**(`data/dating_interaction_tables.json`);尊爵/动作型只有情绪池。
- **③ 全库只有两个角色**:#18 莎拉(48)、#16 奥利维耶(30)。#16 是白捡的第二个动作语音角色。
- 提取方法:bank 内 event GUID 用 `all-fmod-event-paths.tsv` 反查(**不按名字猜**)。

---

## 5. 权威数据文件(前端消费)

| 文件 | 作用 | 覆盖 |
|---|---|---|
| `data/dating_charid_map.json` | 菜单#↔charId 权威映射 | 19/19 ✅ |
| `data/dating_audio.json` | 音频清单(voice+sfx event/sample/action) | voice 19/19;sfx 1-19(18 手写动作;6/11/12/13/14/15/16/17/19 部分缺口) |
| `data/dating_actions.json` | 每点动作(mix动画/gyro/touch) | 18(缺18;18 仍用前端手写特殊逻辑) |
| `data/dating_hotzones.json` | 热区 skeleton-space 坐标 | 18(缺18;18 仍用前端手写特殊逻辑) |
| `data/dating_interaction_tables.json` | 心契点→情绪语音母表 | 14 心契 |
| `data/dating_interaction_meta.json` | 每角色 bank/BGM/环境音元数据 | 14 |
| `upstream/ + clam314/bd2web-assets` | Spine 立绘 | 19/19 ✅ |
| `audio/dating/illust_datingN/{voice,sfx}/` | OGG 本体 | voice 19/19;sfx 1-19(6/11/12/13/14/15/16/17/19 部分缺口) |

---

## 6. 当前状态矩阵(2026-07-01)

图例:✅完成 / 🟡部分 / ⬜未做 / —不适用

| # | 角色 | 立绘 | 热区+动作 | 情绪voice素材 | 点→语音(心契) | 动作SFX | mix动作语音 |
|---|---|---|---|---|---|---|---|
| 1 | 内布利斯 | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| 2 | 墨菲亚 | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| 3 | 罗安 | ✅ | ✅ | ✅ | 🟡(情绪✅/mix缺1) | ✅ | — |
| 4 | 泰瑞丝 | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| 5 | 爱丽洁 | ✅ | ✅ | ✅ | 🟡(情绪✅/mix缺3) | ✅ | — |
| 6 | 威廉明娜 | ✅ | ✅ | ✅ | 🟡(情绪✅/mix缺7) | 🟡(缺4) | — |
| 7 | 悠丝缇亚★ | ✅ | ✅ | ✅ | ⬜(非心契) | ✅ | — |
| 8 | 席比雅 | ✅ | ✅ | ✅ | 🟡(情绪✅/mix缺7) | ✅ | — |
| 9 | 奶牛泰瑞丝★ | ✅ | ✅ | ✅ | ⬜(非心契) | ✅ | — |
| 10 | 安洁莉卡 | ✅ | ✅ | ✅ | 🟡(情绪✅/mix缺1) | ✅ | — |
| 11 | 伊柯利普斯 | ✅ | ✅ | ✅ | 🟡(情绪✅/mix缺2) | 🟡(缺2) | — |
| 12 | 杰尼斯★ | ✅ | ✅ | ✅ | ⬜(非心契) | 🟡(缺4) | — |
| 13 | 提尔 | ✅ | ✅ | ✅ | 🟡(情绪✅/mix缺9) | 🟡(缺3) | — |
| 14 | 黎维塔★ | ✅ | ✅ | ✅ | ⬜(非心契) | 🟡(缺2) | — |
| 15 | 班塔纳 | ✅ | ✅ | ✅ | 🟡(情绪✅/mix缺12) | 🟡(缺3) | — |
| 16 | 奥利维耶 | ✅ | ✅ | ✅ | 🟡(情绪✅/mix缺22) | 🟡(缺2) | **⬜ 可做** |
| 17 | 帕莱特 | ✅ | ✅ | ✅ | 🟡(情绪✅/mix缺20) | 🟡(缺2) | — |
| 18 | 莎拉★ | ✅ | ⬜ | ✅ | —(非心契) | ✅ | ✅ |
| 19 | 格兰希特 | ✅ | ✅ | ✅ | 🟡(情绪✅/mix缺10) | 🟡(缺2) | — |

注:18 莎拉仍保留前端手写特殊热区/动作逻辑,未写入 `dating_actions/hotzones.json`。

**心契点→语音 键不一致 bug —— 已修复(2026-07-01)。** 记录经过备查:

- **发现**:用真实点击路径 + 母表基准复验(推翻此前"已落地/无问题"的误判)。前端点击热区用 `dating_actions.json`
  的键(`stage_id_tool`)作 pointKey,精确查 `interactionVoices[pointKey]`。但 `extract_dating_actions.py` 与
  interactionVoices 构建器对 toolId 键方案不一致 → 大量点击查不到语音。两类:①tool 变体点(选道具后点击是
  `tool21/22`,iv 只有 `tool0`,见 16/8/10/17);②**19 号整体错位**(iv 全键成 `tool19/20`,点击是 `tool0`,零交集,55/55 全哑)。
- **修法(前端 (stage,id) 兜底,`dating.html` `scheduleInteractionVoice`)**:精确键查不到时,回退到同 `stage_id_*`
  的任一变体。依据两条硬验证:母表只按 (stage,id) 索引语音、与 tool 无关;且 (a) 同 (stage,id) 不同 tool 变体在 iv 里
  语音 **0 冲突**,(b) 每条 iv 语音都对应母表有语音的点 **0 反例** → 兜底安全且忠实母表,不会误触发。**没有改数据**。
- **修后核验**:可修复集(母表要的事件确实在 voice bank 里)**14 角色残留全 0**;19 号真实点击 `1_1_0→Neutral1`、
  `2_1_0→Shy1` 等全部出声;对照点 `2_16_0`(mix 语音未提取)正确静音。浏览器无语法/运行错。
- **残留 94 个属第三类**(非本 bug):母表要的是 `Char*_Int_Mix*`/`Special*` 等 **mix/special 动作语音**(音频三层的
  第③层),压根不在情绪 voice bank,需另做提取(见 TODO)。各号第三类残留:3=1,5=3,6=7,8=7,10=1,11=2,13=9,15=12,16=22,17=20,19=10。
- 校验脚本:`dating_actions.json` 键 × `dating_interaction_tables` 母表 × `dating_audio` events 三方交叉(会话内)。

### 2026-07-01 音频防串审计与本批 SFX

审计脚本:`tools/audit_dating_audio_integrity.py`。

本轮固定规则:

1. `datingN -> charId` 只读 `data/dating_charid_map.json`。
2. FMOD event path 必须含同一个 `CharXXXXXX`。
3. `SpineInteractionPointTable.gid` 只做 charId 反查,不等于菜单编号；本轮审计明确有
   **8 个 PointTable 角色的 gid != dating number**。
4. `visual_interaction_sfx` 只认有可播放 FSB stream 的 timeline；只有空 wave GUID 的事件不算可用音频。

审计输出保存在忽略目录:

- `local_device_cache/dating_audio_integrity_audit.json`
- `local_device_cache/dating_audio_integrity_audit.md`

已接入的高确定性动作 SFX 角色:

`visual_interaction_sfx` 组:

| dating | charId | SFX events | samples | required action missing | path char mismatch | OGG bad |
|---|---|---:|---:|---:|---:|---:|
| `illust_dating2` | `char003402` | 81 | 57 | 0 | 0 | 0 |
| `illust_dating3` | `char003203` | 70 | 63 | 0 | 0 | 0 |
| `illust_dating4` | `char001106` | 82 | 65 | 0 | 0 | 0 |
| `illust_dating5` | `char060802` | 73 | 65 | 0 | 0 | 0 |
| `illust_dating8` | `char001006` | 69 | 75 | 0 | 0 | 0 |
| `illust_dating9` | `char001197` | 128 | 140 | 0 | 0 | 0 |
| `illust_dating10` | `char066403` | 113 | 87 | 0 | 0 | 0 |

部分覆盖、保守留缺口:

| dating | charId | SFX events | samples | remaining missing | bad OGG |
|---|---|---:|---:|---|---:|
| `illust_dating6` | `char067603` | 59 | 83 | `mix2_1_1`, `mix3_1_1`, `mix4_1_1`, `mix5_1_1` | 0 |
| `illust_dating11` | `char000706` | 67 | 69 | `mix1_0_1`, `mix2_0_1` | 0 |
| `illust_dating12` | `char061492` | 128 | 145 | `mix1_0_1`, `mix1_35_1`, `mix2_0_1`, `mix3_0_1` | 0 |

`Visual_Novel_SFX` 组:

| dating | charId | SFX events | samples | remaining missing | path char mismatch | OGG bad |
|---|---|---:|---:|---|---:|---:|
| `illust_dating13` | `char004102` | 79 | 87 | `mix1_0_1`, `mix2_0_1`, `mix3_0_1` | 0 | 0 |
| `illust_dating14` | `char003892` | 69 | 70 | `mix1_0_1`, `mix2_0_1` | 0 | 0 |
| `illust_dating15` | `char067004` | 71 | 114 | `mix1_0_1`, `mix2_0_1`, `mix3_0_1` | 0 | 0 |
| `illust_dating16` | `char003604` | 78 | 119 | `mix1_0_1`, `mix2_0_1` | 0 | 0 |
| `illust_dating17` | `char004202` | 73 | 105 | `mix1_0_1`, `mix2_0_1` | 0 | 0 |
| `illust_dating19` | `char067104` | 56 | 87 | `mix1_0_1`, `mix2_0_1` | 0 | 0 |

当前 `Visual_Novel_SFX` 证据:

```text
common-sound_assets_sound/visual_novel_sfx.bytes
bundleName=ae2d0048197fd9af691d991454050be2
hash=67087266740ce88580ec3bf3f84b8ff6
bankGuid=bcbf2950f645bb4bbd33ad593e44c248
```

其中可确认的 Interaction SFX path 数:

```text
Char004102(dating13)=79
Char003892(dating14)=69
Char067004(dating15)=71
Char003604(dating16)=78
Char004202(dating17)=73
Char067104(dating19)=56
Char000396(dating18)=112
```

已知工具细节:

- `extract_dating_sfx.py` 会跳过 FMOD timeline 中的空 wave GUID。比如 dating2 的若干事件同时有有效
  sample 和空引用,空引用不应导致整条事件失败。
- `extract_dating_sfx.py` 会直接写 `data/dating_audio.json`,不要并行跑多个角色;并行写会让后完成者覆盖
  先完成者的 JSON 修改。
- 当前 macOS/Homebrew `ffmpeg` 没有 `libvorbis` encoder,工具会 fallback 到原生 `vorbis`;命令输出会先
  打 `Unknown encoder 'libvorbis'`,但最终 OGG 仍需以 `ffprobe` 验证为准。

---

## 7. 待办(按性价比排序)

0. **【2026-07-02】mix 播放语义**:前端旧代码把 `mix:[...]` 当一次触发全量串播;游戏真实语义分三种:
   drag=两阶段(`_1`=拖住,`_2`=松手回弹)、touch=逐次点击递进(clickMax/1秒连点窗口/停止播 `*_end`)、
   部分 touch=随机单段(IsPlayRandomMixAnim)。资源与 (group,id,tool) 匹配本身没错。
   - ✅ **拖拽已修**(纯前端,dating2 三阶段全部拖拽点浏览器实测通过,详见 `CODEX_CHANGES.md` §5.5)。
   - ⬜ **touch 多段/随机待修**:需先给 `extract_dating_actions.py` 补抽
     `IsPlayRandomMixAnim`/`ContinuousClickResetTime`/`PlayMixAnimNameWhenActionStop`(+拖拽目的地 `_destinations`)
     并重生成 JSON,再改前端播放器。所有字段都在本地 bundle 里,**不需要进游戏/连设备**。
1. **补剩余 SFX 缺口**:dating6/11/12/13/14/15/16/17/19 只剩少量 gyro/初始动作缺口,需要运行态或更精确 bank 证据,
   不要用 `*_end` 硬 alias。
2. **运行态确认 `mix*_0_1`**:多名角色剩下的都是阶段入口/默认动作类 `mixN_0_1`;当前 FMOD event path
   没有对应可播放事件。不要把它们硬 alias 到其它动作。
3. **谨慎处理 dating18 外部化**:莎拉有前端手写特殊逻辑,新抽 prefab 与手写计数不完全一致,不要直接覆盖。
4. **#16 奥利维耶做莎拉式 mix 动作语音**(30 事件,现成)。
5. ✅ **心契点→语音 键不一致 bug 已修**(见第 6 节):`dating.html` `scheduleInteractionVoice` 加 (stage,id) 兜底,
   14 角色可修复集残留全 0,浏览器实测通过。**未改数据**。

6. **【设备侧】补第三类 mix/special 互动语音**(94 个残留点,需连 S25 真机重跑抽取管线):
   - 母表引用了 `Char*_Int_Special*` / `Char*_Int_Mix*` 互动语音(Voices 命名空间,tsv 有 `..._KR` 事件路径),
     但当年 `extract_dating_audio.py` 没抽出来(OGG 未解码、json 未登记 event)。
   - 各号残留点数:3=1,5=3,6=7,8=7,10=1,11=2,13=9,15=12,16=22,17=20,19=10。
   - **A 类·在角色自己 bank(重跑补抽即可)**:据 `interaction_voice_audit.tsv` 片段确认——
     3/5/6(special)、10(mix)、11/13(special)、15(special+mix)的目标样例就在各自
     `interaction_charXXXXXX.bytes`。步骤:adb pull 该角色 interaction voice bundle → `extract_dating_audio.py`
     带完整 `voice_event_paths/CharXXXXXX.tsv`(注意 `Char003203.tsv` 当前为空,得重导)→ 补 events/OGG。
   - **B 类·宿主 bank 待查(先反查再抽)**:8/16/19 的 mix/special 在自己 bank 的 audit 片段里=✗;
     17 号 audit 是 `no-stdt-region`/0 片段(异常)。需上设备用 tsv 里对应 event GUID 反查真正宿主 bank,
     不要猜。这 4 个(8/16/17/19)在定位前不要硬接。
   - 本地只有 dating1(char003303)的原始 bank,其余都要从设备拉;这是本任务的前置门槛。
   - 完成后前端无需再改:兜底逻辑会自动让新登记的 (stage,id) 语音生效。

---

## 8. 工具索引

| 工具 | 阶段 | 作用 |
|---|---|---|
| `tools/extract_dating_spine.py` | B | 抽 Spine 立绘 |
| `tools/extract_dating_hotzones.py` | C | 抽热区坐标 |
| `tools/extract_dating_actions.py` | C | 抽点动作(mix/gyro/touch) |
| `tools/extract_dating_audio.py` | D | 抽情绪 voice(bank→OGG+manifest) |
| `tools/extract_dating_sfx.py` | D | 抽动作 SFX |
| `tools/audit_dating_audio_integrity.py` | D | 音频防串审计/批量前门禁 |
| `tools/apply_dating_interaction_voice_actions.py` | D | 心契点→语音落地 |
| `tools/build_dating_character.py` | D | 串联单角色全流程 |
| `tools/il2cpp-re/capture_interaction_agent.ts` | 母表 | frida 抓 `SpineInteractionPointTable`(bulk 全 gid) |
| `tools/il2cpp-re/*` | 逆向 | il2cpp dump / 表抓取 agent |

详见 `AGENTS.md`(逆向/frida/自托管细节)和 `CODEX_CHANGES.md`(音频线索日志)。

---

## 修订说明

- 2026-07-01：将 `Visual_Novel_SFX` 对 `dating13/14/19` 的确认结果合并进第 6 节状态与音频审计表；尾部只保留本修订说明，详细流水记录见 `CODEX_CHANGES.md`。
- 2026-07-01：补入 `dating15/16/17` 的外部热区/动作 JSON 与 `Visual_Novel_SFX` 结果；`dating18` 继续保留手写特殊逻辑。
