import "frida-il2cpp-bridge";

const OUT = "/sdcard/Android/data/com.neowizgames.game.browndust2/files/avatar_motion_table.log";
let SHOULD_SCAN_GETTER = false;

function log(s: string) {
  try {
    const f = new File(OUT, "a");
    f.write(s + "\n");
    f.flush();
    f.close();
  } catch (e) {}
}

function readString(row: Il2Cpp.Object, getter: string): string {
  try {
    const v = row.method<Il2Cpp.String>(getter).invoke();
    return v && !v.handle.isNull() ? (v.content ?? "") : "";
  } catch (e) {
    return "";
  }
}

function readInt(row: Il2Cpp.Object, getter: string): number | null {
  try {
    return row.method<number>(getter).invoke();
  } catch (e) {
    return null;
  }
}

function readRepeatedString(row: Il2Cpp.Object, getter: string): string {
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
  } catch (e) {
    return "";
  }
}

log("=== AvatarMotionTable script loaded " + new Date().toISOString() + " ===");
setTimeout(() => {
  try {
    const m = Process.findModuleByName("libil2cpp.so");
    log("diagnostic libil2cpp=" + (m ? `${m.base} size=${m.size}` : "NULL"));
  } catch (e: any) {
    log("diagnostic ERR " + e);
  }
}, 3000);

function rowText(id: number, row: Il2Cpp.Object): string {
  const fields: string[] = [];
  const simple = [
    "get_Id",
    "get_DefaultAvatarCharId",
    "get_IsInteraction",
    "get_IsHidden",
    "get_MaxCount",
    "get_MotionType",
    "get_MotionNameTextId",
    "get_MotionDescNameTextId",
  ];
  for (const g of simple) {
    const v = readInt(row, g);
    if (v !== null) fields.push(`${g.substring(4)}=${v}`);
  }
  const strings = [
    "get_MotionResourcePath",
    "get_SoundVoicePath",
    "get_SoundEffectPath",
    "get_MotionIconName",
    "get_BgmPath",
  ];
  for (const g of strings) {
    const v = readString(row, g);
    if (v) fields.push(`${g.substring(4)}=${v}`);
  }
  const ex = readRepeatedString(row, "get_ExceptionSoundVoicePath");
  if (ex) fields.push(`ExceptionSoundVoicePath=[${ex}]`);
  return `key=${id} ${fields.join("  ")}`;
}

function objInfo(o: any): string {
  try {
    if (!o) return "null";
    if (o.handle && o.handle.isNull()) return "NULL_HANDLE";
    const cls = o.class ? o.class.name : "?";
    return `${cls}@${o.handle || o}`;
  } catch (e) {
    return String(o);
  }
}

function tryDumpCache(extensionClass: Il2Cpp.Class) {
  log("=== AvatarMotion static cache probe ===");
  try {
    log(
      "EXT FIELDS " +
        extensionClass.fields
          .map((f) => `${f.name}:${f.type.name}:static=${f.isStatic}`)
          .join(",")
    );
  } catch (e: any) {
    log("EXT FIELDS ERR " + e);
  }

  const cacheField = extensionClass.fields.find(
    (f) => f.name === "ὬὧὢὣὣὥὢὩὦὮὪ" || /AvatarMotionTable/.test(f.type.name)
  );
  if (!cacheField) {
    log("NO AvatarMotion cache field");
    return;
  }
  log(`CACHE FIELD name=${cacheField.name} type=${cacheField.type.name}`);

  let cache: Il2Cpp.Object | null = null;
  try {
    cache = cacheField.value as Il2Cpp.Object;
    log("CACHE OBJ " + objInfo(cache));
  } catch (e: any) {
    log("CACHE READ ERR " + e);
    return;
  }
  if (!cache || cache.handle.isNull()) return;

  try {
    log(
      "CACHE METHODS " +
        cache.class.methods
          .filter((m) => m.parameterCount <= 1)
          .map((m) => `${m.name}/${m.parameterCount}:${m.returnType.name}`)
          .join(",")
    );
  } catch (e: any) {
    log("CACHE METHODS ERR " + e);
  }
  try {
    log(
      "CACHE FIELDS " +
        cache.class.fields.map((f) => `${f.name}:${f.type.name}`).join(",")
    );
  } catch (e: any) {
    log("CACHE FIELDS ERR " + e);
  }

  for (const fname of ["ὡὣὫὨὮὩὯὧὡὫὤ", "ὬὮὬὥὡὡὧὮὩὥὦ"]) {
    try {
      const inner = cache.field<Il2Cpp.Object>(fname).value;
      log(`INNER ${fname} ${objInfo(inner)}`);
      if (!inner || inner.handle.isNull()) continue;
      try {
        log(`INNER ${fname} count=${inner.method<number>("get_Count").invoke()}`);
      } catch (e: any) {
        log(`INNER ${fname} count ERR ${e}`);
      }
      try {
        log(
          `INNER ${fname} methods=` +
            inner.class.methods
              .filter((m) => m.parameterCount <= 1)
              .slice(0, 80)
              .map((m) => `${m.name}/${m.parameterCount}:${m.returnType.name}`)
              .join(",")
        );
      } catch (e: any) {
        log(`INNER ${fname} methods ERR ${e}`);
      }
    } catch (e: any) {
      log(`INNER ${fname} ERR ${e}`);
    }
  }
}

