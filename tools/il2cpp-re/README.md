# BD2 IL2CPP 逆向 / 数据提取工具

记录从 BD2 (libil2cpp.so, metadata v31) 提取游戏数据的工具与结论。
完整背景见 `AGENTS.md` 的「Data 表解密进度」章节。

## 已确认的关键事实

- **游戏 DB 的 SQLCipher 密钥** = `SHA1(UTF8("spdhdnlwmrpavmtm"))` → 大写 hex → 去掉 `-`
  = `67E939EAAE0F44ED3C1091B176A32F5CDC6D3E49`（经标准 `sqlite3_key` 设入，存档库+母表共用）。
- `Data/<hash>` 文件是**自定义 SQLite VFS 边读边解密**的 SQLCipher（固定头 b3d5，stock sqlcipher
  打不开）。磁盘无明文 db。
- 心契语音表 `SpineInteractionPointTable`（列 `SoundVoiceName`/`SoundMotionVoiceName`）**进入心契
  功能才加载进内存**。
- 关键 RVA（dump.cs）：列文本读取 `0x6CD45C4`、`RawDataManager.GetSQLite` `0x5B18AE8`。

## 静态分析（不需要设备）

- `annot2.py <RVA...>` — 反汇编单个函数并注释：用 ELF 重定位表把 il2cpp 字符串/方法引用解析出来
  （绕开 il2cpp 的 usage 间接层，不需要 Ghidra）。依赖 `/tmp/strmap.json`(ScriptString)、
  `/tmp/methmap.json`(ScriptMethod)、`/tmp/relocs.txt`(`objdump -R` 导出)。
- `xref.py <slot_vaddr...>` — 全量反汇编扫哪些代码引用了某个字符串槽位。

先决条件：用 Il2CppDumper 产出 `dump.cs`/`script.json`；`objdump -R libil2cpp.so > relocs.txt`；
从 script.json 抽 strmap/methmap。

## 运行态（frida，需要能跑起来的设备）

### ✅ 已跑通：`capture_interaction_agent.ts`（推荐，已成功提取 Char003303 全表）
frida-il2cpp-bridge agent，**被动 hook 高层 getter 读返回值**，不主动 invoke、不阻塞、不崩：
- `Interceptor.attach(RawDataManager.GetSpineInteractionPointTables.virtualAddress, {onLeave})`，
  在**游戏自己查表时**读返回的 `List<SpineInteractionPointTable>`，逐行取
  `get_Id / get_GroupId / get_InteractionGroupId / get_SoundVoiceName(repeated) / get_SoundMotionVoiceName`。
- 按 `(name,interactionGroupId,count)` 去重，**每张表只 dump 一次**，避免重复阻塞。
- 进心契互动页 → 游戏查表 → 自动写 `table.log`。打包：
  `npm i frida-il2cpp-bridge esbuild @types/frida-gum --ignore-scripts && node
  node_modules/esbuild/bin/esbuild capture_interaction_agent.ts --bundle --format=iife -o hook.js`

**坑（务必避开）**：
- ❌ 不要用 `method.implementation = fn` 再在里面 `method.invoke()` → **调到被替换的自己 → 无限递归卡死**。
  要读返回值就用 `Interceptor.attach + onLeave`。
- onLeave 里的读取（invoke）跑在**游戏线程**上，安全；放到 frida 自己线程异步读会 **GC 并发崩**。
- 量大时务必去重，否则游戏 loop 调用 + 每次全表 dump 会卡。

**统一全量（关键）**：表是**母表(含所有角色,不看拥有权)**。`capture_interaction_agent.ts` 即全量版：
onEnter 抓 `this`，onLeave 里用 `bulking` 防重入、循环 `GetSpineInteractionPointTables(gid)` gid=1..800，
一次 burst 拿**全部 14 个情绪型角色**。

成果：
- `all_interaction_tables_raw.log` + `../../data/dating_interaction_tables.json` — 全部 14 情绪型角色
  (dating1-14，gid==dating 编号) 的 点→语音 映射。
- `char003303_table_raw.log` + `../../data/illust_dating1_interaction.json` — 单角色(dating1)示例。
- `spine_interaction_table_raw.log` + `../../data/dating_interaction_meta.json` — 每角色元数据
  (`SoundVoiceBankName=Interaction_CharXXXXXX`、BGM、环境音、HasSoundVoiceKR/JP)，来自 `SpineInteractionTable`。

**约会角色三分类**：情绪型 dating1-14（这张表，✅全拿）、动作型 dating18 莎拉（bank mix 采样，另一管线）、
客串 Guest dating15-17（Refithea/Olivier/Palette，**当前母包已删,无解,需旧版数据**）。多表已排查：
`SpineInteractionTable`/`DatingCostumeTable` 都只有同样 14 个，Guest 一张表都不在。

**通用 dump 技巧**：不知结构时遍历类的无参 `get_*`，基础类型取值、list 取 count+items；先 introspection
列 `RawDataManager` 全部 `Get*`(共 361 个) 找候选表。gadget `on_change:reload` 在大量 invoke 后可能失效，
最稳是 `am force-stop` 重启游戏让 gadget 启动时重载。

### 设备选择：必须用**原生 arm 真机**，不能用 houdini 模拟器
- Genymotion + houdini（ARM 翻译）上：frida `Memory.scan`/读内存**能用**，但
  `Process.findModuleByName("libil2cpp.so")` 返回 NULL、**Interceptor 没法 hook 译码的 arm64 函数** →
  il2cpp-bridge 不可用。内存里也**没有连续的明文 SQLite 库**（自定义 VFS 是分散页缓存/数据已进 il2cpp 对象）。
- 真机（如 S25，原生 arm64）+ frida-gadget 重打包：bridge / Interceptor **完全可用**。这是成功路径。

### 其它（备用 / 历史）
- `passive_column_hook.js` — 被动 hook 列读取 `0x6CD45C4` 抓文本列。但情绪型语音存在 protobuf
  blob 里、不是文本列，**抓不到** → 改用上面的高层 getter hook。
- `dump_table_agent.ts` — 早期主动 invoke 版本，⚠️ 主动遍历有崩/卡风险，已被 `capture_interaction_agent.ts` 取代。

### gadget 注入（非 root，重打包）
1. APKEditor 合并 split → merged.apk
2. lief 给 `lib/arm64-v8a/libmain.so` 加 `DT_NEEDED libgadget.so`，放入 frida-gadget arm64 .so
3. 加 `libgadget.config.so`（script 模式，path 指向 `/sdcard/Android/data/<pkg>/files/hook.js`）
4. 删 META-INF → zipalign → apksigner → install
5. **坑**：重打包后 Google 登录失效（签名校验）；frida 17 用 `Process.getModuleByName(...).findExportByName`

### 最省事的路（推荐有 root 时）
root 设备 + frida-server hook（不用重打包→能正常登录→进心契→`passive_column_hook.js` 自动抓）。
