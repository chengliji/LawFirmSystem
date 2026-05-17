<template>
  <div class="bg-slate-50 min-h-screen pb-12">
    
    <div class="bg-white rounded-[32px] p-8 mb-6 shadow-sm flex justify-between items-center border-l-4 border-blue-600">
      <div>
        <h2 class="text-2xl font-bold text-gray-800">律师人员管理</h2>
        <p class="text-slate-500 mt-2">统一管理所内律师账号。注意：系统禁止删除律师，离职人员请修改其状态为“离职”。</p>
      </div>
      <el-button type="primary" size="large" class="!rounded-xl font-bold px-6" icon="Plus" @click="openAddDialog">
        新增律师账户
      </el-button>
    </div>

    <section class="bg-white rounded-[32px] p-8 shadow-sm">
      <el-table v-loading="loading" :data="lawyers" stripe class="w-full !rounded-xl overflow-hidden text-sm">
        <el-table-column prop="full_name" label="姓名" min-width="120" class-name="font-bold text-blue-700" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column prop="username" label="登录账号" min-width="120" />
        <el-table-column prop="license_type" label="执业证类别" min-width="120">
          <template #default="scope">
            <el-tag :type="scope.row.license_type === '专职律师' ? 'primary' : 'warning'" effect="plain" round>
              {{ scope.row.license_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="license_no" label="执业证号" min-width="160" />
        <el-table-column prop="phone" label="联系电话" min-width="140" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === '在职' ? 'success' : 'info'" effect="dark" round class="border-none font-bold">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="scope">
            <el-button type="primary" size="small" plain round icon="Edit" @click="openEditDialog(scope.row)">编辑</el-button>
            <el-button type="danger" size="small" plain round icon="Lock" @click="openPasswordDialog(scope.row)">密码</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="formDialog.visible" :title="formDialog.isEdit ? '编辑律师信息' : '新增律师账户'" width="600px" class="!rounded-[24px]">
      <el-form :model="formData" label-width="100px" class="pr-6">
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="姓名" required>
            <el-input v-model="formData.full_name" class="!rounded-xl" />
          </el-form-item>
          <el-form-item label="性别">
            <el-select v-model="formData.gender" class="w-full">
              <el-option label="男" value="男" />
              <el-option label="女" value="女" />
              <el-option label="未知" value="未知" />
            </el-select>
          </el-form-item>
          
          <template v-if="!formDialog.isEdit">
            <el-form-item label="登录账号" required>
              <el-input v-model="formData.username" placeholder="建议使用拼音" />
            </el-form-item>
            <el-form-item label="初始密码" required>
              <el-input v-model="formData.password" show-password />
            </el-form-item>
          </template>

          <el-form-item label="执业证类别">
            <el-select v-model="formData.license_type" class="w-full">
              <el-option label="专职律师" value="专职律师" />
              <el-option label="兼职律师" value="兼职律师" />
            </el-select>
          </el-form-item>
          <el-form-item label="执业证号">
            <el-input v-model="formData.license_no" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="formData.phone" />
          </el-form-item>
          
          <el-form-item label="在职状态" v-if="formDialog.isEdit">
            <el-radio-group v-model="formData.status">
              <el-radio label="在职">在职 (可登录)</el-radio>
              <el-radio label="离职">离职 (禁止登录)</el-radio>
            </el-radio-group>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="formDialog.visible = false" class="!rounded-xl">取消</el-button>
        <el-button type="primary" @click="submitForm" class="!rounded-xl font-bold" :loading="submitting">确定保存</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const submitting = ref(false)
const lawyers = ref([])

// 权限拦截器：如果律师强行通过 URL 访问，直接踢回控制台
onMounted(() => {
  if (!['管理员', '风控'].includes(userStore.userInfo.role)) {
    ElMessage.error('越权访问，已拦截')
    router.replace('/dashboard')
    return
  }
  fetchLawyers()
})

const fetchLawyers = async () => {
  loading.value = true
  try {
    lawyers.value = await request.get('/users/lawyers')
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 新增与编辑逻辑
const formDialog = reactive({ visible: false, isEdit: false, currentId: null })
const formData = reactive({
  username: '', password: '', full_name: '', gender: '男', license_no: '', license_type: '专职律师', phone: '', status: '在职'
})

const openAddDialog = () => {
  formDialog.isEdit = false
  Object.assign(formData, { username: '', password: '', full_name: '', gender: '男', license_no: '', license_type: '专职律师', phone: '', status: '在职' })
  formDialog.visible = true
}

const openEditDialog = (row) => {
  formDialog.isEdit = true
  formDialog.currentId = row.id
  Object.assign(formData, row)
  formDialog.visible = true
}

const submitForm = async () => {
  if (!formData.full_name) return ElMessage.warning('姓名不能为空')
  
  submitting.value = true
  try {
    if (formDialog.isEdit) {
      await request.put(`/users/lawyers/${formDialog.currentId}`, formData)
      ElMessage.success('信息更新成功')
    } else {
      if (!formData.username || !formData.password) return ElMessage.warning('账号和密码不能为空')
      await request.post('/users/lawyers', formData)
      ElMessage.success('新增律师成功')
    }
    formDialog.visible = false
    fetchLawyers()
  } catch (error) {
    console.error(error)
  } finally {
    submitting.value = false
  }
}

// 修改密码逻辑
const openPasswordDialog = (row) => {
  ElMessageBox.prompt(`请输入为【${row.full_name}】设置的新密码：`, '修改密码', {
    confirmButtonText: '确认修改',
    cancelButtonText: '取消',
    inputType: 'password',
    inputPattern: /.+/,
    inputErrorMessage: '密码不能为空',
    customClass: '!rounded-[24px]'
  }).then(async ({ value }) => {
    try {
      await request.put(`/users/lawyers/${row.id}/password`, { new_password: value })
      ElMessage.success('密码修改成功！')
    } catch (error) {
      console.error(error)
    }
  }).catch(() => {})
}
</script>