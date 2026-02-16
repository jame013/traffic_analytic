<script lang="ts">
  import { page } from '$app/stores';
  import { onDestroy, onMount } from 'svelte'; // 1. เพิ่ม onMount

  const qp = () => $page.url.searchParams;
  $: videoFile = qp().get('video') ?? ''; // รับชื่อไฟล์วิดีโอมาจากหน้า upload
  
  // read settings from Input page
  $: camera = qp().get('camera') ?? 'Cam 01 - Main Road';
  $: mode = qp().get('mode') ?? 'realtime';
  $: refresh = qp().get('refresh') ?? '5s';

  $: densityTh = Number(qp().get('density') ?? 30);
  $: speedTh = Number(qp().get('speed') ?? 5);
  $: durationTh = Number(qp().get('duration') ?? 5);

  // 2. เปลี่ยนตัวเลขจำลองตั้งต้นเป็น 0
  let lastUpdated = new Date();
  let flowRate = 0;          // vehicles/min
  let totalToday = 0;      // vehicles
  let density = 0;           // vehicles in zone
  let avgSpeed = 0;          // km/h

  let totalLine: number[] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
  let carLine: number[]   = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
  let motoLine: number[]  = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

  // analytics mock (คงไว้ก่อนเพราะส่วนนี้เรายังไม่ได้เขียนหลังบ้านส่งมา)
  let comp = [
    { name: 'Car', pct: 60 },
    { name: 'Motorcycle', pct: 30 },
    { name: 'Bus', pct: 5 },
    { name: 'Truck', pct: 5 }
  ];

  let peak = [
    { h: '06:00', v: 35 }, { h: '07:00', v: 55 }, { h: '08:00', v: 85 },
    { h: '09:00', v: 60 }, { h: '12:00', v: 45 }, { h: '17:00', v: 90 },
    { h: '18:00', v: 70 }, { h: '20:00', v: 40 }
  ];

  // alert logic
  $: isJam = density > densityTh && avgSpeed < speedTh;

  // model quality (simple mock)
  $: modelQuality = avgSpeed < 3 ? 'LOW' : (avgSpeed < 8 ? 'MED' : 'HIGH');

  let timer: any = null;

  // 3. ฟังก์ชันดึงข้อมูลจาก Python API
  async function fetchStats() {
    if (!videoFile) return;
    try {
      const res = await fetch("http://localhost:8000/stats");
      const data = await res.json();

      density = data.density;
      flowRate = data.flowRate || 0;
      totalToday = data.totalToday;
      avgSpeed = data.avgSpeed || Math.floor(Math.random() * 10) + 5; // mock speed ไปก่อนถ้า AI ยังไม่ได้คำนวณ

      // อัปเดตเส้นกราฟ
      totalLine = [...totalLine.slice(1), density];
      carLine = [...carLine.slice(1), Math.round(density * 0.6)];
      motoLine = [...motoLine.slice(1), density - Math.round(density * 0.6)];

      lastUpdated = new Date();
    } catch (err) {
      console.error("Cannot fetch stats API:", err);
    }
  }

  // 4. เริ่มดึงข้อมูลอัตโนมัติ ทุกๆ 1 วินาที
  onMount(() => {
    timer = setInterval(fetchStats, 1000);
  });

  onDestroy(() => {
    if (timer) clearInterval(timer);
  });

  function densityLabel(d: number) {
    if (d >= 35) return 'Heavy';
    if (d >= 25) return 'Slow';
    return 'Flow';
  }

  function badgeClass(q: string) {
    if (q === 'HIGH') return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
    if (q === 'MED')  return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
    return 'bg-red-500/15 text-red-300 border-red-500/30';
  }

  function barHeight(v: number) {
    return `${Math.min(100, Math.max(5, v))}%`;
  }
</script>

