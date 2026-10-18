# TrendRadarht — Hướng dẫn chạy an toàn trên Proxmox/Portainer

Bản fork này giữ bộ hotlist đa nền tảng của TrendRadar, dùng NewsNow nội bộ, Ollama local và tạo tối đa 3 nháp X tiếng Việt mỗi lượt. Hệ thống **không đăng nhập X và không tự đăng bài**.

## Cài bằng Portainer

1. Vào **Portainer → Stacks → Add stack → Repository**.
2. Điền:
   - **Repository URL:** `https://github.com/hoangthang0106/TrendRadarht`
   - **Repository reference:** `refs/heads/master`
   - **Compose path:** `docker/docker-compose.yml`
   - **Stack name:** `trendradarht`
3. Lúc đầu **chưa cần Telegram**. Deploy stack trước để kiểm tra NewsNow, Ollama và TrendRadar.
4. Bấm **Deploy the stack**. Lần đầu Ollama sẽ tải model `qwen2.5:3b`, có thể mất một lúc.
5. Xem log theo thứ tự:
   - `trendradar-ollama-init`: đợi pull model hoàn tất.
   - `trendradar`: kiểm tra crawler/AI chạy.
6. Web mặc định chỉ bind vào `127.0.0.1:8080` trên Ubuntu để tránh vô tình lộ ra mạng. Nếu cần xem từ máy khác trong LAN, đặt biến `WEBSERVER_HOST` thành **IP LAN của Ubuntu** (ví dụ `192.168.10.50`), không nên đặt `0.0.0.0` trừ khi firewall đã giới hạn đúng mạng LAN.

Web server đã được harden: **không directory listing và chặn truy cập các file DB/TXT/config/secrets**. Dù vậy vẫn không forward port 8080 trực tiếp ra Internet; nếu cần truy cập từ ngoài, dùng reverse proxy HTTPS + xác thực/VPN.

## Telegram — cách add token an toàn

### Cách A — đơn giản, phù hợp Portainer cá nhân

Trong **Stacks → trendradarht → Environment variables**, thêm:

- `TELEGRAM_BOT_TOKEN` = token lấy từ BotFather.
- `TELEGRAM_CHAT_ID` = chat ID nhận tin.

Token không nằm trong GitHub và file `docker/.env` đã bị Git ignore. Tuy nhiên người có quyền quản trị Portainer/Docker vẫn có thể xem environment của container, nên chỉ dùng khi Portainer của mày được bảo vệ tốt.

### Cách B — an toàn hơn: token nằm trong file chmod 600

Trên Ubuntu host:

```bash
sudo install -d -m 700 /opt/trendradar/secrets
read -s -p "Telegram token: " TG_TOKEN; echo
printf '%s' "$TG_TOKEN" | sudo tee /opt/trendradar/secrets/telegram_bot_token >/dev/null
unset TG_TOKEN
sudo chmod 600 /opt/trendradar/secrets/telegram_bot_token
```

Sau đó thêm bind mount cho container `trendradar`:

```yaml
volumes:
  - /opt/trendradar/secrets/telegram_bot_token:/run/secrets/telegram_bot_token:ro
```

và Environment variable:

```text
TELEGRAM_BOT_TOKEN_FILE=/run/secrets/telegram_bot_token
TELEGRAM_CHAT_ID=<chat_id_cua_may>
```

Khi dùng `TELEGRAM_BOT_TOKEN_FILE`, **không cần** đặt `TELEGRAM_BOT_TOKEN`. Code đã hỗ trợ đọc secret từ file. Cách này giúp token không xuất hiện trong cấu hình environment của container.

> Nếu token từng bị commit/push lên GitHub, gửi nhầm vào chat công khai hoặc nghi bị lộ: vào **BotFather → /revoke** (hoặc tạo token mới) rồi thay token cũ ngay. Xóa token khỏi file Git không đủ vì lịch sử commit có thể vẫn chứa nó.

### Lấy Telegram Chat ID

1. Mở `@BotFather` → `/newbot` → tạo bot.
2. Mở bot mới → **Start** → gửi một tin bất kỳ.
3. Trên máy của mày, mở:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Tìm `message.chat.id`. Chat ID không nhạy cảm bằng bot token, nhưng vẫn không cần commit vào Git.

## Cấu hình đã đặt sẵn

- **Nguồn:** 11 hotlist gốc + RSS Hacker News/Yahoo Finance; NewsNow chạy nội bộ trong Docker network.
- **Tần suất:** mặc định 30 phút/lần, `incremental` để giảm gửi lặp.
- **AI:** Ollama local + `qwen2.5:3b`, không cần API AI trả phí.
- **X draft:** tối đa 3 chủ đề/lượt, mỗi draft riêng và có source URL để kiểm tra.
- **X:** không lưu cookie/token X, không auto-post.
- **Image pinning:** NewsNow = `v0.0.42`, Ollama = `0.40.4`, uv = `0.13.1`; không dùng `:latest` cho ba thành phần này.

## Tài nguyên

Nên có khoảng **4 vCPU, 8 GB RAM trống và 15 GB disk** nếu Ollama chạy CPU. Máy yếu vẫn chạy được nhưng AI sẽ chậm. Dữ liệu NewsNow/Ollama nằm trong Docker volumes:

- `trendradar_newsnow_data`
- `trendradar_ollama_data`

Không xóa hai volume này khi redeploy nếu muốn giữ cache/model.

## Cập nhật

Sau khi repo có commit mới: **Portainer → Stacks → trendradarht → Pull and redeploy**.

Vì image đã pin version, update repo sẽ **không tự nhảy sang bản NewsNow/Ollama mới ngoài ý muốn**. Khi muốn nâng version, kiểm release notes trước rồi sửa tag có chủ đích.
