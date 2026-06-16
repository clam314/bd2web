# 优化清单（技能动画还原）

已从 APK 提取并固化的部分见 git 历史；以下为后续优化项，数据多在
`/Users/woods/bd2_gamedata_backup/`（13G bundle + catalog，含解析说明）。

## 待办

1. **运镜曲线（放大缩小/平移）** — 优先级中
   - 游戏技能是 Timeline `CharXXXXXX_Skill`，含 Animation Track 给 RectTransform 打的
     缩放/位移关键帧（"Recorded" 无限片段）。当前播放器是固定取景，没有运镜。
   - 难点：曲线存在 Unity 压缩二进制（m_MuscleClip / streamed clip），UnityPy typetree 读不到，
     需解 streamed 格式或 il2cpp 类型树。
   - 产出：每套服装一条相机关键帧 → 播放时驱动 player viewport 动画。

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

5. **后期精修** — 优先级低
   - 现用 CSS 近似（暗角 + brightness/contrast/saturate）。APK 真值：
     Bloom intensity 1.59/阈值 0.64/偏蓝 tint；Tonemapping ACES；
     ColorAdjustments 曝光 -0.3/对比 49/饱和 33。想更准可上 WebGL 后期 pass。
