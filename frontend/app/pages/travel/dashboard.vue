<script setup lang="ts">
import {
  mdiArrowLeft,
  mdiWeatherPartlyCloudy,
  mdiAirplaneClock,
  mdiAccount,
  mdiCheckCircle,
  mdiCalendarMonth,
  mdiTextBoxCheckOutline,
  mdiCreditCardOutline,
  mdiMedicalBag,
  mdiTshirtCrew,
} from '@mdi/js'
import type { ItineraryDay } from '~/composables/useTravel'

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

const router = useRouter()
const config = useRuntimeConfig()
const { currentPlan, contactInfo, formatPrice, editPlan } = useTravel()

const weather = ref<Weather>({
  temp: null,
  description: 'Прогноз недоступен',
  source: 'fallback',
})

const selectedDay = ref(1)
const pickedDate = ref('')
const applyingDate = ref(false)

const tripTitle = computed(() => {
  if (!currentPlan.value) return 'Алматы → Астана'
  return `${currentPlan.value.trip.from} → ${currentPlan.value.trip.to}`
})

const flightItem = computed(() => currentPlan.value?.items.find(i => i.category === 'flight'))

const todayLabel = computed(() => {
  const d = new Date()
  const months = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']
  return `Сегодня: ${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`
})

const tripDateLine = computed(() => {
  const plan = currentPlan.value
  if (!plan) return ''
  const months = ['янв','фев','мар','апр','май','июн','июл','авг','сен','окт','ноя','дек']
  const parts: string[] = []
  const sd = plan.start_date
  if (sd) {
    const d = new Date(sd + 'T00:00:00')
    parts.push(`с ${d.getDate()} ${months[d.getMonth()]}`)
  } else if (plan.trip.dates) {
    parts.push(plan.trip.dates)
  }
  if (plan.trip.nights) parts.push(`${plan.trip.nights} ноч`)
  if (plan.trip.pax) parts.push(`${plan.trip.pax} чел`)
  return parts.join(' · ')
})

const itinerary = computed<ItineraryDay[]>(() => currentPlan.value?.itinerary || [])

const selectedDayObj = computed<ItineraryDay | null>(() =>
  itinerary.value.find(d => d.day === selectedDay.value) || null,
)

const FULL_MONTHS = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']
const FULL_DAYS = ['Воскресенье','Понедельник','Вторник','Среда','Четверг','Пятница','Суббота']
const SHORT_DAYS = ['Вс','Пн','Вт','Ср','Чт','Пт','Сб']

const monthYearLabel = computed(() => {
  const first = itinerary.value[0]
  if (!first?.date) return ''
  const d = new Date(first.date + 'T00:00:00')
  return `${FULL_MONTHS[d.getMonth()]} ${d.getFullYear()}`
})

const weekdayShort = (dateStr: string | null) => {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  return SHORT_DAYS[d.getDay()]
}

const dayNumber = (dateStr: string | null, fallback: number) => {
  if (!dateStr) return fallback.toString()
  return new Date(dateStr + 'T00:00:00').getDate().toString()
}

const longDateLabel = (dateStr: string | null): string => {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  return `${FULL_DAYS[d.getDay()]}, ${d.getDate()} ${FULL_MONTHS[d.getMonth()]}`
}

const isToday = (dateStr: string | null): boolean => {
  if (!dateStr) return false
  return dateStr === new Date().toISOString().split('T')[0]
}

const applyDate = async () => {
  if (!pickedDate.value) return
  applyingDate.value = true
  try {
    const d = new Date(pickedDate.value + 'T00:00:00')
    const months = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']
    await editPlan(`дата поездки ${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`)
    pickedDate.value = ''
  } finally {
    applyingDate.value = false
  }
}

// --- What to prepare ---
type PrepareCategory = { icon: string; title: string; items: string[] }
const prepareCategories = computed<PrepareCategory[]>(() => {
  const plan = currentPlan.value
  const hasKids = (plan?.checklist || []).some(
    (g: any) => (g.person || '').toLowerCase().includes('ребён') || (g.person || '').toLowerCase().includes('ребен')
  )
  return [
    {
      icon: '📄',
      title: 'Документы',
      items: ['Удостоверение личности или паспорт', 'Распечатанные / скаченные билеты', 'Страховой полис'],
    },
    {
      icon: '💳',
      title: 'Деньги',
      items: [
        'Карта Halyk',
        plan ? `Бонусов на поездку: ${formatPrice(plan.bonus)}` : 'Бонусы Halyk',
        'Небольшой запас наличных',
      ],
    },
    {
      icon: '👕',
      title: 'Вещи',
      items: [
        'Одежда по прогнозу погоды',
        'Удобная обувь',
        weather.value.temp !== null && weather.value.temp < 15 ? 'Тёплая куртка (прохладно)' : 'Лёгкая одежда',
      ],
    },
    {
      icon: '💊',
      title: 'Здоровье',
      items: hasKids
        ? ['Аптечка для детей (включена в план)', 'Жаропонижающее', 'Антисептик и пластыри']
        : ['Аптечка (включена в план)', 'Личные лекарства', 'Солнцезащитный крем'],
    },
  ]
})

