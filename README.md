# BD2 Spine 动画播放器

纯静态网站：用 Spine 官方 Web Player 在浏览器里实时渲染《棕色尘埃2》的角色骨骼动画。
全屏沉浸式播放，左缘滑出菜单（角色 → 服装 / 动作），双击切换全屏。

仅供个人学习研究使用，请勿公开传播游戏素材。

## 目录结构

```
bd2web/
├── index.html            页面（全部 UI 逻辑，无构建步骤）
├── vendor/               Spine Web Player 运行时（已本地化，离线可用）
├── data/roster.json      角色清单（由 tools/gen_roster.py 自动生成，勿手改）
├── upstream/             上游素材仓库的 sparse 克隆（只含 spine/ 目录，~2.8GB）
├── tools/
│   ├── sync.sh           同步素材 + 重新生成 roster（可重复执行）
│   └── gen_roster.py     扫描 upstream/spine 生成 data/roster.json
└── docker-compose.yml    nginx 静态服务
```

## 部署（家庭主机，需 Docker + git + python3）

```bash
# 1. 把整个 bd2web 目录拷到主机（或 git clone 代码 + 在主机上跑同步）
# 2. 首次同步素材（约 2.8GB，之后增量）
./tools/sync.sh
# 3. 启动
docker compose up -d
# 4. 浏览器打开 http://<主机IP>:8080
```

## 跟随上游更新

上游素材仓库（myssal/Brown-Dust-2-Asset）出新角色后，重跑一次同步即可，
新角色会自动出现在菜单里：

```bash
./tools/sync.sh
```

放进 crontab 每天自动同步（素材是静态文件，nginx 不需要重启）：

```cron
0 5 * * * /path/to/bd2web/tools/sync.sh >> /path/to/bd2web/sync.log 2>&1
```

## 换成 GitHub Pages 部署（可选）

仓库里只放代码（`upstream/` 不要提交），把 [index.html](index.html) 里的
`ASSET_BASE` 改成 jsDelivr 前缀：

```js
const ASSET_BASE = "https://cdn.jsdelivr.net/gh/myssal/Brown-Dust-2-Asset@<commit>/";
```

`data/roster.json` 需要在有素材的机器上生成后一并提交。

## 已知约定

- 素材为 Spine 4.1.x 导出，vendor 里的运行时必须保持 4.1，不能换 4.2+。
- 贴图为预乘 alpha（pma），播放器配置了 `premultipliedAlpha: true`；
  如果某套素材边缘发黑/发白，单独将该套改为 false。
- 上游目录命名：`char<AAAA><BB>`（AAAA=角色编号，BB=服装序号），
  cutscene 为 `cutscene_char<AAAA><BB>`；不符合此规律的目录会被 gen_roster 跳过。
- 角色/服装中文名暂缺：名字来自上游 `CharInfo(Dropped).json`（英文，且只覆盖部分角色），
  没有名字的角色显示为 `Char <编号>`。
