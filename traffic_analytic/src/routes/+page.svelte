<script lang="ts">
  import { goto } from '$app/navigation';
  import { DarkMode } from "flowbite-svelte";

  let lastUpdated = new Date();

  // เก็บไฟล์ที่ผู้ใช้เลือก (client-side)
  let file: File | null = null;
  let error = '';
  let loading = false;

  // สำหรับโชว์ชื่อไฟล์ใน UI
  $: filename = file?.name ?? 'No file selected';

  // รับไฟล์จาก input
  function onPick(e: Event) {
    const input = e.currentTarget as HTMLInputElement;
    const f = input.files?.[0];
    if (!f) return;

    // รับเฉพาะวิดีโอ (แบบง่าย)
    if (!f.type.startsWith('video/')) {
      error = 'Please upload a video file (mp4, mov, etc.)';
      file = null;
      return;
    }

    error = '';
    file = f;
  }

  // drag & drop
  function onDrop(e: DragEvent) {
    e.preventDefault();
    const f = e.dataTransfer?.files?.[0];
    if (!f) return;

    if (!f.type.startsWith('video/')) {
      error = 'Please upload a video file (mp4, mov, etc.)';
      file = null;
      return;
    }

    error = '';
    file = f;
  }

  function onDragOver(e: DragEvent) {
    e.preventDefault();
  }

  async function apply() {
    error = '';
    if (!file) {
      error = 'Please select a video first.';
      return;
    }

    loading = true;
    
    // --- โค้ดใหม่ที่เชื่อมกับ API ---
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData
      });
      
      const data = await response.json();
      
      if(data.status === "success") {
        const qs = new URLSearchParams({
          video: data.filename // ส่งชื่อไฟล์ที่เซฟใน backend ไปให้ dashboard
        });
        goto(`/dashboard?${qs.toString()}`);
      }
    } catch (err) {
      error = "Failed to connect to AI server. Is it running?";
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen bg-snow-50 dark:bg-zinc-950 text-zinc-950 dark:text-zinc-100">
  <!-- Header เดิม (เหมือน dashboard) -->
  <div class="border-b border-zinc-800">
    <div class="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between gap-4">
      <div class="text-lg font-semibold">🚦 Smart Traffic AI</div>

      <div class="flex items-center gap-3 text-sm text-zinc-950 dark:text-zinc-400">
        <div>🟢 Online</div>
        <div>Last Updated: {lastUpdated.toLocaleTimeString()}</div>
        <DarkMode />
      </div>
    </div>
  </div>

  <!-- กล่อง Upload อยู่กลางจอ -->
  <div class="mx-auto max-w-6xl px-4 py-10 text-zinc-950 dark:text-zinc-100">
    <div class="min-h-[70vh] flex items-center justify-center">
      <div class="w-full max-w-2xl rounded-2xl border border-zinc-800 bg-white  dark:bg-zinc-900/40 p-8">
        <div class="text-xl font-semibold">Upload Video</div>
        <div class="mt-1 text-sm dark:text-zinc-400">
          Drag & drop a video here, or choose a file to analyze in Dashboard.
        </div>

        <!-- Drop zone -->
        <div
          role="button"
          tabindex="0"
          class="mt-6 rounded-2xl border border-dashed border-zinc-700 dark:bg-zinc-950 p-10 text-center text-zinc-950"
          on:drop={(onDrop)}
          on:dragover={onDragOver}
        >
          <div class="dark:text-zinc-300 font-medium">Drop video file here</div>
          <div class="mt-2 text-sm dark:text-zinc-500">Supported: mp4, mov, webm (any video/*)</div>

          <div class="mt-6">
            <label class="inline-flex cursor-pointer items-center justify-center rounded-xl border border-zinc-700 dark:text-zinc-100 dark:bg-zinc-950 px-4 py-2 text-sm hover:text-zinc-100 hover:bg-zinc-800">
              Choose file
              <input class="hidden" type="file" accept="video/*" on:change={onPick} />
            </label>
          </div>

          <div class="mt-4 text-sm text-zinc-950 dark:text-zinc-400">
            Selected: <span class="text-zinc-700 dark:text-zinc-200">{filename}</span>
          </div>

          {#if error}
            <div class="mt-3 text-sm text-red-400">{error}</div>
          {/if}
        </div>

        <!-- Apply button -->
        <button
          class="mt-6 w-full rounded-2xl bg-zinc-950 text-zinc-100 dark:bg-zinc-100 dark:text-zinc-950 font-semibold py-3 disabled:opacity-60"
          on:click={apply}
          disabled={loading}
        >
          {#if loading}Applying…{:else}Apply → Analyze in Dashboard{/if}
        </button>

        <div class="mt-3 text-xs text-zinc-500">
          * This page only selects the video. Analysis happens in Dashboard.
        </div>
      </div>
    </div>
  </div>
</div>
