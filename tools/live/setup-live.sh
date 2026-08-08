#!/usr/bin/env bash
# ============================================================================
# SDE 讲堂 · 直播服务器一键部署（Ubuntu 22.04/24.04，新加坡节点）
#
#   OBS ──RTMP──> 本机 nginx-rtmp ──切 HLS 分片──> rclone 实时同步 ──> R2 桶 live/
#                                                              └─> sdeuniverses.com/live/*
#
# 跑法（root 或 sudo）：
#   bash setup-live.sh
# 跑完按提示填三样：R2 Access Key ID / Secret / 账号 ID。
#
# 为什么这么设计：
#  · 分片写到本机再同步进桶，而不是让 100 个学生直连这台小机器——
#    这台机器的带宽只服务"讲师一路上行"，学生那 100 路全部由 Cloudflare 边缘扛。
#    机器规格因此可以最小档（1C1G 足够），每月只花几美元。
#  · 分片一旦写出永不改动，所以同步是"只增不改"，rclone 每秒扫一次代价极低。
#  · status.json 由 start/stop 钩子改写，网页据此自动切换开播/未开播——讲师不必碰网页。
# ============================================================================
set -euo pipefail

STREAM_KEY="${STREAM_KEY:-$(head -c 18 /dev/urandom | base64 | tr -d '/+=' | head -c 24)}"
LIVE_DIR=/var/live
HLS_DIR=$LIVE_DIR/hls
REC_DIR=$LIVE_DIR/rec

echo "==> 1/6 装 nginx-rtmp、ffmpeg、rclone"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq libnginx-mod-rtmp nginx ffmpeg rclone jq curl

mkdir -p "$HLS_DIR" "$REC_DIR"
chown -R www-data:www-data "$LIVE_DIR"

echo "==> 2/6 写 nginx-rtmp 配置"
cat > /etc/nginx/modules-enabled/60-rtmp.conf <<'NGINX'
# 由 setup-live.sh 生成
NGINX

cat > /etc/nginx/rtmp.conf <<NGINX
rtmp {
  server {
    listen 1935;
    chunk_size 4096;

    application live {
      live on;
      record all;
      record_path $REC_DIR;
      record_unique on;
      record_suffix _%Y%m%d-%H%M%S.flv;

      # 分片 6 秒、保留 20 片（2 分钟回看窗）。
      # ⚠ 别为了"低延迟"把 hls_fragment 压到 1-2 秒：跨境网络下分片越碎越容易卡，
      #   而讲课本来就不需要实时——延迟是拿来换稳的。
      hls on;
      hls_path $HLS_DIR;
      hls_fragment 6s;
      hls_playlist_length 120s;
      hls_continuous on;
      hls_cleanup on;

      # 只认这一个串流密钥，别人猜不到就推不进来
      on_publish http://127.0.0.1:8088/auth;
      exec_publish /usr/local/bin/live-start.sh;
      exec_publish_done /usr/local/bin/live-stop.sh;
    }
  }
}
NGINX

grep -q 'include /etc/nginx/rtmp.conf;' /etc/nginx/nginx.conf \
  || echo 'include /etc/nginx/rtmp.conf;' >> /etc/nginx/nginx.conf

echo "==> 3/6 串流密钥校验小服务（只在本机监听）"
cat > /usr/local/bin/live-auth.py <<PY
#!/usr/bin/env python3
# 极小的 on_publish 校验：串流密钥不对就拒绝推流（返回非 2xx）。
import http.server, urllib.parse, os
KEY = os.environ.get("STREAM_KEY", "")
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("content-length", 0) or 0)
        q = urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8", "ignore"))
        ok = q.get("name", [""])[0] == KEY
        self.send_response(200 if ok else 403); self.end_headers()
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

echo "==> 4/6 配 rclone 连 R2（交互，需要三样东西）"
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

