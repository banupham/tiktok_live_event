# TikTok LIVE Event — bản chạy sẵn

Repo phân phối **Direct Webcast mode** đã đóng gói. Không cần `npm install` hoặc `pip install`, không dùng Chrome/DOM/Playwright.

## Tải và chạy

| Hệ | Gói | Chạy |
|---|---|---|
| Windows x64 | `releases/tiktok-live-event-windows-x64.zip` | Giải nén → `run.bat ten_tiktok` |
| Linux x64 | `releases/tiktok-live-event-linux-x64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |
| Linux ARM64 | `releases/tiktok-live-event-linux-arm64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |
| Termux ARM64 | `releases/tiktok-live-event-termux-arm64.tar.gz` | Giải nén → `./run.sh ten_tiktok` |

Có thể thêm API port ở tham số thứ hai:

```bash
# Windows
run.bat ten_tiktok 8788

# Linux / Termux
./run.sh ten_tiktok 8788
```

Port mặc định là `8787`.

---

## Truy cập từ LAN

Các bản portable mặc định bind API vào:

```text
0.0.0.0:8787
```

Vì vậy máy/điện thoại khác cùng mạng LAN có thể truy cập bằng **IP LAN của máy đang chạy middleware**.

Ví dụ máy chạy middleware có IP:

```text
192.168.1.10
```

thì API sẽ được truy cập bằng:

```text
http://192.168.1.10:8787
```

> `0.0.0.0` chỉ là địa chỉ bind để lắng nghe trên mọi card mạng. Client không kết nối tới `0.0.0.0`; client phải dùng IP LAN thật như `192.168.1.10`.

Kiểm tra middleware:

```bash
curl http://192.168.1.10:8787/api/health
```

Nếu chỉ muốn cho phép truy cập trên chính máy đang chạy middleware, đặt:

```text
API_HOST=127.0.0.1
```

### Windows Firewall

Gói Windows có `allow-lan.bat`.

Nếu máy khác trong LAN không kết nối được, chạy:

```bat
allow-lan.bat
```

Nếu dùng port khác, ví dụ `8788`:

```bat
allow-lan.bat 8788
```

Script sẽ tự yêu cầu quyền Administrator và chỉ mở TCP port tương ứng trên **Private network**.

---

# Nhận event từ middleware

Hiện tại có 4 cách chính để lấy event:

| Cách | Realtime | Kiểu hoạt động | Phù hợp |
|---|---|---|---|
| SSE `/api/events` | Có | Client giữ kết nối và middleware đẩy event xuống | Web, Node.js, app/game hỗ trợ SSE |
| Webhook | Có | Middleware chủ động HTTP POST event sang server khác | Game server, backend, service khác |
| Polling `/api/recent` | Gần realtime | Client gọi API định kỳ | App đơn giản, thiết bị không hỗ trợ SSE |
| JSONL | Gần realtime | Đọc file log event trên máy chạy middleware | Log, debug, replay, xử lý cùng máy |

Hiện tại middleware **chưa mở WebSocket server**.

---

## 1. SSE realtime — `/api/events`

Đây là cách đơn giản nhất để một client giữ kết nối và nhận event ngay khi TikTok LIVE phát sinh sự kiện.

Endpoint:

```text
GET /api/events
```

Ví dụ cùng máy:

```text
http://127.0.0.1:8787/api/events
```

Ví dụ từ máy khác trong LAN:

```text
http://192.168.1.10:8787/api/events
```

### Test bằng curl

```bash
curl -N http://192.168.1.10:8787/api/events
```

Khi mới kết nối sẽ nhận event `connected`.

Sau đó mỗi TikTok event được gửi theo SSE với tên:

```text
event: tiktok-event
```

Ví dụ:

```text
id: 1234567890
event: tiktok-event
data: {"schemaVersion":1,"eventId":"1234567890","eventType":"comment",...}
```

Middleware cũng gửi ping định kỳ để giữ kết nối sống.

### JavaScript / Browser

