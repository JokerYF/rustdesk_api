/**
 * 设备管理页面模块 (nav-2)
 *
 * 处理设备列表、详情、编辑、状态刷新等功能
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

    function getNavigation() {
        return APP.navigation || {};
    }

    function getConstants() {
        return {
            STORAGE_KEY: APP.STORAGE_KEY || 'homeActiveNavKey',
            URLS: APP.URLS || {},
            ICONS: APP.ICONS || {}
        };
    }

    // nav-2 自动刷新控制变量
    let TIMER_ID = null;
    let RUNNING = false;
    let INFLIGHT_CONTROLLER = null;
    let FAILURES = 0;
    const BASE_INTERVAL = 10000;   // 10s
    const MAX_INTERVAL = 60000;    // 60s

    /**
     * 收集nav-2当前页设备ID列表
     *
     * :returns: 设备ID数组
     * :rtype: Array<string>
     */
    function collectPeerIdsFromDOM() {
        const rows = document.querySelectorAll('.nav2-table tbody tr[data-peer-id]');
        const ids = [];
        rows.forEach(tr => {
            const pid = tr.getAttribute('data-peer-id') || '';
            if (pid) ids.push(pid);
        });
        return ids;
    }

    /**
     * 将状态应用到DOM
     *
     * :param {Object} statusMap: 状态映射
     * :returns: 无
     * :rtype: void
     */
    function applyStatuses(statusMap) {
        if (!statusMap) return;
        Object.keys(statusMap).forEach(pid => {
            const el = document.querySelector(`.nav2-status[data-status-for="${pid}"]`);
            if (!el) return;
            const isOnline = !!(statusMap[pid] && statusMap[pid].is_online);
            el.classList.toggle('online', isOnline);
            el.classList.toggle('offline', !isOnline);
            el.textContent = isOnline ? '在线' : '离线';
        });
    }

    /**
     * 拉取并刷新状态
     *
     * :returns: Promise
     * :rtype: Promise
     */
    function refreshStatusesOnce() {
        const {URLS} = getConstants();
        const ids = collectPeerIdsFromDOM();
        if (!ids.length) return Promise.resolve();
        try {
            if (INFLIGHT_CONTROLLER) INFLIGHT_CONTROLLER.abort();
        } catch (e) {
            console.warn('refreshStatusesOnce: abort失败', e);
        }
        INFLIGHT_CONTROLLER = new AbortController();
        return fetch(URLS.DEVICE_STATUSES, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-Session-No-Renew': '1',
                'X-CSRFToken': APP.utils.getCookie('csrftoken')
            },
            body: JSON.stringify({ids: ids.join(',')}),
            signal: INFLIGHT_CONTROLLER.signal
        }).then(resp => {
            if (!resp.ok) throw new Error('请求失败');
            return resp.json();
        }).then(data => {
            if (!data || data.ok !== true) return;
            applyStatuses(data.data || {});
        }).catch(() => {
            // 静默失败
        }).finally(() => {
            INFLIGHT_CONTROLLER = null;
        });
    }

    /**
     * 计算下一次轮询延迟（指数退避）
     *
     * :returns: 毫秒数
     * :rtype: number
     */
    function computeDelay() {
        const backoff = BASE_INTERVAL * Math.pow(2, Math.max(0, Math.min(6, FAILURES)));
        return Math.min(backoff, MAX_INTERVAL);
    }

    /**
     * 轮询主循环
     *
     * :returns: 无
     * :rtype: void
     */
    function tick() {
        if (!RUNNING) return;
        if (document.hidden) {
            TIMER_ID = null;
            return;
        }
        refreshStatusesOnce().then(() => {
            FAILURES = 0;
        }).catch(() => {
            FAILURES += 1;
        }).finally(() => {
            if (!RUNNING) return;
            const delay = computeDelay();
            TIMER_ID = setTimeout(tick, delay);
        });
    }

    /**
     * 启动/停止状态自动刷新
     *
     * :param {boolean} enable: 是否启用
     * :returns: 无
     * :rtype: void
     */
    function toggleAutoRefresh(enable) {
        RUNNING = !!enable;
        if (TIMER_ID) {
            clearTimeout(TIMER_ID);
            TIMER_ID = null;
        }
        try {
            if (INFLIGHT_CONTROLLER) INFLIGHT_CONTROLLER.abort();
        } catch (e) {
            console.warn('toggleAutoRefresh: abort失败', e);
        }
        INFLIGHT_CONTROLLER = null;
        FAILURES = 0;
        if (RUNNING) {
            tick();
        }
    }

    /**
     * 收集查询参数
     *
     * :param {HTMLFormElement} formEl: 表单元素
     * :returns: 查询参数对象
     * :rtype: Object
     */
    function collectQueryOptions(formEl) {
        const {collectFormParams} = getUtils();
        return collectFormParams(formEl, ['q', 'os', 'status', 'page_size']);
    }

    /**
     * 预填重命名表单
     *
     * :param {string} peerId: 设备ID
     * :param {string} currentAlias: 当前别名
     * :returns: 无
     * :rtype: void
     */
    function prefillRenameForm(peerId, currentAlias = '') {
        const peerInput = document.getElementById('nav2-rename-peer');
        const aliasInput = document.getElementById('nav2-rename-alias');
        if (peerInput) peerInput.value = peerId || '';
        if (aliasInput) {
            aliasInput.value = currentAlias || '';
            aliasInput.focus();
            aliasInput.select();
        }
    }

    /**
     * 渲染详情内容HTML
     *
     * :param {Object} detail: 设备详情对象
     * :returns: HTML字符串
     * :rtype: string
     */
    function renderDetailHTML(detail) {
        const {ICONS} = getConstants();
        const {escapeHTML} = getUtils();
        const tags = Array.isArray(detail.tags) ? detail.tags.join(', ') : (detail.tags || '');
        const esc = escapeHTML;
        return (
            '<dl style="margin:0;">' +
            '<div style="display:flex;gap:8px;margin:6px 0;align-items:center;"><dt style="min-width:88px;color:#6a737d;">设备ID</dt><dd style="margin:0;flex:1;">' + esc(detail.peer_id || '-') + '</dd></div>' +
            '<div style="display:flex;gap:8px;margin:6px 0;align-items:center;"><dt style="min-width:88px;color:#6a737d;">用户名</dt><dd style="margin:0;flex:1;">' + esc(detail.username || '-') + '</dd></div>' +
            '<div style="display:flex;gap:8px;margin:6px 0;align-items:center;"><dt style="min-width:88px;color:#6a737d;">主机名</dt><dd style="margin:0;flex:1;">' + esc(detail.hostname || '-') + '</dd></div>' +
            '<div style="display:flex;gap:8px;margin:6px 0;align-items:center;"><dt style="min-width:88px;color:#6a737d;">设备别名</dt>' +
            '<dd id="nav2-detail-alias" style="margin:0;flex:1;" data-original="' + esc(detail.alias || '') + '">' +
            '<span class="nav2-detail-text">' + esc(detail.alias || '-') + '</span> ' +
            '<button type="button" class="nav2-link nav2-edit-btn" data-field="alias" data-peer="' + esc(detail.peer_id || '') + '" aria-label="编辑别名">' +
            '<img src="' + ICONS.EDIT + '" width="16" height="16" alt="" aria-hidden="true">' +
            '</button>' +
            '</dd>' +
            '</div>' +
            '<div style="display:flex;gap:8px;margin:6px 0;align-items:center;"><dt style="min-width:88px;color:#6a737d;">设备标签</dt>' +
            '<dd id="nav2-detail-tags" style="margin:0;flex:1;" data-original="' + esc(tags || '') + '">' +
            '<span class="nav2-detail-text">' + esc(tags || '-') + '</span> ' +
            '<button type="button" class="nav2-link nav2-edit-btn" data-field="tags" data-peer="' + esc(detail.peer_id || '') + '" aria-label="编辑标签">' +
            '<img src="' + ICONS.EDIT + '" width="16" height="16" alt="" aria-hidden="true">' +
            '</button>' +
            '</dd>' +
            '</div>' +
            '<div style="display:flex;gap:8px;margin:6px 0;align-items:center;"><dt style="min-width:88px;color:#6a737d;">平台</dt><dd style="margin:0;flex:1;">' + esc(detail.platform || '-') + '</dd></div>' +
            '</dl>'
        );
    }

    /**
     * 获取并展示设备详情
     *
     * :param {string} peerId: 设备ID
     * :returns: 无
     * :rtype: void
     */
    function fetchAndShowDetail(peerId) {
        const {URLS} = getConstants();
        const {open: openModal} = getModal();
        const bodyEl = document.getElementById('nav2-modal-body');
        if (bodyEl) bodyEl.innerHTML = '<div style="color:#6a737d;">加载中...</div>';
        openModal('nav2-modal-root');
        const params = new URLSearchParams({peer_id: peerId});
        fetch(`${URLS.DEVICE_DETAIL}?${params.toString()}`, {
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
            const {escapeHTML} = getUtils();
            if (bodyEl) bodyEl.innerHTML = '<div style="color:#b91c1c;">' + escapeHTML(err.message || '加载失败') + '</div>';
        });
    }

    /**
     * 启动内联编辑
     *
     * :param {HTMLElement} containerEl: 容器元素
     * :param {string} field: 字段名
     * :param {string} peerId: 设备ID
     * :returns: 无
     * :rtype: void
     */
    function startInlineEdit(containerEl, field, peerId) {
        const {ICONS} = getConstants();
        const {escapeHTML} = getUtils();
        const esc = escapeHTML;
        const placeholder = field === 'alias' ? '请输入设备别名' : '用逗号分隔多个标签';
        const isInlineCell = containerEl.hasAttribute('data-inline-field');
        const original = containerEl.getAttribute('data-original')
            || (containerEl.querySelector('.nav2-detail-text')?.textContent || '')
            || '';
        const value = original;

        if (isInlineCell) {
            if (containerEl.querySelector('.nav2-inline-pop')) return;
            const pop = document.createElement('div');
            pop.className = 'nav2-inline-pop';
            pop.innerHTML =
                '<input type="text" class="nav2-input" value="' + esc(value) + '" ' +
                'data-field="' + esc(field) + '" data-peer="' + esc(peerId) + '" placeholder="' + esc(placeholder) + '" /> ' +
                '<button type="button" class="nav2-link nav2-edit-confirm" data-field="' + esc(field) + '" data-peer="' + esc(peerId) + '" aria-label="确认">' +
                '<img src="' + ICONS.CONFIRM + '" width="16" height="16" alt="" aria-hidden="true">' +
                '</button> ' +
                '<button type="button" class="nav2-link nav2-edit-cancel" data-field="' + esc(field) + '" data-peer="' + esc(peerId) + '" aria-label="取消">' +
                '<img src="' + ICONS.CANCEL + '" width="16" height="16" alt="" aria-hidden="true">' +
                '</button>';
            containerEl.appendChild(pop);
            const input = pop.querySelector('input[type="text"]');
            if (input) {
                input.focus();
                input.select();
            }
            return;
        }

        containerEl.innerHTML =
            '<input type="text" class="nav2-input" style="min-width:200px;" value="' + esc(value) + '" ' +
            'data-field="' + esc(field) + '" data-peer="' + esc(peerId) + '" placeholder="' + esc(placeholder) + '" /> ' +
            '<button type="button" class="nav2-link nav2-edit-confirm" data-field="' + esc(field) + '" data-peer="' + esc(peerId) + '" aria-label="确认">' +
            '<img src="' + ICONS.CONFIRM + '" width="16" height="16" alt="" aria-hidden="true">' +
            '</button> ' +
            '<button type="button" class="nav2-link nav2-edit-cancel" data-field="' + esc(field) + '" data-peer="' + esc(peerId) + '" aria-label="取消">' +
            '<img src="' + ICONS.CANCEL + '" width="16" height="16" alt="" aria-hidden="true">' +
            '</button>';
    }

    /**
     * 提交内联编辑
     *
     * :param {HTMLElement} ddEl: 容器元素
     * :param {string} field: 字段名
     * :param {string} peerId: 设备ID
     * :returns: 无
     * :rtype: void
     */
    function submitInlineEdit(ddEl, field, peerId) {
        const {showToast, parseFetchError, getCookie} = getUtils();
        const {URLS, STORAGE_KEY} = getConstants();
        const {renderContent} = getNavigation();
        const input = ddEl.querySelector('input[type="text"][data-field="' + field + '"]');
        const value = input ? input.value.trim() : '';
        const csrf = getCookie('csrftoken');
        const body = new URLSearchParams();
        body.set('peer_id', peerId);
        if (field === 'alias') {
            body.set('alias', value);
        } else if (field === 'tags') {
            body.set('tags', value);
        }
        fetch(URLS.DEVICE_UPDATE, {
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
            const inModal = !!ddEl.closest('#nav2-modal-root');
            if (inModal) {
                fetchAndShowDetail(peerId);
            }
            const extra = collectQueryOptions(document.getElementById('nav2-search-form'));
            renderContent('nav-2', extra);
            try {
                localStorage.setItem(STORAGE_KEY, 'nav-2');
            } catch (e) {
            }
        }).catch(err => {
            showToast(err.message || '保存失败，请稍后重试', 'error');
        });
    }

    /**
     * 取消内联编辑
     *
     * :param {HTMLElement} containerEl: 容器元素
     * :param {string} field: 字段名
     * :returns: 无
     * :rtype: void
     */
    function cancelInlineEdit(containerEl, field) {
        const {ICONS} = getConstants();
        const {escapeHTML} = getUtils();
        const esc = escapeHTML;
        const pop = containerEl.querySelector('.nav2-inline-pop');
        if (pop) {
            pop.remove();
            return;
        }
        const original = containerEl.getAttribute('data-original') || '';
        const peerAttr = containerEl.getAttribute('data-peer') || '';
        containerEl.innerHTML =
            '<span class="nav2-detail-text">' + esc(original || '-') + '</span> ' +
            '<button type="button" class="nav2-link nav2-edit-btn" data-field="' + esc(field) + '" data-peer="' + esc(peerAttr) + '" aria-label="编辑">' +
            '<img src="' + ICONS.EDIT + '" width="16" height="16" alt="" aria-hidden="true">' +
            '</button>';
    }

    // 导出到全局
    APP.nav2 = {
        toggleAutoRefresh,
        collectQueryOptions,
        prefillRenameForm,
        fetchAndShowDetail,
        startInlineEdit,
        submitInlineEdit,
        cancelInlineEdit
    };

    window.APP = APP;

})(window);
