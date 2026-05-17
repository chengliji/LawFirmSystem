<template>
  <div class="space-y-6 pb-6">
    
    <section>
      <h3 class="text-lg font-bold text-gray-700 mb-4 px-2">业务概览</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white rounded-[32px] p-8 shadow-sm hover:shadow-md transition-shadow flex items-center space-x-6 relative overflow-hidden group">
          <div class="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
            <el-icon :size="32"><TrendCharts /></el-icon>
          </div>
          <div>
            <p class="text-slate-500 text-sm font-medium mb-1">本月案件</p>
            <p class="text-3xl font-black text-gray-800">{{ metrics.month_cases }} <span class="text-sm font-normal text-green-500 ml-2"></span></p>
          </div>
        </div>
        <div class="bg-white rounded-[32px] p-8 shadow-sm hover:shadow-md transition-shadow flex items-center space-x-6 group">
          <div class="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
            <el-icon :size="32"><FolderChecked /></el-icon>
          </div>
          <div>
            <p class="text-slate-500 text-sm font-medium mb-1">累计案件</p>
            <p class="text-3xl font-black text-gray-800">{{ metrics.total_cases }}</p>
          </div>
        </div>
        <div class="bg-white rounded-[32px] p-8 shadow-sm hover:shadow-md transition-shadow flex items-center space-x-6 group">
          <div class="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
            <el-icon :size="32"><Avatar /></el-icon>
          </div>
          <div>
            <p class="text-slate-500 text-sm font-medium mb-1">服务客户</p>
            <p class="text-3xl font-black text-gray-800">{{ metrics.total_clients }}</p>
          </div>
        </div>
      </div>
    </section>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <section class="bg-white rounded-[32px] p-8 shadow-sm flex flex-col">
        <h3 class="text-lg font-bold text-gray-700 mb-6">案件类型分布</h3>
        <div ref="chartRef" class="w-full flex-1 min-h-[300px]"></div>
      </section>

      <section class="bg-white rounded-[32px] p-8 shadow-sm">
        <h3 class="text-lg font-bold text-gray-700 mb-6">快速链接</h3>
        <div class="grid grid-cols-2 gap-4">
          <a v-for="(link, index) in quickLinks" :key="index" :href="link.url" target="_blank" 
             class="flex flex-col items-center justify-center p-6 bg-slate-50 rounded-[32px] hover:bg-blue-50 border border-transparent hover:border-blue-100 transition-all group">
            <el-icon :size="28" class="text-blue-500 mb-3 group-hover:scale-110 transition-transform"><Link /></el-icon>
            <span class="text-gray-700 font-medium group-hover:text-blue-700">{{ link.name }}</span>
          </a>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { TrendCharts, FolderChecked, Avatar, Link } from '@element-plus/icons-vue'
import request from '../utils/request'

const chartRef = ref(null)
let myChart = null

// 响应式指标数据
const metrics = ref({
  month_cases: 0,
  total_cases: 0,
  total_clients: 0
})

const quickLinks = [
  { name: '人民法院案例库', url: 'https://rmfyalk.court.gov.cn/' },
  { name: '中国裁判文书网', url: 'https://wenshu.court.gov.cn/' },
  { name: '执行信息公开网', url: 'http://zxgk.court.gov.cn/' },
  { name: '全国人大法律库', url: 'http://www.npc.gov.cn/npc/c2/c30834/flfg.shtml' }
]

const initChart = (pieData) => {
  if (!myChart) myChart = echarts.init(chartRef.value)
  const option = {
    tooltip: { trigger: 'item' },
    legend: { bottom: '0%', left: 'center' },
    color: ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe'],
    series: [
      {
        name: '案件类型',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 20, fontWeight: 'bold' } },
        labelLine: { show: false },
        data: pieData
      }
    ]
  }
  myChart.setOption(option)
}

// 拉取真实数据
const fetchDashboardData = async () => {
  try {
    const res = await request.get('/cases/dashboard/metrics')
    metrics.value.month_cases = res.month_cases
    metrics.value.total_cases = res.total_cases
    metrics.value.total_clients = res.total_clients
    initChart(res.pie_data.length > 0 ? res.pie_data : [{ name: '暂无数据', value: 0 }])
  } catch (error) {
    console.error('获取控制台数据失败', error)
  }
}

onMounted(() => {
  fetchDashboardData()
  window.addEventListener('resize', () => myChart && myChart.resize())
})

onBeforeUnmount(() => {
  if (myChart) {
    window.removeEventListener('resize', () => myChart.resize())
    myChart.dispose()
  }
})
</script>