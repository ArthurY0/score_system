<template>
  <div class="grade-statistics">
    <h2>年级统计</h2>

    <!-- Filter bar -->
    <el-form :inline="true" class="filter-bar">
      <el-form-item label="学期">
        <el-select v-model="filters.semester_id" placeholder="选择学期" @change="loadData">
          <el-option v-for="s in semesters" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="年级">
        <el-select v-model="filters.grade_id" placeholder="选择年级" @change="loadData">
          <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="课程(对比)">
        <el-select v-model="filters.course_id" placeholder="选择课程" @change="loadComparison">
          <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
    </el-form>

    <!-- Class comparison chart -->
    <div v-if="comparisonData" class="chart-box">
      <ClassComparisonChart :data="comparisonData.classes" />
    </div>

    <!-- Grade ranking table -->
    <div v-if="gradeRanking.length" class="ranking-section">
      <h3>年级总分排名</h3>
      <el-table :data="gradeRanking" stripe>
        <el-table-column prop="rank" label="排名" width="80" />
        <el-table-column prop="student_no" label="学号" width="120" />
        <el-table-column prop="student_name" label="姓名" width="120" />
        <el-table-column prop="class_name" label="班级" width="120" />
        <el-table-column prop="total_score" label="总分" width="100" />
        <el-table-column label="各科成绩">
          <template #default="{ row }">
            <span v-for="(s, i) in row.subjects" :key="i" class="subject-score">
              {{ s.course_name }}: {{ s.score }}
            </span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="gradeRankingTotal > pageSize"
        layout="prev, pager, next"
        :total="gradeRankingTotal"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
        style="margin-top: 12px; justify-content: center"
      />
    </div>

    <el-empty v-else-if="!loading" description="请选择筛选条件后查看统计" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
import { fetchGradeRanking, fetchGradeComparison } from '@/api/statistics'
import type { GradeRankingItem, GradeComparisonResponse } from '@/api/statistics'
import ClassComparisonChart from '@/components/statistics/ClassComparisonChart.vue'

interface Option { id: number; name: string }

const semesters = ref<Option[]>([])
const grades = ref<Option[]>([])
const courses = ref<Option[]>([])

const filters = ref({ semester_id: null as number | null, grade_id: null as number | null, course_id: null as number | null })
const gradeRanking = ref<GradeRankingItem[]>([])
const gradeRankingTotal = ref(0)
const comparisonData = ref<GradeComparisonResponse | null>(null)
const currentPage = ref(1)
const pageSize = 20
const loading = ref(false)

async function loadOptions() {
  const [semRes, gradeRes, courseRes] = await Promise.all([
    http.get('/semesters'),
    http.get('/grades'),
    http.get('/courses'),
  ])
  semesters.value = semRes.data.items ?? semRes.data
  grades.value = gradeRes.data.items ?? gradeRes.data
  courses.value = courseRes.data.items ?? courseRes.data
}

async function loadData() {
  const { semester_id, grade_id } = filters.value
  if (!semester_id || !grade_id) return

  loading.value = true
  try {
    const res = await fetchGradeRanking({ grade_id, semester_id, page: 1, page_size: pageSize })
    gradeRanking.value = res.data.items
    gradeRankingTotal.value = res.data.total
    currentPage.value = 1
    // Also load comparison if course selected
    if (filters.value.course_id) await loadComparison()
  } catch {
    ElMessage.error('加载年级排名失败')
  } finally {
    loading.value = false
  }
}

async function loadComparison() {
  const { semester_id, grade_id, course_id } = filters.value
  if (!semester_id || !grade_id || !course_id) return
  try {
    const res = await fetchGradeComparison({ grade_id, course_id, semester_id })
    comparisonData.value = res.data
  } catch {
    ElMessage.error('加载班级对比数据失败')
  }
}

async function handlePageChange(page: number) {
  const { semester_id, grade_id } = filters.value
  if (!semester_id || !grade_id) return
  currentPage.value = page
  const res = await fetchGradeRanking({ grade_id, semester_id, page, page_size: pageSize })
  gradeRanking.value = res.data.items
}

onMounted(loadOptions)
</script>

<style scoped>
.filter-bar { margin-bottom: 16px; }
.chart-box {
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
.ranking-section {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
.subject-score {
  margin-right: 12px;
  font-size: 13px;
  color: #606266;
}
</style>
