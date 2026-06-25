// 被动列读取 hook:只记录,不调用任何 il2cpp 方法 → 安全不卡不崩
var EXT="/sdcard/Android/data/com.neowizgames.game.browndust2/files/";
function logf(m){try{var f=new File(EXT+"voice.log","a");f.write(m+"\n");f.flush();f.close();}catch(e){}}
function rstr(p){try{if(p.isNull())return null;var n=p.add(0x10).readS32();if(n<0||n>8192)return null;return p.add(0x14).readUtf16String(n);}catch(e){return null;}}
logf("[SAFE] loaded "+Date.now());
function go(){
  var m=Process.findModuleByName("libil2cpp.so"); if(!m){setTimeout(go,500);return;}
  var addr=m.base.add(0x6CD45C4); // 列文本读取方法
  Interceptor.attach(addr,{ onLeave(r){ try{var s=rstr(ptr(r)); if(s && /Char[0-9]{6}|_Int_|Joy|Smile|Sigh|Surprise|Shout|Excit|Sad|Anger|Pain|Voice|interaction_char/i.test(s)) logf("[V] "+s);}catch(e){} } });
  logf("[SAFE] hooked column-reader @"+addr);
}
go();
