<script setup lang="ts">
import {
  mdiArrowLeft,
  mdiWeatherPartlyCloudy,
  mdiAirplaneClock,
  mdiAccount,
  mdiCheckCircle,
  mdiCalendarMonth,
  mdiAirplane,
  mdiBed,
  mdiMapMarker,
  mdiHomeCity,
  mdiTextBoxCheckOutline,
  mdiCreditCardOutline,
  mdiMedicalBag,
  mdiTshirtCrew,
} from '@mdi/js'

type ChecklistItem = {
  title: string
  checked: boolean
}

type ChecklistGroup = {
  person: string
  items: ChecklistItem[]
}

type Weather = {
  temp: number | null
  description: string
  source: string
}

type CalendarDay = {
  label: string
  sublabel: string
  icon: string
  mdiIcon: string
  highlight: boolean
}

type PrepareCategory = {
  icon: string
  mdiIcon: string
  title: string
  items: string[]
}

const router = useRouter()
const config = useRuntimeConfig()
const { currentPlan, formatPrice } = useTravel()

const weather = ref<Weather>({
  temp: null,
  description: 'Прогноз недоступен',
  source: 'fallback',
})

const tripTitle = computed(() => {
  if (!currentPlan.value) return 'Алматы → Астана'
  return `${currentPlan.value.trip.from} → ${currentPlan.value.trip.to}`
})

const flightItem = computed(() => {
  return currentPlan.value?.items.find(item => item.category === 'flight')
})

const hotelItem = computed(() => {
  return currentPlan.value?.items.find(item => item.category === 'hotel')
})

// --- Calendar ---
const calendarDays = computed<CalendarDay[]>(() => {
  if (!currentPlan.value) return []
  const { from, to, nights } = currentPlan.value.trip
  const days: CalendarDay[] = []

  days.push({
    label: 'Сегодня',
    sublabel: 'Финальная подготовка',
    icon: '🎒',
    mdiIcon: mdiTextBoxCheckOutline,
    highlight: false,
  })

  days.push({
    label: 'День 1',
    sublabel: `Вылет из ${from}`,
    icon: '✈️',
    mdiIcon: mdiAirplane,
    highlight: true,
  })

  const stayNights = Math.max(1, nights - 1)
  for (let i = 1; i <= stayNights; i++) {
    days.push({
      label: `День ${i + 1}`,
      sublabel: `В ${to}`,
      icon: '🏨',
      mdiIcon: mdiBed,
      highlight: false,
    })
  }

  days.push({
    label: `День ${nights + 1}`,
    sublabel: `Возвращение в ${from}`,
    icon: '🏠',
    mdiIcon: mdiHomeCity,
    highlight: false,
  })

  return days
})

// --- What to prepare ---
const prepareCategories = computed<PrepareCategory[]>(() => {
  const plan = currentPlan.value
  const tripType = plan?.trip.type
  const hasKids = (plan?.checklist || []).some(
    (g: any) => (g.person || '').toLowerCase().includes('ребён') || (g.person || '').toLowerCase().includes('ребен')
  )

  const cats: PrepareCategory[] = [
    {
      icon: '📄',
      mdiIcon: mdiTextBoxCheckOutline,
      title: 'Документы',
      items: [
        'Удостоверение личности или паспорт',
        'Распечатанные / скаченные билеты',
        'Страховой полис',
      ],
    },
    {
      icon: '💳',
      mdiIcon: mdiCreditCardOutline,
      title: 'Деньги',
      items: [
        'Карта Halyk',
        plan ? `Бонусов на поездку: ${formatPrice(plan.bonus)}` : 'Бонусы Halyk',
        'Небольшой запас наличных',
      ],
    },
    {
      icon: '👕',
      mdiIcon: mdiTshirtCrew,
      title: 'Вещи',
      items: [
        'Одежда по прогнозу погоды',
        'Удобная обувь',
        weather.value.temp !== null && weather.value.temp < 15 ? 'Тёплая куртка (прохладно)' : 'Лёгкая одежда',
      ],
    },
    {
      icon: '💊',
      mdiIcon: mdiMedicalBag,
      title: 'Здоровье',
      items: hasKids
        ? ['Аптечка для детей (включена в план)', 'Жаропонижающее', 'Антисептик и пластыри']
        : ['Аптечка (включена в план)', 'Личные лекарства', 'Солнцезащитный крем'],
    },
  ]

  return cats
})

const checklist = ref<ChecklistGroup[]>([])

const hydrateChecklist = () => {
  const groups = (currentPlan.value?.checklist || []) as Array<{
    member?: string
    items?: Array<{ item?: string; title?: string; checked?: boolean }>
  }>

  checklist.value = groups.map(group => ({
    person: group.member || 'Пассажир',
    items: (group.items || []).map(item => ({
      title: item.title || item.item || 'Пункт чеклиста',
      checked: Boolean(item.checked),
    })),
  }))
}

const loadWeather = async () => {
  const city = currentPlan.value?.trip.to
  if (!city) return

  try {
    weather.value = await $fetch<Weather>(`${config.public.apiBase}/api/travel/weather`, {
      query: { city },
    })
  } catch (error) {
    console.warn('Weather fallback on frontend', error)
  }
}

