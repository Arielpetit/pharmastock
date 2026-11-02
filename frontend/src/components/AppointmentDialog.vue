<template>
  <Sheet v-model:open="ui.appointment.open" :title="t('Book an appointment')" :message="t('The patient will be listed for the doctor on that day.')"
    icon="lucide-calendar-plus" theme="blue" size="xl">
    <form class="grid grid-cols-2 items-start gap-x-3 gap-y-4 sm:gap-x-4" @submit.prevent="save">
      <PatientPicker v-if="ui.appointment.open" v-model="form.patient" class="col-span-2" :label="t('Patient')" required />
      <FormControl variant="outline" v-model="form.practitioner" type="select" class="col-span-2" :label="t('Doctor')" size="lg" required
        :options="doctors.map((d) => ({ label: d.practitioner_name + (d.me ? ' (' + t('you') + ')' : ''), value: d.name }))" :placeholder="t('Choose…')" />
      <FormControl variant="outline" v-model="form.date" type="date" format="D MMM YYYY" :label="t('Day')" size="lg" :min="today()" class="col-span-2 sm:col-span-1" />
      <FormControl variant="outline" v-model="form.time" type="time" :label="t('Time')" size="lg" class="col-span-2 sm:col-span-1" />
      <FormControl variant="outline" v-model="form.duration" type="select" class="col-span-2 sm:col-span-1" :label="t('Length')" size="lg"
        :options="[15, 20, 30, 45, 60].map((m) => ({ label: t('{0} min', m), value: m }))" />
      <FormControl variant="outline" v-model="form.notes" class="col-span-2" type="textarea" :rows="2" :label="t('Reason (optional)')" size="lg"
        :placeholder="t('e.g. Follow-up after the fever')" />
      <ErrorMessage class="col-span-2" :message="error" />
    </form>
    <template #actions>
      <Btn variant="ghost" :label="t('Cancel')" @click="ui.appointment.open = false" />
      <Btn variant="primary" icon="lucide-check" :label="t('Book')" :loading="saving" @click="save" />
    </template>
  </Sheet>
</template>

<script setup>
import Sheet from './Sheet.vue'
import { reactive, ref, watch } from 'vue'
import { ErrorMessage, FormControl, toast } from 'frappe-ui'
import Btn from './Btn.vue'
import PatientPicker from './PatientPicker.vue'
import { get, post } from '@/api'
import { t } from '@/i18n'
import { today } from '@/format'
import { session } from '@/session'
import { ui, changed, H } from '@/ui'

const doctors = ref([])
const blank = () => ({ patient: ui.appointment.patient, practitioner: session.practitioner || '', date: today(), time: '09:00', duration: 20, notes: '' })
const form = reactive(blank())
const saving = ref(false)
const error = ref('')

watch(() => ui.appointment.open, async (open) => {
  if (!open) return
  Object.assign(form, blank())
  error.value = ''
  try {
    doctors.value = await get(H('practitioners'))
    if (!form.practitioner && doctors.value.length === 1) form.practitioner = doctors.value[0].name
  } catch (e) {
    error.value = e.message
  }
})

async function save() {
  error.value = ''
  if (!form.patient) return (error.value = t('Please choose a patient.'))
  if (!form.practitioner) return (error.value = t('Please choose a doctor.'))
  saving.value = true
  try {
    await post(H('save_appointment'), { ...form, duration: Number(form.duration) })
    ui.appointment.open = false
    toast.success(t('Appointment booked'))
    changed()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>
