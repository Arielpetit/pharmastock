<template>
  <div class="flex items-center gap-2.5">
    <img :src="MARK" :class="markClass" alt="" />
    <div v-if="!markOnly" class="leading-tight">
      <div class="text-lg font-bold tracking-tight text-ink-gray-9" :class="inverted && '!text-white'">
        Pharma<span class="text-[#0f766e]" :class="inverted && '!text-teal-100'">Stock</span>
      </div>
      <div v-if="subtitle" class="truncate text-xs text-ink-gray-5" :class="inverted && '!text-teal-50/80'">{{ subtitle }}</div>
    </div>
  </div>
</template>

<script setup>
const MARK = '/assets/pharmastock/images/logo-mark.svg'
defineProps({
  markOnly: Boolean,
  subtitle: String,
  inverted: Boolean,
  markClass: { type: String, default: 'size-9' },
})
</script>
