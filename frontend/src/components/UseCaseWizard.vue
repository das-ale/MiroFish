<template>
  <div class="ucw">
    <div class="ucw-chips">
      <button
        v-for="opt in options"
        :key="opt.id"
        class="ucw-chip"
        :class="{ active: modelValue.useCase === opt.id }"
        :disabled="disabled"
        @click="select(opt.id)"
      >{{ opt.title }}</button>
    </div>
    <p v-if="currentCase" class="ucw-desc">{{ localized(currentCase.description) }}</p>
    <div v-if="currentCase" class="ucw-form">
      <div v-for="f in currentCase.form_fields" :key="f.key" class="ucw-field">
        <label>
          {{ localized(f.label) }}
          <span v-if="f.required" class="req">*</span>
        </label>
        <textarea
          v-if="f.type === 'textarea'"
          :value="modelValue.inputs[f.key] || ''"
          rows="2"
          :disabled="disabled"
          @input="setInput(f.key, $event.target.value)"
        ></textarea>
        <input
          v-else
          type="text"
          :value="modelValue.inputs[f.key] || ''"
          :disabled="disabled"
          @input="setInput(f.key, $event.target.value)"
        />
      </div>
      <p v-if="modelValue.useCase === 'ad_test'" class="ucw-note">
        {{ $t('home.adTestNote') }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { listUseCases } from '../api/graph'

const props = defineProps({
  modelValue: { type: Object, required: true }, // { useCase: null|string, inputs: {} }
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
const { t, locale } = useI18n()

const useCases = ref([])
const localized = (obj) => (obj && (obj[locale.value] || obj.es || obj.en)) || ''

const options = computed(() => ([
  { id: null, title: t('home.useCaseFree') },
  ...useCases.value.map(u => ({ id: u.id, title: localized(u.name) })),
]))
const currentCase = computed(() =>
  useCases.value.find(u => u.id === props.modelValue.useCase) || null
)

const select = (id) => {
  emit('update:modelValue', { useCase: id, inputs: {} })
}
const setInput = (key, value) => {
  emit('update:modelValue', {
    useCase: props.modelValue.useCase,
    inputs: { ...props.modelValue.inputs, [key]: value },
  })
}

onMounted(async () => {
  try {
    const res = await listUseCases()
    if (res.success) useCases.value = res.data.use_cases || []
  } catch (e) { console.error('use-cases', e) }
})

defineExpose({
  isValid: () => {
    if (!currentCase.value) return true
    return currentCase.value.form_fields
      .filter(f => f.required)
      .every(f => (props.modelValue.inputs[f.key] || '').trim() !== '')
  },
})
</script>

<style scoped>
.ucw { margin-bottom: 12px; }
.ucw-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.ucw-chip { padding: 6px 14px; border-radius: 16px; border: 1px solid rgba(128,128,128,0.35); background: transparent; cursor: pointer; font-size: 12.5px; }
.ucw-chip.active { border-color: #4a7dff; color: #4a7dff; background: rgba(74,125,255,0.08); font-weight: 600; }
.ucw-desc { font-size: 12px; opacity: 0.7; margin: 8px 0 4px; }
.ucw-form { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.ucw-field label { display: block; font-size: 12px; font-weight: 600; margin-bottom: 3px; }
.req { color: #d9534f; }
.ucw-field input, .ucw-field textarea { width: 100%; box-sizing: border-box; border: 1px solid rgba(128,128,128,0.3); border-radius: 6px; padding: 7px 9px; font-size: 13px; font-family: inherit; background: transparent; color: inherit; }
.ucw-note { font-size: 11px; opacity: 0.65; margin: 2px 0 0; font-style: italic; }
</style>
