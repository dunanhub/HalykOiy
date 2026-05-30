<script setup lang="ts">
import { mdiArrowLeft, mdiSend, mdiHistory } from '@mdi/js'

const router = useRouter()
const { pendingMessage, pendingEditMessage, resetTravelDraft } = useTravel()

const message = ref('')

onMounted(() => {
  const route = useRoute()
  const prompt = route.query.prompt

  if (typeof prompt === 'string') {
    message.value = prompt
  }
})

const submitRequest = () => {
  if (!message.value.trim()) return

  pendingMessage.value = message.value.trim()
  pendingEditMessage.value = ''
  resetTravelDraft()

  router.push('/travel/thinking')
}
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
          Halyk Sapar
        </h1>

        <button
          class="absolute right-0 flex h-9 w-9 items-center justify-center"
          @click="router.push('/travel/history')"
        >
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiHistory" fill="currentColor" />
          </svg>
        </button>
      </header>

      <section class="mt-6 rounded-[28px] bg-white p-5 shadow-sm">
        <p class="text-[13px] font-semibold text-[#009b63]">
          AI Travel Companion
        </p>

        <h2 class="mt-3 text-[26px] font-bold leading-tight">
          Куда хотите поехать?
        </h2>

        <p class="mt-3 text-[15px] leading-6 text-[#6b7280]">
          Напишите свободно: город, даты, количество людей и бюджет. Я соберу поездку целиком.
        </p>
      </section>

      <section class="mt-5 flex-1 rounded-[28px] bg-white p-4 shadow-sm">
        <div class="rounded-[22px] bg-[#f4f6fb] p-4">
          <p class="text-[14px] text-[#7b8190]">
            Например:
          </p>

          <p class="mt-2 text-[15px] font-medium leading-6">
            хочу с семьёй в Астану на выходные, бюджет 150к
          </p>
        </div>
      </section>

      <form
        class="mt-4 flex items-center gap-3 rounded-[24px] bg-white p-3 shadow-sm"
        @submit.prevent="submitRequest"
      >
        <input
          v-model="message"
          class="min-w-0 flex-1 bg-transparent px-2 text-[15px] outline-none placeholder:text-[#9aa3b5]"
          placeholder="Напишите запрос..."
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
