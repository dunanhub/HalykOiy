<script setup lang="ts">
import {
  mdiArrowLeft,
  mdiWeatherPartlyCloudy,
  mdiAirplaneClock,
  mdiAccount,
  mdiCheckCircle
} from '@mdi/js'

const router = useRouter()
const { currentPlan } = useTravel()

const tripTitle = computed(() => {
  if (!currentPlan.value) return 'Алматы → Астана'

  return `${currentPlan.value.trip.from} → ${currentPlan.value.trip.to}`
})

const flightItem = computed(() => {
  return currentPlan.value?.items.find(item => item.category === 'flight')
})

const checklist = ref([
  {
    person: 'Папа',
    items: [
      { title: 'Паспорт / удостоверение', checked: false },
      { title: 'Телефон + зарядка', checked: false },
      { title: 'Банковская карта Halyk', checked: true }
    ]
  },
  {
    person: 'Мама',
    items: [
      { title: 'Паспорт / удостоверение', checked: false },
      { title: 'Телефон + зарядка', checked: false },
      { title: 'Билеты в приложении Halyk', checked: true }
    ]
  },
  {
    person: 'Аня, 8 лет',
    items: [
      { title: 'Свидетельство о рождении', checked: false },
      { title: 'Детское жаропонижающее', checked: false },
      { title: 'Любимая игрушка', checked: true }
    ]
  },
  {
    person: 'Коля, 5 лет',
    items: [
      { title: 'Свидетельство о рождении', checked: false },
      { title: 'Подгузники запас', checked: false },
      { title: 'Планшет заряжен', checked: false }
    ]
  }
])

const totalItems = computed(() => {
  return checklist.value.reduce((sum, group) => sum + group.items.length, 0)
})

const checkedItems = computed(() => {
  return checklist.value.reduce((sum, group) => {
    return sum + group.items.filter(item => item.checked).length
  }, 0)
})

const progress = computed(() => {
  return Math.round((checkedItems.value / totalItems.value) * 100)
})
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
          Travel Dashboard
        </h1>
      </header>

      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <p class="text-[13px] font-semibold text-[#009b63]">
          Завтра
        </p>

        <h2 class="mt-2 text-[25px] font-bold leading-tight">
          {{ tripTitle }}
        </h2>

        <p class="mt-3 text-[14px] text-[#6b7280]">
          Суббота · вылет в 14:40 · выезд из дома в 12:30
        </p>
      </section>

      <section class="mt-5 grid grid-cols-2 gap-3">
        <div class="rounded-[24px] bg-white p-4 shadow-sm">
          <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#edf3f2]">
            <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
              <path :d="mdiWeatherPartlyCloudy" fill="currentColor" />
            </svg>
          </div>

          <p class="mt-3 text-[13px] text-[#6b7280]">
            Погода в Астане
          </p>

          <p class="mt-1 text-[18px] font-bold">
            +18°C
          </p>

          <p class="mt-1 text-[12px] text-[#9aa3b5]">
            Переменная облачность
          </p>
        </div>

        <div class="rounded-[24px] bg-white p-4 shadow-sm">
          <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#edf3f2]">
            <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
              <path :d="mdiAirplaneClock" fill="currentColor" />
            </svg>
          </div>

          <p class="mt-3 text-[13px] text-[#6b7280]">
            Статус рейса
          </p>

          <p class="mt-1 text-[18px] font-bold">
            По расписанию
          </p>

          <p class="mt-1 text-[12px] text-[#9aa3b5]">
            {{ flightItem?.title || 'FlyArystan' }} KC-123
          </p>
        </div>
      </section>

      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <div class="flex items-center justify-between">
          <h2 class="text-[18px] font-bold">
            Чеклист
          </h2>

          <span class="text-[13px] font-semibold text-[#009b63]">
            {{ checkedItems }} из {{ totalItems }}
          </span>
        </div>

        <div class="mt-4 h-2 rounded-full bg-[#e5e7eb]">
          <div
            class="h-2 rounded-full bg-[#009b63]"
            :style="{ width: progress + '%' }"
          />
        </div>

        <p class="mt-2 text-[13px] text-[#6b7280]">
          Готовность: {{ progress }}%
        </p>
      </section>

      <section class="mt-5 space-y-4">
        <div
          v-for="group in checklist"
          :key="group.person"
          class="rounded-[28px] bg-white p-5 shadow-sm"
        >
          <div class="mb-4 flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-full bg-[#edf3f2]">
              <svg viewBox="0 0 24 24" class="h-6 w-6 text-[#00845f]">
                <path :d="mdiAccount" fill="currentColor" />
              </svg>
            </div>

            <h3 class="text-[17px] font-bold">
              {{ group.person }}
            </h3>
          </div>

          <label
            v-for="item in group.items"
            :key="item.title"
            class="flex cursor-pointer items-center gap-3 border-t border-[#edf0f5] py-3 first:border-t-0"
          >
            <input
              v-model="item.checked"
              type="checkbox"
              class="h-5 w-5 accent-[#009b63]"
            >

            <span
              class="flex-1 text-[15px]"
              :class="item.checked ? 'text-[#9aa3b5] line-through' : 'text-[#202436]'"
            >
              {{ item.title }}
            </span>

            <svg
              v-if="item.checked"
              viewBox="0 0 24 24"
              class="h-5 w-5 text-[#009b63]"
            >
              <path :d="mdiCheckCircle" fill="currentColor" />
            </svg>
          </label>
        </div>
      </section>

      <button
        class="mt-6 w-full rounded-2xl bg-[#009b63] py-4 text-[15px] font-semibold text-white shadow-sm"
        @click="router.push('/travel/next')"
      >
        Завершить поездку
      </button>
    </div>
  </main>
</template>
