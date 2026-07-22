<script setup lang="ts">
defineProps<{
  msg: string
}>()
</script>

<template>
{% raw %}
  <div>
    <h1>{{ msg }}</h1>
  </div>
{% endraw %}
</template>
