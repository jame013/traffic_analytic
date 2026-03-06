<script>
  import { DarkMode } from "flowbite-svelte";
  import { onMount } from 'svelte';

  let lastUpdated = $state(new Date());
  let { title = '', camera = '' } = $props();

  onMount(() => {
    const interval = setInterval(() => {
      lastUpdated = new Date();
    }, 1000);
    return () => clearInterval(interval);
  });

</script>

<div class="border-b border-zinc-800">
    <div class="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between gap-4">
      <div>
        <a href="/" class="text-lg font-semibold">🚦 Smart Traffic AI</a>
        <div class="ml-5 text-sm text-zinc-950 dark:text-zinc-400">{title} {camera}</div>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <a href="/analytics" class="px-3 py-1.5 rounded-lg border bg-blue-500/10 text-blue-400 border-blue-500/30 hover:bg-blue-500/20 transition-colors">
          📊 ดูสถิติย้อนหลัง
        </a>
        <div class="text-zinc-950 dark:text-zinc-400">Update: {lastUpdated.toLocaleTimeString()}</div>
        <DarkMode />
      </div>
    </div>
</div>