<template>
  <div class="experiments-view">
    <div class="exp-header">
      <button class="back-btn" @click="$router.push('/')">←</button>
      <h2>{{ $t('experiments.title') }}</h2>
    </div>

    <div class="exp-layout">
      <!-- Lista -->
      <aside class="exp-list">
        <div class="new-box">
          <p class="new-title">{{ $t('experiments.newAnalysis') }}</p>
          <p class="new-hint">{{ $t('experiments.selectSims') }}</p>
          <div class="sim-select">
            <label v-for="s in completedSims" :key="s.simulation_id" class="sim-option">
              <input type="checkbox" :value="s.simulation_id" v-model="selectedSims" />
              <span class="sim-id">{{ s.simulation_id }}</span>
            </label>
            <p v-if="completedSims.length === 0" class="empty-hint">{{ $t('experiments.noSims') }}</p>
          </div>
          <div class="new-actions">
            <button :disabled="selectedSims.length < 2 || creating" @click="create('compare')">
              {{ creating === 'compare' ? $t('experiments.generating') : $t('experiments.compareBtn') }}
            </button>
            <button :disabled="selectedSims.length < 2 || creating" @click="create('stability')">
              {{ creating === 'stability' ? $t('experiments.generating') : $t('experiments.stabilityBtn') }}
            </button>
          </div>
          <p v-if="createError" class="create-error">{{ createError }}</p>
        </div>

        <div
          v-for="c in comparisons"
          :key="c.comparison_id"
          class="exp-card"
          :class="{ active: current && current.comparison_id === c.comparison_id }"
          @click="open(c.comparison_id)"
        >
          <div class="exp-card-top">
            <span class="exp-type" :class="c.type === 'stability' ? 'type-stb' : 'type-cmp'">
              {{ c.type === 'stability' ? $t('experiments.typeStability') : $t('experiments.typeCompare') }}
            </span>
            <span class="exp-date">{{ (c.created_at || '').slice(0, 16).replace('T', ' ') }}</span>
          </div>
          <p class="exp-label">{{ c.label || c.comparison_id }}</p>
          <p class="exp-sims">{{ c.simulation_ids.length }} sims · {{ c.same_population ? $t('experiments.samePop') : $t('experiments.diffPop') }}</p>
        </div>
        <p v-if="comparisons.length === 0" class="empty-hint">{{ $t('experiments.empty') }}</p>
      </aside>

      <!-- Detalle -->
      <main class="exp-detail">
        <div v-if="!current" class="empty-detail">{{ $t('experiments.selectOne') }}</div>
        <div v-else>
          <div class="detail-meta">
            <span v-for="sid in current.simulation_ids" :key="sid" class="meta-chip mono">{{ sid }}</span>
            <span class="meta-chip" :class="current.same_population ? 'chip-ok' : 'chip-warn'">
              {{ current.same_population ? $t('experiments.samePop') : $t('experiments.diffPop') }}
            </span>
          </div>
          <div class="md-content" v-html="renderedContent"></div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { listComparisons, getComparisonById, createComparison, createStability } from '../api/report'
import { listSimulations } from '../api/simulation'

const comparisons = ref([])
const current = ref(null)
const completedSims = ref([])
const selectedSims = ref([])
const creating = ref(null)
const createError = ref('')

const load = async () => {
  try {
    const res = await listComparisons()
    if (res.success) comparisons.value = res.data.comparisons || []
  } catch (e) { console.error(e) }
  try {
    const res = await listSimulations()
    const sims = res?.data?.simulations || res?.data || []
    completedSims.value = (Array.isArray(sims) ? sims : []).filter(
      s => ['completed', 'stopped'].includes(s.status)
    )
  } catch (e) { console.error(e) }
}

const open = async (cid) => {
  try {
    const res = await getComparisonById(cid)
    if (res.success) current.value = res.data
  } catch (e) { console.error(e) }
}

const create = async (kind) => {
  creating.value = kind
  createError.value = ''
  try {
    const fn = kind === 'compare' ? createComparison : createStability
    const res = await fn(selectedSims.value)
    if (res.success) {
      selectedSims.value = []
      await load()
      current.value = res.data
    } else {
      createError.value = res.error || 'Error'
    }
  } catch (e) {
    createError.value = e?.response?.data?.error || String(e)
  } finally {
    creating.value = null
  }
}

