import Calendar from 'react-calendar'
import 'react-calendar/dist/Calendar.css'
import { formatDate } from '../utils.js'

export default function CalendarSidebar({ selectedDate, entryDates, maxDate, onDateChange }) {
  const entryDateSet = new Set(entryDates)

  const [maxYear, maxMonth, maxDay] = maxDate.split('-').map(Number)
  const maxDateObj = new Date(maxYear, maxMonth - 1, maxDay)

  const [selYear, selMonth, selDay] = selectedDate.split('-').map(Number)
  const calendarValue = new Date(selYear, selMonth - 1, selDay)

  const tileClassName = ({ date }) => {
    return entryDateSet.has(formatDate(date)) ? 'has-entry' : null
  }

  const handleChange = (date) => {
    onDateChange(formatDate(date))
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-today">
        <button className="today-btn" onClick={() => onDateChange(maxDate)}>
          Today
        </button>
      </div>
      <Calendar
        onChange={handleChange}
        value={calendarValue}
        maxDate={maxDateObj}
        tileClassName={tileClassName}
        calendarType="gregory"
      />
    </aside>
  )
}
