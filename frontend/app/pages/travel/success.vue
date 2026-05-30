<script setup lang="ts">
import {
  mdiCheckCircle,
  mdiTicketConfirmation,
  mdiBed,
  mdiShieldCheck,
  mdiGiftOutline,
  mdiArrowLeft,
} from '@mdi/js'

const router = useRouter()
const { paymentResult, currentPlan, formatPrice } = useTravel()

onMounted(() => {
  if (!paymentResult.value) {
    router.push('/travel/payment')
  }
})
</script>

<template>
  <main class="travel-screen">
    <div class="travel-shell flex flex-col pt-8">
      <section class="travel-card travel-hero pop-in p-6 text-center">
        <div class="travel-icon-bubble mx-auto h-20 w-20 travel-pulse">
          <svg viewBox="0 0 24 24" class="h-12 w-12">
            <path :d="mdiCheckCircle" fill="currentColor" />
          </svg>
        </div>

        <h1 class="mt-5 text-[28px] font-bold leading-tight">
          Всё забронировано!
        </h1>
      </section>

      <section class="stagger mt-5 space-y-3">
        <div class="travel-card flex items-center gap-3 p-4">
          <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#009b63]">
            <path :d="mdiTicketConfirmation" fill="currentColor" />
          </svg>
          <p class="text-[15px] font-semibold">Билеты отправлены на почту</p>
        </div>

        <div class="travel-card flex items-center gap-3 p-4">
          <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#009b63]">
            <path :d="mdiBed" fill="currentColor" />
          </svg>
          <p class="text-[15px] font-semibold">Отель подтверждён</p>
        </div>

        <div class="travel-card flex items-center gap-3 p-4">
          <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#009b63]">
            <path :d="mdiShieldCheck" fill="currentColor" />
          </svg>
          <p class="text-[15px] font-semibold">Страховка оформлена</p>
        </div>

        <div class="travel-card flex items-center gap-3 p-4">
          <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#009b63]">
            <path :d="mdiGiftOutline" fill="currentColor" />
          </svg>
          <p class="text-[15px] font-semibold">Бонусы +{{ formatPrice(paymentResult?.bonus || currentPlan?.bonus || 0) }} зачислены</p>
        </div>
      </section>

      <div class="flex-1" />

      <div class="travel-sticky-action mt-6 grid gap-3">
        <button
          class="travel-primary-button w-full py-4 text-[15px]"
          @click="router.push('/travel/dashboard')"
        >
          Открыть Travel Dashboard
        </button>

        <button
          class="travel-secondary-button flex w-full items-center justify-center gap-2 py-4 text-[15px]"
          @click="router.push('/travel')"
        >
          <svg viewBox="0 0 24 24" class="h-5 w-5">
            <path :d="mdiArrowLeft" fill="currentColor" />
          </svg>
          Назад в Halyk Sapar
        </button>
      </div>
    </div>
  </main>
</template>
