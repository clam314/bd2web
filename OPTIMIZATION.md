# 优化清单（技能动画还原）

已从 APK 提取并固化的部分见 git 历史；以下为后续优化项，数据多在
`/Users/woods/bd2_gamedata_backup/`（13G bundle + catalog，含解析说明）。

## 待办

1. **运镜曲线（放大缩小/平移）** — 数据已就绪，前端接入待办
   - 游戏技能是 Timeline `CharXXXXXX_Skill`，含 Animation Track 给 RectTransform 打的
     缩放/位移关键帧（"Recorded" 无限片段）。
   - **2026-06-17 突破**：StreamedClip 二进制格式按 AssetStudio 格式手解通了，
     `tools/extract_cutscene_shots.py` 已经把 154 个角色的真实运镜/Bg 切换/PostProcessVolume
     调色全部解出存 `data/cutscene_shots.json`（1.6M）。增量提取（bundle hash 做 key）。
   - **关键发现**：真实运镜比想象的简单——大多数角色只是 Anchors 的 X 慢平移
     + 在某个时间点硬切（Bg_A_shadow OFF + PostProcessVolume 切换）。
     之前做的程序化平滑 push-in + 段切震屏方向是错的，需要回退。
   - **2026-06-17**：
     - 接入 Timeline 后发现 Anchors.AnchoredX/Y 语义不统一：char000101 末尾用 5000/200000 把 UI
       容器"飞出屏幕"切回战斗 UI；char003803 主阶段是 0.7-0.87 的 normalized 值；真实平移
       （749→-787）在 loop_2 阶段。统一映射成 translate 会把角色推出可视区。
     - **当前**：translate 驱动已撤回，只保留 PostProcessVolume 调色切换（清晰可靠）。
       sentinel frame 已正确解为 t=0 基线（之前漏了，导致末段大数值被读为初始值）。
     - **下一步**：要做相机平移得先搞清"对每个角色哪个节点才是相机锚点"——可能
       要看 PlayableDirector 的绑定信息，或者用更针对性的启发式（按值域筛掉非相机轨）。

7. **多 SkeletonGraphic 实例叠播 cutscene** — **未解决，优先级高**
   - 2026-06-18 两轮 dump 才搞清结构：cutscene 不是单 skel，也不是"1 主 + 1 副"，而是**多 SkeletonGraphic 实例**
     按 Unity sibling 顺序叠 z-order。char003803_Skill 场景里就有 4 个 SG 实例（back/main/fx/front 四层），
     每个实例内部只播一条 spine track（同实例多 track 会 attachment 冲突）。
   - 之前三轮修复（commit `2927a7b` / `dd1f7fc` / `e75b372`）方向都错，靠近但都没修对。
   - 详细分析与正确方案见 **AGENTS.md「多 skel + 多实例 叠播 cutscene」** 段。
   - 待做：roster 加 cutscene.layers 列表 + index.html 按 layers 建 N 个 player + schedule 按 layerIdx 分发
     + 各 layer player 起播前清 slot.attachment 避免 setup pose 鬼影 + 共享主 skel cut_A∪cut_B 包围盒框对齐。

6. **char003803 黎维塔奇迹玫瑰"只剩腿脚"** — 已解决
   - 之前以为是部件化骨骼（小写 `a_arm*` 部件动画）缺失，写了 overlayTarget 的 `^[a-z]_` 分支
     去叠播——实际是误判：用 `strings` 提取 skel 时把 bone/slot 名字混进来当 anim 名了，
     这个角色其实只有 5 个动画（cut_A、cut_A_fx、cut_B、loop、loop_2）。
   - 真因：主链 `cut_A → cut_B → loop` 终止于 `loop`，而 `loop` 是横躺翻腾过渡帧；
     `loop_2` 才是站立 hero 终态。
   - **2026-06-17 修复**：`chainQueue` 改为跳过中间 loop，链尾用 bodies 里最后一个 loop
     （loop_2 优先于 loop），对所有角色生效。拉德尔验证渲染依然正常。
   - 小写部件分支（`^[a-z]_` 在 overlayTarget）保留，对其他真有部件化设计的角色可能有用。

2. **逐角色取景精修** — 优先级中
   - 现在 cutscene 用统一 1600 窗口、原点居中略上移（CUT_WIN/CUT_CX/CUT_CY，见 index.html）。
     这是 Luvencia 调出来的通用值，部分角色（骨骼原点位置不同）可能需要单独偏移。
   - 真实窗口 1600×720 + scale=1 已确认；逐角色差异主要在 spine 原点位置。
   - **立绘取景已修**（2026-06-16）：立绘形态曾因 spine 自动取景按整段动画并集，互动(motion)
     特效骨骼甩出导致人物被缩成小点。现已锁定到待机包围盒固定取景（详见 AGENTS.md「立绘取景锁定」）。
     可选精修：像 cutscene 那样从 APK 角色详情 prefab 的 RectTransform 挖立绘真实机位做像素级对齐。优先级低。

