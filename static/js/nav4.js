/**
 * 地址簿管理页面模块 (nav-4)
 *
 * 处理地址簿列表、详情、重命名、删除、设备管理等功能
 */

(function (window) {
    'use strict';

    const APP = window.APP || {};

    // 延迟获取依赖，避免模块加载顺序问题
    function getUtils() {
        return APP.utils || {};
    }

    function getModal() {
        return APP.modal || {
            open: function () {
            },
            close: function () {
            }
        };
    }

    function getConstants() {
        return {
            STORAGE_KEY: APP.STORAGE_KEY || 'homeActiveNavKey',
            URLS: APP.URLS || {},
            ICONS: APP.ICONS || {}
        };
    }

    /**
     * 收集查询参数
     *
     * :param {HTMLFormElement} formEl: 表单元素
     * :returns: 查询参数对象
     * :rtype: Object
     */
    function collectQueryOptions(formEl) {
        const params = {};
        if (!formEl) return params;
        const formData = new FormData(formEl);
        ['q', 'type', 'page_size'].forEach((k) => {
            const v = formData.get(k);
            if (v !== null && String(v).trim() !== '') {
                params[k] = String(v).trim();
            }
        });
        return params;
    }

    /**
     * 渲染地址簿详情HTML
     *
     * :param {Object} detail: 地址簿详情对象
     * :returns: HTML字符串
     * :rtype: string
     */
    function renderDetailHTML(detail) {
        const {ICONS} = getConstants();
        let devicesHtml = '';
        if (detail.devices && detail.devices.length > 0) {
            devicesHtml = '<table class="nav2-table" style="margin-top:16px;"><thead><tr>' +
                '<th>设备ID</th><th>别名</th><th>标签</th><th>设备名</th><th>系统</th><th>状态</th><th>操作</th>' +
                '</tr></thead><tbody>';
            detail.devices.forEach(d => {
                const statusClass = d.is_online ? 'online' : 'offline';
                const statusText = d.is_online ? '在线' : '离线';
                const tags = Array.isArray(d.tags) ? d.tags.join(', ') : (d.tags || '');
                devicesHtml += '<tr data-guid="' + detail.guid + '" data-peer-id="' + d.peer_id + '">' +
                    '<td>' + (d.peer_id || '-') + '</td>' +
                    '<td class="nav4-editable-cell" data-field="alias" data-guid="' + detail.guid + '" data-peer-id="' + d.peer_id + '" data-original="' + (d.alias || '') + '">' +
                    '<span class="nav2-detail-text">' + (d.alias || '-') + '</span> ' +
                    '<button type="button" class="nav2-link nav4-edit-btn" data-field="alias" data-guid="' + detail.guid + '" data-peer-id="' + d.peer_id + '" aria-label="编辑别名">' +
                    '<img src="' + ICONS.EDIT + '" width="16" height="16" alt="" aria-hidden="true">' +
                    '</button>' +
                    '</td>' +
                    '<td class="nav4-editable-cell" data-field="tags" data-guid="' + detail.guid + '" data-peer-id="' + d.peer_id + '" data-original="' + (tags || '') + '">' +
                    '<span class="nav2-detail-text">' + (tags || '-') + '</span> ' +
                    '<button type="button" class="nav2-link nav4-edit-btn" data-field="tags" data-guid="' + detail.guid + '" data-peer-id="' + d.peer_id + '" aria-label="编辑标签">' +
                    '<img src="' + ICONS.EDIT + '" width="16" height="16" alt="" aria-hidden="true">' +
                    '</button>' +
                    '</td>' +
                    '<td>' + (d.device_name || '-') + '</td>' +
                    '<td>' + (d.os || '-') + '</td>' +
                    '<td><span class="nav2-status ' + statusClass + '">' + statusText + '</span></td>' +
                    '<td><button type="button" class="nav2-link nav4-remove-device-btn" data-guid="' + detail.guid + '" data-peer-id="' + d.peer_id + '">移除</button></td>' +
                    '</tr>';
            });
            devicesHtml += '</tbody></table>';
        } else {
            devicesHtml = '<div style="color:#6a737d;margin-top:16px;">暂无设备</div>';
        }

        const typeText = detail.personal_type === 'public' ? '公开' : '私有';
        const displayName = detail.display_name || detail.personal_name || '-';
        return (
            '<dl style="margin:0;">' +
            '<div style="display:flex;gap:8px;margin:6px 0;"><dt style="min-width:88px;color:#6a737d;">地址簿名称</dt><dd style="margin:0;">' + displayName + '</dd></div>' +
            '<div style="display:flex;gap:8px;margin:6px 0;"><dt style="min-width:88px;color:#6a737d;">类型</dt><dd style="margin:0;">' + typeText + '</dd></div>' +
            '<div style="display:flex;gap:8px;margin:6px 0;"><dt style="min-width:88px;color:#6a737d;">设备数量</dt><dd style="margin:0;">' + (detail.device_count || 0) + '</dd></div>' +
            '<div style="display:flex;gap:8px;margin:6px 0;"><dt style="min-width:88px;color:#6a737d;">创建时间</dt><dd style="margin:0;">' + (detail.created_at || '-') + '</dd></div>' +
            '</dl>' +
            devicesHtml
        );
    }

    /**
     * 获取并展示地址簿详情
     *
     * :param {string} guid: 地址簿GUID
     * :returns: 无
     * :rtype: void
     */
    function fetchAndShowDetail(guid) {
        const {URLS} = getConstants();
        const {open: openModal} = getModal();
        const bodyEl = document.getElementById('nav4-detail-body');
        if (bodyEl) bodyEl.innerHTML = '<div style="color:#6a737d;">加载中...</div>';
        openModal('nav4-detail-root');
        const params = new URLSearchParams({guid: guid});
        fetch(`${URLS.PERSONAL_DETAIL}?${params.toString()}`, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        }).then(resp => {
            if (!resp.ok) throw new Error('请求失败');
            return resp.json();
        }).then(data => {
            if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '加载失败');
            const html = renderDetailHTML(data.data || {});
            if (bodyEl) bodyEl.innerHTML = html;
        }).catch(err => {
            if (bodyEl) bodyEl.innerHTML = '<div style="color:#b91c1c;">' + (err.message || '加载失败') + '</div>';
        });
    }

    /**
     * 开始内联编辑（地址簿设备）
     *
     * :param {HTMLElement} cell: 单元格元素
     * :param {string} field: 字段名
     * :param {string} guid: 地址簿GUID
     * :param {string} peerId: 设备ID
     * :returns: 无
     * :rtype: void
     */
    function startInlineEdit(cell, field, guid, peerId) {
        const {showToast, parseFetchError, getCookie} = getUtils();
        const {ICONS, URLS} = getConstants();
        const textEl = cell.querySelector('.nav2-detail-text');
        const editBtn = cell.querySelector('.nav4-edit-btn');
        if (!textEl || !editBtn) return;

        const original = cell.getAttribute('data-original') || '';
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'nav2-input';
        input.value = original;
        input.style.width = '200px';
        input.setAttribute('data-field', field);

        const confirmBtn = document.createElement('button');
        confirmBtn.type = 'button';
        confirmBtn.className = 'nav2-link';
        confirmBtn.setAttribute('aria-label', '确认');
        confirmBtn.innerHTML = '<img src="' + ICONS.CONFIRM + '" width="16" height="16" alt="" aria-hidden="true">';

        const cancelBtn = document.createElement('button');
        cancelBtn.type = 'button';
        cancelBtn.className = 'nav2-link';
        cancelBtn.setAttribute('aria-label', '取消');
        cancelBtn.innerHTML = '<img src="' + ICONS.CANCEL + '" width="16" height="16" alt="" aria-hidden="true">';

        const save = () => {
            const val = input.value.trim();
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('guid', guid);
            body.set('peer_id', peerId);
            body.set(field, val);

            let url = '';
            if (field === 'alias') {
                url = URLS.PERSONAL_UPDATE_ALIAS;
            } else if (field === 'tags') {
                url = URLS.PERSONAL_UPDATE_TAGS;
            } else {
                showToast('未知字段', 'error');
                return;
            }

            fetch(url, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'X-CSRFToken': csrf
                },
                body: body.toString()
            }).then(resp => {
                if (!resp.ok) return parseFetchError(resp);
                return resp.json();
            }).then(data => {
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '保存失败');
                cell.setAttribute('data-original', val);
                textEl.textContent = val || '-';
                cell.innerHTML = '';
                cell.appendChild(textEl);
                cell.appendChild(document.createTextNode(' '));
                cell.appendChild(editBtn);
                showToast('保存成功', 'success');
            }).catch(err => {
                showToast(err.message || '保存失败', 'error');
            });
        };

        const cancel = () => {
            cell.innerHTML = '';
            cell.appendChild(textEl);
            cell.appendChild(document.createTextNode(' '));
            cell.appendChild(editBtn);
        };

        confirmBtn.addEventListener('click', save, false);
        cancelBtn.addEventListener('click', cancel, false);
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                save();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancel();
            }
        }, false);

        cell.innerHTML = '';
        cell.appendChild(input);
        cell.appendChild(document.createTextNode(' '));
        cell.appendChild(confirmBtn);
        cell.appendChild(cancelBtn);
        input.focus();
        input.select();
    }

    /**
     * 显示添加设备到地址簿弹框
     *
     * :param {string} peerId: 设备ID
     * :returns: 无
     * :rtype: void
     */
    function showAddDeviceModal(peerId) {
        const {showToast, parseFetchError} = getUtils();
        const {open: openModal} = getModal();
        const {URLS} = getConstants();
        fetch(URLS.PERSONAL_LIST, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(resp => {
            if (!resp.ok) return parseFetchError(resp);
            return resp.json();
        }).then(data => {
            if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '获取地址簿列表失败');
            const personals = data.data || [];

            if (personals.length === 0) {
                showToast('暂无可用地址簿，请先创建地址簿', 'info');
                return;
            }

            const select = document.getElementById('nav2-add-to-book-guid');
            select.innerHTML = '<option value="" disabled selected hidden>请选择地址簿</option>';
            personals.forEach(p => {
                const option = document.createElement('option');
                option.value = p.guid;
                option.textContent = p.display_name;
                select.appendChild(option);
            });

            document.getElementById('nav2-add-to-book-peer-id').value = peerId;
            document.getElementById('nav2-add-to-book-peer-id-display').textContent = peerId;
            document.getElementById('nav2-add-to-book-alias').value = '';

            openModal('nav2-add-to-book-root');
        }).catch(err => {
            showToast(err.message || '获取地址簿列表失败，请稍后重试', 'error');
        });
    }

    /**
     * 随机生成一个默认颜色
     *
     * :returns: 随机生成的十六进制颜色值
     * :rtype: string
     */
    function getRandomColor() {
        const colors = [
            '#2da44e', '#0366d6', '#d73a49', '#6f42c1', '#e36209',
            '#107c10', '#005a9e', '#da3633', '#8957e5', '#d83b01',
            '#238636', '#0550ae', '#d13438', '#7952b3', '#e66a00'
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    /**
     * 初始化添加标签功能
     *
     * :returns: 无
     * :rtype: void
     */
    function initAddTag() {
        const {open: openModal, close: closeModal} = getModal();
        const {showToast, parseFetchError, getCookie} = getUtils();
        const {URLS} = getConstants();

        // 处理添加标签按钮点击事件
        document.addEventListener('click', function (e) {
            // 添加标签按钮点击事件
            if (e.target.closest('.nav4-add-tag-btn')) {
                // 设置随机默认颜色
                const colorInput = document.getElementById('nav4-add-tag-color');
                if (colorInput) {
                    colorInput.value = getRandomColor();
                }
                // 清空表单
                const nameInput = document.getElementById('nav4-add-tag-name');
                if (nameInput) {
                    nameInput.value = '';
                }
                // 打开模态框
                openModal('nav4-add-tag-root');
            }
        });

        // 处理添加标签表单提交事件
        document.addEventListener('submit', function (e) {
            if (e.target.id === 'nav4-add-tag-form') {
                e.preventDefault();
                const form = e.target;
                const formData = new FormData(form);
                const tag = formData.get('tag')?.trim();
                const color = formData.get('color')?.trim();
                const guid = formData.get('guid')?.trim();

                // 验证表单
                if (!tag) {
                    showToast('标签名称不能为空', 'error');
                    return;
                }
                if (!color) {
                    showToast('标签颜色不能为空', 'error');
                    return;
                }
                if (!guid) {
                    showToast('地址簿GUID不能为空', 'error');
                    return;
                }

                // 提交表单
                const csrf = getCookie('csrftoken');
                const body = new URLSearchParams();
                body.set('tag', tag);
                body.set('color', color);
                body.set('guid', guid);

                fetch('/personal/add-tag', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                        'X-CSRFToken': csrf
                    },
                    body: body.toString()
                }).then(resp => {
                    if (!resp.ok) return parseFetchError(resp);
                    return resp.json();
                }).then(data => {
                    if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '添加标签失败');
                    showToast('标签添加成功', 'success');
                    closeModal('nav4-add-tag-root');
                    // 刷新页面或重新加载内容
                    window.location.reload();
                }).catch(err => {
                    showToast(err.message || '添加标签失败，请稍后重试', 'error');
                });
            }
        });
    }

    /**
     * 初始化编辑标签功能
     *
     * :returns: 无
     * :rtype: void
     */
    function initEditTag() {
        const {open: openModal, close: closeModal} = getModal();
        const {showToast, parseFetchError, getCookie} = getUtils();
        const {URLS} = getConstants();

        // 处理编辑标签按钮点击事件
        document.addEventListener('click', function (e) {
            // 编辑标签按钮点击事件
            if (e.target.closest('.nav4-edit-tag-btn')) {
                const btn = e.target.closest('.nav4-edit-tag-btn');
                const tagItem = btn.closest('.nav4-tag-item');
                if (tagItem) {
                    const tagId = tagItem.getAttribute('data-tag-id');
                    const tagName = tagItem.getAttribute('data-tag-name');
                    // 设置表单值
                    const idInput = document.getElementById('nav4-edit-tag-id');
                    const nameInput = document.getElementById('nav4-edit-tag-name');
                    if (idInput) idInput.value = tagId || '';
                    if (nameInput) nameInput.value = tagName || '';
                    // 打开模态框
                    openModal('nav4-edit-tag-root');
                }
            }
        });
    }

    /**
     * 初始化所有地址簿功能
     *
     * :returns: 无
     * :rtype: void
     */
    function initNav4() {
        initAddTag();
        initEditTag();
    }

    // 导出到全局
    APP.nav4 = {
        collectQueryOptions,
        renderDetailHTML,
        fetchAndShowDetail,
        startInlineEdit,
        showAddDeviceModal,
        initNav4
    };

    // 监听内容加载完成事件，初始化地址簿功能
    document.addEventListener('contentLoaded', function (e) {
        if (e.detail && e.detail.key === 'nav-4') {
            initNav4();
        }
    });

    window.APP = APP;

})(window);
