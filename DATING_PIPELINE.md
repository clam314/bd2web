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
- **③ 全库只有两个角色**:#18 莎拉(48)、#16 奥利维耶(30,已完成 2026-07-03)。
  ③ 层的 mix/motion 事件**不带新录音**:FMOD timeline 按时间点触发已有情绪 sample(带 at/window/权重),
  所以只要角色自己的 interaction bank 在手,重解 bank 即可,不需要设备。#16 的"30 事件"= 15 KR + 15 JP。
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
| 3 | 罗安 | ✅ | ✅ | ✅ | ✅(2026-07-03) | ✅ | — |
| 4 | 泰瑞丝 | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| 5 | 爱丽洁 | ✅ | ✅ | ✅ | ✅(2026-07-03) | ✅ | — |
| 6 | 威廉明娜 | ✅ | ✅ | ✅ | ✅(2026-07-03) | 🟡(缺4) | — |
| 7 | 悠丝缇亚★ | ✅ | ✅ | ✅ | ⬜(非心契) | ✅ | — |
| 8 | 席比雅 | ✅ | ✅ | ✅ | ✅(2026-07-03) | ✅ | — |
| 9 | 奶牛泰瑞丝★ | ✅ | ✅(骨骼窗口驱动交互链 2026-07-07) | ✅ | ⬜(非心契) | ✅ | — |
| 10 | 安洁莉卡 | ✅ | ✅ | ✅ | ✅(2026-07-03) | ✅ | — |
| 11 | 伊柯利普斯 | ✅ | ✅ | ✅ | ✅(2026-07-03) | 🟡(缺2) | — |
| 12 | 杰尼斯★ | ✅ | ✅ | ✅ | ⬜(非心契) | 🟡(缺4) | — |
| 13 | 提尔 | ✅ | ✅ | ✅ | ✅(2026-07-03) | 🟡(缺3) | — |
| 14 | 黎维塔★ | ✅ | ✅ | ✅ | ⬜(非心契) | 🟡(缺2) | — |
| 15 | 班塔纳 | ✅ | ✅ | ✅ | ✅(2026-07-03) | 🟡(缺3) | — |
| 16 | 奥利维耶 | ✅ | ✅ | ✅ | ✅(2026-07-03) | 🟡(缺2) | ✅(2026-07-03) |
| 17 | 帕莱特 | ✅ | ✅ | ✅ | ✅(2026-07-03) | 🟡(缺2) | — |
| 18 | 莎拉★ | ✅ | ⬜ | ✅ | —(非心契) | ✅ | ✅ |
| 19 | 格兰希特 | ✅ | ✅ | ✅ | ✅(2026-07-03) | 🟡(缺2) | — |

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
  第③层),压根不在情绪 voice bank,需另做提取(见 TODO)。
  ⚠️ 2026-07-03 复核:94 的口径 = **缺失 voice 引用条数**(重复计入);当时的分摊表 13=9/16=22 是错的,
  实为 13=15/16=16(和恰好都是 31,总数才碰巧对上)。修正后各号:3=1,5=3,6=7,8=7,10=1,11=2,13=15,15=12,16=16,17=20,19=10。
- **⚠️ 2026-07-03 修正:"16 不在自己 bank"的判断是错的。** #16 的全部 15 个 KR mix 事件就在
  `interaction_char003604.bank`(本地 `local_device_cache/dating_build/char003604/`),timeline 全部可播。
  当年误判根源:该 bank 提取时 per-char tsv(`Char003604.tsv`)是空的,只能用
  `--infer-event-paths-from-samples` 从 sample 名反推事件名 → mix 事件(引用情绪 sample)被误标成情绪名,
  与真情绪事件同名互撞,只剩 15 个事件且 6 个 GUID 张冠李戴(如 `Kiss1` 的 GUID 实为 `mix1_3_1_KR`)。
  用总表 `all-fmod-event-paths.tsv` 重跑后 31 个 KR 事件全部对号(15 情绪 + 15 mix + motion1_15)。
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

### 2026-07-02 拖拽语义与跟手复现(已完成,全角色生效)

真机语义,il2cpp 静态确证(so=`apk_20260624/libil2cpp.so`,RVA 对应 `cpp2il_dump/dump.cs`,
反汇编用 `tools/il2cpp-re/annot2.py`):