```js
const source = new EventSource(
  "http://192.168.1.10:8787/api/events"
);

source.addEventListener("connected", (event) => {
  console.log("Đã kết nối middleware", event.data);
});

source.addEventListener("tiktok-event", (event) => {
  const data = JSON.parse(event.data);

  console.log("EVENT:", data.eventType, data);

  switch (data.eventType) {
    case "comment":
      console.log(
        "COMMENT:",
        data.user.displayName,
        data.payload.text
      );
      break;

    case "gift":
      console.log(
        "GIFT:",
        data.user.displayName,
        data.payload.giftName,
        data.payload.count
      );
      break;

    case "like":
      console.log(
        "LIKE:",
        data.user.displayName,
        data.payload.count
      );
      break;

    case "join":
      console.log("JOIN:", data.user.displayName);
      break;

    case "follow":
      console.log("FOLLOW:", data.user.displayName);
      break;

    case "share":
      console.log("SHARE:", data.user.displayName);
      break;

    case "avatar":
      console.log(
        "AVATAR:",
        data.user.uniqueId,
        data.payload.avatarPath
      );
      break;
  }
});

source.onerror = (error) => {
  console.error("SSE lỗi/mất kết nối", error);
};
```

`EventSource` của trình duyệt sẽ tự thử reconnect khi kết nối bị mất.

### Node.js không dùng thư viện SSE

Node có thể đọc stream HTTP trực tiếp:

```js
const response = await fetch(
  "http://192.168.1.10:8787/api/events"
);

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const { value, done } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, { stream: true });

  const blocks = buffer.split("\n\n");
  buffer = blocks.pop() || "";

  for (const block of blocks) {
    const eventLine = block
      .split("\n")
      .find(line => line.startsWith("event:"));

    const dataLine = block
      .split("\n")
      .find(line => line.startsWith("data:"));

    if (eventLine?.includes("tiktok-event") && dataLine) {
      const event = JSON.parse(dataLine.slice(5).trim());
      console.log(event.eventType, event);
    }
  }
}
```

---

## 2. Webhook — middleware chủ động POST event

Webhook phù hợp khi game/backend của bạn đã có HTTP server riêng.

Luồng hoạt động:

```text
TikTok LIVE
    ↓
Middleware
    ↓ HTTP POST JSON
Game server / Backend
```

Mỗi event được middleware gửi bằng:

```text
POST application/json
```

### Linux / Termux

Đặt biến `WEBHOOK_URLS` trước khi chạy:

```bash
WEBHOOK_URLS=http://192.168.1.20:9000/tiktok-event \
./run.sh ten_tiktok
```

Có thể gửi tới nhiều webhook, phân cách bằng dấu phẩy:

```bash
WEBHOOK_URLS=http://192.168.1.20:9000/tiktok-event,http://192.168.1.30:8080/event \
./run.sh ten_tiktok
```

### Windows CMD

```bat
set WEBHOOK_URLS=http://192.168.1.20:9000/tiktok-event
run.bat ten_tiktok
```

### Ví dụ server Node.js nhận Webhook

Không cần package ngoài:

```js
import http from "node:http";

const server = http.createServer((req, res) => {
  if (req.method !== "POST" || req.url !== "/tiktok-event") {
    res.statusCode = 404;
    res.end("Not found");
    return;
  }

  let body = "";

  req.on("data", chunk => {
    body += chunk;
  });

  req.on("end", () => {
    try {
      const event = JSON.parse(body);

      console.log("TikTok event:", event.eventType);
      console.log(event);

      res.statusCode = 200;
      res.end("OK");
    } catch {
      res.statusCode = 400;
      res.end("Invalid JSON");
    }
  });
});

server.listen(9000, "0.0.0.0", () => {
  console.log("Listening on port 9000");
});
```

Middleware coi HTTP `2xx` là gửi thành công. Nếu endpoint lỗi hoặc timeout, middleware có cơ chế thử gửi lại theo cấu hình retry.

---

## 3. Polling HTTP — `/api/recent`

Nếu client không giữ được SSE và cũng không mở được webhook server, có thể gọi API định kỳ.

Endpoint:

```text
GET /api/recent?limit=50
```

Ví dụ:

```bash
curl "http://192.168.1.10:8787/api/recent?limit=50"
```

Response:

```json
{
  "ok": true,
  "count": 2,
  "events": [
    {
      "schemaVersion": 1,
      "eventId": "1234567890",
      "eventType": "comment",
      "timestamp": 1760000000000,
      "receivedAt": 1760000000010,
      "user": {
        "id": "123456",
        "uniqueId": "example_user",
        "displayName": "Example User"
      },
      "payload": {
        "text": "hello"
      }
    }
  ]
}
```

`limit` tối đa hiện tại là `500`.

### JavaScript polling mỗi 1 giây

