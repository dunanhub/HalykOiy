<script setup lang="ts">
import { mdiArrowLeft, mdiSend } from '@mdi/js'

const router = useRouter()
const { pendingEditMessage, currentPlan } = useTravel()

const editMessage = ref('')

const submitEdit = () => {
  if (!editMessage.value.trim()) return

  pendingEditMessage.value = editMessage.value.trim()

  router.push('/travel/thinking')
}

onMounted(() => {
  if (!currentPlan.value) {
    router.push('/travel')
  }
})
</script>

<template>
  <main class="min-h-screen bg-[#f4f6fb] text-[#202436]">
    <div class="mx-auto flex min-h-screen max-w-[430px] flex-col bg-[#f4f6fb] px-4 pb-6 pt-4">
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
          Изменить план
        </h1>
      </header>

      <section class="mt-6 rounded-[28px] bg-white p-5 shadow-sm">
        <h2 class="text-[24px] font-bold leading-tight">
          Что изменить?
        </h2>

        <p class="mt-3 text-[15px] leading-6 text-[#6b7280]">
          Напишите правку обычным текстом. Например: убрать ресторан, добавить багаж или уменьшить бюджет.
        </p>

        <div class="mt-5 rounded-[22px] bg-[#f4f6fb] p-4 text-[15px]">
          убери ресторан, бюджет хочу оставить запас
        </div>
      </section>

      <div class="flex-1" />

      <form
        class="mt-4 flex items-center gap-3 rounded-[24px] bg-white p-3 shadow-sm"
        @submit.prevent="submitEdit"
      >
        <input
          v-model="editMessage"
          class="min-w-0 flex-1 bg-transparent px-2 text-[15px] outline-none placeholder:text-[#9aa3b5]"
          placeholder="Напишите изменение..."
        >

        <button
          type="submit"
          class="flex h-11 w-11 items-center justify-center rounded-full bg-[#009b63] text-white"
        >
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiSend" fill="currentColor" />
          </svg>
        </button>
      </form>
    </div>
  </main>
</template>
