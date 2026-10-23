<template>
  <component :is="to ? 'RouterLink' : 'div'" :to="to"
    class="card group flex flex-col gap-3 p-4 transition hover:border-outline-gray-3 hover:shadow-md">
    <div class="flex items-center justify-between">
      <span class="text-sm font-medium text-ink-gray-5">{{ label }}</span>
      <span class="flex size-8 items-center justify-center rounded-4" :class="tones[tone].bg">
        <span :class="[icon, tones[tone].fg]" class="size-4" />
      </span>
    </div>
    <div class="flex items-baseline gap-2">
      <span class="text-3xl font-semibold tracking-tight text-ink-gray-9 tabular">{{ value }}</span>
      <span v-if="unit" class="text-sm text-ink-gray-5">{{ unit }}</span>
    </div>
    <div v-if="hint" class="text-sm" :class="hintClass || 'text-ink-gray-5'">{{ hint }}</div>
  </component>
</template>

<script setup>
defineProps({ label: String, value: [String, Number], unit: String, icon: String, hint: String, hintClass: String, to: [String, Object],
  tone: { type: String, default: 'teal' } })
const tones = {
  teal: { bg: 'bg-teal-50', fg: 'text-teal-700' },
  blue: { bg: 'bg-blue-50', fg: 'text-blue-600' },
  red: { bg: 'bg-red-50', fg: 'text-red-600' },
  amber: { bg: 'bg-amber-50', fg: 'text-amber-600' },
  violet: { bg: 'bg-violet-50', fg: 'text-violet-600' },
}
</script>
