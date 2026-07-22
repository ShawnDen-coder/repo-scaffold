<script setup lang="ts">
import AppCard from '@/components/ui/AppCard.vue'
</script>

<template>
{% raw %}
  <section class="container grid gap-6 py-12 max-[840px]:pt-8">
    <AppCard>
      <div class="grid gap-4">
        <p class="eyebrow">About</p>
        <h1 class="section-title">About this template</h1>
        <p class="section-lead">
          This project was generated with a Vue 3 + Vue Router + Pinia + Tailwind CSS template that
          emphasizes a scalable directory structure. Edit this page to make it your own.
        </p>
        <ul class="m-0 pl-note text-ink-soft">
          <li>components/ui — reusable primitives</li>
          <li>components/layout — app shell</li>
          <li>components/common — shared utilities</li>
          <li>pages — route views with colocated sub-components</li>
          <li>router — centralized route config</li>
          <li>stores — Pinia state management</li>
        </ul>
      </div>
    </AppCard>
  </section>
{% endraw %}
</template>
