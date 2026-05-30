<script setup lang="ts">
import { mdiArrowLeft } from '@mdi/js'

const router = useRouter()
const {
  pendingMessage,
  pendingEditMessage,
  currentPlan,
  getThinkingSteps,
  createPlan,
  editPlan,
} = useTravel()

const steps = ref<string[]>([])
const loading = ref(true)
const errorMessage = ref('')
const planReady = computed(() => Boolean(currentPlan.value) && !loading.value && !errorMessage.value)

const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

onMounted(async () => {
  try {
    const backendSteps = await getThinkingSteps()

    for (const step of backendSteps) {
      steps.value.push(`${step.icon} ${step.text}`)
      await wait(350)
    }

    if (pendingEditMessage.value) {
      await editPlan(pendingEditMessage.value)
      pendingEditMessage.value = ''
    } else {
      await createPlan(pendingMessage.value || 'хочу с семьёй в Астану на выходные, бюджет 150к')
      pendingMessage.value = ''
    }

    steps.value.push('✅ План готов!')
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Не удалось собрать план. Проверьте, что backend запущен.'
  } finally {
    loading.value = false
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
          AI думает
        </h1>
      </header>

      <section class="mt-6 rounded-[28px] bg-white p-5 shadow-sm">
        <h2 class="text-[22px] font-bold">
          Собираю поездку
        </h2>

        <div class="mt-6 space-y-4">
          <div
            v-for="step in steps"
            :key="step"
            class="rounded-2xl bg-[#f4f6fb] px-4 py-3 text-[15px]"
          >
            {{ step }}
          </div>

          <div
            v-if="errorMessage"
            class="rounded-2xl bg-[#fff1f2] px-4 py-3 text-[15px] text-[#be123c]"
          >
            {{ errorMessage }}
          </div>
        </div>

        <button
          class="mt-6 w-full rounded-2xl bg-[#009b63] py-4 text-[15px] font-semibold text-white"
          :class="planReady ? '' : 'opacity-50'"
          :disabled="!planReady"
          @click="router.push('/travel/plan')"
        >
          {{ loading ? 'Собираю план...' : 'Посмотреть план' }}
        </button>
      </section>
    </div>
  </main>
</template>