- **mix 播放入口 `0x7804FA4`**:`SetSpineAnimationExternal(name, track=1, loop=false, onComplete)`。
  拖住(`mix_1`)和回弹(`mix_2`)都是**单次播、停末帧,不循环**;按住期间保持拉扯姿势直到松手(真机行为已确认)。
  drag 的 `mix_1` 普遍只有 0.1-0.17s 且 400+ 条全身 timeline(track1 会整体压住 track0 idle)。
  ⚠️ 勿再犯:OnDragEvent 处理器 `0x780C1C0`(调用点 `0x780C408`)那条 track=1 **loop=true** 是
  "拖到 `_destinations` 目的地后循环播 `_playMotionNames[i]`"的路径(当前 prefab 全量 37 点:
  29 drag + 8 gyro;外部 JSON 排除 dating18 后剩 12 点),不是按住语义;误用会让脸部动画每
  0.1-0.17s 重复一次。
- **跟手 = 拖拽的"生命感"来源**:真机 `OnDrag` 用 `set_position` 移动点位 GO。
  **每个互动点在 skel 里有一根同名骨骼**(SkeletonUtilityBone:drag/touch=mode1 Override 即骨骼跟 GO,
  touch_follow=mode0 Follow 即 GO 跟骨骼);`boneName` = 热区 `source` 字段去掉 `" [Override]"`,
  全量 1301 点中 1300 成立(唯一例外 dating5 `2_19_1`,touch_follow,不影响拖拽)。
  因此前端**不需要重抽数据**即可由现有 `dating_hotzones.json` 定位骨骼。

前端实现(`dating.html`,自动对全部角色的 drag 点生效):

- 两阶段状态机(拖住/松手回弹/拖动中达阈值成功,见 `CODEX_CHANGES.md` §5.5);
- 拖住期间 `startDragFollow` 把点位骨骼钉到手指:包装 `skeleton.updateWorldTransform`,
  先跑一次世界变换拿到当前父级矩阵,覆盖骨骼局部坐标(屏幕→skeleton 世界坐标换算复用热区投影的
  zoom/backingScale),再完整重跑 `updateWorldTransform` 让 IK/约束同帧吃到新 target;
  松手/成功/取消 `stopDragFollow` 精确复位。骨骼找不到时静默跳过(莎拉手写热区无 `source`,不受影响);
- 注意:点位骨骼自身通常没有贴图 slot,而是 IK target。dating2 stage3 的 `point3_3_drag`→IK `mix3_1_3`
  控 `88`,`point3_11_drag_follow`→IK `mix3_1_10A` 控 `113`;只更新 target bone 自己会让可见丝袜/腿部骨骼
  不同帧重算,表现为拖拽3/11 局部拉扯动画不明显或丢失。
- track1 上的动画不经过 start 监听(监听只挂 track0),mix 的 SFX 在 `playDragBegin`/`playDragRelease` 手动触发;
- 浏览器实测 dating2 全三阶段:3_11 跟手变形+按住表情正确、1_7/1_12 单次播放不重复、
  3_3 局部拖拽效果恢复、松手骨骼精确复位(局部/世界坐标回到初值)、1_19 拖到位播 motion 进阶段。
- 已知与真机的小差异:越过启动阈值瞬间骨骼小跳一下(真机为直接钉到手指,行为类似);只做位移未做旋转跟随。

---

## 7. 待办(按性价比排序)

