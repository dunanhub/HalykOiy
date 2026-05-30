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

export type ItineraryItem = {
  type: string
  icon: string
  title: string
  details?: string
}

export type ItineraryDay = {
  day: number
  date: string | null
  title: string
  items: ItineraryItem[]
  weather: { temp: number | null; description: string } | null
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
  itinerary?: ItineraryDay[] | null
  start_date?: string | null
  end_date?: string | null
  days?: number | null
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

export type HistoryEntry = {
  plan_id: string
  title: string
  description: string
  total: number
  saved_at: string
  plan: TravelPlan
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

const HISTORY_KEY = 'halyk:plan-history'
const ACTIVE_TRIP_KEY = 'halyk:active-dashboard-trip'
const COMPLETED_TRIPS_KEY = 'halyk:completed-dashboard-trips'

const _readHistory = (): HistoryEntry[] => {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  } catch {
    return []
  }
}

const _writeHistory = (entries: HistoryEntry[]) => {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(entries.slice(0, 15)))
  } catch {}
}

const _readCompletedTripIds = (): string[] => {
  if (typeof window === 'undefined') return []
  try {
    const parsed = JSON.parse(localStorage.getItem(COMPLETED_TRIPS_KEY) || '[]')
    return Array.isArray(parsed) ? parsed.filter(Boolean) : []
  } catch {
    return []
  }
}

const _writeCompletedTripIds = (ids: string[]) => {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(COMPLETED_TRIPS_KEY, JSON.stringify(Array.from(new Set(ids))))
  } catch {}
}

const _readActiveTripId = (): string | null => {
  if (typeof window === 'undefined') return null
  try {
    return localStorage.getItem(ACTIVE_TRIP_KEY)
  } catch {
    return null
  }
}

const _writeActiveTripId = (planId: string | null) => {
  if (typeof window === 'undefined') return
  try {
    if (planId) {
      localStorage.setItem(ACTIVE_TRIP_KEY, planId)
    } else {
      localStorage.removeItem(ACTIVE_TRIP_KEY)
    }
  } catch {}
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
  const planHistory = useState<HistoryEntry[]>('travel:history', () => [])
  const activeTrip = useState<string | null>('travel:active-dashboard-trip', () => null)
  const completedTripIds = useState<string[]>('travel:completed-dashboard-trips', () => [])

  const loadHistory = () => {
    planHistory.value = _readHistory()
  }

  const loadDashboardState = () => {
    activeTrip.value = _readActiveTripId()
    completedTripIds.value = _readCompletedTripIds()
  }

  const pushToHistory = (plan: TravelPlan) => {
    const entry: HistoryEntry = {
      plan_id: plan.plan_id,
      title: `${plan.trip.from} → ${plan.trip.to}`,
      description: [plan.trip.dates, `${plan.trip.pax} чел`].filter(Boolean).join(' · '),
      total: plan.total,
      saved_at: new Date().toISOString(),
      plan,
    }
    const existing = _readHistory()
    const updated = [entry, ...existing.filter(e => e.plan_id !== plan.plan_id)].slice(0, 15)
    _writeHistory(updated)
    planHistory.value = updated
  }

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

  const activateDashboardTrip = (plan: TravelPlan) => {
    activeTrip.value = plan.plan_id
    _writeActiveTripId(plan.plan_id)
    completedTripIds.value = completedTripIds.value.filter(id => id !== plan.plan_id)
    _writeCompletedTripIds(completedTripIds.value)
    pushToHistory(plan)
  }

  const completeDashboardTrip = (planId: string) => {
    completedTripIds.value = Array.from(new Set([...completedTripIds.value, planId]))
    _writeCompletedTripIds(completedTripIds.value)
    if (activeTrip.value === planId) {
      activeTrip.value = null
      _writeActiveTripId(null)
    }
  }

  const isTripExpired = (plan: TravelPlan | null) => {
    if (!plan) return false
    const date =
      plan.end_date ||
      [...(plan.itinerary || [])].reverse().find(day => Boolean(day.date))?.date ||
      null
    if (!date) return false

    const end = new Date(date + 'T00:00:00')
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return end.getTime() < today.getTime()
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
    pushToHistory(result)

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
    pushToHistory(plan)

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
    pushToHistory(plan)

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
    activateDashboardTrip(currentPlan.value)

    return result
  }

  return {
    pendingMessage,
    pendingEditMessage,
    currentPlan,
    paymentResult,
    contactInfo,
    pendingPartialRequest,
    planHistory,
    activeTrip,
    completedTripIds,
    formatPrice,
    getThinkingSteps,
    resetTravelDraft,
    loadHistory,
    loadDashboardState,
    activateDashboardTrip,
    completeDashboardTrip,
    isTripExpired,
    createPlanStream,
    createPlan,
    editPlan,
    payForPlan,
  }
}
