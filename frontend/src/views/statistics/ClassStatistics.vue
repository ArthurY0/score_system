<template>
  <div class="class-statistics">
    <h2>班级统计</h2>

    <!-- Filter bar -->
    <el-form :inline="true" class="filter-bar">
      <el-form-item label="学期">
        <el-select v-model="filters.semester_id" placeholder="选择学期" @change="loadData">
          <el-option v-for="s in semesters" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="班级">
        <el-select v-model="filters.class_id" placeholder="选择班级" @change="loadData">
          <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="课程">
        <el-select v-model="filters.course_id" placeholder="选择课程" @change="loadData">
          <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
    </el-form>

    <template v-if="stats">
      <!-- Stat cards -->
      <div class="stat-cards">
        <StatCard title="平均分" :value="stats.avg_score" suffix="分" />
        <StatCard title="最高分" :value="stats.max_score" suffix="分" color="#67c23a" />
        <StatCard title="最低分" :value="stats.min_score" suffix="分" color="#f56c6c" />
        <StatCard title="及格率" :value="stats.pass_rate" suffix="%" color="#409eff" />
        <StatCard title="良好率" :value="stats.good_rate" suffix="%" />
        <StatCard title="优秀率" :value="stats.excellent_rate" suffix="%" color="#6f7ad3" />
        <StatCard title="低分率" :value="stats.low_rate" suffix="%" color="#e6a23c" />
        <StatCard title="超低分率" :value="stats.ultra_low_rate" suffix="%" color="#f56c6c" />
      </div>

      <!-- Charts -->
      <div class="charts-row">
        <div class="chart-box">
          <ScoreDistributionChart :data="stats.distribution" />
        </div>
        <div class="chart-box">
          <PassRatePieChart
            :ultra-low-rate="stats.ultra_low_rate"
            :low-rate="stats.low_rate"
            :pass-rate="stats.pass_rate"
            :good-rate="stats.good_rate"
            :excellent-rate="stats.excellent_rate"
          />
        </div>
      </div>

      <!-- Ranking table -->
      <div class="ranking-section">
        <h3>排名表</h3>
        <el-table :data="ranking" stripe>
          <el-table-column prop="rank" label="排名" width="80" />
          <el-table-column prop="student_no" label="学号" width="120" />
          <el-table-column prop="student_name" label="姓名" />
          <el-table-column prop="score" label="分数" width="100" />
        </el-table>
        <el-pagination
          v-if="rankingTotal > pageSize"
          layout="prev, pager, next"
          :total="rankingTotal"
          :page-size="pageSize"
          :current-page="currentPage"
          @current-change="handlePageChange"
          style="margin-top: 12px; justify-content: center"
        />
      </div>
    </template>

    <el-empty v-else-if="!loading" description="请选择筛选条件后查看统计" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
import { fetchClassCourseStats, fetchClassRanking } from '@/api/statistics'
import type { ClassCourseStatistics, ClassRankingItem } from '@/api/statistics'
import StatCard from '@/components/statistics/StatCard.vue'
import ScoreDistributionChart from '@/components/statistics/ScoreDistributionChart.vue'
import PassRatePieChart from '@/components/statistics/PassRatePieChart.vue'

interface Option { id: number; name: string }

const semesters = ref<Option[]>([])
const classes = ref<Option[]>([])
const courses = ref<Option[]>([])

const filters = ref({ semester_id: null as number | null, class_id: null as number | null, course_id: null as number | null })
const stats = ref<ClassCourseStatistics | null>(null)
const ranking = ref<ClassRankingItem[]>([])
const rankingTotal = ref(0)
const currentPage = ref(1)
const pageSize = 20
const loading = ref(false)

async function loadOptions() {
  const [semRes, clsRes, courseRes] = await Promise.all([
    http.get('/semesters'),
    http.get('/classes'),
    http.get('/courses'),
  ])
  semesters.value = semRes.data.items ?? semRes.data
  classes.value = clsRes.data.items ?? clsRes.data
  courses.value = courseRes.data.items ?? courseRes.data
}

async function loadData() {
  const { semester_id, class_id, course_id } = filters.value
  if (!semester_id || !class_id || !course_id) return

  loading.value = true
  try {
    const [statsRes, rankRes] = await Promise.all([
      fetchClassCourseStats({ class_id, course_id, semester_id }),
      fetchClassRanking({ class_id, course_id, semester_id, page: 1, page_size: pageSize }),
    ])
    stats.value = statsRes.data
    ranking.value = rankRes.data.items
    rankingTotal.value = rankRes.data.total
    currentPage.value = 1
  } catch {
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

async function handlePageChange(page: number) {
  const { semester_id, class_id, course_id } = filters.value
  if (!semester_id || !class_id || !course_id) return
  currentPage.value = page
  const res = await fetchClassRanking({ class_id, course_id, semester_id, page, page_size: pageSize })
  ranking.value = res.data.items
}

onMounted(loadOptions)
</script>

<style scoped>
.filter-bar { margin-bottom: 16px; }
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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
