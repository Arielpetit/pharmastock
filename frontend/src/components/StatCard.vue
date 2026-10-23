<template>
  <component :is="to ? 'RouterLink' : 'div'" :to="to" class="surface group flex flex-col p-4 transition md:p-5 hover:-translate-y-px hover:shadow-lift">
    <div class="flex items-start justify-between gap-3">
      <span class="text-[13px] font-medium text-ink-mute">{{ label }}</span>
      <span class="flex size-8 shrink-0 items-center justify-center rounded-full" :class="tones[tone]">
        <span :class="icon" class="size-[15px]" />
      </span>
    </div>
    <div class="mt-4 font-display text-[36px] leading-none text-ink tabular md:mt-5 md:text-[44px]">{{ value }}</div>
    <div class="mt-3 flex items-center gap-1.5 text-[13px]" :class="hintTone ? hintTones[hintTone] : 'text-ink-mute'">
      <span v-if="hintTone" class="size-1.5 rounded-full bg-current" />{{ hint }}
    </div>
  </component>
</template>

<script setup>
defineProps({ label: String, value: [String, Number], icon: String, hint: String, hintTone: String, to: [String, Object],
  tone: { type: String, default: 'green' } })
const tones = { green: 'bg-apo-soft text-apo', amber: 'bg-warn-soft text-warn', red: 'bg-alert-soft text-alert',
  ink: 'bg-paper-deep text-ink-soft', blue: 'bg-[#E8EEF7] text-[#2F4E7A]' }
const hintTones = { red: 'text-alert', amber: 'text-warn', green: 'text-apo' }
</script>
