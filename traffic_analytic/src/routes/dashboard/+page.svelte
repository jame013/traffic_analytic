<script lang="ts">
  import { page } from '$app/state';
  import { onDestroy, onMount } from 'svelte';
  import Chart from 'chart.js/auto';
  import Header from '$lib/Header.svelte';

  const qp = () => page.url.searchParams;
  $: videoFile = qp().get('video') ?? '';
  $: camera = qp().get('camera') ?? 'Cam 01 - Main Road';
  $: mode = qp().get('mode') ?? 'realtime';

  let lastUpdated = new Date();
  let flowRate = 0;
  let totalToday = 0;
  let density = 0;
  let avgSpeed = 0;
  
  let vehicleCounts = { car: 0, motorcycle: 0, bus: 0, truck: 0 };

  // ตัวแปร Canvas สำหรับกราฟทั้ง 3 ตัว
  let trendCanvas: HTMLCanvasElement;
  let compCanvas: HTMLCanvasElement;
  let peakCanvas: HTMLCanvasElement; // 🌟 เพิ่ม Canvas สำหรับกราฟแท่ง
  
  let trendChart: Chart;
  let compChart: Chart;
  let peakChart: Chart; // 🌟 เพิ่มตัวแปร Chart สำหรับกราฟแท่ง

  let timer: any = null;
  let peakTimer: any = null;

  // 🌟 ฟังก์ชันตั้งค่ากราฟเริ่มต้น
  function initCharts() {
    Chart.defaults.color = '#a1a1aa';
    Chart.defaults.borderColor = '#27272a';
    Chart.defaults.font.family = "'Inter', sans-serif";

    // 1. กราฟเส้นแบบ 5 สี (Real-time Trend ครบทุกประเภทรถ)
    trendChart = new Chart(trendCanvas, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Total (Density)',
            data: [],
            borderColor: '#8b5cf6', // สีม่วง (ยอดรวม)
            backgroundColor: 'rgba(139, 92, 246, 0.05)',
            borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0
          },
          {
            label: 'Car',
            data: [],
            borderColor: '#3b82f6', // สีน้ำเงิน
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0
          },
          {
            label: 'Motorcycle',
            data: [],
            borderColor: '#10b981', // สีเขียว
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0
          },
          {
            label: 'Bus',
            data: [],
            borderColor: '#f59e0b', // สีเหลือง/ส้ม
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0
          },
          {
            label: 'Truck',
            data: [],
            borderColor: '#ef4444', // สีแดง
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false, animation: { duration: 0 },
        plugins: { 
          legend: { 
            position: 'top', align: 'end',
            labels: { usePointStyle: true, boxWidth: 8, font: { size: 10 } } 
          } 
        },
        scales: { 
          x: { ticks: { maxTicksLimit: 8, font: { size: 10 } } },
          y: { beginAtZero: true, suggestedMax: 15 } 
        }
      }
    });

    // 2. กราฟโดนัท (Composition)
    compChart = new Chart(compCanvas, {
      type: 'doughnut',
      data: {
        labels: ['Car', 'Motorcycle', 'Bus', 'Truck'],
        datasets: [{
          data: [0, 0, 0, 0],
          backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
          borderWidth: 0, hoverOffset: 4
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { 
          legend: { position: 'right', labels: { usePointStyle: true, boxWidth: 8 } } 
        },
        cutout: '70%' // ทำให้รูตรงกลางกว้างขึ้นเหมือนในรูป
      }
    });

    // 3. 🌟 กราฟแท่ง (Peak Hour Analysis)
    peakChart = new Chart(peakCanvas, {
      type: 'bar',
      data: {
        labels: [], // จะใส่เวลา 08:00, 09:00...
        datasets: [{
          label: 'Vehicle Volume',
          data: [],
          backgroundColor: '#f59e0b', // สีส้มทองตามรูป
          borderRadius: 4,
          barPercentage: 0.6
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } }, // ซ่อนป้ายชื่อ
        scales: { 
          x: { grid: { display: false }, ticks: { font: { size: 10 } } },
          y: { beginAtZero: true, ticks: { maxTicksLimit: 6, font: { size: 10 } } } 
        }
      }
    });
  }

  // 🌟 ฟังก์ชันดึงข้อมูล Real-time (ทุก 1 วินาที)
  async function fetchStats() {
    if (!videoFile) return;
    try {
      const resStats = await fetch("http://localhost:8000/stats");
      const dataStats = await resStats.json();
      
      density = dataStats.density;
      flowRate = dataStats.flowRate || 0;
      totalToday = dataStats.totalToday;
      avgSpeed = dataStats.avgSpeed || 0;
      
      vehicleCounts = {
        car: dataStats.car || 0,
        motorcycle: dataStats.motorcycle || 0,
        bus: dataStats.bus || 0,
        truck: dataStats.truck || 0
      };

      const resHist = await fetch("http://localhost:8000/api/history");
      const dataHist = await resHist.json();
      
      if (trendChart && dataHist.history.length > 0) {
        trendChart.data.labels = dataHist.history.map((h: any) => h.time);
        trendChart.data.datasets[0].data = dataHist.history.map((h: any) => h.density);
        trendChart.data.datasets[1].data = dataHist.history.map((h: any) => h.car);
        trendChart.data.datasets[2].data = dataHist.history.map((h: any) => h.motorcycle);
        trendChart.data.datasets[3].data = dataHist.history.map((h: any) => h.bus);    // 🌟 เพิ่ม Bus
        trendChart.data.datasets[4].data = dataHist.history.map((h: any) => h.truck);  // 🌟 เพิ่ม Truck
        trendChart.update();
      }

      if (compChart) {
        compChart.data.datasets[0].data = [
          vehicleCounts.car, vehicleCounts.motorcycle, vehicleCounts.bus, vehicleCounts.truck
        ];
        compChart.update();
      }

      lastUpdated = new Date();
    } catch (err) { console.error(err); }
  }

  // 🌟 ฟังก์ชันดึงข้อมูลกราฟแท่ง (ดึงทุกๆ 10 วินาที ก็พอครับ ไม่ต้องดึงถี่)
  async function fetchPeakData() {
    try {
      const res = await fetch("http://localhost:8000/api/summary");
      const data = await res.json();
      if (peakChart && data.hourly) {
        peakChart.data.labels = data.hourly.map((d: any) => d.hour);
        peakChart.data.datasets[0].data = data.hourly.map((d: any) => d.peak_volume);
        peakChart.update();
      }
    } catch(err) { console.error(err); }
  }

  onMount(() => {
    initCharts();
    timer = setInterval(fetchStats, 1000);
    fetchPeakData(); // ดึงครั้งแรกตอนโหลดหน้าเว็บ
    peakTimer = setInterval(fetchPeakData, 10000); // อัปเดตกราฟแท่งทุก 10 วิ
  });

  onDestroy(() => {
    if (timer) clearInterval(timer);
    if (peakTimer) clearInterval(peakTimer);
    if (trendChart) trendChart.destroy();
    if (compChart) compChart.destroy();
    if (peakChart) peakChart.destroy();
  });

  $: isJam = density >= 20;
</script>

<div class="min-h-screen bg-snow-50 dark:bg-zinc-950 text-zinc-950 dark:text-zinc-100">
  <Header title="Dashboard" camera={camera} />

  <div class="mx-auto max-w-6xl px-4 py-6 grid gap-4">
    <div class="grid gap-4 md:grid-cols-3">
      <div class="rounded-2xl border border-zinc-800 bg-white dark:bg-zinc-900/40 p-5 flex items-center gap-4">
        <div class="w-12 h-12 rounded-full flex items-center justify-center {isJam ? 'bg-red-500/20 text-red-500' : 'bg-blue-500/20 text-blue-500'} text-2xl">
          {isJam ? '⚠️' : '🚗'}
        </div>
        <div>
          <div class="text-sm text-zinc-950 dark:text-zinc-400">Traffic Density</div>
          <div class="text-2xl font-semibold {isJam ? 'text-red-400' : 'text-blue-400'}">
            {isJam ? 'HEAVY' : 'FLOW'} <span class="text-sm font-normal text-black dark:text-zinc-400">({density} veh)</span>
          </div>
        </div>
      </div>
      <div class="rounded-2xl border border-zinc-800 bg-white dark:bg-zinc-900/40 p-5 flex items-center gap-4">
        <div class="w-12 h-12 rounded-full bg-blue-500/20 text-blue-500 flex items-center justify-center text-2xl">⚡</div>
        <div>
          <div class="text-sm text-zinc-950 dark:text-zinc-400">Flow Rate Now</div>
          <div class="text-2xl font-semibold text-blue-400">{flowRate} <span class="text-sm font-normal text-black dark:text-zinc-400">/min</span></div>
        </div>
      </div>
      <div class="rounded-2xl border border-zinc-800 bg-white dark:bg-zinc-900/40 p-5 flex items-center gap-4">
        <div class="w-12 h-12 rounded-full bg-blue-500/20 text-zinc-300 flex items-center justify-center text-2xl">📊</div>
        <div>
          <div class="text-sm text-zinc-950 dark:text-zinc-400">Total Vehicles Today</div>
          <div class="text-2xl font-semibold text-blue-400">{totalToday.toLocaleString()}</div>
        </div>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <div class="rounded-2xl border border-zinc-800 bg-white dark:bg-zinc-900/40 p-5 flex flex-col">
        <div class="font-semibold mb-3">Live AI View</div>
        <div class="flex-1 aspect-video rounded-xl border border-zinc-800 bg-snow-50 dark:bg-zinc-950 flex items-center justify-center overflow-hidden">
          {#if videoFile}
            <img src="http://localhost:8000/stream/{videoFile}" alt="Live AI" class="w-full h-full object-cover" />
          {:else}
            <div class="text-zinc-500 text-sm">No video source</div>
          {/if}
        </div>
      </div>

      <div class="rounded-2xl border border-zinc-800 bg-white dark:bg-zinc-900/40 p-5 flex flex-col">
        <div class="font-semibold mb-2">Real-time Traffic Trend</div>
        <div class="flex-1 w-full relative min-h-55">
          <canvas bind:this={trendCanvas}></canvas>
        </div>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <div class="rounded-2xl border border-zinc-800 bg-white dark:bg-zinc-900/40 p-5 flex flex-col">
        <div class="font-semibold mb-2">Vehicle Composition</div>
        <div class="flex-1 w-full relative min-h-55 flex justify-center items-center">
          <canvas bind:this={compCanvas}></canvas>
        </div>
      </div>

      <div class="rounded-2xl border border-zinc-800 bg-white dark:bg-zinc-900/40 p-5 flex flex-col">
        <div class="font-semibold mb-2">Peak Hour Analysis</div>
        <div class="flex-1 w-full relative min-h-55">
          <canvas bind:this={peakCanvas}></canvas>
        </div>
      </div>
    </div>
  </div>
</div>