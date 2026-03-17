const RUSSIAN_MONTHS = [
  "января", "февраля", "марта", "апреля", "мая", "июня",
  "июля", "августа", "сентября", "октября", "ноября", "декабря",
];

/**
 * Format price from kopecks to display string.
 * @example formatPrice(250000) => "2 500 ₽"
 * @example formatPrice(0) => "0 ₽"
 */
export function formatPrice(kopecks: number): string {
  const rubles = Math.floor(kopecks / 100);
  const formatted = rubles.toString().replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0");
  return `${formatted} \u20BD`;
}

/**
 * Format duration in minutes to human-readable Russian string.
 * @example formatDuration(60) => "1 ч"
 * @example formatDuration(90) => "1 ч 30 мин"
 * @example formatDuration(30) => "30 мин"
 */
export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours > 0 && mins > 0) {
    return `${hours} ч ${mins} мин`;
  }
  if (hours > 0) {
    return `${hours} ч`;
  }
  return `${mins} мин`;
}

/**
 * Format date to Russian locale string.
 * @example formatDate("2026-03-25") => "25 марта 2026"
 * @example formatDate(new Date(2026, 2, 25)) => "25 марта 2026"
 */
export function formatDate(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date + "T00:00:00") : date;
  const day = d.getDate();
  const month = RUSSIAN_MONTHS[d.getMonth()];
  const year = d.getFullYear();
  return `${day} ${month} ${year}`;
}

/**
 * Format time string for display.
 * @example formatTime("14:00") => "14:00"
 * @example formatTime("9:30") => "9:30"
 */
export function formatTime(time: string): string {
  return time;
}