echo "==> 5/6 写开播/下课钩子与分片同步"
cat > /usr/local/bin/live-status.sh <<'SH'
#!/usr/bin/env bash
# 改写 status.json 并立刻推进桶。网页每 15 秒问一次它，据此切开播/未开播。
set -euo pipefail
LIVE=$1                      # true / false
TITLE=$(cat /var/live/title.txt 2>/dev/null || echo "SDE 讲堂")
NEXT=$(cat /var/live/next.json 2>/dev/null || echo 'null')
STAMP=$(date '+%H:%M')
cat > /var/live/status.json <<JSON
{"live":$LIVE,"title":"$TITLE","startedAt":"$STAMP","playlist":"stream.m3u8","next":$NEXT}
JSON
rclone copyto /var/live/status.json r2:sdeuniverses-pdf/live/status.json \
  --s3-no-check-bucket --header-upload "Cache-Control: no-store" >/dev/null 2>&1 || true
SH
chmod +x /usr/local/bin/live-status.sh

cat > /usr/local/bin/live-start.sh <<'SH'
#!/usr/bin/env bash
/usr/local/bin/live-status.sh true
systemctl start live-sync.service
SH

cat > /usr/local/bin/live-stop.sh <<'SH'
#!/usr/bin/env bash
# 先停同步再改状态：反过来的话网页已显示未开播、最后几片却还在传，学生会看到画面突然截断。
sleep 8
systemctl stop live-sync.service || true
/usr/local/bin/live-status.sh false
/usr/local/bin/live-archive.sh &
SH
chmod +x /usr/local/bin/live-start.sh /usr/local/bin/live-stop.sh

cat > /usr/local/bin/live-sync.sh <<'SH'
#!/usr/bin/env bash
# 每秒把新分片和最新播放列表推进桶。
#  · 分片：只增不改，--ignore-existing 让它永不重传
#  · 播放列表：每次都要覆盖，且必须 no-store，否则学生拿到旧列表会永远停在几分钟前
set -uo pipefail
while true; do
  rclone copy /var/live/hls r2:sdeuniverses-pdf/live \
    --include "*.ts" --ignore-existing --transfers 8 --s3-no-check-bucket \
    --header-upload "Cache-Control: public, max-age=31536000, immutable" >/dev/null 2>&1
  if [ -f /var/live/hls/stream.m3u8 ]; then
    rclone copyto /var/live/hls/stream.m3u8 r2:sdeuniverses-pdf/live/stream.m3u8 \
      --s3-no-check-bucket --header-upload "Cache-Control: no-store" >/dev/null 2>&1
  fi
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
# 下课后：把 nginx 录的 flv 转成 mp4 推进桶，并往 replays.json 里加一条。
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
SH
chmod +x /usr/local/bin/live-archive.sh

echo "==> 6/6 起服务"
systemctl daemon-reload
systemctl enable --now live-auth.service
nginx -t && systemctl restart nginx
/usr/local/bin/live-status.sh false

IP=$(curl -s4 ifconfig.me || echo "<本机公网IP>")
cat <<DONE

============================================================
 装好了。OBS 里填这两行（设置 → 直播 → 服务：自定义）：

   服务器      rtmp://$IP/live
   串流密钥    $STREAM_KEY

 ⚠ 串流密钥等于开课权限，只留在讲师那台电脑上，不要发群里。

 OBS 输出建议（设置 → 输出 → 高级 → 串流）：
   编码器 x264 ／ 码率 1500 Kbps ／ 关键帧间隔 2 秒 ／ 预设 veryfast
   分辨率 1280x720 ／ 帧率 25
   —— 讲 PPT 这个码率足够清楚；再高只是白占跨境上行。

 每次开课前改标题（可选）：
   echo "SDE 本体论 · 第三讲" > /var/live/title.txt

 挂下一课预告（可选，网页未开播时会显示）：
   echo '{"title":"第四讲 · 承载权","at":"8月12日 20:00","note":"接着上一讲往下讲"}' > /var/live/next.json
   /usr/local/bin/live-status.sh false

 自检：推流后打开 https://sdeuniverses.com/live/status.json
       应看到 {"live":true,...}；再打开 https://sdeuniverses.com/meeting/ 应出画面。
============================================================
DONE
