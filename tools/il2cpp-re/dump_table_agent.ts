import "frida-il2cpp-bridge";

const OUT = "/sdcard/Android/data/com.neowizgames.game.browndust2/files/table.log";
function log(s: string) {
  try { const f = new File(OUT, "a"); f.write(s + "\n"); f.flush(); f.close(); } catch (e) {}
}
function readRepeated(rf: Il2Cpp.Object | null): string {
  try {
    if (!rf || rf.handle.isNull()) return "";
    const n = rf.method<number>("get_Count").invoke();
    const out: string[] = [];
    for (let i = 0; i < n; i++) {
      const v = rf.method<Il2Cpp.String>("get_Item").invoke(i);
      out.push(v && !v.handle.isNull() ? (v.content ?? "") : "");
    }
    return out.join("|");
  } catch (e) { return "<err>"; }
}

let savedHandle: NativePointer | null = null;
let dumped = false;

function doDump() {
  if (dumped || !savedHandle) return;
  dumped = true;
  Il2Cpp.perform(() => {
    try {
      const rdm = new Il2Cpp.Object(savedHandle!);
      log("dump start rdm=" + rdm.handle + " class=" + rdm.class.name);
      // 父表诊断
      try {
        const gp = rdm.method<Il2Cpp.Object>("GetSpineInteractionTables", 1);
        let pg = 0;
        for (let x = 0; x <= 3000; x++) {
          let pl: Il2Cpp.Object; try { pl = gp.invoke(x); } catch (e) { continue; }
          if (!pl || pl.handle.isNull()) continue;
          let pc = 0; try { pc = pl.method<number>("get_Count").invoke(); } catch (e) { continue; }
          if (pc > 0) { log(`[PARENT] x=${x} count=${pc}`); if (++pg > 30) break; }
        }
        log(`[PARENT] nonEmpty=${pg}`);
      } catch (e: any) { log("[PARENT] err " + e); }
      // 点表
      const getTables = rdm.method<Il2Cpp.Object>("GetSpineInteractionPointTables", 1);
      let groups = 0, rows = 0;
      for (let gid = 0; gid <= 5000; gid++) {
        let list: Il2Cpp.Object; try { list = getTables.invoke(gid); } catch (e) { continue; }
        if (!list || list.handle.isNull()) continue;
        let cnt = 0; try { cnt = list.method<number>("get_Count").invoke(); } catch (e) { continue; }
        if (cnt <= 0) continue;
        groups++;
        for (let i = 0; i < cnt; i++) {
          const row = list.method<Il2Cpp.Object>("get_Item").invoke(i);
          if (!row || row.handle.isNull()) continue;
          const id = row.method<number>("get_Id").invoke();
          const g = row.method<number>("get_GroupId").invoke();
          const ig = row.method<number>("get_InteractionGroupId").invoke();
          const voice = readRepeated(row.method<Il2Cpp.Object>("get_SoundVoiceName").invoke());
          const motion = readRepeated(row.method<Il2Cpp.Object>("get_SoundMotionVoiceName").invoke());
          log(`ig=${ig} g=${g} id=${id} VOICE=[${voice}] MOTION=[${motion}]`);
          rows++;
        }
      }
      log(`=== DONE groups=${groups} rows=${rows} ===`);
    } catch (e: any) { log("DUMP ERR " + e + " " + (e.stack || "")); }
  });
}

function driver() {
  if (savedHandle && !dumped) { doDump(); return; }
  if (!dumped) setTimeout(driver, 1500);
}

log("=== START " + new Date().toISOString() + " ===");
Il2Cpp.perform(() => {
  try {
    const image = Il2Cpp.domain.assembly("Assembly-CSharp").image;
    const RDM = image.class("RawDataManager");
    const getSQLite = RDM.method("GetSQLite");
    log("hooking GetSQLite va=" + getSQLite.virtualAddress);
    Interceptor.attach(getSQLite.virtualAddress, {
      onEnter(args) { if (!savedHandle) savedHandle = args[0]; }  // 仅存指针,不阻塞游戏线程
    });
    log("hooked; driver polling on frida thread...");
    setTimeout(driver, 1500);
  } catch (e: any) { log("SETUP ERR " + e); }
});
