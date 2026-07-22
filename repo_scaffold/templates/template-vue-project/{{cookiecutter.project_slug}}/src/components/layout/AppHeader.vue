<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { RouterLink, useRoute } from 'vue-router'

import { useAppStore } from '@/stores/app'

const projectName = '{{cookiecutter.project_slug}}'
const route = useRoute()
const appStore = useAppStore()
const { navItems } = storeToRefs(appStore)
</script>

<template>
{% raw %}
  <header class="sticky top-0 z-10 border-b border-line/80 bg-slate-50/80 py-4 backdrop-blur-shell">
    <div class="container flex flex-wrap items-center justify-between gap-4">
      <RouterLink class="inline-flex items-center gap-4 text-inherit no-underline" to="/">
        <span
          class="grid h-10 w-10 place-items-center rounded-brand bg-linear-to-br from-brand to-teal-400 font-extrabold text-white"
          >V</span
        >
        <span>
          <strong class="block text-ink-strong">{{ projectName }}</strong>
          <small class="block text-ink-soft">Vue 3 + Router + Pinia + Tailwind</small>
        </span>
      </RouterLink>

      <nav
        class="order-3 inline-flex w-full items-center justify-center gap-2 rounded-full border border-line/85 bg-white/75 p-1 sm:order-0 sm:w-auto"
        aria-label="Primary"
      >
        <RouterLink
          :class="[
            'rounded-full px-4 py-2 font-bold no-underline',
            route.name === 'home' ? 'bg-brand/10 text-brand-strong' : 'text-ink-soft',
          ]"
          to="/"
        >
          Home
        </RouterLink>
        <RouterLink
          :class="[
            'rounded-full px-4 py-2 font-bold no-underline',
            route.name === 'about' ? 'bg-brand/10 text-brand-strong' : 'text-ink-soft',
          ]"
          to="/about"
        >
          About
        </RouterLink>
      </nav>
    </div>
  </header>
{% endraw %}
</template>