```js
const processed = new Set();

setInterval(async () => {
  const response = await fetch(
    "http://192.168.1.10:8787/api/recent?limit=100"
  );

  const result = await response.json();

  for (const event of result.events) {
    if (processed.has(event.eventId)) continue;

    processed.add(event.eventId);

    console.log("NEW EVENT:", event.eventType, event);
  }
}, 1000);
```

### Quan trọng khi polling

`/api/recent` trả lại **event gần nhất đã nằm trong bộ nhớ**, không chỉ event mới kể từ lần gọi trước.

Vì vậy client nên lưu `eventId` đã xử lý để tránh chạy một event nhiều lần.

---

## 4. Đọc file JSONL

Middleware có thể ghi event xuống file JSONL để log/debug/replay.

Mỗi dòng là một JSON event độc lập:

```text
{"eventId":"...","eventType":"join",...}
{"eventId":"...","eventType":"comment",...}
{"eventId":"...","eventType":"gift",...}
```

Có thể theo dõi realtime trên Linux/Termux bằng:

```bash
tail -f data/events.jsonl
```

Tùy layout của bản portable, file nằm trong thư mục `data` của app/middleware.

Cách này phù hợp nhất khi chương trình đọc event chạy trên **cùng máy** với middleware.

---

# Các loại event hiện có

Middleware hiện hỗ trợ:

```text
join
comment
follow
share
like
gift
avatar
```

Không phát event `leave`.

## Cấu trúc event chung

Event chuẩn có dạng:

```json
{
  "schemaVersion": 1,
  "eventId": "1234567890",
  "eventType": "comment",
  "timestamp": 1760000000000,
  "receivedAt": 1760000000010,
  "source": {
    "platform": "tiktok",
    "collector": "webcast-direct",
    "liveUrl": "https://www.tiktok.com/@example/live",
    "roomId": "123456789"
  },
  "user": {
    "id": "123456",
    "uniqueId": "example_user",
    "displayName": "Example User",
    "identityType": "userId"
  },
  "payload": {},
  "raw": {}
}
```

Các field quan trọng cho app/game:

| Field | Ý nghĩa |
|---|---|
| `eventId` | ID event, dùng để chống xử lý trùng |
| `eventType` | Loại event |
| `timestamp` | Thời gian event, Unix milliseconds |
| `receivedAt` | Thời gian middleware nhận event |
| `user.id` | TikTok numeric user ID khi có |
| `user.uniqueId` | TikTok username |
| `user.displayName` | Tên hiển thị |
| `payload` | Dữ liệu riêng của từng event |

---

## COMMENT

```json
{
  "eventType": "comment",
  "user": {
    "uniqueId": "abc",
    "displayName": "ABC"
  },
  "payload": {
    "text": "hello",
    "normalizedText": "hello"
  }
}
```

Dùng:

```js
if (event.eventType === "comment") {
  console.log(event.user.displayName, event.payload.text);
}
```

---

## JOIN

```json
{
  "eventType": "join",
  "user": {
    "uniqueId": "abc",
    "displayName": "ABC"
  },
  "payload": {
    "memberCount": 123
  }
}
```

---

## LIKE

```json
{
  "eventType": "like",
  "user": {
    "uniqueId": "abc",
    "displayName": "ABC"
  },
  "payload": {
    "count": 5,
    "totalCount": 1000
  }
}
```

`payload.count` là số like của event đó.

---

## FOLLOW

```json
{
  "eventType": "follow",
  "user": {
    "uniqueId": "abc",
    "displayName": "ABC"
  },
  "payload": {
    "followCount": 1
  }
}
```

---

## SHARE

```json
{
  "eventType": "share",
  "user": {
    "uniqueId": "abc",
    "displayName": "ABC"
  },
  "payload": {
    "shareCount": 1
  }
}
```

---

## GIFT

Ví dụ:

```json
{
  "eventType": "gift",
  "user": {
    "uniqueId": "abc",
    "displayName": "ABC"
  },
  "payload": {
    "giftName": "Rose",
    "giftKey": "rose",
    "count": 1,
    "giftId": 5655,
    "comboCount": 1,
    "diamondCount": 1
  }
}
```

Direct mode phát `count` theo **delta của combo** để tránh cộng trùng quà trong chuỗi gift.

Ví dụ xử lý:

```js
if (event.eventType === "gift") {
  console.log(
    `${event.user.displayName} gửi ${event.payload.giftName} x${event.payload.count}`
  );
}
```

---

# Event avatar

Direct collector lấy `avatar_thumb` của user và tải file ảnh vào **thư mục tạm của tiến trình**.

