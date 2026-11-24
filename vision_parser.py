import base64
import json
import os
import urllib.error
import urllib.request
import cv2
import numpy as np

GROQ_MODEL = "qwen/qwen3.8-27b"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

CLOUD_PROMPT = """Analyze this hand-drawn graph image carefully.
1. Find every circular or circled node and read the exact label/number inside it.
2. Trace every line or curve connecting two nodes from endpoint to endpoint. Do NOT invent edges between nodes that have no visible connecting line.
3. Read the edge weight number written beside or on each connecting line. If no weight label is written for an edge, set weight to 1.
4. Estimate each node's center position (x, y) on a 0 to 1000 scale where (0,0) is top-left and (1000,1000) is bottom-right.

Return ONLY valid JSON in this exact format:
{
  "nodes": [
    {"id": "1", "x": 200, "y": 300}
  ],
  "edges": [
    {"source": "1", "target": "2", "weight": 4}
  ]
}"""


def load_and_resize(image_bytes_or_path, target_max=1280):
    if isinstance(image_bytes_or_path, str):
        raw_img = cv2.imread(image_bytes_or_path)
    else:
        nparr = np.frombuffer(image_bytes_or_path, np.uint8)
        raw_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if raw_img is None:
        raise ValueError("Could not decode image.")

    h, w = raw_img.shape[:2]
    scale = min(1.0, target_max / max(h, w))
    if scale < 1.0:
        raw_img = cv2.resize(raw_img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    lab = cv2.cvtColor(raw_img, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    return cv2.cvtColor(cv2.merge((l_ch, a_ch, b_ch)), cv2.COLOR_LAB2BGR)


def _extract_json_object(raw_text: str) -> dict:
    cleaned = (raw_text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise


def _parse_cloud_groq(img, api_key):
    """Online-only parser using Groq vision chat completions endpoint."""
    h, w = img.shape[:2]
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not ok:
        raise ValueError("Failed to encode image.")
    b64_img = base64.b64encode(buf.tobytes()).decode("utf-8")

    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.7,
        "top_p": 0.8,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": CLOUD_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                    },
                ],
            }
        ],
    }

    req = urllib.request.Request(
        GROQ_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AlgoCanvas/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Groq HTTP {exc.code}: {detail}") from exc

    message = data["choices"][0]["message"]
    raw_text = message.get("content") or ""
    if isinstance(raw_text, list):
        raw_text = "".join(
            part.get("text", "") for part in raw_text if isinstance(part, dict)
        )

    parsed = _extract_json_object(raw_text)

    nodes, seen_ids = [], set()
    for n in parsed.get("nodes", []):
        nid = str(n.get("id", "")).strip()
        if not nid or nid in seen_ids:
            continue
        seen_ids.add(nid)
        x_norm = max(0.0, min(1000.0, float(n.get("x", 500))))
        y_norm = max(0.0, min(1000.0, float(n.get("y", 500))))
        nx = int(round(x_norm / 1000.0 * w))
        ny = int(round(y_norm / 1000.0 * h))
        nodes.append({"id": nid, "x": nx, "y": ny, "r": 24})

    node_map = {n["id"]: n for n in nodes}
    edges, seen_edges = [], set()
    for e in parsed.get("edges", []):
        u = str(e.get("source", "")).strip()
        v = str(e.get("target", "")).strip()
        if u not in node_map or v not in node_map or u == v:
            continue
        pair = tuple(sorted((u, v)))
        if pair in seen_edges:
            continue
        seen_edges.add(pair)
        try:
            weight = max(1, int(round(float(e.get("weight", 1)))))
        except (ValueError, TypeError):
            weight = 1
        edges.append({"source": u, "target": v, "weight": weight})

    return {"nodes": nodes, "edges": edges, "parser_used": f"cloud ({GROQ_MODEL})"}


def extract_graph(image_bytes_or_path, mode="cloud", api_key=None, save_debug=False):
    """Online-only Graph Parser via Groq."""
    img = load_and_resize(image_bytes_or_path, target_max=1280)
    resolved_key = (api_key or os.environ.get("GROQ_API_KEY") or "").strip()
    if not resolved_key:
        raise RuntimeError("GROQ_API_KEY is missing. Set GROQ_API_KEY in your environment or Render settings.")
    return _parse_cloud_groq(img, resolved_key)


if __name__ == "__main__":
    res = extract_graph("sketch.jpg", mode="cloud")
    print(f"\n--- PARSED GRAPH [{res['parser_used']}] ---")
    print("Nodes:", [n["id"] for n in res["nodes"]])
    print("Edges:", res["edges"])