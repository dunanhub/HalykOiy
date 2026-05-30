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
  mdiAirplane,
  mdiBed,
  mdiHomeOutline,
  mdiInformationOutline,
  mdiMapMarkerPath,
  mdiAlertCircleOutline,
  mdiCheckBold,
  mdiGestureSwipeHorizontal,
  mdiHistory,
  mdiLockCheckOutline,
  mdiPlus,
  mdiChevronDoubleRight,
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
const {
  currentPlan,
  contactInfo,
  formatPrice,
  editPlan,
  activeTrip,
  completedTripIds,
  loadHistory,
  loadDashboardState,
  completeDashboardTrip,
  isTripExpired,
  planHistory,
} = useTravel()

const weather = ref<Weather>({
  temp: null,
  description: 'Прогноз недоступен',
  source: 'fallback',
})

const selectedDay = ref(1)
const pickedDate = ref('')
const applyingDate = ref(false)
const slideTrack = ref<HTMLElement | null>(null)
const slideProgress = ref(0)
const slideOffset = ref(0)
const slideDragging = ref(false)
const slideCompleted = ref(false)
const slideStartX = ref(0)
const slideMoved = ref(false)

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

type PrepareCategory = { icon: string; title: string; items: string[] }
const iconByItineraryType: Record<string, string> = {
  flight: mdiAirplane,
  hotel: mdiBed,
  transfer: mdiAirplaneClock,
  activity: mdiMapMarkerPath,
  pharmacy: mdiMedicalBag,
  restaurant: mdiTextBoxCheckOutline,
  return: mdiHomeOutline,
}

const prepareCategories = computed<PrepareCategory[]>(() => {
  const plan = currentPlan.value
  const hasKids = (plan?.checklist || []).some(
    (g: any) => (g.person || '').toLowerCase().includes('ребён') || (g.person || '').toLowerCase().includes('ребен')
  )
  return [
    {
      icon: mdiTextBoxCheckOutline,
      title: 'Документы',
      items: ['Удостоверение личности или паспорт', 'Распечатанные / скаченные билеты', 'Страховой полис'],
    },
    {
      icon: mdiCreditCardOutline,
      title: 'Деньги',
      items: [
        'Карта Halyk',
        plan ? `Бонусов на поездку: ${formatPrice(plan.bonus)}` : 'Бонусы Halyk',
        'Небольшой запас наличных',
      ],
    },
    {
      icon: mdiTshirtCrew,
      title: 'Вещи',
      items: [
        'Одежда по прогнозу погоды',
        'Удобная обувь',
        weather.value.temp !== null && weather.value.temp < 15 ? 'Тёплая куртка (прохладно)' : 'Лёгкая одежда',
      ],
    },
    {
      icon: mdiMedicalBag,
      title: 'Здоровье',
      items: hasKids
        ? ['Аптечка для детей (включена в план)', 'Жаропонижающее', 'Антисептик и пластыри']
        : ['Аптечка (включена в план)', 'Личные лекарства', 'Солнцезащитный крем'],
    },
  ]
})

const checklist = ref<ChecklistGroup[]>([])
const checklistHydrated = ref(false)

const checklistStorageKey = computed(() => {
  const planId = currentPlan.value?.plan_id
  return planId ? `halyk:dashboard-checklist:${planId}` : ''
})

const checklistItemKey = (groupIndex: number, itemTitle: string) => `${groupIndex}:${itemTitle}`

const loadSavedChecklist = (): Record<string, boolean> => {
  if (!process.client || !checklistStorageKey.value) return {}
  try {
    return JSON.parse(localStorage.getItem(checklistStorageKey.value) || '{}')
  } catch {
    return {}
  }
}

const saveChecklist = () => {
  if (!process.client || !checklistStorageKey.value || !checklistHydrated.value) return
  const saved = checklist.value.reduce<Record<string, boolean>>((acc, group, groupIndex) => {
    group.items.forEach((item) => {
      acc[checklistItemKey(groupIndex, item.title)] = item.checked
    })
    return acc
  }, {})
  localStorage.setItem(checklistStorageKey.value, JSON.stringify(saved))
}

