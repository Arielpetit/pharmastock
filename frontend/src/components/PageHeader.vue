<template>
  <div class="rise mb-7 flex flex-wrap items-end justify-between gap-4">
    <div class="min-w-0">
      <RouterLink v-if="back" :to="back" class="mb-3 inline-flex items-center gap-1.5 text-[13px] font-medium text-ink-mute transition hover:text-ink">
        <span class="lucide-arrow-left size-3.5" /> {{ backLabel }}
      </RouterLink>
      <p v-else-if="eyebrow" class="eyebrow mb-2">{{ eyebrow }}</p>
      <h1 class="font-display text-[34px] leading-[1.05] text-ink md:text-[40px]">{{ title }}</h1>
      <p v-if="subtitle" class="mt-2 max-w-xl text-[15px] text-ink-mute">{{ subtitle }}</p>
      <slot name="meta" />
    </div>
    <div v-if="$slots.actions" class="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto sm:flex-wrap sm:items-center [&>*:only-child]:col-span-2"><slot name="actions" /></div>
  </div>
</template>

<script setup>
defineProps({ title: String, subtitle: String, eyebrow: String, back: [String, Object], backLabel: String })
</script>
