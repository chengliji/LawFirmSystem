<template>
  <div class="bg-slate-50 min-h-screen pb-12">

    <el-form :model="form" ref="formRef" label-position="top" class="space-y-6">
      
      <section class="bg-white rounded-[32px] p-8 shadow-sm">
        <h3 class="text-lg font-bold text-blue-600 mb-6 flex items-center"><el-icon class="mr-2"><Collection /></el-icon> 案件类型</h3>
        <el-form-item required>
          <el-radio-group v-model="form.case_type" size="large" @change="handleCaseTypeChange">
            <el-radio-button v-for="type in caseTypes" :key="type" :label="type" class="!rounded-xl mr-4 mb-4 border-none shadow-sm data-[state=checked]:bg-blue-600" />
          </el-radio-group>
        </el-form-item>
      </section>

      <section class="bg-white rounded-[32px] p-8 shadow-sm relative overflow-hidden">
        <div class="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-lg font-bold text-blue-600 flex items-center"><el-icon class="mr-2"><UserFilled /></el-icon> 案件人员</h3>
          <el-button type="danger" plain class="!rounded-xl font-bold" icon="Search" @click="doConflictCheck" :loading="checkingConflict">
            进行冲突检索
          </el-button>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div v-for="role in currentRoles" :key="role" class="bg-slate-50 p-6 rounded-2xl border border-slate-100">
            <div class="flex justify-between items-center mb-4">
              <span class="font-bold text-gray-700">{{ role }}</span>
              <el-button size="small" type="primary" plain round @click="openEntityDialog(role)">+ 添加</el-button>
            </div>
            <div class="space-y-2">
              <div v-for="(entity, idx) in getEntitiesByRole(role)" :key="idx" class="flex justify-between items-center bg-white p-3 rounded-xl shadow-sm text-sm">
                <span><b class="text-blue-700">{{ entity.name }}</b> ({{ entity.id_number || '无证件号' }})</span>
                <el-button type="danger" icon="Delete" circle size="small" text @click="removeEntity(entity)" />
              </div>
              <div v-if="getEntitiesByRole(role).length === 0" class="text-slate-400 text-sm text-center py-2">暂未添加</div>
            </div>
          </div>
        </div>
      </section>

      <section class="bg-white rounded-[32px] p-8 shadow-sm">
        <h3 class="text-lg font-bold text-blue-600 mb-6 flex items-center"><el-icon class="mr-2"><Share /></el-icon> 案件来源</h3>
        <el-form-item required>
          <el-radio-group v-model="form.source">
            <el-radio label="个人案源" size="large" border class="!rounded-xl !mr-4" />
            <el-radio label="公共案源" size="large" border class="!rounded-xl" />
          </el-radio-group>
        </el-form-item>
      </section>

      <section class="bg-white rounded-[32px] p-8 shadow-sm">
        <h3 class="text-lg font-bold text-blue-600 mb-6 flex items-center"><el-icon class="mr-2"><Document /></el-icon> 案件信息</h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <template v-if="['刑事案件', '民事案件', '行政案件', '仲裁案件'].includes(form.case_type)">
            <el-form-item :label="topicLabel">
              <el-select 
                v-model="form.topic_id" 
                filterable 
                remote 
                reserve-keyword 
                placeholder="点击查看或输入关键字搜索" 
                :remote-method="searchTopics" 
                @focus="() => searchTopics('')"
                :loading="searchingTopic" 
                size="large" 
                class="w-full">
                <el-option v-for="item in topicOptions" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="刑事类型" v-if="form.case_type === '刑事案件'">
              <el-select v-model="form.criminal_type" size="large" class="w-full">
                <el-option v-for="t in criminalTypes" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
            <el-form-item label="办案机关省市">
              <el-select 
                v-model="form.region_id" 
                filterable 
                remote 
                reserve-keyword 
                placeholder="点击查看或输入省市名称搜索" 
                :remote-method="searchRegions" 
                @focus="() => searchRegions('')"
                :loading="searchingRegion" 
                size="large" 
                class="w-full">
                <el-option v-for="item in regionOptions" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="办案机关名称">
              <el-input v-model="form.agency_names" placeholder="如：朝阳区人民法院" size="large"/>
            </el-form-item>
          </template>

          <template v-if="form.case_type === '顾问案件'">
            <el-form-item label="服务开始时间">
              <el-date-picker v-model="form.service_start" type="date" placeholder="选择开始日期" size="large" class="w-full" value-format="YYYY-MM-DD" />
            </el-form-item>
            <el-form-item label="服务结束时间">
              <el-date-picker v-model="form.service_end" type="date" placeholder="选择结束日期" size="large" class="w-full" value-format="YYYY-MM-DD" />
            </el-form-item>
          </template>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <el-form-item label="案件名称" required class="!mb-0">
            <el-input v-model="form.title" placeholder="如：张三与李四+案由" class="!rounded-xl" size="large"/>
          </el-form-item>
          <div class="flex space-x-6 items-end pb-2">
            <el-checkbox v-model="form.is_legal_aid" label="是否法律援助" size="large" class="!font-bold text-orange-500" @change="handleLegalAidChange"/>
            <el-checkbox v-model="form.is_foreign" label="是否涉外案件" size="large" class="!font-bold"/>
          </div>
        </div>

        <el-form-item label="案件说明" class="w-full">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入案件详细说明..." />
        </el-form-item>
      </section>

      <section class="bg-white rounded-[32px] p-8 shadow-sm">
        <h3 class="text-lg font-bold text-blue-600 mb-6 flex items-center"><el-icon class="mr-2"><Briefcase /></el-icon> 委托事项</h3>
        <el-form-item label="委托阶段 (可多选)" class="mb-6">
          <el-checkbox-group v-model="form.stages">
            <el-checkbox v-for="stage in currentStages" :key="stage" :label="stage" border class="!rounded-xl !mr-3 !mb-3" />
          </el-checkbox-group>
        </el-form-item>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <el-form-item label="主办律师" required>
            <el-select 
              v-model="lawyerSelections.main" 
              placeholder="请选择主办律师" 
              size="large" 
              class="w-full"
              :disabled="userStore.userInfo.role === '律师'" 
            >
              <el-option v-for="l in realLawyerList" :key="l.id" :label="l.name" :value="l.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="协办律师 (可多选)">
            <el-select v-model="lawyerSelections.co" multiple placeholder="请选择协办律师" size="large" class="w-full">
              <el-option v-for="l in realLawyerList" :key="l.id" :label="l.name" :value="l.id" />
            </el-select>
          </el-form-item>
        </div>
      </section>

      <section class="bg-white rounded-[32px] p-8 shadow-sm">
        <h3 class="text-lg font-bold text-blue-600 mb-6 flex items-center"><el-icon class="mr-2"><Money /></el-icon> 财务信息</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <el-form-item label="收费方式">
            <el-select v-model="form.billing_method" size="large" class="w-full">
              <el-option v-for="m in billingMethods" :key="m" :label="m" :value="m" />
            </el-select>
          </el-form-item>
          <el-form-item label="案件标的额 (元)">
            <el-input-number v-model="form.target_amount" :min="0" :precision="2" :step="1000" size="large" class="!w-full" />
          </el-form-item>
          <el-form-item label="应收金额 (元)">
            <el-input-number v-model="form.receivable" :min="0" :precision="2" :disabled="form.is_legal_aid" size="large" class="!w-full" />
          </el-form-item>
          <el-form-item label="已收金额 (元)">
            <el-input-number v-model="form.received" :min="0" :precision="2" :disabled="form.is_legal_aid" size="large" class="!w-full" />
          </el-form-item>
        </div>
        <el-form-item label="收费说明" class="mb-6">
          <el-input v-model="form.fee_remark" type="textarea" :rows="2" placeholder="发票开具要求等财务说明..." />
        </el-form-item>

        <div class="border border-blue-100 rounded-2xl p-6 bg-slate-50/50">
          <div class="flex justify-between items-center mb-4">
            <p class="font-bold text-gray-700">收入分配比例</p>
            <el-tag :type="Number(totalAllocationRatio) === 100 ? 'success' : 'danger'" effect="dark" round>
              合计: {{ totalAllocationRatio }}%
            </el-tag>
          </div>
          
          <el-table :data="allocations" size="default" border class="!rounded-xl overflow-hidden shadow-sm">
            <el-table-column prop="name" label="办案律师" min-width="150" />
            <el-table-column prop="role_type" label="人员类型" width="120">
              <template #default="scope">
                <el-tag :type="scope.row.role_type === '主办律师' ? 'danger' : 'info'" size="small">{{ scope.row.role_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="分配比例 (%)" width="180">
              <template #default="scope">
                <el-input-number 
                  v-model="scope.row.ratio" 
                  :min="0" 
                  :max="100" 
                  :precision="2" 
                  :controls="false" 
                  class="!w-full" 
                  placeholder="请输入比例"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>

      <div class="bg-white rounded-[32px] p-8 mb-6 shadow-sm flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-bold text-gray-800">收案登记</h2>
          <p class="text-slate-500 mt-2">冲突检索后，案件信息方可提交登记。</p>
        </div>
        <div class="text-right">
          <el-button size="large" type="primary" class="!rounded-xl !px-8 font-bold" :disabled="!hasCheckedConflict" @click="handleSubmit" :loading="submitting">
            确认收案登记
          </el-button>
          <p v-if="!hasCheckedConflict" class="text-xs text-red-500 mt-2">请先完成冲突检索</p>
        </div>
      </div>

    </el-form>

    <el-dialog v-model="entityDialogVisible" :title="`添加 ${activeRole}`" width="500px" class="!rounded-[24px]">
      <el-form :model="entityForm" label-position="top">
        <el-form-item label="主体类型">
          <el-radio-group v-model="entityForm.entity_type">
            <el-radio label="自然人">自然人</el-radio>
            <el-radio label="企业">企业</el-radio>
            <el-radio label="政府">政府</el-radio>
            <el-radio label="社会组织及其它">其它</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="entityForm.entity_type === '自然人' ? '姓名' : '机构名称'" required>
          <el-input v-model="entityForm.name" />
        </el-form-item>
        <el-form-item :label="entityForm.entity_type === '自然人' ? '证件号码' : '统一社会信用代码'" required>
          <el-input v-model="entityForm.id_number" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="entityForm.phone" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="entityDialogVisible = false" class="!rounded-xl">取消</el-button>
        <el-button type="primary" @click="confirmAddEntity" class="!rounded-xl">确定添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="conflictDialogVisible" title="⚠️ 冲突检索警告" width="800px" class="!rounded-[24px]">
      <div v-if="conflicts.length > 0">
        <p class="text-red-600 font-bold mb-4">系统检测到以下人员曾参与过本所其它案件，请仔细核对是否存在利益冲突：</p>
        <el-table :data="conflicts" border stripe class="w-full">
          <el-table-column prop="conflict_name" label="冲突人员" width="100" />
          <el-table-column prop="serial_no" label="流水号" width="120" />
          <el-table-column prop="title" label="案件名称" min-width="180" />
          <el-table-column prop="lawyer" label="承办律师" width="100" />
          <el-table-column prop="status" label="状态" width="100" />
        </el-table>
      </div>
      <div v-else class="text-center py-8">
        <el-icon class="text-green-500 text-5xl mb-4"><CircleCheckFilled /></el-icon>
        <p class="text-lg font-bold text-gray-700">未检索到历史利益冲突记录</p>
      </div>
      <template #footer>
        <el-button v-if="conflicts.length > 0" @click="conflictDialogVisible = false" class="!rounded-xl">返回修改</el-button>
        <el-button type="danger" @click="acceptConflict" class="!rounded-xl font-bold">
          {{ conflicts.length > 0 ? '确认豁免并接受冲突' : '完成检索' }}
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { Collection, UserFilled, Share, Document, Briefcase, Money, CircleCheckFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import request from '../utils/request'
import { useUserStore } from '../store/user'

const userStore = useUserStore()
const router = useRouter()
const formRef = ref(null)

// 字典常量定义
const caseTypes = ['民事案件', '刑事案件', '行政案件', '仲裁案件', '顾问案件', '非诉案件']
const criminalTypes = ['刑事辩护', '刑事代理(被害人委托)', '刑事附带民事(被害人委托)', '刑事附带民事(被告人委托)']
const billingMethods = ['一次性收费', '全风险代理', '半风险代理', '计价收费', '计时收费']

const roleMap = {
  '刑事案件': ['委托人', '犯罪嫌疑人或被告人', '被害人'],
  '民事案件': ['委托人', '原告', '被告', '第三人'],
  '行政案件': ['委托人', '原告', '被告', '第三人'],
  '仲裁案件': ['委托人', '申请人', '被申请人', '第三人'],
  '顾问案件': ['委托人'],
  '非诉案件': ['委托人', '利益相对方', '利害关系人']
}

const stageMap = {
  '刑事案件': ['侦查阶段', '审查起诉', '一审阶段', '二审阶段', '申诉阶段', '抗诉阶段', '执行阶段'],
  '民事案件': ['诉前阶段', '一审阶段', '二审阶段', '再审阶段', '执行阶段', '监督程序', '特殊程序'],
  '行政案件': ['行政复议', '诉前阶段', '一审阶段', '二审阶段', '再审阶段', '执行阶段', '监督程序', '特殊程序'],
  '仲裁案件': ['裁前阶段', '仲裁阶段', '撤销仲裁', '执行阶段', '特殊程序'],
  '顾问案件': [],
  '非诉案件': []
}

// 动态数据变量
const realLawyerList = ref([])
const topicOptions = ref([])
const regionOptions = ref([])
const searchingTopic = ref(false)
const searchingRegion = ref(false)

const fetchLawyers = async () => {
  try {
    realLawyerList.value = await request.get('/dicts/lawyers')
  } catch (error) {
    console.error('拉取律师列表失败', error)
  }
}

// 案由异步搜索（支持空查询）
const searchTopics = async (query) => {
  searchingTopic.value = true
  try {
    let category = 'civil_cause'
    if (form.case_type === '刑事案件') category = 'criminal_charge'
    else if (form.case_type === '行政案件') category = 'admin_cause'

    topicOptions.value = await request.get(`/dicts/topics?category=${category}&keyword=${query || ''}`)
  } catch (error) {
    console.error(error)
  } finally {
    searchingTopic.value = false
  }
}

// 省市异步搜索（支持空查询）
const searchRegions = async (query) => {
  searchingRegion.value = true
  try {
    regionOptions.value = await request.get(`/dicts/topics?category=region&keyword=${query || ''}`)
  } catch (error) {
    console.error(error)
  } finally {
    searchingRegion.value = false
  }
}

onMounted(async () => {
  await fetchLawyers() 
  if (userStore.userInfo.role === '律师') {
    lawyerSelections.main = userStore.userInfo.id
  }
})

const handleCaseTypeChange = () => {
  form.entities = []
  form.stages = []
  form.topic_id = null 
  topicOptions.value = [] 
  hasCheckedConflict.value = false 
}

// 核心响应式表单
const form = reactive({
  title: '', case_type: '民事案件', source: '个人案源', is_conflict_waived: false, description: '',
  entities: [], criminal_type: '', topic_id: null, region_id: null, agency_names: '',
  is_legal_aid: false, is_foreign: false, service_start: null, service_end: null,
  stages: [], billing_method: '一次性收费', target_amount: 0, receivable: 0, received: 0, fee_remark: ''
})

const lawyerSelections = reactive({ main: null, co: [] })
const allocations = ref([])

// 计算比例合计
const totalAllocationRatio = computed(() => {
  return allocations.value.reduce((sum, curr) => sum + Number(curr.ratio || 0), 0).toFixed(2)
})

// 监听律师变动，动态生成分配表格
watch([() => lawyerSelections.main, () => lawyerSelections.co], ([mainId, coIds]) => {
  const newAlloc = []
  if (mainId) {
    const lw = realLawyerList.value.find(l => l.id === mainId)
    const existing = allocations.value.find(a => a.lawyer_id === mainId)
    newAlloc.push({
      lawyer_id: mainId, name: lw ? lw.name : '', role_type: '主办律师',
      ratio: existing ? existing.ratio : (coIds.length === 0 ? 100 : 0)
    })
  }
  coIds.forEach(id => {
    const lw = realLawyerList.value.find(l => l.id === id)
    const existing = allocations.value.find(a => a.lawyer_id === id)
    newAlloc.push({
      lawyer_id: id, name: lw ? lw.name : '', role_type: '协办律师', ratio: existing ? existing.ratio : 0
    })
  })
  allocations.value = newAlloc
}, { deep: true })

const currentRoles = computed(() => roleMap[form.case_type] || [])
const currentStages = computed(() => stageMap[form.case_type] || [])
const topicLabel = computed(() => {
  if (form.case_type === '刑事案件') return '刑法罪名'
  if (form.case_type === '行政案件') return '行政案由'
  if (form.case_type === '仲裁案件') return '仲裁案由'
  return '民事案由'
})

const handleLegalAidChange = (val) => {
  if (val) {
    form.receivable = 0
    form.received = 0
  }
}

// 案件人员
const entityDialogVisible = ref(false)
const activeRole = ref('')
const entityForm = reactive({ entity_type: '自然人', name: '', id_type: '身份证', id_number: '', phone: '' })

const getEntitiesByRole = (role) => form.entities.filter(e => e.role_name === role)

const openEntityDialog = (role) => {
  activeRole.value = role
  Object.assign(entityForm, { entity_type: '自然人', name: '', id_type: '身份证', id_number: '', phone: '' })
  entityDialogVisible.value = true
}

const confirmAddEntity = () => {
  if (!entityForm.name || !entityForm.id_number) {
    ElMessage.warning('名称和证件号码为必填项！')
    return
  }
  form.entities.push({ ...entityForm, role_name: activeRole.value })
  hasCheckedConflict.value = false 
  entityDialogVisible.value = false
}

const removeEntity = (entity) => {
  const index = form.entities.indexOf(entity)
  if (index > -1) form.entities.splice(index, 1)
  hasCheckedConflict.value = false 
}

// 冲突检索
const checkingConflict = ref(false)
const hasCheckedConflict = ref(false)
const conflictDialogVisible = ref(false)
const conflicts = ref([])

const doConflictCheck = async () => {
  if (form.entities.length === 0) {
    ElMessage.warning('请先添加至少一名案件人员！')
    return
  }
  checkingConflict.value = true
  try {
    const res = await request.post('/cases/conflict-check', { entities: form.entities })
    conflicts.value = res.conflicts
    conflictDialogVisible.value = true
  } catch (error) {
    console.error(error)
  } finally {
    checkingConflict.value = false
  }
}

const acceptConflict = () => {
  form.is_conflict_waived = conflicts.value.length > 0
  hasCheckedConflict.value = true
  conflictDialogVisible.value = false
  ElMessage.success('冲突检索完成，可以提交收案登记。')
}

// 提交登记
const submitting = ref(false)

const handleSubmit = async () => {
  if (!form.title || !lawyerSelections.main) {
    ElMessage.error('请确保已填写案件名称并选择了主办律师！')
    return
  }
  
  if (Number(totalAllocationRatio.value) !== 100) {
    ElMessage.error(`当前人员分配比例总和为 ${totalAllocationRatio.value}%，必须强制等于 100%！`)
    return
  }

  const lawyersPayload = allocations.value.map(a => ({
    lawyer_id: a.lawyer_id,
    role_type: a.role_type,
    allocation_ratio: Number(a.ratio)
  }))

  const payload = { ...form, lawyers: lawyersPayload }

  submitting.value = true
  try {
    const res = await request.post('/cases/register', payload)
    ElMessageBox.alert(`流水号：${res.serial_no}，请等待风控审核生成案号。`, '✅ 收案登记成功', {
      confirmButtonText: '前往控制台',
      callback: () => {
        router.push('/dashboard')
      }
    })
  } catch (error) {
    console.error('提交失败', error)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
:deep(.el-radio-button__inner) {
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  padding: 12px 24px;
}
:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  box-shadow: none !important;
}
</style>