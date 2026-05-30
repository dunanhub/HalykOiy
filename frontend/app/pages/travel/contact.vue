<script setup lang="ts">
import { mdiArrowLeft, mdiAccount, mdiCalendarBlankOutline, mdiChevronLeft, mdiChevronRight, mdiEmail, mdiPhone } from '@mdi/js'
import type { ContactInfo } from '~/composables/useTravel'

const router = useRouter()
const { currentPlan, contactInfo } = useTravel()

const name = ref('')
const surname = ref('')
const email = ref('')
const phone = ref('')
const errors = ref<Record<string, string>>({})
const dobPickerIndex = ref<number | null>(null)
const dobCursor = ref(new Date(new Date().getFullYear() - 8, new Date().getMonth(), 1))

type Companion = { name: string; surname: string; role: string; dob: string }
const companions = ref<Companion[]>([])

onMounted(() => {
  if (!currentPlan.value) {
    router.push('/travel')
    return
  }

  if (contactInfo.value) {
    name.value = contactInfo.value.name
    surname.value = contactInfo.value.surname || ''
    email.value = contactInfo.value.email
    phone.value = formatPhone(contactInfo.value.phone)
  }

  const pax = currentPlan.value.trip.pax || 1
  const members = currentPlan.value.family_members

  if (pax > 1) {
    const count = pax - 1
    companions.value = Array.from({ length: count }, (_, i) => ({
      name: members?.[i]?.name || '',
      surname: '',
      role: members?.[i]?.role || 'взрослый',
      dob: '',
    }))
  }
})

const isChild = (role: string) => ['ребёнок', 'ребенок', 'child', 'kid'].includes(role.toLowerCase())
const phoneDigits = (value: string) => value.replace(/\D/g, '')

const formatPhone = (value: string) => {
  let digits = phoneDigits(value)
  if (!digits) return ''
  if (digits.startsWith('8')) digits = '7' + digits.slice(1)
  if (!digits.startsWith('7')) digits = '7' + digits
  digits = digits.slice(0, 11)

  const rest = digits.slice(1)
  const p1 = rest.slice(0, 3)
  const p2 = rest.slice(3, 6)
  const p3 = rest.slice(6, 10)
  return ['+7', p1, p2, p3].filter(Boolean).join(' ')
}

const onPhoneInput = (event: Event) => {
  phone.value = formatPhone((event.target as HTMLInputElement).value)
}

const MONTHS = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
const WEEKDAYS = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс']

const calendarTitle = computed(() => `${MONTHS[dobCursor.value.getMonth()]} ${dobCursor.value.getFullYear()}`)
const activeDobCompanion = computed(() => {
  if (dobPickerIndex.value === null) return null
  return companions.value[dobPickerIndex.value] || null
})

const calendarDays = computed(() => {
  const year = dobCursor.value.getFullYear()
  const month = dobCursor.value.getMonth()
  const first = new Date(year, month, 1)
  const startOffset = (first.getDay() + 6) % 7
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  return [
    ...Array.from({ length: startOffset }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => new Date(year, month, i + 1)),
  ]
})

const toIsoDate = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const formatDob = (value: string) => {
  if (!value) return 'Выбрать дату'
  const date = new Date(value + 'T00:00:00')
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}

const openDobPicker = (index: number) => {
  dobPickerIndex.value = dobPickerIndex.value === index ? null : index
  const current = companions.value[index]?.dob
  dobCursor.value = current
    ? new Date(current + 'T00:00:00')
    : new Date(new Date().getFullYear() - 8, new Date().getMonth(), 1)
}

const shiftDobMonth = (delta: number) => {
  dobCursor.value = new Date(dobCursor.value.getFullYear(), dobCursor.value.getMonth() + delta, 1)
}

const selectDob = (index: number, date: Date) => {
  companions.value[index].dob = toIsoDate(date)
  dobPickerIndex.value = null
}

const closeDobPicker = () => {
  dobPickerIndex.value = null
}

const validate = () => {
  const e: Record<string, string> = {}
  if (!name.value.trim()) e.name = 'Введите имя'
  if (!surname.value.trim()) e.surname = 'Введите фамилию'
  if (!email.value.trim()) e.email = 'Введите email'
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) e.email = 'Неверный формат email'
  if (!phone.value.trim()) e.phone = 'Введите телефон'
  else {
    const digits = phoneDigits(phone.value)
    if (digits.length !== 11 || !digits.startsWith('7')) e.phone = 'Введите полный номер +7 XXX XXX XXXX'
  }

  companions.value.forEach((c, i) => {
    if (!c.name.trim()) e[`comp_name_${i}`] = 'Введите имя'
    if (!c.surname.trim()) e[`comp_surname_${i}`] = 'Введите фамилию'
    if (isChild(c.role) && !c.dob.trim()) e[`comp_dob_${i}`] = 'Введите дату рождения'
  })

  errors.value = e
  return Object.keys(e).length === 0
}

