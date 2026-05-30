<script setup lang="ts">
import { mdiArrowLeft, mdiAccount, mdiEmail, mdiPhone } from '@mdi/js'
import type { ContactInfo } from '~/composables/useTravel'

const router = useRouter()
const { currentPlan, contactInfo } = useTravel()

const name = ref('')
const surname = ref('')
const email = ref('')
const phone = ref('')
const errors = ref<Record<string, string>>({})

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
    phone.value = contactInfo.value.phone
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

const validate = () => {
  const e: Record<string, string> = {}
  if (!name.value.trim()) e.name = 'Введите имя'
  if (!surname.value.trim()) e.surname = 'Введите фамилию'
  if (!email.value.trim()) e.email = 'Введите email'
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) e.email = 'Неверный формат email'
  if (!phone.value.trim()) e.phone = 'Введите телефон'
  else if (!/^[\+\d][\d\s\-\(\)]{6,}$/.test(phone.value)) e.phone = 'Неверный формат'

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
  <main class="min-h-screen bg-[#f4f6fb] text-[#202436]">
    <div class="mx-auto flex min-h-screen max-w-[430px] flex-col bg-[#f4f6fb] px-4 pb-8 pt-4">
      <header class="relative flex items-center justify-center py-3">
        <button class="absolute left-0 flex h-9 w-9 items-center justify-center" @click="router.back()">
          <svg viewBox="0 0 24 24" class="h-6 w-6">
            <path :d="mdiArrowLeft" fill="currentColor" />
          </svg>
        </button>
        <h1 class="text-[18px] font-semibold">Данные пассажиров</h1>
      </header>

      <section class="mt-5 rounded-[28px] bg-white p-5 shadow-sm">
        <p class="text-[13px] font-semibold text-[#009b63]">Шаг 1 из 2</p>
        <h2 class="mt-2 text-[24px] font-bold">Контактная информация</h2>
        <p class="mt-1 text-[14px] text-[#6b7280]">Нужна для билетов и подтверждения брони</p>
      </section>

      <!-- Main passenger -->
      <section class="mt-4 rounded-[28px] bg-white p-5 shadow-sm">
        <p class="mb-4 text-[15px] font-bold text-[#202436]">Вы (главный пассажир)</p>

        <div class="space-y-3">
          <div>
            <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Имя</label>
            <div class="flex items-center gap-3 rounded-2xl bg-[#f4f6fb] px-3 py-2.5">
              <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 text-[#009b63]">
                <path :d="mdiAccount" fill="currentColor" />
              </svg>
              <input v-model="name" type="text" placeholder="Ваше имя" autocomplete="given-name"
                class="flex-1 bg-transparent text-[15px] outline-none placeholder:text-[#9aa3b5]" />
            </div>
            <p v-if="errors.name" class="mt-1 text-[12px] text-[#be123c]">{{ errors.name }}</p>
          </div>

          <div>
            <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Фамилия</label>
            <div class="flex items-center gap-3 rounded-2xl bg-[#f4f6fb] px-3 py-2.5">
              <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 text-[#009b63]">
                <path :d="mdiAccount" fill="currentColor" />
              </svg>
              <input v-model="surname" type="text" placeholder="Ваша фамилия" autocomplete="family-name"
                class="flex-1 bg-transparent text-[15px] outline-none placeholder:text-[#9aa3b5]" />
            </div>
            <p v-if="errors.surname" class="mt-1 text-[12px] text-[#be123c]">{{ errors.surname }}</p>
          </div>

          <div>
            <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Email</label>
            <div class="flex items-center gap-3 rounded-2xl bg-[#f4f6fb] px-3 py-2.5">
              <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 text-[#009b63]">
                <path :d="mdiEmail" fill="currentColor" />
              </svg>
              <input v-model="email" type="email" placeholder="example@mail.com" autocomplete="email"
                class="flex-1 bg-transparent text-[15px] outline-none placeholder:text-[#9aa3b5]" />
            </div>
            <p v-if="errors.email" class="mt-1 text-[12px] text-[#be123c]">{{ errors.email }}</p>
          </div>

          <div>
            <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Телефон</label>
            <div class="flex items-center gap-3 rounded-2xl bg-[#f4f6fb] px-3 py-2.5">
              <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 text-[#009b63]">
                <path :d="mdiPhone" fill="currentColor" />
              </svg>
              <input v-model="phone" type="tel" placeholder="+7 777 000 00 00" autocomplete="tel"
                class="flex-1 bg-transparent text-[15px] outline-none placeholder:text-[#9aa3b5]" />
            </div>
            <p v-if="errors.phone" class="mt-1 text-[12px] text-[#be123c]">{{ errors.phone }}</p>
          </div>
        </div>
      </section>

      <!-- Companions -->
      <section v-if="companions.length > 0" class="mt-4 space-y-3">
        <div
          v-for="(comp, i) in companions"
          :key="i"
          class="rounded-[28px] bg-white p-5 shadow-sm"
        >
          <p class="mb-4 text-[15px] font-bold text-[#202436]">
            {{ comp.role ? (comp.role.charAt(0).toUpperCase() + comp.role.slice(1)) : `Пассажир ${i + 2}` }}
          </p>

          <div class="space-y-3">
            <div>
              <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Имя</label>
              <input v-model="comp.name" type="text" :placeholder="`Имя`"
                class="w-full rounded-2xl bg-[#f4f6fb] px-3 py-2.5 text-[15px] outline-none placeholder:text-[#9aa3b5]" />
              <p v-if="errors[`comp_name_${i}`]" class="mt-1 text-[12px] text-[#be123c]">{{ errors[`comp_name_${i}`] }}</p>
            </div>

            <div>
              <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Фамилия</label>
              <input v-model="comp.surname" type="text" placeholder="Фамилия"
                class="w-full rounded-2xl bg-[#f4f6fb] px-3 py-2.5 text-[15px] outline-none placeholder:text-[#9aa3b5]" />
              <p v-if="errors[`comp_surname_${i}`]" class="mt-1 text-[12px] text-[#be123c]">{{ errors[`comp_surname_${i}`] }}</p>
            </div>

            <div v-if="isChild(comp.role)">
              <label class="mb-1 block text-[12px] font-semibold text-[#6b7280]">Дата рождения</label>
              <input v-model="comp.dob" type="date"
                class="w-full rounded-2xl bg-[#f4f6fb] px-3 py-2.5 text-[15px] outline-none" />
              <p v-if="errors[`comp_dob_${i}`]" class="mt-1 text-[12px] text-[#be123c]">{{ errors[`comp_dob_${i}`] }}</p>
            </div>
          </div>
        </div>
      </section>

      <div class="mt-4 rounded-[24px] bg-[#eaf8f1] px-4 py-3">
        <p class="text-[13px] text-[#00845f]">
          Билеты и подтверждение брони придут на ваш email.
        </p>
      </div>

      <div class="mt-auto pt-5">
        <button
          class="w-full rounded-2xl bg-[#009b63] py-4 text-[15px] font-semibold text-white shadow-sm"
          @click="proceed"
        >
          Перейти к оплате
        </button>
      </div>
    </div>
  </main>
</template>
