<template>
  <component :is="to ? 'RouterLink' : 'div'" :to="to" class="surface group flex flex-col p-4 transition md:p-5 hover:-translate-y-px hover:shadow-lift">
    <div class="flex items-start justify-between gap-3">
      <span class="text-[12.5px] font-medium leading-snug text-ink-mute md:text-[13px]">{{ label }}</span>
      <span v-if="icon" class="hidden size-8 shrink-0 items-center justify-center rounded-full md:flex" :class="tones[tone]">
        <span :class="icon" class="size-[15px]" />
      </span>
    </div>
    <div class="mt-3 font-display text-[32px] leading-none text-ink tabular md:mt-5 md:text-[44px]">{{ value }}</div>
    <div v-if="hint" class="mt-2.5 flex items-center gap-1.5 text-[12px] md:mt-3 md:text-[13px]" :class="hintTone ? hintTones[hintTone] : 'text-ink-mute'">
      <span v-if="hintTone" class="size-1.5 rounded-full bg-current" />{{ hint }}
    </div>
  </component>
</template>

<script setup>
defineProps({ label: String, value: [String, Number], icon: String, hint: String, hintTone: String, to: [String, Object],
  tone: { type: String, default: 'green' } })
const tones = { green: 'bg-paper-deep text-ink-soft', amber: 'bg-warn-soft text-warn', red: 'bg-alert-soft text-alert',
  ink: 'bg-paper-deep text-ink-soft', blue: 'bg-info-soft text-info' }
const hintTones = { red: 'text-alert', amber: 'text-alert', green: 'text-ink-mute' }
</script>