3. **场景背景接入全角色** — 优先级高（视觉影响大）
   - 代码已支持 `costume.bg`（index.html backgroundImage）。缺的是数据：
     每套服装的背景图。来源 gamekee content JSON 的 `bg` 字段（fetch_zh_names.py 已路过该字段）。
   - 落地：扩展 fetch 抓 bg URL → 下载到本地 bg/（家庭主机）；Pages 需解决托管（gamekee 防盗链）。

4. **粒子特效（水花/光线）** — 优先级低 / 可能不做
   - 游戏 Timeline 的 Control Track 触发 Unity ParticleSystem（如 0.35s 水爆、5.73s 光线）。
     网页 spine 框架无法播放，需 WebGL 粒子另写，投入产出比低。
   - **部分已解决（2026-06-16）**：制作者把光效/血花/武器轨迹/召唤物也做成了 spine 动画
     （与主 cut 共骨骼，不同插槽）。index.html `renderEntries` 现在把它们识别为 overlay
     并在 track 2+ 上与对应主 cut 同时播。剩下的纯 Unity 粒子（爆炸、火花粒子流）仍未覆盖。

5. **后期精修** — 优先级低
   - 现用 CSS 近似（暗角 + brightness/contrast/saturate）。APK 真值：
     Bloom intensity 1.59/阈值 0.64/偏蓝 tint；Tonemapping ACES；
     ColorAdjustments 曝光 -0.3/对比 49/饱和 33。想更准可上 WebGL 后期 pass。

8. **心契互动音频** — dating18 已完成并公开部署
   - `dating18` 是【尊爵不凡】致胜王牌莎赫拉查德（莎拉），资源编号 `char000396`；
     prefab 中禁用的 `Char067004` 字段是残留配置，不能作为映射依据。
   - 已确认 2026-06-18 更新后的语音、Visual_Novel_SFX、Master.strings、FMOD 事件图和
     FSB5/FADPCM 解码链路。
   - **2026-06-23 已完成第一阶段**：通用 FEV/FSB 提取工具、`data/dating_audio.json`、
     100 条 KR OGG、本地预载、真实多触发点时间轴、随机权重和切动作取消。
   - **语言策略最终确定：统一使用韩语 KR。** 不开发语言切换，也不托管多套语言。
     KR interaction bank 的事件、时间轴、随机权重和 100 个 waveform 完整可验证。
   - **2026-06-23 JP 全量审计**：扫描手机 86 个 `LocalVoice_JP` + 4 个 `LocalVisualNovel_JP`，
     对照 49 个 JP event GUID 和全部 FSB stream name；当前版本没有发布 `char000396` 心契日配。
     莎拉只有 26 条普通战斗/档案日语，不能拿来冒充互动语音。
   - 新增 `tools/audit_dating_jp_audio.py`；游戏更新后可自动重扫 GUID、sample 和 catalog。
   - JP 审计结论仅限当前版本，不代表未来不会补发；审计工具保留，但当前主线不等待 JP。
   - 已恢复 100 条 KR OGG 和完整 `data/dating_audio.json` 播放映射。
   - **2026-06-23 SFX 已完整接入**：112 个事件、670 个时间触发点、127 个直接引用 sample
     和 117 个动画映射；保留真实时间轴、播放窗口与每个随机池的权重。
   - 127 个 sample 中含 10 个角色专属音效，以及公共衣料、液体、碰撞、挥动等音效。
     审计确认目标 Timeline 的 670 个 instrument 全部属于已解析的 WAIT/MUIT，没有猜测未知结构。
   - FSB 没有内嵌无限循环点；`*_loop` 事件使用有限音频片段。voice/SFX 使用独立音量总线，
     共用动画起点和取消生命周期，切动作时会停止旧 source。
   - 100 条 KR voice + 127 条 SFX OGG 合计约 4.9 MB，已允许进入公开仓库并由 GitHub Pages
     同源提供；资源缺失时仍无声降级。
   - 后续任务是把同一生成流程扩展到其他心契角色，不再为 dating18 单独补音频结构。

9. **心契素材 CDN 容错** — 2026-06-23 已修
   - 心契页现在会在创建 SpinePlayer 前检查 skeleton、atlas 和全部贴图页；整套不可用就换镜像。
   - 移除会跳转 HTTP 的 statically，补齐 BunnyCDN / Cloudflare testing 镜像。
   - 半加载播放器采用安全销毁，旧请求用 generation 隔离。
   - 已用 404 首源故障注入验证：自动切到本地次源，控制台无残留异常。
   - 详细结论见 [CODEX_CHANGES.md](CODEX_CHANGES.md) 的
     “2026-06-22 心契音频资源分析与通用接入方案”。