const hydrateChecklist = () => {
  checklistHydrated.value = false
  const saved = loadSavedChecklist()
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
      items: (group.items || []).map((item) => {
        const title = item.title || item.item || 'Пункт чеклиста'
        const savedKey = checklistItemKey(idx, title)
        return {
          title,
          checked: savedKey in saved ? saved[savedKey] : Boolean(item.checked),
        }
      }),
    }
  })
  checklistHydrated.value = true
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
const isCompleted = computed(() => Boolean(currentPlan.value?.plan_id && completedTripIds.value.includes(currentPlan.value.plan_id)))
const expired = computed(() => isTripExpired(currentPlan.value))
const dashboardBlocked = computed(() => isCompleted.value || expired.value)
const blockedTitle = computed(() => {
  if (isCompleted.value) return 'Поездка уже завершена'
  return 'Поездка уже завершилась или дата прошла'
})
const blockedText = computed(() => {
  if (isCompleted.value) return 'Вы завершили этот dashboard. План можно посмотреть в истории или начать новую поездку.'
  return 'Активный режим dashboard недоступен, потому что дата поездки уже прошла.'
})

const updateSlideProgress = (clientX: number) => {
  const rect = slideTrack.value?.getBoundingClientRect()
  if (!rect) return
  const knob = 56
  const max = Math.max(1, rect.width - knob)
  const nextOffset = Math.max(0, Math.min(max, clientX - rect.left - knob / 2))
  slideOffset.value = nextOffset
  slideProgress.value = (nextOffset / max) * 100
}

