# Implementation Plan: Student Score Management System (学生成绩管理系统)

## Task Type
- [x] Fullstack (Frontend + Backend + Database)

---

## 一、推荐技术栈

| 层级 | 技术选择 | 说明 |
|------|---------|------|
| **前端** | Vue 3 + TypeScript + Element Plus | Vue 在国内生态最成熟，Element Plus 是最流行的后台管理 UI 库 |
| **构建工具** | Vite | 快速的开发体验，Vue 官方推荐 |
| **后端** | Python + FastAPI | 语法简洁、上手快、自带 API 文档、性能优秀 |
| **数据库** | PostgreSQL | 可靠、功能强大、免费，适合结构化的成绩数据 |
| **ORM** | SQLAlchemy 2.0 + Alembic | Python 最成熟的 ORM，Alembic 负责数据库迁移 |
| **认证** | JWT (JSON Web Token) | 无状态认证，前后端分离的标准方案 |
| **测试** | Pytest (后端) + Vitest (前端) | 各自领域最流行的测试框架 |
| **部署** | Docker + Docker Compose | 一键部署，环境一致性保证 |

---

## 二、用户角色

| 角色 | 权限 |
|------|------|
| **管理员** | 全部权限：用户管理、班级管理、课程管理、系统配置 |
| **教师** | 录入/修改自己所教课程的成绩、查看本班统计 |
| **学生** | 查看自己的成绩、成绩单、排名 |

---

## 三、功能模块

```
学生成绩管理系统
├── 1. 用户管理（登录/角色/权限）
├── 2. 基础数据管理（学期/年级/班级/课程）
├── 3. 学生管理（信息录入/分班/Excel导入）
├── 4. 成绩管理（录入/修改/查询/批量导入）
├── 5. 统计分析（排名/平均分/分布/趋势）
├── 6. 报表导出（PDF成绩单/Excel汇总表）
└── 7. 系统管理（操作日志/数据备份/系统配置）
```

---

## 四、实施计划

### Phase 1：项目基础搭建
1. 初始化 FastAPI 后端项目结构
2. 配置 SQLAlchemy + Alembic 数据库迁移
3. 初始化 Vue 3 + Vite 前端项目
4. 配置 Element Plus + Vue Router + Pinia
5. Docker Compose 编排
6. 配置 CORS、环境变量、日志

### Phase 2：用户认证与权限
1. 用户表设计（users, roles）
2. JWT 登录/登出接口
3. RBAC 角色权限中间件
4. 前端登录页面 + 路由守卫
5. 用户管理 CRUD 界面

### Phase 3：基础数据管理
1. 数据库表设计：
   - `semesters`（学期：学期名称、开始/结束日期）
   - `grades`（年级：年级名称，如初一/高一）
   - `classes`（班级：班级名称，关联年级）
   - `courses`（课程：课程名称）
   - `students`（学生：**学号（student_no，唯一）**、**姓名（name）**、性别、所属班级、关联用户账号）
2. 各实体的 CRUD API
3. 前端管理界面（表格 + 表单）
   - 年级管理页面（年级列表、新增/编辑/删除）
   - 班级管理页面（按年级过滤、新增/编辑/删除）
   - 学生管理页面（按年级/班级过滤，显示学号和姓名）
4. Excel 批量导入学生信息（模板字段：学号、姓名、性别、年级、班级）
5. 教师-课程-班级关联管理

### Phase 4：成绩管理（核心）
1. 成绩表设计（scores, score_audit_logs）
2. 成绩录入 API（单条 + 批量）
3. Excel 批量导入成绩
4. 成绩修改 + 审计日志记录
5. 成绩查询界面（多维度筛选）
6. 学生端查看个人成绩

### Phase 5：统计分析与报表（详细展开）

#### 子阶段 5.1：统计分析 API（后端）

**评分等级定义**（统一配置，用于所有统计计算）：

| 等级 | 阈值 | 字段名 |
|------|------|--------|
| 超低分 | score < 30 | `ultra_low_rate` |
| 低分 | score < 40 | `low_rate` |
| 及格 | score >= 60 | `pass_rate` |
| 良好 | score >= 70 | `good_rate` |
| 优秀 | score >= 85 | `excellent_rate` |

> 注意：用户原文"抄低分率"应为"超低分率"（typo），阈值为 score < 30。

**6 个统计端点**：

| 端点 | 用途 |
|------|------|
| `GET /api/v1/statistics/class-course` | 班级单科统计（均分/最值/及格率/良好率/优秀率/低分率/超低分率/分布） |
| `GET /api/v1/statistics/class-ranking` | 班级单科排名（分页） |
| `GET /api/v1/statistics/grade-ranking` | 年级总分排名（含各科分数） |
| `GET /api/v1/statistics/student/{id}` | 学生个人统计（各科成绩+班级/年级排名） |
| `GET /api/v1/statistics/trend` | 多学期成绩趋势（个人/班级均分折线） |
| `GET /api/v1/statistics/comparison` | 同年级各班横向对比 |

**关键 SQL 伪代码**：
- 班级排名：使用 `RANK() OVER (ORDER BY score DESC)` 窗口函数
- 年级总分排名：`WITH` CTE 先汇总再双层 `RANK() OVER (PARTITION BY class_id ...)`
- 各等级统计：
  ```sql
  COUNT(*) FILTER (WHERE score < 30)  AS ultra_low_count,   -- 超低分 <30
  COUNT(*) FILTER (WHERE score < 40)  AS low_count,         -- 低分 <40
  COUNT(*) FILTER (WHERE score >= 60) AS pass_count,        -- 及格 >=60
  COUNT(*) FILTER (WHERE score >= 70) AS good_count,        -- 良好 >=70
  COUNT(*) FILTER (WHERE score >= 85) AS excellent_count,   -- 优秀 >=85
  -- 各率 = 上述 count / COUNT(*) * 100.0
  ```
