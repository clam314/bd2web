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

- `passive_column_hook.js` — **安全被动 hook**：attach 列读取方法 `0x6CD45C4`，把游戏查询出的、
  匹配 voice 正则的字符串写到 `voice.log`。只读不调用 il2cpp，不卡不崩。进心契时自动抓语音映射。
- `dump_table_agent.ts` — frida-il2cpp-bridge agent：hook `GetSQLite` 抓 RawDataManager 单例，
  遍历 `GetSpineInteractionPointTables(gid)` dump 整表。⚠️ **主动 invoke 有风险**（游戏线程跑会卡
  白屏、frida 线程跑会因 GC 并发崩），仅在能容忍崩溃/有把握时用。用 esbuild 打包：
  `npm i frida-il2cpp-bridge esbuild --ignore-scripts && node node_modules/esbuild/bin/esbuild
  dump_table_agent.ts --bundle --format=iife -o hook.js`。

### gadget 注入（非 root，重打包）
1. APKEditor 合并 split → merged.apk
2. lief 给 `lib/arm64-v8a/libmain.so` 加 `DT_NEEDED libgadget.so`，放入 frida-gadget arm64 .so
3. 加 `libgadget.config.so`（script 模式，path 指向 `/sdcard/Android/data/<pkg>/files/hook.js`）
4. 删 META-INF → zipalign → apksigner → install
5. **坑**：重打包后 Google 登录失效（签名校验）；frida 17 用 `Process.getModuleByName(...).findExportByName`

### 最省事的路（推荐有 root 时）
root 设备 + frida-server hook（不用重打包→能正常登录→进心契→`passive_column_hook.js` 自动抓）。
