<script setup lang="ts">
import { mdiArrowLeft, mdiPlus, mdiMinus } from '@mdi/js'
import type { ClarificationResult, TravelPlan } from '~/composables/useTravel'

const router = useRouter()
const {
  pendingMessage,
  pendingEditMessage,
  pendingPartialRequest,
  currentPlan,
  createPlanStream,
  editPlan,
} = useTravel()

const steps = ref<string[]>([])
const loading = ref(true)
const errorMessage = ref('')
const clarification = ref<ClarificationResult | null>(null)
const planReady = computed(() => Boolean(currentPlan.value) && !loading.value && !errorMessage.value && !clarification.value && !showCustomGroup.value)

// --- Custom group form ---
const showCustomGroup = ref(false)
const customPax = ref(2)

type Member = { role: string; name: string; age: string }
const customMembers = ref<Member[]>([{ role: 'жена', name: '', age: '' }])

const ROLES = ['жена', 'муж', 'девушка', 'парень', 'друг', 'подруга', 'мама', 'папа', 'ребёнок']

watch(customPax, (newPax) => {
  const needed = Math.max(0, newPax - 1)
  while (customMembers.value.length < needed) {
    customMembers.value.push({ role: '', name: '', age: '' })
  }
  customMembers.value = customMembers.value.slice(0, needed)
})

const setPax = (delta: number) => {
  customPax.value = Math.max(1, Math.min(10, customPax.value + delta))
}

const submitCustomGroup = () => {
  const parts: string[] = []
  for (const m of customMembers.value) {
    if (!m.role) continue
    let desc = m.role
    if (m.name.trim()) desc += ` ${m.name.trim()}`
    if (m.role === 'ребёнок' && m.age) desc += ` ${m.age} лет`
    parts.push(desc)
  }

  let message = `нас ${customPax.value} ${paxLabel(customPax.value)}`
  if (parts.length > 0) {
    message += ': ' + parts.join(', ')
  }

  showCustomGroup.value = false
  runPlanning(message)
}

const paxLabel = (n: number) => {
  if (n === 1) return 'человек'
  if (n >= 2 && n <= 4) return 'человека'
  return 'человек'
}
// --- end custom group form ---

const createPlan = (message: string) => createPlanStream(
  message,
  step => {
    if (step.status !== 'done') {
      steps.value.push(`${step.icon} ${step.text}`)
    }
  },
  pendingPartialRequest.value,
)

const handleResult = (result: TravelPlan | ClarificationResult) => {
  if ('status' in result && result.status === 'need_clarification') {
    clarification.value = result
    // When asking about companions — skip quick replies, show group form directly
    const fields = result.missing_fields || []
    if (fields.includes('pax') || fields.includes('family_members')) {
      showCustomGroup.value = true
    }
    return
  }

  clarification.value = null
  steps.value.push('✅ План готов!')
}

const handleReply = (reply: string) => {
  runPlanning(reply)
}

const runPlanning = async (message: string) => {
  loading.value = true
  errorMessage.value = ''
  clarification.value = null
  showCustomGroup.value = false
  steps.value = []

  try {
    const result = await createPlan(message)
    handleResult(result)
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Не удалось собрать план. Проверьте, что backend запущен.'
    if (error instanceof Error) {
      errorMessage.value = error.message
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    if (pendingEditMessage.value) {
      await editPlan(pendingEditMessage.value)
      pendingEditMessage.value = ''
      steps.value.push('✅ План готов!')
    } else {
      const result = await createPlan(pendingMessage.value || 'хочу с семьёй в Астану на выходные, бюджет 150к')
      pendingMessage.value = ''
      handleResult(result)
    }
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Не удалось собрать план. Проверьте, что backend запущен.'
    if (error instanceof Error) {
      errorMessage.value = error.message
    }
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

          <!-- Standard clarification (quick replies) -->
          <div
            v-if="clarification && !showCustomGroup"
            class="rounded-2xl bg-[#eaf8f1] px-4 py-4 text-[15px]"
          >
            <p class="font-semibold text-[#202436]">
              {{ clarification.question }}
            </p>

            <div class="mt-3 grid gap-2">
              <button
                v-for="reply in clarification.quick_replies"
                :key="reply"
                class="rounded-2xl bg-white px-4 py-3 text-left text-[14px] font-semibold text-[#00845f]"
                :disabled="loading"
                @click="handleReply(reply)"
              >
                {{ reply }}
              </button>
            </div>
          </div>

          <!-- Group form — shown directly for companion clarification -->
          <div
            v-if="showCustomGroup"
            class="rounded-2xl bg-[#eaf8f1] px-4 py-4"
          >
            <div class="mb-4">
              <p class="text-[16px] font-bold text-[#202436]">
                Ваша группа
              </p>
            </div>

            <!-- Pax counter -->
            <div class="mb-5">
              <p class="mb-2 text-[13px] text-[#6b7280]">
                Сколько человек едет?
              </p>
              <div class="flex items-center gap-4">
                <button
                  class="flex h-9 w-9 items-center justify-center rounded-full bg-white shadow-sm"
                  @click="setPax(-1)"
                >
                  <svg viewBox="0 0 24 24" class="h-5 w-5 text-[#009b63]">
                    <path :d="mdiMinus" fill="currentColor" />
                  </svg>
                </button>
                <span class="min-w-[2ch] text-center text-[22px] font-bold text-[#202436]">{{ customPax }}</span>
                <button
                  class="flex h-9 w-9 items-center justify-center rounded-full bg-white shadow-sm"
                  @click="setPax(1)"
                >
                  <svg viewBox="0 0 24 24" class="h-5 w-5 text-[#009b63]">
                    <path :d="mdiPlus" fill="currentColor" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Member slots -->
            <div
              v-if="customMembers.length > 0"
              class="mb-4 space-y-4"
            >
              <div
                v-for="(member, i) in customMembers"
                :key="i"
                class="rounded-2xl bg-white p-3"
              >
                <p class="mb-2 text-[13px] font-semibold text-[#6b7280]">
                  Участник {{ i + 1 }}
                </p>

                <!-- Role chips -->
                <div class="mb-3 flex flex-wrap gap-1.5">
                  <button
                    v-for="role in ROLES"
                    :key="role"
                    class="rounded-full px-3 py-1 text-[12px] font-semibold transition-colors"
                    :class="member.role === role
                      ? 'bg-[#009b63] text-white'
                      : 'bg-[#f4f6fb] text-[#202436]'"
                    @click="member.role = role"
                  >
                    {{ role }}
                  </button>
                </div>

                <!-- Name input -->
                <input
                  v-model="member.name"
                  class="mb-2 w-full rounded-xl bg-[#f4f6fb] px-3 py-2 text-[14px] outline-none placeholder:text-[#9aa3b5]"
                  placeholder="Имя (необязательно)"
                >

                <!-- Age input for children -->
                <input
                  v-if="member.role === 'ребёнок'"
                  v-model="member.age"
                  type="number"
                  min="0"
                  max="17"
                  class="w-full rounded-xl bg-[#f4f6fb] px-3 py-2 text-[14px] outline-none placeholder:text-[#9aa3b5]"
                  placeholder="Возраст ребёнка"
                >
              </div>
            </div>

            <button
              class="w-full rounded-2xl bg-[#009b63] py-3.5 text-[15px] font-semibold text-white"
              @click="submitCustomGroup"
            >
              Продолжить
            </button>
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
          {{ loading ? 'Собираю план...' : (clarification || showCustomGroup) ? 'Ответьте на вопрос выше' : 'Посмотреть план' }}
        </button>
      </section>
    </div>
  </main>
</template>
