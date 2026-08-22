# TikTok LIVE Event — bản chạy sẵn

Repo phân phối **Direct Webcast mode** đã đóng gói. Không cần `npm install` hoặc `pip install`, không dùng Chrome/DOM/Playwright.

| Hệ | Gói | Chạy |
|---|---|---|
| Windows x64 | `releases/tiktok-live-event-windows-x64.zip` | Giải nén → `run.bat ten_tiktok` |
| Linux x64 | `releases/tiktok-live-event-linux-x64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |
| Linux ARM64 | `releases/tiktok-live-event-linux-arm64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |
| Termux ARM64 | `releases/tiktok-live-event-termux-arm64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |

Có thể thêm API port ở tham số thứ hai, ví dụ `run.bat ten_tiktok 8788` hoặc `./run.sh ten_tiktok 8788`.

## Truy cập từ LAN

Các bản portable mặc định bind API vào `0.0.0.0:8787`, vì vậy máy/điện thoại khác cùng mạng LAN có thể truy cập bằng IP LAN của máy chạy middleware, ví dụ `http://192.168.1.10:8787/api/health` hoặc SSE `http://192.168.1.10:8787/api/events`.

Muốn giới hạn chỉ trên máy local, đặt `API_HOST=127.0.0.1` trước khi chạy.

**Windows:** gói có thêm `allow-lan.bat`. Nếu Windows Firewall chặn kết nối, chạy `allow-lan.bat` (hoặc `allow-lan.bat 8788` nếu dùng port khác). Script chỉ mở TCP port tương ứng trên profile **Private network** và sẽ tự yêu cầu quyền Administrator.

## Event avatar

Direct collector lấy `avatar_thumb` của user và tải file ảnh vào **thư mục tạm của tiến trình**. Avatar được cache theo TikTok `userId` (fallback `uniqueId`) nên COMMENT/JOIN/LIKE/FOLLOW/SHARE/GIFT của cùng user **không tải và không phát avatar lặp lại**.

Khi gặp avatar lần đầu hoặc avatar thật sự đổi, middleware phát một event riêng `eventType: "avatar"`. `payload` có `avatarUrl`, `avatarPath`, `mimeType`, `bytes`, `cache: "temp"`, `changed` và `previousAvatarUrl`. Các event khác không mang avatar để tránh dữ liệu lặp. Cache RAM mới nhất cũng được giữ trong `EventBus` cho phần sử dụng tùy biến sau; `/api/health` có `avatarCount`.

File ảnh temp tự thuộc vòng đời của collector/process và không phải dữ liệu lưu lâu dài.

**Windows/Linux:** Node và Python collector đã nằm trong gói, không cần cài runtime hay thư viện.

**Termux ARM64:** thư viện Python (kể cả `pydantic-core` native Android) đã nằm trong gói nên không cần npm/pip. Termux cần có sẵn runtime `node` và `python` 3.14+.

Hash SHA-256: xem `SHA256SUMS.txt`.
