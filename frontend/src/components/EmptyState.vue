<template>
  <div class="flex flex-col items-center justify-center px-6 py-10 text-center">
    <div class="mb-3 flex size-11 items-center justify-center rounded-full bg-surface-gray-2">
      <span :class="icon" class="size-5 text-ink-gray-5" />
    </div>
    <p class="text-base font-medium text-ink-gray-8">{{ title }}</p>
    <p v-if="text" class="mt-1 max-w-xs text-sm text-ink-gray-5">{{ text }}</p>
    <div v-if="$slots.default" class="mt-4"><slot /></div>
  </div>
</template>

<script setup>
defineProps({ title: String, text: String, icon: { type: String, default: 'lucide-inbox' } })
</script>
