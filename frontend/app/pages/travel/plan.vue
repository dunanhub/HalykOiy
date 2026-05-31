<script setup lang="ts">
import {
  mdiArrowLeft,
  mdiAirplane,
  mdiBed,
  mdiShieldCheck,
  mdiMedicalBag,
  mdiSilverwareForkKnife,
  mdiCar,
  mdiTicketConfirmation,
  mdiChevronDown,
} from '@mdi/js'
import type { TravelItem } from '~/composables/useTravel'

const router = useRouter()
const { currentPlan, formatPrice } = useTravel()

const excludedOptionalIds = ref<string[]>([])
const expandedGroups = ref<Record<string, boolean>>({})
const groupedCategories = ['transfer', 'activity', 'restaurant']

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
const canToggleItem = (item: TravelItem) => Boolean(item.optional) || item.category === 'insurance'
const isExcluded = (item: TravelItem) => excludedOptionalIds.value.includes(itemKey(item))
const visibleItems = computed(() => (currentPlan.value?.items || []).filter(item => !isExcluded(item)))
const displayTotal = computed(() => visibleItems.value.reduce((sum, item) => sum + (item.price || 0), 0))
const displayBonus = computed(() => Math.round(displayTotal.value * 0.02))
const displayWithinBudget = computed(() => {
  const budget = currentPlan.value?.budget
  return budget ? displayTotal.value <= budget : true
})

const toggleOptional = (item: TravelItem) => {
  const key = itemKey(item)
  excludedOptionalIds.value = isExcluded(item)
    ? excludedOptionalIds.value.filter(id => id !== key)
    : [...excludedOptionalIds.value, key]
}

const visibleCountByCategory = computed(() => {
  return visibleItems.value.reduce<Record<string, number>>((acc, item) => {
    acc[item.category] = (acc[item.category] || 0) + 1
    return acc
  }, {})
})

type PlanRow =
  | { type: 'item'; key: string; item: TravelItem }
  | { type: 'group'; key: string; category: string; items: TravelItem[]; total: number }

const planRows = computed<PlanRow[]>(() => {
  const rows: PlanRow[] = []
  const usedGroups = new Set<string>()
  const items = currentPlan.value?.items || []

  for (const item of items) {
    const shouldGroup = groupedCategories.includes(item.category) && (visibleCountByCategory.value[item.category] || 0) > 1

    if (!shouldGroup) {
      rows.push({ type: 'item', key: itemKey(item), item })
      continue
    }

    if (usedGroups.has(item.category)) continue
    const groupItems = items.filter(candidate => candidate.category === item.category)
    rows.push({
      type: 'group',
      key: `group:${item.category}`,
      category: item.category,
      items: groupItems,
      total: groupItems.reduce((sum, candidate) => isExcluded(candidate) ? sum : sum + (candidate.price || 0), 0),
    })
    usedGroups.add(item.category)
  }

  return rows
})

