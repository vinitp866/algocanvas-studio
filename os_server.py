import http.server
import socketserver
import webbrowser
import threading

PORT = 8050

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KernelPulse // OS Telemetry & Execution Visualizer</title>
<style>
  :root {
    --bg-base: #ede9e0;
    --bg-panel: #faf8f5;
    --bg-surface-2: #e4dfd4;
    --border-glow: rgba(17, 17, 16, 0.2);
    --accent-cyan: #2d4a3e;
    --accent-purple: #b04a2e;
    --accent-emerald: #143d2b;
    --accent-amber: #9e630c;
    --accent-rose: #9e2a2b;
    --text-main: #111110;
    --text-muted: #2b2926;
    --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background-color: var(--bg-base);
    color: var(--text-main);
    font-family: var(--font-sans);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background: var(--bg-panel);
    border-bottom: 1.5px solid var(--border-glow);
    gap: 14px;
    flex-wrap: wrap;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .pulse-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--accent-cyan);
    box-shadow: 0 0 8px rgba(45, 74, 62, 0.45);
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.35); opacity: 0.65; }
  }

  .brand h1 {
    font-size: 1.12rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #111110;
  }

  .nav-tabs {
    display: flex;
    gap: 6px;
    background: var(--bg-surface-2);
    padding: 4px;
    border-radius: 9px;
    border: 1.5px solid var(--border-glow);
  }

  .tab-btn, .top-link-btn {
    padding: 7px 13px;
    border-radius: 7px;
    border: 1.5px solid transparent;
    background: transparent;
    color: var(--text-muted);
    font-family: var(--font-mono);
    font-size: 0.78rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.16s ease;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
  }

  .top-link-btn {
    border-color: var(--border-glow);
    background: var(--bg-surface-2);
    color: #111110;
  }

  .tab-btn:hover, .top-link-btn:hover {
    color: #111110;
    background: #d8d2c5;
  }

  .tab-btn.active {
    background: var(--accent-cyan);
    border-color: var(--accent-cyan);
    color: #ffffff;
  }

  .hud-stats {
    display: flex;
    gap: 20px;
    font-family: var(--font-mono);
    font-size: 0.85rem;
  }

  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }

  .stat-label { color: var(--text-muted); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }
  .stat-val { color: var(--accent-cyan); font-weight: 800; font-size: 1.02rem; }

  .module-view {
    flex: 1 1 auto;
    min-height: 0;
    display: none;
    grid-template-columns: 344px minmax(0, 1fr);
    gap: 16px;
    padding: 16px 24px;
    overflow: hidden;
  }

  .module-view.active { display: grid; }

  .sidebar {
    display: flex;
    flex-direction: column;
    gap: 12px;
    overflow-y: auto;
    padding-right: 2px;
    min-height: 0;
  }

  .panel {
    background: var(--bg-panel);
    border: 1.5px solid var(--border-glow);
    border-radius: 14px;
    padding: 14px;
    box-shadow: 0 2px 10px rgba(17, 17, 16, 0.05);
  }

  .panel-title {
    font-size: 0.78rem;
    font-family: var(--font-mono);
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #111110;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .row-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 8px;
  }

  .row-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
    margin-bottom: 8px;
  }

  label.mini {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-family: var(--font-mono);
    font-size: 0.74rem;
    font-weight: 700;
    color: #111110;
  }

  select, input[type="number"], input[type="text"], input[type="range"] {
    background: #f4f1ea;
    border: 1.5px solid var(--border-glow);
    border-radius: 8px;
    color: #111110;
    font-family: var(--font-mono);
    font-size: 0.82rem;
    font-weight: 600;
    padding: 7px 9px;
    outline: none;
    width: 100%;
  }

  select:focus, input:focus { border-color: var(--accent-cyan); }

  .btn {
    padding: 8px 10px;
    border-radius: 8px;
    border: 1.5px solid var(--border-glow);
    background: var(--bg-surface-2);
    color: #111110;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.14s ease;
    display: inline-flex;
    justify-content: center;
    align-items: center;
    gap: 5px;
  }

  .btn:hover {
    background: #d8d2c5;
    border-color: rgba(45, 74, 62, 0.65);
  }

  .btn-play {
    border-color: var(--accent-cyan);
    background: var(--accent-cyan);
    color: #ffffff;
  }

  .btn-play:hover {
    background: #21382f;
    border-color: #21382f;
  }

  .btn-interrupt {
    border-color: rgba(158, 42, 43, 0.55);
    background: #f3d4d4;
    color: #6e1415;
  }

  .btn-amber {
    border-color: rgba(158, 99, 12, 0.55);
    background: #f5e2ba;
    color: #4a2c00;
  }

  .btn-purple {
    border-color: rgba(176, 74, 46, 0.55);
    background: #f3dcd5;
    color: #6b2613;
  }

  .btn-purple.active {
    border-color: var(--accent-purple);
    background: var(--accent-purple);
    color: #ffffff;
  }

  .pcb-table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--font-mono);
    font-size: 0.78rem;
  }

  .pcb-table th {
    text-align: left;
    color: #111110;
    padding: 5px 3px;
    border-bottom: 1.5px solid var(--border-glow);
    font-weight: 800;
  }

  .pcb-table td {
    padding: 4px 3px;
    border-bottom: 1px solid rgba(17, 17, 16, 0.1);
    color: #111110;
  }

  .pcb-table input {
    width: 46px;
    padding: 4px 5px;
    font-size: 0.76rem;
    font-weight: 700;
  }

  .pid-pill {
    display: inline-block;
    padding: 3px 7px;
    border-radius: 5px;
    font-weight: 800;
    color: #ffffff;
  }

  .log-box {
    height: 98px;
    background: #f2eee6;
    border: 1.5px solid var(--border-glow);
    border-radius: 8px;
    padding: 8px 10px;
    font-family: var(--font-mono);
    font-size: 0.76rem;
    font-weight: 500;
    color: #111110;
    overflow-y: auto;
    line-height: 1.5;
  }

  .log-entry span.time { color: #5c4b3b; font-weight: 700; }
  .log-entry span.tag { color: var(--accent-emerald); font-weight: 700; }
  .log-entry span.irq { color: var(--accent-rose); font-weight: 800; }
  .log-entry span.ctx { color: var(--accent-amber); font-weight: 700; }

  .stage {
    display: flex;
    flex-direction: column;
    gap: 12px;
    overflow: hidden;
    min-height: 0;
    height: 100%;
  }

  .metrics-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    flex-shrink: 0;
  }

  .metric-card {
    background: var(--bg-panel);
    border: 1.5px solid var(--border-glow);
    border-radius: 12px;
    padding: 10px 14px;
    font-family: var(--font-mono);
    box-shadow: 0 2px 8px rgba(17, 17, 16, 0.04);
  }

  .metric-card .m-label { font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; }
  .metric-card .m-val { font-size: 1.22rem; font-weight: 800; margin-top: 3px; color: #111110; }

  .canvas-wrap {
    flex: 1 1 0;
    position: relative;
    padding: 0;
    overflow: hidden;
    min-height: 240px;
    background: #eae4d7;
  }

  canvas {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    display: block;
  }

  .battle-panel {
    display: none;
    padding: 12px 15px;
    border-color: rgba(176, 74, 46, 0.55);
    flex-shrink: 0;
  }

  .battle-panel.active {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .battle-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    font-weight: 800;
    color: #111110;
  }

  .verdict-badge {
    padding: 4px 10px;
    border-radius: 999px;
    background: #f3dcd5;
    border: 1.5px solid rgba(176, 74, 46, 0.55);
    color: #6b2613;
    font-weight: 800;
  }

  .battle-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .lane-card {
    background: #f2eee6;
    border: 1.5px solid var(--border-glow);
    border-radius: 8px;
    padding: 9px 11px;
    font-family: var(--font-mono);
    font-size: 0.76rem;
    color: #111110;
  }

  .lane-top {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    font-weight: 800;
  }

  .lane-stats {
    display: flex;
    justify-content: space-between;
    color: var(--text-muted);
    margin-bottom: 6px;
    font-size: 0.72rem;
    font-weight: 700;
  }

  .mini-gantt {
    display: flex;
    height: 24px;
    gap: 2px;
    overflow-x: auto;
    align-items: stretch;
  }

  .mini-block {
    min-width: 18px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.66rem;
    font-weight: 800;
    color: #ffffff;
    flex-shrink: 0;
  }

  .gantt-panel { padding: 12px 15px; flex-shrink: 0; }

  .gantt-track {
    display: flex;
    height: 36px;
    background: #e4dfd4;
    border: 1.5px solid var(--border-glow);
    border-radius: 8px;
    overflow-x: auto;
    align-items: stretch;
    gap: 3px;
    padding: 4px;
  }

  .gantt-block {
    min-width: 26px;
    border-radius: 5px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-family: var(--font-mono);
    font-size: 0.74rem;
    font-weight: 800;
    color: #ffffff;
    flex-shrink: 0;
  }

  .gantt-idle {
    background: #d4cec2;
    color: #2b2926;
    font-weight: 700;
  }

  /* Virtual Memory Styles */
  .ref-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 6px;
  }

  .ref-chip {
    width: 32px;
    height: 32px;
    border-radius: 7px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-mono);
    font-size: 0.84rem;
    font-weight: 800;
    background: #f2eee6;
    border: 1.5px solid var(--border-glow);
    color: #111110;
    transition: all 0.2s ease;
  }

  .ref-chip.current {
    border-color: var(--accent-cyan);
    background: var(--accent-cyan);
    color: #ffffff;
    transform: scale(1.1);
  }

  .ref-chip.hit { border-color: rgba(20, 61, 43, 0.65); background: #cfe6da; color: #0f3323; }
  .ref-chip.fault { border-color: rgba(158, 42, 43, 0.6); background: #f3d4d4; color: #6e1415; }

  .mem-matrix-wrap {
    flex: 1;
    overflow-x: auto;
    overflow-y: auto;
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 4px;
  }

  .frame-labels {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding-top: 38px;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    font-weight: 800;
    color: #111110;
    flex-shrink: 0;
  }

  .frame-label-cell {
    height: 42px;
    display: flex;
    align-items: center;
    padding-right: 8px;
  }

  .mem-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    min-width: 52px;
    padding: 7px 6px;
    border-radius: 10px;
    background: #f2eee6;
    border: 1.5px solid var(--border-glow);
    flex-shrink: 0;
  }

  .mem-col.hit-col { border-color: rgba(20, 61, 43, 0.55); background: #e6f2ec; }
  .mem-col.fault-col { border-color: rgba(158, 42, 43, 0.5); background: #f7e6e6; }

  .mem-req-hdr {
    font-family: var(--font-mono);
    font-size: 0.9rem;
    font-weight: 800;
    color: #111110;
    padding-bottom: 2px;
  }

  .ram-slot {
    width: 42px;
    height: 42px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-mono);
    font-size: 0.95rem;
    font-weight: 800;
    background: #faf8f5;
    border: 1.5px solid var(--border-glow);
    color: #111110;
  }

  .ram-slot.new-load {
    border-color: #9e2a2b;
    background: #f3d4d4;
    color: #6e1415;
  }

  .ram-slot.hit-slot {
    border-color: #143d2b;
    background: #cfe6da;
    color: #0f3323;
  }

  .status-pill {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    font-weight: 800;
    padding: 3px 6px;
    border-radius: 5px;
  }

  .pill-hit { background: #cfe6da; color: #0f3323; border: 1px solid rgba(20, 61, 43, 0.45); }
  .pill-fault { background: #f3d4d4; color: #6e1415; border: 1px solid rgba(158, 42, 43, 0.45); }

  .seq-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    align-items: center;
  }

  .seq-chip {
    padding: 5px 10px;
    border-radius: 7px;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    font-weight: 800;
    background: #f2eee6;
    border: 1.5px solid var(--border-glow);
    color: #111110;
  }

  .seq-chip.done {
    border-color: rgba(20, 61, 43, 0.55);
    background: #cfe6da;
    color: #0f3323;
  }

  .seq-chip.next {
    border-color: rgba(158, 99, 12, 0.65);
    background: #f5e2ba;
    color: #4a2c00;
  }
  .app-footer {
    flex-shrink: 0;
    text-align: center;
    padding: 7px 24px;
    font-family: var(--font-mono);
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    background: var(--bg-panel);
    border-top: 1.5px solid var(--border-glow);
  }
</style>
</head>
<body>

<header>
  <div class="brand">
    <div class="pulse-dot"></div>
    <h1>KernelPulse</h1>
    <div class="nav-tabs">
      <button class="tab-btn active" id="tabCpuBtn" onclick="switchSubsystem('cpu')">[01] CPU SCHEDULER</button>
      <button class="tab-btn" id="tabMemBtn" onclick="switchSubsystem('mem')">[02] VIRTUAL MEMORY</button>
      <button class="tab-btn" id="tabDiskBtn" onclick="switchSubsystem('disk')">[03] DISK I/O</button>
    </div>
    <a class="top-link-btn" href="/">Graph Studio</a>
  </div>
  <div class="hud-stats">
    <div class="stat-item">
      <span class="stat-label" id="hudLabel1">Tick / Clock</span>
      <span class="stat-val" id="clockVal">t = 0</span>
    </div>
    <div class="stat-item">
      <span class="stat-label" id="hudLabel2">Running Core</span>
      <span class="stat-val" id="runningVal" style="color: var(--accent-purple);">IDLE</span>
    </div>
    <div class="stat-item">
      <span class="stat-label" id="hudLabel3">CPU Load</span>
      <span class="stat-val" id="loadVal" style="color: var(--accent-emerald);">0%</span>
    </div>
  </div>
</header>

<main class="module-view active" id="cpuModule">
  <aside class="sidebar">
    <div class="panel">
      <div class="panel-title">Scheduler Policy</div>
      <div class="row-2">
        <label class="mini">
          Primary Algo
          <select id="algoSelect" onchange="resetSim()">
            <option value="FCFS">FCFS</option>
            <option value="SJF">SJF (Non-Preemptive)</option>
            <option value="SRTF">SRTF (Preemptive)</option>
            <option value="RR" selected>Round Robin (RR)</option>
            <option value="PRIORITY">Priority (Preemptive)</option>
          </select>
        </label>
        <label class="mini">
          Quantum (ticks)
          <input type="number" id="quantumInput" value="2" min="1" max="10" onchange="resetSim()">
        </label>
      </div>

      <div class="row-2">
        <label class="mini">
          Battle Challenger
          <select id="challengerSelect" onchange="resetSim()">
            <option value="FCFS" selected>FCFS</option>
            <option value="SJF">SJF</option>
            <option value="SRTF">SRTF</option>
            <option value="RR">Round Robin (RR)</option>
            <option value="PRIORITY">Priority</option>
          </select>
        </label>
        <label class="mini" style="justify-content: flex-end;">
          <span>Battle Mode</span>
          <button class="btn btn-purple" id="battleToggleBtn" onclick="toggleBattleMode()">⚔ Off</button>
        </label>
      </div>

      <div class="row-3">
        <button class="btn btn-play" id="playBtn" onclick="togglePlay()">▶ Run</button>
        <button class="btn" onclick="stepTick()">⏭ Step</button>
        <button class="btn btn-amber" onclick="resetSim()">↺ Reset</button>
      </div>

      <label class="mini" style="margin-top: 2px;">
        <span>Speed: <strong id="speedLabel" style="color:var(--accent-cyan);">1.0x</strong></span>
        <input type="range" id="speedSlider" min="0.5" max="3" step="0.5" value="1" oninput="updateSpeed()">
      </label>
    </div>

    <div class="panel">
      <div class="panel-title">
        <span>Process Control Blocks</span>
        <span style="display:flex; gap:5px;">
          <button class="btn" style="padding:3px 7px; font-size:0.68rem;" onclick="loadPreset('convoy')">Convoy</button>
          <button class="btn" style="padding:3px 7px; font-size:0.68rem;" onclick="addProcessRow()">+ PCB</button>
        </span>
      </div>
      <table class="pcb-table">
        <thead>
          <tr>
            <th>PID</th>
            <th>AT</th>
            <th>BT</th>
            <th>PRIO</th>
            <th>REM</th>
          </tr>
        </thead>
        <tbody id="pcbBody"></tbody>
      </table>
    </div>

    <div class="panel">
      <div class="panel-title">Live Chaos & Kernel Log</div>
      <div class="row-2">
        <button class="btn" onclick="spawnDynamicProcess()">+ Spawn PCB</button>
        <button class="btn btn-interrupt" onclick="triggerInterrupt()">⚡ Inject IRQ</button>
      </div>
      <div class="log-box" id="kernelLog"></div>
    </div>
  </aside>

  <section class="stage">
    <div class="metrics-strip">
      <div class="metric-card">
        <div class="m-label">Avg Waiting Time</div>
        <div class="m-val" id="avgWt" style="color: var(--accent-cyan);">0.00</div>
      </div>
      <div class="metric-card">
        <div class="m-label">Avg Turnaround Time</div>
        <div class="m-val" id="avgTat" style="color: var(--accent-emerald);">0.00</div>
      </div>
      <div class="metric-card">
        <div class="m-label">CPU Utilization</div>
        <div class="m-val" id="cpuUtil" style="color: var(--accent-amber);">0.0%</div>
      </div>
      <div class="metric-card">
        <div class="m-label">Context Switches</div>
        <div class="m-val" id="ctxCount" style="color: var(--accent-purple);">0</div>
      </div>
    </div>

    <div class="panel canvas-wrap">
      <canvas id="pipelineCanvas"></canvas>
    </div>

    <div class="panel battle-panel" id="battlePanel">
      <div class="battle-header">
        <span>⚔ SIDE-BY-SIDE SCHEDULER RACE (IDENTICAL WORKLOAD)</span>
        <span class="verdict-badge" id="battleVerdict">RACING...</span>
      </div>
      <div class="battle-grid">
        <div class="lane-card">
          <div class="lane-top">
            <span id="lane1Title" style="color:var(--accent-cyan);">PRIMARY: RR</span>
            <span id="lane1Run">IDLE</span>
          </div>
          <div class="lane-stats" id="lane1Stats">WT: 0.00 | TAT: 0.00 | CTX: 0</div>
          <div class="mini-gantt" id="lane1Gantt"></div>
        </div>
        <div class="lane-card">
          <div class="lane-top">
            <span id="lane2Title" style="color:var(--accent-purple);">CHALLENGER: FCFS</span>
            <span id="lane2Run">IDLE</span>
          </div>
          <div class="lane-stats" id="lane2Stats">WT: 0.00 | TAT: 0.00 | CTX: 0</div>
          <div class="mini-gantt" id="lane2Gantt"></div>
        </div>
      </div>
    </div>

    <div class="panel gantt-panel">
      <div class="panel-title" style="margin-bottom: 6px;">
        <span>Live Execution Gantt Timeline</span>
        <span id="ganttSummary" style="color: var(--accent-cyan);">0 ticks recorded</span>
      </div>
      <div class="gantt-track" id="ganttTrack"></div>
    </div>
  </section>
</main>

<main class="module-view" id="memModule">
  <aside class="sidebar">
    <div class="panel">
      <div class="panel-title">MMU & Paging Policy</div>
      <div class="row-2">
        <label class="mini">
          Replacement Algo
          <select id="memAlgoSelect" onchange="resetMemSim()">
            <option value="FIFO">FIFO (First-In First-Out)</option>
            <option value="LRU" selected>LRU (Least Recently Used)</option>
            <option value="OPT">OPT (Optimal Lookahead)</option>
          </select>
        </label>
        <label class="mini">
          Physical Frames
          <select id="frameCountSelect" onchange="resetMemSim()">
            <option value="3" selected>3 Frames</option>
            <option value="4">4 Frames</option>
            <option value="5">5 Frames</option>
            <option value="6">6 Frames</option>
          </select>
        </label>
      </div>

      <label class="mini" style="margin-bottom: 8px;">
        Page Reference String (comma/space separated)
        <input type="text" id="refStringInput" value="7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2" onchange="resetMemSim()">
      </label>

      <div class="row-2" style="margin-bottom: 8px;">
        <button class="btn btn-purple" onclick="loadBeladyPreset()">⚠ Belady's Anomaly</button>
        <button class="btn" onclick="randomizeRefString()">🎲 Random Stream</button>
      </div>

      <div class="row-3">
        <button class="btn btn-play" id="memPlayBtn" onclick="toggleMemPlay()">▶ Run</button>
        <button class="btn" onclick="stepMemTick()">⏭ Step</button>
        <button class="btn btn-amber" onclick="resetMemSim()">↺ Reset</button>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">Virtual Address Stream</div>
      <div class="ref-strip" id="refStrip"></div>
    </div>

    <div class="panel" style="flex:1; display:flex; flex-direction:column;">
      <div class="panel-title">MMU Telemetry Log</div>
      <div class="log-box" id="memLog" style="flex:1; height:auto;"></div>
    </div>
  </aside>

  <section class="stage">
    <div class="metrics-strip">
      <div class="metric-card">
        <div class="m-label">Page Faults</div>
        <div class="m-val" id="memFaults" style="color: var(--accent-rose);">0</div>
      </div>
      <div class="metric-card">
        <div class="m-label">Page Hits</div>
        <div class="m-val" id="memHits" style="color: var(--accent-emerald);">0</div>
      </div>
      <div class="metric-card">
        <div class="m-label">Hit Ratio</div>
        <div class="m-val" id="memHitRatio" style="color: var(--accent-cyan);">0.0%</div>
      </div>
      <div class="metric-card">
        <div class="m-label">Last MMU Event</div>
        <div class="m-val" id="memLastEvent" style="color: var(--accent-amber);">READY</div>
      </div>
    </div>

    <div class="panel" style="flex:1; display:flex; flex-direction:column; overflow:hidden;">
      <div class="panel-title">
        <span>Physical RAM Frame Allocation Matrix</span>
        <span id="memProgressLabel" style="color: var(--accent-cyan);">Step 0 / 0</span>
      </div>
      <div class="mem-matrix-wrap" id="memMatrixWrap"></div>
    </div>
  </section>
</main>

<main class="module-view" id="diskModule">
  <aside class="sidebar">
    <div class="panel">
      <div class="panel-title">HDD Controller Policy</div>
      <div class="row-2">
        <label class="mini">
          Seek Algorithm
          <select id="diskAlgoSelect" onchange="resetDiskSim()">
            <option value="FCFS">FCFS</option>
            <option value="SSTF" selected>SSTF (Shortest Seek)</option>
            <option value="SCAN">SCAN (Elevator)</option>
            <option value="CSCAN">C-SCAN (Circular)</option>
            <option value="LOOK">LOOK</option>
          </select>
        </label>
        <label class="mini">
          Sweep Direction
          <select id="diskDirSelect" onchange="resetDiskSim()">
            <option value="UP" selected>UP (→ Max Cyl)</option>
            <option value="DOWN">DOWN (← Cyl 0)</option>
          </select>
        </label>
      </div>

      <div class="row-2">
        <label class="mini">
          Initial Head Cyl
          <input type="number" id="diskHeadInput" value="53" min="0" max="199" onchange="resetDiskSim()">
        </label>
        <label class="mini">
          Max Cylinder
          <input type="number" id="diskMaxInput" value="199" min="50" max="999" onchange="resetDiskSim()">
        </label>
      </div>

      <label class="mini" style="margin-bottom: 8px;">
        I/O Cylinder Requests
        <input type="text" id="diskQueueInput" value="98, 183, 37, 122, 14, 124, 65, 67" onchange="resetDiskSim()">
      </label>

      <div class="row-2" style="margin-bottom: 8px;">
        <button class="btn" onclick="randomizeDiskQueue()">🎲 Random Queue</button>
        <button class="btn btn-interrupt" onclick="injectDiskSeek()">⚡ Burst Seek</button>
      </div>

      <div class="row-3">
        <button class="btn btn-play" id="diskPlayBtn" onclick="toggleDiskPlay()">▶ Run</button>
        <button class="btn" onclick="stepDiskTick()">⏭ Step</button>
        <button class="btn btn-amber" onclick="resetDiskSim()">↺ Reset</button>
      </div>
    </div>

    <div class="panel" style="flex:1; display:flex; flex-direction:column;">
      <div class="panel-title">Actuator Telemetry Log</div>
      <div class="log-box" id="diskLog" style="flex:1; height:auto;"></div>
    </div>
  </aside>

  <section class="stage">
    <div class="metrics-strip">
      <div class="metric-card">
        <div class="m-label">Total Head Seek</div>
        <div class="m-val" id="diskTotalSeek" style="color: var(--accent-cyan);">0 cyl</div>
      </div>
      <div class="metric-card">
        <div class="m-label">Avg Seek Distance</div>
        <div class="m-val" id="diskAvgSeek" style="color: var(--accent-emerald);">0.0</div>
      </div>
      <div class="metric-card">
        <div class="m-label">Current Head Cyl</div>
        <div class="m-val" id="diskCurrHead" style="color: var(--accent-amber);">53</div>
      </div>
      <div class="metric-card">
        <div class="m-label">Requests Serviced</div>
        <div class="m-val" id="diskServiced" style="color: var(--accent-purple);">0 / 8</div>
      </div>
    </div>

    <div class="panel canvas-wrap">
      <canvas id="diskCanvas"></canvas>
    </div>

    <div class="panel gantt-panel">
      <div class="panel-title" style="margin-bottom: 6px;">
        <span>Scheduled Service Order</span>
        <span id="diskOrderMeta" style="color: var(--accent-cyan);">Waiting to run</span>
      </div>
      <div class="seq-chips" id="diskOrderChips"></div>
    </div>
  </section>
</main>
<footer class="app-footer">Made by Vinit</footer>
<script>
  let activeSubsystem = 'cpu';

  function switchSubsystem(sub) {
    activeSubsystem = sub;
    document.getElementById('tabCpuBtn').classList.toggle('active', sub === 'cpu');
    document.getElementById('tabMemBtn').classList.toggle('active', sub === 'mem');
    document.getElementById('tabDiskBtn').classList.toggle('active', sub === 'disk');

    document.getElementById('cpuModule').classList.toggle('active', sub === 'cpu');
    document.getElementById('memModule').classList.toggle('active', sub === 'mem');
    document.getElementById('diskModule').classList.toggle('active', sub === 'disk');

    requestAnimationFrame(() => {
      resize();
      if (sub === 'cpu') {
        document.getElementById('hudLabel1').textContent = 'Tick / Clock';
        document.getElementById('hudLabel2').textContent = 'Running Core';
        document.getElementById('hudLabel3').textContent = 'CPU Load';
        updateMetrics();
      } else if (sub === 'mem') {
        document.getElementById('hudLabel1').textContent = 'Memory Ref';
        document.getElementById('hudLabel2').textContent = 'MMU Policy';
        document.getElementById('hudLabel3').textContent = 'Hit Ratio';
        updateMemHud();
      } else {
        document.getElementById('hudLabel1').textContent = 'Head Cyl';
        document.getElementById('hudLabel2').textContent = 'Seek Algo';
        document.getElementById('hudLabel3').textContent = 'Total Seek';
        updateDiskHud();
        renderDiskCanvas(0.016);
      }
    });
  }

  const COLORS = ['#2d4a3e', '#b04a2e', '#9e630c', '#4a5899', '#8c3b5e', '#1e6b63', '#6b4c35'];

  const DEFAULT_PROCS = [
    { pid: 'P1', at: 0, bt: 5, prio: 2, color: COLORS[0] },
    { pid: 'P2', at: 1, bt: 3, prio: 1, color: COLORS[1] },
    { pid: 'P3', at: 2, bt: 4, prio: 3, color: COLORS[2] },
    { pid: 'P4', at: 4, bt: 2, prio: 1, color: COLORS[3] }
  ];

  const CONVOY_PROCS = [
    { pid: 'P1', at: 0, bt: 12, prio: 3, color: COLORS[0] },
    { pid: 'P2', at: 1, bt: 2,  prio: 1, color: COLORS[1] },
    { pid: 'P3', at: 2, bt: 2,  prio: 1, color: COLORS[2] },
    { pid: 'P4', at: 3, bt: 1,  prio: 1, color: COLORS[3] }
  ];

  let baseProcs = JSON.parse(JSON.stringify(DEFAULT_PROCS));
  let battleMode = false;
  let isPlaying = false;
  let speedMult = 1.0;
  let tickAccumulator = 0;
  let lastFrameTime = performance.now();

  let sparks = [];
  let ctxFlash = 0;

  let primaryEngine = null;
  let challengerEngine = null;

  const canvas = document.getElementById('pipelineCanvas');
  const ctx = canvas.getContext('2d');
  const diskCanvas = document.getElementById('diskCanvas');
  const diskCtx = diskCanvas.getContext('2d');
  const logBox = document.getElementById('kernelLog');

  function syncCanvasSize(c) {
    if (!c || !c.parentElement) return;
    const rect = c.parentElement.getBoundingClientRect();
    const w = Math.floor(rect.width);
    const h = Math.floor(rect.height);
    if (w > 0 && h > 0 && (c.width !== w || c.height !== h)) {
      c.width = w;
      c.height = h;
    }
  }

  function resize() {
    syncCanvasSize(canvas);
    syncCanvasSize(diskCanvas);
  }
  window.addEventListener('resize', resize);
  resize();

  function addLog(tag, msg, cls = 'tag', tVal = null) {
    const t = tVal !== null ? tVal : (primaryEngine ? primaryEngine.tick : 0);
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.innerHTML = `<span class="time">[t=${t}]</span> <span class="${cls}">[${tag}]</span> ${msg}`;
    logBox.appendChild(div);
    logBox.scrollTop = logBox.scrollHeight;
  }

  function createEngine(algo, quantum, sourceProcs) {
    return {
      algo,
      quantum,
      tick: 0,
      quantumUsed: 0,
      contextSwitches: 0,
      busyTicks: 0,
      procs: sourceProcs.map(p => ({
        ...p,
        rem: p.bt,
        startTime: null,
        finishTime: null,
        waitingTime: 0,
        turnaroundTime: 0,
        arrived: false
      })),
      readyQueue: [],
      runningProc: null,
      completedProcs: [],
      ganttHistory: []
    };
  }

  function pickFromReady(eng) {
    if (eng.readyQueue.length === 0) return null;
    if (eng.algo === 'FCFS' || eng.algo === 'RR') return eng.readyQueue.shift();
    if (eng.algo === 'SJF' || eng.algo === 'SRTF') {
      eng.readyQueue.sort((a, b) => a.rem - b.rem || a.at - b.at);
      return eng.readyQueue.shift();
    }
    if (eng.algo === 'PRIORITY') {
      eng.readyQueue.sort((a, b) => a.prio - b.prio || a.at - b.at);
      return eng.readyQueue.shift();
    }
    return eng.readyQueue.shift();
  }

  function advanceEngine(eng, logEvents = false) {
    const totalCount = eng.procs.length;
    if (eng.completedProcs.length === totalCount && totalCount > 0) return;

    for (const p of eng.procs) {
      if (!p.arrived && p.at <= eng.tick) {
        p.arrived = true;
        eng.readyQueue.push(p);
        if (logEvents) addLog('ARRIVE', `<b>${p.pid}</b> entered Ready Queue (BT=${p.bt}, PRIO=${p.prio}).`, 'tag', eng.tick);
      }
    }

    if (eng.runningProc) {
      if (eng.algo === 'SRTF' && eng.readyQueue.length > 0) {
        const shortest = [...eng.readyQueue].sort((a, b) => a.rem - b.rem)[0];
        if (shortest && shortest.rem < eng.runningProc.rem) {
          eng.readyQueue.push(eng.runningProc);
          eng.runningProc = null;
          eng.quantumUsed = 0;
          eng.contextSwitches++;
          if (logEvents) {
            ctxFlash = 0.8;
            addLog('PREEMPT', `SRTF preempted by <b>${shortest.pid}</b> (rem ${shortest.rem}).`, 'ctx', eng.tick);
          }
        }
      } else if (eng.algo === 'PRIORITY' && eng.readyQueue.length > 0) {
        const higher = [...eng.readyQueue].sort((a, b) => a.prio - b.prio)[0];
        if (higher && higher.prio < eng.runningProc.prio) {
          eng.readyQueue.push(eng.runningProc);
          eng.runningProc = null;
          eng.quantumUsed = 0;
          eng.contextSwitches++;
          if (logEvents) {
            ctxFlash = 0.8;
            addLog('PREEMPT', `Higher priority <b>${higher.pid}</b> (P=${higher.prio}) preempted core.`, 'ctx', eng.tick);
          }
        }
      } else if (eng.algo === 'RR' && eng.quantumUsed >= eng.quantum && eng.runningProc.rem > 0) {
        eng.readyQueue.push(eng.runningProc);
        eng.runningProc = null;
        eng.quantumUsed = 0;
        eng.contextSwitches++;
        if (logEvents) {
          ctxFlash = 0.65;
          addLog('QUANTUM', `Time quantum (${eng.quantum}) expired; rotated process.`, 'ctx', eng.tick);
        }
      }
    }

    if (!eng.runningProc && eng.readyQueue.length > 0) {
      const next = pickFromReady(eng);
      if (eng.ganttHistory.length > 0) {
        const last = eng.ganttHistory[eng.ganttHistory.length - 1];
        if (last.pid !== 'IDLE' && last.pid !== next.pid) eng.contextSwitches++;
      }
      eng.runningProc = next;
      eng.quantumUsed = 0;
      if (eng.runningProc.startTime === null) eng.runningProc.startTime = eng.tick;
      if (logEvents) addLog('DISPATCH', `<b>${eng.runningProc.pid}</b> executing on CPU Core 0.`, 'tag', eng.tick);
    }

    if (eng.runningProc) {
      eng.runningProc.rem -= 1;
      eng.quantumUsed += 1;
      eng.busyTicks += 1;
      eng.ganttHistory.push({ pid: eng.runningProc.pid, color: eng.runningProc.color, t: eng.tick });

      for (const w of eng.readyQueue) w.waitingTime += 1;

      if (eng.runningProc.rem <= 0) {
        eng.runningProc.finishTime = eng.tick + 1;
        eng.runningProc.turnaroundTime = eng.runningProc.finishTime - eng.runningProc.at;
        eng.completedProcs.push(eng.runningProc);
        if (logEvents) {
          addLog('DONE', `<b>${eng.runningProc.pid}</b> finished at t=${eng.runningProc.finishTime} (TAT=${eng.runningProc.turnaroundTime}, WT=${eng.runningProc.waitingTime}).`, 'tag', eng.tick);
        }
        eng.runningProc = null;
        eng.quantumUsed = 0;
      }
    } else {
      eng.ganttHistory.push({ pid: 'IDLE', color: null, t: eng.tick });
      for (const w of eng.readyQueue) w.waitingTime += 1;
    }

    eng.tick += 1;
  }

  function getEngineMetrics(eng) {
    const avgWt = eng.procs.length > 0
      ? eng.procs.reduce((s, p) => s + p.waitingTime, 0) / eng.procs.length : 0;
    const avgTat = eng.completedProcs.length > 0
      ? eng.completedProcs.reduce((s, p) => s + p.turnaroundTime, 0) / eng.completedProcs.length : 0;
    const util = eng.tick > 0 ? (eng.busyTicks / eng.tick) * 100 : 0;
    return { avgWt, avgTat, util, ctx: eng.contextSwitches };
  }

  function toggleBattleMode() {
    battleMode = !battleMode;
    const btn = document.getElementById('battleToggleBtn');
    const panel = document.getElementById('battlePanel');
    btn.textContent = battleMode ? '⚔ Active' : '⚔ Off';
    btn.classList.toggle('active', battleMode);
    panel.classList.toggle('active', battleMode);
    resize();
    resetSim();
  }

  function updateSpeed() {
    speedMult = parseFloat(document.getElementById('speedSlider').value);
    document.getElementById('speedLabel').textContent = speedMult.toFixed(1) + 'x';
  }

  function loadPreset(type) {
    baseProcs = JSON.parse(JSON.stringify(type === 'convoy' ? CONVOY_PROCS : DEFAULT_PROCS));
    resetSim();
    addLog('PRESET', `Loaded <b>${type.toUpperCase()}</b> workload.`);
  }

  function addProcessRow() {
    const nextNum = baseProcs.length + 1;
    baseProcs.push({
      pid: 'P' + nextNum,
      at: 0,
      bt: Math.floor(Math.random() * 5) + 2,
      prio: Math.floor(Math.random() * 4) + 1,
      color: COLORS[(nextNum - 1) % COLORS.length]
    });
    resetSim();
  }

  function spawnDynamicProcess() {
    const nextNum = baseProcs.length + 1;
    const p = {
      pid: 'P' + nextNum,
      at: primaryEngine.tick,
      bt: Math.floor(Math.random() * 4) + 2,
      prio: 0,
      color: COLORS[(nextNum - 1) % COLORS.length]
    };
    baseProcs.push(p);

    const runtimeP = { ...p, rem: p.bt, startTime: null, finishTime: null, waitingTime: 0, turnaroundTime: 0, arrived: true };
    primaryEngine.procs.push(runtimeP);
    primaryEngine.readyQueue.push(runtimeP);

    if (battleMode && challengerEngine) {
      const chalP = { ...p, rem: p.bt, startTime: null, finishTime: null, waitingTime: 0, turnaroundTime: 0, arrived: true };
      challengerEngine.procs.push(chalP);
      challengerEngine.readyQueue.push(chalP);
    }

    renderPcbTable();
    addLog('SPAWN', `Dynamic PCB <b>${p.pid}</b> (BT=${p.bt}, PRIO=${p.prio}) joined Ready Queue.`);
  }

  function triggerInterrupt() {
    ctxFlash = 1.0;
    const cx = canvas.width * 0.66;
    const cy = canvas.height * 0.46;
    for (let i = 0; i < 26; i++) {
      const a = Math.random() * Math.PI * 2;
      const spd = 2 + Math.random() * 4.5;
      sparks.push({ x: cx, y: cy, vx: Math.cos(a) * spd, vy: Math.sin(a) * spd, life: 1.0 });
    }
    if (primaryEngine.runningProc && primaryEngine.algo !== 'FCFS') {
      const prev = primaryEngine.runningProc;
      primaryEngine.readyQueue.push(prev);
      primaryEngine.runningProc = null;
      primaryEngine.quantumUsed = 0;
      primaryEngine.contextSwitches++;
      addLog('IRQ-0', `Interrupt preempted <b>${prev.pid}</b> -> returned to Ready Queue.`, 'irq');
    } else {
      addLog('IRQ-0', `Hardware IRQ pulse observed on bus.`, 'irq');
    }
    renderPcbTable();
  }

  function resetSim() {
    isPlaying = false;
    document.getElementById('playBtn').textContent = '▶ Run';
    tickAccumulator = 0;
    logBox.innerHTML = '';

    const algo = document.getElementById('algoSelect').value;
    const chalAlgo = document.getElementById('challengerSelect').value;
    const quantum = Math.max(1, parseInt(document.getElementById('quantumInput').value) || 2);

    primaryEngine = createEngine(algo, quantum, baseProcs);
    challengerEngine = battleMode ? createEngine(chalAlgo, quantum, baseProcs) : null;

    addLog('INIT', `Engine ready (${algo}${battleMode ? ' vs ' + chalAlgo : ''}).`);
    renderPcbTable();
    renderGantt();
    updateMetrics();
    renderBattleUI();
  }

  function togglePlay() {
    isPlaying = !isPlaying;
    document.getElementById('playBtn').textContent = isPlaying ? '⏸ Pause' : '▶ Run';
  }

  function stepTick() {
    advanceEngine(primaryEngine, true);
    if (battleMode && challengerEngine) advanceEngine(challengerEngine, false);

    renderPcbTable();
    renderGantt();
    updateMetrics();
    renderBattleUI();

    const pDone = primaryEngine.completedProcs.length === primaryEngine.procs.length && primaryEngine.procs.length > 0;
    const cDone = !battleMode || (challengerEngine && challengerEngine.completedProcs.length === challengerEngine.procs.length);
    if (pDone && cDone && isPlaying) {
      isPlaying = false;
      document.getElementById('playBtn').textContent = '▶ Run';
      addLog('COMPLETE', `Execution completed.`);
    }
  }

  function renderPcbTable() {
    const tbody = document.getElementById('pcbBody');
    tbody.innerHTML = '';
    primaryEngine.procs.forEach((p, idx) => {
      const tr = document.createElement('tr');
      const statusBadge = primaryEngine.runningProc && primaryEngine.runningProc.pid === p.pid
        ? '▶' : (p.rem === 0 ? '✓' : p.rem);
      tr.innerHTML = `
        <td><span class="pid-pill" style="background:${p.color}">${p.pid}</span></td>
        <td><input type="number" min="0" max="30" value="${baseProcs[idx].at}" onchange="editBase(${idx}, 'at', this.value)"></td>
        <td><input type="number" min="1" max="20" value="${baseProcs[idx].bt}" onchange="editBase(${idx}, 'bt', this.value)"></td>
        <td><input type="number" min="0" max="10" value="${baseProcs[idx].prio}" onchange="editBase(${idx}, 'prio', this.value)"></td>
        <td style="font-weight:800; color:${p.rem === 0 ? 'var(--accent-emerald)' : '#111110'}">${statusBadge}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  function editBase(idx, field, val) {
    const num = Math.max(field === 'bt' ? 1 : 0, parseInt(val) || 0);
    baseProcs[idx][field] = num;
    resetSim();
  }

  function renderGantt() {
    const track = document.getElementById('ganttTrack');
    track.innerHTML = '';
    primaryEngine.ganttHistory.forEach(item => {
      const div = document.createElement('div');
      if (item.pid === 'IDLE') {
        div.className = 'gantt-block gantt-idle';
        div.textContent = '·';
        div.title = `t=${item.t}: IDLE`;
      } else {
        div.className = 'gantt-block';
        div.style.background = item.color;
        div.textContent = item.pid;
        div.title = `t=${item.t}: ${item.pid}`;
      }
      track.appendChild(div);
    });
    track.scrollLeft = track.scrollWidth;
    document.getElementById('ganttSummary').textContent = `${primaryEngine.ganttHistory.length} ticks recorded`;
  }

  function renderMiniGantt(containerId, history) {
    const el = document.getElementById(containerId);
    el.innerHTML = '';
    history.forEach(item => {
      const b = document.createElement('div');
      b.className = 'mini-block';
      if (item.pid === 'IDLE') {
        b.style.background = '#d4cec2';
        b.style.color = '#2b2926';
        b.textContent = '·';
      } else {
        b.style.background = item.color;
        b.textContent = item.pid;
      }
      el.appendChild(b);
    });
    el.scrollLeft = el.scrollWidth;
  }

  function renderBattleUI() {
    if (!battleMode || !challengerEngine) return;
    const m1 = getEngineMetrics(primaryEngine);
    const m2 = getEngineMetrics(challengerEngine);

    document.getElementById('lane1Title').textContent = `PRIMARY: ${primaryEngine.algo}`;
    document.getElementById('lane2Title').textContent = `CHALLENGER: ${challengerEngine.algo}`;
    document.getElementById('lane1Run').textContent = primaryEngine.runningProc ? `RUN ${primaryEngine.runningProc.pid}` : 'DONE/IDLE';
    document.getElementById('lane2Run').textContent = challengerEngine.runningProc ? `RUN ${challengerEngine.runningProc.pid}` : 'DONE/IDLE';

    document.getElementById('lane1Stats').textContent = `WT: ${m1.avgWt.toFixed(2)} | TAT: ${m1.avgTat.toFixed(2)} | CTX: ${m1.ctx}`;
    document.getElementById('lane2Stats').textContent = `WT: ${m2.avgWt.toFixed(2)} | TAT: ${m2.avgTat.toFixed(2)} | CTX: ${m2.ctx}`;

    renderMiniGantt('lane1Gantt', primaryEngine.ganttHistory);
    renderMiniGantt('lane2Gantt', challengerEngine.ganttHistory);

    const pDone = primaryEngine.completedProcs.length === primaryEngine.procs.length && primaryEngine.procs.length > 0;
    const cDone = challengerEngine.completedProcs.length === challengerEngine.procs.length && challengerEngine.procs.length > 0;
    const verdictEl = document.getElementById('battleVerdict');

    if (pDone && cDone) {
      if (m1.avgWt < m2.avgWt - 0.001) {
        verdictEl.textContent = `🏆 ${primaryEngine.algo} WINS LOWER WAIT (${m1.avgWt.toFixed(2)} vs ${m2.avgWt.toFixed(2)})`;
      } else if (m2.avgWt < m1.avgWt - 0.001) {
        verdictEl.textContent = `🏆 ${challengerEngine.algo} WINS LOWER WAIT (${m2.avgWt.toFixed(2)} vs ${m1.avgWt.toFixed(2)})`;
      } else {
        verdictEl.textContent = `🤝 TIED ON AVG WAIT (${m1.avgWt.toFixed(2)})`;
      }
    } else {
      verdictEl.textContent = `RACING... (P:${primaryEngine.completedProcs.length}/${primaryEngine.procs.length} | C:${challengerEngine.completedProcs.length}/${challengerEngine.procs.length})`;
    }
  }

  function updateMetrics() {
    const m = getEngineMetrics(primaryEngine);
    if (activeSubsystem === 'cpu') {
      document.getElementById('clockVal').textContent = `t = ${primaryEngine.tick}`;
      document.getElementById('runningVal').textContent = primaryEngine.runningProc ? primaryEngine.runningProc.pid : 'IDLE';
      document.getElementById('loadVal').textContent = `${m.util.toFixed(0)}%`;
    }
    document.getElementById('cpuUtil').textContent = `${m.util.toFixed(1)}%`;
    document.getElementById('ctxCount').textContent = String(m.ctx);
    document.getElementById('avgWt').textContent = m.avgWt.toFixed(2);
    document.getElementById('avgTat').textContent = m.avgTat.toFixed(2);
  }

  function drawBox(x, y, w, h, title, sub, color) {
    ctx.save();
    ctx.fillStyle = '#faf8f5';
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    ctx.rect(x - w/2, y - h/2, w, h);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#111110';
    ctx.font = '800 13px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(title, x, y - 5);

    ctx.fillStyle = '#2b2926';
    ctx.font = '700 11px JetBrains Mono, monospace';
    ctx.fillText(sub, x, y + 13);
    ctx.restore();
  }

  function drawOrb(x, y, r, p, extraLabel = '') {
    ctx.save();
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#111110';
    ctx.lineWidth = 1.6;
    ctx.stroke();

    ctx.fillStyle = '#ffffff';
    ctx.font = '800 12px JetBrains Mono, monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(p.pid, x, y);

    if (extraLabel) {
      ctx.fillStyle = '#111110';
      ctx.font = '700 11px JetBrains Mono, monospace';
      ctx.fillText(extraLabel, x, y + r + 13);
    }
    ctx.restore();
  }

  let memRefs = [];
  let memStepIdx = 0;
  let memFrames = [];
  let memFifoQueue = [];
  let memLastUsed = new Map();
  let memHistory = [];
  let memHits = 0;
  let memFaults = 0;
  let memPlaying = false;
  let memAcc = 0;

  function parseRefString() {
    const raw = document.getElementById('refStringInput').value;
    const nums = raw.split(/[\s,]+/).map(x => parseInt(x, 10)).filter(n => !isNaN(n) && n >= 0);
    return nums.length > 0 ? nums : [7, 0, 1, 2, 0, 3, 0, 4];
  }

  function addMemLog(tag, msg, cls = 'tag') {
    const box = document.getElementById('memLog');
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.innerHTML = `<span class="time">[ref#${memStepIdx}]</span> <span class="${cls}">[${tag}]</span> ${msg}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  function loadBeladyPreset() {
    document.getElementById('memAlgoSelect').value = 'FIFO';
    document.getElementById('refStringInput').value = '1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5';
    resetMemSim();
    addMemLog('BELADY', 'Loaded Belady sequence. Compare 3 Frames (9 faults) vs 4 Frames (10 faults) under FIFO!', 'ctx');
  }

  function randomizeRefString() {
    const arr = Array.from({ length: 14 }, () => Math.floor(Math.random() * 6));
    document.getElementById('refStringInput').value = arr.join(', ');
    resetMemSim();
  }

  function resetMemSim() {
    memPlaying = false;
    document.getElementById('memPlayBtn').textContent = '▶ Run';
    memRefs = parseRefString();
    const frameCap = parseInt(document.getElementById('frameCountSelect').value, 10) || 3;
    memStepIdx = 0;
    memFrames = Array(frameCap).fill(null);
    memFifoQueue = [];
    memLastUsed = new Map();
    memHistory = [];
    memHits = 0;
    memFaults = 0;
    memAcc = 0;
    document.getElementById('memLog').innerHTML = '';
    document.getElementById('memLastEvent').textContent = 'READY';
    document.getElementById('memLastEvent').style.color = 'var(--accent-amber)';
    addMemLog('MMU', `Initialized ${frameCap} physical RAM frames (${document.getElementById('memAlgoSelect').value}).`);
    renderMemUI();
  }

  function toggleMemPlay() {
    memPlaying = !memPlaying;
    document.getElementById('memPlayBtn').textContent = memPlaying ? '⏸ Pause' : '▶ Run';
  }

  function stepMemTick() {
    if (memStepIdx >= memRefs.length) {
      memPlaying = false;
      document.getElementById('memPlayBtn').textContent = '▶ Run';
      return;
    }

    const page = memRefs[memStepIdx];
    const algo = document.getElementById('memAlgoSelect').value;
    const hitIdx = memFrames.indexOf(page);

    if (hitIdx !== -1) {
      memHits++;
      memLastUsed.set(page, memStepIdx);
      memHistory.push({ page, status: 'HIT', frames: [...memFrames], highlightIdx: hitIdx });
      document.getElementById('memLastEvent').textContent = `HIT (Page ${page})`;
      document.getElementById('memLastEvent').style.color = 'var(--accent-emerald)';
      addMemLog('HIT', `Virtual Page <b>${page}</b> found in Frame F${hitIdx}.`, 'tag');
    } else {
      memFaults++;
      let targetIdx = memFrames.indexOf(null);
      let evicted = null;

      if (targetIdx === -1) {
        let victimPage = null;
        if (algo === 'FIFO') {
          victimPage = memFifoQueue.shift();
        } else if (algo === 'LRU') {
          let oldest = Infinity;
          for (const fPage of memFrames) {
            const usedAt = memLastUsed.has(fPage) ? memLastUsed.get(fPage) : -1;
            if (usedAt < oldest) { oldest = usedAt; victimPage = fPage; }
          }
        } else if (algo === 'OPT') {
          let farthest = -1;
          for (const fPage of memFrames) {
            const nextUse = memRefs.slice(memStepIdx + 1).indexOf(fPage);
            if (nextUse === -1) { victimPage = fPage; break; }
            if (nextUse > farthest) { farthest = nextUse; victimPage = fPage; }
          }
        }
        targetIdx = memFrames.indexOf(victimPage);
        evicted = victimPage;
      }

      memFrames[targetIdx] = page;
      memFifoQueue.push(page);
      memLastUsed.set(page, memStepIdx);

      memHistory.push({ page, status: 'FAULT', frames: [...memFrames], highlightIdx: targetIdx });
      document.getElementById('memLastEvent').textContent = `FAULT (Page ${page})`;
      document.getElementById('memLastEvent').style.color = 'var(--accent-rose)';
      if (evicted !== null) {
        addMemLog('FAULT', `Page <b>${page}</b> evicted <b>${evicted}</b> from Frame F${targetIdx}.`, 'irq');
      } else {
        addMemLog('FAULT', `Page <b>${page}</b> loaded into free Frame F${targetIdx}.`, 'irq');
      }
    }

    memStepIdx++;
    if (memStepIdx >= memRefs.length && memPlaying) {
      memPlaying = false;
      document.getElementById('memPlayBtn').textContent = '▶ Run';
      addMemLog('DONE', `Completed reference stream (${memFaults} faults, ${memHits} hits).`);
    }
    renderMemUI();
  }

  function updateMemHud() {
    const total = memHits + memFaults;
    const ratio = total > 0 ? ((memHits / total) * 100).toFixed(1) + '%' : '0.0%';
    document.getElementById('memFaults').textContent = String(memFaults);
    document.getElementById('memHits').textContent = String(memHits);
    document.getElementById('memHitRatio').textContent = ratio;
    document.getElementById('memProgressLabel').textContent = `Step ${memStepIdx} / ${memRefs.length}`;

    if (activeSubsystem === 'mem') {
      document.getElementById('clockVal').textContent = `${memStepIdx}/${memRefs.length}`;
      document.getElementById('runningVal').textContent = document.getElementById('memAlgoSelect').value;
      document.getElementById('loadVal').textContent = ratio;
    }
  }

  function renderMemUI() {
    updateMemHud();
    const strip = document.getElementById('refStrip');
    strip.innerHTML = '';
    memRefs.forEach((p, idx) => {
      const chip = document.createElement('div');
      chip.className = 'ref-chip';
      if (idx === memStepIdx) chip.classList.add('current');
      if (idx < memHistory.length) chip.classList.add(memHistory[idx].status === 'HIT' ? 'hit' : 'fault');
      chip.textContent = p;
      strip.appendChild(chip);
    });

    const wrap = document.getElementById('memMatrixWrap');
    wrap.innerHTML = '';
    const frameCap = parseInt(document.getElementById('frameCountSelect').value, 10) || 3;
    const labelsCol = document.createElement('div');
    labelsCol.className = 'frame-labels';
    for (let f = 0; f < frameCap; f++) {
      const lbl = document.createElement('div');
      lbl.className = 'frame-label-cell';
      lbl.textContent = `FRAME ${f}`;
      labelsCol.appendChild(lbl);
    }
    wrap.appendChild(labelsCol);

    memHistory.forEach(entry => {
      const col = document.createElement('div');
      col.className = `mem-col ${entry.status === 'HIT' ? 'hit-col' : 'fault-col'}`;
      const hdr = document.createElement('div');
      hdr.className = 'mem-req-hdr';
      hdr.textContent = entry.page;
      col.appendChild(hdr);

      entry.frames.forEach((val, fIdx) => {
        const slot = document.createElement('div');
        slot.className = 'ram-slot';
        if (fIdx === entry.highlightIdx) slot.classList.add(entry.status === 'HIT' ? 'hit-slot' : 'new-load');
        slot.textContent = val === null ? '·' : val;
        col.appendChild(slot);
      });

      const pill = document.createElement('div');
      pill.className = `status-pill ${entry.status === 'HIT' ? 'pill-hit' : 'pill-fault'}`;
      pill.textContent = entry.status;
      col.appendChild(pill);
      wrap.appendChild(col);
    });

    wrap.scrollLeft = wrap.scrollWidth;
  }

  let diskMaxCyl = 199;
  let diskInitHead = 53;
  let diskCurrHead = 53;
  let diskVisualHead = 53;
  let diskPlatterAngle = 0;
  let diskQueueRaw = [];
  let diskScheduleOrder = [];
  let diskServicedCount = 0;
  let diskTotalSeek = 0;
  let diskSeekSteps = [];
  let diskPlaying = false;
  let diskAcc = 0;

  function addDiskLog(tag, msg, cls = 'tag') {
    const box = document.getElementById('diskLog');
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.innerHTML = `<span class="time">[cyl=${diskCurrHead}]</span> <span class="${cls}">[${tag}]</span> ${msg}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  function computeDiskOrder(algo, dir, head, maxCyl, queue) {
    const rem = [...queue];
    if (algo === 'FCFS') return rem;

    if (algo === 'SSTF') {
      const order = [];
      let cur = head;
      while (rem.length > 0) {
        rem.sort((a, b) => Math.abs(a - cur) - Math.abs(b - cur) || a - b);
        const nxt = rem.shift();
        order.push(nxt);
        cur = nxt;
      }
      return order;
    }

    const asc = [...rem].sort((a, b) => a - b);
    const desc = [...rem].sort((a, b) => b - a);

    if (algo === 'LOOK') {
      if (dir === 'UP') {
        return [...asc.filter(x => x >= head), ...desc.filter(x => x < head)];
      } else {
        return [...desc.filter(x => x <= head), ...asc.filter(x => x > head)];
      }
    }

    if (algo === 'SCAN') {
      if (dir === 'UP') {
        return [...asc.filter(x => x >= head), maxCyl, ...desc.filter(x => x < head)];
      } else {
        return [...desc.filter(x => x <= head), 0, ...asc.filter(x => x > head)];
      }
    }

    if (algo === 'CSCAN') {
      if (dir === 'UP') {
        const up = asc.filter(x => x >= head);
        const wrapped = asc.filter(x => x < head);
        return wrapped.length > 0 ? [...up, maxCyl, 0, ...wrapped] : up;
      } else {
        const dn = desc.filter(x => x <= head);
        const wrapped = desc.filter(x => x > head);
        return wrapped.length > 0 ? [...dn, 0, maxCyl, ...wrapped] : dn;
      }
    }

    return rem;
  }

  function resetDiskSim() {
    diskPlaying = false;
    document.getElementById('diskPlayBtn').textContent = '▶ Run';
    diskMaxCyl = Math.max(20, parseInt(document.getElementById('diskMaxInput').value, 10) || 199);
    diskInitHead = Math.min(diskMaxCyl, Math.max(0, parseInt(document.getElementById('diskHeadInput').value, 10) || 0));

    const raw = document.getElementById('diskQueueInput').value;
    const parsed = raw.split(/[\s,]+/)
      .map(x => parseInt(x, 10))
      .filter(n => !isNaN(n) && n >= 0 && n <= diskMaxCyl);
    diskQueueRaw = parsed.length > 0 ? parsed : [98, 183, 37, 122, 14, 124, 65, 67];

    const algo = document.getElementById('diskAlgoSelect').value;
    const dir = document.getElementById('diskDirSelect').value;

    diskCurrHead = diskInitHead;
    diskVisualHead = diskInitHead;
    diskServicedCount = 0;
    diskTotalSeek = 0;
    diskSeekSteps = [{ cyl: diskInitHead, delta: 0, isRequest: false }];
    diskScheduleOrder = computeDiskOrder(algo, dir, diskInitHead, diskMaxCyl, diskQueueRaw);
    diskAcc = 0;

    document.getElementById('diskLog').innerHTML = '';
    addDiskLog('HDD', `Head parked at cyl <b>${diskInitHead}</b> (${algo} ${dir}). ${diskQueueRaw.length} I/O requests queued.`);
    renderDiskUI();
  }

  function randomizeDiskQueue() {
    const maxC = Math.max(20, parseInt(document.getElementById('diskMaxInput').value, 10) || 199);
    const arr = Array.from({ length: 8 }, () => Math.floor(Math.random() * (maxC + 1)));
    document.getElementById('diskQueueInput').value = arr.join(', ');
    resetDiskSim();
  }

  function injectDiskSeek() {
    const extraCyl = Math.floor(Math.random() * (diskMaxCyl + 1));
    diskQueueRaw.push(extraCyl);
    document.getElementById('diskQueueInput').value = diskQueueRaw.join(', ');
    const algo = document.getElementById('diskAlgoSelect').value;
    const dir = document.getElementById('diskDirSelect').value;
    const remainingTargets = diskScheduleOrder.slice(diskServicedCount);
    remainingTargets.push(extraCyl);
    diskScheduleOrder = [
      ...diskScheduleOrder.slice(0, diskServicedCount),
      ...computeDiskOrder(algo, dir, diskCurrHead, diskMaxCyl, remainingTargets)
    ];
    addDiskLog('BURST', `Injected urgent I/O request at cylinder <b>${extraCyl}</b>.`, 'irq');
    renderDiskUI();
  }

  function toggleDiskPlay() {
    diskPlaying = !diskPlaying;
    document.getElementById('diskPlayBtn').textContent = diskPlaying ? '⏸ Pause' : '▶ Run';
  }

  function stepDiskTick() {
    if (diskServicedCount >= diskScheduleOrder.length) {
      diskPlaying = false;
      document.getElementById('diskPlayBtn').textContent = '▶ Run';
      return;
    }

    const target = diskScheduleOrder[diskServicedCount];
    const delta = Math.abs(target - diskCurrHead);
    diskTotalSeek += delta;
    diskCurrHead = target;
    diskServicedCount++;

    const isReq = diskQueueRaw.includes(target);
    diskSeekSteps.push({ cyl: target, delta, isRequest: isReq });
    addDiskLog('SEEK', `Moved head to cyl <b>${target}</b> (+${delta} cyl)${isReq ? ' [SERVICED]' : ' [TURNAROUND]'}.`, isReq ? 'tag' : 'ctx');

    if (diskServicedCount >= diskScheduleOrder.length && diskPlaying) {
      diskPlaying = false;
      document.getElementById('diskPlayBtn').textContent = '▶ Run';
      addDiskLog('DONE', `Disk I/O sweep complete. Total seek: <b>${diskTotalSeek}</b> cylinders.`);
    }

    renderDiskUI();
  }

  function updateDiskHud() {
    const avg = diskServicedCount > 0 ? (diskTotalSeek / diskServicedCount).toFixed(1) : '0.0';
    document.getElementById('diskTotalSeek').textContent = `${diskTotalSeek} cyl`;
    document.getElementById('diskAvgSeek').textContent = avg;
    document.getElementById('diskCurrHead').textContent = String(diskCurrHead);
    document.getElementById('diskServiced').textContent = `${diskServicedCount} / ${diskScheduleOrder.length}`;

    if (activeSubsystem === 'disk') {
      document.getElementById('clockVal').textContent = `CYL ${diskCurrHead}`;
      document.getElementById('runningVal').textContent = document.getElementById('diskAlgoSelect').value;
      document.getElementById('loadVal').textContent = `${diskTotalSeek} cyl`;
    }
  }

  function renderDiskUI() {
    updateDiskHud();
    const chips = document.getElementById('diskOrderChips');
    chips.innerHTML = '';
    diskScheduleOrder.forEach((cyl, idx) => {
      const c = document.createElement('div');
      c.className = 'seq-chip';
      if (idx < diskServicedCount) c.classList.add('done');
      else if (idx === diskServicedCount) c.classList.add('next');
      c.textContent = `#${idx + 1}: ${cyl}`;
      chips.appendChild(c);
    });
    document.getElementById('diskOrderMeta').textContent = `${diskServicedCount}/${diskScheduleOrder.length} moves executed`;
  }

  function renderDiskCanvas(dt) {
    syncCanvasSize(diskCanvas);
    diskPlatterAngle += dt * 2.2;
    diskVisualHead += (diskCurrHead - diskVisualHead) * Math.min(1, dt * 8);

    const w = diskCanvas.width;
    const h = diskCanvas.height;
    if (w <= 0 || h <= 0) return;

    diskCtx.clearRect(0, 0, w, h);

    const platterCx = w * 0.24;
    const platterCy = h * 0.5;
    const maxRadius = Math.max(48, Math.min(w * 0.17, h * 0.34, 125));
    const minRadius = Math.max(18, maxRadius * 0.24);

    diskCtx.save();
    diskCtx.fillStyle = '#faf8f5';
    diskCtx.strokeStyle = '#2d4a3e';
    diskCtx.lineWidth = 2.6;
    diskCtx.beginPath();
    diskCtx.arc(platterCx, platterCy, maxRadius + 8, 0, Math.PI * 2);
    diskCtx.fill();
    diskCtx.stroke();

    for (let r = 1; r <= 5; r++) {
      const rad = minRadius + ((maxRadius - minRadius) * (r / 5));
      diskCtx.strokeStyle = 'rgba(17, 17, 16, 0.22)';
      diskCtx.lineWidth = 1.2;
      diskCtx.beginPath();
      diskCtx.arc(platterCx, platterCy, rad, 0, Math.PI * 2);
      diskCtx.stroke();
    }

    diskCtx.save();
    diskCtx.translate(platterCx, platterCy);
    diskCtx.rotate(diskPlatterAngle);
    diskCtx.strokeStyle = 'rgba(176, 74, 46, 0.35)';
    diskCtx.lineWidth = 1.3;
    for (let i = 0; i < 8; i++) {
      const ang = (i * Math.PI) / 4;
      diskCtx.beginPath();
      diskCtx.moveTo(Math.cos(ang) * minRadius, Math.sin(ang) * minRadius);
      diskCtx.lineTo(Math.cos(ang) * maxRadius, Math.sin(ang) * maxRadius);
      diskCtx.stroke();
    }
    diskCtx.restore();

    const cylToRadius = (cyl) => {
      const ratio = Math.min(1, Math.max(0, cyl / Math.max(1, diskMaxCyl)));
      return minRadius + ratio * (maxRadius - minRadius);
    };

    diskQueueRaw.forEach(cyl => {
      const rad = cylToRadius(cyl);
      const isDone = diskSeekSteps.some(s => s.cyl === cyl);
      diskCtx.fillStyle = isDone ? '#143d2b' : '#9e630c';
      diskCtx.beginPath();
      diskCtx.arc(platterCx, platterCy - rad, 5, 0, Math.PI * 2);
      diskCtx.fill();
    });

    diskCtx.fillStyle = '#2b2926';
    diskCtx.beginPath();
    diskCtx.arc(platterCx, platterCy, 11, 0, Math.PI * 2);
    diskCtx.fill();

    const pivotX = platterCx + maxRadius * 0.85;
    const pivotY = platterCy - maxRadius * 0.85;
    const headRad = cylToRadius(diskVisualHead);
    const tipX = platterCx;
    const tipY = platterCy - headRad;

    diskCtx.strokeStyle = '#2d4a3e';
    diskCtx.lineWidth = 4.5;
    diskCtx.beginPath();
    diskCtx.moveTo(pivotX, pivotY);
    diskCtx.lineTo(tipX, tipY);
    diskCtx.stroke();

    diskCtx.fillStyle = '#b04a2e';
    diskCtx.beginPath();
    diskCtx.arc(tipX, tipY, 6.5, 0, Math.PI * 2);
    diskCtx.fill();

    diskCtx.fillStyle = '#111110';
    diskCtx.font = '800 12px JetBrains Mono, monospace';
    diskCtx.textAlign = 'center';
    diskCtx.fillText(`PLATTER // HEAD CYL ${Math.round(diskVisualHead)}`, platterCx, platterCy + maxRadius + 24);

    // Right Half: Seek Trajectory Graph
    const gx = w * 0.48;
    const gy = Math.max(14, h * 0.12);
    const gw = Math.max(180, w * 0.48);
    const gh = Math.max(140, h * 0.76);

    diskCtx.fillStyle = '#faf8f5';
    diskCtx.strokeStyle = 'rgba(17, 17, 16, 0.22)';
    diskCtx.lineWidth = 1.5;
    diskCtx.beginPath();
    diskCtx.rect(gx, gy, gw, gh);
    diskCtx.fill();
    diskCtx.stroke();

    diskCtx.fillStyle = '#111110';
    diskCtx.font = '800 12px JetBrains Mono, monospace';
    diskCtx.textAlign = 'left';
    diskCtx.fillText('SEEK TRAJECTORY (CYLINDER VS STEP)', gx + 14, gy + 21);

    const plotLeft = gx + 46;
    const plotRight = gx + gw - 20;
    const plotTop = gy + 38;
    const plotBottom = gy + gh - 26;

    diskCtx.fillStyle = '#2b2926';
    diskCtx.font = '700 11px JetBrains Mono, monospace';
    diskCtx.textAlign = 'right';
    diskCtx.fillText(String(diskMaxCyl), plotLeft - 6, plotTop + 6);
    diskCtx.fillText('0', plotLeft - 6, plotBottom);

    const totalPoints = Math.max(1, diskScheduleOrder.length);
    const getPt = (idx, cyl) => {
      const px = plotLeft + (idx / totalPoints) * (plotRight - plotLeft);
      const py = plotBottom - (cyl / Math.max(1, diskMaxCyl)) * (plotBottom - plotTop);
      return { x: px, y: py };
    };

    if (diskSeekSteps.length > 0) {
      diskCtx.strokeStyle = '#2d4a3e';
      diskCtx.lineWidth = 3;
      diskCtx.beginPath();
      diskSeekSteps.forEach((pt, idx) => {
        const pos = getPt(idx, pt.cyl);
        if (idx === 0) diskCtx.moveTo(pos.x, pos.y);
        else diskCtx.lineTo(pos.x, pos.y);
      });
      diskCtx.stroke();

      diskSeekSteps.forEach((pt, idx) => {
        const pos = getPt(idx, pt.cyl);
        diskCtx.fillStyle = idx === 0 ? '#b04a2e' : (pt.isRequest ? '#143d2b' : '#9e630c');
        diskCtx.beginPath();
        diskCtx.arc(pos.x, pos.y, 5, 0, Math.PI * 2);
        diskCtx.fill();

        diskCtx.fillStyle = '#111110';
        diskCtx.font = '800 11px JetBrains Mono, monospace';
        diskCtx.textAlign = 'center';
        diskCtx.fillText(String(pt.cyl), pos.x, pos.y - 9);
      });
    }

    diskCtx.restore();
  }

  function renderCanvas(now) {
    const dt = Math.min(0.1, (now - lastFrameTime) / 1000);
    lastFrameTime = now;

    if (isPlaying && activeSubsystem === 'cpu') {
      tickAccumulator += dt * speedMult * 1.4;
      while (tickAccumulator >= 1) {
        stepTick();
        tickAccumulator -= 1;
      }
    }

    if (memPlaying && activeSubsystem === 'mem') {
      memAcc += dt * 1.6;
      while (memAcc >= 1) {
        stepMemTick();
        memAcc -= 1;
      }
    }

    if (diskPlaying && activeSubsystem === 'disk') {
      diskAcc += dt * 1.4;
      while (diskAcc >= 1) {
        stepDiskTick();
        diskAcc -= 1;
      }
    }

    if (activeSubsystem === 'cpu') {
      syncCanvasSize(canvas);
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const w = canvas.width;
      const h = canvas.height;
      if (w > 0 && h > 0) {
        const pending = primaryEngine.procs.filter(p => !p.arrived);

        const col1 = w * 0.14;
        const col2 = w * 0.40;
        const col3 = w * 0.67;
        const col4 = w * 0.89;
        const midY = h * 0.42;

        ctx.save();
        ctx.strokeStyle = 'rgba(17, 17, 16, 0.28)';
        ctx.lineWidth = 3.5;
        ctx.beginPath();
        ctx.moveTo(col1, midY);
        ctx.lineTo(col4, midY);
        ctx.stroke();
        ctx.restore();

        drawBox(col1, midY, 114, 64, 'JOB POOL', `${pending.length} waiting`, '#4a463f');
        drawBox(col2, midY, 144, 64, 'READY QUEUE', `${primaryEngine.readyQueue.length} queued`, '#2d4a3e');

        const coreColor = ctxFlash > 0.05 ? '#9e2a2b' : (primaryEngine.runningProc ? '#143d2b' : '#b04a2e');
        drawBox(col3, midY, 162, 80, 'CPU CORE 0', primaryEngine.runningProc ? `EXEC ${primaryEngine.runningProc.pid} (rem ${primaryEngine.runningProc.rem})` : 'IDLE CYCLE', coreColor);
        if (ctxFlash > 0) ctxFlash *= 0.9;

        drawBox(col4, midY, 118, 64, 'TERMINATED', `${primaryEngine.completedProcs.length}/${primaryEngine.procs.length} done`, '#143d2b');

        primaryEngine.readyQueue.forEach((p, i) => {
          const ox = col2 - ((primaryEngine.readyQueue.length - 1) * 22) + i * 44;
          const oy = midY + 66;
          drawOrb(ox, oy, 15, p, `rem:${p.rem}`);
        });

        if (primaryEngine.runningProc) {
          drawOrb(col3, midY + 64, 18, primaryEngine.runningProc, `prio:${primaryEngine.runningProc.prio}`);
        }

        primaryEngine.completedProcs.forEach((p, i) => {
          const ox = col4 - ((primaryEngine.completedProcs.length - 1) * 18) + i * 36;
          const oy = midY + 66;
          drawOrb(ox, oy, 13, p, '');
        });

        for (let i = sparks.length - 1; i >= 0; i--) {
          const s = sparks[i];
          s.x += s.vx;
          s.y += s.vy;
          s.life -= 0.03;
          ctx.fillStyle = `rgba(158, 42, 43, ${s.life})`;
          ctx.beginPath();
          ctx.arc(s.x, s.y, 3.5, 0, Math.PI * 2);
          ctx.fill();
          if (s.life <= 0) sparks.splice(i, 1);
        }
      }
    } else if (activeSubsystem === 'disk') {
      renderDiskCanvas(dt);
    }

    requestAnimationFrame(renderCanvas);
  }

  resetSim();
  resetMemSim();
  resetDiskSim();
  requestAnimationFrame(renderCanvas);
</script>
</body>
</html>
"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(HTML_CONTENT.encode("utf-8"))
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"KernelPulse running at http://localhost:{PORT}")
        threading.Timer(0.8, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
        httpd.serve_forever()