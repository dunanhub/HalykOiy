<script setup lang="ts">
import {
  mdiArrowLeft,
  mdiPlus,
  mdiMinus,
  mdiMagnify,
  mdiDatabaseSearch,
  mdiCheckCircleOutline,
  mdiBrain,
  mdiAirplaneSearch,
  mdiBed,
  mdiShieldCheck,
  mdiMedicalBag,
  mdiSilverwareForkKnife,
  mdiCalculatorVariant,
  mdiInformationOutline,
  mdiAccountGroupOutline,
} from '@mdi/js'
import type { ClarificationResult, ThinkingStep, TravelPlan } from '~/composables/useTravel'

const router = useRouter()
const {
  pendingMessage,
  pendingEditMessage,
  pendingPartialRequest,
  currentPlan,
  createPlanStream,
  editPlan,
} = useTravel()

const steps = ref<ThinkingStep[]>([])
const loading = ref(true)
const errorMessage = ref('')
const clarification = ref<ClarificationResult | null>(null)
const showDatePicker = ref(false)
const datePickerValue = ref('')
const planReady = computed(() =>
  Boolean(currentPlan.value) && !loading.value && !errorMessage.value &&
  !clarification.value && !showCustomGroup.value && !showDatePicker.value
)

const iconByStep: Record<string, string> = {
  extract: mdiMagnify,
  fetch: mdiDatabaseSearch,
  select: mdiBrain,
  flights: mdiAirplaneSearch,
  flight: mdiAirplaneSearch,
  hotel: mdiBed,
  insurance: mdiShieldCheck,
  pharmacy: mdiMedicalBag,
  restaurant: mdiSilverwareForkKnife,
  budget: mdiCalculatorVariant,
  ready: mdiCheckCircleOutline,
}

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
      steps.value.push(step)
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
  steps.value.push({
    step: 'ready',
    icon: '',
    text: 'План готов',
    status: 'done',
  })
}

const handleReply = (reply: string) => {
  if (reply === 'Выбрать дату') {
    showDatePicker.value = true
    return
  }
  showDatePicker.value = false
  runPlanning(reply)
}

