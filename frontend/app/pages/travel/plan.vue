<script setup lang="ts">
import {
  mdiArrowLeft,
  mdiAirplane,
  mdiBed,
  mdiChevronDown,
  mdiShieldCheck,
  mdiMedicalBag,
  mdiSilverwareForkKnife,
  mdiCar,
  mdiTicketConfirmation
} from '@mdi/js'
import type { TravelItem } from '~/composables/useTravel'

const router = useRouter()
const { currentPlan, formatPrice } = useTravel()

const expanded = ref<Record<string, boolean>>({})
const excludedOptionalIds = ref<string[]>([])

const iconByCategory: Record<string, string> = {
  flight: mdiAirplane,
  hotel: mdiBed,
  insurance: mdiShieldCheck,
  pharmacy: mdiMedicalBag,
  travel_kit: mdiMedicalBag,
  restaurant: mdiSilverwareForkKnife,
  transfer: mdiCar,
  activity: mdiTicketConfirmation,
}

const labelByCategory: Record<string, string> = {
  flight: 'Перелёт',
  hotel: 'Отель',
  insurance: 'Страховка',
  pharmacy: 'Дорожный набор',
  travel_kit: 'Дорожный набор',
  restaurant: 'Ресторан',
  transfer: 'Трансфер',
  activity: 'Активность',
}

const itemKey = (item: TravelItem) => `${item.category}:${item.id || item.title}`
const isExcluded = (item: TravelItem) => excludedOptionalIds.value.includes(itemKey(item))
const visibleItems = computed(() => (currentPlan.value?.items || []).filter(item => !isExcluded(item)))
const displayTotal = computed(() => visibleItems.value.reduce((sum, item) => sum + (item.price || 0), 0))
const displayBonus = computed(() => Math.round(displayTotal.value * 0.02))
const displayWithinBudget = computed(() => {
  const budget = currentPlan.value?.budget
  return budget ? displayTotal.value <= budget : true
})

const toggleExpanded = (item: TravelItem) => {
  const key = itemKey(item)
  expanded.value[key] = !expanded.value[key]
}

const toggleOptional = (item: TravelItem) => {
  const key = itemKey(item)
  excludedOptionalIds.value = isExcluded(item)
    ? excludedOptionalIds.value.filter(id => id !== key)
    : [...excludedOptionalIds.value, key]
}

const tripLabel = computed(() => {
  const trip = currentPlan.value?.trip
  if (!trip) return 'Поездка'
  const { pax, type, dates } = trip
  if (type === 'family_weekend') return `Семейная поездка · ${dates || 'выходные'}`
  if (pax === 1) return `Самостоятельная поездка · ${dates || 'выходные'}`
  if (pax === 2) return `Поездка вдвоём · ${dates || 'выходные'}`
  return `Поездка · ${dates || 'выходные'}`
})

const paxWord = (n: number) => n === 1 ? 'человек' : (n >= 2 && n <= 4) ? 'человека' : 'человек'
const nightsWord = (n: number) => n === 1 ? 'ночь' : (n >= 2 && n <= 4) ? 'ночи' : 'ночей'

const saveAndContinue = () => {
  if (!currentPlan.value) return

  currentPlan.value = {
    ...currentPlan.value,
    items: visibleItems.value,
    total: displayTotal.value,
    bonus: displayBonus.value,
    within_budget: displayWithinBudget.value,
    can_book: displayWithinBudget.value,
  }

  router.push('/travel/contact')
}