0. **【2026-07-02】mix 播放语义**:前端旧代码把 `mix:[...]` 当一次触发全量串播;游戏真实语义分三种:
   drag=两阶段(`_1`=拖住,`_2`=松手回弹)、touch=逐次点击递进(clickMax/1秒连点窗口/停止播 `*_end`)、
   部分 touch=随机单段(IsPlayRandomMixAnim)。资源与 (group,id,tool) 匹配本身没错。
   - ✅ **拖拽已修完**(两阶段+不循环+SFX+跟手,见上方"拖拽语义与跟手复现"一节)。
   - ✅ **touch 多段/随机已落地并抽样复核(2026-07-03)**:`extract_dating_actions.py` 已补抽
     `IsPlayRandomMixAnim`/`ContinuousClickResetTime`/`PlayMixAnimNameWhenActionStop`,输出
     `randomMix`/`clickReset`/`stopMix`;前端 touch 已改为单次点击只播一段 mix,`clickMax`
     在重置窗口内递进,非 gauge 到上限后拦截额外点击,停手按 `clickReset` 重置,`randomMix`
     随机选单段。浏览器自动化抽样覆盖:非 gauge 有/无 `stopMix`、完成后额外点击、reset 后重来、
     gauge 不被拦截、randomMix 单段选择、普通多段无 clickMax 保持原逻辑。完成后的 `stopMix` 证据不足,
     前端仍保守跳过。
   - ✅ **无 clickMax 的 repeated/end mix 按点击索引单段播放**:原生 `SpineInteractionPoint.OnClick`
     会先递增 `CurClickCount`,随后 `SpineInteractionActionController` 对 `PlayMixAnimNames` 取
     `min(CurClickCount - 1, mixCount - 1)` 播单段,不是把整列 mix 排队连播。`ClickMaxCount=0`
     的 dating6 `2_1_0`/`3_1_0`/`4_1_0`/`5_1_0` 因而每点一次推进:
     前 4 次播 `mix*_1_1`,第 5 次起钳到 `mix*_1_end`。前端只对
     `touch + 无 clickMax + 非 random + 非 gauge + 无 stopMix + 无 motion/nextStage/setFlag + 多 mix 且有重复或 _end`
     启用该路径;实际切阶段时清空该索引计数,对齐原生换组重置互动点状态;当前全库命中仅这 4 个点。
   - ✅ **`_destinations` 拖到目的地(drag)**:数据已补抽,前端 drag 命中行为已接入。证据来自当前
     `common-char-datingillust_assets_all.bundle` prefab:全量 37 个非空 destination ref
     (29 drag + 8 gyro),其中 dating18 仍按既有策略排除外部化;`data/dating_actions.json`
     现有 12 个 action 带 skeleton-space `destinations` 矩形(dating1/2/6/11)。前端现在对可投影
     drag 目标要求指针进入目的地矩形才成功;若目标在当前网页视口下完全不可投影,保守退回旧距离阈值,
     避免卡死阶段推进。gyro destination 仍未做。
   - ✅ **`*_follow` 热区按当前 Spine bone 跟随**:prefab 里的 follow 点不是静态 RectTransform,
     而是 `SkeletonUtilityBone` 绑定到同名 Spine bone。前端现在对 `source` 含 `_follow` 的热区用
     `skeleton.findBone(name).worldX/worldY` 作为中心,并在每帧轻量刷新已有按钮位置。屏外 follow 点会先
     作为隐藏按钮保留,动画把 bone 带进视口后自动显示。dating6 stage6 复核:初始 33 点中 13 点可见,
     20 点隐藏;点 `6_15_0` 后隐藏点 `6_16_0`/`6_27_0`/`6_30_0` 进入可见集,点 `6_7_0` 后
     `6_8_0`/`6_23_0` 进入可见集,点 `6_19_0` 后 `6_20_0` 进入可见集。攻略式顺序互动由此可触发,
     未硬编码攻略文本到状态机。2026-07-06 追加复核:二/三层路径
     `6_5_0→6_21_0→6_22_0`,`6_7_0→6_23_0→6_24_0`,`6_4_0→6_25_0→6_26_0`,
     `6_15_0→6_27_0→6_28_0/6_29_0`,`6_15_0→6_30_0→6_31_0→6_33_0`,
     `6_15_0→6_30_0→6_32_0` 均可点击并记录对应 `mix6_*` 动画历史。
1. **补剩余 SFX 缺口**:dating6/11/12/13/14/15/16/17/19 只剩少量 gyro/初始动作缺口,需要运行态或更精确 bank 证据,
   不要用 `*_end` 硬 alias。
2. **运行态确认 `mix*_0_1`**:多名角色剩下的都是阶段入口/默认动作类 `mixN_0_1`;当前 FMOD event path
   没有对应可播放事件。不要把它们硬 alias 到其它动作。
