import "frida-il2cpp-bridge";

const OUT = "/sdcard/Android/data/com.neowizgames.game.browndust2/files/trace_spine_animation.log";

function log(line: string) {
  try {
    const f = new File(OUT, "a");
    f.write(`${new Date().toISOString()} ${line}\n`);
    f.flush();
    f.close();
  } catch (e) {}
}

function ptrFieldInt(p: NativePointer, offset: number): number {
  try { return p.add(offset).readS32(); } catch (e) { return -9999; }
}

function ptrFieldBool(p: NativePointer, offset: number): number {
  try { return p.add(offset).readU8(); } catch (e) { return 255; }
}

function pointInfo(p: NativePointer): string {
  if (!p || p.isNull()) return "point=NULL";
  return [
    `gid=${ptrFieldInt(p, 0x30)}`,
    `id=${ptrFieldInt(p, 0x34)}`,
    `tool=${ptrFieldInt(p, 0x38)}`,
    `type=${ptrFieldInt(p, 0x3c)}`,
    `dragOk=${ptrFieldBool(p, 0x160)}`,
    `dragIndex=${ptrFieldInt(p, 0x164)}`,
  ].join(" ");
}

function il2String(p: NativePointer): string {
  try {
    if (!p || p.isNull()) return "";
    return new Il2Cpp.String(p).content ?? "";
  } catch (e: any) {
    return `<str err ${e}>`;
  }
}

function hookRva(
  name: string,
  rva: number,
  cb: (args: InvocationArguments) => string,
  leaveCb?: (retval: InvocationReturnValue, state: any) => string,
) {
  try {
    const base = Process.getModuleByName("libil2cpp.so").base;
    Interceptor.attach(base.add(rva), {
      onEnter(args) {
        (this as any)._traceState = { self: args[0] };
        try { log(`${name}:enter ${cb(args)}`); } catch (e: any) { log(`${name}:enter ERR ${e}`); }
      },
      onLeave(retval) {
        if (!leaveCb) return;
        try { log(`${name}:leave ${leaveCb(retval, (this as any)._traceState)}`); } catch (e: any) { log(`${name}:leave ERR ${e}`); }
      },
    });
    log(`hooked ${name} rva=0x${rva.toString(16)}`);
  } catch (e: any) {
    log(`hook fail ${name} ${e}`);
  }
}

function hookMethodGroup(className: string, methodNames: string[], pointArgIndex: number) {
  try {
    const image = Il2Cpp.domain.assembly("Assembly-CSharp").image;
    const klass = image.class(className);
    const wanted = new Set(methodNames);
    for (const m of klass.methods) {
      if (!wanted.has(m.name)) continue;
      try {
        Interceptor.attach(m.virtualAddress, {
          onEnter(args) {
            const point = args[pointArgIndex];
            (this as any)._traceState = { point };
            log(`${className}.${m.name}/${m.parameterCount}:enter ${pointInfo(point)}`);
          },
          onLeave() {
            const point = (this as any)._traceState?.point;
            log(`${className}.${m.name}/${m.parameterCount}:leave ${pointInfo(point)}`);
          },
        });
        log(`hooked ${className}.${m.name}/${m.parameterCount} ${m.virtualAddress}`);
      } catch (e: any) {
        log(`hook fail ${className}.${m.name}/${m.parameterCount} ${e}`);
      }
    }
  } catch (e: any) {
    log(`class method hook setup ERR ${className} ${e}`);
  }
}

Il2Cpp.perform(() => {
  log("=== trace spine animation loaded ===");

  try {
    const image = Il2Cpp.domain.assembly("Assembly-CSharp").image;
    const spineObj = image.class("SpineAnimationObject");
    for (const m of spineObj.methods) {
      if (m.name !== "SetSpineAnimationExternal" && m.name !== "AddSpineAnimationExternal") continue;
      try {
        Interceptor.attach(m.virtualAddress, {
          onEnter(args) {
            const anim = il2String(args[1]);
            const track = m.parameterCount >= 2 ? args[2].toInt32() : -1;
            const loop = m.parameterCount >= 3 ? args[3].toInt32() : -1;
            log(`SpineAnimationObject.${m.name}/${m.parameterCount} anim=${anim} track=${track} loop=${loop}`);
          },
        });
        log(`hooked SpineAnimationObject.${m.name}/${m.parameterCount} ${m.virtualAddress}`);
      } catch (e: any) {
        log(`hook fail SpineAnimationObject.${m.name}/${m.parameterCount} ${e}`);
      }
    }
  } catch (e: any) {
    log(`class hook setup ERR ${e}`);
  }

  hookMethodGroup("SpineInteractionPoint", [
    "OnPointerDown",
    "OnPointerUp",
    "OnBeginDrag",
    "OnEndDrag",
    "OnDrag",
    "OnDragInReplay",
  ], 0);
  hookMethodGroup("SpineInteractionActionController", [
    "OnBeginDragInteraction",
    "OnEndDragInteraction",
    "OnSetMixAnimation",
    "OnCompletedMixAnimation",
  ], 1);

  hookRva("Point.OnBeginDrag.rva", 0x4d2b194, (args) => pointInfo(args[0]), (_ret, s) => pointInfo(s.self));
  hookRva("Point.OnEndDrag.rva", 0x4d27d4c, (args) => pointInfo(args[0]), (_ret, s) => pointInfo(s.self));
  hookRva("Point.OnDragCore.rva", 0x4d23f84, (args) => pointInfo(args[0]), (_ret, s) => pointInfo(s.self));
  hookRva("Point.OnDragPointer.rva", 0x4d2a014, (args) => pointInfo(args[0]), (_ret, s) => pointInfo(s.self));
});
