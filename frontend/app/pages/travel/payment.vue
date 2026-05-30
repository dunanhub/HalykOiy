<script setup lang="ts">
import { mdiArrowLeft, mdiCheckCircle } from '@mdi/js'

const router = useRouter()
const { currentPlan, formatPrice, payForPlan } = useTravel()

const loading = ref(false)
const errorMessage = ref('')

onMounted(() => {
  if (!currentPlan.value) {
    router.push('/travel')
  }
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
        <button
          class="absolute left-0 flex h-9 w-9 items-center justify-center"
          @click="router.back()"
        >
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiArrowLeft" fill="currentColor" />
          </svg>
        </button>

        <h1 class="text-[18px] font-semibold">
          Подтверждение
        </h1>
      </header>

      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <div class="flex h-14 w-14 items-center justify-center rounded-full bg-[#eaf8f1] text-[#009b63]">
          <svg viewBox="0 0 24 24" class="h-8 w-8">
            <path :d="mdiCheckCircle" fill="currentColor" />
          </svg>
        </div>

        <h2 class="mt-4 text-[24px] font-bold leading-tight">
          Подтвердите бронирование
        </h2>

        <p class="mt-2 text-[14px] text-[#6b7280]">
          {{ currentPlan?.trip.from }} → {{ currentPlan?.trip.to }} · {{ currentPlan?.trip.nights }} ночи · {{ currentPlan?.trip.pax }} человека
        </p>
      </section>

      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <div class="space-y-4">
          <div
            v-for="item in currentPlan?.items || []"
            :key="item.title"
            class="flex items-center justify-between gap-4"
          >
            <p class="text-[15px] text-[#374151]">
              {{ item.title }}
            </p>

            <p class="shrink-0 text-[15px] font-semibold">
              {{ formatPrice(item.price) }}
            </p>
          </div>
        </div>

        <div class="my-5 h-px bg-[#edf0f5]" />

        <div class="flex items-center justify-between">
          <p class="text-[16px] font-semibold">
            Итого
          </p>

          <p class="text-[22px] font-bold">
            {{ formatPrice(currentPlan?.total || 0) }}
          </p>
        </div>

        <div class="mt-3 flex items-center justify-between">
          <p class="text-[14px] text-[#6b7280]">
            Будет начислено бонусов
          </p>

          <p class="text-[16px] font-bold text-[#009b63]">
            + {{ formatPrice(currentPlan?.bonus || 0) }}
          </p>
        </div>
      </section>

      <p
        v-if="errorMessage"
        class="mt-4 rounded-2xl bg-[#fff1f2] px-4 py-3 text-[14px] text-[#be123c]"
      >
        {{ errorMessage }}
      </p>

      <section class="mt-5 rounded-[24px] bg-white p-4 shadow-sm">
        <p class="text-[13px] text-[#6b7280]">
          Оплата с карты
        </p>

        <p class="mt-1 text-[17px] font-bold">
          Halyk **** 4821
        </p>
      </section>

      <div class="mt-5 grid grid-cols-2 gap-3">
        <button
          class="rounded-2xl bg-white py-4 text-[15px] font-semibold text-[#202436] shadow-sm"
          @click="router.push('/travel/plan')"
        >
          Отмена
        </button>

        <button
          class="rounded-2xl bg-[#009b63] py-4 text-[15px] font-semibold text-white shadow-sm"
          :class="loading ? 'opacity-50' : ''"
          :disabled="loading"
          @click="pay"
        >
          {{ loading ? 'Оплачиваем...' : 'Оплатить ' + formatPrice(currentPlan?.total || 0) }}
        </button>
      </div>
    </div>
  </main>
</template>
