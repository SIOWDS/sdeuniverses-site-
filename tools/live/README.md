# SDE 讲堂直播 · 交接说明

2026-08-08 立。取代原来的 `/meeting/` 会议室（meet.jit.si）。

## 为什么换掉会议室

原来那套的硬顶是 **meet.jit.si 公共实例约 75 人**，且主持人必须用
Google / GitHub / Facebook 登录才能开房——这两条在「100 人、学员在大陆」的目标下都过不去。
市面上的替代（腾讯会议、钉钉、飞书）要么被排除、要么免费版卡在 60 分钟、
要么不限时的年费五位数。

出路是**换形态**：SDE 讲课本来就是「1 讲 99 听」，不是 100 路对等视频。
改成单向直播之后，人数上限这件事从根上不存在了——100 人和 500 人对讲师端完全一样。

## 结构（v2，双码率）

```
讲师 OBS ─1080p RTMP─> 新加坡 VPS（2核4G）
                        ├─ 原画  -c copy 不重编码 ──┐
                        └─ 720p  转一路给网络差的 ──┤ nginx-rtmp 切 6 秒分片
                                                     │ rclone 每秒同步
                                                     ▼
                          R2 桶 sdeuniverses-pdf 的 live/ 前缀
                                                     │ 零 egress
                                                     ▼
              sdeuniverses.com/live/sde.m3u8（Worker 路由，见 src/worker.js）
                                                     │ 分片挂 immutable，200 人看同一片只回桶一次
                                                     ▼
              /meeting/ 页内 hls.js 播放器 —— 学生什么都不用装，网络差的自动降档
```

**最高档为什么不重编码**：讲师推什么清晰度学员就看到什么，中间一次都不重压。
屏幕共享和白板是高频锐边，任何一次转码都会把文字压糊且不可逆——
这是"PPT 看不清字"的真正原因，跟分辨率够不够无关。

**为什么只转一路**：两档而不是三档，是为了让 2 核机器跑得动
（一路 1080p→720p 的 x264 veryfast 约吃 1～1.5 核）。三档要 4 核，价钱翻倍。

## 桶里的三份文件（服务器写，网页只读）

| 键 | 谁写 | 缓存 | 作用 |
|---|---|---|---|
| `live/status.json` | `live-status.sh` | no-store | 开播状态、课程标题、下一课预告 |
| `live/sde.m3u8` | nginx 自动生成 | no-store | **主播放列表**（列出两个档） |
| `live/sde_hi/*`、`live/sde_mid/*` | `live-sync.sh` 每秒 | m3u8 no-store／ts immutable | 各档的子列表与分片 |
| `live/replays.json` | `live-archive.sh` | no-store | 回放清单 |
| `live/replay/*.mp4` | `live-archive.sh` | immutable 一年 | 整堂录像 |

**播放列表和分片的缓存必须分开设**——这是 HLS 最经典的坑：
播放列表若被边缘缓存住，学生会永远停在几分钟前那一段，而且不会自愈。

## 部署

新加坡 VPS（1C1G 最小档即可，约 $5–6/月）上：

```bash
bash setup-live.sh
```

机器规格：**2 核 4G**（Hetzner CPX22 新加坡一档即可）。转码只有一路，2 核有余量。

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


## 存储会自己长胖，已经装了闸

1080p 一堂课的分片约 4GB，一个月二十堂就是 80GB 往上累，且分片过了直播当下就没用了。
`/etc/cron.daily/sde-live-prune` 每天清一次桶里超过 24 小时的 `.ts`。
**`--include "*.ts"` 是护栏**：回放的 mp4 在 `live/replay/` 下，绝不能被这条扫掉——改这行前先想清楚。

## 200 人的账

- 分发：边缘 ＋ R2 零 egress，与人数无关。
- Worker 请求：2 小时 200 人约 50 万次/堂 → 付费版 1000 万/月 ≈ 每月 20 堂，够用。
- **人数再往上（500＋）就要把桶挂自定义域 `live.sdeuniverses.com`**（Dashboard 配 CORS，
  再改页面里 `LIVE.base` 一行），Worker 请求归零。现在还不必做。