<div class="min-h-screen bg-zinc-950 text-zinc-100">
  <div class="border-b border-zinc-800">
    <div class="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between gap-4">
      <div>
        <div class="text-lg font-semibold">🚦 Smart Traffic AI</div>
        <div class="text-sm text-zinc-400">{camera} • Dashboard</div>
      </div>

      <div class="flex items-center gap-3 text-sm">
        <div class="text-zinc-400">🟢 Online</div>
        <div class="text-zinc-400">
          Last Updated: {lastUpdated.toLocaleTimeString()}
        </div>

        <span class={`px-2 py-1 rounded-lg border ${badgeClass(modelQuality)}`}>
          Model: {modelQuality}
        </span>

        {#if mode === 'realtime' && refresh !== 'manual'}
          <div class="text-zinc-400">Refresh: {refresh}</div>
        {/if}
      </div>
    </div>

    {#if isJam}
      <div class="mx-auto max-w-6xl px-4 pb-4">
        <div class="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 flex items-center justify-between">
          <div class="font-semibold text-red-200">
            🚨 ALERT: Traffic Jam Detected (Density &gt; {densityTh}, Speed &lt; {speedTh})
          </div>
          <div class="flex gap-2">
            <button class="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm">View Zone</button>
            <button class="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm">Acknowledge</button>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <div class="mx-auto max-w-6xl px-4 py-6 grid gap-4">
    <div class="grid gap-4 md:grid-cols-3">
      <div class="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
        <div class="text-sm text-zinc-400">Traffic Density</div>
        <div class="mt-2 text-3xl font-semibold">{densityLabel(density)}</div>
        <div class="mt-2 text-sm text-zinc-400">Current: {density} vehicles • Avg speed {avgSpeed} km/h</div>
      </div>

      <div class="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
        <div class="text-sm text-zinc-400">Flow Rate (Now)</div>
        <div class="mt-2 text-3xl font-semibold">{flowRate} <span class="text-base text-zinc-400">veh/min</span></div>
        <div class="mt-2 text-sm text-zinc-400">Δ +5% vs last hour (mock)</div>
      </div>

      <div class="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
        <div class="text-sm text-zinc-400">Total Vehicles (Today)</div>
        <div class="mt-2 text-3xl font-semibold">{totalToday.toLocaleString()}</div>
        <div class="mt-2 text-sm text-zinc-400">Since 00:00</div>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <div class="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
        <div class="flex items-center justify-between">
          <div class="font-semibold">Live AI View</div>
          <div class="text-xs text-zinc-400">AI Tracking Active</div>
        </div>

        <div class="mt-4 aspect-video rounded-xl border border-zinc-800 bg-zinc-950 flex items-center justify-center overflow-hidden">
          {#if videoFile}
            <img src="http://localhost:8000/stream/{videoFile}" alt="Live AI Stream" class="w-full h-full object-cover" />
          {:else}
            <div class="text-zinc-500 text-sm">No video source provided</div>
          {/if}
        </div>

        <div class="mt-3 flex flex-wrap gap-2 text-xs">
          <span class="px-2 py-1 rounded-lg border border-zinc-800 text-zinc-300">FPS: 24 (mock)</span>
          <span class="px-2 py-1 rounded-lg border border-zinc-800 text-zinc-300">Latency: 1.2s (mock)</span>
          <span class="px-2 py-1 rounded-lg border border-zinc-800 text-zinc-300">Zones: A / B</span>
        </div>
      </div>

      <div class="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
        <div class="flex items-center justify-between">
          <div class="font-semibold">Real-time Trend (Count)</div>
          <div class="text-xs text-zinc-400">Total / Car / Motorcycle</div>
        </div>

        <div class="mt-4 h-48 rounded-xl border border-zinc-800 bg-zinc-950 p-3 flex items-end gap-1">
          {#each totalLine as v, i}
            <div class="flex-1 flex flex-col items-center gap-1">
              <div class="w-full rounded bg-zinc-700/60" style="height: {barHeight(v)}"></div>
              <div class="text-[10px] text-zinc-600">{i % 3 === 0 ? '|' : ''}</div>
            </div>
          {/each}
        </div>

        <div class="mt-3 text-xs text-zinc-400">
          (Placeholder graph) If you want real charts, we can swap this with ECharts later.
        </div>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <div class="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
        <div class="font-semibold">Vehicle Composition</div>
        <div class="mt-3 space-y-3">
          {#each comp as c}
            <div>
              <div class="flex items-center justify-between text-sm">
                <div class="text-zinc-300">{c.name}</div>
                <div class="text-zinc-400">{c.pct}%</div>
              </div>
              <div class="mt-1 h-2 rounded bg-zinc-800">
                <div class="h-2 rounded bg-zinc-200" style="width: {c.pct}%"></div>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <div class="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
        <div class="font-semibold">Peak Hour Analysis</div>

        <div class="mt-4 h-48 rounded-xl border border-zinc-800 bg-zinc-950 p-3 flex items-end gap-2">
          {#each peak as p}
            <div class="flex-1 flex flex-col items-center gap-2">
              <div
                class="w-full rounded bg-zinc-200"
                style="height: {barHeight(p.v)}"
                title={`${p.h} • ${p.v}`}
              ></div>
              <div class="text-[10px] text-zinc-500">{p.h}</div>
            </div>
          {/each}
        </div>

        <div class="mt-2 text-xs text-zinc-400">
          Highlight peaks (mock): 08:00 & 17:00
        </div>
      </div>
    </div>

    <div class="flex flex-wrap gap-2 justify-end">
      <a href="/" class="rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm">
        ← Back to Input
      </a>
      <button class="rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm">
        Export (mock)
      </button>

      {#if refresh === 'manual' || mode !== 'realtime'}
        <button class="rounded-xl bg-zinc-100 text-zinc-950 px-4 py-2 text-sm font-semibold" on:click={fetchStats}>
          Refresh Now
        </button>
      {/if}
    </div>
  </div>
</div>