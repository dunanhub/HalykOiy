<script setup lang="ts">
import {
  mdiArrowLeft,
  mdiCreditCard,
  mdiCalendarMonth,
  mdiReceiptTextCheckOutline,
  mdiAirplane,
  mdiBed,
  mdiCar,
  mdiTicketConfirmation,
  mdiSilverwareForkKnife,
  mdiShieldCheck,
  mdiMedicalBag,
} from '@mdi/js'
import type { TravelItem } from '~/composables/useTravel'

const router = useRouter()
const { currentPlan, formatPrice, payForPlan, contactInfo } = useTravel()

const loading = ref(false)
const errorMessage = ref('')
const payMode = ref<'full' | 3 | 6 | 12>('full')

const iconByCategory: Record<string, string> = {
  flight: mdiAirplane,
  hotel: mdiBed,
  transfer: mdiCar,
  activity: mdiTicketConfirmation,
  restaurant: mdiSilverwareForkKnife,
  insurance: mdiShieldCheck,
  pharmacy: mdiMedicalBag,
  travel_kit: mdiMedicalBag,
}

const labelByCategory: Record<string, string> = {
  flight: 'Перелёт',
  hotel: 'Проживание',
  transfer: 'Трансфер',
  activity: 'Активности',
  restaurant: 'Ресторан',
  insurance: 'Страховка',
  pharmacy: 'Аптечка',
  travel_kit: 'Аптечка',
}

const paymentGroups = computed(() => {
  const groups = new Map<string, { category: string; label: string; icon: string; items: TravelItem[]; total: number }>()

  for (const item of currentPlan.value?.items || []) {
    const category = item.category
    const existing = groups.get(category)
    if (existing) {
      existing.items.push(item)
      existing.total += item.price || 0
      continue
    }

    groups.set(category, {
      category,
      label: labelByCategory[category] || item.title,
      icon: iconByCategory[category] || mdiTicketConfirmation,
      items: [item],
      total: item.price || 0,
    })
  }

  return Array.from(groups.values())
})

const monthlyPayment = computed(() => {
  const total = currentPlan.value?.total || 0
  if (payMode.value === 'full') return 0
  return Math.ceil(total / (payMode.value as number))
})

onMounted(() => {
  if (!currentPlan.value) router.push('/travel')
})