const submitDate = () => {
  if (!datePickerValue.value) return
  const d = new Date(datePickerValue.value + 'T00:00:00')
  const months = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']
  const msg = `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`
  showDatePicker.value = false
  datePickerValue.value = ''
  runPlanning(msg)
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
      steps.value.push({
        step: 'ready',
        icon: '',
        text: 'План готов',
        status: 'done',
      })
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
  <main class="travel-screen">
    <div class="travel-shell">
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
          AI думает
        </h1>
      </header>

      <section class="travel-card travel-soft-gradient fade-slide mt-6 p-5">
        <div class="flex items-center gap-3">
          <div
            class="travel-icon-bubble h-12 w-12 text-[22px]"
            :class="loading ? 'travel-pulse' : ''"
          >
            <svg viewBox="0 0 24 24" class="h-7 w-7">
              <path :d="mdiBrain" fill="currentColor" />
            </svg>
          </div>
          <div>
            <h2 class="text-[22px] font-bold">Собираю поездку</h2>
            <p class="mt-1 text-[13px] text-[#6b7280]">
              Проверяю рейсы, отели, бюджет и бонусы
            </p>
          </div>
        </div>

        <div class="travel-timeline mt-6 space-y-4">
          <TransitionGroup name="travel-step" tag="div" class="space-y-4">
          <div
            v-for="step in steps"
            :key="`${step.step}:${step.text}`"
            class="travel-timeline-item"
          >
            <div class="travel-step-dot">
              <svg viewBox="0 0 24 24" class="h-5 w-5 text-[#00845f]">
                <path :d="iconByStep[step.step] || mdiInformationOutline" fill="currentColor" />
              </svg>
            </div>
            <div class="flex-1 rounded-2xl bg-[#f4f6fb] px-4 py-3 text-[15px] leading-6">
              {{ step.text }}
            </div>
          </div>
          </TransitionGroup>

          <!-- Standard clarification (quick replies) -->
          <div
            v-if="clarification && !showCustomGroup"
            class="travel-card pop-in bg-[#eaf8f1] px-4 py-4 text-[15px]"
          >
            <p class="font-semibold text-[#202436]">
              {{ clarification.question }}
            </p>

            <div class="mt-3 grid gap-2">
              <button
                v-for="reply in clarification.quick_replies"
                :key="reply"
                class="pressable rounded-2xl bg-white px-4 py-3 text-left text-[14px] font-semibold text-[#00845f] shadow-sm"
                :disabled="loading"
                @click="handleReply(reply)"
              >
                {{ reply }}
              </button>
            </div>
          </div>

          <!-- Date picker — shown when user clicks "Выбрать дату" -->
          <div
            v-if="showDatePicker"
            class="travel-card pop-in bg-[#eaf8f1] px-4 py-4"
          >
            <p class="mb-3 text-[15px] font-semibold text-[#202436]">
              Выберите дату поездки
            </p>
            <input
              v-model="datePickerValue"
              type="date"
              class="travel-field w-full rounded-xl bg-white px-3 py-2.5 text-[14px] outline-none"
            >
            <button
              class="travel-primary-button mt-3 w-full py-3 text-[14px]"
              :disabled="!datePickerValue"
              @click="submitDate"
            >
              Подтвердить
            </button>
          </div>

          <!-- Group form — shown directly for companion clarification -->
          <div
            v-if="showCustomGroup"
            class="travel-card pop-in bg-white px-4 py-4"
          >
            <div class="mb-4 flex items-start gap-3">
              <div class="travel-icon-bubble h-11 w-11 shrink-0">
                <svg viewBox="0 0 24 24" class="h-6 w-6">
                  <path :d="mdiAccountGroupOutline" fill="currentColor" />
                </svg>
              </div>
              <div>
                <p class="text-[17px] font-bold text-[#202436]">Ваша группа</p>
                <p class="mt-1 text-[13px] leading-5 text-[#6b7280]">
                  Уточните состав, чтобы план был точнее.
                </p>
              </div>
            </div>

            <!-- Pax counter -->
            <div class="mb-5 rounded-[22px] bg-[#f4f6fb] px-4 py-4">
              <p class="mb-3 text-center text-[13px] font-semibold text-[#6b7280]">
                Сколько человек едет?
              </p>
              <div class="flex items-center justify-center gap-5">
                <button
                  class="pressable flex h-9 w-9 items-center justify-center rounded-full bg-white shadow-sm"
                  @click="setPax(-1)"
                >
                  <svg viewBox="0 0 24 24" class="h-5 w-5 text-[#009b63]">
                    <path :d="mdiMinus" fill="currentColor" />
                  </svg>
                </button>
                <div class="min-w-[76px] text-center">
                  <p class="text-[28px] font-bold leading-none text-[#202436]">{{ customPax }}</p>
                  <p class="mt-1 text-[11px] font-semibold text-[#9aa3b5]">включая вас</p>
                </div>
                <button
                  class="pressable flex h-9 w-9 items-center justify-center rounded-full bg-white shadow-sm"
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
                class="rounded-[22px] border border-[#edf0f5] bg-[#fbfcfd] p-3"
              >
                <div class="mb-3 flex items-center justify-between">
                  <p class="text-[13px] font-semibold text-[#6b7280]">
                    Участник {{ i + 1 }}
                  </p>
                  <span class="rounded-full bg-white px-2 py-1 text-[11px] font-semibold text-[#9aa3b5]">
                    кроме вас
                  </span>
                </div>

                <!-- Role chips -->
                <div class="mb-3 flex flex-wrap gap-1.5">
                  <button
                    v-for="role in ROLES"
                    :key="role"
                    class="pressable rounded-full border px-3 py-1 text-[12px] font-semibold transition-colors"
                    :class="member.role === role
                      ? 'border-[#009b63] bg-[#009b63] text-white'
                      : 'border-[#edf0f5] bg-white text-[#202436]'"
                    @click="member.role = role"
                  >
                    {{ role }}
                  </button>
                </div>

                <!-- Name input -->
                <input
                  v-model="member.name"
                  class="travel-field mb-2 w-full rounded-xl px-3 py-2 text-[14px] outline-none placeholder:text-[#9aa3b5]"
                  placeholder="Имя (необязательно)"
                >

                <!-- Age input for children -->
                <input
                  v-if="member.role === 'ребёнок'"
                  v-model="member.age"
                  type="number"
                  min="0"
                  max="17"
                  class="travel-field w-full rounded-xl px-3 py-2 text-[14px] outline-none placeholder:text-[#9aa3b5]"
                  placeholder="Возраст ребёнка"
                >
              </div>
            </div>

            <button
              class="travel-primary-button w-full py-3.5 text-[15px]"
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
          v-if="!clarification && !showCustomGroup && !showDatePicker"
          class="travel-primary-button mt-6 w-full py-4 text-[15px]"
          :disabled="!planReady"
          @click="router.push('/travel/plan')"
        >
          {{ loading ? 'Собираю план...' : 'Посмотреть план' }}
        </button>
      </section>
    </div>
  </main>
</template>
