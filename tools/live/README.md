# SDE 讲堂直播 · 交接说明

2026-08-08 立。取代原来的 `/meeting/` 会议室（meet.jit.si）。

## 为什么换掉会议室

原来那套的硬顶是 **meet.jit.si 公共实例约 75 人**，且主持人必须用
Google / GitHub / Facebook 登录才能开房——这两条在「100 人、学员在大陆」的目标下都过不去。
市面上的替代（腾讯会议、钉钉、飞书）要么被排除、要么免费版卡在 60 分钟、
要么不限时的年费五位数。

出路是**换形态**：SDE 讲课本来就是「1 讲 99 听」，不是 100 路对等视频。
改成单向直播之后，人数上限这件事从根上不存在了——100 人和 500 人对讲师端完全一样。

## 结构

```
讲师 OBS ──RTMP──> 新加坡 VPS（nginx-rtmp 切 HLS 6 秒分片）
                     │ rclone 每秒同步
                     ▼
                  R2 桶 sdeuniverses-pdf 的 live/ 前缀
                     │ 零 egress
                     ▼
        sdeuniverses.com/live/*（Worker 路由，见 src/worker.js）
                     │ 分片挂 immutable，100 人看同一片只回桶一次
                     ▼
        /meeting/ 页内 hls.js 播放器 —— 学生什么都不用装
```

## 桶里的三份文件（服务器写，网页只读）

| 键 | 谁写 | 缓存 | 作用 |
|---|---|---|---|
| `live/status.json` | `live-status.sh` | no-store | 开播状态、课程标题、下一课预告 |
| `live/stream.m3u8` | `live-sync.sh` 每秒 | no-store | HLS 播放列表 |
| `live/*.ts` | `live-sync.sh` 每秒 | immutable 一年 | 分片，只增不改 |
| `live/replays.json` | `live-archive.sh` | no-store | 回放清单 |
| `live/replay/*.mp4` | `live-archive.sh` | immutable 一年 | 整堂录像 |

**播放列表和分片的缓存必须分开设**——这是 HLS 最经典的坑：
播放列表若被边缘缓存住，学生会永远停在几分钟前那一段，而且不会自愈。

## 部署

新加坡 VPS（1C1G 最小档即可，约 $5–6/月）上：

```bash
bash setup-live.sh
```

跑完按提示填 R2 的 Access Key ID / Secret / Cloudflare 账号 ID
（Dashboard → R2 → Manage API Tokens，权限选 Object Read & Write）。
脚本会打印 OBS 用的服务器地址与串流密钥。

**机器规格为什么可以这么小**：这台机器只服务讲师那一路上行，
学生的 100 路全部由 Cloudflare 边缘扛。真正的分发压力从来没落到它头上。

## 每堂课的动作

1. （可选）改标题：`echo "SDE 本体论 · 第三讲" > /var/live/title.txt`
2. OBS 点「开始推流」→ 网页自动转直播态
3. 讲课；提问看 `/meeting/` 页的讨论区
4. OBS 点「停止推流」→ 网页自动转未开播态，录像自动进回放专区

## 已知取舍

- **延迟约 20–40 秒**，因此不设举手上麦；互动走讨论区文字。
  这是拿延迟换跨境稳定，参数在 `public/meeting/index.html` 的 `play()` 里
  （`lowLatencyMode:false` / `liveSyncDurationCount:6` / `maxBufferLength:60`），
  **别按「低延迟」的直觉去调**。
- **Worker 请求量**：一堂 2 小时 100 人的课约 30 万次
  （9 万次分片 + 18 万次播放列表轮询）。Workers 付费版 1000 万次/月 ≈ 每月 30 堂。
  真要归零，就把桶挂 R2 自定义域 `live.sdeuniverses.com` 并在 Dashboard 配 CORS，
  然后把页面里 `LIVE.base` 改成那个域名——一行的事，留着以后用。

## 改动过的文件

- `public/meeting/index.html` —— 整页重写为直播厅（原会议室版本已废）
- `public/assets/lib/hls.min.js` —— hls.js 1.5.20 自托管，按需加载
- `src/worker.js` —— 新增 `/live/*` 路由（R2_LIVE 段）
- `tools/sim_meeting_live.mjs` —— 脱机模拟，**改直播厅 JS 必须先跑它**
- `tools/sim_meeting_guest.mjs` —— 已删（测的是会议室时代的代码）
