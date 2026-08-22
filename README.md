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
| SSE `/api/events` | Có | Client giữ kết nối và middleware đẩy event xuống | Web, Node.js, app/game hỗ trợ HTTP stream |
| Webhook | Có | Middleware chủ động HTTP POST event sang server khác | Game server, backend, service khác |
| Polling `/api/recent` | Gần realtime | Client gọi API định kỳ | App đơn giản, thiết bị không hỗ trợ SSE |
| JSONL | Gần realtime | Đọc file log event trên máy chạy middleware | Log, debug, replay, xử lý cùng máy |

Hiện tại middleware **chưa mở WebSocket server**.

Trong toàn bộ ví dụ bên dưới, giả sử máy chạy TikTok middleware có địa chỉ:

```text
192.168.1.10:8787
```

Nếu client chạy cùng máy, có thể thay bằng:

```text
127.0.0.1:8787
```

---

# 1. SSE realtime — `/api/events`

SSE là cách đơn giản nhất để client giữ một kết nối HTTP mở và nhận event ngay khi TikTok LIVE phát sinh sự kiện.

Endpoint:

```text
GET /api/events
Content-Type: text/event-stream
```

URL LAN:

```text
http://192.168.1.10:8787/api/events
```

Middleware phát TikTok event với tên SSE:

```text
event: tiktok-event
```

Ví dụ dữ liệu nhận được:

```text
id: 1234567890
event: tiktok-event
data: {"schemaVersion":1,"eventId":"1234567890","eventType":"comment",...}
```

Middleware cũng gửi ping định kỳ để giữ kết nối sống.

## SSE — test nhanh bằng curl

```bash
curl -N http://192.168.1.10:8787/api/events
```

`-N` giúp curl không buffer output, event sẽ hiện ngay khi nhận được.

## SSE — JavaScript trên Browser

```html
<script>
const source = new EventSource(
  "http://192.168.1.10:8787/api/events"
);

source.addEventListener("connected", (event) => {
  console.log("Đã kết nối middleware:", event.data);
});

source.addEventListener("tiktok-event", (message) => {
  const event = JSON.parse(message.data);

  console.log("EVENT:", event.eventType, event);

  switch (event.eventType) {
    case "comment":
      console.log(
        "COMMENT:",
        event.user.displayName,
        event.payload.text
      );
      break;

    case "gift":
      console.log(
        "GIFT:",
        event.user.displayName,
        event.payload.giftName,
        event.payload.count
      );
      break;

    case "like":
      console.log(
        "LIKE:",
        event.user.displayName,
        event.payload.count
      );
      break;

    case "join":
      console.log("JOIN:", event.user.displayName);
      break;

    case "follow":
      console.log("FOLLOW:", event.user.displayName);
      break;

    case "share":
      console.log("SHARE:", event.user.displayName);
      break;

    case "avatar":
      console.log(
        "AVATAR:",
        event.user.uniqueId,
        event.payload.avatarPath
      );
      break;
  }
});

source.onerror = (error) => {
  console.error("SSE lỗi/mất kết nối:", error);
};
</script>
```

`EventSource` của trình duyệt sẽ tự thử reconnect nếu kết nối bị mất.

## SSE — Node.js 18+ không cần package ngoài

Tạo file `sse-client.mjs`:

```js
const url = "http://192.168.1.10:8787/api/events";

console.log("Connecting:", url);

const response = await fetch(url);

if (!response.ok || !response.body) {
  throw new Error(`SSE HTTP ${response.status}`);
}

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const { value, done } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, { stream: true });
  buffer = buffer.replace(/\r\n/g, "\n");

  const blocks = buffer.split("\n\n");
  buffer = blocks.pop() || "";

  for (const block of blocks) {
    if (!block || block.startsWith(":")) continue;

    const lines = block.split("\n");
    const eventName = lines
      .find(line => line.startsWith("event:"))
      ?.slice(6)
      .trim();

    const dataText = lines
      .filter(line => line.startsWith("data:"))
      .map(line => line.slice(5).trimStart())
      .join("\n");

    if (eventName !== "tiktok-event" || !dataText) continue;

    const event = JSON.parse(dataText);
    console.log(event.eventType, event);
  }
}
```

