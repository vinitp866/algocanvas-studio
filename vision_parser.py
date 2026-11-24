import base64
import json
import math
import os
import urllib.error
import urllib.request
import cv2
import numpy as np
import onnxruntime as ort

DIGIT_MODEL_PATH = "mnist-12.onnx"
DIGIT_MODEL_URL = "https://github.com/onnx/models/raw/main/validated/vision/classification/mnist/model/mnist-12.onnx"
GROQ_MODEL = "qwen/qwen3.8-27b"

CLOUD_PROMPT = """Analyze this hand-drawn graph image.
Identify every circular node (with its label inside) and every edge connecting two nodes (with its weight number beside the line; use 1 if no weight is written).
Estimate each node's center position (x, y) on a 0 to 1000 scale where (0,0) is top-left and (1000,1000) is bottom-right.

Return ONLY valid JSON in this exact format:
{
  "nodes": [
    {"id": "1", "x": 200, "y": 300}
  ],
  "edges": [
    {"source": "1", "target": "2", "weight": 4}
  ]
}"""


class DigitEngine:
    """Offline MNIST-12 ONNX CNN for reading handwritten node numbers and edge weights."""
    def __init__(self):
        if not os.path.exists(DIGIT_MODEL_PATH):
            urllib.request.urlretrieve(DIGIT_MODEL_URL, DIGIT_MODEL_PATH)
        self.sess = ort.InferenceSession(DIGIT_MODEL_PATH, providers=["CPUExecutionProvider"])
        self.input_name = self.sess.get_inputs()[0].name

    def _to_mnist_tensor(self, binary_crop):
        ys, xs = np.where(binary_crop > 0)
        if len(xs) == 0 or len(ys) == 0:
            return None
        glyph = binary_crop[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        h, w = glyph.shape
        scale = 20.0 / max(h, w)
        nh, nw = max(1, int(h * scale)), max(1, int(w * scale))
        resized = cv2.resize(glyph, (nw, nh), interpolation=cv2.INTER_AREA)

        canvas = np.zeros((28, 28), dtype=np.float32)
        y_off, x_off = (28 - nh) // 2, (28 - nw) // 2
        canvas[y_off:y_off + nh, x_off:x_off + nw] = resized / 255.0
        return canvas.reshape(1, 1, 28, 28)

    def predict_single_digit(self, ink_crop):
        best_digit, best_conf = None, 0.0
        for angle in [-12, 0, 12]:
            if angle == 0:
                test_ink = ink_crop
            else:
                h, w = ink_crop.shape
                M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
                test_ink = cv2.warpAffine(ink_crop, M, (w, h), borderValue=0)

            tensor = self._to_mnist_tensor(test_ink)
            if tensor is None:
                continue
            logits = self.sess.run(None, {self.input_name: tensor})[0][0]
            exp_l = np.exp(logits - np.max(logits))
            probs = exp_l / np.sum(exp_l)
            idx = int(np.argmax(probs))
            if float(probs[idx]) > best_conf:
                best_conf = float(probs[idx])
                best_digit = str(idx)
        return best_digit, best_conf

    def predict_number(self, ink_crop, border_mask=None):
        num_labels, labels_img, stats, _ = cv2.connectedComponentsWithStats(ink_crop)
        blobs = []
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            x, y = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP]
            w, h = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            if area < 15 or max(w, h) < 8:
                continue
            if border_mask is not None and np.any(border_mask[labels_img == i] > 0):
                continue
            blobs.append((x, y, w, h, i))

        if not blobs:
            return None
        blobs.sort(key=lambda b: b[0])
        digits_str = ""
        for (x, y, w, h, cid) in blobs:
            sub_mask = ((labels_img[y:y + h, x:x + w] == cid).astype(np.uint8)) * 255
            d, conf = self.predict_single_digit(sub_mask)
            if d is not None and conf >= 0.45:
                digits_str += d
        return digits_str if digits_str else None


_digit_engine = None


def get_digit_engine():
    global _digit_engine
    if _digit_engine is None:
        _digit_engine = DigitEngine()
    return _digit_engine


def load_and_resize(image_bytes_or_path, target_max=900):
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
    return raw_img


