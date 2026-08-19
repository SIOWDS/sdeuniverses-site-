#!/usr/bin/env bash
# ============================================================================
# SDE 讲堂 · 直播服务器一键部署 v2（Ubuntu 22.04/24.04，新加坡节点，2 核 4G）
#
#   OBS ─1080p SRT──> ffmpeg 收 ─> nginx-rtmp ─┬─ 原画  直接复制，不重编码（零 CPU）
#                                 └─ 720p  转一路给网络差的学员
#                                        │ 切 HLS 6 秒分片
#                                        ▼
#                             rclone 每秒同步 ──> R2 桶 live/
#                                        └──> sdeuniverses.com/live/sde.m3u8
#
# 跑法（root 或 sudo）：  bash setup-live.sh
#
# ── 为什么是这个形状 ───────────────────────────────────────────────────────
# · **最高档不重编码**（-c copy）。讲师推什么清晰度，学员就看到什么清晰度，
#   中间一次都不重压——这是"屏幕共享和白板要非常清晰"唯一靠得住的做法。
#   任何一次转码都会把 PPT 文字的锐边压糊，且不可逆。
# · **只转一路 720p**。两档而不是三档，是为了让 2 核机器跑得动：
#   一路 1080p→720p 的 x264 veryfast 约吃 1～1.5 核，2 核有余量；三档就要 4 核。
# · **学员的 200 路不落到这台机器上**——它只服务讲师那一路上行，
#   分发全部由 Cloudflare 边缘扛。所以机器可以这么小。
# · **入口用 SRT 不用 RTMP**。讲师走的是 eSIM 漫游（蜂窝网络），特点不是慢而是**抖**：
#   RTMP 跑在 TCP 上，一丢包就重传、OBS 立刻掉帧，两百人一起卡。
#   SRT 是专为不稳定链路设计的（自带前向纠错与重传窗口），把丢包在最脆弱的那一跳就吃掉。
#   进来之后 `-c copy` 原样转成 RTMP 喂给本机 nginx，**全程零重编码**，清晰度一点不损。
#   RTMP 端口仍然开着作后备——SRT 万一不通，改回 RTMP 就能开课，不至于停摆。
# ============================================================================
set -euo pipefail

STREAM_KEY="${STREAM_KEY:-$(head -c 18 /dev/urandom | base64 | tr -d '/+=' | head -c 24)}"
# SRT 用口令加密而不是靠密钥字符串，长度必须 10–79 位
SRT_PASS="${SRT_PASS:-$(head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 32)}"
LIVE_DIR=/var/live
HLS_DIR=$LIVE_DIR/hls
REC_DIR=$LIVE_DIR/rec

echo "==> 1/8 装 nginx-rtmp、ffmpeg、rclone"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq libnginx-mod-rtmp nginx ffmpeg rclone jq curl

# ⚠ 发行版的 ffmpeg 不一定编进了 libsrt。缺了的话 SRT 那条通道会静默失效，
#   而症状只是"OBS 推不上去"，开课当天才发现就晚了——所以现在就查。
if ! ffmpeg -hide_banner -protocols 2>/dev/null | grep -qw srt; then
  echo "!! 这台机器的 ffmpeg 不支持 SRT。"
  echo "   先跑：apt-get install -y libsrt1.5-openssl  然后换一个带 SRT 的 ffmpeg 版本，"
  echo "   或者先用 RTMP 通道开课（脚本尾部会打印 RTMP 的地址）。"
  echo "   现在继续安装，SRT 那一路会装但起不来。"
fi

mkdir -p "$HLS_DIR" "$REC_DIR"
chown -R www-data:www-data "$LIVE_DIR"