Chạy:

```bash
node sse-client.mjs
```

## SSE — Python chỉ dùng thư viện chuẩn

Tạo file `sse_client.py`:

```python
import json
import urllib.request

url = "http://192.168.1.10:8787/api/events"
request = urllib.request.Request(
    url,
    headers={"Accept": "text/event-stream"},
)

with urllib.request.urlopen(request, timeout=None) as response:
    event_name = None
    data_lines = []

    for raw_line in response:
        line = raw_line.decode("utf-8").rstrip("\r\n")

        if line == "":
            if event_name == "tiktok-event" and data_lines:
                event = json.loads("\n".join(data_lines))
                print(event["eventType"], event)

            event_name = None
            data_lines = []
            continue

        if line.startswith(":"):
            continue

        if line.startswith("event:"):
            event_name = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
```

Chạy:

```bash
python sse_client.py
```

---

# 2. Webhook — middleware chủ động POST event

Webhook phù hợp khi game/backend của bạn đã có HTTP server riêng.

Luồng hoạt động:

```text
TikTok LIVE
    ↓
Middleware
    ↓ HTTP POST JSON
Game server / Backend
```

Mỗi event được middleware gửi bằng HTTP `POST` với body JSON.

## Cấu hình Webhook trên Linux / Termux

```bash
WEBHOOK_URLS=http://192.168.1.20:9000/tiktok-event \
./run.sh ten_tiktok
```

Có thể gửi tới nhiều webhook, phân cách bằng dấu phẩy:

```bash
WEBHOOK_URLS=http://192.168.1.20:9000/tiktok-event,http://192.168.1.30:8080/event \
./run.sh ten_tiktok
```

## Cấu hình Webhook trên Windows CMD

```bat
set WEBHOOK_URLS=http://192.168.1.20:9000/tiktok-event
run.bat ten_tiktok
```

## Webhook receiver — Node.js không cần package ngoài

Tạo file `webhook-server.mjs` trên máy sẽ nhận event:

```js
import http from "node:http";

const host = "0.0.0.0";
const port = 9000;

const server = http.createServer((req, res) => {
  if (req.method !== "POST" || req.url !== "/tiktok-event") {
    res.statusCode = 404;
    res.end("Not found");
    return;
  }

  let body = "";

  req.setEncoding("utf8");

  req.on("data", chunk => {
    body += chunk;
  });

  req.on("end", () => {
    try {
      const event = JSON.parse(body);

      console.log("EVENT:", event.eventType, event);

      if (event.eventType === "comment") {
        console.log(
          `${event.user.displayName}: ${event.payload.text}`
        );
      }

      res.statusCode = 200;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ ok: true }));
    } catch (error) {
      console.error(error);
      res.statusCode = 400;
      res.end("Invalid JSON");
    }
  });
});

server.listen(port, host, () => {
  console.log(`Webhook listening on http://${host}:${port}/tiktok-event`);
});
```

Chạy:

```bash
node webhook-server.mjs
```

Sau đó cấu hình máy chạy middleware gửi tới IP của máy này, ví dụ:

```text
http://192.168.1.20:9000/tiktok-event
```

## Webhook receiver — Python chỉ dùng thư viện chuẩn

Tạo file `webhook_server.py`:

```python
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "0.0.0.0"
PORT = 9000


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/tiktok-event":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        try:
            event = json.loads(body.decode("utf-8"))
            print("EVENT:", event.get("eventType"), event)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        except Exception as exc:
            print("Invalid event:", exc)
            self.send_response(400)
            self.end_headers()


