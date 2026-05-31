<script setup lang="ts">
import { mdiArrowLeft, mdiSend, mdiHistory, mdiLightbulbOnOutline, mdiViewDashboardOutline } from '@mdi/js'

const router = useRouter()
const { pendingMessage, pendingEditMessage, resetTravelDraft, activeTrip, loadDashboardState } = useTravel()

const message = ref('')
const quickPrompts = [
  'семьёй в Астану на выходные',
  'добавь хороший отель',
  'бюджет 150к',
]
const examplePrompt = 'хочу с семьёй в Астану на выходные, бюджет 150к'

onMounted(() => {
  loadDashboardState()

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

const useQuickPrompt = (prompt: string) => {
  message.value = message.value
    ? `${message.value}, ${prompt}`
    : `хочу ${prompt}`
}

const useExamplePrompt = () => {
  message.value = examplePrompt
}
</script>

<template>
  <main class="travel-screen">
    <div class="travel-shell flex flex-col">
      <header class="travel-topbar fade-slide">
        <button
          class="pressable absolute left-0 flex h-9 w-9 items-center justify-center rounded-full bg-white/70 shadow-sm"
          @click="router.back()"
        >
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiArrowLeft" fill="currentColor" />
          </svg>
        </button>

        <h1 class="text-[18px] font-semibold">
          Halyk Sapar
        </h1>

        <div class="absolute right-0 flex items-center gap-2">
          <button
            v-if="activeTrip"
            class="pressable flex h-9 w-9 items-center justify-center rounded-full bg-[#eaf8f1] text-[#00845f] shadow-sm"
            aria-label="Открыть Dashboard"
            @click="router.push('/travel/dashboard')"
          >
            <svg viewBox="0 0 24 24" class="h-6 w-6">
              <path :d="mdiViewDashboardOutline" fill="currentColor" />
            </svg>
          </button>

          <button
            class="pressable flex h-9 w-9 items-center justify-center rounded-full bg-white/70 shadow-sm"
            aria-label="История поездок"
            @click="router.push('/travel/history')"
          >
            <svg viewBox="0 0 24 24" class="h-6 w-6">
              <path :d="mdiHistory" fill="currentColor" />
            </svg>
          </button>
        </div>
      </header>

      <section class="travel-card travel-hero travel-soft-gradient fade-slide mt-6 p-5">
        <p class="text-[13px] font-semibold text-[#009b63]">AI Travel Companion</p>

        <h2 class="mt-3 text-[26px] font-bold leading-tight">
          Куда хотите поехать?
        </h2>

        <p class="mt-3 text-[15px] leading-6 text-[#6b7280]">
          Напишите свободно: город, даты, количество людей и бюджет. Я соберу поездку целиком.
        </p>

        <p class="mt-5 text-[12px] font-semibold uppercase tracking-[0.08em] text-[#9aa3b5]">
          Быстрые подсказки
        </p>

        <div class="mt-2 flex flex-wrap gap-2">
          <button
            v-for="prompt in quickPrompts"
            :key="prompt"
            type="button"
            class="travel-chip pressable px-3 py-2"
            @click="useQuickPrompt(prompt)"
          >
            {{ prompt }}
          </button>
        </div>
      </section>

      <section class="travel-card stagger mt-5 flex-1 p-4">
        <div class="travel-soft-gradient rounded-[22px] border border-[#e7ebf3] p-4">
          <div class="flex items-start gap-3">
            <div class="travel-icon-bubble h-10 w-10 shrink-0">
              <svg viewBox="0 0 24 24" class="h-6 w-6">
                <path :d="mdiLightbulbOnOutline" fill="currentColor" />
              </svg>
            </div>

            <div class="min-w-0 flex-1">
              <p class="text-[13px] font-semibold text-[#00845f]">Пример запроса</p>
              <p class="mt-1 text-[15px] font-medium leading-6">
                {{ examplePrompt }}
              </p>
              <button
                type="button"
                class="travel-chip pressable mt-3 px-3 py-2"
                @click="useExamplePrompt"
              >
                Использовать пример
              </button>
            </div>
          </div>
        </div>
      </section>

      <form
        class="travel-input-bar mt-4 flex items-center gap-3 p-3"
        @submit.prevent="submitRequest"
      >
        <input
          v-model="message"
          class="min-w-0 flex-1 bg-transparent px-2 text-[15px] outline-none placeholder:text-[#9aa3b5]"
          placeholder="Напишите запрос..."
        >

        <button
          type="submit"
          class="travel-primary-button flex h-11 w-11 items-center justify-center rounded-full"
          :disabled="!message.trim()"
        >
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiSend" fill="currentColor" />
          </svg>
        </button>
      </form>
    </div>
  </main>
</template>
