import {
  mdiCreditCardOutline,
  mdiPiggyBankOutline,
  mdiCashMultiple,
  mdiShoppingOutline,
  mdiAirplane,
  mdiShieldCheckOutline,
  mdiMovieOpenOutline,
  mdiQrcode,
  mdiHomeOutline,
  mdiCar,
  mdiMedicalBag,
  mdiSilverwareForkKnife,
  mdiMessageTextOutline,
  mdiPhoneOutline,
  mdiMapMarkerOutline,
  mdiInformationOutline,
  mdiPlusThick,
  mdiCurrencyUsd
} from '@mdi/js'

export const useServices = () => {
  const topServices = [
    { title: 'Карты', icon: mdiCreditCardOutline },
    { title: 'Депозиты', icon: mdiPiggyBankOutline },
    { title: 'Кредиты', icon: mdiCashMultiple },
    { title: 'Рассрочка', icon: mdiShoppingOutline },
    { title: 'Маркет', icon: mdiShoppingOutline },
    { title: 'Travel', icon: mdiAirplane },
    { title: 'Страховка', icon: mdiShieldCheckOutline },
    { title: 'Kino.kz', icon: mdiMovieOpenOutline },
    { title: 'Halyk+', icon: mdiCurrencyUsd },
    { title: 'Госуслуги', icon: mdiHomeOutline },
    { title: 'Invest', icon: mdiCashMultiple },
    { title: 'QR', icon: mdiQrcode }
  ]

  const mainServices = [
    { title: 'Halyk FX', icon: mdiCurrencyUsd },
    { title: 'Airba fresh', icon: mdiHomeOutline },
    { title: 'Аптека', icon: mdiPlusThick },
    { title: 'Рестораны', icon: mdiSilverwareForkKnife },
    { title: 'inDrive', icon: mdiCar }
  ]

  const services = [
    { title: 'Курсы вал...', icon: mdiCurrencyUsd },
    { title: 'Halyk Easy', icon: mdiCashMultiple },
    { title: 'Аптека', icon: mdiPlusThick },
    { title: 'Рестораны', icon: mdiSilverwareForkKnife },
    { title: 'Kundelik pro', icon: mdiInformationOutline },
    { title: 'Airba fresh', icon: mdiHomeOutline },
    { title: 'Halyk FX', icon: mdiCurrencyUsd },
    { title: 'inDrive', icon: mdiCar },
    { title: 'Mektep Me...', icon: mdiHomeOutline },
    { title: 'Детям', icon: mdiPiggyBankOutline }
  ]

  const personal = [
    { title: 'Мое авто', icon: mdiCar },
    { title: 'Мой дом', icon: mdiHomeOutline },
    { title: 'Здоровье', icon: mdiMedicalBag },
    { title: 'Мой QR', icon: mdiQrcode }
  ]

  const support = [
    { title: 'Написать', icon: mdiMessageTextOutline },
    { title: 'Позвонить', icon: mdiPhoneOutline },
    { title: 'Halyk Map', icon: mdiMapMarkerOutline },
    { title: 'Инфо', icon: mdiInformationOutline }
  ]

  return {
    topServices,
    mainServices,
    services,
    personal,
    support
  }
}