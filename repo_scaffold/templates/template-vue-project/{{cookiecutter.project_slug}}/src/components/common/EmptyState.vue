<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

<template>
{% raw %}
  <div class="rounded-md border border-dashed border-line bg-white/65 p-6 text-center">
    <p class="m-0 font-bold text-ink-strong">{{ title }}</p>
    <p class="mt-1.5 mb-0 text-ink-soft">{{ description }}</p>
  </div>
{% endraw %}
</template>
