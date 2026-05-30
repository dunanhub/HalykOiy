<script setup lang="ts">
import { mdiAccountGroupOutline, mdiArrowLeft, mdiBed, mdiMapMarkerPath, mdiPencilOutline, mdiSend } from '@mdi/js'

const router = useRouter()
const { currentPlan, editPlan } = useTravel()

const editMessage = ref('')
const saving = ref(false)
const quickEdits = ['убрать ресторан', 'добавить активность', 'поменять отель']

const nightsWord = (n: number) => n === 1 ? 'ночь' : (n >= 2 && n <= 4) ? 'ночи' : 'ночей'

onMounted(() => {
  if (!currentPlan.value) {
    router.push('/travel')
  }
})

const submitEdit = async () => {
  if (!editMessage.value.trim() || !currentPlan.value) return
  saving.value = true
  try {
    await editPlan(editMessage.value.trim())
    router.push('/travel/plan')
  } finally {
    saving.value = false
  }
}

const useQuickEdit = (text: string) => {
  editMessage.value = editMessage.value
    ? `${editMessage.value}, ${text}`
    : text
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
        <h1 class="text-[18px] font-semibold">Изменить план</h1>
      </header>

      <section class="travel-card travel-hero travel-soft-gradient fade-slide mt-6 p-5">
        <div class="flex items-start gap-3">
          <div class="travel-icon-bubble h-12 w-12 shrink-0">
            <svg viewBox="0 0 24 24" class="h-7 w-7">
              <path :d="mdiPencilOutline" fill="currentColor" />
            </svg>
          </div>
          <div>
            <h2 class="text-[24px] font-bold leading-tight">Как обновить поездку?</h2>
            <p class="mt-2 text-[14px] leading-6 text-[#6b7280]">
              Напишите правку обычным текстом, а мы пересоберём план.
            </p>
          </div>
        </div>

        <div v-if="currentPlan" class="mt-4 rounded-[22px] border border-[#e7ebf3] bg-white/85 p-4">
          <p class="text-[12px] font-bold uppercase tracking-[0.08em] text-[#9aa3b5]">Текущий план</p>
          <div class="mt-3 flex items-center gap-2">
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-[#009b63]">
              <path :d="mdiMapMarkerPath" fill="currentColor" />
            </svg>
            <p class="text-[16px] font-bold text-[#202436]">
              {{ currentPlan.trip.from }} → {{ currentPlan.trip.to }}
            </p>
          </div>
          <div class="mt-3 flex flex-wrap gap-2">
            <span class="inline-flex items-center gap-1.5 rounded-full bg-[#eaf8f1] px-3 py-1.5 text-[12px] font-semibold text-[#00845f]">
              <svg viewBox="0 0 24 24" class="h-4 w-4">
                <path :d="mdiAccountGroupOutline" fill="currentColor" />
              </svg>
              {{ currentPlan.trip.pax }} чел
            </span>
            <span class="inline-flex items-center gap-1.5 rounded-full bg-[#f4f6fb] px-3 py-1.5 text-[12px] font-semibold text-[#6b7280]">
              <svg viewBox="0 0 24 24" class="h-4 w-4">
                <path :d="mdiBed" fill="currentColor" />
              </svg>
              {{ currentPlan.trip.nights }} {{ nightsWord(currentPlan.trip.nights) }}
            </span>
            <span v-if="currentPlan.trip.dates" class="rounded-full bg-[#f4f6fb] px-3 py-1.5 text-[12px] font-semibold text-[#6b7280]">
              {{ currentPlan.trip.dates }}
            </span>
          </div>
        </div>

        <div class="mt-4 flex flex-wrap gap-2">
          <button
            v-for="quick in quickEdits"
            :key="quick"
            type="button"
            class="travel-chip pressable px-3 py-2"
            @click="useQuickEdit(quick)"
          >
            {{ quick }}
          </button>
        </div>

        <div class="mt-4 rounded-[20px] bg-[#f4f6fb] px-4 py-3 text-[13px] leading-5 text-[#7b8190]">
          Например: хочу самый дорогой отель или добавь семейную активность вечером.
        </div>
      </section>

      <div class="flex-1" />

      <form
        class="travel-input-bar mt-4 flex items-center gap-3 p-3"
        @submit.prevent="submitEdit"
      >
        <input
          v-model="editMessage"
          class="min-w-0 flex-1 bg-transparent px-2 text-[15px] outline-none placeholder:text-[#9aa3b5]"
          placeholder="Напишите изменение..."
        >
        <button
          type="submit"
          class="travel-primary-button flex h-11 w-11 items-center justify-center rounded-full"
          :disabled="!editMessage.trim() || saving"
        >
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiSend" fill="currentColor" />
          </svg>
        </button>
      </form>
    </div>
  </main>
</template>
