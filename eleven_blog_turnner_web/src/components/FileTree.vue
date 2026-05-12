<template>
  <t-card
    class="file-tree-card"
    :bordered="false"
  >
    <!-- 自定义头部 -->
    <div class="custom-header">
      <div class="card-title">文件树</div>
      <div class="header-actions">
        <t-input
          v-model="filterText"
          placeholder="搜索..."
          clearable
          class="search-input"
          @input="handleFilter"
        >
          <template #prefix-icon>
            <t-icon name="search" />
          </template>
        </t-input>
        <t-dropdown :options="createOptions" @click="handleCreateAction">
          <t-button variant="outline">
            <template #icon>
              <t-icon name="plus" />
            </template>
          </t-button>
        </t-dropdown>
      </div>
    </div>

    <div class="file-tree-content">
      <t-tree
        ref="treeRef"
        :data="filteredTreeData"
        :expanded="expandedNodes"
        :activable="true"
        :multiple="false"
        :load-more="loadMore"
        :lazy="false"
        :expand-on-click-node="true"
        :filter="filterByText"
        :draggable="true"
        hover
        line
        @expand="handleTreeExpand"
        @drag-start="handleDragStart"
        @drag-end="handleDragEnd"
        @drag-over="handleDragOver"
        @drag-leave="handleDragLeave"
        @drop="handleDrop"
      >
        <template #icon="{ node }">
          <t-icon :name="getNodeIcon(node)" />
        </template>
        <template #label="{ node }">
          <div class="tree-node-label">
            <span>{{ (getRealNodeData(node) as TreeNode).label }}</span>
            <!-- 三点按钮 -->
            <div
              v-if="(getRealNodeData(node) as TreeNode).type !== 'root'"
              class="custom-dropdown"
            >
              <t-button
                variant="text"
                size="small"
                class="node-action-btn"
                @click.stop="handleMenuClick($event, node)"
              >
                <t-icon name="ellipsis" />
              </t-button>
            </div>
          </div>
        </template>
      </t-tree>
    </div>


    <!-- 新建文件夹弹窗 -->
    <t-dialog v-model:visible="showFolderDialog" header="新建文件夹" :footer="false" width="400px">
      <t-form @submit="handleCreateFolder">
        <t-form-item label="文件夹名称" name="folderName">
          <t-input v-model="newFolderForm.name" placeholder="请输入文件夹名称" />
        </t-form-item>
        <t-form-item label="类型" name="folderType">
          <t-select v-model="newFolderForm.type" placeholder="请选择文件夹类型">
            <t-option value="note" label="笔记文件夹" />
            <t-option value="article" label="文章文件夹" />
          </t-select>
        </t-form-item>
        <t-form-item label="父级文件夹" name="parentFolder">
          <t-tree-select
            v-model="newFolderForm.parent_id"
            :data="folderOnlyTree"
            placeholder="请选择父级文件夹（可选）"
            clearable
          />
        </t-form-item>
        <t-form-item>
          <t-space>
            <t-button type="submit" theme="primary">创建</t-button>
            <t-button @click="showFolderDialog = false">取消</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- 重命名弹窗 -->
    <t-dialog v-model:visible="showRenameDialog" header="重命名" :footer="false" width="400px">
      <t-form @submit="handleRenameSubmit">
        <t-form-item label="名称" name="name">
          <t-input v-model="renameForm.name" placeholder="请输入新的名称" />
        </t-form-item>
        <t-form-item>
          <t-space>
            <t-button type="submit" theme="primary">确定</t-button>
            <t-button @click="showRenameDialog = false">取消</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </t-dialog>
  </t-card>

  <!-- 全局下拉菜单（最外层） -->
  <div
    v-if="menuVisible && currentMenuNode"
    class="global-dropdown-menu"
    :style="{ position: 'fixed', top: menuY + 'px', left: menuX + 'px', zIndex: 999999 }"
  >
    <div
      v-for="operation in getNodeOperations(getRealNodeData(currentMenuNode) as TreeNode)"
      :key="operation.value"
      class="dropdown-item"
      @click.stop="handleMenuItemClick(operation)"
    >
      <t-icon :name="operation.icon" class="item-icon" />
      <span>{{ operation.content }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { fileTreeApi } from '@/api/fileTree'

interface TreeNode {
  id: string
  label: string
  type: 'folder' | 'note' | 'article' | 'root'
  categoryId?: string
  parentId?: string
  children?: TreeNode[]
  data?: any
  isLeaf?: boolean
}

interface FolderForm {
  name: string
  type: 'note' | 'article'
  parent_id?: string
}

interface RenameForm {
  name: string
}

interface NodeOperation {
  content: string
  value: string
  icon: string
}

const router = useRouter()
const loading = ref(false)
const treeRef = ref()
const fileTreeData = ref<TreeNode[]>([])
const expandedNodes = ref<string[]>([])
const showFolderDialog = ref(false)
const showRenameDialog = ref(false)
const filterText = ref('')
const filterByText = ref<((node: any) => boolean) | null>(null)
// 菜单相关
const menuVisible = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const currentMenuNode = ref<any>(null)

const newFolderForm = reactive<FolderForm>({
  name: '',
  type: 'note',
  parent_id: undefined
})

const renameForm = reactive<RenameForm>({
  name: ''
})

const selectedNode = ref<TreeNode | null>(null)

const createOptions = [
  { content: '新建笔记', value: 'note', id: 'note' },
  { content: '新建文章', value: 'article', id: 'article' },
  { content: '新建文件夹', value: 'folder', id: 'folder' }
]

const folderOptions = [
  { content: '笔记文件夹', value: 'note', id: 'note' },
  { content: '文章文件夹', value: 'article', id: 'article' }
]

// 点击外部关闭下拉菜单
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Element
  if (!target.closest('.custom-dropdown') && !target.closest('.global-dropdown-menu') && menuVisible.value) {
    console.log('点击外部区域，关闭下拉菜单')
    menuVisible.value = false
    currentMenuNode.value = null
  }
}

