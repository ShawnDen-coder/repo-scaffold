import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export interface NavItem {
  slug: string
  title: string
  description: string
  path: string
  highlights: string[]
}

export interface FolderTreeItem {
  name: string
  path: string
  description: string
  summary?: string
  highlights?: string[]
  children?: FolderTreeItem[]
}

const seedNavItems: NavItem[] = [
  {
    slug: 'components',
    title: 'Components',
    description: 'Reusable UI components organized by responsibility.',
    path: 'src/components/',
    highlights: ['ui/ for primitives', 'layout/ for app shell', 'common/ for shared utilities'],
  },
  {
    slug: 'pages',
    title: 'Pages',
    description: 'Route-level views with colocated sub-components.',
    path: 'src/pages/',
    highlights: ['Each page is a directory', 'Private components live next to the page'],
  },
  {
    slug: 'router',
    title: 'Router',
    description: 'Vue Router configuration and setup helpers.',
    path: 'src/router/',
    highlights: ['Centralized route definitions', 'Lazy-loaded page components'],
  },
  {
    slug: 'stores',
    title: 'Stores',
    description: 'Pinia stores for shared state management.',
    path: 'src/stores/',
    highlights: ['Composition API style stores', 'Type-safe by default'],
  },
]

const seedFolderTree: FolderTreeItem[] = [
  {
    name: 'src',
    path: 'src/',
    description: 'Project source root — all business code lives here.',
    summary: 'All pages, components, routes, and stores are organized under this directory.',
    highlights: ['Unified source root', 'Clear separation of concerns', 'Scalable structure'],
    children: [
      {
        name: 'components',
        path: 'src/components/',
        description: 'Reusable components, organized by responsibility.',
        highlights: ['ui/ — pure presentation', 'layout/ — app shell', 'common/ — shared utilities'],
        children: [
          {
            name: 'ui',
            path: 'src/components/ui/',
            description: 'Primitive UI components (buttons, cards, etc.).',
            highlights: ['Maximum reuse potential', 'No business logic', 'Props + slots API'],
          },
          {
            name: 'layout',
            path: 'src/components/layout/',
            description: 'App shell components (header, footer, nav).',
            highlights: ['Structural, not business', 'Mounted by App.vue', 'Global navigation'],
          },
          {
            name: 'common',
            path: 'src/components/common/',
            description: 'Shared components that don\'t fit ui or layout.',
            highlights: ['Cross-cutting utilities', 'Empty states, notes', 'Avoid turning into a dump'],
          },
        ],
      },
      {
        name: 'pages',
        path: 'src/pages/',
        description: 'Route pages with colocated private components.',
        highlights: ['Page + sub-components in one directory', 'Easier to locate code', 'Scales well'],
      },
      {
        name: 'router',
        path: 'src/router/',
        description: 'Vue Router config and setup helpers.',
        highlights: ['Centralized route map', 'Lazy-loaded components', 'Scroll behavior config'],
      },
      {
        name: 'stores',
        path: 'src/stores/',
        description: 'Pinia stores for shared state.',
        highlights: ['Composition API stores', 'Type-safe getters/actions', 'Shared across pages'],
      },
    ],
  },
]

export const useAppStore = defineStore('app', () => {
  const navItems = ref<NavItem[]>(seedNavItems)
  const folderTree = computed(() => seedFolderTree)
  const activeNavSlug = ref<string>(seedNavItems[0]?.slug ?? '')

  const activeNavItem = computed(() => navItems.value.find((item) => item.slug === activeNavSlug.value))

  function setActiveNav(slug: string) {
    activeNavSlug.value = slug
  }

  return {
    activeNavItem,
    activeNavSlug,
    folderTree,
    navItems,
    setActiveNav,
  }
})
