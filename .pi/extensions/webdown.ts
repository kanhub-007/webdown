/**
 * Pi extension that bridges to the webdown MCP server via HTTP.
 *
 * Expects the MCP server to be already running (start with
 * ``WEBDOWN_TRANSPORT=http python run_mcp.py``).
 * Discovers MCP tools and registers them as pi custom tools.
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type } from "typebox";

// ── MCP JSON-RPC types ──────────────────────────────────────────

interface JsonRpcRequest {
  jsonrpc: "2.0";
  id: number;
  method: string;
  params?: Record<string, unknown>;
}

interface JsonRpcResponse {
  jsonrpc: "2.0";
  id: number;
  result?: unknown;
  error?: { code: number; message: string };
}

interface McpToolDef {
  name: string;
  description?: string;
  inputSchema: {
    type: "object";
    properties?: Record<string, { type?: string; description?: string }>;
    required?: string[];
  };
}

// ── MCP Client over HTTP ───────────────────────────────────────

class McpHttpClient {
  private requestId = 0;
  private connected = false;
  private baseUrl: string;
  private sessionId: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async start(): Promise<void> {
    const initResponse = await fetch(this.baseUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 0,
        method: "initialize",
        params: {
          protocolVersion: "2024-11-05",
          capabilities: {},
          clientInfo: { name: "pi-webdown", version: "1.0.0" },
        },
      }),
    });

    if (!initResponse.ok) {
      throw new Error(
        `MCP initialize failed: HTTP ${initResponse.status} ${initResponse.statusText}`
      );
    }

    const sid = initResponse.headers.get("mcp-session-id");
    if (sid) this.sessionId = sid;
    await initResponse.text();

    await this.sendNotification("notifications/initialized", {});
    this.connected = true;
  }

  isConnected(): boolean {
    return this.connected;
  }

  async listTools(): Promise<McpToolDef[]> {
    const res = await this.request("tools/list", {});
    return (res.result as { tools: McpToolDef[] })?.tools ?? [];
  }

  async callTool(name: string, args: Record<string, unknown>): Promise<string> {
    const res = await this.request("tools/call", { name, arguments: args });
    const content = (
      res.result as { content?: Array<{ type: string; text?: string }> }
    )?.content;
    if (content && content.length > 0) {
      return content.map((c) => c.text ?? "").join("\n");
    }
    return JSON.stringify(res.result);
  }

  private request(method: string, params: Record<string, unknown>): Promise<JsonRpcResponse> {
    const id = ++this.requestId;
    const timeoutMs = method === "tools/call" ? 300000 : 30000;

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`MCP request timeout after ${timeoutMs}ms: ${method}`));
      }, timeoutMs);

      this.sendHttp(id, method, params)
        .then((response) => {
          clearTimeout(timer);
          if (response.error) reject(new Error(response.error.message));
          else resolve(response);
        })
        .catch((err) => {
          clearTimeout(timer);
          reject(err);
        });
    });
  }

  private requestHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
    };
    if (this.sessionId) headers["mcp-session-id"] = this.sessionId;
    return headers;
  }

  private async sendHttp(id: number, method: string, params: Record<string, unknown>): Promise<JsonRpcResponse> {
    const body: JsonRpcRequest = { jsonrpc: "2.0", id, method, params };
    const response = await fetch(this.baseUrl, {
      method: "POST",
      headers: this.requestHeaders(),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`MCP HTTP error ${response.status}: ${response.statusText}`);
    }
    const text = await response.text();
    if (text.startsWith("{")) return JSON.parse(text) as JsonRpcResponse;
    for (const line of text.split("\n")) {
      if (line.startsWith("data:")) return JSON.parse(line.slice(5).trim()) as JsonRpcResponse;
    }
    return { jsonrpc: "2.0", id, result: {} };
  }

  private async sendNotification(method: string, params: Record<string, unknown>): Promise<void> {
    const body = { jsonrpc: "2.0", method, params };
    await fetch(this.baseUrl, {
      method: "POST",
      headers: this.requestHeaders(),
      body: JSON.stringify(body),
    });
  }
}

// ── JSON schema → TypeBox helper ───────────────────────────────

function jsonSchemaToTypeBox(schema: McpToolDef["inputSchema"]) {
  const shape: Record<string, unknown> = {};
  for (const [key, prop] of Object.entries(schema.properties ?? {})) {
    const desc = prop.description ?? key;
    const typ = prop.type ?? "string";
    if (typ === "string") shape[key] = Type.Optional(Type.String({ description: desc }));
    else if (typ === "integer" || typ === "number") shape[key] = Type.Optional(Type.Number({ description: desc }));
    else if (typ === "boolean") shape[key] = Type.Optional(Type.Boolean({ description: desc }));
    else shape[key] = Type.Optional(Type.String({ description: desc }));
  }
  return Type.Object(shape);
}

// ── Extension entry point ──────────────────────────────────────

export default async function (pi: ExtensionAPI) {
  const baseUrl = process.env.WEBDOWN_MCP_URL || "http://127.0.0.1:8002/mcp";
  const client = new McpHttpClient(baseUrl);

  pi.on("session_start", async (_event, ctx) => {
    try {
      ctx.ui.notify(`webdown: Connecting to MCP server at ${baseUrl}...`, "info");
      if (!client.isConnected()) await client.start();
      const tools = await client.listTools();
      ctx.ui.notify(`webdown: Connected, ${tools.length} tools discovered`, "success");

      for (const tool of tools) {
        const paramsSchema = jsonSchemaToTypeBox(tool.inputSchema);
        pi.registerTool({
          name: tool.name,
          label: tool.name,
          description: tool.description ?? `webdown tool: ${tool.name}`,
          parameters: paramsSchema,
          async execute(_toolCallId, params) {
            try {
              const result = await client.callTool(tool.name, params as Record<string, unknown>);
              return { content: [{ type: "text" as const, text: result }], details: {} };
            } catch (err) {
              return {
                content: [{ type: "text" as const, text: `webdown error: ${err instanceof Error ? err.message : String(err)}` }],
                details: {},
              };
            }
          },
        });
        ctx.ui.notify(`webdown: Registered tool '${tool.name}'`, "info");
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      ctx.ui.notify(
        `webdown: ${msg}. Is the server running? Start it with:\n  WEBDOWN_TRANSPORT=http python run_mcp.py`,
        "error"
      );
    }
  });
}
