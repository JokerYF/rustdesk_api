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
        return APP.modal || {};
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

        // 收集所有标签
        const tagsMap = {};
        if (detail.devices && detail.devices.length > 0) {
            detail.devices.forEach(d => {
                const tags = Array.isArray(d.tags) ? d.tags : (d.tags ? d.tags.split(',').map(t => t.trim()) : []);
                tags.forEach(tag => {
                    if (tag) {
                        if (!tagsMap[tag]) {
                            tagsMap[tag] = [];
                        }
                        tagsMap[tag].push(d.peer_id);
                    }
                });
            });
        }

        // 左侧：标签信息
        let tagsHtml = '<div class="nav4-tags-section">' +
            '<h4 style="margin:0 0 12px 0;font-size:14px;font-weight:600;color:#0b3d60;">标签列表</h4>';

        const tagsList = Object.keys(tagsMap);
        if (tagsList.length > 0) {
            tagsHtml += '<div class="nav4-tags-list">';
            tagsList.forEach(tag => {
                const count = tagsMap[tag].length;
                tagsHtml += '<div class="nav4-tag-item" data-tag="' + tag + '">' +
                    '<span class="nav4-tag-name">' + tag + '</span>' +
                    '<span class="nav4-tag-count">(' + count + ')</span>' +
                    '</div>';
            });
            tagsHtml += '</div>';
        } else {
            tagsHtml += '<div style="color:#8a939e;font-size:14px;">暂无标签</div>';
        }
        tagsHtml += '</div>';

        // 右侧：设备信息
        let devicesHtml = '<div class="nav4-devices-section">' +
            '<h4 style="margin:0 0 12px 0;font-size:14px;font-weight:600;color:#0b3d60;">设备列表</h4>';

        if (detail.devices && detail.devices.length > 0) {
            devicesHtml += '<div class="x-scroll-container"><table class="nav2-table"><thead><tr>' +
                '<th style="width:150px;">设备ID</th>' +
                '<th style="width:120px;">别名</th>' +
                '<th style="width:150px;">标签</th>' +
                '<th style="width:120px;">设备名</th>' +
                '<th style="width:80px;">系统</th>' +
                '<th style="width:80px;">状态</th>' +
                '<th style="width:100px;">操作</th>' +
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
            devicesHtml += '</tbody></table></div>';
        } else {
            devicesHtml += '<div style="color:#8a939e;font-size:14px;">暂无设备</div>';
        }
        devicesHtml += '</div>';

        // 组合成左右布局
        const typeText = detail.personal_type === 'public' ? '公开' : '私有';
        const displayName = detail.display_name || detail.personal_name || '-';
        return (
            '<div style="margin-bottom:16px;">' +
            '<dl style="margin:0;display:flex;flex-wrap:wrap;gap:16px;">' +
            '<div style="display:flex;gap:8px;"><dt style="min-width:88px;color:#6a737d;">地址簿名称</dt><dd style="margin:0;">' + displayName + '</dd></div>' +
            '<div style="display:flex;gap:8px;"><dt style="min-width:88px;color:#6a737d;">类型</dt><dd style="margin:0;">' + typeText + '</dd></div>' +
            '<div style="display:flex;gap:8px;"><dt style="min-width:88px;color:#6a737d;">设备数量</dt><dd style="margin:0;">' + (detail.device_count || 0) + '</dd></div>' +
            '<div style="display:flex;gap:8px;"><dt style="min-width:88px;color:#6a737d;">创建时间</dt><dd style="margin:0;">' + (detail.created_at || '-') + '</dd></div>' +
            '</dl>' +
            '</div>' +
            '<div class="nav4-detail-layout">' +
            tagsHtml +
            devicesHtml +
            '</div>'
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

    // 导出到全局
    APP.nav4 = {
        collectQueryOptions,
        renderDetailHTML,
        fetchAndShowDetail,
        startInlineEdit,
        showAddDeviceModal
    };

    window.APP = APP;

})(window);
