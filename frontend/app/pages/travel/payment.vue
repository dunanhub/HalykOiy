<script setup lang="ts">
import { mdiArrowLeft, mdiCheckCircle, mdiCreditCard, mdiCalendarMonth } from '@mdi/js'

const router = useRouter()
const { currentPlan, formatPrice, payForPlan, contactInfo } = useTravel()

const loading = ref(false)
const errorMessage = ref('')
const payMode = ref<'full' | 3 | 6 | 12>('full')

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
  <main class="min-h-screen bg-[#f4f6fb] text-[#202436]">
    <div class="mx-auto min-h-screen max-w-[430px] bg-[#f4f6fb] px-4 pb-8 pt-4">
      <header class="relative flex items-center justify-center py-3">
        <button class="absolute left-0 flex h-9 w-9 items-center justify-center" @click="router.back()">
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiArrowLeft" fill="currentColor" />
          </svg>
        </button>
        <h1 class="text-[18px] font-semibold">Подтверждение</h1>
      </header>

      <!-- Trip summary -->
      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <div class="flex h-14 w-14 items-center justify-center rounded-full bg-[#eaf8f1] text-[#009b63]">
          <svg viewBox="0 0 24 24" class="h-8 w-8">
            <path :d="mdiCheckCircle" fill="currentColor" />
          </svg>
        </div>
        <h2 class="mt-4 text-[24px] font-bold">Подтвердите бронирование</h2>
        <p class="mt-2 text-[14px] text-[#6b7280]">
          {{ currentPlan?.trip.from }} → {{ currentPlan?.trip.to }} · {{ currentPlan?.trip.nights }} ноч · {{ currentPlan?.trip.pax }} чел
        </p>
        <div v-if="contactInfo" class="mt-3 rounded-2xl bg-[#f4f6fb] px-3 py-2 text-[13px] text-[#6b7280]">
          {{ contactInfo.name }} {{ contactInfo.surname }} · {{ contactInfo.email }}
        </div>
      </section>

      <!-- Items -->
      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <div class="space-y-4">
          <div v-for="item in currentPlan?.items || []" :key="item.title" class="flex items-center justify-between gap-4">
            <p class="text-[15px] text-[#374151]">{{ item.title }}</p>
            <p class="shrink-0 text-[15px] font-semibold">{{ formatPrice(item.price) }}</p>
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
      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <p class="mb-3 text-[16px] font-bold">Способ оплаты</p>

        <!-- Full payment -->
        <button
          class="mb-2 flex w-full items-center gap-3 rounded-2xl border-2 px-4 py-3 text-left transition-colors"
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
            class="flex flex-col items-center rounded-2xl border-2 px-2 py-3 transition-colors"
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

      <p v-if="errorMessage" class="mt-4 rounded-2xl bg-[#fff1f2] px-4 py-3 text-[14px] text-[#be123c]">
        {{ errorMessage }}
      </p>

      <div class="mt-5 grid grid-cols-2 gap-3">
        <button
          class="rounded-2xl bg-white py-4 text-[15px] font-semibold text-[#202436] shadow-sm"
          @click="router.push('/travel/plan')"
        >
          Назад
        </button>

        <button
          class="rounded-2xl bg-[#009b63] py-4 text-[15px] font-semibold text-white shadow-sm"
          :class="loading ? 'opacity-50' : ''"
          :disabled="loading"
          @click="pay"
        >
          {{ loading ? 'Обрабатываем...' : payMode === 'full' ? 'Оплатить ' + formatPrice(currentPlan?.total || 0) : `Оформить рассрочку` }}
        </button>
      </div>
    </div>
  </main>
</template>
