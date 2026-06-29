import "frida-il2cpp-bridge";

const OUT = "/sdcard/Android/data/com.neowizgames.game.browndust2/files/table.log";
function log(s: string) { try { const f = new File(OUT, "a"); f.write(s + "\n"); f.flush(); f.close(); } catch (e) {} }

function readRepeated(row: Il2Cpp.Object, getter: string): string {
  try {
    const rf = row.method<Il2Cpp.Object>(getter).invoke();
    if (!rf || rf.handle.isNull()) return "";
    const n = rf.method<number>("get_Count").invoke();
    const out: string[] = [];
    for (let i = 0; i < n; i++) {
      const v = rf.method<Il2Cpp.String>("get_Item").invoke(i);
      out.push(v && !v.handle.isNull() ? (v.content ?? "") : "");
    }
    return out.join("|");
  } catch (e) { return ""; }
}

const seen: { [k: string]: boolean } = {};

Il2Cpp.perform(() => {
  try {
    const image = Il2Cpp.domain.assembly("Assembly-CSharp").image;
    const RDM = image.class("RawDataManager");
    // 一次性 dump 表结构(所有 get_* 字段),方便理解
    try {
      const SC = image.class("SpineInteractionPointTable");
      const fields = SC.methods.filter((m) => m.name.indexOf("get_") === 0 && m.parameterCount === 0).map((m) => m.name);
      log("FIELDS: " + fields.join(","));
    } catch (e: any) { log("introspect ERR " + e); }
    const names = ["GetSpineInteractionPointTables", "GetSpineInteractionPointTablesByInteractionPointGroup"];
    let hooked = 0;
    RDM.methods.forEach((mm) => {
      if (names.indexOf(mm.name) < 0) return;
      try {
        Interceptor.attach(mm.virtualAddress, {
          onLeave(retval) {
            try {
              if (retval.isNull()) return;
              const list = new Il2Cpp.Object(retval);
              const cnt = list.method<number>("get_Count").invoke();
              if (cnt <= 0) return;
              const r0 = list.method<Il2Cpp.Object>("get_Item").invoke(0);
              const ig0 = r0.method<number>("get_InteractionGroupId").invoke();
              const key = mm.name + ":" + ig0 + ":" + cnt;
              if (seen[key]) return;   // 同一张表只 dump 一次,避免重复阻塞
              seen[key] = true;
              for (let i = 0; i < cnt; i++) {
                const row = list.method<Il2Cpp.Object>("get_Item").invoke(i);
                if (!row || row.handle.isNull()) continue;
                const id = row.method<number>("get_Id").invoke();
                const ig = row.method<number>("get_InteractionGroupId").invoke();
                let g = -1; try { g = row.method<number>("get_GroupId").invoke(); } catch (e) {}
                const voice = readRepeated(row, "get_SoundVoiceName");
                const motion = readRepeated(row, "get_SoundMotionVoiceName");
                log(`ig=${ig} g=${g} id=${id} VOICE=[${voice}] MOTION=[${motion}]`);
              }
              log(`--- captured ${mm.name} group=${ig0} rows=${cnt} ---`);
            } catch (e: any) { log("onLeave ERR " + e); }
          }
        });
        hooked++;
        log("hooked " + mm.name);
      } catch (e: any) { log("hook fail " + mm.name + " " + e); }
    });
    log("=== READY hooked=" + hooked + " (Interceptor) 去切角色 ===");
  } catch (e: any) { log("SETUP ERR " + e); }
});