def _parse_cloud_groq(img, api_key):
    """Online parser using Groq OpenAI-compatible vision chat completions endpoint."""
    h, w = img.shape[:2]
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise ValueError("Failed to encode image.")
    b64_img = base64.b64encode(buf.tobytes()).decode("utf-8")

    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.0,
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
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AlgoCanvas/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Groq HTTP {exc.code}: {detail}") from exc

    raw_text = data["choices"][0]["message"]["content"]
    parsed = json.loads(raw_text)

    nodes, seen_ids = [], set()
    for n in parsed.get("nodes", []):
        nid = str(n.get("id", "")).strip()
        if not nid or nid in seen_ids:
            continue
        seen_ids.add(nid)
        nx = int(float(n.get("x", 500)) / 1000.0 * w)
        ny = int(float(n.get("y", 500)) / 1000.0 * h)
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
            weight = max(1, int(float(e.get("weight", 1))))
        except (ValueError, TypeError):
            weight = 1
        edges.append({"source": u, "target": v, "weight": weight})

    return {"nodes": nodes, "edges": edges, "parser_used": f"cloud ({GROQ_MODEL})"}


def _perimeter_ink_ratio(ink_dilated, cx, cy, r, num_samples=36):
    h, w = ink_dilated.shape
    hits = 0
    for k in range(num_samples):
        theta = 2.0 * math.pi * k / num_samples
        px, py = int(round(cx + r * math.cos(theta))), int(round(cy + r * math.sin(theta)))
        if 0 <= px < w and 0 <= py < h and ink_dilated[py, px] > 0:
            hits += 1
    return hits / float(num_samples)