const pay = async () => {
  loading.value = true
  errorMessage.value = ''

  try {
    await payForPlan()
    router.push('/travel/success')
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Не удалось провести mock-оплату. Проверьте backend.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="travel-screen">
    <div class="travel-shell">
      <header class="travel-topbar fade-slide">
        <button class="pressable absolute left-0 flex h-9 w-9 items-center justify-center rounded-full bg-white/70 shadow-sm" @click="router.back()">
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiArrowLeft" fill="currentColor" />
          </svg>
        </button>
        <h1 class="text-[18px] font-semibold">Подтверждение</h1>
      </header>

      <!-- Trip summary -->
      <section class="travel-card travel-hero travel-soft-gradient fade-slide mt-5 p-5">
        <div class="travel-icon-bubble h-14 w-14">
          <svg viewBox="0 0 24 24" class="h-8 w-8">
            <path :d="mdiReceiptTextCheckOutline" fill="currentColor" />
          </svg>
        </div>
        <h2 class="mt-4 text-[24px] font-bold">Проверка и оплата</h2>
        <p class="mt-2 text-[14px] text-[#6b7280]">
          {{ currentPlan?.trip.from }} → {{ currentPlan?.trip.to }} · {{ currentPlan?.trip.nights }} ноч · {{ currentPlan?.trip.pax }} чел
        </p>
        <div v-if="contactInfo" class="mt-3 rounded-2xl bg-white/80 px-3 py-2 text-[13px] text-[#6b7280]">
          {{ contactInfo.name }} {{ contactInfo.surname }} · {{ contactInfo.email }}
        </div>
      </section>

      <!-- Items -->
      <section class="travel-card mt-5 p-5">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-[17px] font-bold">Ваш заказ</h2>
          <span class="text-[12px] font-semibold text-[#9aa3b5]">{{ currentPlan?.items.length || 0 }} позиций</span>
        </div>

        <div class="space-y-3">
          <div
            v-for="group in paymentGroups"
            :key="group.category"
            class="rounded-[22px] bg-[#f8fafc] px-3 py-3"
          >
            <div class="flex items-start gap-3">
              <div class="travel-icon-bubble h-10 w-10 shrink-0">
                <svg viewBox="0 0 24 24" class="h-6 w-6 text-[#00845f]">
                  <path :d="group.icon" fill="currentColor" />
                </svg>
              </div>

              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between gap-3">
                  <p class="text-[14px] font-bold text-[#202436]">{{ group.label }}</p>
                  <p class="shrink-0 text-[14px] font-bold">{{ formatPrice(group.total) }}</p>
                </div>
                <div class="mt-2 space-y-2">
                  <div
                    v-for="item in group.items"
                    :key="`${item.category}:${item.title}`"
                    class="flex items-start justify-between gap-3"
                  >
                    <p class="min-w-0 text-[13px] leading-5 text-[#6b7280]">{{ item.title }}</p>
                    <p class="shrink-0 text-[13px] font-semibold text-[#202436]">{{ formatPrice(item.price) }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="my-5 h-px bg-[#edf0f5]" />

        <div class="flex items-center justify-between">
          <p class="text-[16px] font-semibold">Итого</p>
          <p class="text-[22px] font-bold">{{ formatPrice(currentPlan?.total || 0) }}</p>
        </div>

        <div class="mt-3 flex items-center justify-between">
          <p class="text-[14px] text-[#6b7280]">Бонусов Halyk</p>
          <p class="text-[16px] font-bold text-[#009b63]">+ {{ formatPrice(currentPlan?.bonus || 0) }}</p>
        </div>
      </section>

      <!-- Payment method -->
      <section class="travel-card mt-5 p-5">
        <p class="mb-3 text-[16px] font-bold">Способ оплаты</p>

        <!-- Full payment -->
        <button
          class="pressable mb-2 flex w-full items-center gap-3 rounded-2xl border-2 px-4 py-3 text-left transition-colors"
          :class="payMode === 'full' ? 'border-[#009b63] bg-[#eaf8f1]' : 'border-[#edf0f5] bg-white'"
          @click="payMode = 'full'"
        >
          <svg viewBox="0 0 24 24" class="h-6 w-6 shrink-0 text-[#009b63]">
            <path :d="mdiCreditCard" fill="currentColor" />
          </svg>
          <div class="flex-1">
            <p class="text-[15px] font-semibold">Оплатить сразу</p>
            <p class="text-[13px] text-[#6b7280]">{{ formatPrice(currentPlan?.total || 0) }} · Halyk **** 4821</p>
          </div>
          <div
            class="h-5 w-5 rounded-full border-2"
            :class="payMode === 'full' ? 'border-[#009b63] bg-[#009b63]' : 'border-[#d1d5db]'"
          />
        </button>

        <!-- Installment options -->
        <p class="mb-2 mt-4 text-[13px] font-semibold text-[#6b7280]">Рассрочка Halyk</p>

        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="months in [3, 6, 12]"
            :key="months"
            class="pressable flex flex-col items-center rounded-2xl border-2 px-2 py-3 transition-colors"
            :class="payMode === months ? 'border-[#009b63] bg-[#eaf8f1]' : 'border-[#edf0f5] bg-white'"
            @click="payMode = months"
          >
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-[#009b63]">
              <path :d="mdiCalendarMonth" fill="currentColor" />
            </svg>
            <p class="mt-1 text-[14px] font-bold">{{ months }} мес</p>
            <p class="text-[11px] text-[#6b7280]">
              {{ formatPrice(Math.ceil((currentPlan?.total || 0) / months)) }}/мес
            </p>
          </button>
        </div>

        <div v-if="payMode !== 'full'" class="mt-3 rounded-2xl bg-[#fff7ed] px-4 py-3">
          <p class="text-[13px] font-semibold text-[#9a3412]">
            Рассрочка на {{ payMode }} месяцев — {{ formatPrice(monthlyPayment) }}/мес без переплаты
          </p>
          <p class="mt-1 text-[12px] text-[#9a3412]">Оформляется через Halyk Bank</p>
        </div>
      </section>

      <p v-if="errorMessage" class="fade-slide mt-4 rounded-2xl bg-[#fff1f2] px-4 py-3 text-[14px] text-[#be123c]">
        {{ errorMessage }}
      </p>

      <div class="travel-sticky-action mt-5 grid grid-cols-2 gap-3">
        <button
          class="travel-secondary-button py-4 text-[15px]"
          @click="router.push('/travel/plan')"
        >
          Назад
        </button>

        <button
          class="travel-primary-button py-4 text-[15px]"
          :disabled="loading"
          @click="pay"
        >
          {{ loading ? 'Обрабатываем...' : payMode === 'full' ? 'Оплатить ' + formatPrice(currentPlan?.total || 0) : `Оформить рассрочку` }}
        </button>
      </div>
    </div>
  </main>
</template>
