<template>
  <div class="bg-slate-50 min-h-screen pb-12" v-loading="loading">
    
    <div class="bg-white rounded-[32px] p-8 mb-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b-4"
         :class="caseData.process_tag === '正常' ? 'border-blue-600' : 'border-red-600 bg-red-50'">
      <div>
        <div class="flex items-center space-x-3 mb-2">
          <el-button icon="ArrowLeft" circle @click="router.back()" class="!border-none !bg-slate-100 hover:!bg-slate-200" />
          <h2 class="text-2xl font-bold" :class="caseData.process_tag === '正常' ? 'text-gray-800' : 'text-red-600 line-through'">{{ caseData.title || '加载中...' }}</h2>
          <el-tag :type="getStatusType(caseData.status)" effect="dark" round class="font-bold">{{ caseData.status }}</el-tag>
          <el-tag v-if="caseData.process_tag !== '正常'" type="danger" effect="dark" round class="font-black">{{ caseData.process_tag }}</el-tag>
        </div>
        <p class="text-slate-500 text-sm ml-11">
          流水号：<span class="font-bold text-gray-700 mr-4">{{ caseData.serial_no }}</span> 
          案号：<span class="font-bold text-gray-700 mr-4">{{ caseData.case_no || '暂未生成' }}</span>
          登记日期：<span>{{ caseData.reg_date }}</span>
        </p>
      </div>
      <div class="flex space-x-3 flex-wrap gap-y-2">
        <template v-if="canEdit && caseData.process_tag === '正常'">
          <el-button type="danger" plain class="!rounded-xl font-bold" @click="handleProcessTag('案件作废')">案件作废</el-button>
          <el-button type="warning" plain class="!rounded-xl font-bold" @click="handleProcessTag('合同解除')">合同解除</el-button>
        </template>
        <template v-if="canEdit && caseData.process_tag !== '正常'">
          <el-button type="success" plain class="!rounded-xl font-bold" @click="handleProcessTag('正常')">恢复正常</el-button>
        </template>
        
        <el-button type="success" plain class="!rounded-xl font-bold" icon="Download" @click="exportCSV">导出档案</el-button>
        <el-button v-if="canEdit && caseData.process_tag === '正常'" type="primary" class="!rounded-xl font-bold" icon="Check" @click="saveChanges" :loading="saving">保存修改</el-button>
      </div>
    </div>

    <el-alert v-if="caseData.process_tag !== '正常'" title="⚠️ 此案件已被标记为异常状态，所有信息已锁定，无法修改。" type="error" show-icon class="!rounded-2xl mb-6 !font-bold" :closable="false" />
    <el-alert v-if="!canEdit" title="您当前为律师账户，仅可查看案件详情，如需修改请联系风控或管理员。" type="info" show-icon class="!rounded-2xl mb-6 !bg-blue-50 !text-blue-600" :closable="false" />

    <el-form :model="caseData" label-position="top" class="space-y-6" :disabled="!canEdit || caseData.process_tag !== '正常'">
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        <section class="bg-white rounded-[32px] p-8 shadow-sm">
          <h3 class="text-lg font-bold text-blue-600 mb-6 flex items-center"><el-icon class="mr-2"><Collection /></el-icon> 案件基础属性</h3>
          <div class="grid grid-cols-2 gap-4">
            <el-form-item label="案件类型">
              <el-input v-model="caseData.case_type" disabled class="!rounded-xl" />
            </el-form-item>
            <el-form-item label="案件来源">
              <el-input v-model="caseData.source" disabled class="!rounded-xl" />
            </el-form-item>

            <template v-if="['刑事案件', '民事案件', '行政案件', '仲裁案件'].includes(caseData.case_type)">
              <el-form-item label="案由/罪名">
                <el-input v-model="caseData.details.topic_name" disabled class="!rounded-xl" />
              </el-form-item>
              <el-form-item label="办案机关省市">
                <el-input v-model="caseData.details.region_name" disabled class="!rounded-xl" />
              </el-form-item>
              <el-form-item label="刑事类型" v-if="caseData.case_type === '刑事案件'">
                <el-input v-model="caseData.details.criminal_type" />
              </el-form-item>
              <el-form-item label="办案机关名称" :class="caseData.case_type === '刑事案件' ? '' : 'col-span-2'">
                <el-input v-model="caseData.details.agency_names" />
              </el-form-item>
            </template>

            <template v-if="caseData.case_type === '顾问案件'">
              <el-form-item label="服务开始时间">
                <el-date-picker v-model="caseData.details.service_start" type="date" value-format="YYYY-MM-DD" class="w-full" />
              </el-form-item>
              <el-form-item label="服务结束时间">
                <el-date-picker v-model="caseData.details.service_end" type="date" value-format="YYYY-MM-DD" class="w-full" />
              </el-form-item>
            </template>

            <div class="col-span-2 flex space-x-6 pt-2">
              <el-checkbox v-model="caseData.details.is_legal_aid" label="法律援助" class="!font-bold text-orange-500" />
              <el-checkbox v-model="caseData.details.is_foreign" label="涉外案件" class="!font-bold" />
            </div>
            
            <el-form-item label="案件名称" class="col-span-2 mt-4">
              <el-input v-model="caseData.title" size="large" />
            </el-form-item>
            <el-form-item label="案件说明" class="col-span-2">
              <el-input v-model="caseData.description" type="textarea" :rows="3" />
            </el-form-item>
          </div>
        </section>

        <section class="bg-white rounded-[32px] p-8 shadow-sm flex flex-col space-y-6">
          <div>
            <h3 class="text-lg font-bold text-blue-600 mb-6 flex items-center"><el-icon class="mr-2"><Money /></el-icon> 财务信息</h3>
            <div class="grid grid-cols-2 gap-4">
              <el-form-item label="收费方式">
                <el-input v-model="caseData.finance.billing_method" disabled />
              </el-form-item>
              <el-form-item label="标的额 (元)">
                <el-input-number v-model="caseData.finance.target_amount" :min="0" :precision="2" class="!w-full" />
              </el-form-item>
              <el-form-item label="应收金额 (元)">
                <el-input-number v-model="caseData.finance.receivable" :min="0" :precision="2" class="!w-full" :disabled="caseData.details.is_legal_aid" />
              </el-form-item>
              <el-form-item label="已收金额 (元)">
                <el-input-number v-model="caseData.finance.received" :min="0" :precision="2" class="!w-full" :disabled="caseData.details.is_legal_aid" />
              </el-form-item>
              <el-form-item label="收费说明" class="col-span-2 mt-2">
                <el-input v-model="caseData.finance.fee_remark" type="textarea" :rows="2" placeholder="发票开具要求等财务说明..." />
              </el-form-item>
              </div>
          </div>
        </section>
      </div>

      <section class="bg-white rounded-[32px] p-8 shadow-sm">
        <h3 class="text-lg font-bold text-blue-600 mb-6 flex items-center"><el-icon class="mr-2"><UserFilled /></el-icon> 案件人员清单</h3>
        <el-table :data="caseData.entities" stripe class="w-full !rounded-xl overflow-hidden border border-slate-100">
          <el-table-column prop="role_name" label="案件角色" width="150">
            <template #default="scope">
              <el-tag effect="plain" type="info">{{ scope.row.role_name }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="entity_type" label="主体类型" width="120" />
          <el-table-column prop="name" label="姓名/名称" min-width="150" class-name="font-bold text-blue-700" />
          <el-table-column prop="id_number" label="证件号码/信用代码" min-width="200" />
          <el-table-column prop="phone" label="联系电话" width="150" />
        </el-table>
      </section>

      <section class="bg-white rounded-[32px] p-8 shadow-sm">
        <h3 class="text-lg font-bold text-blue-600 mb-6 flex items-center"><el-icon class="mr-2"><Briefcase /></el-icon> 内部执行信息</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <p class="text-sm font-bold text-gray-500 mb-3">已选委托阶段</p>
            <div class="flex flex-wrap gap-2">
              <el-tag v-for="stage in caseData.stages" :key="stage" size="large" effect="plain" class="!rounded-lg !border-blue-200 !text-blue-700">{{ stage }}</el-tag>
              <span v-if="caseData.stages.length === 0" class="text-slate-400 text-sm">无特定阶段</span>
            </div>
          </div>
          <div>
            <p class="text-sm font-bold text-gray-500 mb-3">案件承办律师及比例</p>
            <div class="space-y-2">
              <div v-for="lw in caseData.lawyers" :key="lw.lawyer_id" class="flex items-center justify-between bg-slate-50 p-3 rounded-xl border border-slate-100 w-full">
                <div class="flex items-center space-x-3">
                  <el-tag :type="lw.role_type === '主办律师' ? 'danger' : 'info'" size="small" effect="dark">{{ lw.role_type }}</el-tag>
                  <span class="font-bold text-gray-700">{{ lw.name }}</span>
                </div>
                <div class="flex items-center space-x-1">
                  <span class="text-blue-600 font-black">{{ lw.allocation_ratio }}</span>
                  <span class="text-slate-400 text-xs">%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section v-if="caseData.logs.length > 0" class="bg-white rounded-[32px] p-8 shadow-sm">
        <h3 class="text-lg font-bold text-blue-600 mb-6 flex items-center"><el-icon class="mr-2"><Clock /></el-icon> 风控操作审计日志</h3>
        <el-timeline>
          <el-timeline-item v-for="(log, index) in caseData.logs" :key="index" :timestamp="log.time" placement="top" color="#2563eb">
            <el-card shadow="hover" class="!rounded-xl">
              <p class="text-sm">风控/管理员 <span class="font-bold text-blue-700">[{{ log.operator }}]</span> {{ log.action }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </section>

    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Collection, UserFilled, Money, Briefcase, Clock } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'
import { useUserStore } from '../store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const saving = ref(false)
const caseId = route.params.id

const canEdit = computed(() => {
  const role = userStore.userInfo.role
  return role === '风控' || role === '管理员'
})

const caseData = reactive({
  title: '', case_type: '', source: '', status: '', serial_no: '', case_no: '', reg_date: '', description: '',
  process_tag: '正常',
  details: { is_legal_aid: false, is_foreign: false, criminal_type: '', topic_name: '', region_name: '', agency_names: '', service_start: null, service_end: null },
  entities: [], lawyers: [], stages: [],
  finance: { billing_method: '', target_amount: 0, receivable: 0, received: 0, fee_remark: '' },
  logs: []
})

const handleProcessTag = async (tag) => {
  try {
    await ElMessageBox.confirm(`确定要将该案件标记为【${tag}】吗？`, '警示操作', {
      confirmButtonText: '确认执行',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    await request.put(`/cases/process-tag/${caseId}`, { tag })
    ElMessage.success(`操作成功，已标记为${tag}`)
    fetchDetail() 
  } catch (error) {
    if (error !== 'cancel') console.error('标记失败', error)
  }
}

const getStatusType = (status) => {
  const map = { '案件审核': 'warning', '合同审核': 'primary', '结案审核': 'info', '已结案': 'success' }
  return map[status] || 'info'
}

const fetchDetail = async () => {
  loading.value = true
  try {
    const data = await request.get(`/cases/detail/${caseId}`)
    Object.assign(caseData, data)
  } catch (error) {
    console.error('获取详情失败', error)
    router.back()
  } finally {
    loading.value = false
  }
}

const saveChanges = async () => {
  saving.value = true
  try {
    await request.put(`/cases/detail/${caseId}`, {
      title: caseData.title,
      description: caseData.description,
      finance: caseData.finance
    })
    ElMessage.success('案件信息已成功更新并保存')
  } catch (error) {
    console.error('保存失败', error)
  } finally {
    saving.value = false
  }
}

const exportCSV = async () => {
  try {
    ElMessage.info('正在生成 CSV 文件，请稍候...')
    const response = await request.get(`/cases/export/${caseId}`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `案件详情_${caseData.serial_no}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success('CSV 导出成功！')
  } catch (error) {
    console.error('导出失败', error)
    ElMessage.error('导出文件失败')
  }
}

onMounted(() => {
  if (caseId) fetchDetail()
})
</script>