const proceed = () => {
  if (!validate()) return
  contactInfo.value = {
    name: name.value.trim(),
    surname: surname.value.trim(),
    email: email.value.trim(),
    phone: phone.value.trim(),
  }
  router.push('/travel/payment')
}
</script>

<template>
  <main class="travel-screen">
    <div class="travel-shell flex flex-col">
      <header class="travel-topbar fade-slide">
        <button class="pressable absolute left-0 flex h-9 w-9 items-center justify-center rounded-full bg-white/70 shadow-sm" @click="router.back()">
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiArrowLeft" fill="currentColor" />
          </svg>
        </button>
        <h1 class="text-[18px] font-semibold">Данные пассажиров</h1>
      </header>

      <section class="travel-card travel-hero travel-soft-gradient fade-slide mt-5 p-5">
        <p class="text-[13px] font-semibold text-[#009b63]">Шаг 1 из 2</p>
        <h2 class="mt-2 text-[24px] font-bold">Контактная информация</h2>
        <p class="mt-1 text-[14px] text-[#6b7280]">Нужна для билетов и подтверждения брони</p>
        <div class="mt-4 h-2 rounded-full bg-white/80">
          <div class="h-2 w-1/2 rounded-full bg-[#009b63]" />
        </div>
      </section>

      <!-- Main passenger -->
      <section class="travel-card mt-4 p-5">
        <p class="mb-4 text-[15px] font-bold text-[#202436]">Вы (главный пассажир)</p>

        <div class="space-y-3">
          <div>
            <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Имя</label>
            <div class="travel-field flex items-center gap-3 rounded-2xl px-3 py-2.5">
              <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 text-[#009b63]">
                <path :d="mdiAccount" fill="currentColor" />
              </svg>
              <input v-model="name" type="text" placeholder="Ваше имя" autocomplete="given-name"
                class="flex-1 bg-transparent text-[15px] outline-none placeholder:text-[#9aa3b5]" />
            </div>
            <p v-if="errors.name" class="fade-slide mt-1 text-[12px] text-[#be123c]">{{ errors.name }}</p>
          </div>

          <div>
            <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Фамилия</label>
            <div class="travel-field flex items-center gap-3 rounded-2xl px-3 py-2.5">
              <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 text-[#009b63]">
                <path :d="mdiAccount" fill="currentColor" />
              </svg>
              <input v-model="surname" type="text" placeholder="Ваша фамилия" autocomplete="family-name"
                class="flex-1 bg-transparent text-[15px] outline-none placeholder:text-[#9aa3b5]" />
            </div>
            <p v-if="errors.surname" class="fade-slide mt-1 text-[12px] text-[#be123c]">{{ errors.surname }}</p>
          </div>

          <div>
            <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Email</label>
            <div class="travel-field flex items-center gap-3 rounded-2xl px-3 py-2.5">
              <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 text-[#009b63]">
                <path :d="mdiEmail" fill="currentColor" />
              </svg>
              <input v-model="email" type="email" placeholder="example@mail.com" autocomplete="email"
                class="flex-1 bg-transparent text-[15px] outline-none placeholder:text-[#9aa3b5]" />
            </div>
            <p v-if="errors.email" class="fade-slide mt-1 text-[12px] text-[#be123c]">{{ errors.email }}</p>
          </div>

          <div>
            <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Телефон</label>
            <div class="travel-field flex items-center gap-3 rounded-2xl px-3 py-2.5">
              <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 text-[#009b63]">
                <path :d="mdiPhone" fill="currentColor" />
              </svg>
              <input v-model="phone" type="tel" placeholder="+7 777 777 7777" autocomplete="tel"
                inputmode="numeric" maxlength="15" @input="onPhoneInput"
                class="flex-1 bg-transparent text-[15px] outline-none placeholder:text-[#9aa3b5]" />
            </div>
            <p v-if="errors.phone" class="fade-slide mt-1 text-[12px] text-[#be123c]">{{ errors.phone }}</p>
          </div>
        </div>
      </section>

      <!-- Companions -->
      <section v-if="companions.length > 0" class="mt-4 space-y-3">
        <div
          v-for="(comp, i) in companions"
          :key="i"
          class="travel-card p-5"
        >
          <p class="mb-4 text-[15px] font-bold text-[#202436]">
            {{ comp.role ? (comp.role.charAt(0).toUpperCase() + comp.role.slice(1)) : `Пассажир ${i + 2}` }}
          </p>

          <div class="space-y-3">
            <div>
              <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Имя</label>
              <input v-model="comp.name" type="text" :placeholder="`Имя`"
                class="travel-field w-full rounded-2xl px-3 py-2.5 text-[15px] outline-none placeholder:text-[#9aa3b5]" />
              <p v-if="errors[`comp_name_${i}`]" class="mt-1 text-[12px] text-[#be123c]">{{ errors[`comp_name_${i}`] }}</p>
            </div>

            <div>
              <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Фамилия</label>
              <input v-model="comp.surname" type="text" placeholder="Фамилия"
                class="travel-field w-full rounded-2xl px-3 py-2.5 text-[15px] outline-none placeholder:text-[#9aa3b5]" />
              <p v-if="errors[`comp_surname_${i}`]" class="mt-1 text-[12px] text-[#be123c]">{{ errors[`comp_surname_${i}`] }}</p>
            </div>

            <div v-if="isChild(comp.role)">
              <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Дата рождения</label>
              <div>
                <button
                  type="button"
                  class="travel-field flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[15px] outline-none"
                  @click="openDobPicker(i)"
                >
                  <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 text-[#009b63]">
                    <path :d="mdiCalendarBlankOutline" fill="currentColor" />
                  </svg>
                  <span :class="comp.dob ? 'text-[#202436]' : 'text-[#9aa3b5]'">
                    {{ formatDob(comp.dob) }}
                  </span>
                </button>
              </div>
              <p v-if="errors[`comp_dob_${i}`]" class="mt-1 text-[12px] text-[#be123c]">{{ errors[`comp_dob_${i}`] }}</p>
            </div>
          </div>
        </div>
      </section>

      <Transition name="fade">
        <div
          v-if="dobPickerIndex !== null && activeDobCompanion"
          class="fixed inset-0 z-50 flex items-center justify-center bg-[#202436]/35 px-4 py-6 backdrop-blur-[3px]"
          @click.self="closeDobPicker"
        >
          <div
            class="w-full max-w-[360px] rounded-[26px] border border-[#e7ebf3] bg-white p-4 shadow-[0_24px_70px_rgba(32,36,54,0.28)]"
          >
            <div class="mb-4">
              <p class="text-[12px] font-semibold uppercase tracking-wide text-[#009b63]">Дата рождения</p>
              <p class="mt-1 text-[16px] font-bold text-[#202436]">
                {{ activeDobCompanion.name || 'Пассажир' }}
              </p>
            </div>

            <div class="mb-3 flex items-center justify-between">
              <button type="button" class="pressable rounded-full bg-[#f4f6fb] p-2" @click="shiftDobMonth(-1)">
                <svg viewBox="0 0 24 24" class="h-5 w-5">
                  <path :d="mdiChevronLeft" fill="currentColor" />
                </svg>
              </button>
              <p class="text-[15px] font-bold">{{ calendarTitle }}</p>
              <button type="button" class="pressable rounded-full bg-[#f4f6fb] p-2" @click="shiftDobMonth(1)">
                <svg viewBox="0 0 24 24" class="h-5 w-5">
                  <path :d="mdiChevronRight" fill="currentColor" />
                </svg>
              </button>
            </div>

            <div class="grid grid-cols-7 gap-1 text-center">
              <span
                v-for="day in WEEKDAYS"
                :key="day"
                class="py-1 text-[10px] font-bold text-[#9aa3b5]"
              >
                {{ day }}
              </span>
              <button
                v-for="(day, dayIndex) in calendarDays"
                :key="day ? toIsoDate(day) : `empty-${dayIndex}`"
                type="button"
                class="h-10 rounded-xl text-[13px] font-semibold transition-colors"
                :class="day
                  ? (activeDobCompanion.dob === toIsoDate(day) ? 'bg-[#009b63] text-white shadow-sm' : 'bg-[#f8fafc] text-[#202436] hover:bg-[#eaf8f1]')
                  : 'pointer-events-none opacity-0'"
                @click="day && dobPickerIndex !== null && selectDob(dobPickerIndex, day)"
              >
                {{ day?.getDate() }}
              </button>
            </div>

            <button
              type="button"
              class="travel-secondary-button mt-4 w-full py-3 text-[14px]"
              @click="closeDobPicker"
            >
              Закрыть
            </button>
          </div>
        </div>
      </Transition>

      <div class="mt-4 rounded-[24px] bg-[#eaf8f1] px-4 py-3">
        <p class="text-[13px] text-[#00845f]">
          Билеты и подтверждение брони придут на ваш email.
        </p>
      </div>

      <div class="travel-sticky-action mt-auto">
        <button
          class="travel-primary-button w-full py-4 text-[15px]"
          @click="proceed"
        >
          Перейти к оплате
        </button>
      </div>
    </div>
  </main>
</template>
