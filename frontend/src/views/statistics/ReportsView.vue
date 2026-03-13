<template>
  <div class="reports-view">
    <h2>报表导出</h2>

    <el-card class="section">
      <template #header><span>PDF 成绩单</span></template>
      <el-form :inline="true">
        <el-form-item label="学期">
          <el-select v-model="pdfForm.semester_id" placeholder="选择学期">
            <el-option v-for="s in semesters" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学生">
          <el-select v-model="pdfForm.student_id" placeholder="选择学生" filterable clearable>
            <el-option v-for="s in students" :key="s.id" :label="`${s.student_no} ${s.name}`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="pdfLoading" @click="handleSinglePdf">下载个人成绩单</el-button>
        </el-form-item>
      </el-form>
      <el-divider />
      <el-form :inline="true">
        <el-form-item label="班级(批量)">
          <el-select v-model="pdfForm.class_id" placeholder="选择班级">
            <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="warning" :loading="batchPdfLoading" @click="handleBatchPdf">批量导出整班</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="section">
      <template #header><span>Excel 导出</span></template>
      <el-form :inline="true">
        <el-form-item label="学期">
          <el-select v-model="excelForm.semester_id" placeholder="选择学期">
            <el-option v-for="s in semesters" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <div class="export-buttons">
        <el-button type="success" :loading="excelLoading.classSummary" @click="handleClassSummary">
          班级汇总表
        </el-button>
        <el-button type="success" :loading="excelLoading.gradeRanking" @click="handleGradeRanking">
          年级排名表
        </el-button>
        <el-button type="success" :loading="excelLoading.studentScores" @click="handleStudentScores">
          学生多学期成绩
        </el-button>
      </div>
      <el-form :inline="true" style="margin-top: 12px">
        <el-form-item label="班级(汇总)">
          <el-select v-model="excelForm.class_id" placeholder="选择班级">
            <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="年级(排名)">
          <el-select v-model="excelForm.grade_id" placeholder="选择年级">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学生(个人)">
          <el-select v-model="excelForm.student_id" placeholder="选择学生" filterable clearable>
            <el-option v-for="s in students" :key="s.id" :label="`${s.student_no} ${s.name}`" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { saveAs } from 'file-saver'
import http from '@/api/http'
import {
  downloadTranscriptPdf,
  downloadBatchTranscriptPdf,
  downloadClassSummaryExcel,
  downloadGradeRankingExcel,
  downloadStudentScoresExcel,
} from '@/api/reports'

interface Option { id: number; name: string; student_no?: string }

const semesters = ref<Option[]>([])
const classes = ref<Option[]>([])
const grades = ref<Option[]>([])
const students = ref<Option[]>([])

const pdfForm = reactive({ semester_id: null as number | null, student_id: null as number | null, class_id: null as number | null })
const excelForm = reactive({ semester_id: null as number | null, class_id: null as number | null, grade_id: null as number | null, student_id: null as number | null })

const pdfLoading = ref(false)
const batchPdfLoading = ref(false)
const excelLoading = reactive({ classSummary: false, gradeRanking: false, studentScores: false })

async function loadOptions() {
  const [semRes, clsRes, gradeRes, stuRes] = await Promise.all([
    http.get('/semesters'),
    http.get('/classes'),
    http.get('/grades'),
    http.get('/students'),
  ])
  semesters.value = semRes.data.items ?? semRes.data
  classes.value = clsRes.data.items ?? clsRes.data
  grades.value = gradeRes.data.items ?? gradeRes.data
  students.value = stuRes.data.items ?? stuRes.data
}

function saveBlobAs(blob: Blob, filename: string) {
  saveAs(blob, filename)
}

async function handleSinglePdf() {
  if (!pdfForm.semester_id || !pdfForm.student_id) {
    ElMessage.warning('请选择学期和学生')
    return
  }
  pdfLoading.value = true
  try {
    const res = await downloadTranscriptPdf({ student_id: pdfForm.student_id, semester_id: pdfForm.semester_id })
    saveBlobAs(new Blob([res.data], { type: 'application/pdf' }), `transcript_${pdfForm.student_id}.pdf`)
  } catch {
    ElMessage.error('下载失败')
  } finally {
    pdfLoading.value = false
  }
}

async function handleBatchPdf() {
  if (!pdfForm.semester_id || !pdfForm.class_id) {
    ElMessage.warning('请选择学期和班级')
    return
  }
  batchPdfLoading.value = true
  try {
    const res = await downloadBatchTranscriptPdf({ class_id: pdfForm.class_id, semester_id: pdfForm.semester_id })
    saveBlobAs(new Blob([res.data], { type: 'application/pdf' }), `batch_transcript_${pdfForm.class_id}.pdf`)
  } catch {
    ElMessage.error('下载失败')
  } finally {
    batchPdfLoading.value = false
  }
}

async function handleClassSummary() {
  if (!excelForm.semester_id || !excelForm.class_id) {
    ElMessage.warning('请选择学期和班级')
    return
  }
  excelLoading.classSummary = true
  try {
    const res = await downloadClassSummaryExcel({ class_id: excelForm.class_id, semester_id: excelForm.semester_id })
    saveBlobAs(new Blob([res.data]), `class_summary_${excelForm.class_id}.xlsx`)
  } catch {
    ElMessage.error('下载失败')
  } finally {
    excelLoading.classSummary = false
  }
}

async function handleGradeRanking() {
  if (!excelForm.semester_id || !excelForm.grade_id) {
    ElMessage.warning('请选择学期和年级')
    return
  }
  excelLoading.gradeRanking = true
  try {
    const res = await downloadGradeRankingExcel({ grade_id: excelForm.grade_id, semester_id: excelForm.semester_id })
    saveBlobAs(new Blob([res.data]), `grade_ranking_${excelForm.grade_id}.xlsx`)
  } catch {
    ElMessage.error('下载失败')
  } finally {
    excelLoading.gradeRanking = false
  }
}

async function handleStudentScores() {
  if (!excelForm.student_id) {
    ElMessage.warning('请选择学生')
    return
  }
  excelLoading.studentScores = true
  try {
    const res = await downloadStudentScoresExcel({ student_id: excelForm.student_id })
    saveBlobAs(new Blob([res.data]), `student_scores_${excelForm.student_id}.xlsx`)
  } catch {
    ElMessage.error('下载失败')
  } finally {
    excelLoading.studentScores = false
  }
}

onMounted(loadOptions)
</script>

<style scoped>
.section { margin-bottom: 20px; }
.export-buttons { display: flex; gap: 12px; }
</style>
