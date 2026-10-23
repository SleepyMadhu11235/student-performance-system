// Client-side validation bounds for the 5 model features, matching the
// backend's PredictRequestSchema exactly. Not mock data: real UI config.

export const FEATURE_LIMITS = {
  attendance_rate: { min: 0, max: 100, step: 1, unit: '%', label: 'Attendance Rate' },
  midterm_1: { min: 0, max: 100, step: 1, unit: 'pts', label: 'Midterm 1' },
  midterm_2: { min: 0, max: 100, step: 1, unit: 'pts', label: 'Midterm 2' },
  assignments_avg: { min: 0, max: 100, step: 1, unit: '%', label: 'Assignments Avg.' },
  study_hours_weekly: { min: 0, max: 30, step: 0.5, unit: 'hrs/wk', label: 'Weekly Study Hours' },
}
