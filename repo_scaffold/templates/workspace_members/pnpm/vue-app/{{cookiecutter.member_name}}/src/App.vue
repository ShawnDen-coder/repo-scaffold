<script setup lang="ts">
const title = "Vue workspace app";
</script>

<template>
  <main class="min-h-screen bg-slate-950 p-8 text-slate-100">
    <section class="mx-auto max-w-3xl space-y-4">
      <p class="text-sm font-medium text-emerald-300">{{ cookiecutter.package_name }}</p>
      <h1 class="text-4xl font-bold tracking-tight">{% raw %}{{ title }}{% endraw %}</h1>
      <p class="text-slate-300">Vite, Tailwind CSS, Biome, and Vitest are ready.</p>
    </section>
  </main>
</template>
