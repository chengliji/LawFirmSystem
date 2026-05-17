<template>
  <div class="bg-slate-50 min-h-screen pb-12 space-y-6">
    
    <section>
      <h3 class="text-lg font-bold text-gray-700 mb-4 px-2">业务状态</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div v-for="(item, index) in statusCards" :key="index" 
             class="bg-white rounded-[32px] p-6 shadow-sm hover:shadow-md transition-shadow flex items-center space-x-4 border border-transparent hover:border-blue-100">
          <div :class="`w-14 h-14 rounded-2xl flex items-center justify-center text-white ${item.color}`">
            <el-icon :size="28"><component :is="item.icon" /></el-icon>
          </div>
          <div>
            <p class="text-slate-500 text-sm font-medium">{{ item.label }}</p>
            <p class="text-3xl font-black text-gray-800">{{ stats[item.label] || 0 }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="bg-white rounded-[32px] p-8 shadow-sm">
      <el-form :model="searchForm" class="flex flex-wrap gap-4 items-end">
        <el-form-item label="关键字检索" class="!mb-0 w-64">
          <el-input v-model="searchForm.keyword" placeholder="案号/流水号/案件名称" class="!rounded-xl" clearable @clear="fetchData" />
        </el-form-item>
        <el-form-item label="案件类型" class="!mb-0 w-48">
          <el-select v-model="searchForm.case_type" placeholder="全部类型" clearable @change="fetchData">
            <el-option v-for="t in caseTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="案件状态" class="!mb-0 w-48">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable @change="fetchData">
            <el-option v-for="s in Object.keys(stats)" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>

        <el-form-item class="!mb-0">
          <el-button type="primary" icon="Search" class="!rounded-xl font-bold px-6" @click="fetchData">搜索</el-button>
          <el-button icon="Refresh" class="!rounded-xl" @click="resetSearch">重置</el-button>
          
          <template v-if="['管理员', '风控'].includes(userStore.userInfo.role)">
            <el-button type="warning" plain icon="Download" class="!rounded-xl ml-4" @click="exportBatchCSV">导出历史案件</el-button>
            <el-button type="success" plain icon="Upload" class="!rounded-xl ml-4" @click="importDialogVisible = true">导入历史案件</el-button>
          </template>
        </el-form-item>
      </el-form>
    </section>

    <section class="bg-white rounded-[32px] p-8 shadow-sm">
      <div class="flex justify-between items-center mb-6">
        <h3 class="text-lg font-bold text-gray-700">案件列表</h3>
      </div>
      
      <el-table v-loading="loading" :data="tableData" stripe class="w-full !rounded-xl overflow-hidden text-sm">
        <el-table-column prop="serial_no" label="流水号" width="100" />
        <el-table-column prop="case_no" label="案号" min-width="180">
          <template #default="scope">
            <div class="relative inline-block w-full">
              <span :class="scope.row.case_no === '等待生成' ? 'text-slate-400 italic' : 'font-bold text-blue-700'">
                {{ scope.row.case_no }}
              </span>
              
              <div v-if="scope.row.process_tag === '案件作废'" 
                   class="absolute -top-1 -right-2 transform rotate-12 border-2 border-red-500 text-red-500 text-xs font-black px-1.5 py-0.5 rounded shadow-sm bg-white/90 select-none pointer-events-none z-10 opacity-90 tracking-widest"
                   style="border-style: double;">
                作废
              </div>
              <div v-if="scope.row.process_tag === '合同解除'" 
                   class="absolute -top-1 -right-2 transform rotate-12 border-2 border-orange-500 text-orange-500 text-xs font-black px-1.5 py-0.5 rounded shadow-sm bg-white/90 select-none pointer-events-none z-10 opacity-90 tracking-widest"
                   style="border-style: double;">
                解除
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="案件名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="case_type" label="案件类型" width="120">
          <template #default="scope">
            <el-tag size="small" type="info" round effect="plain">{{ scope.row.case_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="main_lawyer" label="主办律师" width="120" />
        <el-table-column prop="reg_date" label="登记日期" width="120" />
        <el-table-column prop="status" label="当前状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" effect="dark" round class="font-bold border-none">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right" align="center">
          <template #default="scope">
            
            <template v-if="['管理员', '风控'].includes(userStore.userInfo.role)">
              <el-button v-if="scope.row.status === '案件审核'" type="danger" size="small" round @click="handleApprove(scope.row)">
                审核收案(生成案号)
              </el-button>
              <el-button v-if="scope.row.status === '合同审核'" type="danger" size="small" round @click="handleApprove(scope.row)">
                审核合同
              </el-button>
              <el-button v-if="scope.row.status === '结案审核'" type="danger" size="small" round @click="handleApprove(scope.row)">
                审核档案(结案)
              </el-button>
            </template>

            <template v-if="userStore.userInfo.role === '律师'">
              <el-button v-if="scope.row.status === '合同审核'" type="primary" size="small" plain round @click="openUpload(scope.row, 'contract')">
                上传合同
              </el-button>
              <el-button v-if="scope.row.status === '结案审核'" type="success" size="small" plain round @click="openUpload(scope.row, 'archive')">
                上传档案
              </el-button>
            </template>

            <el-button type="info" size="small" text bg round @click="goToDetail(scope.row.id)">案件详情</el-button>
            
            <el-button v-if="userStore.userInfo.role === '管理员'" type="danger" size="small" text bg round @click="handleDelete(scope.row.id)">删除</el-button>

          </template>
        </el-table-column>
      </el-table>

      <div class="mt-6 flex justify-end">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
          class="!font-bold"
        />
      </div>
    </section>

    <el-dialog v-model="uploadDialog.visible" :title="uploadDialog.type === 'contract' ? '上传委托合同' : '上传归档资料'" width="500px" class="!rounded-[24px]">
      <div class="p-4 text-center">
        <el-upload
          drag
          action="#"
          :http-request="customUploadRequest"
          :show-file-list="false"
          class="w-full"
        >
          <el-icon class="el-icon--upload text-blue-500"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或 <em>点击选择文件自动上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip text-slate-500 mt-2">支持 PDF/JPG/PNG，文件将直接保存至服务器 uploads 目录</div>
          </template>
        </el-upload>
      </div>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" title="导入历史案件 (CSV)" width="500px" class="!rounded-[24px]">
      <div class="p-4 text-center">
        <el-upload
          drag
          action="#"
          :http-request="customImportRequest"
          :show-file-list="false"
          accept=".csv"
          class="w-full"
        >
          <el-icon class="el-icon--upload text-green-500"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将 CSV 表格拖到此处，或 <em>点击选择文件</em>
          </div>
          <template #tip>
            <div class="el-upload__tip text-slate-500 mt-2">请确保上传的 CSV 模板字段与导出字段完全一致</div>
          </template>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false" class="!rounded-xl">关闭</el-button>
        <el-button type="success" plain @click="downloadTemplate" class="!rounded-xl font-bold">下载导入模板</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { DocumentChecked, Document, Files, Check, UploadFilled } from '@element-plus/icons-vue'
import request from '../utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '../store/user'

const userStore = useUserStore() // 初始化 Store 以获取角色权限
const router = useRouter()
const loading = ref(false)
const importDialogVisible = ref(false)

// 顶部状态统计数据
const stats = ref({
  '案件审核': 0, '合同审核': 0, '结案审核': 0, '已结案': 0
})

const statusCards = [
  { label: '案件审核', icon: Document, color: 'bg-orange-400' },
  { label: '合同审核', icon: DocumentChecked, color: 'bg-blue-500' },
  { label: '结案审核', icon: Files, color: 'bg-purple-500' },
  { label: '已结案', icon: Check, color: 'bg-green-500' }
]

// 搜索与表格数据
const caseTypes = ['民事案件', '刑事案件', '行政案件', '仲裁案件', '顾问案件', '非诉案件']
const searchForm = reactive({ keyword: '', case_type: '', status: '', dateRange: [] })
const tableData = ref([])
const pagination = reactive({ page: 1, size: 10, total: 0 })

// 状态标签颜色匹配
const getStatusType = (status) => {
  const map = { '案件审核': 'warning', '合同审核': 'primary', '结案审核': 'info', '已结案': 'success' }
  return map[status] || 'info'
}

// 获取数据核心方法
const fetchData = async () => {
  loading.value = true
  try {
    // 获取统计数据
    stats.value = await request.get('/cases/stats')
    
    // 获取列表数据
    const res = await request.get('/cases/list', { 
      params: { 
        page: pagination.page, 
        size: pagination.size,
        ...searchForm 
      } 
    })
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('获取案件列表失败', error)
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.case_type = ''
  searchForm.status = ''
  searchForm.dateRange = []
  pagination.page = 1
  fetchData()
}

// 管理员删除案件逻辑
const handleDeleteCase = async (id) => {
  try {
    await ElMessageBox.confirm('确定要彻底删除该案件吗？此底层及关联数据将全部清空，操作不可逆！', '高危操作', { type: 'error' })
    await request.delete(`/cases/${id}`)
    ElMessage.success('案件已彻底删除')
    fetchData()
  } catch (err) {}
}

// 批量导出逻辑
const exportBatchCSV = async () => {
  try {
    ElMessage.info('正在提取历史案件生成宽表台账，请稍候...')
    
    // 构造日期参数
    let url = '/cases/export-batch'
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      url += `?start_date=${searchForm.dateRange[0]}&end_date=${searchForm.dateRange[1]}`
    }

    // 调用批量导出接口
    const response = await request.get(url, { responseType: 'blob' })
    
    // 利用 Blob 触发文件下载
    const downloadUrl = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = downloadUrl
    
    // 如果选择了日期，文件名带上日期范围提示
    let fileName = '历史案件台账.csv'
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      fileName = `历史案件_${searchForm.dateRange[0]}至${searchForm.dateRange[1]}.csv`
    }
    
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('历史案件导出成功！此文件可直接作为导入模板使用。')
  } catch (error) {
    console.error('批量导出失败', error)
    ElMessage.error('导出失败，请检查网络或权限')
  }
}

// 操作交互
const uploadDialog = reactive({ visible: false, type: '', currentRowId: null })

const openUpload = (row, type) => {
  uploadDialog.type = type
  uploadDialog.currentRowId = row.id
  uploadDialog.visible = true
}

// 风控审核流转逻辑
const handleApprove = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要通过该案件的【${row.status}】阶段吗？操作后不可逆。`, 
      '系统提示', 
      { confirmButtonText: '确定通过', cancelButtonText: '取消', type: 'warning' }
    )
    const res = await request.post(`/cases/approve/${row.id}`)
    ElMessage.success(res.message)
    fetchData()
  } catch (error) {
    if (error !== 'cancel') console.error(error)
  }
}

const downloadTemplate = () => {
  ElMessage.info('模板正在生成，这与导出单案的 CSV 结构相同。')
}

const customImportRequest = async (options) => {
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    const res = await request.post('/cases/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success(res.message)
    importDialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error('导入失败，请检查文件格式')
  }
}

// 真实的物理文件上传逻辑
const customUploadRequest = async (options) => {
  const loadingInstance = ElMessage({ message: '正在上传到服务器...', type: 'info', duration: 0 })
  
  // 使用 FormData 来上传物理文件
  const formData = new FormData()
  formData.append('case_id', uploadDialog.currentRowId)
  formData.append('doc_type', uploadDialog.type === 'contract' ? '委托合同' : '归档资料')
  formData.append('file', options.file)

  try {
    await request.post('/cases/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    loadingInstance.close()
    ElMessage.success('文件上传成功，已入库！')
    uploadDialog.visible = false
    fetchData()
  } catch (error) {
    loadingInstance.close()
    options.onError(error)
    ElMessage.error('上传失败，请检查网络或文件格式')
  }
}

const goToDetail = (id) => {
  ElMessage.info('正在进入案件详情页...')
  router.push(`/case-detail/${id}`)
}

onMounted(() => {
  fetchData()
})

// 管理员彻底删除案件逻辑
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要彻底删除该案件及其所有底层关联数据吗？此操作极度危险且不可逆！', '高危操作警告', {
      confirmButtonText: '确认彻底删除',
      cancelButtonText: '取消',
      type: 'error'
    })
    
    await request.delete(`/cases/${id}`)
    ElMessage.success('该案件已被彻底删除')
    fetchData()
  } catch (err) {
    if (err !== 'cancel') console.error('删除失败', err)
  }
}
</script>

<style scoped>
:deep(.el-table th.el-table__cell) {
  background-color: #f8fafc;
  color: #475569;
  font-weight: bold;
}
</style>