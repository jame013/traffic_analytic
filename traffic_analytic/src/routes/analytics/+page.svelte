<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Chart from 'chart.js/auto';

  let selectedDate = '';
  let availableDates: string[] = [];
  let kpis = { max_total: 0, avg_speed: 0, max_density: 0 };
  
  let densityCanvas: HTMLCanvasElement;
  let speedCanvas: HTMLCanvasElement;
  let densityChart: Chart;
  let speedChart: Chart;

  async function fetchSummary(dateParam = '') {
    try {
      const url = dateParam ? `http://localhost:8000/api/summary?date=${dateParam}` : 'http://localhost:8000/api/summary';
      const res = await fetch(url);
      const data = await res.json();

      selectedDate = data.selected_date;
      availableDates = data.available_dates;
      kpis = data.kpis;

      updateCharts(data.hourly);
    } catch (err) {
      console.error("Error fetching summary:", err);
    }
  }

  function updateCharts(hourlyData: any[]) {
    const labels = hourlyData.map(d => d.hour);
    const densityData = hourlyData.map(d => d.avg_density);
    const speedData = hourlyData.map(d => d.avg_speed);

    Chart.defaults.color = '#a1a1aa';
    Chart.defaults.borderColor = '#27272a';

    // วาดกราฟแท่ง (ความหนาแน่นรายชั่วโมง)
    if (densityChart) densityChart.destroy();
    densityChart = new Chart(densityCanvas, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Avg Density (คัน/ช่วงเวลา)',
          data: densityData,
          backgroundColor: '#3b82f6',
          borderRadius: 4
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });

    // วาดกราฟเส้น (ความเร็วเฉลี่ยรายชั่วโมง)
    if (speedChart) speedChart.destroy();
    speedChart = new Chart(speedCanvas, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Avg Speed (km/h)',
          data: speedData,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.3
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  onMount(() => {
    fetchSummary();
  });

  onDestroy(() => {
    if (densityChart) densityChart.destroy();
    if (speedChart) speedChart.destroy();
  });
</script>

<div class="min-h-screen bg-zinc-950 text-zinc-100 p-6">
  <div class="max-w-6xl mx-auto">
    
    <div class="flex flex-col md:flex-row justify-between items-center mb-8 gap-4 border-b border-zinc-800 pb-4">
      <div>
        <h1 class="text-2xl font-bold">📊 Historical Data Analytics</h1>
        <p class="text-zinc-400 text-sm">สรุปสถิติการจราจรย้อนหลังแบบรายวัน</p>
      </div>
      
      <div class="flex items-center gap-4">
        <select 
          class="bg-zinc-900 border border-zinc-700 text-white text-sm rounded-lg p-2.5 outline-none focus:border-blue-500"
          bind:value={selectedDate}
          on:change={() => fetchSummary(selectedDate)}
        >
          {#each availableDates as d}
            <option value={d}>{d}</option>
          {/each}
        </select>
        <a href="/" class="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition-colors">
          🏠 กลับหน้าหลัก
        </a>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
        <div class="text-zinc-400 text-sm mb-1">รถวิ่งผ่านทั้งหมด (คัน)</div>
        <div class="text-4xl font-bold text-blue-400">{kpis.max_total}</div>
      </div>
      <div class="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
        <div class="text-zinc-400 text-sm mb-1">ความเร็วเฉลี่ยทั้งวัน (km/h)</div>
        <div class="text-4xl font-bold text-emerald-400">{kpis.avg_speed}</div>
      </div>
      <div class="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
        <div class="text-zinc-400 text-sm mb-1">ความหนาแน่นสูงสุด (คัน/เฟรม)</div>
        <div class="text-4xl font-bold text-red-400">{kpis.max_density}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6 h-[400px] flex flex-col">
        <h2 class="font-semibold mb-4">📈 ความหนาแน่นของรถ แบ่งตามชั่วโมง (Density)</h2>
        <div class="relative flex-1 w-full"><canvas bind:this={densityCanvas}></canvas></div>
      </div>
      
      <div class="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6 h-[400px] flex flex-col">
        <h2 class="font-semibold mb-4">🏎️ ความเร็วเฉลี่ย แบ่งตามชั่วโมง (Speed)</h2>
        <div class="relative flex-1 w-full"><canvas bind:this={speedCanvas}></canvas></div>
      </div>
    </div>

  </div>
</div>