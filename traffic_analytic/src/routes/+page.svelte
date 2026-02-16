<script lang="ts">
  import { goto } from '$app/navigation';

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
    // ⚠️ หมายเหตุ: ถ้าคุณยังไม่ได้ทำระบบอัปโหลดจริง
    // เราจะส่ง "ชื่อไฟล์" ไปที่ dashboard ก่อน (mock)
    // ถ้าจะทำจริง ต้องทำ endpoint upload แล้วส่ง URL/ID แทน
    const qs = new URLSearchParams({
      video: file.name
    });

    await new Promise((r) => setTimeout(r, 300));
    loading = false;

    goto(`/dashboard?${qs.toString()}`);
  }
</script>

<div class="min-h-screen bg-zinc-950 text-zinc-100">
  <!-- Header เดิม (เหมือน dashboard) -->
  <div class="border-b border-zinc-800">
    <div class="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between gap-4">
      <div>
        <div class="text-lg font-semibold">🚦 Smart Traffic AI</div>
        <div class="text-sm text-zinc-400">Video Input</div>
      </div>

      <div class="flex items-center gap-3 text-sm">
        <div class="text-zinc-400">🟢 Online</div>
        <div class="text-zinc-400">
          Last Updated: {lastUpdated.toLocaleTimeString()}
        </div>
      </div>
    </div>
  </div>

  <!-- กล่อง Upload อยู่กลางจอ -->
  <div class="mx-auto max-w-6xl px-4 py-10">
    <div class="min-h-[70vh] flex items-center justify-center">
      <div class="w-full max-w-2xl rounded-2xl border border-zinc-800 bg-zinc-900/40 p-8">
        <div class="text-xl font-semibold">Upload Video</div>
        <div class="mt-1 text-sm text-zinc-400">
          Drag & drop a video here, or choose a file to analyze in Dashboard.
        </div>

        <!-- Drop zone -->
        <div
          class="mt-6 rounded-2xl border border-dashed border-zinc-700 bg-zinc-950 p-10 text-center"
          on:drop={onDrop}
          on:dragover={onDragOver}
        >
          <div class="text-zinc-300 font-medium">Drop video file here</div>
          <div class="mt-2 text-sm text-zinc-500">Supported: mp4, mov, webm (any video/*)</div>

          <div class="mt-6">
            <label class="inline-flex cursor-pointer items-center justify-center rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm hover:bg-zinc-900">
              Choose file
              <input class="hidden" type="file" accept="video/*" on:change={onPick} />
            </label>
          </div>

          <div class="mt-4 text-sm text-zinc-400">
            Selected: <span class="text-zinc-200">{filename}</span>
          </div>

          {#if error}
            <div class="mt-3 text-sm text-red-400">{error}</div>
          {/if}
        </div>

        <!-- Apply button -->
        <button
          class="mt-6 w-full rounded-2xl bg-zinc-100 text-zinc-950 font-semibold py-3 disabled:opacity-60"
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
