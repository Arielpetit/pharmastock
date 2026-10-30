<template>
  <component :is="to ? 'RouterLink' : 'div'" :to="to"
    class="surface group relative flex min-h-[140px] flex-col overflow-hidden p-4 transition duration-200 md:min-h-[168px] md:p-5"
    :class="to && 'hover:-translate-y-0.5 hover:shadow-lift'">
    <div class="flex items-center justify-between gap-2">
      <span class="flex size-9 shrink-0 items-center justify-center rounded-[12px] md:size-10" :class="tones[tone]">
        <span :class="icon" class="size-[17px] md:size-[19px]" />
      </span>
      <span v-if="to" class="lucide-arrow-up-right size-4 text-ink-faint opacity-0 transition duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:opacity-100" />
    </div>

    <div class="pt-4 md:pt-5">
      <div class="flex items-baseline gap-1.5">
        <span class="font-display text-[38px] leading-none tabular md:text-[52px]" :class="valueTones[tone]">{{ value }}</span>
        <span v-if="unit" class="text-[12.5px] text-ink-mute md:text-[13.5px]">{{ unit }}</span>
      </div>
      <p class="mt-2 text-[13px] font-medium leading-snug text-ink-soft md:text-[14px]">{{ label }}</p>
      <p v-if="hint" class="mt-1 flex items-center gap-1.5 text-[12px] leading-snug md:text-[12.5px]" :class="hintTone ? hintTones[hintTone] : 'text-ink-mute'">
        <span v-if="hintTone" class="size-1.5 shrink-0 rounded-full bg-current" />{{ hint }}
      </p>
    </div>
  </component>
</template>

<script setup>
defineProps({ label: String, value: [String, Number], unit: String, icon: { type: String, default: 'lucide-circle' },
  hint: String, hintTone: String, to: [String, Object], tone: { type: String, default: 'green' } })
// icon chip colour and, for warnings, the number itself
const tones = { green: 'bg-apo-soft text-apo', amber: 'bg-warn-soft text-warn', red: 'bg-alert-soft text-alert',
  ink: 'bg-paper-deep text-ink-soft', blue: 'bg-info-soft text-info' }
const valueTones = { green: 'text-ink', ink: 'text-ink', blue: 'text-ink', amber: 'text-warn', red: 'text-alert' }
const hintTones = { red: 'text-alert', amber: 'text-warn', green: 'text-ink-mute' }
</script>
