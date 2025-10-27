// 全局JavaScript功能

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    setupEventListeners();
});

// 页面初始化
function initializePage() {
    // 初始化工具提示
    initTooltips();
    
    // 初始化表单验证
    initFormValidation();
    
    // 初始化表格排序
    initTableSorting();
    
    // 显示当前时间
    updateCurrentTime();
}

// 设置事件监听器
function setupEventListeners() {
    // 表单提交确认
    setupFormConfirmations();
    
    // 搜索功能
    setupSearchFunctionality();
    
    // 模态框事件
    setupModalEvents();
}

// 初始化Bootstrap工具提示
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 初始化表单验证
function initFormValidation() {
    // 为所有表单添加验证
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(this)) {
                event.preventDefault();
                event.stopPropagation();
            }
        }, false);
    });
}

// 表单验证函数
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            markFieldInvalid(field, '此字段为必填项');
            isValid = false;
        } else {
            markFieldValid(field);
        }
    });
    
    // 验证数字字段
    const numberFields = form.querySelectorAll('input[type="number"]');
    numberFields.forEach(field => {
        if (field.value) {
            const value = parseFloat(field.value);
            const min = parseFloat(field.min) || 0;
            const max = parseFloat(field.max) || 100;
            
            if (value < min || value > max) {
                markFieldInvalid(field, `数值必须在 ${min} 到 ${max} 之间`);
                isValid = false;
            } else {
                markFieldValid(field);
            }
        }
    });
    
    return isValid;
}

// 标记字段为无效
function markFieldInvalid(field, message) {
    field.classList.add('is-invalid');
    field.classList.remove('is-valid');
    
    // 移除现有的反馈信息
    const existingFeedback = field.parentNode.querySelector('.invalid-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    // 添加新的反馈信息
    const feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    feedback.textContent = message;
    field.parentNode.appendChild(feedback);
}

// 标记字段为有效
function markFieldValid(field) {
    field.classList.add('is-valid');
    field.classList.remove('is-invalid');
    
    // 移除无效反馈信息
    const existingFeedback = field.parentNode.querySelector('.invalid-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
}

// 初始化表格排序
function initTableSorting() {
    const sortableHeaders = document.querySelectorAll('th[data-sort]');
    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(this);
        });
    });
}

// 表格排序函数
function sortTable(header) {
    const table = header.closest('table');
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const isNumeric = header.dataset.type === 'number';
    const isAscending = header.dataset.sort === 'asc';
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        let comparison = 0;
        if (isNumeric) {
            comparison = parseFloat(aValue) - parseFloat(bValue);
        } else {
            comparison = aValue.localeCompare(bValue);
        }
        
        return isAscending ? comparison : -comparison;
    });
    
    // 移除现有行
    while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
    }
    
    // 添加排序后的行
    rows.forEach(row => tbody.appendChild(row));
    
    // 更新排序状态
    header.dataset.sort = isAscending ? 'desc' : 'asc';
    
    // 更新排序指示器
    updateSortIndicators(table, header);
}

// 更新排序指示器
function updateSortIndicators(table, activeHeader) {
    const headers = table.querySelectorAll('th[data-sort]');
    headers.forEach(header => {
        header.classList.remove('sort-asc', 'sort-desc');
        if (header === activeHeader) {
            header.classList.add(activeHeader.dataset.sort === 'asc' ? 'sort-asc' : 'sort-desc');
        }
    });
}

// 设置表单提交确认
function setupFormConfirmations() {
    const deleteButtons = document.querySelectorAll('form[data-confirm]');
    deleteButtons.forEach(form => {
        form.addEventListener('submit', function(event) {
            const message = this.getAttribute('data-confirm') || '确定要执行此操作吗？';
            if (!confirm(message)) {
                event.preventDefault();
                event.stopPropagation();
            }
        });
    });
}

// 设置搜索功能
function setupSearchFunctionality() {
    const searchInputs = document.querySelectorAll('.table-search');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const table = this.closest('.table-responsive').querySelector('table');
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    });
}

// 设置模态框事件
function setupModalEvents() {
    // 模态框显示时重置表单
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', function() {
            const form = this.querySelector('form');
            if (form) {
                resetFormValidation(form);
            }
        });
    });
    
    // 模态框隐藏时清理
    modals.forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            const form = this.querySelector('form');
            if (form) {
                form.reset();
                resetFormValidation(form);
            }
        });
    });
}

// 重置表单验证状态
function resetFormValidation(form) {
    const fields = form.querySelectorAll('.is-invalid, .is-valid');
    fields.forEach(field => {
        field.classList.remove('is-invalid', 'is-valid');
    });
    
    const feedbacks = form.querySelectorAll('.invalid-feedback');
    feedbacks.forEach(feedback => feedback.remove());
}

// 更新当前时间显示
function updateCurrentTime() {
    const timeElements = document.querySelectorAll('.current-time');
    if (timeElements.length > 0) {
        const now = new Date();
        const timeString = now.toLocaleString('zh-CN');
        timeElements.forEach(element => {
            element.textContent = timeString;
        });
    }
}

// 显示加载状态
function showLoading(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="loading-spinner me-2"></span>处理中...';
    button.disabled = true;
    return originalText;
}

// 隐藏加载状态
function hideLoading(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
}

// 显示消息
function showMessage(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 自动隐藏
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// 导出数据为CSV
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            // 清理数据并转义引号
            let data = cols[j].textContent.replace(/(\r\n|\n|\r)/gm, '').replace(/(\s\s)/gm, ' ');
            data = data.replace(/"/g, '""');
            row.push('"' + data + '"');
        }
        
        csv.push(row.join(','));
    }
    
    // 下载CSV文件
    const csvString = csv.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// 添加搜索框到表格
function addTableSearch(tableId, placeholder = '搜索...') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tableContainer = table.closest('.table-responsive') || table.parentNode;
    const searchDiv = document.createElement('div');
    searchDiv.className = 'mb-3';
    searchDiv.innerHTML = `
        <div class="input-group">
            <input type="text" class="form-control table-search" placeholder="${placeholder}">
            <button class="btn btn-outline-secondary" type="button" onclick="clearSearch(this)">
                <i class="bi bi-x-circle"></i> 清除
            </button>
        </div>
    `;
    
    tableContainer.insertBefore(searchDiv, table);
}

// 清除搜索
function clearSearch(button) {
    const input = button.parentNode.querySelector('.table-search');
    input.value = '';
    input.dispatchEvent(new Event('input'));
}

// 键盘快捷键
document.addEventListener('keydown', function(event) {
    // Ctrl + F 聚焦搜索框
    if (event.ctrlKey && event.key === 'f') {
        event.preventDefault();
        const searchInput = document.querySelector('.table-search');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape 键关闭模态框
    if (event.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modal = bootstrap.Modal.getInstance(openModal);
            if (modal) {
                modal.hide();
            }
        }
    }
});