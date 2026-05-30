<script setup lang="ts">
import { mdiChevronRight, mdiQrcodeScan } from '@mdi/js'

const router = useRouter()
const { topServices, mainServices } = useServices()

const goToServices = () => {
  router.push('/services')
}
</script>

<template>
  <main class="min-h-screen bg-[#f4f6fb] text-[#202436]">
    <div class="mx-auto min-h-screen max-w-[430px] bg-[#f4f6fb] px-4 pb-24 pt-4">
      <header class="flex items-center gap-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-full bg-white font-semibold">
          БУ
        </div>

        <div class="flex h-10 flex-1 items-center rounded-2xl bg-[#e9edf7] px-4 text-[#9aa3b5]">
          Поиск
        </div>

        <div class="rounded-2xl bg-white px-3 py-2 text-sm font-semibold text-[#1c7c55]">
          418.03
        </div>
      </header>

      <section class="mt-5 grid grid-cols-[2fr_1fr] gap-3">
        <div class="rounded-[22px] bg-gradient-to-r from-[#172040] to-[#7b315f] p-4 text-white">
          <p class="text-[24px] font-bold leading-6">50% БОНУСОВ</p>
          <p class="mt-1 text-[12px] font-semibold">НА МЕЖДУГОРОДНИЕ АВТОБУСЫ</p>
          <div class="mt-5 h-14 rounded-xl bg-white/20" />
        </div>

        <div class="rounded-[22px] bg-gradient-to-br from-[#4b39d8] to-[#8d5cf6] p-4 text-white">
          <p class="text-xs">HalykMarket</p>
          <p class="mt-4 text-3xl font-bold">+10%</p>
        </div>
      </section>

      <section class="mt-6 grid grid-cols-4 gap-x-4 gap-y-5">
        <ServiceIcon
          v-for="item in topServices"
          :key="item.title"
          :title="item.title"
          :icon="item.icon"
        />
      </section>

      <section class="mt-7 rounded-[24px] bg-white p-4 shadow-sm">
        <button
          class="mb-4 flex w-full items-center justify-between"
          @click="goToServices"
        >
          <h2 class="text-[17px] font-bold">Все сервисы</h2>

          <svg viewBox="0 0 24 24" class="h-6 w-6 text-[#1f2937]">
            <path :d="mdiChevronRight" fill="currentColor" />
          </svg>
        </button>

        <div class="grid grid-cols-5 gap-3">
          <ServiceIcon
            v-for="item in mainServices"
            :key="item.title"
            :title="item.title"
            :icon="item.icon"
          />
        </div>
      </section>

      <nav class="fixed bottom-0 left-1/2 grid w-full max-w-[430px] -translate-x-1/2 grid-cols-5 items-center bg-white px-4 pb-3 pt-2 shadow-[0_-8px_24px_rgba(0,0,0,0.06)]">
        <span class="text-center text-[11px] text-[#00845f]">Главная</span>
        <span class="text-center text-[11px] text-[#7b8190]">Мой банк</span>

        <button class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#009b63] text-white">
          <svg viewBox="0 0 24 24" class="h-7 w-7">
            <path :d="mdiQrcodeScan" fill="currentColor" />
          </svg>
        </button>

        <span class="text-center text-[11px] text-[#7b8190]">Переводы</span>
        <span class="text-center text-[11px] text-[#7b8190]">Платежи</span>
      </nav>
    </div>
  </main>
</template>