<script setup lang="ts">
import {
  mdiHomeHeart,
  mdiMapMarkerPath,
  mdiArrowRight,
  mdiImageFilterHdr,
  mdiMosque
} from '@mdi/js'

const router = useRouter()
const { currentPlan, paymentResult, formatPrice } = useTravel()

const tripTitle = computed(() => {
  if (!currentPlan.value) return 'Астану'

  return currentPlan.value.trip.to
})

const spent = computed(() => {
  return formatPrice(paymentResult.value?.total || currentPlan.value?.total || 125500)
})

const bonus = computed(() => {
  return formatPrice(paymentResult.value?.bonus || currentPlan.value?.bonus || 2510)
})

const suggestions = [
  {
    title: 'Алматы → Боровое',
    description: '2 часа на машине · природа · детям понравится',
    price: '~80 000 ₸',
    icon: mdiImageFilterHdr,
    prompt: 'хочу с семьёй в Боровое на выходные, бюджет 80к'
  },
  {
    title: 'Алматы → Туркестан',
    description: 'Исторический маршрут · культурная поездка',
    price: '~120 000 ₸',
    icon: mdiMosque,
    prompt: 'хочу с семьёй в Туркестан, бюджет 120к'
  }
]

const startNextTrip = (prompt: string) => {
  router.push({
    path: '/travel',
    query: {
      prompt
    }
  })
}
</script>

<template>
  <main class="travel-screen">
    <div class="travel-shell pt-8">
      <section class="travel-card travel-hero pop-in p-6 text-center">
        <div class="travel-icon-bubble mx-auto h-20 w-20">
          <svg viewBox="0 0 24 24" class="h-11 w-11">
            <path :d="mdiHomeHeart" fill="currentColor" />
          </svg>
        </div>

        <h1 class="mt-5 text-[27px] font-bold leading-tight">
          Добро пожаловать домой!
        </h1>

        <p class="mt-3 text-[14px] leading-6 text-[#6b7280]">
          Поездка в {{ tripTitle }} завершена. Потрачено {{ spent }}, бонусов начислено +{{ bonus }}.
        </p>
      </section>

      <section class="travel-card mt-5 p-5">
        <div class="flex items-center gap-3">
            <div class="travel-icon-bubble h-11 w-11">
            <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
              <path :d="mdiMapMarkerPath" fill="currentColor" />
            </svg>
          </div>

          <div>
            <h2 class="text-[18px] font-bold">
              Куда следующий раз?
            </h2>

            <p class="mt-1 text-[13px] text-[#6b7280]">
              AI подобрал идеи на основе вашей поездки
            </p>
          </div>
        </div>
      </section>

      <section class="stagger mt-5 space-y-3">
        <button
          v-for="item in suggestions"
          :key="item.title"
          class="travel-card pressable w-full p-5 text-left"
          @click="startNextTrip(item.prompt)"
        >
          <div class="flex gap-4">
            <div class="travel-icon-bubble h-12 w-12 shrink-0">
              <svg viewBox="0 0 24 24" class="h-7 w-7 text-[#00845f]">
                <path :d="item.icon" fill="currentColor" />
              </svg>
            </div>

            <div class="min-w-0 flex-1">
              <div class="flex items-start justify-between gap-3">
                <h3 class="text-[16px] font-bold">
                  {{ item.title }}
                </h3>

                <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 text-[#9aa3b5]">
                  <path :d="mdiArrowRight" fill="currentColor" />
                </svg>
              </div>

              <p class="mt-1 text-[13px] leading-5 text-[#6b7280]">
                {{ item.description }}
              </p>

              <p class="mt-3 text-[15px] font-bold text-[#009b63]">
                {{ item.price }}
              </p>
            </div>
          </div>
        </button>
      </section>

      <button
        class="travel-secondary-button mt-6 w-full py-4 text-[15px]"
        @click="router.push('/travel')"
      >
        Посмотреть другие направления
      </button>
    </div>
  </main>
</template>
