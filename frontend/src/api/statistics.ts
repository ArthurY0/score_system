import http from './http'

// ── Types ───────────────────────────────────────────────────────────────────

export interface ScoreDistributionBucket {
  range: string
  count: number
}

export interface ClassCourseStatistics {
  class_id: number
  class_name: string
  course_id: number
  course_name: string
  semester_id: number
  student_count: number
  avg_score: number
  max_score: number
  min_score: number
  ultra_low_rate: number
  low_rate: number
  pass_rate: number
  good_rate: number
  excellent_rate: number
  distribution: ScoreDistributionBucket[]
}

export interface ClassRankingItem {
  rank: number
  student_id: number
  student_no: string
  student_name: string
  score: number
}

export interface ClassRankingResponse {
  items: ClassRankingItem[]
  total: number
  page: number
  page_size: number
}

export interface GradeRankingSubjectScore {
  course_id: number
  course_name: string
  score: number
}

export interface GradeRankingItem {
  rank: number
  student_id: number
  student_no: string
  student_name: string
  class_name: string
  total_score: number
  subjects: GradeRankingSubjectScore[]
}

export interface GradeRankingResponse {
  items: GradeRankingItem[]
  total: number
  page: number
  page_size: number
}

export interface StudentSubjectStat {
  course_id: number
  course_name: string
  score: number
  class_rank: number
  class_total: number
  grade_rank: number
  grade_total: number
  class_avg: number
}

export interface StudentStatisticsResponse {
  student_id: number
  student_no: string
  student_name: string
  class_name: string
  semester_id: number
  subjects: StudentSubjectStat[]
  total_score: number
  total_class_rank: number
  total_grade_rank: number
}

export interface TrendPoint {
  semester_id: number
  semester_name: string
  student_score: number | null
  class_avg: number | null
}

export interface ScoreTrendResponse {
  course_id: number
  course_name: string
  trend: TrendPoint[]
}

export interface ClassComparisonItem {
  class_id: number
  class_name: string
  avg_score: number
  pass_rate: number
  excellent_rate: number
  student_count: number
}

export interface GradeComparisonResponse {
  course_id: number
  course_name: string
  semester_id: number
  classes: ClassComparisonItem[]
}

// ── API calls ───────────────────────────────────────────────────────────────

export function fetchClassCourseStats(params: {
  class_id: number
  course_id: number
  semester_id: number
}) {
  return http.get<ClassCourseStatistics>('/statistics/class-course', { params })
}

export function fetchClassRanking(params: {
  class_id: number
  course_id: number
  semester_id: number
  page?: number
  page_size?: number
}) {
  return http.get<ClassRankingResponse>('/statistics/class-ranking', { params })
}

export function fetchGradeRanking(params: {
  grade_id: number
  semester_id: number
  page?: number
  page_size?: number
}) {
  return http.get<GradeRankingResponse>('/statistics/grade-ranking', { params })
}

export function fetchStudentStatistics(
  studentId: number,
  params: { semester_id: number },
) {
  return http.get<StudentStatisticsResponse>(`/statistics/student/${studentId}`, { params })
}

export function fetchScoreTrend(params: {
  student_id: number
  course_id: number
}) {
  return http.get<ScoreTrendResponse>('/statistics/trend', { params })
}

export function fetchGradeComparison(params: {
  grade_id: number
  course_id: number
  semester_id: number
}) {
  return http.get<GradeComparisonResponse>('/statistics/comparison', { params })
}
