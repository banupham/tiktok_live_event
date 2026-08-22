# TikTok LIVE Event — bản chạy sẵn

Repo phân phối **Direct Webcast mode** đã đóng gói. Không cần `npm install` hoặc `pip install`, không dùng Chrome/DOM/Playwright.

| Hệ | Gói | Chạy |
|---|---|---|
| Windows x64 | `releases/tiktok-live-event-windows-x64.zip` | Giải nén → `run.bat ten_tiktok` |
| Linux x64 | `releases/tiktok-live-event-linux-x64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |
| Linux ARM64 | `releases/tiktok-live-event-linux-arm64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |
| Termux ARM64 | `releases/tiktok-live-event-termux-arm64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |

Có thể thêm API port ở tham số thứ hai, ví dụ `run.bat ten_tiktok 8788` hoặc `./run.sh ten_tiktok 8788`.

**Windows/Linux:** Node và Python collector đã nằm trong gói, không cần cài runtime hay thư viện.

**Termux ARM64:** toàn bộ thư viện Python (kể cả `pydantic-core` native Android) đã nằm trong gói nên không cần npm/pip. Do Node/Python của Termux phụ thuộc hệ Android và prefix của app, Termux cần có sẵn hai runtime cơ bản `node` và `python` (Python 3.14+). Không dùng gói Linux ARM64 trên Android.

Hash SHA-256: xem `SHA256SUMS.txt`.
