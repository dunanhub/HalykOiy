export type TravelItem = {
  category: string
  id?: string
  title: string
  details: string
  price: number
  disclaimer?: string
  optional?: boolean
}

export type FamilyMember = {
  role: string
  name?: string | null
  age?: number | null
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
  family_members?: FamilyMember[] | null
  items: TravelItem[]
  total: number
  budget: number
  within_budget: boolean
  bonus: number
  can_book?: boolean
  checklist?: unknown[]
  next_trip?: unknown
}

export type ThinkingStep = {
  type?: 'thinking'
  step: string
  icon: string
  text: string
  status: string
}

export type ClarificationResult = {
  status: 'need_clarification'
  question: string
  quick_replies: string[]
  missing_fields: string[]
  partial_request: Record<string, unknown>
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

export type ContactInfo = {
  name: string
  surname: string
  email: string
  phone: string
}

export const useTravel = () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase

  const pendingMessage = useState<string>('travel:pending-message', () => '')
  const pendingEditMessage = useState<string>('travel:pending-edit-message', () => '')
  const currentPlan = useState<TravelPlan | null>('travel:current-plan', () => null)
  const paymentResult = useState<PaymentResult | null>('travel:payment-result', () => null)
  const contactInfo = useState<ContactInfo | null>('travel:contact', () => null)
  const pendingPartialRequest = useState<Record<string, unknown> | null>('travel:partial-request', () => null)

  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('ru-RU').format(value) + ' ₸'
  }

  const getThinkingSteps = async () => {
    return await $fetch<ThinkingStep[]>(`${apiBase}/api/travel/thinking`)
  }

  const resetTravelDraft = () => {
    currentPlan.value = null
    paymentResult.value = null
    contactInfo.value = null
    pendingPartialRequest.value = null
  }

  const createPlanStream = async (
    message: string,
    onThinking: (step: ThinkingStep) => void,
    partialRequest?: Record<string, unknown> | null,
  ) => {
    const wsBase = apiBase.replace(/^http/, 'ws')

    const result = await new Promise<TravelPlan | ClarificationResult>((resolve, reject) => {
      const socket = new WebSocket(`${wsBase}/ws/travel`)

      socket.onopen = () => {
        socket.send(JSON.stringify({ text: message, partial_request: partialRequest || undefined }))
      }

      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data)

        if (payload.type === 'thinking') {
          onThinking(payload)
          return
        }

        if (payload.type === 'plan_ready') {
          resolve(payload.plan)
          socket.close()
          return
        }

        if (payload.type === 'need_clarification') {
          resolve(payload)
          socket.close()
          return
        }

        if (payload.type === 'error') {
          const reason = payload.reason ? ` ${payload.reason}` : ''
          reject(new Error(`${payload.text || 'Travel planning failed'}${reason}`))
          socket.close()
        }
      }

      socket.onerror = () => {
        reject(new Error('WebSocket connection failed'))
      }
    })

    if ('status' in result && result.status === 'need_clarification') {
      pendingPartialRequest.value = result.partial_request
      return result
    }

    currentPlan.value = result
    pendingPartialRequest.value = null
    paymentResult.value = null

    return result
  }

  const createPlan = async (message: string) => {
    const plan = await $fetch<TravelPlan | ClarificationResult>(`${apiBase}/api/travel/plan`, {
      method: 'POST',
      body: {
        text: message,
        partial_request: pendingPartialRequest.value || undefined,
      },
    })

    if ('status' in plan && plan.status === 'need_clarification') {
      pendingPartialRequest.value = plan.partial_request
      return plan
    }

    currentPlan.value = plan
    pendingPartialRequest.value = null
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
    contactInfo,
    pendingPartialRequest,
    formatPrice,
    getThinkingSteps,
    resetTravelDraft,
    createPlanStream,
    createPlan,
    editPlan,
    payForPlan,
  }
}
