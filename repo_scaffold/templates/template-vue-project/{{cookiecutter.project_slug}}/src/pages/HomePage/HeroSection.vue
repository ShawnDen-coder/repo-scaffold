<script setup lang="ts">
import AppButton from '@/components/ui/AppButton.vue'
import type { NavItem } from '@/stores/app'

defineProps<{
  featuredItem: NavItem
}>()
</script>

<template>
{% raw %}
  <section class="hero-section container">
    <div class="hero-section__copy">
      <p class="eyebrow">Vue Project Structure</p>
      <h1 class="section-title">Understand your project layout at a glance.</h1>
      <p class="section-lead">
        This template ships with a layered directory structure — components are split by
        responsibility, pages colocate their private sub-components, and routes & stores each have
        a dedicated home.
      </p>
      <div class="hero-section__actions">
        <AppButton to="/about">
          About this template
        </AppButton>
        <AppButton variant="secondary" href="https://vuejs.org/">
          Vue docs
        </AppButton>
      </div>
    </div>
    <div class="hero-section__panel">
      <p class="chip">Featured</p>
      <h2>{{ featuredItem.title }}</h2>
      <p>{{ featuredItem.description }}</p>
      <dl>
        <div>
          <dt>Path</dt>
          <dd>{{ featuredItem.path }}</dd>
        </div>
      </dl>
    </div>
  </section>
{% endraw %}
</template>

<style scoped>
.hero-section {
  display: grid;
  grid-template-columns: 1.4fr 0.9fr;
  gap: 1.5rem;
  padding: 3rem 0 2rem;
}

.hero-section__copy,
.hero-section__panel {
  padding: 2rem;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(219, 228, 240, 0.85);
  box-shadow: var(--shadow);
}

.hero-section__copy {
  display: grid;
  gap: 1.25rem;
}

.hero-section__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
}

.hero-section__panel h2,
.hero-section__panel p,
.hero-section__panel dl {
  margin: 0;
}

.hero-section__panel {
  display: grid;
  align-content: start;
  gap: 1rem;
}

.hero-section__panel h2 {
  color: var(--ink-strong);
  font-size: 1.5rem;
}

.hero-section__panel p {
  color: var(--ink-soft);
}

.hero-section__panel dl {
  display: flex;
  gap: 1.2rem;
}

.hero-section__panel dt {
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-soft);
}

.hero-section__panel dd {
  margin: 0.2rem 0 0;
  color: var(--ink-strong);
  font-weight: 700;
}

@media (max-width: 840px) {
  .hero-section {
    grid-template-columns: 1fr;
    padding-top: 2rem;
  }
}
</style>