def _parse_offline_local(img):
    """Offline parser using OpenCV HoughCircles + MNIST-12 ONNX CNN."""
    engine = get_digit_engine()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    ink = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 8
    )
    ink_verify = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)), iterations=1)

    raw_circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
        param1=60, param2=22, minRadius=18, maxRadius=50
    )

    candidate_nodes = []
    if raw_circles is not None:
        for (cx, cy, r) in np.round(raw_circles[0, :]).astype("int"):
            ratio = _perimeter_ink_ratio(ink_verify, cx, cy, r)
            if ratio >= 0.55:
                candidate_nodes.append((cx, cy, r, ratio))

    candidate_nodes.sort(key=lambda x: x[3], reverse=True)
    filtered_circles = []
    for cx, cy, r, _ in candidate_nodes:
        if all(math.hypot(cx - fx, cy - fy) > max(r, fr) * 1.05 for fx, fy, fr in filtered_circles):
            filtered_circles.append((cx, cy, r))
    filtered_circles.sort(key=lambda c: (c[1] // 60, c[0]))

    nodes, used_ids = [], set()
    for idx, (x, y, r) in enumerate(filtered_circles):
        inner_r = max(6, int(r * 0.78))
        inner_mask = np.zeros_like(ink)
        cv2.circle(inner_mask, (x, y), inner_r, 255, -1)
        border_ring = np.zeros_like(ink)
        cv2.circle(border_ring, (x, y), inner_r, 255, 3)

        pred = engine.predict_number(cv2.bitwise_and(ink, inner_mask), border_mask=border_ring)
        if pred is None:
            tight = np.zeros_like(ink)
            cv2.circle(tight, (x, y), max(4, int(r * 0.60)), 255, -1)
            pred = engine.predict_number(cv2.bitwise_and(ink, tight), border_mask=None)

        node_id = pred if (pred and pred not in used_ids) else str(idx)
        while node_id in used_ids:
            idx += 1
            node_id = str(idx)
        used_ids.add(node_id)
        nodes.append({"id": node_id, "x": x, "y": y, "r": r})

    non_node_ink = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=2)
    raw_non_node_ink = ink.copy()
    for n in nodes:
        cv2.circle(non_node_ink, (n["x"], n["y"]), int(n["r"] * 1.18), 0, -1)
        cv2.circle(raw_non_node_ink, (n["x"], n["y"]), int(n["r"] * 1.18), 0, -1)

    num_labels, labels_img, stats, centroids = cv2.connectedComponentsWithStats(non_node_ink)
    edge_pairs, digit_boxes = set(), []
    for comp_id in range(1, num_labels):
        comp_area = stats[comp_id, cv2.CC_STAT_AREA]
        cw, ch = stats[comp_id, cv2.CC_STAT_WIDTH], stats[comp_id, cv2.CC_STAT_HEIGHT]
        if comp_area < 20:
            continue
        ys, xs = np.where(labels_img == comp_id)
        touched = {n["id"] for n in nodes if np.min(np.hypot(xs - n["x"], ys - n["y"])) <= n["r"] * 1.48}
        if len(touched) == 2 and math.hypot(cw, ch) >= 20:
            edge_pairs.add(tuple(sorted(list(touched))))
        elif len(touched) == 0 and 12 <= max(cw, ch) <= 55 and comp_area >= 30:
            digit_boxes.append((centroids[comp_id][0], centroids[comp_id][1],
                                stats[comp_id, cv2.CC_STAT_LEFT], stats[comp_id, cv2.CC_STAT_TOP], cw, ch))

    node_map = {n["id"]: n for n in nodes}
    edges = []
    for u, v in sorted(edge_pairs):
        mx, my = (node_map[u]["x"] + node_map[v]["x"]) // 2, (node_map[u]["y"] + node_map[v]["y"]) // 2
        edges.append({"source": u, "target": v, "weight": 1, "mx": mx, "my": my, "digits": []})

    for (cx, cy, x0, y0, cw, ch) in digit_boxes:
        best_edge, min_dist = None, 75
        for e in edges:
            d = math.hypot(cx - e["mx"], cy - e["my"])
            if d < min_dist:
                min_dist, best_edge = d, e
        if best_edge:
            best_edge["digits"].append((x0, y0, cw, ch))

    clean_edges = []
    for e in edges:
        if e["digits"]:
            e["digits"].sort(key=lambda b: b[0])
            w_str = ""
            for (x0, y0, cw, ch) in e["digits"]:
                d, conf = engine.predict_single_digit(raw_non_node_ink[y0:y0 + ch, x0:x0 + cw])
                if d is not None and conf >= 0.55:
                    w_str += d
            if w_str and int(w_str) > 0:
                e["weight"] = int(w_str)
        clean_edges.append({"source": e["source"], "target": e["target"], "weight": e["weight"]})

    return {"nodes": nodes, "edges": clean_edges, "parser_used": "offline (OpenCV + MNIST-12)"}


def extract_graph(image_bytes_or_path, mode="auto", api_key=None, save_debug=False):
    """
    Hybrid Graph Parser:
    - mode='auto': tries Groq Cloud API if api_key is set & online, else falls back to offline local CNN.
    - mode='cloud': forces Groq Cloud API.
    - mode='offline': forces local OpenCV + MNIST-12 ONNX.
    """
    img = load_and_resize(image_bytes_or_path, target_max=900)
    api_key = (api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()

    result = None
    if mode in ("auto", "cloud") and api_key:
        try:
            result = _parse_cloud_groq(img, api_key)
        except Exception as e:
            if mode == "cloud":
                raise RuntimeError(f"Cloud parser failed: {e}")
            print(f"[Hybrid Fallback] Groq cloud unavailable ({e}); switching to offline parser...")

    if result is None:
        result = _parse_offline_local(img)

    if save_debug:
        debug_img = img.copy()
        node_map = {n["id"]: n for n in result["nodes"]}
        for e in result["edges"]:
            u, v = node_map[e["source"]], node_map[e["target"]]
            dx, dy = v["x"] - u["x"], v["y"] - u["y"]
            dist = math.hypot(dx, dy)
            if dist > u["r"] + v["r"]:
                ux, uy = dx / dist, dy / dist
                p1 = (int(u["x"] + ux * u["r"]), int(u["y"] + uy * u["r"]))
                p2 = (int(v["x"] - ux * v["r"]), int(v["y"] - uy * v["r"]))
                cv2.line(debug_img, p1, p2, (0, 220, 255), 3)
            mx, my = (u["x"] + v["x"]) // 2, (u["y"] + v["y"]) // 2
            cv2.putText(debug_img, f"w={e['weight']}", (mx - 15, my - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)
        for n in result["nodes"]:
            cv2.circle(debug_img, (n["x"], n["y"]), n["r"], (0, 255, 0), 2)
            cv2.putText(debug_img, n["id"], (n["x"] - 12, n["y"] + 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
        cv2.imwrite("debug_result.jpg", debug_img)

    return result


if __name__ == "__main__":
    # Set $env:GROQ_API_KEY="your_key" in PowerShell to test Cloud mode, or leave unset for Offline mode
    res = extract_graph("sketch.jpg", mode="auto", save_debug=True)
    print(f"\n--- PARSED GRAPH [{res['parser_used']}] ---")
    print("Nodes:", [n["id"] for n in res["nodes"]])
    print("Edges:", res["edges"])