const totalItems = computed(() => {
  return checklist.value.reduce((sum, group) => sum + group.items.length, 0)
})

const checkedItems = computed(() => {
  return checklist.value.reduce((sum, group) => {
    return sum + group.items.filter(item => item.checked).length
  }, 0)
})

const progress = computed(() => {
  if (!totalItems.value) return 0
  return Math.round((checkedItems.value / totalItems.value) * 100)
})

onMounted(async () => {
  if (!currentPlan.value) {
    router.push('/travel')
    return
  }

  hydrateChecklist()
  await loadWeather()
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
        <h1 class="text-[18px] font-semibold">Travel Dashboard</h1>
      </header>

      <!-- Trip header -->
      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <p class="text-[13px] font-semibold text-[#009b63]">Завтра</p>
        <h2 class="mt-2 text-[25px] font-bold leading-tight">{{ tripTitle }}</h2>
        <p class="mt-3 text-[14px] text-[#6b7280]">
          Суббота · вылет в 14:40 · выезд из дома в 12:30
        </p>
      </section>

      <!-- Weather + Flight status -->
      <section class="mt-5 grid grid-cols-2 gap-3">
        <div class="rounded-[24px] bg-white p-4 shadow-sm">
          <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#edf3f2]">
            <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
              <path :d="mdiWeatherPartlyCloudy" fill="currentColor" />
            </svg>
          </div>
          <p class="mt-3 text-[13px] text-[#6b7280]">Погода в {{ currentPlan?.trip.to || 'городе' }}</p>
          <p class="mt-1 text-[18px] font-bold">{{ weather.temp === null ? '—' : `${weather.temp}°C` }}</p>
          <p class="mt-1 text-[12px] text-[#9aa3b5]">{{ weather.description }}</p>
        </div>

        <div class="rounded-[24px] bg-white p-4 shadow-sm">
          <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#edf3f2]">
            <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
              <path :d="mdiAirplaneClock" fill="currentColor" />
            </svg>
          </div>
          <p class="mt-3 text-[13px] text-[#6b7280]">Статус рейса</p>
          <p class="mt-1 text-[18px] font-bold">По расписанию</p>
          <p class="mt-1 text-[12px] text-[#9aa3b5]">{{ flightItem?.title || 'Рейс' }}</p>
        </div>
      </section>

      <!-- Trip calendar timeline -->
      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <div class="mb-4 flex items-center gap-2">
          <svg viewBox="0 0 24 24" class="h-5 w-5 text-[#009b63]">
            <path :d="mdiCalendarMonth" fill="currentColor" />
          </svg>
          <h2 class="text-[18px] font-bold">Расписание поездки</h2>
        </div>

        <div class="relative">
          <!-- vertical line -->
          <div class="absolute left-[19px] top-2 bottom-2 w-0.5 bg-[#e5e7eb]" />

          <div class="space-y-4">
            <div
              v-for="(day, i) in calendarDays"
              :key="i"
              class="relative flex items-start gap-4"
            >
              <!-- dot -->
              <div
                class="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[18px]"
                :class="day.highlight ? 'bg-[#009b63] shadow-md' : 'bg-[#f4f6fb]'"
              >
                {{ day.icon }}
              </div>

              <div
                class="flex-1 rounded-2xl px-4 py-3"
                :class="day.highlight ? 'bg-[#eaf8f1]' : 'bg-[#f4f6fb]'"
              >
                <p
                  class="text-[13px] font-bold"
                  :class="day.highlight ? 'text-[#009b63]' : 'text-[#6b7280]'"
                >
                  {{ day.label }}
                </p>
                <p class="text-[15px] font-semibold text-[#202436]">{{ day.sublabel }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- What to prepare -->
      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <h2 class="mb-4 text-[18px] font-bold">Что взять с собой</h2>

        <div class="space-y-3">
          <div
            v-for="cat in prepareCategories"
            :key="cat.title"
            class="rounded-2xl bg-[#f4f6fb] p-4"
          >
            <div class="mb-2 flex items-center gap-2">
              <span class="text-[18px]">{{ cat.icon }}</span>
              <p class="text-[15px] font-bold text-[#202436]">{{ cat.title }}</p>
            </div>
            <ul class="space-y-1">
              <li
                v-for="item in cat.items"
                :key="item"
                class="flex items-start gap-2 text-[13px] text-[#6b7280]"
              >
                <span class="mt-0.5 text-[#009b63]">·</span>
                {{ item }}
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Checklist progress -->
      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <div class="flex items-center justify-between">
          <h2 class="text-[18px] font-bold">Чеклист</h2>
          <span class="text-[13px] font-semibold text-[#009b63]">{{ checkedItems }} из {{ totalItems }}</span>
        </div>

        <div class="mt-4 h-2 rounded-full bg-[#e5e7eb]">
          <div
            class="h-2 rounded-full bg-[#009b63] transition-all"
            :style="{ width: progress + '%' }"
          />
        </div>

        <p class="mt-2 text-[13px] text-[#6b7280]">Готовность: {{ progress }}%</p>
      </section>

      <!-- Checklist groups -->
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
            <h3 class="text-[17px] font-bold">{{ group.person }}</h3>
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
            <svg v-if="item.checked" viewBox="0 0 24 24" class="h-5 w-5 text-[#009b63]">
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