function getAvatarMotionCache(extensionClass: Il2Cpp.Class): Il2Cpp.Object | null {
  try {
    const cacheField = extensionClass.fields.find(
      (f) => f.name === "ὬὧὢὣὣὥὢὩὦὮὪ" || /AvatarMotionTable/.test(f.type.name)
    );
    if (!cacheField) return null;
    const cache = cacheField.value as Il2Cpp.Object;
    if (!cache || cache.handle.isNull()) return null;
    return cache;
  } catch (e) {
    return null;
  }
}

Il2Cpp.perform(() => {
  try {
    const image = Il2Cpp.domain.assembly("Assembly-CSharp").image;
    const avatarMotion = image.classes.find(
      (c) => c.name === "AvatarMotionTable" || c.name.endsWith(".AvatarMotionTable")
    );
    if (!avatarMotion) {
      log(
        "NO AvatarMotionTable class; sample classes=" +
          image.classes
            .filter((c) => /AvatarMotion/i.test(c.name))
            .map((c) => c.name)
            .join(",")
      );
      return;
    }
    log("=== AvatarMotionTable dump start " + new Date().toISOString() + " ===");
    log(
      "FIELDS " +
        avatarMotion.methods
          .filter((m) => m.name.indexOf("get_") === 0 && m.parameterCount === 0)
          .map((m) => m.name)
          .join(",")
    );

    const extensionClass = image.classes.find((c) =>
      c.fields.some((f) => /AvatarMotionTable/.test(f.type.name))
    );
    if (extensionClass) {
      log(`EXT CAND class=${extensionClass.name}`);
      tryDumpCache(extensionClass);
    } else {
      log("NO EXTENSION CLASS WITH AvatarMotionTable FIELD");
    }

    const candidates: Il2Cpp.Method[] = [];
    for (const klass of image.classes) {
      for (const m of klass.methods) {
        try {
          if (m.parameterCount !== 1) continue;
          if (!m.isStatic) continue;
          if (
            m.returnType.name !== "AvatarMotionTable" &&
            !m.returnType.name.endsWith(".AvatarMotionTable")
          )
            continue;
          candidates.push(m);
          log(
            `CAND class=${klass.name} method=${m.name} va=${m.virtualAddress} ret=${m.returnType.name}`
          );
        } catch (e) {}
      }
    }
    log(`candidate count=${candidates.length}`);
    if (candidates.length === 0) {
      log("NO CANDIDATE");
      return;
    }

    if (!SHOULD_SCAN_GETTER) {
      log("SKIP getter scan because cache is null-prone; passive watch enabled");
      if (extensionClass) {
        let ticks = 0;
        const timer = setInterval(() => {
          ticks++;
          try {
            const cache = getAvatarMotionCache(extensionClass);
            log(`WATCH tick=${ticks} cache=${objInfo(cache)}`);
            if (cache && !cache.handle.isNull()) {
              tryDumpCache(extensionClass);
              clearInterval(timer);
            }
            if (ticks >= 60) clearInterval(timer);
          } catch (e: any) {
            log("WATCH ERR " + e);
          }
        }, 5000);
      }
      return;
    }

    log("getter scan disabled by default");
  } catch (e: any) {
    log("SETUP ERR " + e + " " + (e.stack || ""));
  }
}).catch((e: any) => {
  log("Il2Cpp.perform ERR " + e + " " + (e && e.stack ? e.stack : ""));
});
