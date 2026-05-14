/**
 * WebSocket + HTTP mock server for local development testing.
 *
 * Usage:
 *   node scripts/ws-test-server.mjs
 *
 * Commands (type in terminal after server starts):
 *   ping.confirmed <segment_id> [volunteer_name]
 *   ping.no_response <segment_id> [volunteer_name]
 *   delay <segment_id> [message]
 *   sos <segment_id>
 *   unread <count>        — change unread count returned by /notifications/unread
 *   clients               — show number of connected WebSocket clients
 *   help
 */

import { createServer } from "http";
import { createInterface } from "readline";

// ── ws 패키지 동적 로드 ────────────────────────────────────────────────────────
let WebSocketServer, WebSocket;
try {
  ({ WebSocketServer, WebSocket } = await import("ws"));
} catch {
  console.error(
    "\n[ERROR] ws 패키지가 없습니다. 아래 명령어로 설치 후 다시 실행하세요.\n\n  npm install -D ws\n"
  );
  process.exit(1);
}

const PORT = 8001;

// ── 미읽은 알림 더미 데이터 ───────────────────────────────────────────────────
let unreadCount = 2;

function makeUnreadResponse() {
  return {
    notifications: Array.from({ length: unreadCount }, (_, i) => ({
      id: i + 1,
      type: "matching_proposed",
      message: `테스트 알림 ${i + 1}`,
      payload: { segment_id: i + 1, url: `/volunteer/matching/${i + 1}` },
      created_at: new Date().toISOString(),
    })),
  };
}

// ── HTTP 서버 (WS 업그레이드 + /notifications/unread 폴백) ─────────────────────
const ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:3001"];

const httpServer = createServer((req, res) => {
  const origin = req.headers.origin;
  if (origin && ALLOWED_ORIGINS.includes(origin)) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Access-Control-Allow-Credentials", "true");
  }

  if (req.method === "GET" && req.url === "/notifications/unread") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(makeUnreadResponse()));
    return;
  }

  // /auth/refresh — 401 방지용 더미 응답
  if (req.method === "POST" && req.url === "/auth/refresh") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ ok: true }));
    return;
  }

  res.writeHead(404);
  res.end("Not found");
});

// ── WebSocket 서버 ─────────────────────────────────────────────────────────────
const wss = new WebSocketServer({ server: httpServer, path: "/ws" });

wss.on("connection", (ws, req) => {
  const shareToken = new URL(req.url, "http://localhost").searchParams.get("share_token");
  const label = shareToken ? `입양자(${shareToken})` : "보호소/봉사자";
  console.log(`[WS] 연결됨 — ${label}  (현재 ${wss.clients.size}개)`);

  ws.on("close", () => {
    console.log(`[WS] 연결 종료  (현재 ${wss.clients.size}개)`);
  });
});

function broadcast(eventName, payload) {
  const msg = JSON.stringify({ event: eventName, payload });
  let sent = 0;
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(msg);
      sent++;
    }
  });
  console.log(`[→] ${eventName}  payload=${JSON.stringify(payload)}  (${sent}개 클라이언트에 전송)`);
}

// ── 터미널 입력 처리 ──────────────────────────────────────────────────────────
const rl = createInterface({ input: process.stdin, output: process.stdout, prompt: "> " });

function printHelp() {
  console.log(`
명령어 목록:
  ping.confirmed <segment_id> [volunteer_name]   — 출발 확인 (초록)
  ping.no_response <segment_id> [volunteer_name] — 핑 미응답 (주황 경고)
  delay <segment_id> [message]                   — 지연 신고 토스트
  sos <segment_id>                               — SOS 토스트
  unread <count>                                 — /notifications/unread 응답 개수 변경
  clients                                        — 연결된 클라이언트 수
  help                                           — 이 도움말
`);
}

rl.on("line", (line) => {
  const [cmd, ...args] = line.trim().split(/\s+/);

  switch (cmd) {
    case "ping.confirmed": {
      const segment_id = Number(args[0] ?? 1);
      const volunteer_name = args.slice(1).join(" ") || "홍길동";
      broadcast("ping.confirmed", { segment_id, volunteer_name });
      break;
    }
    case "ping.no_response": {
      const segment_id = Number(args[0] ?? 1);
      const volunteer_name = args.slice(1).join(" ") || "홍길동";
      broadcast("ping.no_response", {
        segment_id,
        volunteer_name,
        scheduled_time: new Date().toISOString(),
      });
      break;
    }
    case "delay": {
      const segment_id = Number(args[0] ?? 1);
      const message = args.slice(1).join(" ") || "교통 체증으로 30분 지연 예상";
      broadcast("delay.reported", { segment_id, message });
      break;
    }
    case "sos": {
      const segment_id = Number(args[0] ?? 1);
      broadcast("sos.triggered", { segment_id, latitude: 36.35, longitude: 127.38 });
      break;
    }
    case "unread": {
      unreadCount = Math.max(0, Number(args[0] ?? 0));
      console.log(`[HTTP] /notifications/unread → ${unreadCount}개로 변경`);
      break;
    }
    case "clients":
      console.log(`연결된 클라이언트: ${wss.clients.size}개`);
      break;
    case "help":
    case "":
      printHelp();
      break;
    default:
      if (cmd) console.log(`알 수 없는 명령어: "${cmd}"  (help 로 도움말 확인)`);
  }

  rl.prompt();
});

rl.on("close", () => process.exit(0));

// ── 서버 시작 ─────────────────────────────────────────────────────────────────
httpServer.listen(PORT, () => {
  console.log(`
✅ Mock 서버 시작  ws://localhost:${PORT}/ws
               http://localhost:${PORT}/notifications/unread

프론트엔드 .env.local 에 아래 항목을 설정하세요:
  NEXT_PUBLIC_WS_URL=ws://localhost:${PORT}
  (변경 후 Next.js dev 서버 재시작 필요)

준비되면 명령어를 입력하세요. (help 로 목록 확인)
`);
  rl.prompt();
});