onMounted(() => {
  fetchFileTree()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 获取真实的节点数据
const getRealNodeData = (node: any): TreeNode => {
  // 如果是 TreeNodeModel，先获取 __tdesign_tree-node__，然后获取其 data 属性
  let tdesignNode: any = null
  if (node['__tdesign_tree-node__']) {
    tdesignNode = node['__tdesign_tree-node__']
  }

  if (tdesignNode && tdesignNode.data) {
    return tdesignNode.data
  }

  if (node.data) {
    return node.data
  }

  return node
}

// 获取节点的唯一标识符
const getNodeKey = (node: any): string => {
  const realNode = getRealNodeData(node)
  return realNode.id || realNode.value || String(Math.random())
}

// 显示下拉菜单
const handleMenuClick = (event: MouseEvent, node: any) => {
  const realNode = getRealNodeData(node)
  console.log('点击三点按钮 - 节点:', realNode.label, '节点类型:', realNode.type)

  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()

  menuX.value = rect.left
  menuY.value = rect.bottom + 4

  currentMenuNode.value = node
  menuVisible.value = true
}

// 处理菜单项点击
const handleMenuItemClick = (operation: NodeOperation) => {
  const realNode = getRealNodeData(currentMenuNode.value)
  console.log('点击菜单项 - 操作:', operation.content, '节点:', realNode.label)

  menuVisible.value = false
  currentMenuNode.value = null

  handleNodeOperation(operation, realNode)
}

// 过滤后的树数据
const filteredTreeData = computed(() => {
  return fileTreeData.value
})

// 只包含文件夹的树，用于父级选择
const folderOnlyTree = computed(() => {
  const convertToTreeSelect = (nodes: TreeNode[]): any[] => {
    return nodes
      .filter(node => node.type === 'folder')
      .map(node => ({
        value: node.id,
        label: node.label,
        children: node.children ? convertToTreeSelect(node.children) : undefined
      }))
  }
  return convertToTreeSelect(fileTreeData.value)
})

const fetchFileTree = async () => {
  loading.value = true
  try {
    const tree = await fileTreeApi.getFileTree()
    fileTreeData.value = tree
    expandedNodes.value = collectFolderIds(tree)
  } catch (error) {
    console.error('Failed to fetch file tree:', error)
    MessagePlugin.error('获取文件树失败')
  } finally {
    loading.value = false
  }
}

// 递归收集所有文件夹ID
const collectFolderIds = (nodes: TreeNode[]): string[] => {
  const ids: string[] = []
  const collect = (nodeList: TreeNode[]) => {
    for (const node of nodeList) {
      if (node.type === 'folder') {ids.push(node.id)
        if (node.children) {
          collect(node.children)
        }
      }
    }
  }
  collect(nodes)
  return ids
}

// 获取节点图标
const getNodeIcon = (node: any) => {
  const realNode = getRealNodeData(node)
  if (realNode.type === 'folder') {
    return realNode.expanded ? 'folder-opened' : 'folder'
  }
  if (realNode.type === 'note') {
    return 'file-markdown'
  }
  if (realNode.type === 'article') {
    return 'article'
  }
  return 'file'
}

// 获取节点操作菜单
const getNodeOperations = (node: TreeNode): NodeOperation[] => {
  if (node.type === 'folder') {
    return [
      { content: '新建笔记', value: 'createNoteInFolder', icon: 'file-add' },
      { content: '新建文章', value: 'createArticleInFolder', icon: 'article-add' },
      { content: '重命名', value: 'rename', icon: 'edit' },
      { content: '删除', value: 'delete', icon: 'delete' }
    ]
  }
  if (node.type === 'note') {
    return [
      { content: '编辑', value: 'editNote', icon: 'edit' },
      { content: '重命名', value: 'renameNote', icon: 'edit' },
      { content: '删除', value: 'deleteNote', icon: 'delete' }
    ]
  }
  if (node.type === 'article') {
    return [
      { content: '编辑', value: 'editArticle', icon: 'edit' },
      { content: '重命名', value: 'renameArticle', icon: 'edit' },
      { content: '删除', value: 'deleteArticle', icon: 'delete' }
    ]
  }
  return []
}

// 处理节点操作
const handleNodeOperation = async (data: NodeOperation, node: TreeNode) => {
  selectedNode.value = node

  switch (data.value) {
    case 'rename':
    case 'renameNote':
    case 'renameArticle':
      renameForm.name = node.label
      showRenameDialog.value = true
      break
    case 'delete':
      await handleDeleteFolder(node)
      break
    case 'view':
      if (node.data) {
        emit('view-note', node.data)
      }
      break
    case 'editNote':
      const noteId = getActualNodeId(node)
      router.push({ name: 'NoteEdit', params: { id: noteId } })
      break
    case 'deleteNote':
      await handleDeleteNote(node)
      break
    case 'viewArticle':
      if (node.data) {
        emit('view-article', node.data)
      }
      break
    case 'editArticle':
      const articleId = getActualNodeId(node)
      router.push({ name: 'ArticleEdit', params: { id: articleId } })
      break
    case 'deleteArticle':
      await handleDeleteArticle(node)
      break
    case 'createNoteInFolder':
      if (node.id === 'notes-root' || node.id === 'articles-root') {
        router.push({ name: 'NoteNew' })
      } else {
        router.push({ name: 'NoteNew', query: { category_id: node.id } })
      }
      break
    case 'createArticleInFolder':
      if (node.id === 'notes-root' || node.id === 'articles-root') {
        router.push({ name: 'ArticleNew' })
      } else {
        router.push({ name: 'ArticleNew', query: { category_id: node.id } })
      }
      break
  }
}

const handleTreeExpand = (expanded: string[]) => {
  expandedNodes.value = expanded
}

const handleCreateAction = (data: { value: string }) => {
  if (data.value === 'folder') {
    newFolderForm.type = 'note'
    showFolderDialog.value = true
  } else if (data.value === 'note') {
    router.push({ name: 'NoteNew' })
  } else if (data.value === 'article') {
    router.push({ name: 'ArticleNew' })
  }
}

const handleFolderAction = (data: { value: string }) => {
  newFolderForm.type = data.value as 'note' | 'article'
  showFolderDialog.value = true
}

const handleCreateFolder = async () => {
  if (!newFolderForm.name) {
    MessagePlugin.warning('请输入文件夹名称')
    return
  }

  try {
    await fileTreeApi.createFolder(newFolderForm)
    MessagePlugin.success('文件夹创建成功')
    showFolderDialog.value = false
    newFolderForm.name = ''
    newFolderForm.parent_id = undefined
    fetchFileTree()
  } catch (error) {
    MessagePlugin.error('创建失败')
  }
}

// 解析真实的节点 ID（去除前缀）
const getActualNodeId = (node: TreeNode) => {
  if (node.type === 'folder') {
    return node.id
  } else if (node.type === 'note') {
    return node.id.startsWith('note-') ? node.id.slice(5) : node.id
  } else if (node.type === 'article') {
    return node.id.startsWith('article-') ? node.id.slice(8) : node.id
  }
  return node.id
}

const handleRenameSubmit = async () => {
  if (!renameForm.name || !selectedNode.value) {
    MessagePlugin.warning('请输入名称')
    return
  }

  try {
    const actualId = getActualNodeId(selectedNode.value)
    if (selectedNode.value.type === 'folder') {
      await fileTreeApi.updateCategory(actualId, { name: renameForm.name })
      MessagePlugin.success('文件夹重命名成功')
    } else if (selectedNode.value.type === 'note') {
      await fileTreeApi.updateNote(actualId, { title: renameForm.name })
      MessagePlugin.success('笔记重命名成功')
    } else if (selectedNode.value.type === 'article') {
      await fileTreeApi.updateArticle(actualId, { title: renameForm.name })
      MessagePlugin.success('文章重命名成功')
    }
    showRenameDialog.value = false
    fetchFileTree()
  } catch (error) {
    MessagePlugin.error('重命名失败')
  }
}

const handleDeleteFolder = async (node?: TreeNode) => {
  const targetNode = node || selectedNode.value
  if (!targetNode) return

  if (targetNode.id === 'notes-root' || targetNode.id === 'articles-root') {
    MessagePlugin.warning('根文件夹无法删除')
    return
  }

  try {
    const actualId = getActualNodeId(targetNode)
    await fileTreeApi.deleteFolder(actualId)
    MessagePlugin.success('文件夹删除成功')
    fetchFileTree()
  } catch (error) {
    MessagePlugin.error('删除失败')
  }
}

const handleDeleteNote = async (node?: TreeNode) => {
  const targetNode = node || selectedNode.value
  if (!targetNode?.id) return

  try {
    const actualId = getActualNodeId(targetNode)
    await fileTreeApi.deleteNote(actualId)
    MessagePlugin.success('笔记删除成功')
    fetchFileTree()
  } catch (error) {
    MessagePlugin.error('删除失败')
  }
}

const handleDeleteArticle = async (node?: TreeNode) => {
  const targetNode = node || selectedNode.value
  if (!targetNode?.id) return

  try {
    const actualId = getActualNodeId(targetNode)
    await fileTreeApi.deleteArticle(actualId)
    MessagePlugin.success('文章删除成功')
    fetchFileTree()
  } catch (error) {
    MessagePlugin.error('删除失败')
  }
}

// 搜索过滤
const handleFilter = () => {
  if (filterText.value) {
    filterByText.value = (node: any) => {
      const label = node?.label || ''
      return label.toLowerCase().indexOf(filterText.value.toLowerCase()) >= 0
    }
  } else {
    filterByText.value = null
  }
}

// 拖拽相关处理
const handleDragStart = (ctx: any) => {
  console.log('handleDragStart:', ctx)
}

const handleDragEnd = (ctx: any) => {
  console.log('handleDragEnd:', ctx)
}

const handleDragOver = (ctx: any) => {
  console.log('handleDragOver:', ctx)
}

const handleDragLeave = (ctx: any) => {
  console.log('handleDragLeave:', ctx)
}

const handleDrop = async (ctx: any) => {
  console.log('handleDrop - ctx 类型:', Object.keys(ctx))

  try {
    const { dragNode, dropNode, dropPosition } = ctx
    const sourceNode = dragNode?.data || dragNode
    const targetNode = dropNode?.data || dropNode

    console.log('handleDrop - sourceNode:', sourceNode)
    console.log('handleDrop - targetNode:', targetNode)
    console.log('handleDrop - dropPosition:', dropPosition)

    if (!sourceNode || sourceNode.type === 'root') {
      MessagePlugin.warning('无法移动根节点')
      return
    }

    let targetParentId: string | undefined
    let nodeType: 'category' | 'note' | 'article'
    let actualNodeId: string

    // 确定节点类型和真实的 ID（去除前缀）
    if (sourceNode.type === 'folder') {
      nodeType = 'category'
      actualNodeId = sourceNode.id
    } else if (sourceNode.type === 'note') {
      nodeType = 'note'
      actualNodeId = getActualNodeId(sourceNode)
    } else if (sourceNode.type === 'article') {
      nodeType = 'article'
      actualNodeId = getActualNodeId(sourceNode)
    } else {
      MessagePlugin.warning('不支持的节点类型')
      return
    }

    console.log('handleDrop - 解析结果:', { actualNodeId, nodeType, sourceNodeType: sourceNode.type, sourceNodeId: sourceNode.id })

    // 确定目标父节点
    // TDesign dropPosition: 0=作为子节点, 1=上方, -1=下方
    if (dropPosition === 0) {
      // 拖入目标节点内部
      if (targetNode.type === 'folder') {
        if (targetNode.id === 'notes-root' || targetNode.id === 'articles-root') {
          targetParentId = undefined
        } else {
          targetParentId = targetNode.id
        }
      } else if (targetNode.type === 'note' || targetNode.type === 'article') {
        MessagePlugin.warning('只能拖入文件夹')
        return
      } else {
        targetParentId = undefined
      }
    } else {
      // 拖到目标节点的上方(1)或下方(-1)，找到目标节点的父节点
      const targetParentNode = dropNode?.parent
      if (!targetParentNode) {
        targetParentId = undefined
      } else if (targetParentNode.data?.id === 'notes-root' || targetParentNode.data?.id === 'articles-root') {
        targetParentId = undefined
      } else if (targetParentNode.data?.type === 'folder') {
        targetParentId = targetParentNode.data.id
      } else {
        targetParentId = undefined
      }
    }

    // 防止循环引用：不能将文件夹拖到自己的子文件夹中
    if (sourceNode.type === 'folder' && targetParentId) {
      let currentNode = dropNode
      while (currentNode) {
        if (currentNode.data?.id === sourceNode.id) {
          MessagePlugin.warning('不能将文件夹移动到自己的子文件夹中')
          return
        }
        currentNode = currentNode?.parent
      }
    }

    console.log('移动节点 - 发送请求:', { node_id: actualNodeId, node_type: nodeType, target_parent_id: targetParentId })

    // 调用移动接口
    await fileTreeApi.moveNode({
      node_id: actualNodeId,
      node_type: nodeType,
      target_parent_id: targetParentId
    })

    MessagePlugin.success('移动成功')
    fetchFileTree()
  } catch (error) {
    console.error('移动失败 - 错误详情:', error)
    MessagePlugin.error('移动失败')
  }
}

// 加载更多子节点（可选，用于懒加载）
const loadMore = (node: TreeNode) => {
  return Promise.resolve()
}

// 暴露方法给父组件
const emit = defineEmits(['view-note', 'view-article'])

defineExpose({
  refresh: fetchFileTree
})
</script>

<style scoped>
.file-tree-card {
  width: 100%;
  height: 100%;
}

.custom-header {
  margin-bottom: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  flex: 1;
  min-width: 0;
}

.file-tree-content {
  height: calc(100% - 80px);
  min-height: 400px;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.file-tree-content::-webkit-scrollbar {
  display: none;
}

:deep(.t-tree) {
  height: 100%;
}

:deep(.t-tree__list) {
  height: 100%;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

:deep(.t-tree__list::-webkit-scrollbar) {
  display: none;
}

/* 数据为空时水平居中显示 */
:deep(.t-tree__empty) {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
}

.tree-node-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 8px;
}

.node-action-btn {
  opacity: 0;
  transition: opacity 0.2s;
  padding: 2px 6px;
}

.tree-node-label:hover .node-action-btn {
  opacity: 1;
}

/* 自定义下拉菜单样式 */
.custom-dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  min-width: 120px;
  background: white !important;
  border: 2px solid red !important;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 999999;
  margin-top: 4px;
  display: block;
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  gap: 8px;
  font-size: 14px;
  color: #333;
  transition: background-color 0.2s;
}

.dropdown-item:hover {
  background-color: #f3f3f3;
}

.item-icon {
  font-size: 16px;
  color: #666;
}

/* 全局下拉菜单样式 */
.global-dropdown-menu {
  min-width: 140px;
  background: white;
  border: 1px solid #e7e7e7;
  border-radius: 6px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.18);
}
</style>
