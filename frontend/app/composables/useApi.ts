const API_BASE_URL = 'http://localhost:8000'

export const useApi = () => {
  const getFlights = async () => {
    return await $fetch(`${API_BASE_URL}/api/flights/`, {
      params: {
        from_: 'ALA',
        to: 'NQZ',
        date: '2026-07-01',
        pax: 4
      }
    })
  }

  const getHotels = async () => {
    return await $fetch(`${API_BASE_URL}/api/hotels/`, {
      params: {
        city: 'Astana',
        checkin: '2026-07-01',
        nights: 2,
        family: true
      }
    })
  }

  return {
    getFlights,
    getHotels
  }
}