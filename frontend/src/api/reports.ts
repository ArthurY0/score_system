import http from './http'

export function downloadTranscriptPdf(params: {
  student_id: number
  semester_id: number
}) {
  return http.get('/reports/transcript/pdf', {
    params,
    responseType: 'blob',
  })
}

export function downloadBatchTranscriptPdf(data: {
  class_id: number
  semester_id: number
}) {
  return http.post('/reports/transcript/pdf/batch', data, {
    responseType: 'blob',
  })
}

export function downloadClassSummaryExcel(params: {
  class_id: number
  semester_id: number
}) {
  return http.get('/reports/class-summary/excel', {
    params,
    responseType: 'blob',
  })
}

export function downloadGradeRankingExcel(params: {
  grade_id: number
  semester_id: number
}) {
  return http.get('/reports/grade-ranking/excel', {
    params,
    responseType: 'blob',
  })
}

export function downloadStudentScoresExcel(params: {
  student_id: number
}) {
  return http.get('/reports/student-scores/excel', {
    params,
    responseType: 'blob',
  })
}
