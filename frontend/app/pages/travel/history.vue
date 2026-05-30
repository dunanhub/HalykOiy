<script setup lang="ts">
import { mdiArrowLeft, mdiPlus, mdiAirplane, mdiDeleteOutline } from '@mdi/js'
import type { HistoryEntry } from '~/composables/useTravel'

const router = useRouter()
const { currentPlan, planHistory, loadHistory, formatPrice } = useTravel()

onMounted(() => {
  loadHistory()
})

const openPlan = (entry: HistoryEntry) => {
  currentPlan.value = entry.plan
  router.push('/travel/plan')
}

const relativeDate = (iso: string): string => {
  const d = new Date(iso)
  const now = new Date()
  const diff = Math.floor((now.getTime() - d.getTime()) / 86_400_000)
  if (diff === 0) return 'Сегодня'
  if (diff === 1) return 'Вчера'
  if (diff < 7) return `${diff} дня назад`
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

const typeLabel = (entry: HistoryEntry): string => {
  const type = entry.plan.trip.type
  if (type === 'family_weekend') return 'Семейная'
  if (type === 'business') return 'Бизнес'
  return 'Поездка'
}
</script>

<template>
  <main class="travel-screen">
    <div class="travel-shell flex flex-col">
      <header class="travel-topbar fade-slide">
        <button
          class="pressable absolute left-0 flex h-9 w-9 items-center justify-center rounded-full bg-white/70 shadow-sm"
          @click="router.back()"
        >
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiArrowLeft" fill="currentColor" />
          </svg>
        </button>
        <h1 class="text-[18px] font-semibold">История поездок</h1>
      </header>

      <!-- Empty state -->
      <div
        v-if="!planHistory.length"
        class="fade-slide mt-12 flex flex-1 flex-col items-center gap-3 text-center"
      >
        <div class="flex h-16 w-16 items-center justify-center rounded-full bg-white shadow-sm">
          <svg viewBox="0 0 24 24" class="h-8 w-8 text-[#9aa3b5]">
            <path :d="mdiAirplane" fill="currentColor" />
          </svg>
        </div>
        <p class="text-[16px] font-semibold text-[#202436]">Нет сохранённых поездок</p>
        <p class="text-[14px] text-[#9aa3b5]">Создайте свой первый план путешествия</p>
      </div>

      <!-- History list -->
      <section v-else class="stagger mt-5 space-y-3">
        <button
          v-for="entry in planHistory"
          :key="entry.plan_id"
          class="travel-card pressable w-full p-4 text-left"
          @click="openPlan(entry)"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span
                  class="rounded-full bg-[#eaf8f1] px-2 py-0.5 text-[11px] font-semibold text-[#009b63]"
                >
                  {{ typeLabel(entry) }}
                </span>
              </div>
              <h2 class="mt-1.5 text-[16px] font-bold leading-tight">
                {{ entry.title }}
              </h2>
              <p class="mt-1 text-[13px] leading-5 text-[#6b7280]">
                {{ entry.description }}
              </p>
              <p class="mt-1.5 text-[14px] font-semibold text-[#202436]">
                {{ formatPrice(entry.total) }}
              </p>
            </div>
            <span class="shrink-0 text-[12px] text-[#9aa3b5]">
              {{ relativeDate(entry.saved_at) }}
            </span>
          </div>
        </button>
      </section>

      <div class="travel-sticky-action mt-auto">
        <button
          class="travel-primary-button flex w-full items-center gap-3 p-4 text-left"
          @click="router.push('/travel')"
        >
          <span class="flex h-10 w-10 items-center justify-center rounded-full bg-white/20">
            <svg viewBox="0 0 24 24" class="h-6 w-6">
              <path :d="mdiPlus" fill="currentColor" />
            </svg>
          </span>
          <span>
            <span class="block text-[16px] font-bold">Новая поездка</span>
            <span class="block text-[13px] text-white/80">Начать новый запрос</span>
          </span>
        </button>
      </div>
    </div>
  </main>
</template>