const checklist = ref<ChecklistGroup[]>([])

const hydrateChecklist = () => {
  const groups = (currentPlan.value?.checklist || []) as Array<{
    member?: string
    role?: string
    items?: Array<{ item?: string; title?: string; checked?: boolean }>
  }>
  const userName = contactInfo.value?.name?.trim()
  checklist.value = groups.map((group, idx) => {
    let person = group.member || 'Пассажир'
    // First adult slot — show user's name from contact info, else "Я" for solo
    const isPrimaryAdult = idx === 0 && (group.role === 'взрослый' || person === 'Я' || person === 'Взрослый')
    if (userName && isPrimaryAdult) {
      person = userName
    }
    return {
      person,
      items: (group.items || []).map(item => ({
        title: item.title || item.item || 'Пункт чеклиста',
        checked: Boolean(item.checked),
      })),
    }
  })
}

const loadWeather = async () => {
  const city = currentPlan.value?.trip.to
  if (!city) return
  try {
    weather.value = await $fetch<Weather>(`${config.public.apiBase}/api/travel/weather`, {
      query: { city },
    })
  } catch {
    // keep fallback
  }
}

const totalItems = computed(() => checklist.value.reduce((s, g) => s + g.items.length, 0))
const checkedItems = computed(() => checklist.value.reduce((s, g) => s + g.items.filter(i => i.checked).length, 0))
const progress = computed(() => totalItems.value ? Math.round((checkedItems.value / totalItems.value) * 100) : 0)

