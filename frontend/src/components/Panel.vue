<template>
  <section class="card flex flex-col">
    <header v-if="title || $slots.actions" class="flex items-center justify-between gap-2 border-b border-outline-gray-1 px-4 py-3">
      <div class="flex items-center gap-2">
        <span v-if="icon" :class="[icon, iconClass]" class="size-4" />
        <h2 class="text-base font-semibold text-ink-gray-9">{{ title }}</h2>
        <span v-if="count !== undefined && count !== null" class="rounded-full bg-surface-gray-2 px-2 py-0.5 text-xs font-medium text-ink-gray-6 tabular">{{ count }}</span>
      </div>
      <slot name="actions" />
    </header>
    <div class="flex-1" :class="padded && 'p-4'"><slot /></div>
  </section>
</template>

<script setup>
defineProps({ title: String, icon: String, iconClass: { type: String, default: 'text-ink-gray-5' }, count: [Number, String], padded: Boolean })
</script>