echo "==> 2/8 写 nginx-rtmp 配置（双码率）"
cat > /etc/nginx/rtmp.conf <<NGINX
rtmp {
  server {
    listen 1935;
    chunk_size 4096;

    # ── 讲师推到这里 ──────────────────────────────────────────────
    application live {
      live on;
      record all;
      record_path $REC_DIR;
      record_unique on;
      record_suffix _%Y%m%d-%H%M%S.flv;

      # 串流密钥不对就拒收
      on_publish http://127.0.0.1:8088/auth;
      exec_publish_done /usr/local/bin/live-stop.sh;

      # 收到推流后立刻分成两路，都送进下面的 show。
      # ⚠ 目标名写死成 sde_hi / sde_mid，**不带 \$name**——
      #   \$name 就是串流密钥，带进去等于把密钥暴露在学员看得见的 URL 路径里。
      exec_push ffmpeg -nostdin -loglevel error -i rtmp://127.0.0.1/live/\$name
        -c copy -f flv rtmp://127.0.0.1/show/sde_hi
        -c:a aac -b:a 96k -ac 2
        -c:v libx264 -preset veryfast -profile:v main -tune zerolatency
        -b:v 1500k -maxrate 1600k -bufsize 3000k -vf scale=-2:720
        -g 50 -keyint_min 50 -sc_threshold 0
        -f flv rtmp://127.0.0.1/show/sde_mid;
    }

    # ── 切片与生成多码率播放列表 ──────────────────────────────────
    application show {
      live on;
      allow publish 127.0.0.1;
      deny publish all;

      hls on;
      hls_path $HLS_DIR;
      hls_nested on;
      # 6 秒分片。⚠ 别为"低延迟"压到 1–2 秒：跨境网络下分片越碎越容易卡，
      #   而讲课本来就不需要实时——延迟是拿来换稳的。
      hls_fragment 6s;
      hls_playlist_length 120s;
      hls_continuous on;
      hls_cleanup on;

      # 这两行让 nginx 自动生成主播放列表 $HLS_DIR/sde.m3u8，
      # 播放器据此在两档之间自动切换（网络差的自动降到 720p，不是卡死）。
      hls_variant _hi  BANDWIDTH=4800000,RESOLUTION=1920x1080;
      hls_variant _mid BANDWIDTH=1700000,RESOLUTION=1280x720;

      exec_publish /usr/local/bin/live-start.sh;
    }
  }
}
NGINX

grep -q 'include /etc/nginx/rtmp.conf;' /etc/nginx/nginx.conf \
  || echo 'include /etc/nginx/rtmp.conf;' >> /etc/nginx/nginx.conf

echo "==> 3/8 串流密钥校验（只在本机监听）"
cat > /usr/local/bin/live-auth.py <<'PY'
#!/usr/bin/env python3
# 极小的 on_publish 校验：串流密钥不对就拒绝推流（返回非 2xx）。
import http.server, urllib.parse, os
KEY = os.environ.get("STREAM_KEY", "")
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("content-length", 0) or 0)
        q = urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8", "ignore"))
        self.send_response(200 if q.get("name", [""])[0] == KEY else 403)
        self.end_headers()
    def log_message(self, *a): pass
http.server.HTTPServer(("127.0.0.1", 8088), H).serve_forever()
PY
chmod +x /usr/local/bin/live-auth.py

cat > /etc/systemd/system/live-auth.service <<UNIT
[Unit]
Description=SDE live stream key auth
[Service]
Environment=STREAM_KEY=$STREAM_KEY
ExecStart=/usr/bin/python3 /usr/local/bin/live-auth.py
Restart=always
[Install]
WantedBy=multi-user.target
UNIT

echo "==> 4/8 SRT 接收口（讲师主用通道）"
# ffmpeg 以 listener 模式蹲在 10080 端口收 SRT，收到就原样转成 RTMP 喂给本机 nginx。
#  · latency=2000000（2 秒，单位微秒）是给蜂窝网络留的重传窗口——
#    留小了丢包救不回来，留大了徒增延迟；两小时的课延迟多两秒毫无影响，所以宁可留足。
#  · passphrase 直接把链路加密了，比 RTMP 那种明文推流密钥更稳妥。
#  · 没人推流时 ffmpeg 会退出，靠 Restart=always 反复蹲守，这是正常状态、不是故障。
cat > /usr/local/bin/live-srt.sh <<SH
#!/usr/bin/env bash
exec ffmpeg -nostdin -loglevel warning \
  -mode listener -i "srt://0.0.0.0:10080?mode=listener&latency=2000000&passphrase=$SRT_PASS" \
  -c copy -f flv "rtmp://127.0.0.1/live/$STREAM_KEY"
SH
chmod +x /usr/local/bin/live-srt.sh

cat > /etc/systemd/system/live-srt.service <<'UNIT'
[Unit]
Description=SDE live SRT ingest
[Service]
ExecStart=/usr/local/bin/live-srt.sh
Restart=always
RestartSec=2
[Install]
WantedBy=multi-user.target
UNIT

# 只开这两个入口，其余不动
command -v ufw >/dev/null 2>&1 && { ufw allow 10080/udp >/dev/null 2>&1 || true; ufw allow 1935/tcp >/dev/null 2>&1 || true; }

echo "==> 5/8 配 rclone 连 R2"
echo "    去 Cloudflare Dashboard → R2 → Manage API Tokens 建一个 Object Read & Write 的令牌"
read -rp "    R2 Access Key ID: " R2_ID
read -rsp "    R2 Secret Access Key: " R2_SECRET; echo
read -rp "    Cloudflare 账号 ID（R2 概览页右侧）: " CF_ACCT

mkdir -p /root/.config/rclone
cat > /root/.config/rclone/rclone.conf <<CONF
[r2]
type = s3
provider = Cloudflare
access_key_id = $R2_ID
secret_access_key = $R2_SECRET
endpoint = https://$CF_ACCT.r2.cloudflarestorage.com
acl = private
no_check_bucket = true
CONF
chmod 600 /root/.config/rclone/rclone.conf