onMounted(() => {
  if (!currentPlan.value) {
    router.push('/travel')
  }
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
          План поездки
        </h1>
      </header>

      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <p class="text-[13px] font-semibold text-[#009b63]">
          {{ currentPlan?.trip.from }} → {{ currentPlan?.trip.to }}
        </p>

        <h2 class="mt-2 text-[25px] font-bold leading-tight">
          {{ tripLabel }}
        </h2>

        <p class="mt-3 text-[14px] text-[#6b7280]">
          {{ currentPlan?.trip.nights }} {{ nightsWord(currentPlan?.trip.nights || 2) }} · {{ currentPlan?.trip.pax }} {{ paxWord(currentPlan?.trip.pax || 1) }} · бюджет {{ formatPrice(currentPlan?.budget || 0) }}
        </p>
      </section>

      <section class="mt-5 space-y-3">
        <article
          v-for="item in currentPlan?.items || []"
          :key="itemKey(item)"
          class="rounded-[24px] bg-white shadow-sm"
        >
          <button
            class="flex w-full items-center gap-3 p-4 text-left"
            type="button"
            @click="toggleExpanded(item)"
          >
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#edf3f2]">
              <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
                <path :d="iconByCategory[item.category] || mdiTicketConfirmation" fill="currentColor" />
              </svg>
            </div>

            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <h3 class="truncate text-[15px] font-bold">
                  {{ labelByCategory[item.category] || item.title }}
                </h3>

                <span
                  v-if="item.optional"
                  class="rounded-full bg-[#eaf8f1] px-2 py-0.5 text-[11px] font-semibold text-[#00845f]"
                >
                  optional
                </span>
              </div>

              <p class="mt-1 truncate text-[13px] text-[#6b7280]">
                {{ item.title }}
              </p>
            </div>

            <div class="flex shrink-0 items-center gap-2">
              <label
                v-if="item.optional"
                class="flex h-8 w-8 items-center justify-center"
                @click.stop
              >
                <input
                  type="checkbox"
                  class="h-5 w-5 accent-[#009b63]"
                  :checked="!isExcluded(item)"
                  @change="toggleOptional(item)"
                >
              </label>

              <p
                class="text-right text-[14px] font-bold"
                :class="isExcluded(item) ? 'text-[#9aa3b5] line-through' : ''"
              >
                {{ formatPrice(item.price) }}
              </p>

              <svg
                viewBox="0 0 24 24"
                class="h-5 w-5 text-[#6b7280] transition-transform"
                :class="expanded[itemKey(item)] ? 'rotate-180' : ''"
              >
                <path :d="mdiChevronDown" fill="currentColor" />
              </svg>
            </div>
          </button>

          <div
            v-if="expanded[itemKey(item)]"
            class="border-t border-[#edf0f5] px-4 pb-4 pt-3"
          >
            <p class="text-[13px] leading-5 text-[#6b7280]">
              {{ item.details }}
            </p>

            <p
              v-if="item.disclaimer"
              class="mt-3 rounded-2xl bg-[#fff7ed] px-3 py-2 text-[12px] leading-5 text-[#9a3412]"
            >
              {{ item.disclaimer }}
            </p>
          </div>
        </article>
      </section>

      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <div class="flex items-center justify-between">
          <span class="text-[15px] text-[#6b7280]">Итого</span>
          <span class="text-[22px] font-bold">{{ formatPrice(displayTotal) }}</span>
        </div>

        <div class="mt-3 flex items-center justify-between">
          <span class="text-[15px] text-[#6b7280]">Бонусов Halyk</span>
          <span class="text-[17px] font-bold text-[#009b63]">
            + {{ formatPrice(displayBonus) }}
          </span>
        </div>

        <div class="mt-4 rounded-2xl bg-[#eaf8f1] px-4 py-3 text-[14px] font-semibold text-[#00845f]">
          {{ displayWithinBudget ? 'План входит в бюджет ✓' : 'План выше бюджета' }}
        </div>

        <div
          v-if="currentPlan?.budget && currentPlan.budget > displayTotal"
          class="mt-2 rounded-2xl bg-[#f4f6fb] px-4 py-3 text-[13px] text-[#6b7280]"
        >
          Сэкономлено: {{ formatPrice(currentPlan.budget - displayTotal) }} от бюджета
        </div>
      </section>

      <div class="mt-5 grid grid-cols-2 gap-3">
        <button
          class="rounded-2xl bg-white py-4 text-[15px] font-semibold text-[#202436] shadow-sm"
          @click="router.push('/travel/edit')"
        >
          Изменить
        </button>

        <button
          class="rounded-2xl bg-[#009b63] py-4 text-[15px] font-semibold text-white shadow-sm"
          @click="saveAndContinue"
        >
          Забронировать всё
        </button>
      </div>
    </div>
  </main>
</template>
