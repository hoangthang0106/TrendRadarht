# TrendRadarht — Hướng dẫn chạy trên Proxmox/Portainer

Bản fork này giữ bộ hotlist đa nền tảng của tác giả TrendRadar, dùng RSS mặc định Hacker News và Yahoo Finance; mỗi 30 phút gửi tóm tắt cùng tối đa 3 nháp X cho các chủ đề đang nổi, mỗi chủ đề một bài riêng. Mày tự mở nguồn, kiểm tra, sửa và đăng; hệ thống không đăng nhập hay tự đăng lên X.

## Cách cài bằng Portainer

1. Mở **Portainer → Stacks → Add stack → Repository**.
2. Điền:
   - **Repository URL:** `https://github.com/hoangthang0106/TrendRadarht`
   - **Repository reference:** `refs/heads/master`
   - **Compose path:** `docker/docker-compose.yml`
   - **Stack name:** `trendradarht`
3. Ở **Environment variables**, thêm hai biến:
   - `TELEGRAM_BOT_TOKEN`: token bot Telegram.
   - `TELEGRAM_CHAT_ID`: chat ID Telegram nhận nháp.
4. Bấm **Deploy the stack**. Portainer build mã của fork thành image riêng, đồng thời chạy NewsNow nội bộ và tải model Ollama vào Docker volume; lần đầu có thể mất một lúc.
5. Mở **Containers → trendradar-ollama-init → Logs**. Khi thấy `success`/hoàn tất tải model, mở **trendradar → Logs** để kiểm tra worker.
6. Trên máy trong mạng LAN, mở `http://IP_UBUNTU:8080` để xem báo cáo và copy nháp X. Chưa cấu hình Telegram thì hệ thống không gửi thông báo đẩy; dùng trang này để xem kết quả.

### Tạo bot Telegram

1. Mở Telegram, nhắn `@BotFather`, gửi `/newbot` và làm theo hướng dẫn.
2. Lưu token riêng. Mở bot vừa tạo, bấm **Start** rồi gửi một tin bất kỳ.
3. Mở `https://api.telegram.org/bot<TOKEN>/getUpdates`, thay `<TOKEN>` bằng token thật; lấy `message.chat.id`.
4. Chỉ điền token trong biến môi trường của Portainer. Không commit token vào GitHub và không gửi token cho người khác.

## Cấu hình đã đặt sẵn

- **Nguồn:** giữ nguyên 11 nền tảng hotlist gốc (Toutiao, Baidu, Wallstreetcn, ThePaper, Bilibili, CLS, Ifeng, Tieba, Weibo, Douyin, Zhihu); RSS giữ Hacker News và Yahoo Finance. NewsNow chạy trong cùng stack và TrendRadar gọi API qua mạng Docker nội bộ.
- **Phạm vi:** không khóa vào một ngách; AI nhận các hotlist đã chọn và RSS. Telegram chỉ gửi tóm tắt và các nháp, tránh đổ nguyên bảng dài vào chat.
- **Tần suất:** 30 phút/lần; chế độ incremental giúp tránh gửi lặp các mục đã thấy.
- **Nháp:** tối đa 3 bài mỗi lượt, mỗi bài về một chủ đề riêng, tối đa 240 ký tự và kèm link nguồn để mày kiểm tra.
- **AI:** Ollama chạy cục bộ với Qwen 2.5 3B; không cần API AI trả phí. Model lưu trong volume `trendradar_ollama_data`.
- **X:** không lưu cookie/token X, không tự đăng bài.

RSS chỉ giúp phát hiện tin và dẫn về bài gốc. Trước khi đăng để kiếm tiền, mở nguồn, kiểm chứng thông tin, ghi nguồn phù hợp và tự viết lại bằng góc nhìn của mày; điều khoản RSS của từng báo có thể giới hạn việc sử dụng thương mại.

## Tài nguyên và giới hạn

Nên dành khoảng **4 vCPU, 8 GB RAM trống và 15 GB ổ đĩa** cho container/model nếu chạy CPU. Máy yếu vẫn có thể chạy nhưng bước tạo nháp sẽ chậm; giảm tần suất ở Portainer bằng biến `CRON_SCHEDULE` nếu cần. Lần đầu phải có Internet để tải image NewsNow/Ollama, build TrendRadar và tải model; dữ liệu/model sau đó lưu ở thư mục repo và Docker volume. Giữ volume `trendradar_newsnow_data` và `trendradar_ollama_data` khi cập nhật.

Port 8080 được mở trên interface của Ubuntu để xem trong LAN. **Không forward port 8080 ra Internet** nếu chưa đặt reverse proxy và xác thực. Không có cách bảo đảm tuyệt đối X sẽ không giới hạn tài khoản; để tài khoản tự kiểm duyệt và tự đăng, giữ nhịp đăng tự nhiên, tránh đăng nguyên văn liên tục hoặc spam hashtag/link.

## Cập nhật

Sau khi có commit mới trên GitHub: vào **Portainer → Stacks → trendradarht → Pull and redeploy**. Không xóa volume `trendradar_ollama_data`; volume đó chứa model đã tải.
