<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

<template>
{% raw %}
  <aside class="rounded-r-sm rounded-l-none border-l-4 border-accent bg-accent/10 px-note py-4">
    <p class="m-0 font-bold text-ink-strong">{{ title }}</p>
    <p class="mt-offset-xs mb-0 text-ink-soft">{{ description }}</p>
  </aside>
{% endraw %}
</template>