const startSlide = (event: PointerEvent) => {
  if (dashboardBlocked.value || slideCompleted.value) return
  slideDragging.value = true
  slideStartX.value = event.clientX
  slideMoved.value = false
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

const moveSlide = (event: PointerEvent) => {
  if (!slideDragging.value) return
  if (Math.abs(event.clientX - slideStartX.value) > 4) slideMoved.value = true
  updateSlideProgress(event.clientX)
}

const endSlide = () => {
  if (!slideDragging.value) return
  slideDragging.value = false

  if (slideMoved.value && slideProgress.value >= 85 && currentPlan.value) {
    const rect = slideTrack.value?.getBoundingClientRect()
    if (rect) slideOffset.value = Math.max(0, rect.width - 56)
    slideProgress.value = 100
    slideCompleted.value = true
    completeDashboardTrip(currentPlan.value.plan_id)
    window.setTimeout(() => router.push('/travel/next'), 420)
    return
  }

  slideProgress.value = 0
  slideOffset.value = 0
}

onMounted(async () => {
  loadDashboardState()
  loadHistory()

  if (!currentPlan.value && activeTrip.value) {
    const activeEntry = planHistory.value.find(entry => entry.plan_id === activeTrip.value)
    currentPlan.value = activeEntry?.plan || null
  }

  if (!currentPlan.value) {
    router.push('/travel')
    return
  }

  if (activeTrip.value !== currentPlan.value.plan_id && !completedTripIds.value.includes(currentPlan.value.plan_id)) {
    router.push('/travel/payment')
    return
  }

  hydrateChecklist()
  await loadWeather()

  // Auto-select today's day if in trip, otherwise Day 1
  const today = new Date().toISOString().split('T')[0]
  const todayDay = itinerary.value.find(d => d.date === today)
  selectedDay.value = todayDay?.day ?? 1
})

watch(checklist, saveChecklist, { deep: true })
</script>

<template>
  <main class="travel-screen">
    <div class="travel-shell">
      <header class="travel-topbar fade-slide">
        <button
          class="pressable absolute left-0 flex h-9 w-9 items-center justify-center rounded-full bg-white/70 shadow-sm"
          @click="router.back()"
        >
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiArrowLeft" fill="currentColor" />
          </svg>
        </button>
        <h1 class="text-[18px] font-semibold">Travel Dashboard</h1>
      </header>

      <!-- Trip header -->
      <section class="travel-card travel-hero mt-5 p-5">
        <p class="text-[13px] font-semibold text-[#009b63]">{{ todayLabel }}</p>
        <h2 class="mt-2 text-[25px] font-bold leading-tight">{{ tripTitle }}</h2>
        <p class="mt-2 text-[14px] text-[#6b7280]">{{ tripDateLine }}</p>
      </section>

      <section v-if="dashboardBlocked" class="travel-card mt-5 p-5 text-center">
        <div class="travel-icon-bubble mx-auto h-14 w-14">
          <svg viewBox="0 0 24 24" class="h-8 w-8">
            <path :d="isCompleted ? mdiLockCheckOutline : mdiAlertCircleOutline" fill="currentColor" />
          </svg>
        </div>
        <h2 class="mt-4 text-[22px] font-bold">{{ blockedTitle }}</h2>
        <p class="mt-2 text-[14px] leading-6 text-[#6b7280]">{{ blockedText }}</p>
        <div class="mt-5 grid grid-cols-2 gap-3">
          <button class="travel-secondary-button flex items-center justify-center gap-2 py-3 text-[14px]" @click="router.push('/travel/history')">
            <svg viewBox="0 0 24 24" class="h-5 w-5">
              <path :d="mdiHistory" fill="currentColor" />
            </svg>
            История
          </button>
          <button class="travel-primary-button flex items-center justify-center gap-2 py-3 text-[14px]" @click="router.push('/travel')">
            <svg viewBox="0 0 24 24" class="h-5 w-5">
              <path :d="mdiPlus" fill="currentColor" />
            </svg>
            Новая
          </button>
        </div>
      </section>

      <template v-else>

      <!-- Weather + Flight status -->
      <section class="mt-5 grid grid-cols-2 gap-3">
        <div class="travel-card p-4">
          <div class="travel-icon-bubble h-11 w-11">
            <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
              <path :d="mdiWeatherPartlyCloudy" fill="currentColor" />
            </svg>
          </div>
          <p class="mt-3 text-[13px] text-[#6b7280]">Погода в {{ currentPlan?.trip.to || 'городе' }}</p>
          <p class="mt-1 text-[18px] font-bold">{{ weather.temp === null ? '—' : `${weather.temp}°C` }}</p>
          <p class="mt-1 text-[12px] text-[#9aa3b5]">{{ weather.description }}</p>
        </div>

        <div class="travel-card p-4">
          <div class="travel-icon-bubble h-11 w-11">
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
          class="mt-5 travel-card p-5"
      >
        <h2 class="text-[17px] font-bold">Когда едем?</h2>
        <p class="mt-1 text-[13px] text-[#9aa3b5]">Укажите дату для расписания по дням</p>
        <input
          v-model="pickedDate"
          type="date"
          class="mt-3 w-full rounded-xl bg-[#f4f6fb] px-4 py-3 text-[15px] outline-none"
        >
        <button
          class="travel-primary-button mt-3 w-full py-3 text-[15px]"
          :disabled="!pickedDate || applyingDate"
          @click="applyDate"
        >
          {{ applyingDate ? 'Обновляю...' : 'Обновить план' }}
        </button>
      </section>

      <!-- Calendar view (when itinerary exists) -->
      <section
        v-if="itinerary.length"
          class="mt-5 travel-card p-5"
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
              class="pressable relative flex min-w-[64px] shrink-0 flex-col items-center gap-0.5 rounded-2xl px-3 py-3 transition-colors"
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
              class="pressable flex items-start gap-3 rounded-xl bg-white px-3 py-3"
            >
              <span class="travel-icon-bubble mt-0.5 h-9 w-9 shrink-0">
                <svg viewBox="0 0 24 24" class="h-5 w-5">
                  <path :d="iconByItineraryType[item.type] || mdiInformationOutline" fill="currentColor" />
                </svg>
              </span>
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
        class="mt-5 travel-card p-5"
      >
        <div class="mb-4 flex items-center gap-2">
          <svg viewBox="0 0 24 24" class="h-5 w-5 text-[#009b63]">
            <path :d="mdiCalendarMonth" fill="currentColor" />
          </svg>
          <h2 class="text-[18px] font-bold">Расписание поездки</h2>
        </div>
        <div class="space-y-3">
          <div class="flex items-center gap-3 rounded-2xl bg-[#f4f6fb] px-4 py-3">
            <span class="travel-icon-bubble h-9 w-9 shrink-0">
              <svg viewBox="0 0 24 24" class="h-5 w-5">
                <path :d="mdiAirplane" fill="currentColor" />
              </svg>
            </span>
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
            <span class="travel-icon-bubble h-9 w-9 shrink-0">
              <svg viewBox="0 0 24 24" class="h-5 w-5">
                <path :d="mdiBed" fill="currentColor" />
              </svg>
            </span>
            <p class="text-[14px] font-semibold">День {{ n + 1 }} — в {{ currentPlan?.trip.to }}</p>
          </div>
          <div class="flex items-center gap-3 rounded-2xl bg-[#f4f6fb] px-4 py-3">
            <span class="travel-icon-bubble h-9 w-9 shrink-0">
              <svg viewBox="0 0 24 24" class="h-5 w-5">
                <path :d="mdiHomeOutline" fill="currentColor" />
              </svg>
            </span>
            <p class="text-[14px] font-semibold">
              День {{ (currentPlan?.trip.nights || 1) + 1 }} — Возвращение
            </p>
          </div>
        </div>
      </section>

      <!-- What to prepare -->
      <section class="mt-5 travel-card p-5">
        <h2 class="mb-4 text-[18px] font-bold">Что взять с собой</h2>
        <div class="space-y-3">
          <div
            v-for="cat in prepareCategories"
            :key="cat.title"
            class="pressable rounded-2xl bg-[#f4f6fb] p-4"
          >
            <div class="mb-2 flex items-center gap-2">
              <span class="travel-icon-bubble h-9 w-9 shrink-0">
                <svg viewBox="0 0 24 24" class="h-5 w-5">
                  <path :d="cat.icon" fill="currentColor" />
                </svg>
              </span>
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
        <section class="mt-5 travel-card p-5">
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
            class="travel-card p-5"
          >
            <div class="mb-4 flex items-center gap-3">
              <div class="travel-icon-bubble h-10 w-10">
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

      <div class="travel-sticky-action mt-6">
        <div
          ref="slideTrack"
          class="relative h-[68px] touch-none overflow-hidden rounded-[26px] border border-[#cfe9de] bg-white p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_14px_32px_rgba(0,155,99,0.12)]"
          :class="slideDragging ? 'select-none' : ''"
          @pointerdown="startSlide"
          @pointermove="moveSlide"
          @pointerup="endSlide"
          @pointercancel="endSlide"
        >
          <div
            class="absolute inset-y-1 left-1 rounded-[22px] bg-gradient-to-r from-[#dff6eb] to-[#b9ecd7] transition-[width]"
            :style="{ width: `${slideProgress}%` }"
          />
          <div
            class="pointer-events-none absolute inset-y-2 left-20 w-16 rounded-full bg-white/45 blur-sm"
            :class="slideDragging ? 'opacity-0' : 'animate-pulse'"
          />
          <div class="pointer-events-none absolute inset-0 flex items-center justify-center px-[72px] text-center text-[13px] font-bold leading-5 text-[#00845f]">
            {{ slideCompleted ? 'Поездка завершается...' : 'Сдвиньте вправо, чтобы завершить' }}
          </div>
          <div
            class="absolute left-1 top-1 flex h-[60px] w-[60px] items-center justify-center rounded-[23px] bg-gradient-to-br from-[#00a86b] to-[#007a51] text-white shadow-[0_12px_24px_rgba(0,155,99,0.32)]"
            :class="slideDragging ? '' : 'transition-transform duration-300'"
            :style="{ transform: `translateX(${slideOffset}px)` }"
          >
            <svg viewBox="0 0 24 24" class="h-6 w-6">
              <path :d="slideCompleted ? mdiCheckBold : mdiChevronDoubleRight" fill="currentColor" />
            </svg>
          </div>
        </div>
      </div>
      </template>
    </div>
  </main>
</template>