onMounted(async () => {
  if (!currentPlan.value) {
    router.push('/travel')
    return
  }
  hydrateChecklist()
  await loadWeather()

  // Auto-select today's day if in trip, otherwise Day 1
  const today = new Date().toISOString().split('T')[0]
  const todayDay = itinerary.value.find(d => d.date === today)
  selectedDay.value = todayDay?.day ?? 1
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
        <p class="text-[13px] font-semibold text-[#009b63]">{{ todayLabel }}</p>
        <h2 class="mt-2 text-[25px] font-bold leading-tight">{{ tripTitle }}</h2>
        <p class="mt-2 text-[14px] text-[#6b7280]">{{ tripDateLine }}</p>
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

      <!-- Date picker (shown only when start_date is missing) -->
      <section
        v-if="!currentPlan?.start_date"
        class="mt-5 rounded-[28px] bg-white p-5 shadow-sm"
      >
        <h2 class="text-[17px] font-bold">Когда едем?</h2>
        <p class="mt-1 text-[13px] text-[#9aa3b5]">Укажите дату для расписания по дням</p>
        <input
          v-model="pickedDate"
          type="date"
          class="mt-3 w-full rounded-xl bg-[#f4f6fb] px-4 py-3 text-[15px] outline-none"
        >
        <button
          class="mt-3 w-full rounded-2xl bg-[#009b63] py-3 text-[15px] font-semibold text-white disabled:opacity-50"
          :disabled="!pickedDate || applyingDate"
          @click="applyDate"
        >
          {{ applyingDate ? 'Обновляю...' : 'Обновить план' }}
        </button>
      </section>

      <!-- Calendar view (when itinerary exists) -->
      <section
        v-if="itinerary.length"
        class="mt-5 rounded-[28px] bg-white p-5 shadow-sm"
      >
        <div class="mb-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-[#009b63]">
              <path :d="mdiCalendarMonth" fill="currentColor" />
            </svg>
            <h2 class="text-[18px] font-bold">Календарь поездки</h2>
          </div>
          <span class="rounded-full bg-[#eaf8f1] px-3 py-1 text-[12px] font-semibold text-[#009b63]">
            {{ itinerary.length }} дн
          </span>
        </div>

        <p class="mb-3 text-center text-[13px] font-semibold capitalize text-[#6b7280]">
          {{ monthYearLabel }}
        </p>

        <!-- Horizontal date strip -->
        <div class="-mx-5 overflow-x-auto px-5">
          <div class="flex gap-2 pb-1">
            <button
              v-for="day in itinerary"
              :key="day.day"
              class="relative flex min-w-[64px] shrink-0 flex-col items-center gap-0.5 rounded-2xl px-3 py-3 transition-colors"
              :class="day.day === selectedDay
                ? 'bg-[#009b63] text-white shadow-md'
                : 'bg-[#f4f6fb] text-[#202436] hover:bg-[#e9edf5]'"
              @click="selectedDay = day.day"
            >
              <span
                v-if="isToday(day.date)"
                class="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-[#ffd700]"
              />
              <span class="text-[10px] font-bold uppercase opacity-70">
                {{ weekdayShort(day.date) || 'дн' }}
              </span>
              <span class="text-[20px] font-bold leading-tight">
                {{ dayNumber(day.date, day.day) }}
              </span>
              <span
                v-if="day.weather?.temp !== null && day.weather?.temp !== undefined"
                class="text-[11px] opacity-80"
              >{{ day.weather?.temp }}°</span>
              <span v-else class="text-[11px] opacity-40">·</span>
            </button>
          </div>
        </div>

        <!-- Selected day content -->
        <div v-if="selectedDayObj" class="mt-4 rounded-2xl bg-[#f4f6fb] p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <p class="text-[11px] font-bold uppercase tracking-wide text-[#009b63]">
                {{ selectedDayObj.title }}
              </p>
              <h3 class="mt-1 text-[16px] font-bold text-[#202436]">
                {{ longDateLabel(selectedDayObj.date) || `День ${selectedDayObj.day}` }}
              </h3>
            </div>
            <div
              v-if="selectedDayObj.weather && selectedDayObj.weather.temp !== null"
              class="shrink-0 text-right"
            >
              <p class="text-[20px] font-bold leading-tight">{{ selectedDayObj.weather.temp }}°</p>
              <p class="text-[11px] text-[#6b7280]">{{ selectedDayObj.weather.description }}</p>
            </div>
          </div>

          <div class="mt-4 space-y-2">
            <div
              v-for="(item, idx) in selectedDayObj.items"
              :key="idx"
              class="flex items-start gap-3 rounded-xl bg-white px-3 py-3"
            >
              <span class="mt-0.5 text-[20px] leading-none">{{ item.icon }}</span>
              <div class="min-w-0 flex-1">
                <p class="text-[14px] font-semibold text-[#202436]">{{ item.title }}</p>
                <p v-if="item.details" class="mt-0.5 text-[12px] text-[#6b7280]">{{ item.details }}</p>
              </div>
            </div>
            <div
              v-if="!selectedDayObj.items.length"
              class="rounded-xl bg-white px-3 py-4 text-center text-[13px] text-[#9aa3b5]"
            >
              Свободный день
            </div>
          </div>
        </div>
      </section>

      <!-- Simple timeline fallback (when no itinerary) -->
      <section
        v-else
        class="mt-5 rounded-[28px] bg-white p-5 shadow-sm"
      >
        <div class="mb-4 flex items-center gap-2">
          <svg viewBox="0 0 24 24" class="h-5 w-5 text-[#009b63]">
            <path :d="mdiCalendarMonth" fill="currentColor" />
          </svg>
          <h2 class="text-[18px] font-bold">Расписание поездки</h2>
        </div>
        <div class="space-y-3">
          <div class="flex items-center gap-3 rounded-2xl bg-[#f4f6fb] px-4 py-3">
            <span class="text-[20px]">✈️</span>
            <div>
              <p class="text-[14px] font-semibold">День 1 — Вылет из {{ currentPlan?.trip.from }}</p>
              <p class="text-[12px] text-[#9aa3b5]">{{ currentPlan?.trip.dates }}</p>
            </div>
          </div>
          <div
            v-for="n in Math.max(1, (currentPlan?.trip.nights || 1) - 1)"
            :key="n"
            class="flex items-center gap-3 rounded-2xl bg-[#f4f6fb] px-4 py-3"
          >
            <span class="text-[20px]">🏨</span>
            <p class="text-[14px] font-semibold">День {{ n + 1 }} — в {{ currentPlan?.trip.to }}</p>
          </div>
          <div class="flex items-center gap-3 rounded-2xl bg-[#f4f6fb] px-4 py-3">
            <span class="text-[20px]">🏠</span>
            <p class="text-[14px] font-semibold">
              День {{ (currentPlan?.trip.nights || 1) + 1 }} — Возвращение
            </p>
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

      <!-- Checklist (only when populated) -->
      <template v-if="checklist.length">
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
              <input v-model="item.checked" type="checkbox" class="h-5 w-5 accent-[#009b63]">
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
      </template>

      <button
        class="mt-6 w-full rounded-2xl bg-[#009b63] py-4 text-[15px] font-semibold text-white shadow-sm"
        @click="router.push('/travel/next')"
      >
        Завершить поездку
      </button>
    </div>
  </main>
</template>
