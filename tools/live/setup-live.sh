#!/usr/bin/env bash
# ============================================================================
# SDE 讲堂 · 直播服务器一键部署 v2（Ubuntu 22.04/24.04，新加坡节点，2 核 4G）
#
#   OBS ─1080p RTMP─> nginx-rtmp ─┬─ 原画  直接复制，不重编码（零 CPU）
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
# ============================================================================
set -euo pipefail

STREAM_KEY="${STREAM_KEY:-$(head -c 18 /dev/urandom | base64 | tr -d '/+=' | head -c 24)}"
LIVE_DIR=/var/live
HLS_DIR=$LIVE_DIR/hls
REC_DIR=$LIVE_DIR/rec

echo "==> 1/7 装 nginx-rtmp、ffmpeg、rclone"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq libnginx-mod-rtmp nginx ffmpeg rclone jq curl

mkdir -p "$HLS_DIR" "$REC_DIR"
chown -R www-data:www-data "$LIVE_DIR"

echo "==> 2/7 写 nginx-rtmp 配置（双码率）"
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

echo "==> 3/7 串流密钥校验（只在本机监听）"
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

echo "==> 4/7 配 rclone 连 R2"
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

echo "==> 5/7 开播/下课钩子与分片同步"
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

echo "==> 6/7 每天清一次桶里的旧分片（不清回放）"
# 分片只在直播当下有用，留着就是白付存储费：1080p 一堂课约 4GB，一个月二十堂就是 80GB 往上累。
# ⚠ --include "*.ts" 是护栏：回放的 mp4 在 live/replay/ 下，绝不能被这条扫掉。
cat > /etc/cron.daily/sde-live-prune <<'CRON'
#!/bin/sh
rclone delete r2:sdeuniverses-pdf/live --include "*.ts" --min-age 24h --s3-no-check-bucket >/dev/null 2>&1
CRON
chmod +x /etc/cron.daily/sde-live-prune

echo "==> 7/7 起服务"
systemctl daemon-reload
systemctl enable --now live-auth.service
nginx -t && systemctl restart nginx
/usr/local/bin/live-status.sh false

IP=$(curl -s4 ifconfig.me || echo "<本机公网IP>")
cat <<DONE

============================================================
 装好了。OBS → 设置 → 直播 → 服务「自定义」，填这两行：

   服务器      rtmp://$IP/live
   串流密钥    $STREAM_KEY

 ⚠ 串流密钥等于开课权限，只留在讲师那台电脑上，不要发群里。

 ── OBS 输出设置（设置 → 输出 → 输出模式「高级」→ 串流）──
   编码器        x264
   码率控制      CBR
   关键帧间隔    2 秒          ← 必须是 2，HLS 靠它对齐分片
   CPU 预设      veryfast
   配置(Profile) high

 ── 两个场景，两套参数（设置 → 视频，讲课时切）──
   讲人：   1920x1080 / 25 fps / 4000 Kbps
   讲 PPT 或白板：
            1920x1080 / 20 fps / 5000 Kbps
            —— 帧率降下来，把码率全给清晰度。
               文字是锐边，最怕码率不够；笔迹不需要每秒 30 帧。
   ⚠ 输出分辨率必须和你屏幕一致（1080p 屏就填 1920x1080）。
     缩放到 720p 再让学员放大看，文字一定糊——这条没有例外。

 ── 每次开课前（可选）──
   改标题：  echo "SDE 本体论 · 第三讲" > /var/live/title.txt
   挂预告：  echo '{"title":"第四讲 · 承载权","at":"8月12日 20:00","note":"接着上一讲往下讲"}' > /var/live/next.json
             /usr/local/bin/live-status.sh false

 ── 第一次推流自检（三步，缺一不可）──
   1) https://sdeuniverses.com/live/status.json   应变成 {"live":true,...}
   2) https://sdeuniverses.com/live/sde.m3u8      应出 200，内容里有两行 EXT-X-STREAM-INF
   3) https://sdeuniverses.com/meeting/           应出画面
============================================================
DONE