- 分数段分布：`CASE WHEN score < 30 THEN '<30' WHEN score < 40 THEN '30-39' WHEN score < 60 THEN '40-59' ...`
- 推荐复合索引：`scores(semester_id, class_id, course_id)`

**新增文件**：
- `backend/app/api/statistics.py`
- `backend/app/services/statistics_service.py`
- `backend/app/schemas/statistics.py`
- `backend/tests/test_statistics.py`

#### 子阶段 5.2：前端 ECharts 图表（可与 5.1 并行）

**图表组件清单**：

| 组件 | 图表类型 | 展示内容 |
|------|---------|---------|
| `ScoreDistributionChart.vue` | 柱状图 | 分数段人数（0-59/60-69/70-79/80-89/90-100） |
| `ClassComparisonChart.vue` | 分组柱状图 | 同年级各班均分/及格率对比 |
| `ScoreTrendChart.vue` | 折线图 | 个人分数 + 班均线 + 年均线多学期走势 |
| `PassRatePieChart.vue` | 环形图 | 超低分/低分/及格/良好/优秀占比（5段） |
| `StudentRadarChart.vue` | 雷达图 | 学生各科相对班均分表现 |
| `StatCard.vue` | 卡片 | 均分/最高/最低/及格率/良好率/优秀率/低分率/超低分率 |

**统计页面**：
- `views/statistics/ClassStatistics.vue`（筛选栏 + 统计卡片 + 柱状图 + 饼图 + 排名表格）
- `views/statistics/GradeStatistics.vue`（班级对比图 + 年级排名表）
- `views/statistics/StudentStatistics.vue`（雷达图 + 趋势折线图 + 排名卡片）

**新增依赖**：`echarts ^5.5.0`、`vue-echarts ^7.0.0`

#### 子阶段 5.3：PDF 成绩单生成

**成绩单内容**：学校名、学期、姓名+学号+班级、各科成绩表（含班排名/班均分/年排名）、总分及排名、打印日期

**实现方案**：Jinja2 HTML 模板 → WeasyPrint 转 PDF

**端点**：
- `GET /api/v1/reports/transcript/pdf?student_id=&semester_id=`（单人）
- `POST /api/v1/reports/transcript/pdf/batch`（整班，返回合并 PDF）

**关键依赖**：`weasyprint >= 60.0`（需 Docker 中安装 `libpango`/`libcairo`）
Windows 开发备选：`xhtml2pdf`（纯 Python，无系统依赖）

**新增文件**：
- `backend/app/templates/transcript.html`（Jinja2 模板）
- `backend/app/templates/transcript.css`（含中文字体配置）

#### 子阶段 5.4：Excel 导出（可与 5.3 并行）

**3 类导出**：

| 端点 | 内容 |
|------|------|
| `GET /reports/class-summary/excel` | 班级汇总表（学号+姓名+各科分数+总分+排名，底部统计行：均分/最高/最低/及格率/良好率/优秀率/低分率/超低分率） |
| `GET /reports/grade-ranking/excel` | 年级排名表（含班级列） |
| `GET /reports/student-scores/excel` | 学生多学期成绩（每学期一个 Sheet） |

**格式要求**：不及格分数标红、统计行加粗、标题合并单元格、列宽自适应

**依赖**：`openpyxl >= 3.1.0`、前端 `file-saver ^2.0.5`

#### Phase 5 风险

| 风险 | 级别 | 应对 |
|------|------|------|
| 大数据量统计查询慢 | 高 | 复合索引 + 考虑物化视图/缓存 |
| WeasyPrint 中文乱码 | 中 | Docker 预装 Noto Sans CJK，CSS 指定字体回退 |
| Windows 开发 WeasyPrint 系统依赖 | 中 | 开发用 xhtml2pdf，生产用 WeasyPrint（Docker） |
| 批量 PDF 内存占用大 | 中 | 逐个生成后合并，限制单次上限（≤100人） |

#### Phase 5 成功标准
- [ ] 6 个统计 API 正确返回数据，权限边界正确（学生只看自己，教师只看本班）
- [ ] 班级/年级/学生三个统计页面图表正常渲染
- [ ] PDF 成绩单中文无乱码，批量导出整班可用
- [ ] Excel 汇总表格式正确（样式、统计行）
- [ ] 统计 API 测试覆盖率 ≥ 80%
- [ ] 100人班级统计 API 响应时间 < 500ms

### Phase 6：系统完善与部署
1. 操作日志记录
2. 数据备份方案
3. 性能优化（分页、索引、缓存）
4. 安全加固（输入校验、SQL注入防护、XSS防护）
5. 部署文档

---

## 五、推荐项目结构

```
score_system/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/          # 路由层
│   │   ├── core/         # 配置/安全/依赖
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── schemas/      # Pydantic 验证
│   │   ├── services/     # 业务逻辑
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # HTTP 请求封装
│   │   ├── components/   # 通用组件
│   │   ├── views/        # 页面视图
│   │   ├── stores/       # Pinia 状态
│   │   ├── router/       # 路由
│   │   └── utils/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 六、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 成绩数据录入错误 | 高 | 审计日志 + 修改审批 + 数据校验 |
| Excel 导入格式不统一 | 中 | 提供模板下载 + 导入前校验 |
| 并发录入冲突 | 中 | 数据库乐观锁 + 前端提示 |
| 学生成绩隐私泄露 | 高 | RBAC 权限控制 + 接口鉴权 + HTTPS |

---

## SESSION_ID (for /ccg:execute use)
- CODEX_SESSION: N/A (external model unavailable)
- GEMINI_SESSION: N/A (external model unavailable)
