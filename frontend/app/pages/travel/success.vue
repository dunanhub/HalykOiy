<script setup lang="ts">
import {
  mdiCheckCircle,
  mdiTicketConfirmation,
  mdiBed,
  mdiShieldCheck,
  mdiGiftOutline
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
  <main class="min-h-screen bg-[#f4f6fb] text-[#202436]">
    <div class="mx-auto flex min-h-screen max-w-[430px] flex-col bg-[#f4f6fb] px-4 pb-8 pt-8">
      <section class="rounded-[32px] bg-white p-6 text-center shadow-sm">
        <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-[#eaf8f1] text-[#009b63]">
          <svg viewBox="0 0 24 24" class="h-12 w-12">
            <path :d="mdiCheckCircle" fill="currentColor" />
          </svg>
        </div>

        <h1 class="mt-5 text-[28px] font-bold leading-tight">
          Всё забронировано!
        </h1>

        <p class="mt-3 text-[14px] text-[#6b7280]">
          transaction_id: {{ paymentResult?.transaction_id }}
        </p>
      </section>

      <section class="mt-5 space-y-3">
        <div class="flex items-center gap-3 rounded-[24px] bg-white p-4 shadow-sm">
          <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#009b63]">
            <path :d="mdiTicketConfirmation" fill="currentColor" />
          </svg>
          <p class="text-[15px] font-semibold">Билеты отправлены на почту</p>
        </div>

        <div class="flex items-center gap-3 rounded-[24px] bg-white p-4 shadow-sm">
          <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#009b63]">
            <path :d="mdiBed" fill="currentColor" />
          </svg>
          <p class="text-[15px] font-semibold">Отель подтверждён</p>
        </div>

        <div class="flex items-center gap-3 rounded-[24px] bg-white p-4 shadow-sm">
          <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#009b63]">
            <path :d="mdiShieldCheck" fill="currentColor" />
          </svg>
          <p class="text-[15px] font-semibold">Страховка оформлена</p>
        </div>

        <div class="flex items-center gap-3 rounded-[24px] bg-white p-4 shadow-sm">
          <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#009b63]">
            <path :d="mdiGiftOutline" fill="currentColor" />
          </svg>
          <p class="text-[15px] font-semibold">Бонусы +{{ formatPrice(paymentResult?.bonus || currentPlan?.bonus || 0) }} зачислены</p>
        </div>
      </section>

      <div class="flex-1" />

      <button
        class="mt-6 w-full rounded-2xl bg-[#009b63] py-4 text-[15px] font-semibold text-white shadow-sm"
        @click="router.push('/travel/dashboard')"
      >
        Открыть Travel Dashboard
      </button>
    </div>
  </main>
</template>
