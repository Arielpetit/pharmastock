<template>
  <div class="mb-5 flex flex-wrap items-end justify-between gap-3">
    <div class="min-w-0">
      <RouterLink v-if="back" :to="back" class="mb-1.5 inline-flex items-center gap-1 text-sm text-ink-gray-5 hover:text-ink-gray-8">
        <span class="lucide-arrow-left size-3.5" /> {{ backLabel }}
      </RouterLink>
      <h1 class="truncate text-2xl font-semibold tracking-tight text-ink-gray-9">{{ title }}</h1>
      <p v-if="subtitle" class="mt-1 text-base text-ink-gray-5">{{ subtitle }}</p>
      <slot name="meta" />
    </div>
    <div v-if="$slots.actions" class="flex flex-wrap items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({ title: String, subtitle: String, back: [String, Object], backLabel: String })
</script>