3. **谨慎处理 dating18 外部化**:莎拉有前端手写特殊逻辑,新抽 prefab 与手写计数不完全一致,不要直接覆盖。
4. ✅ **#16 奥利维耶 mix 动作语音已完成(2026-07-03)**。做法(下个同类角色照抄):
   ```
   python3 tools/extract_dating_audio.py \
     --bank local_device_cache/dating_build/char003604/interaction_char003604.bank \
     --fsb  local_device_cache/dating_build/char003604/interaction_char003604.fsb \
     --event-paths local_device_cache/bd2_current_20260624/all-fmod-event-paths.tsv \
     --dating-id illust_dating16 --char-id char003604 \
     --source-version 202606240959 --language KR --expect-events 31
   python3 tools/apply_dating_interaction_voice_actions.py \
     --dating-id illust_dating16 --char-id char003604 --gid 12
   ```
   要点:①`--event-paths` 直接喂总表 tsv(不用 per-char tsv,那批文件很多是空的);②不加 `--decode`
   (mix 事件只引用已有 60 个情绪 sample,OGG 无新增);③心契角色 apply 默认 point-based,
   `actions` 置空、语音全走 `interactionVoices`(45→59 点),避免动画路径+点路径双触发
   (尊爵角色如 #18 才用 `actions`)。浏览器实测:2_14(纯 mix 点,修复前全哑)按 timeline 出声
   `Surprise1@0s→Shy2@1.4s`;2_13 情绪语音正常;`motion1_15` 阶段推进语音正常;无报错。
5. ✅ **心契点→语音 键不一致 bug 已修**(见第 6 节):`dating.html` `scheduleInteractionVoice` 加 (stage,id) 兜底,
   14 角色可修复集残留全 0,浏览器实测通过。**未改数据**。

6. ✅ **补第三类 mix/special 互动语音 —— 已全部完成(2026-07-03),全库残留归零**:
   - **实施**:①`apply_dating_interaction_voice_actions.py` 的 `short_voice_name` 补了与 extract
     `normalize_action_name` 一致的大小写规范;②两个工具 + `audit_dating_audio_integrity.py` 增加
     `--char-alias`/`KNOWN_PATH_ALIASES`(仅 char004202→char004102);③11 个角色(3/4/5/6/8/10/11/13/15/17/19)
     按 TODO 4 的两条命令重跑(extract 带 `--expect-events/--expect-samples` 断言,apply 带
     `--hotzones-json`;17 号加 `--char-alias char004102`)。
   - **核验**:11 角色事件独立重建逐字段一致;samples/sfx/bank 元数据零变化;非目标角色零变化;
     (stage,id) 级旧语音零回退(键方案因 hotzones 版本演进有变,前端 (stage,id) 兜底吃掉差异);
     全库第三类残留 voice 引用 78→**0**、缺 motion 点 6→**0**;audit `manifestPathIssues=0`;
     浏览器实测:19 号旧点回归 ✅ + 翻转点 `2_16_0`(此前"正确静音")现按 timeline 出声
     `Embarrass1@0s→Embarrass3@1.5s` ✅;17 号别名事件 `mix1_17_1` 9 个触发点逐秒吻合 ✅;
     11 号 `Special1` 三段(`Smile1@0→Satisfy1@2.66→Touch1@4.0`)✅;无报错。
   - 下面保留 2026-07-03 彻查时的诊断记录(旧 A/B 分类作废的依据):
   - **逐 bank 实测结论(用 extract 的 parse_fev + 总表 tsv 交叉,11 个角色全验)**:
     78 条缺失引用对应的 `Special*`/`Mix*`/`Motion*`/`OilSpread*` KR 事件,**100% 在各角色自己的本地
     bank 里且 timeline 可播,且只引用已解码的情绪 sample(需新解 OGG = 0)**。与 #16 完全同构。
   - **作废的旧结论**:①"本地只有 dating1 的 bank"是错的——`local_device_cache/dating_build/charXXXXXX/`
     里 14 个母表角色 bank+fsb 齐全(缺 bank 的只有 000296/001197/003892/061492 四个无母表尊爵);
     ②"8/17/19 不在自己 bank(audit ✗)"是错的——audit 查的是自有 sample 片段,而这类事件本就只引用
     情绪 sample;③17 号之谜已解:**char004202 自己的 bank 里就有一批 `Char004102_Int_*` 命名的事件**
     (游戏数据本身如此,疑为从提尔项目复制),母表引用与 bank 命名一致,samples 在 17 自己的 fsb 里。
   - **当年没抽出来的根因(基础问题,三层)**:①per-char tsv 空/不全 → 用 `--infer-event-paths-from-samples`
     反推,Mix/Special 事件(引用情绪 sample)被误标成情绪名、与真情绪事件互撞(#16 同款,全库性);
     ②大小写不匹配:`extract` 的 `normalize_action_name` 把事件名规范成小写 `mix*/motion*`,但
     `apply_dating_interaction_voice_actions.py` 拿 raw log 的原名(大写 `Mix3_25_1`)对 events 键匹配,
     必然落空(影响 8/10/13/15/17/19);③17 的 `Char004102_Int_` 前缀在两个工具的
     `short_event_name`/`short_voice_name`(按 char_id 剥前缀)下都返回 None 被丢弃。
   - **修法**:给两个工具补大小写规范一致 + 17 号前缀别名,然后逐角色重跑 #16 那两条命令(见 TODO 4);
     无新 OGG、前端零改动((stage,id) 兜底自动生效)。改 apply 匹配逻辑时注意别动 point key 方案。

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

- 2026-07-16：**#12 神秘兔女郎·杰尼斯(dating12, char061492) 交互还原**,对照巴哈攻略
  (`forum.gamer.com.tw/C.php?bsn=76207&snA=8291`)。此前热区全用静态停车位坐标,隐藏点
  (计量表/节奏圈)全程叠在画面右侧一堆 = "不分状态全出来"。修法与 dating9/11 同机制:
  ①87 个点全部有同名骨骼,加入 `BONE_FOLLOW_HOTZONE_IDS`,隐藏链自动由动画搬运骨骼驱动:
  摸头 `1_22` → 计量表 `1_23`(连点11,`mix1_23_1..10`) → `1_24` 破表 → 节奏圈
  `1_25→1_27→1_29→1_35`(成对成功/失败点同位,成功 mix 2.67s 揭示下一圈、失败 0.67s;
  网页无缩圈时机判定,失败点 `1_26/28/30/31` hidden,点中即成功) → `motion1_35` → 阶段2
  过渡(`2_1` 点击 `motion2_1`) → 阶段3 二型态。二型态隐藏链:`3_21` 冰层连点9 → `3_22` →
  `3_23`(冰柱掉落) → `3_24~3_32` 冰柱、`mix3_32_1` 是 23.3s 完整隐藏演出(拖冰柱→两腿中间),
  t≈17.5s 起 `3_43` 现身;`3_7`连点→`3_8`、`3_9`连点→`3_46` 同理。
  ②skel 是多姿势组(B=一阶段 148 slot / C+S=二型态 318 slot,mix 播 track0 时 C 组从 setup
  冒出=重叠),加入 `OVERLAY_TRACK_INTERACTION_IDS`。③道具 17=冰块(两膝窝+嘴巴)、18=嘴巴
  (仅二型态臀部),`TOOL_LABEL_OVERRIDES`;`STAGE_LABELS`+关键点 `PREFAB_ACTION_LABEL_OVERRIDES`。
  ④新增 `resetFollowPointBones()`:`playIdle` 的 `clearTrack(1)` 掐掉进行中 mix 时,被动画停到
  停车位的 point* 骨骼没有任何轨道再 key 回来会永久冻结(23s 演出中换阶段/点待机必现),回待机时
  统一把 point* 骨骼复位到 setup(骨骼跟随角色通用,dating6/9/11 回归通过)。gyro 点(`mix*_0_1`)
  三个阶段的动画在 skel 里都不存在(真机是倾斜视角平移,对应 `idle2_l1..4/r1..3` 等视差 idle
  变体),网页未接,热区 1×1 不渲染,无影响。
- 2026-07-07：**#9 一阶段进二阶段前的黑色榨乳器确认链纠正。**
  对照攻略截图/原文顺序:猜对泰瑞丝图案奶瓶后,**黑色榨乳器管线/吸杯落下**,
  然后玩家**点击泰瑞丝胸口**进入二阶段。07-07 早版把 `1_37_0` 标成
  "榨乳器落下·点胸口",且 prefab 原始矩形 `2489x2454` 近乎覆盖整个人,容易误判成大范围
  道具/动画触发。前端已改: `1_36_0` 标签为"猜奶瓶7·黑色榨乳器落下",`1_37_0` 标签为
  "黑色榨乳器吸杯接胸·进入二阶段";并在 `HOTZONE_OVERRIDES` 给 `1_37_0` 改成手工胸口确认热区
  (`x=-125,y=-360,w=620,h=520`,`stage1 dropped milker chest confirm [Manual]`)。`dating.html`
  恢复 dating9 的 MERGED 最小覆盖,只给 `1_36_0` 设置 `cow9MilkerDropped`,再让 `1_37_0`
  `requires/hotzoneVisibleWhen` 该 flag 后推进 `motion1_37 -> stage2`。**注意:这里的黑色榨乳器
  是猜对奶瓶后出现并接到胸口的剧情装置,不是 tool8 的普通"挤奶器"道具；`mix1_37_1`
  属于 tool8 普通挤奶器链,不能用于进二阶段。**
- 2026-07-07：**#9 dating9 交互链重做——从"手写 flag 门禁"改为"骨骼窗口驱动"(通用机制)。**
  背景:07-06 版用持久布尔 flag(`cow9StampReady/cow9BottleRow/...`)近似门禁,导致热区叠在一起、
  时机不对(印章一次点亮永久有效、猜瓶 7 点永久重叠在同一处、猜错不需重摆、坐下无限时窗口)。
  **原生真相(preview 里对 skel 逐动画采样 `AttachmentTimeline`/`TranslateTimeline` 证实)**:74 个
  交互点全部有同名骨骼(`point1_30_touch` 等),点的出现/消失/排开/交接**由动画把骨骼搬进画面(±画面内)
  或停到 ±50000(画面外)天然驱动**。例:idle1 把 7 个猜瓶骨骼停在 x≈50567 场外,`mix1_29_1`(4.63s)在
  t≈0.5–3.5s 把它们**排成一排**(x 从 -233 到 720)摆上桌、动画结束收走;`mix1_15_1`(2.2s)只在 t≈0–1.5s
  让 8 个盖章点在场(→**每次盖章都要重新点印章**,07-06 猜测"一次性 flag"被证伪);榨乳器 1_37 只在
  `mix1_36_1` 的 t≈5–5.5s 在场;坐下 2_11 只在 `mix2_10_1` 前 ~1.9s 窗口(→抬臀后 2 秒内点肚子才坐下)。
  **改动(全在 `dating.html`)**:①`hotzoneUsesFollowBone` 从"只认 `*_follow` 源"泛化——新增
  `BONE_FOLLOW_HOTZONE_IDS`(当前=`{illust_dating9}`),集合内角色对**所有点**用"源名(去 ` [Override]`)
  = 骨骼名"跟骨骼世界坐标,矩形只当尺寸;②删掉 dating9 大部分手写 `PREFAB_POINT_ACTIONS` 门禁,
  仅保留 `1_36_0 -> 1_37_0` 榨乳器确认链的最小 stateful 覆盖。播放语义(clickMax/stopMix/nextStage)
  大多由外部 `dating_actions.json` 提供。**浏览器全链路实测通过**:
  猜瓶一排出现/收走、印章限时、榨乳器→二阶段、抬臀后 2_11 限时窗口(2.5s 后消失)、乳牛 25 连击→2_20
  绝顶;dating4(25 热区)、dating6 stage6(33 点/13 可见/30 follow)回归无错。
  **每帧刷新**:复用既有 `frame` 回调里的 `refreshHotzonePositions()`(原本只为 `_follow`),现对
  `BONE_FOLLOW_HOTZONE_IDS` 角色同样每帧重投影,骨骼一动位置就跟。
  **遗留·泳衣带子拖拽方向(1_8/1_9)——需设备运行态证据,未改**:用户反馈"画面左带子只能往右拉"。
  查明是**骨骼 IK 内禀**:两条带子点(`point1_8_drag`/`point1_9_drag`)各驱动单骨 IK(`BR_G1`/`BR_GR1`,
  compress=true/stretch=false),rest 时骨骼已指向画面左(arot 180)满伸展 → 水平**左拉被钳制(带子驱动骨
  `bone33`/`bone46` 世界坐标不动)**,只有**右拉(骨骼横扫过去,arot 180→360)和下拉/斜下**才让带子形变
  (preview 里逐点扫 tip 世界坐标证实,左右两带对称)。同一 skel 游戏也是这套 IK,所以纯水平左拉在游戏里
  应同样无效;带子的自然脱肩动作是**向下/斜下拉**(当前已支持)。要让"水平左拉"也响应需 frida hook 游戏
  `OnDrag` 看 finger delta→点位 GO 的真实映射(S25 离线未做),**不要盲改 IK**(违反"方向不靠猜、要运行态
  证据"的项目铁律)。
- 2026-07-06：**#9 奶牛泰瑞丝(dating9, char001197) 交互还原**，对照 PTT 攻略
  (https://disp.cc/ptt/C_Chat/1edNVIad)完成。语义证据 = Spine slot 命名(泰瑞丝 skel 的
  slot 高度语义化：`paint_face/hip/belly/arm/breast`=印章8个落点、`table_bottle_fall`=打翻、
  `idle1_milk_bottle`=摆出猜图案奶瓶、`swinsuit_yes_no`=猜错摇手、`arm_L_yes`+`milking_machine_l/r`
  =猜对比爱心+黑色榨乳器管线/吸杯出现、`Gauge1-5/Gauge_char`=计量条(动画自带,无需 UI)、`F_smoke`=左下奶罐故障、
  `F_leg_up_l/r`=乳牛道具抬腿) × 热区投影位置逐点比对。前端改动(全在 `dating.html`)：
  ①`TOOL_LABEL_OVERRIDES`：tool8=挤奶器(普通道具)/tool9=牛奶瓶/tool10=乳牛道具;
  ②`PREFAB_ACTION_LABEL_OVERRIDES` 74 点全量语义标签;
  ③dating9 加入 `MERGED_PREFAB_ACTION_IDS`，`PREFAB_POINT_ACTIONS` 按 dating4 先例加攻略门禁
  (印章1_15→盖章1_16-23、后方奶罐1_29→猜瓶1_30-36(藏到点罐后)→猜对1_36→榨乳器1_37(热区隐藏+requires)
  →二阶段、连点完成态1_38/1_39、抬臀2_10→坐下2_11、计量条集满2_16→绝顶2_20);
  ④`isPrefabActionVisible` 的 `visibleWhen` 检查从 dating4-only 泛化为全角色(dating4 语义不变,已回归)。
  浏览器实测：印章/猜瓶/榨乳器进二阶段/2_11 门禁/25连击出 2_20 全链路通过,控制台无错误。
  **门禁方向的原生证据(2026-07-06 复核追加)**：skel 里每个动画的 TranslateTimeline 会把
  `point1_N_touch` 骨骼停放到 ±5 万(画面外)或留在画面内——**idle1 默认停放 1_16-23(印章落点)、
  1_30-36(猜瓶)、1_37/38/39,画面内只留普通点+1_15+1_29+工具点**,与前端门禁的隐藏集合一致;
  **mix1_29_1 恰好把 1_30-36 七个点搬进画面**(猜瓶行出现的直接原生证据)。因此复核后给
  1_16-23 补了 `hotzoneVisibleWhen`(原生默认不可见,此前只有 requires 拦截)。
  1_15=印章为间接推断(默认在画面内、位置在桌面印章处、动画无身体反应、攻略语义排除法),已注明。
  另:audioDebug 下同一 SFX 日志打 2 次为**原版既有行为**(stash 原版 A/B 实测相同),与本次改动无关。
  **遗留(需运行态证据,不要猜)**：猜奶瓶正确瓶按 prefab 固定为 1_36,游戏内是否随机未证实;
  印章门禁做成一次性 flag,游戏内是否每次需重新点印章未证实;攻略"转到背后视角乳牛暴走→绝顶"
  就是 mix2_16_25 动画内容(无独立阶段/gyro);1_29-1_36 热区 prefab 静态坐标重叠在同一处
  (运行时由游戏摆放),网页按标签区分。
- 2026-07-03(二)：TODO 6 完结——第三类 mix/special 互动语音全库归零(11 角色重跑,无新 OGG,前端零改动)。根因是三层基础问题(空 tsv 推断/extract-apply 大小写不匹配/17 号 Char004102 前缀),工具修正:apply 补大小写规范、extract/apply/audit 增 `--char-alias`(char004202→char004102)。状态矩阵"点→语音"列 14 心契全 ✅。
- 2026-07-06：`_destinations` drag 命中行为已接入前端。浏览器烟测覆盖 dating6 `1_6_0`:拖远但未进目标仍停阶段1、拖进目标推进阶段2;另确认 `4_2_0` 目的地当前视口不可投影时走旧阈值兜底,不会卡死阶段4→5。未处理 gyro destination。
- 2026-07-06：dating6 无 clickMax 的 repeated/end mix 语义已接入。il2cpp 证据:普通 `OnClick` 递增 `CurClickCount`,动作控制器取 `PlayMixAnimNames[min(CurClickCount - 1, mixCount - 1)]` 播单段;`IsSettedContinuousClick` 需要 `ClickMaxCount >= 2`,所以 dating6 `ClickMaxCount=0` 不能套连续点击逻辑。切阶段会清空索引计数以对齐原生换组重置。全库谓词命中仅 `illust_dating6` 四个 `*_1_end` 点。
- 2026-07-06：`*_follow` 热区跟随 Spine bone 已接入前端。证据:dating6 stage6 原先大量 follow 点被投到画面左侧空白区;修后初始屏外点保留为隐藏按钮,点击 `6_15_0` 可让 `6_16_0`/`6_27_0`/`6_30_0` 随动画进入可见集,页面无错误。后续补验 `6_5_0→6_21_0→6_22_0`,`6_7_0→6_23_0→6_24_0`,`6_4_0→6_25_0→6_26_0`,`6_15_0→6_30_0→6_31_0→6_33_0` 等链路均可触发对应 `mix6_*`。这是攻略顺序互动的前置机制,未硬编码攻略组合。
- 2026-07-03：`_destinations` 数据抽取阶段完成,前端行为未接。`extract_dating_actions.py` 现在从 destination MonoBehaviour 的 GameObject 反查 RectTransform,输出 skeleton-space 目的地矩形;生成前去掉 `destinations` 后与旧 `data/dating_actions.json` 完全一致,因此本次数据变化仅新增 12 个目的地字段(dating1/2/6/11,不含 dating18)。
- 2026-07-03(二)：TODO 6 完结——第三类 mix/special 互动语音全库归零(11 角色重跑,无新 OGG,前端零改动)。根因是三层基础问题(空 tsv 推断/extract-apply 大小写不匹配/17 号 Char004102 前缀),工具修正:apply 补大小写规范、extract/apply/audit 增 `--char-alias`(char004202→char004102)。状态矩阵"点→语音"列 14 心契全 ✅。
- 2026-07-03：touch 多段/随机抽样复核完成。样本包括 `illust_dating13 3_19_0`(非 gauge+stopMix,未完成停手播 `mix3_19_end`,完成后额外点击无新增动画)、`illust_dating10 1_18_13`(非 gauge 无 stopMix,三连后拦截第 4 下,reset 后从 `mix1_18_1` 重来)、`illust_dating4 1_1_0`(randomMix 单段随机)、`illust_dating15 1_1_0`(gauge 连点未被拦截)、`illust_dating1 1_16_0`(多段无 clickMax 保持原逻辑)。语法检查与 audio audit 通过,控制台仅 favicon 404。
- 2026-07-03：#16 奥利维耶 mix 动作语音 + 点→语音全部完成(TODO 4 完结)。纠正三处旧结论:①"16 的 mix 不在自己 bank"系 audit 误判(mix 事件只引用情绪 sample,无自有片段);②dating16 旧 events 因 `--infer-event-paths-from-samples` 存在 GUID 错标,已用总表 tsv 重跑修正;③旧"94 残留"分摊表 13=9/16=22 有误(实为 13=15/16=16),第三类残留(缺 voice 引用条数)94→78,另发现 6 个缺 motion 点为旧统计漏算、17 号母表跨角色引用 Char004102 的新线索(见第 6/7 节)。仅改 `data/dating_audio.json`,前端零改动。
- 2026-07-01：将 `Visual_Novel_SFX` 对 `dating13/14/19` 的确认结果合并进第 6 节状态与音频审计表；尾部只保留本修订说明，详细流水记录见 `CODEX_CHANGES.md`。
- 2026-07-01：补入 `dating15/16/17` 的外部热区/动作 JSON 与 `Visual_Novel_SFX` 结果；`dating18` 继续保留手写特殊逻辑。
