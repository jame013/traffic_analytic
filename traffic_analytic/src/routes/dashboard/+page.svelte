<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onDestroy } from 'svelte';

  const qp = () => $page.url.searchParams;

  // read settings from Input page
  $: camera = qp().get('camera') ?? 'Cam 01 - Main Road';
  $: mode = qp().get('mode') ?? 'realtime';
  $: refresh = qp().get('refresh') ?? '5s';

  $: densityTh = Number(qp().get('density') ?? 30);
  $: speedTh = Number(qp().get('speed') ?? 5);
  $: durationTh = Number(qp().get('duration') ?? 5);

  // mock realtime data
  let lastUpdated = new Date();
  let flowRate = 45;         // vehicles/min
  let totalToday = 1250;     // vehicles
  let density = 28;          // vehicles in zone
  let avgSpeed = 8;          // km/h

  let totalLine: number[] = [20, 22, 25, 28, 31, 27, 26, 29, 33, 30, 28, 32];
  let carLine: number[]   = [12, 13, 15, 17, 19, 16, 15, 17, 20, 18, 17, 19];
  let motoLine: number[]  = [8,  9,  10, 11, 12, 11, 11, 12, 13, 12, 11, 13];

  // analytics mock
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

  // auto refresh
  function intervalMs(s: string) {
    if (s === '10s') return 10000;
    if (s === 'manual') return 0;
    return 5000;
  }

  let timer: any = null;
  function tick() {
    // simulate small changes
    const rand = (a: number, b: number) => Math.round(a + Math.random() * (b - a));
    flowRate = rand(35, 60);
    density = rand(15, 45);
    avgSpeed = rand(2, 15);
    totalToday += rand(0, 3);

    // shift lines
    const nextTotal = Math.max(0, rand(18, 40));
    const nextCar = Math.max(0, Math.round(nextTotal * 0.6));
    const nextMoto = Math.max(0, nextTotal - nextCar);

    totalLine = [...totalLine.slice(1), nextTotal];
    carLine = [...carLine.slice(1), nextCar];
    motoLine = [...motoLine.slice(1), nextMoto];

    lastUpdated = new Date();
  }

  $: {
    // rebind interval when refresh changes
    if (timer) clearInterval(timer);
    const ms = intervalMs(refresh);
    if (ms > 0 && mode === 'realtime') timer = setInterval(tick, ms);
  }

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
    // v max ~ 100
    return `${Math.min(100, Math.max(5, v))}%`;
  }
</script>

<div class="min-h-screen bg-zinc-950 text-zinc-100">
  <!-- Header -->
  <div class="border-b border-zinc-800">
    <div class="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between gap-4">
      <div>
        <a href="/" class="text-lg font-semibold">🚦 Smart Traffic AI</a>
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

    <!-- Alert banner -->
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
    <!-- KPI row -->
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

    <!-- Real-time monitor -->
    <div class="grid gap-4 lg:grid-cols-2">
      <!-- Live panel -->
      <div class="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
        <div class="flex items-center justify-between">
          <div class="font-semibold">Live AI View</div>
          <div class="text-xs text-zinc-400">Overlay: bbox + zone (placeholder)</div>
        </div>

        <div class="mt-4 aspect-video rounded-xl border border-zinc-800 bg-zinc-950 flex items-center justify-center">
          <div class="text-zinc-500 text-sm">
            Live Stream Placeholder (put video/frame here)
          </div>
        </div>

        <div class="mt-3 flex flex-wrap gap-2 text-xs">
          <span class="px-2 py-1 rounded-lg border border-zinc-800 text-zinc-300">FPS: 24 (mock)</span>
          <span class="px-2 py-1 rounded-lg border border-zinc-800 text-zinc-300">Latency: 1.2s (mock)</span>
          <span class="px-2 py-1 rounded-lg border border-zinc-800 text-zinc-300">Zones: A / B</span>
        </div>
      </div>

      <!-- Trend graph (simple bars as placeholder) -->
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

    <!-- Deep analytics -->
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

    <!-- Bottom actions -->
    <div class="flex flex-wrap gap-2 justify-end">
      <a href="/" class="rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm">
        ← Back to Input
      </a>
      <button class="rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm">
        Export (mock)
      </button>

      {#if refresh === 'manual' || mode !== 'realtime'}
        <button class="rounded-xl bg-zinc-100 text-zinc-950 px-4 py-2 text-sm font-semibold" on:click={tick}>
          Refresh Now
        </button>
      {/if}
    </div>
  </div>
</div>