echo "==> 6/8 开播/下课钩子与分片同步"
cat > /usr/local/bin/live-status.sh <<'SH'
#!/usr/bin/env bash
# 改写 status.json 并立刻推进桶。网页每 15 秒问一次它，据此切开播/未开播。
set -euo pipefail
LIVE=$1
TITLE=$(cat /var/live/title.txt 2>/dev/null || echo "SDE 讲堂")
NEXT=$(cat /var/live/next.json 2>/dev/null || echo 'null')
STAMP=$(date '+%H:%M')
cat > /var/live/status.json <<JSON
{"live":$LIVE,"title":"$TITLE","startedAt":"$STAMP","playlist":"sde.m3u8","next":$NEXT}
JSON
rclone copyto /var/live/status.json r2:sdeuniverses-pdf/live/status.json \
  --s3-no-check-bucket --header-upload "Cache-Control: no-store" >/dev/null 2>&1 || true
SH
chmod +x /usr/local/bin/live-status.sh

cat > /usr/local/bin/live-start.sh <<'SH'
#!/usr/bin/env bash
# 由 show 里任一路开始切片时触发（会触发两次，幂等无所谓）。
# ⚠ 先让分片跑起来再宣布开播：反过来的话学员在有画面之前就被放进播放器，只会看到转圈。
systemctl start live-sync.service
sleep 12
/usr/local/bin/live-status.sh true
SH

cat > /usr/local/bin/live-stop.sh <<'SH'
#!/usr/bin/env bash
# 先把最后几片传完再改状态：反过来的话网页已显示未开播、最后几片还在传，画面会突然截断。
sleep 10
systemctl stop live-sync.service || true
/usr/local/bin/live-status.sh false
/usr/local/bin/live-archive.sh &
SH
chmod +x /usr/local/bin/live-start.sh /usr/local/bin/live-stop.sh

cat > /usr/local/bin/live-sync.sh <<'SH'
#!/usr/bin/env bash
# 每秒把新分片和最新播放列表推进桶。
#  · 分片（.ts）：写出后永不改动 → --ignore-existing 永不重传，且挂 immutable 一年
#  · 播放列表（.m3u8）：每次都要覆盖，且必须 no-store
#    ——播放列表要是被缓存住，学员会永远停在几分钟前那一段，而且不会自愈。
#      这是 HLS 最经典的坑，两种文件的缓存头绝不能设成一样。
set -uo pipefail
while true; do
  rclone copy /var/live/hls r2:sdeuniverses-pdf/live \
    --include "*.ts" --ignore-existing --transfers 12 --s3-no-check-bucket \
    --header-upload "Cache-Control: public, max-age=31536000, immutable" >/dev/null 2>&1
  rclone copy /var/live/hls r2:sdeuniverses-pdf/live \
    --include "*.m3u8" --s3-no-check-bucket \
    --header-upload "Cache-Control: no-store" >/dev/null 2>&1
  sleep 1
done
SH
chmod +x /usr/local/bin/live-sync.sh

cat > /etc/systemd/system/live-sync.service <<'UNIT'
[Unit]
Description=SDE live HLS sync to R2
[Service]
ExecStart=/usr/local/bin/live-sync.sh
Restart=always
UNIT

