# TikTok LIVE Event — bản chạy sẵn

Repo phân phối **Direct Webcast mode** đã đóng gói. Không cần `npm install` hoặc `pip install`, không dùng Chrome/DOM/Playwright.

| Hệ | Gói | Chạy |
|---|---|---|
| Windows x64 | `releases/tiktok-live-event-windows-x64.zip` | Giải nén → `run.bat ten_tiktok` |
| Linux x64 | `releases/tiktok-live-event-linux-x64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |
| Linux ARM64 | `releases/tiktok-live-event-linux-arm64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |
| Termux ARM64 | `releases/tiktok-live-event-termux-arm64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |

Có thể thêm API port ở tham số thứ hai, ví dụ `run.bat ten_tiktok 8788` hoặc `./run.sh ten_tiktok 8788`.

## Event avatar

Direct collector lấy `avatar_thumb` của user và tải file ảnh vào **thư mục tạm của tiến trình**. Avatar được cache theo TikTok `userId` (fallback `uniqueId`) nên COMMENT/JOIN/LIKE/FOLLOW/SHARE/GIFT của cùng user **không tải và không phát avatar lặp lại**.

Khi gặp avatar lần đầu hoặc avatar thật sự đổi, middleware phát một event riêng `eventType: "avatar"`. `payload` có `avatarUrl`, `avatarPath`, `mimeType`, `bytes`, `cache: "temp"`, `changed` và `previousAvatarUrl`. Các event khác không mang avatar để tránh dữ liệu lặp. Cache RAM mới nhất cũng được giữ trong `EventBus` cho phần sử dụng tùy biến sau; `/api/health` có `avatarCount`.

File ảnh temp tự thuộc vòng đời của collector/process và không phải dữ liệu lưu lâu dài.

**Windows/Linux:** Node và Python collector đã nằm trong gói, không cần cài runtime hay thư viện.

**Termux ARM64:** thư viện Python (kể cả `pydantic-core` native Android) đã nằm trong gói nên không cần npm/pip. Termux cần có sẵn runtime `node` và `python` 3.14+.

Hash SHA-256: xem `SHA256SUMS.txt`.
