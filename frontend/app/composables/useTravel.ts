export type TravelItem = {
  category: string
  title: string
  details: string
  price: number
}

export type TravelPlan = {
  plan_id: string
  trip: {
    from: string
    to: string
    dates: string
    nights: number
    pax: number
    type: string
  }
  items: TravelItem[]
  total: number
  budget: number
  within_budget: boolean
  bonus: number
}

export type ThinkingStep = {
  step: string
  icon: string
  text: string
  status: string
}

export type PaymentResult = {
  success: boolean
  provider: string
  transaction_id: string
  plan_id: string
  currency: string
  total: number
  bonus: number
  message: string
}

export const useTravel = () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase

  const pendingMessage = useState<string>('travel:pending-message', () => '')
  const pendingEditMessage = useState<string>('travel:pending-edit-message', () => '')
  const currentPlan = useState<TravelPlan | null>('travel:current-plan', () => null)
  const paymentResult = useState<PaymentResult | null>('travel:payment-result', () => null)

  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('ru-RU').format(value) + ' ₸'
  }

  const getThinkingSteps = async () => {
    return await $fetch<ThinkingStep[]>(`${apiBase}/api/travel/thinking`)
  }

  const createPlan = async (message: string) => {
    const plan = await $fetch<TravelPlan>(`${apiBase}/api/travel/plan`, {
      method: 'POST',
      body: { message },
    })

    currentPlan.value = plan
    paymentResult.value = null

    return plan
  }

  const editPlan = async (message: string) => {
    if (!currentPlan.value) {
      throw new Error('Travel plan is missing')
    }

    const plan = await $fetch<TravelPlan>(`${apiBase}/api/travel/edit`, {
      method: 'POST',
      body: {
        plan: currentPlan.value,
        message,
      },
    })

    currentPlan.value = plan
    paymentResult.value = null

    return plan
  }

  const payForPlan = async () => {
    if (!currentPlan.value) {
      throw new Error('Travel plan is missing')
    }

    const result = await $fetch<PaymentResult>(`${apiBase}/api/pay/`, {
      method: 'POST',
      body: {
        plan_id: currentPlan.value.plan_id,
        total: currentPlan.value.total,
        items: currentPlan.value.items,
      },
    })

    paymentResult.value = result

    return result
  }

  return {
    pendingMessage,
    pendingEditMessage,
    currentPlan,
    paymentResult,
    formatPrice,
    getThinkingSteps,
    createPlan,
    editPlan,
    payForPlan,
  }
}
