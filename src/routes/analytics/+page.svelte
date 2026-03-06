<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Chart from 'chart.js/auto';
  import { DarkMode } from "flowbite-svelte";

  let selectedDate = '';
  let availableDates: string[] = [];
  let kpis = { max_total: 0, avg_speed: 0, max_density: 0 };
  
  // 🌟 1. ประกาศตัวแปร aiInsight
  let aiInsight = "กำลังให้ AI ประมวลผลข้อมูล...";
  
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
      
      // 🌟 2. เรียกฟังก์ชัน fetchInsight หลังจากดึงข้อมูล summary เสร็จ
      fetchInsight(selectedDate);
      
    } catch (err) {
      console.error("Error fetching summary:", err);
    }
  }

  // 🌟 3. เพิ่มฟังก์ชัน fetchInsight
  async function fetchInsight(targetDate: string) {
    aiInsight = "กำลังให้ AI ประมวลผลข้อมูล...";
    try {
      const res = await fetch(`http://localhost:8000/api/ai-insight?date=${targetDate}`);
      const data = await res.json();
      aiInsight = data.insight;
    } catch (err) {
      aiInsight = "ไม่สามารถเชื่อมต่อกับ AI Engine ได้ในขณะนี้";
      console.error("Error fetching AI insight:", err);
    }
  }

  function updateCharts(hourlyData: any[]) {
    // 🌟 4. เพิ่มการเช็คข้อมูลว่างเหมือนที่เคยทำ
    if (!hourlyData || hourlyData.length === 0) {
      console.warn("ไม่มีข้อมูลรายชั่วโมงสำหรับวาดกราฟ");
      return;
    }
    
    if (!densityCanvas || !speedCanvas) {
      console.error("หาพื้นที่ Canvas ไม่เจอ!");
      return;
    }

    try {
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
    } catch (err) {
        console.error("เกิดข้อผิดพลาดตอนวาดกราฟ:", err);
    }
  }

  onMount(() => {
    fetchSummary();
  });

  onDestroy(() => {
    if (densityChart) densityChart.destroy();
    if (speedChart) speedChart.destroy();
  });
</script>

<div class="min-h-screen bg-snow-50 text-zinc-950 dark:bg-zinc-950 dark:text-zinc-100">
  <div class="border-b border-zinc-200 dark:border-zinc-800">
    <div class="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between gap-4">
      <div>
        <a href="/" class="text-lg font-semibold">📊 Historical Data Analytics</a>
        <p class="ml-5 text-zinc-950 dark:text-zinc-400 text-sm">สรุปสถิติการจราจรย้อนหลังแบบรายวัน</p>
      </div>
      
      <div class="flex items-center gap-4">
        <select 
          class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-950 dark:text-white text-sm rounded-lg pr-6 outline-none focus:border-blue-500"
          bind:value={selectedDate}
          on:change={() => fetchSummary(selectedDate)}
        >
          {#each availableDates as d}
            <option value={d}>{d}</option>
          {/each}
        </select>
        <a href="/" class="px-4 py-2 bg-white border border-zinc-200 dark:border-zinc-700 dark:bg-zinc-800 hover:bg-snow-100 dark:hover:bg-zinc-700 rounded-lg text-sm">
          🏠 กลับหน้าหลัก
        </a>
        <DarkMode />
      </div>
    </div>
  </div>
  <div class="max-w-6xl mx-auto px-4 py-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6">
        <div class="text-zinc-950 dark:text-zinc-400 text-sm mb-1">รถวิ่งผ่านทั้งหมด (คัน)</div>
        <div class="text-4xl font-bold text-blue-400">{kpis.max_total}</div>
      </div>
      <div class="bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6">
        <div class="text-zinc-950 dark:text-zinc-400 text-sm mb-1">ความเร็วเฉลี่ยทั้งวัน (km/h)</div>
        <div class="text-4xl font-bold text-emerald-400">{kpis.avg_speed}</div>
      </div>
      <div class="bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6">
        <div class="text-zinc-950 dark:text-zinc-400 text-sm mb-1">ความหนาแน่นสูงสุด (คัน/เฟรม)</div>
        <div class="text-4xl font-bold text-red-400">{kpis.max_density}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <div class="bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 h-100 flex flex-col">
        <h2 class="mb-4">📈 ความหนาแน่นของรถ แบ่งตามชั่วโมง (Density)</h2>
        <div class="relative flex-1 w-full"><canvas bind:this={densityCanvas}></canvas></div>
      </div>
      
      <div class="bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 h-100 flex flex-col">
        <h2 class="mb-4">🏎️ ความเร็วเฉลี่ย แบ่งตามชั่วโมง (Speed)</h2>
        <div class="relative flex-1 w-full"><canvas bind:this={speedCanvas}></canvas></div>
      </div>
    </div>
    <div class="rounded-2xl border border-blue-500/30 bg-blue-500/5 p-6 flex items-start gap-5 shadow-lg shadow-blue-900/20">
      <div class="text-4xl animate-pulse">✨</div>
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-sm font-bold text-blue-400 uppercase tracking-wider">AI Insight Analysis</span>
          <span class="px-2 py-0.5 rounded text-[10px] bg-blue-500/20 text-blue-300 border border-blue-500/30">Gemini LLM</span>
        </div>
        <div class="text-xl text-zinc-100 leading-relaxed font-medium italic">
          "{aiInsight}"
        </div>
        <p class="mt-3 text-xs text-zinc-500">* ข้อมูลสรุปนี้สร้างขึ้นโดย AI จากสถิติการตรวจจับในวันที่ {selectedDate}</p>
      </div>
    </div>
  </div>
</div>