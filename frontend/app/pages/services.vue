<script setup lang="ts">
import { mdiArrowLeft, mdiPencil } from '@mdi/js'

const router = useRouter()
const { mainServices, services, personal, support } = useServices()

const openService = (item: any) => {
  if (item.route) {
    router.push(item.route)
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

        <h1 class="text-[18px] font-semibold">Все сервисы</h1>
      </header>

      <section class="mt-4 rounded-[24px] bg-white p-4 shadow-sm">
        <h2 class="text-[18px] font-bold">Мои сервисы на главной</h2>

        <div class="mt-5 grid grid-cols-5 gap-3">
          <ServiceIcon
            v-for="item in mainServices"
            :key="item.title"
            :title="item.title"
            :icon="item.icon"
            large
            @click="openService(item)"
          />
        </div>

        <button class="mt-6 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#009b63] py-4 text-[15px] font-semibold text-white">
          <svg viewBox="0 0 24 24" class="h-5 w-5">
            <path :d="mdiPencil" fill="currentColor" />
          </svg>
          Изменить мои сервисы
        </button>
      </section>

      <section class="mt-6">
        <h2 class="px-1 text-[17px] font-bold">Сервисы и услуги</h2>

        <div class="mt-4 grid grid-cols-5 gap-x-3 gap-y-5">
          <ServiceIcon
            v-for="item in services"
            :key="item.title"
            :title="item.title"
            :icon="item.icon"
            large
            @click="openService(item)"
          />
        </div>
      </section>

      <section class="mt-7">
        <h2 class="px-1 text-[17px] font-bold">Личное</h2>

        <div class="mt-4 grid grid-cols-4 gap-x-4">
          <ServiceIcon
            v-for="item in personal"
            :key="item.title"
            :title="item.title"
            :icon="item.icon"
            large
          />
        </div>
      </section>

      <section class="mt-7 rounded-[24px] bg-white p-4 shadow-sm">
        <h2 class="text-[17px] font-bold">Поддержка</h2>

        <div class="mt-4 grid grid-cols-4 gap-x-4">
          <ServiceIcon
            v-for="item in support"
            :key="item.title"
            :title="item.title"
            :icon="item.icon"
            large
          />
        </div>
      </section>
    </div>
  </main>
</template>