cat > /usr/local/bin/live-archive.sh <<'SH'
#!/usr/bin/env bash
# 下课后：把 nginx 录的原画 flv 转成 mp4 推进桶，并往 replays.json 加一条。
# 录的是**推流原画**（未经 720p 那一路），所以回放和现场一样清晰。
set -uo pipefail
LATEST=$(ls -t /var/live/rec/*.flv 2>/dev/null | head -1) || exit 0
[ -z "$LATEST" ] && exit 0
DAY=$(date '+%Y%m%d'); OUT=/var/live/rec/$DAY.mp4
ffmpeg -y -i "$LATEST" -c copy -movflags +faststart "$OUT" >/dev/null 2>&1 || exit 0
rclone copyto "$OUT" "r2:sdeuniverses-pdf/live/replay/$DAY.mp4" --s3-no-check-bucket \
  --header-upload "Cache-Control: public, max-age=31536000, immutable" >/dev/null 2>&1
TITLE=$(cat /var/live/title.txt 2>/dev/null || echo "SDE 讲堂")
rclone copyto r2:sdeuniverses-pdf/live/replays.json /var/live/replays.json --s3-no-check-bucket >/dev/null 2>&1 \
  || echo '{"items":[]}' > /var/live/replays.json
jq --arg t "$TITLE" --arg d "$(date '+%Y-%m-%d')" --arg u "/live/replay/$DAY.mp4" \
   '.items = ([{title:$t,date:$d,url:$u}] + (.items//[]))' \
   /var/live/replays.json > /var/live/replays.new.json && mv /var/live/replays.new.json /var/live/replays.json
rclone copyto /var/live/replays.json r2:sdeuniverses-pdf/live/replays.json --s3-no-check-bucket \
  --header-upload "Cache-Control: no-store" >/dev/null 2>&1
rm -f "$LATEST"
SH
chmod +x /usr/local/bin/live-archive.sh

echo "==> 7/8 每天清一次桶里的旧分片（不清回放）"
# 分片只在直播当下有用，留着就是白付存储费：1080p 一堂课约 4GB，一个月二十堂就是 80GB 往上累。
# ⚠ --include "*.ts" 是护栏：回放的 mp4 在 live/replay/ 下，绝不能被这条扫掉。
cat > /etc/cron.daily/sde-live-prune <<'CRON'
#!/bin/sh
rclone delete r2:sdeuniverses-pdf/live --include "*.ts" --min-age 24h --s3-no-check-bucket >/dev/null 2>&1
CRON
chmod +x /etc/cron.daily/sde-live-prune

echo "==> 8/8 起服务"
systemctl daemon-reload
systemctl enable --now live-auth.service live-srt.service
nginx -t && systemctl restart nginx
/usr/local/bin/live-status.sh false

IP=$(curl -s4 ifconfig.me || echo "<本机公网IP>")
cat <<DONE

============================================================
 装好了。

 ── OBS 推流设置（设置 → 直播 → 服务「自定义」）──
   **主用（SRT，抗抖动，走你的 eSIM 就用这条）**
     服务器      srt://$IP:10080?latency=2000000&passphrase=$SRT_PASS
     串流密钥    留空

   **后备（RTMP，SRT 万一不通时用）**
     服务器      rtmp://$IP/live
     串流密钥    $STREAM_KEY

 ⚠ 上面两行都等于开课权限，只留在讲师那台电脑上，不要发群里。

 ── OBS 输出设置（设置 → 输出 → 输出模式「高级」→ 串流）──
   编码器        优先选 QuickSync H.264 或 NVENC H.264（硬件编码，几乎不占 CPU）
                 都没有再退回 x264 + veryfast
   码率控制      CBR
   关键帧间隔    2 秒          ← 必须是 2，HLS 靠它对齐分片
   配置(Profile) high

 ── 必须打开这一项 ──
   设置 → 高级 → 网络 → **勾选「动态改变码率以管理拥塞」**
   蜂窝网络一波动，它会自动降码率而不是掉帧。
   这一项对 eSIM 漫游是决定性的，不开则前功尽弃。

 ── 两个场景，两套参数（设置 → 视频，讲课时切）──
   讲人：   1920x1080 / 25 fps / 2500 Kbps
   讲 PPT 或白板：
            1920x1080 / 20 fps / 3500 Kbps
            —— 帧率降下来，把码率全给清晰度。
               文字是锐边，最怕码率不够；笔迹不需要每秒 30 帧。
   ⚠ 输出分辨率必须和你屏幕一致（1080p 屏就填 1920x1080）。
     缩放到 720p 再让学员放大看，文字一定糊——这条没有例外。
   ⚠ 码率是按蜂窝网络定的，比固网保守。等实测证明链路稳，再往上加。
     3500 Kbps 一堂两小时的课约耗 3.2 GB 流量。

 ── eSIM 漫游的三条实务（比调参数管用）──
   1. 笔记本**全程插电源**——电池模式会降频，讲到一半开始掉帧，很难查。
   2. 若用手机共享网络，**用 USB 网络共享（USB tethering），不要用 WiFi 热点**——
      WiFi 那一跳会再叠一层抖动。
   3. 开课前在**固定位置**测一遍并记住它，讲课全程别移动；信号格数变化直接反映成画面卡顿。

 ── 每次开课前（可选）──
   改标题：  echo "SDE 本体论 · 第三讲" > /var/live/title.txt
   挂预告：  echo '{"title":"第四讲 · 承载权","at":"8月12日 20:00","note":"接着上一讲往下讲"}' > /var/live/next.json
             /usr/local/bin/live-status.sh false

 ── 第一次推流自检（三步，缺一不可）──
   1) https://sdeuniverses.com/live/status.json   应变成 {"live":true,...}
   2) https://sdeuniverses.com/live/sde.m3u8      应出 200，内容里有两行 EXT-X-STREAM-INF
   3) https://sdeuniverses.com/meeting/           应出画面

 ── 出问题时先看这两条日志 ──
   journalctl -u live-srt  -n 50 --no-pager     # SRT 有没有收到流
   journalctl -u live-sync -n 50 --no-pager     # 分片有没有传进 R2
============================================================
DONE