// Renderer markdown compacto con soporte de tablas
const renderedContent = computed(() => {
  const md = current.value?.content || ''
  const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const inline = (t) => esc(t)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
  const lines = md.split('\n')
  let html = ''
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    if (/^\|/.test(line) && i + 1 < lines.length && /^\|[\s:-|]+\|?$/.test(lines[i + 1])) {
      const headers = line.split('|').slice(1, -1).map(c => inline(c.trim()))
      html += '<table><thead><tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr></thead><tbody>'
      i += 2
      while (i < lines.length && /^\|/.test(lines[i])) {
        const cells = lines[i].split('|').slice(1, -1).map(c => inline(c.trim()))
        html += '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>'
        i++
      }
      html += '</tbody></table>'
      continue
    }
    if (/^### /.test(line)) html += `<h4>${inline(line.slice(4))}</h4>`
    else if (/^## /.test(line)) html += `<h3>${inline(line.slice(3))}</h3>`
    else if (/^# /.test(line)) html += `<h2>${inline(line.slice(2))}</h2>`
    else if (/^> /.test(line)) html += `<blockquote>${inline(line.slice(2))}</blockquote>`
    else if (/^[-*] /.test(line)) html += `<li>${inline(line.slice(2))}</li>`
    else if (line.trim() === '') html += ''
    else html += `<p>${inline(line)}</p>`
    i++
  }
  return html
})

onMounted(load)
</script>

<style scoped>
.experiments-view { max-width: 1280px; margin: 0 auto; padding: 20px; }
.exp-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.back-btn { border: 1px solid rgba(128,128,128,0.3); background: transparent; border-radius: 8px; padding: 4px 12px; cursor: pointer; }
.exp-layout { display: grid; grid-template-columns: 320px 1fr; gap: 18px; align-items: start; }
.exp-list { display: flex; flex-direction: column; gap: 10px; }
.new-box { border: 1px dashed rgba(74,125,255,0.5); border-radius: 10px; padding: 12px; }
.new-title { font-weight: 600; font-size: 13px; margin: 0 0 2px; }
.new-hint { font-size: 11px; opacity: 0.65; margin: 0 0 8px; }
.sim-select { max-height: 180px; overflow: auto; display: flex; flex-direction: column; gap: 4px; }
.sim-option { display: flex; gap: 6px; align-items: center; font-size: 11px; cursor: pointer; }
.sim-id { font-family: monospace; }
.new-actions { display: flex; gap: 8px; margin-top: 10px; }
.new-actions button { flex: 1; padding: 6px 8px; border-radius: 6px; border: 1px solid #4a7dff; background: transparent; color: #4a7dff; cursor: pointer; font-size: 12px; }
.new-actions button:disabled { opacity: 0.45; cursor: not-allowed; }
.create-error { color: #d9534f; font-size: 11px; margin: 6px 0 0; }
.exp-card { border: 1px solid rgba(128,128,128,0.25); border-radius: 10px; padding: 10px 12px; cursor: pointer; }
.exp-card:hover, .exp-card.active { border-color: #4a7dff; }
.exp-card-top { display: flex; justify-content: space-between; align-items: center; }
.exp-type { font-size: 10px; padding: 1px 8px; border-radius: 10px; font-weight: 600; }
.type-cmp { background: rgba(74,125,255,0.15); color: #4a7dff; }
.type-stb { background: rgba(103,194,58,0.15); color: #5da432; }
.exp-date { font-size: 10px; opacity: 0.6; }
.exp-label { font-size: 13px; font-weight: 600; margin: 6px 0 2px; }
.exp-sims { font-size: 11px; opacity: 0.65; margin: 0; }
.empty-hint { font-size: 12px; opacity: 0.6; }
.exp-detail { border: 1px solid rgba(128,128,128,0.2); border-radius: 12px; padding: 20px; min-height: 400px; }
.empty-detail { opacity: 0.5; text-align: center; padding: 80px 0; }
.detail-meta { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
.meta-chip { font-size: 10px; padding: 2px 8px; border-radius: 10px; background: rgba(128,128,128,0.12); }
.meta-chip.mono { font-family: monospace; }
.chip-ok { background: rgba(103,194,58,0.15); color: #5da432; }
.chip-warn { background: rgba(230,162,60,0.18); color: #b8863b; }
.md-content :deep(table) { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 13px; }
.md-content :deep(th), .md-content :deep(td) { border: 1px solid rgba(128,128,128,0.25); padding: 6px 10px; text-align: left; }
.md-content :deep(th) { background: rgba(74,125,255,0.08); }
.md-content :deep(blockquote) { border-left: 3px solid rgba(74,125,255,0.5); margin: 8px 0; padding: 4px 12px; opacity: 0.85; }
.md-content :deep(h2) { margin: 18px 0 8px; }
.md-content :deep(h3) { margin: 14px 0 6px; }
.md-content :deep(p) { margin: 6px 0; line-height: 1.55; font-size: 13.5px; }
.md-content :deep(li) { margin: 3px 0 3px 18px; font-size: 13.5px; }
</style>