server = ThreadingHTTPServer((HOST, PORT), Handler)
print(f"Webhook listening on {HOST}:{PORT}/tiktok-event")
server.serve_forever()
```

Chạy:

```bash
python webhook_server.py
```

Middleware coi HTTP `2xx` là gửi thành công. Nếu endpoint lỗi hoặc timeout, middleware có cơ chế thử gửi lại theo cấu hình retry.

> Vì Webhook có thể retry khi gửi thất bại, phía receiver nên dùng `eventId` để chống xử lý trùng.

---

# 3. Polling HTTP — `/api/recent`

Nếu client không giữ được SSE và cũng không mở được webhook server, có thể gọi API định kỳ.

Endpoint:

```text
GET /api/recent?limit=50
```

Ví dụ test bằng curl:

```bash
curl "http://192.168.1.10:8787/api/recent?limit=50"
```

Response:

```json
{
  "ok": true,
  "count": 1,
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

`/api/recent` trả lại các event gần nhất đang nằm trong bộ nhớ, không chỉ event mới kể từ lần gọi trước. Vì vậy client **phải tự chống trùng bằng `eventId`**.

## Polling — JavaScript / Node.js 18+

Tạo file `polling-client.mjs`:

```js
const url = "http://192.168.1.10:8787/api/recent?limit=100";
const processed = new Set();
const order = [];
const MAX_IDS = 5000;

function remember(eventId) {
  if (processed.has(eventId)) return false;

  processed.add(eventId);
  order.push(eventId);

  while (order.length > MAX_IDS) {
    const oldId = order.shift();
    processed.delete(oldId);
  }

  return true;
}

async function poll() {
  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const result = await response.json();

    // recent thường có thể chứa cả event đã thấy trước đó
    for (const event of result.events) {
      if (!remember(event.eventId)) continue;

      console.log("NEW EVENT:", event.eventType, event);
    }
  } catch (error) {
    console.error("Polling error:", error.message);
  }
}

await poll();
setInterval(poll, 1000);
```

Chạy:

```bash
node polling-client.mjs
```

## Polling — Python chỉ dùng thư viện chuẩn

Tạo file `polling_client.py`:

```python
import json
import time
import urllib.request
from collections import deque

URL = "http://192.168.1.10:8787/api/recent?limit=100"
MAX_IDS = 5000

processed = set()
order = deque()


def remember(event_id):
    if event_id in processed:
        return False

    processed.add(event_id)
    order.append(event_id)

    while len(order) > MAX_IDS:
        old_id = order.popleft()
        processed.discard(old_id)

    return True


while True:
    try:
        with urllib.request.urlopen(URL, timeout=5) as response:
            result = json.load(response)

        for event in result.get("events", []):
            event_id = event.get("eventId")
            if not event_id or not remember(event_id):
                continue

            print("NEW EVENT:", event.get("eventType"), event)

    except Exception as exc:
        print("Polling error:", exc)

    time.sleep(1)
```

Chạy:

```bash
python polling_client.py
```

Khoảng polling `500 ms`–`1000 ms` thường dễ dùng cho game/app thông thường. Poll quá nhanh sẽ tạo nhiều request không cần thiết.

---

# 4. Đọc file JSONL

Middleware có thể ghi event xuống file JSONL để log/debug/replay.

Mỗi dòng là một JSON event độc lập:

```text
{"eventId":"...","eventType":"join",...}
{"eventId":"...","eventType":"comment",...}
{"eventId":"...","eventType":"gift",...}
```

Tùy layout của bản portable, file nằm trong thư mục `data` của app/middleware, thường là:

```text
data/events.jsonl
```

Cách này phù hợp nhất khi chương trình đọc event chạy trên **cùng máy** với middleware.

## JSONL — theo dõi nhanh bằng shell

Linux / Termux:

```bash
tail -F data/events.jsonl
```

Nếu muốn parse từng dòng bằng `jq`:

```bash
tail -F data/events.jsonl | jq -c .
```

## JSONL — Node.js đọc các dòng mới được append

Tạo file `jsonl-client.mjs` trong thư mục app:

```js
import fs from "node:fs";

const file = "data/events.jsonl";
let position = 0;
let remainder = "";
let reading = false;

if (fs.existsSync(file)) {
  position = fs.statSync(file).size;
}

async function readNewData() {
  if (reading) return;
  reading = true;

  try {
    if (!fs.existsSync(file)) return;

    const stat = fs.statSync(file);

    // File bị truncate / tạo lại
    if (stat.size < position) {
      position = 0;
      remainder = "";
    }

    if (stat.size === position) return;

    const length = stat.size - position;
    const buffer = Buffer.alloc(length);
    const fd = fs.openSync(file, "r");

    try {
      fs.readSync(fd, buffer, 0, length, position);
    } finally {
      fs.closeSync(fd);
    }

    position = stat.size;
    remainder += buffer.toString("utf8");

    const lines = remainder.split(/\r?\n/);
    remainder = lines.pop() || "";

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const event = JSON.parse(line);
        console.log("EVENT:", event.eventType, event);
      } catch (error) {
        console.error("JSONL parse error:", error.message);
      }
    }
  } finally {
    reading = false;
  }
}

console.log("Watching:", file);
setInterval(readNewData, 250);
```

Chạy:

```bash
node jsonl-client.mjs
```

Đoạn mẫu trên bắt đầu từ cuối file hiện tại, tức là chỉ xử lý các dòng được append sau khi client chạy.

## JSONL — Python follow file

Tạo file `jsonl_client.py`:

```python
import json
import os
import time

FILE = "data/events.jsonl"

while not os.path.exists(FILE):
    print("Waiting for", FILE)
    time.sleep(1)

with open(FILE, "r", encoding="utf-8") as f:
    # Chỉ nhận event mới từ thời điểm client bắt đầu
    f.seek(0, os.SEEK_END)

    while True:
        line = f.readline()

        if not line:
            time.sleep(0.2)
            continue

        try:
            event = json.loads(line)
            print("EVENT:", event.get("eventType"), event)
        except json.JSONDecodeError as exc:
            print("JSONL parse error:", exc)
```

Chạy:

```bash
python jsonl_client.py
```

---

# So sánh nhanh các kiểu kết nối

| Phương thức | Độ trễ | Client cần mở port? | Middleware cần biết địa chỉ client? | Dùng qua LAN | Ghi chú |
|---|---:|---:|---:|---:|---|
| SSE | Thấp | Không | Không | Có | Client kết nối tới middleware và giữ stream |
| Webhook | Thấp | Có | Có | Có | Middleware POST tới server của client |
| Polling | Phụ thuộc chu kỳ poll | Không | Không | Có | Dễ triển khai nhưng tạo request định kỳ |
| JSONL | Thấp/gần realtime | Không | Không | Không trực tiếp | Tốt nhất khi cùng máy |

### Nên chọn cách nào?

- **Web/app/game client cần nhận liên tục:** SSE.
- **Game server/backend đã có HTTP server:** Webhook.
- **Thiết bị chỉ gọi HTTP request thông thường:** Polling `/api/recent`.
- **Tool xử lý/log chạy cùng máy:** JSONL.

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

Ví dụ xử lý:

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

# Gợi ý xử lý event an toàn

Dù nhận qua SSE, Webhook hay Polling, nên dùng `eventId` làm khóa chống xử lý trùng.

Ví dụ cache giới hạn ID gần nhất:

```js
const processed = new Set();
const order = [];
const MAX_IDS = 5000;

function handleTikTokEvent(event) {
  if (processed.has(event.eventId)) return;

  processed.add(event.eventId);
  order.push(event.eventId);

  if (order.length > MAX_IDS) {
    processed.delete(order.shift());
  }

  switch (event.eventType) {
    case "comment":
      console.log("comment", event.payload.text);
      break;

    case "gift":
      console.log("gift", event.payload.giftName, event.payload.count);
      break;

    case "like":
    case "join":
    case "follow":
    case "share":
    case "avatar":
      console.log(event.eventType, event);
      break;
  }
}
```

Không nên giữ `Set` vô hạn khi chương trình chạy lâu.

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
