<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { RouteLocationRaw } from 'vue-router'

const props = withDefaults(
  defineProps<{
    href?: string
    to?: RouteLocationRaw
    variant?: 'primary' | 'secondary'
  }>(),
  {
    variant: 'primary',
  },
)

const componentTag = computed(() => {
  if (props.to) {
    return RouterLink
  }

  if (props.href) {
    return 'a'
  }

  return 'button'
})

const componentProps = computed(() => {
  if (props.to) {
    return { to: props.to }
  }

  if (props.href) {
    return {
      href: props.href,
      target: '_blank',
      rel: 'noreferrer',
    }
  }

  return { type: 'button' }
})

const buttonClass = computed(() => {
  const baseClass =
    'inline-flex min-h-12 items-center justify-center gap-2 rounded-full border px-5 py-3.5 font-bold no-underline transition duration-200 hover:-translate-y-0.5'

  if (props.variant === 'secondary') {
    return `${baseClass} border-line bg-white/70 text-ink-strong`
  }

  return `${baseClass} border-transparent bg-brand text-white hover:bg-brand-strong`
})
</script>

<template>
{% raw %}
  <component :is="componentTag" :class="buttonClass" v-bind="componentProps">
    <slot />
  </component>
{% endraw %}
</template>
