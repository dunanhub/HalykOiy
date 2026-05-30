<script setup lang="ts">
import { mdiArrowLeft, mdiPlus } from '@mdi/js'

const router = useRouter()
const { currentPlan, formatPrice } = useTravel()

const histories = computed(() => {
  const activeHistory = currentPlan.value
    ? {
        id: 1,
        title: `${currentPlan.value.trip.from} → ${currentPlan.value.trip.to}`,
        description: `Семейная поездка · ${currentPlan.value.trip.pax} человека · ${formatPrice(currentPlan.value.total)}`,
        date: 'Сегодня',
      }
    : {
        id: 1,
        title: 'Алматы → Астана',
        description: 'Семейная поездка · 4 человека · 125 500 ₸',
        date: 'Сегодня',
      }

  return [
    activeHistory,
    {
      id: 2,
      title: 'Алматы → Боровое',
      description: 'Природа · выходные · ~80 000 ₸',
      date: 'Вчера',
    },
  ]
})

const openHistory = () => {
  router.push('/travel/plan')
}
</script>

<template>
  <main class="min-h-screen bg-[#f4f6fb] text-[#202436]">
    <div class="mx-auto min-h-screen max-w-[430px] bg-[#f4f6fb] px-4 pb-8 pt-4">
      <header class="relative flex items-center justify-center py-3">
        <button
          class="absolute left-0 flex h-9 w-9 items-center justify-center"
          @click="router.back()"
        >
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiArrowLeft" fill="currentColor" />
          </svg>
        </button>

        <h1 class="text-[18px] font-semibold">
          История поездок
        </h1>
      </header>

      <button
        class="mt-5 flex w-full items-center gap-3 rounded-[24px] bg-[#009b63] p-4 text-left text-white shadow-sm"
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

      <section class="mt-5 space-y-3">
        <button
          v-for="item in histories"
          :key="item.id"
          class="w-full rounded-[24px] bg-white p-4 text-left shadow-sm"
          @click="openHistory"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <h2 class="text-[16px] font-bold">
                {{ item.title }}
              </h2>

              <p class="mt-1 text-[13px] leading-5 text-[#6b7280]">
                {{ item.description }}
              </p>
            </div>

            <span class="shrink-0 text-[12px] text-[#9aa3b5]">
              {{ item.date }}
            </span>
          </div>
        </button>
      </section>
    </div>
  </main>
</template>
