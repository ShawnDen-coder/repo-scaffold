<script setup lang="ts">
import { storeToRefs } from 'pinia'

import HeroSection from '@/pages/HomePage/HeroSection.vue'
import StructureHighlights from '@/pages/HomePage/StructureHighlights.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const { folderTree, navItems } = storeToRefs(appStore)
</script>

<template>
{% raw %}
  <div class="home-page">
    <HeroSection :featured-item="navItems[0]" />
    <StructureHighlights :items="folderTree" />
  </div>
{% endraw %}
</template>

<style scoped>
.home-page {
  padding: 2rem 0 3rem;
}
</style>
