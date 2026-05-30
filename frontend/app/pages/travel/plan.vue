<script setup lang="ts">
import {
  mdiArrowLeft,
  mdiAirplane,
  mdiBed,
  mdiShieldCheck,
  mdiMedicalBag,
  mdiSilverwareForkKnife,
  mdiCar,
  mdiTicketConfirmation
} from '@mdi/js'

const router = useRouter()
const { currentPlan, formatPrice } = useTravel()

const iconByCategory: Record<string, string> = {
  flight: mdiAirplane,
  hotel: mdiBed,
  insurance: mdiShieldCheck,
  pharmacy: mdiMedicalBag,
  restaurant: mdiSilverwareForkKnife,
  transfer: mdiCar,
  activity: mdiTicketConfirmation,
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
          Семейная поездка на выходные
        </h2>

        <p class="mt-3 text-[14px] text-[#6b7280]">
          {{ currentPlan?.trip.nights }} ночи · {{ currentPlan?.trip.pax }} человека · бюджет {{ formatPrice(currentPlan?.budget || 0) }}
        </p>
      </section>

      <section class="mt-5 space-y-3">
        <article
          v-for="item in currentPlan?.items || []"
          :key="item.category"
          class="flex gap-3 rounded-[24px] bg-white p-4 shadow-sm"
        >
          <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#edf3f2]">
            <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
              <path :d="iconByCategory[item.category] || mdiTicketConfirmation" fill="currentColor" />
            </svg>
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex items-start justify-between gap-2">
              <h3 class="text-[15px] font-bold">
                {{ item.title }}
              </h3>

              <p class="shrink-0 text-[14px] font-bold">
                {{ formatPrice(item.price) }}
              </p>
            </div>

            <p class="mt-1 text-[13px] leading-5 text-[#6b7280]">
              {{ item.details }}
            </p>
          </div>
        </article>
      </section>

      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <div class="flex items-center justify-between">
          <span class="text-[15px] text-[#6b7280]">Итого</span>
          <span class="text-[22px] font-bold">{{ formatPrice(currentPlan?.total || 0) }}</span>
        </div>

        <div class="mt-3 flex items-center justify-between">
          <span class="text-[15px] text-[#6b7280]">Бонусов Halyk</span>
          <span class="text-[17px] font-bold text-[#009b63]">
            + {{ formatPrice(currentPlan?.bonus || 0) }}
          </span>
        </div>

        <div class="mt-4 rounded-2xl bg-[#eaf8f1] px-4 py-3 text-[14px] font-semibold text-[#00845f]">
          {{ currentPlan?.within_budget ? 'План входит в бюджет ✓' : 'План выше бюджета' }}
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
          @click="router.push('/travel/payment')"
        >
          Забронировать всё
        </button>
      </div>
    </div>
  </main>
</template>