const toggleGroup = (key: string) => {
  expandedGroups.value[key] = !expandedGroups.value[key]
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

        <h1 class="text-[18px] font-semibold">
          План поездки
        </h1>
      </header>

      <section class="travel-card travel-hero travel-soft-gradient fade-slide mt-5 p-5">
        <p class="text-[13px] font-semibold text-[#009b63]">
          {{ currentPlan?.trip.from }} → {{ currentPlan?.trip.to }}
        </p>

        <h2 class="mt-2 text-[25px] font-bold leading-tight">
          {{ tripLabel }}
        </h2>

        <p class="mt-3 text-[14px] text-[#6b7280]">
          {{ currentPlan?.trip.nights }} {{ nightsWord(currentPlan?.trip.nights || 2) }} · {{ currentPlan?.trip.pax }} {{ paxWord(currentPlan?.trip.pax || 1) }} · бюджет {{ formatPrice(currentPlan?.budget || 0) }}
        </p>

        <div class="mt-5 h-2 rounded-full bg-white/80">
          <div
            class="h-2 rounded-full bg-[#009b63] transition-all duration-500"
            :style="{ width: `${Math.min(100, Math.round((displayTotal / (currentPlan?.budget || displayTotal || 1)) * 100))}%` }"
          />
        </div>
      </section>

      <section class="stagger mt-5 space-y-3">
        <article
          v-for="row in planRows"
          :key="row.key"
          class="travel-card p-4"
        >
          <template v-if="row.type === 'item'">
          <div class="flex items-start gap-3">
            <div class="travel-icon-bubble h-12 w-12 shrink-0">
              <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
                <path :d="iconByCategory[row.item.category] || mdiTicketConfirmation" fill="currentColor" />
              </svg>
            </div>

            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <h3 class="truncate text-[15px] font-bold">
                  {{ labelByCategory[row.item.category] || row.item.title }}
                </h3>

                <span
                  v-if="canToggleItem(row.item)"
                  class="text-[11px] font-semibold text-[#6b7280]"
                >
                  Можно убрать
                </span>
              </div>

              <p class="mt-1 text-[13px] font-semibold text-[#202436]">
                {{ row.item.title }}
              </p>

              <p class="mt-1 line-clamp-2 text-[13px] leading-5 text-[#6b7280]">
                {{ row.item.details }}
              </p>

              <p
                v-if="row.item.disclaimer"
                class="mt-3 rounded-2xl bg-[#fff7ed] px-3 py-2 text-[12px] leading-5 text-[#9a3412]"
              >
                {{ row.item.disclaimer }}
              </p>
            </div>

            <div class="flex shrink-0 flex-col items-end gap-2">
              <label
                v-if="canToggleItem(row.item)"
                class="pressable flex h-8 w-8 items-center justify-center rounded-full bg-[#f4f6fb]"
                @click.stop
              >
                <input
                  type="checkbox"
                  class="h-5 w-5 accent-[#009b63]"
                  :checked="!isExcluded(row.item)"
                  @change="toggleOptional(row.item)"
                >
              </label>

              <p
                class="text-right text-[14px] font-bold"
                :class="isExcluded(row.item) ? 'text-[#9aa3b5] line-through' : ''"
              >
                {{ formatPrice(row.item.price) }}
              </p>
            </div>
          </div>
          </template>

          <template v-else>
            <button
              type="button"
              class="pressable flex w-full items-center gap-3 text-left"
              @click="toggleGroup(row.key)"
            >
              <div class="travel-icon-bubble h-12 w-12 shrink-0">
                <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
                  <path :d="iconByCategory[row.category] || mdiTicketConfirmation" fill="currentColor" />
                </svg>
              </div>

              <div class="min-w-0 flex-1">
                <h3 class="text-[15px] font-bold">
                  {{ labelByCategory[row.category] }}
                </h3>
                <p class="mt-1 text-[13px] text-[#6b7280]">
                  {{ row.items.length }} варианта в плане
                </p>
              </div>

              <div class="flex shrink-0 items-center gap-2">
                <p class="text-right text-[14px] font-bold">{{ formatPrice(row.total) }}</p>
                <svg
                  viewBox="0 0 24 24"
                  class="h-5 w-5 text-[#6b7280] transition-transform"
                  :class="expandedGroups[row.key] ? 'rotate-180' : ''"
                >
                  <path :d="mdiChevronDown" fill="currentColor" />
                </svg>
              </div>
            </button>

            <div v-if="expandedGroups[row.key]" class="mt-4 space-y-3 border-t border-[#edf0f5] pt-4">
              <div
                v-for="item in row.items"
                :key="itemKey(item)"
                class="rounded-2xl bg-[#f8fafc] px-3 py-3"
              >
                <div class="flex items-start gap-3">
                  <div class="travel-icon-bubble h-9 w-9 shrink-0 rounded-2xl">
                    <svg viewBox="0 0 24 24" class="h-5 w-5 text-[#00845f]">
                      <path :d="iconByCategory[item.category] || mdiTicketConfirmation" fill="currentColor" />
                    </svg>
                  </div>

                  <div class="min-w-0 flex-1">
                    <p class="text-[13px] font-bold text-[#202436]">{{ item.title }}</p>
                    <p class="mt-1 line-clamp-2 text-[12px] leading-5 text-[#6b7280]">{{ item.details }}</p>
                  </div>

                  <p
                    class="shrink-0 text-right text-[13px] font-bold"
                    :class="isExcluded(item) ? 'text-[#9aa3b5] line-through' : ''"
                  >
                    {{ formatPrice(item.price) }}
                  </p>
                </div>
              </div>
            </div>
          </template>
        </article>
      </section>

      <section class="travel-card mt-5 p-5">
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
          {{ displayWithinBudget ? 'План входит в бюджет' : 'План выше бюджета' }}
        </div>

        <div
          v-if="currentPlan?.budget && currentPlan.budget > displayTotal"
          class="mt-2 rounded-2xl bg-[#f4f6fb] px-4 py-3 text-[13px] text-[#6b7280]"
        >
          Сэкономлено: {{ formatPrice(currentPlan.budget - displayTotal) }} от бюджета
        </div>
      </section>

      <div class="travel-sticky-action mt-5 grid grid-cols-2 gap-3">
        <button
          class="travel-secondary-button py-4 text-[15px]"
          @click="router.push('/travel/edit')"
        >
          Изменить
        </button>

        <button
          class="travel-primary-button py-4 text-[15px]"
          @click="saveAndContinue"
        >
          Забронировать всё
        </button>
      </div>
    </div>
  </main>
</template>
