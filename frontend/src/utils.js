export function addDays(dateStr, n) {
  const [year, month, day] = dateStr.split('-').map(Number)
  const date = new Date(year, month - 1, day + n)
  return formatDate(date)
}

export function formatDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// TNG-style stardate. Season 1 (2364 in-universe / 1987 real) opened at ~41000.
// Each real year advances by 1000 units.
export function toStardate(dateStr) {
  const [year, month, day] = dateStr.split('-').map(Number)
  const startOfYear = new Date(year, 0, 1)
  const thisDay    = new Date(year, month - 1, day)
  const dayOfYear  = Math.floor((thisDay - startOfYear) / 86_400_000) + 1
  const daysInYear = (year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)) ? 366 : 365
  const stardate   = 41000 + (year - 1987) * 1000 + (dayOfYear / daysInYear) * 1000
  return stardate.toFixed(1)
}
