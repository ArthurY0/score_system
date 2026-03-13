<template>
  <div class="student-statistics">
    <h2>学生统计</h2>

    <!-- Filter bar -->
    <el-form :inline="true" class="filter-bar">
      <el-form-item label="学期">
        <el-select v-model="filters.semester_id" placeholder="选择学期" @change="loadData">
          <el-option v-for="s in semesters" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="!isStudent" label="学生">
        <el-select v-model="filters.student_id" placeholder="选择学生" filterable @change="loadData">
          <el-option v-for="s in students" :key="s.id" :label="`${s.student_no} ${s.name}`" :value="s.id" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="studentStats" label="趋势课程">
        <el-select v-model="selectedCourseId" placeholder="选择课程" @change="loadTrend">
          <el-option v-for="s in studentStats.subjects" :key="s.course_id" :label="s.course_name" :value="s.course_id" />
        </el-select>
      </el-form-item>
    </el-form>

    <template v-if="studentStats">
      <!-- Summary cards -->
      <div class="stat-cards">
        <StatCard title="总分" :value="studentStats.total_score" suffix="分" />
        <StatCard title="班级排名" :value="studentStats.total_class_rank" suffix="" color="#409eff" />
        <StatCard title="年级排名" :value="studentStats.total_grade_rank" suffix="" color="#6f7ad3" />
      </div>

      <!-- Charts -->
      <div class="charts-row">
        <div class="chart-box">
          <StudentRadarChart :subjects="radarData" />
        </div>
        <div v-if="trendData" class="chart-box">
          <ScoreTrendChart :data="trendData.trend" />
        </div>
      </div>

      <!-- Subject detail table -->
      <div class="ranking-section">
        <h3>各科成绩明细</h3>
        <el-table :data="studentStats.subjects" stripe>
          <el-table-column prop="course_name" label="课程" />
          <el-table-column prop="score" label="分数" width="100" />
          <el-table-column label="班级排名" width="120">
            <template #default="{ row }">{{ row.class_rank }}/{{ row.class_total }}</template>
          </el-table-column>
          <el-table-column label="年级排名" width="120">
            <template #default="{ row }">{{ row.grade_rank }}/{{ row.grade_total }}</template>
          </el-table-column>
          <el-table-column prop="class_avg" label="班均分" width="100" />
        </el-table>
      </div>
    </template>

    <el-empty v-else-if="!loading" description="请选择筛选条件后查看统计" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { fetchStudentStatistics, fetchScoreTrend } from '@/api/statistics'
import type { StudentStatisticsResponse, ScoreTrendResponse } from '@/api/statistics'
import StatCard from '@/components/statistics/StatCard.vue'
import StudentRadarChart from '@/components/statistics/StudentRadarChart.vue'
import ScoreTrendChart from '@/components/statistics/ScoreTrendChart.vue'

interface Option { id: number; name: string; student_no?: string }

const authStore = useAuthStore()
const isStudent = computed(() => authStore.user?.role === 'student')

const semesters = ref<Option[]>([])
const students = ref<Option[]>([])

const filters = ref({ semester_id: null as number | null, student_id: null as number | null })
const studentStats = ref<StudentStatisticsResponse | null>(null)
const trendData = ref<ScoreTrendResponse | null>(null)
const selectedCourseId = ref<number | null>(null)
const loading = ref(false)

const radarData = computed(() =>
  (studentStats.value?.subjects ?? []).map((s) => ({
    course_name: s.course_name,
    score: s.score,
    class_avg: s.class_avg,
  })),
)

async function loadOptions() {
  const [semRes] = await Promise.all([http.get('/semesters')])
  semesters.value = semRes.data.items ?? semRes.data

  if (!isStudent.value) {
    const stuRes = await http.get('/students')
    students.value = stuRes.data.items ?? stuRes.data
  }
}

async function loadData() {
  const { semester_id, student_id } = filters.value
  // For student role, student_id comes from the backend (auto-detected)
  const sid = isStudent.value ? undefined : student_id
  if (!semester_id || (!isStudent.value && !sid)) return

  loading.value = true
  try {
    // For student role, we need to get their linked student_id first
    let resolvedId = sid
    if (isStudent.value) {
      const meRes = await http.get('/scores/my', { params: { semester_id, page_size: 1 } })
      if (meRes.data.items?.length) {
        resolvedId = meRes.data.items[0].student_id
      } else {
        ElMessage.info('暂无成绩数据')
        loading.value = false
        return
      }
    }

    const res = await fetchStudentStatistics(resolvedId!, { semester_id })
    studentStats.value = res.data
    trendData.value = null
    selectedCourseId.value = null
  } catch {
    ElMessage.error('加载学生统计失败')
  } finally {
    loading.value = false
  }
}

async function loadTrend() {
  if (!selectedCourseId.value || !studentStats.value) return
  try {
    const res = await fetchScoreTrend({
      student_id: studentStats.value.student_id,
      course_id: selectedCourseId.value,
    })
    trendData.value = res.data
  } catch {
    ElMessage.error('加载趋势数据失败')
  }
}

onMounted(loadOptions)
</script>

<style scoped>
.filter-bar { margin-bottom: 16px; }
.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}
.chart-box {
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
.ranking-section {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
</style>