Avatar được cache theo TikTok `userId`, fallback sang `uniqueId`, nên COMMENT/JOIN/LIKE/FOLLOW/SHARE/GIFT của cùng user **không tải và không phát avatar lặp lại**.

Khi gặp avatar lần đầu hoặc avatar thật sự thay đổi, middleware phát event riêng:

```text
eventType: avatar
```

Ví dụ:

```json
{
  "eventType": "avatar",
  "user": {
    "id": "123456",
    "uniqueId": "abc",
    "displayName": "ABC"
  },
  "payload": {
    "avatarUrl": "https://...",
    "avatarPath": "/tmp/.../avatar.jpg",
    "mimeType": "image/jpeg",
    "bytes": 12345,
    "cache": "temp",
    "changed": false,
    "previousAvatarUrl": null
  }
}
```

Các field:

| Field | Ý nghĩa |
|---|---|
| `avatarUrl` | URL avatar TikTok/CDN |
| `avatarPath` | Đường dẫn file ảnh temp trên máy chạy middleware |
| `mimeType` | MIME ảnh |
| `bytes` | Kích thước file |
| `cache` | Hiện tại là `temp` |
| `changed` | `true` nếu avatar của user đã đổi |
| `previousAvatarUrl` | URL avatar trước đó khi có |

### Lưu ý rất quan trọng khi nhận avatar qua LAN

`avatarPath` là **đường dẫn local trên máy chạy middleware**.

Ví dụ middleware chạy trên PC:

```text
C:\...\Temp\tiktok-live-event-avatars-...\123.jpg
```

thì điện thoại hoặc máy khác trong LAN **không thể trực tiếp mở đường dẫn đó**.

`avatarPath` hiện chủ yếu dành cho chương trình chạy cùng máy hoặc phần sử dụng tùy biến sau.

Các event COMMENT/JOIN/LIKE/FOLLOW/SHARE/GIFT không nhúng lại avatar để tránh lặp dữ liệu.

File avatar temp tồn tại theo vòng đời của collector/process và không phải dữ liệu lưu lâu dài.

`/api/health` có `avatarCount` để xem số avatar đang được cache trong RAM.

---

# Các API hiện có

## Health

```text
GET /api/health
```

Ví dụ:

```bash
curl http://192.168.1.10:8787/api/health
```

Dùng để kiểm tra middleware còn chạy, số event, số client SSE, số avatar cache, v.v.

## SSE realtime

```text
GET /api/events
```

## Recent events

```text
GET /api/recent?limit=50
```

`limit` tối đa `500`.

## Schema

```text
GET /api/schema
```

Ví dụ:

```bash
curl http://192.168.1.10:8787/api/schema
```

## API root

```text
GET /
GET /api
```

Trả danh sách endpoint cơ bản.

---

# Nên dùng cách nào?

Nếu một **web/app/game client** cần nhận event liên tục:

```text
SSE /api/events
```

Nếu **game server/backend đã có HTTP server**:

```text
Webhook
```

Nếu thiết bị/client chỉ gọi HTTP thông thường được:

```text
Polling /api/recent
```

Nếu xử lý/log ở cùng máy:

```text
JSONL
```

Về độ phù hợp cho realtime:

```text
SSE / Webhook  >  Polling  >  đọc JSONL thủ công
```

---

# Gợi ý xử lý event an toàn

Dù nhận qua SSE, Webhook hay polling, nên dùng `eventId` làm khóa chống xử lý trùng.

Ví dụ:

```js
const processedEventIds = new Set();

function handleTikTokEvent(event) {
  if (processedEventIds.has(event.eventId)) {
    return;
  }

  processedEventIds.add(event.eventId);

  switch (event.eventType) {
    case "comment":
      break;

    case "gift":
      break;

    case "like":
      break;

    case "join":
      break;

    case "follow":
      break;

    case "share":
      break;

    case "avatar":
      break;
  }
}
```

Nếu chạy lâu, không nên giữ `Set` vô hạn; có thể dùng cache giới hạn số lượng ID gần nhất.

---

# Runtime

**Windows/Linux:** Node và Python collector đã nằm trong gói, không cần cài runtime hay thư viện.

**Termux ARM64:** thư viện Python, kể cả `pydantic-core` native Android, đã nằm trong gói nên không cần `npm install` hoặc `pip install`. Termux cần có sẵn runtime `node` và `python` 3.14+.

---

# SHA-256

Hash SHA-256 của các gói phát hành nằm trong:

```text
SHA256SUMS.txt
```
