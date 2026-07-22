<script setup lang="ts">
import type { FolderTreeItem } from '@/stores/app'

const props = withDefaults(
  defineProps<{
    items: FolderTreeItem[]
    level?: number
    activePath?: string
  }>(),
  {
    level: 0,
    activePath: '',
  },
)

const emit = defineEmits<{
  select: [item: FolderTreeItem]
}>()

function handleSelect(item: FolderTreeItem) {
  emit('select', item)
}
</script>

<template>
{% raw %}
  <ul class="m-0 grid list-none gap-3 p-0">
    <li v-for="item in items" :key="item.path" class="grid gap-3">
      <button
        type="button"
        class="w-full cursor-pointer rounded-md border border-line bg-white/82 px-note py-4 text-left shadow-soft"
        :class="item.path === activePath ? 'border-brand/60 bg-brand/10' : ''"
        :style="{ '--level': String(level) }"
        @click="handleSelect(item)"
      >
        <div
          class="flex flex-wrap items-center gap-soft"
          :style="{ paddingLeft: `calc(1rem + ${level} * 1.25rem)` }"
        >
          <span class="text-tree font-bold text-ink-strong">{{ item.name }}</span>
          <code>{{ item.path }}</code>
        </div>
        <p
          class="mb-0 mt-3 text-ink-soft"
          :style="{ paddingLeft: `calc(1rem + ${level} * 1.25rem)` }"
        >
          {{ item.description }}
        </p>
      </button>

      <FolderTree
        v-if="item.children?.length"
        :items="item.children"
        :level="level + 1"
        :active-path="activePath"
        @select="handleSelect"
      />
    </li>
  </ul>
{% endraw %}
</template>
