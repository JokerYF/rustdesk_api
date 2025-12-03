/**
 * 事件处理中心
 *
 * 集中管理所有页面事件委托和事件监听
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

    function getNav2() {
        return APP.nav2 || {};
    }

    function getNav3() {
        return APP.nav3 || {};
    }

    function getNav4() {
        return APP.nav4 || {};
    }

    function getConstants() {
        return {
            STORAGE_KEY: APP.STORAGE_KEY || 'homeActiveNavKey',
            URLS: APP.URLS || {}
        };
    }

    /**
     * 初始化所有事件监听
     *
     * :returns: 无
     * :rtype: void
     */
    function init() {
        const contentEl = document.getElementById('content');
        if (!contentEl) return;

        // ========== 通用事件 ==========

        // 通用弹窗关闭按钮
        contentEl.addEventListener('click', function (e) {
            const {close: closeModal} = getModal();
            const closeBtn = e.target.closest('[data-close]');
            if (!closeBtn) return;
            const token = closeBtn.getAttribute('data-close') || '';
            if (!token) return;
            e.preventDefault();
            const rootId = token.endsWith('-root') ? token : `${token}-root`;
            closeModal(rootId);
        }, false);

        // 点击遮罩关闭弹窗
        contentEl.addEventListener('click', function (e) {
            const backdrop = e.target.closest('.modal-backdrop');
            if (!backdrop) return;
            if (e.target === backdrop) {
                backdrop.style.display = 'none';
                backdrop.setAttribute('aria-hidden', 'true');
            }
        }, false);

        // ESC键关闭弹窗
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                const {closeAll: closeAllModals} = getModal();
                closeAllModals();
            }
        }, false);

        // ========== nav-1 事件 ==========

        // nav-1 分页
        contentEl.addEventListener('click', function (e) {
            const {renderContent} = getNavigation();
            const {STORAGE_KEY} = getConstants();
            const btn = e.target.closest('.nav1-page-btn');
            if (!btn) return;
            e.preventDefault();
            const page = btn.dataset.page;
            const key = btn.dataset.key || 'nav-1';
            if (page) {
                renderContent(key, {page});
                try {
                    localStorage.setItem(STORAGE_KEY, key);
                } catch (e) {
                }
            }
        }, false);

        // ========== nav-2 事件 ==========

        // nav-2 分页
        contentEl.addEventListener('click', function (e) {
            const {renderContent} = getNavigation();
            const {collectQueryOptions} = getNav2();
            const {STORAGE_KEY} = getConstants();
            const btn = e.target.closest('.nav2-page-btn');
            if (!btn) return;
            e.preventDefault();
            const page = btn.dataset.page;
            const key = btn.dataset.key || 'nav-2';
            if (page) {
                const formEl = document.getElementById('nav2-search-form');
                const extra = collectQueryOptions(formEl);
                extra.page = page;
                renderContent(key, extra);
                try {
                    localStorage.setItem(STORAGE_KEY, key);
                } catch (e) {
                }
            }
        }, false);

        // nav-2 重置
        contentEl.addEventListener('click', function (e) {
            const {renderContent} = getNavigation();
            const {STORAGE_KEY} = getConstants();
            const btn = e.target.closest('.nav2-reset-btn');
            if (!btn) return;
            e.preventDefault();
            const key = 'nav-2';
            renderContent(key);
            try {
                localStorage.setItem(STORAGE_KEY, key);
            } catch (e) {
            }
        }, false);

        // nav-2 全选
        contentEl.addEventListener('change', function (e) {
            const target = e.target;
            if (target && target.id === 'nav2-select-all') {
                const check = !!target.checked;
                document.querySelectorAll('.nav2-row-checkbox').forEach(cb => {
                    cb.checked = check;
                });
            }
        }, false);

        // nav-2 批量操作
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav2-bulk-btn');
            if (!btn) return;
            e.preventDefault();
            const action = btn.dataset.action || '';
            const selected = Array.from(document.querySelectorAll('.nav2-row-checkbox:checked')).map(cb => cb.value);
            console.log('nav-2 bulk action:', action, selected);
        }, false);

        // nav-2 行级操作
        contentEl.addEventListener('click', function (e) {
            const {fetchAndShowDetail, prefillRenameForm} = getNav2();
            const {showAddDeviceModal} = getNav4();
            const {open: openModal} = getModal();
            const btn = e.target.closest('.nav2-row-action');
            if (!btn) return;
            e.preventDefault();
            const action = btn.dataset.action || '';
            const id = btn.dataset.id || '';
            if (action === 'view') {
                fetchAndShowDetail(id);
            } else if (action === 'rename') {
                const currentAlias = btn.dataset.alias || '';
                prefillRenameForm(id, currentAlias);
                openModal('nav2-rename-root');
            } else if (action === 'add_to_book') {
                showAddDeviceModal(id);
            } else {
                console.log('nav-2 row action:', action, id);
            }
        }, false);

        // nav-2 详情/行内编辑（进入编辑态）
        contentEl.addEventListener('click', function (e) {
            const {startInlineEdit} = getNav2();
            const editBtn = e.target.closest('.nav2-edit-btn');
            if (!editBtn) return;
            e.preventDefault();
            const field = editBtn.getAttribute('data-field');
            const peer = editBtn.getAttribute('data-peer');
            let container = editBtn.closest('[data-inline-field="' + field + '"]') || document.getElementById('nav2-detail-' + field);
            if (!container) return;
            if (!container.hasAttribute('data-original')) {
                const text = (container.querySelector('.nav2-detail-text')?.textContent || '').trim();
                container.setAttribute('data-original', text);
            }
            if (!container.getAttribute('data-peer') && peer) {
                container.setAttribute('data-peer', peer);
            }
            startInlineEdit(container, field, peer);
        }, false);

        // nav-2 内联编辑（确认）
        contentEl.addEventListener('click', function (e) {
            const {submitInlineEdit} = getNav2();
            const okBtn = e.target.closest('.nav2-edit-confirm');
            if (!okBtn) return;
            e.preventDefault();
            const field = okBtn.getAttribute('data-field');
            const peer = okBtn.getAttribute('data-peer');
            const container = okBtn.closest('[data-inline-field]') || document.getElementById('nav2-detail-' + field);
            if (!container) return;
            submitInlineEdit(container, field, peer);
        }, false);

        // nav-2 内联编辑（取消）
        contentEl.addEventListener('click', function (e) {
            const {cancelInlineEdit} = getNav2();
            const cancelBtn = e.target.closest('.nav2-edit-cancel');
            if (!cancelBtn) return;
            e.preventDefault();
            const field = cancelBtn.getAttribute('data-field');
            const container = cancelBtn.closest('[data-inline-field]') || document.getElementById('nav2-detail-' + field);
            if (!container) return;
            cancelInlineEdit(container, field);
        }, false);

        // nav-2 点击别名文本进入编辑
        contentEl.addEventListener('click', function (e) {
            const {startInlineEdit} = getNav2();
            const textEl = e.target.closest('[data-inline-field="alias"] .nav2-detail-text');
            if (!textEl) return;
            const container = textEl.closest('[data-inline-field="alias"]');
            if (!container) return;
            if (container.querySelector('input[type="text"][data-field="alias"]')) return;
            const peer = container.getAttribute('data-peer') || '';
            if (!container.hasAttribute('data-original')) {
                const text = (textEl.textContent || '').trim();
                container.setAttribute('data-original', text);
            }
            startInlineEdit(container, 'alias', peer);
        }, false);

        // nav-2 重命名表单提交
        contentEl.addEventListener('submit', function (e) {
            const {showToast, parseFetchError, getCookie} = getUtils();
            const {renderContent} = getNavigation();
            const {close: closeModal} = getModal();
            const {collectQueryOptions} = getNav2();
            const {STORAGE_KEY, URLS} = getConstants();
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav2-rename-form') return;
            e.preventDefault();
            const fd = new FormData(formEl);
            const peerId = (fd.get('peer_id') || '').trim();
            const alias = (fd.get('alias') || '').trim();
            if (!peerId || !alias) {
                showToast('请输入有效的别名', 'error');
                return;
            }
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('peer_id', peerId);
            body.set('alias', alias);
            fetch(URLS.RENAME_ALIAS, {
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
                if (!data || data.ok !== true) {
                    throw new Error((data && (data.err_msg || data.error)) ? (data.err_msg || data.error) : '重命名失败');
                }
                closeModal('nav2-rename-root');
                const extra = collectQueryOptions(document.getElementById('nav2-search-form'));
                renderContent('nav-2', extra);
                try {
                    localStorage.setItem(STORAGE_KEY, 'nav-2');
                } catch (e) {
                }
            }).catch(err => {
                showToast(err.message || '重命名失败，请稍后重试', 'error');
            });
        }, false);

        // nav-2 搜索表单提交
        contentEl.addEventListener('submit', function (e) {
            const {renderContent} = getNavigation();
            const {collectQueryOptions} = getNav2();
            const {STORAGE_KEY} = getConstants();
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav2-search-form') return;
            e.preventDefault();
            const key = 'nav-2';
            const extra = collectQueryOptions(formEl);
            renderContent(key, extra);
            try {
                localStorage.setItem(STORAGE_KEY, key);
            } catch (e) {
            }
        }, false);

        // ========== nav-3 事件 ==========

        // nav-3 分页
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav3-page-btn');
            if (!btn) return;
            e.preventDefault();
            const page = btn.dataset.page;
            const key = btn.dataset.key || 'nav-3';
            if (page) {
                const formEl = document.getElementById('nav3-search-form');
                const {collectQueryOptions} = getNav3();
                const extra = collectQueryOptions(formEl);
                extra.page = page;
                renderContent(key, extra);
                try {
                    localStorage.setItem(STORAGE_KEY, key);
                } catch (e) {
                }
            }
        }, false);

        // nav-3 重置
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav3-reset-btn');
            if (!btn) return;
            e.preventDefault();
            const key = 'nav-3';
            renderContent(key);
            try {
                localStorage.setItem(STORAGE_KEY, key);
            } catch (e) {
            }
        }, false);

        // nav-3 搜索表单提交
        contentEl.addEventListener('submit', function (e) {
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav3-search-form') return;
            e.preventDefault();
            const key = 'nav-3';
            const {collectQueryOptions} = getNav3();
            const extra = collectQueryOptions(formEl);
            renderContent(key, extra);
            try {
                localStorage.setItem(STORAGE_KEY, key);
            } catch (e) {
            }
        }, false);

        // nav-3 行级操作
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav3-row-action');
            if (!btn) return;
            e.preventDefault();
            const action = btn.getAttribute('data-action') || '';
            const username = btn.getAttribute('data-username') || '';
            if (!action || !username) return;
            if (action === 'edit') {
                const fullname = btn.getAttribute('data-fullname') || '';
                const email = btn.getAttribute('data-email') || '';
                const isStaff = btn.getAttribute('data-is_staff') === '1';
                const uEl = document.getElementById('nav3-edit-username');
                const fEl = document.getElementById('nav3-edit-fullname');
                const eEl = document.getElementById('nav3-edit-email');
                const sEl = document.getElementById('nav3-edit-is-staff');
                if (uEl) uEl.value = username;
                if (fEl) fEl.value = fullname;
                if (eEl) eEl.value = email;
                if (sEl) {
                    sEl.checked = isStaff;
                    sEl.disabled = (username === document.body.dataset.currentUser);
                }
                openModal('nav3-edit-root');
            } else if (action === 'reset_pwd') {
                const uEl = document.getElementById('nav3-reset-username');
                const p1 = document.getElementById('nav3-reset-pass1');
                const p2 = document.getElementById('nav3-reset-pass2');
                if (uEl) uEl.value = username;
                if (p1) p1.value = '';
                if (p2) p2.value = '';
                openModal('nav3-reset-root');
            } else if (action === 'delete') {
                if (!confirm(`确定要删除用户"${username}"吗？删除后该用户将无法登录。`)) return;
                const csrf = getCookie('csrftoken');
                const body = new URLSearchParams();
                body.set('username', username);
                fetch(URLS.USER_DELETE, {
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
                    if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '删除失败');
                    showToast('删除成功', 'success');
                    const {collectQueryOptions} = getNav3();
                    const extra = collectQueryOptions(document.getElementById('nav3-search-form'));
                    renderContent('nav-3', extra);
                    try {
                        localStorage.setItem(STORAGE_KEY, 'nav-3');
                    } catch (e) {
                    }
                }).catch(err => {
                    showToast(err.message || '删除失败，请稍后重试', 'error');
                });
            }
        }, false);

        // nav-3 编辑表单提交
        contentEl.addEventListener('submit', function (e) {
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav3-edit-form') return;
            e.preventDefault();
            const fd = new FormData(formEl);
            const username = (fd.get('username') || '').trim();
            const fullName = (fd.get('full_name') || '').trim();
            const email = (fd.get('email') || '').trim();
            const isStaff = formEl.querySelector('#nav3-edit-is-staff')?.checked ? '1' : '0';
            if (!username) {
                showToast('用户名无效', 'error');
                return;
            }
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('username', username);
            body.set('full_name', fullName);
            body.set('email', email);
            body.set('is_staff', isStaff);
            fetch(URLS.USER_UPDATE, {
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
                closeModal('nav3-edit-root');
                const {collectQueryOptions} = getNav3();
                const extra = collectQueryOptions(document.getElementById('nav3-search-form'));
                renderContent('nav-3', extra);
                try {
                    localStorage.setItem(STORAGE_KEY, 'nav-3');
                } catch (e) {
                }
            }).catch(err => {
                showToast(err.message || '保存失败，请稍后重试', 'error');
            });
        }, false);

        // nav-3 重置密码表单提交
        contentEl.addEventListener('submit', function (e) {
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav3-reset-form') return;
            e.preventDefault();
            const fd = new FormData(formEl);
            const username = (fd.get('username') || '').trim();
            const p1 = (fd.get('password1') || '').trim();
            const p2 = (fd.get('password2') || '').trim();
            if (!username || !p1 || !p2) {
                showToast('请输入完整信息', 'error');
                return;
            }
            if (p1 !== p2) {
                showToast('两次密码不一致', 'error');
                return;
            }
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('username', username);
            body.set('password1', p1);
            body.set('password2', p2);
            fetch(URLS.USER_RESET_PWD, {
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
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '重置失败');
                closeModal('nav3-reset-root');
                const {collectQueryOptions} = getNav3();
                const extra = collectQueryOptions(document.getElementById('nav3-search-form'));
                renderContent('nav-3', extra);
                try {
                    localStorage.setItem(STORAGE_KEY, 'nav-3');
                } catch (e) {
                }
            }).catch(err => {
                showToast(err.message || '重置失败，请稍后重试', 'error');
            });
        }, false);

        // nav-3 新建用户按钮
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav3-create-btn');
            if (!btn) return;
            e.preventDefault();
            const form = document.getElementById('nav3-create-form');
            if (form) form.reset();
            openModal('nav3-create-root');
        }, false);

        // nav-3 新建用户表单提交
        contentEl.addEventListener('submit', function (e) {
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav3-create-form') return;
            e.preventDefault();
            const fd = new FormData(formEl);
            const username = (fd.get('username') || '').trim();
            const fullName = (fd.get('full_name') || '').trim();
            const email = (fd.get('email') || '').trim();
            const p1 = (fd.get('password1') || '').trim();
            const p2 = (fd.get('password2') || '').trim();
            const isStaff = formEl.querySelector('#nav3-create-is-staff')?.checked ? '1' : '0';
            if (!username || !p1 || !p2) {
                showToast('用户名和密码不能为空', 'error');
                return;
            }
            if (p1 !== p2) {
                showToast('两次密码不一致', 'error');
                return;
            }
            if (p1.length < 6) {
                showToast('密码长度至少为6位', 'error');
                return;
            }
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('username', username);
            body.set('password1', p1);
            body.set('password2', p2);
            if (fullName) body.set('full_name', fullName);
            if (email) body.set('email', email);
            body.set('is_staff', isStaff);
            fetch(URLS.USER_CREATE, {
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
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '创建失败');
                showToast('用户创建成功', 'success');
                closeModal('nav3-create-root');
                const {collectQueryOptions} = getNav3();
                const extra = collectQueryOptions(document.getElementById('nav3-search-form'));
                renderContent('nav-3', extra);
                try {
                    localStorage.setItem(STORAGE_KEY, 'nav-3');
                } catch (e) {
                }
            }).catch(err => {
                showToast(err.message || '创建失败，请稍后重试', 'error');
            });
        }, false);

        // ========== nav-4 事件 ==========

        // nav-4 分页
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-page-btn');
            if (!btn) return;
            e.preventDefault();
            const page = btn.dataset.page;
            const key = btn.dataset.key || 'nav-4';
            if (page) {
                const formEl = document.getElementById('nav4-search-form');
                const {collectQueryOptions} = getNav4();
                const extra = collectQueryOptions(formEl);
                extra.page = page;
                renderContent(key, extra);
                try {
                    localStorage.setItem(STORAGE_KEY, key);
                } catch (e) {
                }
            }
        }, false);

        // nav-4 重置
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-reset-btn');
            if (!btn) return;
            e.preventDefault();
            const key = 'nav-4';
            renderContent(key);
            try {
                localStorage.setItem(STORAGE_KEY, key);
            } catch (e) {
            }
        }, false);

        // nav-4 搜索表单提交
        contentEl.addEventListener('submit', function (e) {
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav4-search-form') return;
            e.preventDefault();
            const key = 'nav-4';
            const {collectQueryOptions} = getNav4();
            const extra = collectQueryOptions(formEl);
            renderContent(key, extra);
            try {
                localStorage.setItem(STORAGE_KEY, key);
            } catch (e) {
            }
        }, false);

        // nav-4 新建地址簿按钮
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-create-btn');
            if (!btn) return;
            e.preventDefault();
            const nameEl = document.getElementById('nav4-create-name');
            const typeEl = document.getElementById('nav4-create-type');
            if (nameEl) nameEl.value = '';
            if (typeEl) typeEl.value = 'private';
            openModal('nav4-create-root');
        }, false);

        // nav-4 新建地址簿表单提交
        contentEl.addEventListener('submit', function (e) {
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav4-create-form') return;
            e.preventDefault();
            const fd = new FormData(formEl);
            const personalName = (fd.get('personal_name') || '').trim();
            const personalType = (fd.get('personal_type') || '').trim();
            if (!personalName) {
                showToast('请输入地址簿名称', 'error');
                return;
            }
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('personal_name', personalName);
            body.set('personal_type', personalType);
            fetch(URLS.PERSONAL_CREATE, {
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
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '创建失败');
                closeModal('nav4-create-root');
                const {collectQueryOptions} = getNav4();
                const extra = collectQueryOptions(document.getElementById('nav4-search-form'));
                renderContent('nav-4', extra);
                showToast('创建成功', 'success');
                try {
                    localStorage.setItem(STORAGE_KEY, 'nav-4');
                } catch (e) {
                }
            }).catch(err => {
                showToast(err.message || '创建失败，请稍后重试', 'error');
            });
        }, false);

        // nav-4 行级操作
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-row-action');
            if (!btn) return;
            e.preventDefault();
            const action = btn.getAttribute('data-action') || '';
            const guid = btn.getAttribute('data-guid') || '';
            const name = btn.getAttribute('data-name') || '';
            if (!action || !guid) return;

            if (action === 'view') {
                const {
                    collectQueryOptions: collectQueryOptions4,
                    fetchAndShowDetail: fetchAndShowDetail4,
                    startInlineEdit: startInlineEdit4
                } = getNav4();
                fetchAndShowDetail(guid);
            } else if (action === 'rename') {
                const guidEl = document.getElementById('nav4-rename-guid');
                const nameEl = document.getElementById('nav4-rename-name');
                if (guidEl) guidEl.value = guid;
                if (nameEl) {
                    nameEl.value = name;
                    nameEl.focus();
                    nameEl.select();
                }
                openModal('nav4-rename-root');
            } else if (action === 'delete') {
                if (!confirm(`确定要删除地址簿"${name}"吗？删除后将无法恢复。`)) return;
                const csrf = getCookie('csrftoken');
                const body = new URLSearchParams();
                body.set('guid', guid);
                fetch(URLS.PERSONAL_DELETE, {
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
                    if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '删除失败');
                    const {collectQueryOptions} = getNav4();
                    const extra = collectQueryOptions(document.getElementById('nav4-search-form'));
                    renderContent('nav-4', extra);
                    showToast('删除成功', 'success');
                    try {
                        localStorage.setItem(STORAGE_KEY, 'nav-4');
                    } catch (e) {
                    }
                }).catch(err => {
                    showToast(err.message || '删除失败，请稍后重试', 'error');
                });
            }
        }, false);

        // nav-4 重命名表单提交
        contentEl.addEventListener('submit', function (e) {
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav4-rename-form') return;
            e.preventDefault();
            const fd = new FormData(formEl);
            const guid = (fd.get('guid') || '').trim();
            const newName = (fd.get('new_name') || '').trim();
            if (!guid || !newName) {
                showToast('请输入新名称', 'error');
                return;
            }
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('guid', guid);
            body.set('new_name', newName);
            fetch(URLS.PERSONAL_RENAME, {
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
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '重命名失败');
                closeModal('nav4-rename-root');
                const {collectQueryOptions} = getNav4();
                const extra = collectQueryOptions(document.getElementById('nav4-search-form'));
                renderContent('nav-4', extra);
                showToast('重命名成功', 'success');
                try {
                    localStorage.setItem(STORAGE_KEY, 'nav-4');
                } catch (e) {
                }
            }).catch(err => {
                showToast(err.message || '重命名失败，请稍后重试', 'error');
            });
        }, false);

        // nav-4 从地址簿移除设备
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-remove-device-btn');
            if (!btn) return;
            e.preventDefault();
            const guid = btn.getAttribute('data-guid') || '';
            const peerId = btn.getAttribute('data-peer-id') || '';
            if (!guid || !peerId) return;
            if (!confirm('确定要从地址簿中移除该设备吗？')) return;
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('guid', guid);
            body.set('peer_id', peerId);
            fetch(URLS.PERSONAL_REMOVE_DEVICE, {
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
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '移除失败');
                const {
                    collectQueryOptions: collectQueryOptions4,
                    fetchAndShowDetail: fetchAndShowDetail4,
                    startInlineEdit: startInlineEdit4
                } = getNav4();
                fetchAndShowDetail(guid);
                showToast('移除成功', 'success');
            }).catch(err => {
                showToast(err.message || '移除失败，请稍后重试', 'error');
            });
        }, false);

        // nav-4 添加标签按钮点击事件
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-add-tag-btn');
            if (!btn) return;
            e.preventDefault();
            // 重置表单
            const form = document.getElementById('nav4-add-tag-form');
            if (form) form.reset();
            openModal('nav4-add-tag-root');
        }, false);

        // nav-4 编辑标签按钮点击事件
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-edit-tag-btn');
            if (!btn) return;
            e.preventDefault();
            const tagItem = btn.closest('.nav4-tag-item');
            if (!tagItem) return;
            const tagId = tagItem.getAttribute('data-tag-id');
            const tagName = tagItem.getAttribute('data-tag-name');
            const tagColor = tagItem.querySelector('.nav4-tag-name').style.backgroundColor;

            // 填充表单
            const tagIdEl = document.getElementById('nav4-edit-tag-id');
            const tagNameEl = document.getElementById('nav4-edit-tag-name');
            const tagColorEl = document.getElementById('nav4-edit-tag-color');

            if (tagIdEl) tagIdEl.value = tagId;
            if (tagNameEl) {
                tagNameEl.value = tagName;
                tagNameEl.focus();
                tagNameEl.select();
            }
            if (tagColorEl) tagColorEl.value = tagColor;

            openModal('nav4-edit-tag-root');
        }, false);

        // nav-4 删除标签按钮点击事件
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-delete-tag-btn');
            if (!btn) return;
            e.preventDefault();
            const tagItem = btn.closest('.nav4-tag-item');
            if (!tagItem) return;
            const tagId = tagItem.getAttribute('data-tag-id');
            const tagName = tagItem.getAttribute('data-tag-name');

            if (!confirm(`确定要删除标签"${tagName}"吗？`)) return;

            const {URLS} = getConstants();
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('tag_id', tagId);

            fetch(URLS.PERSONAL_DELETE_TAG, {
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
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '删除失败');
                const {renderContent} = getNavigation();
                renderContent('nav-4');
                showToast('删除成功', 'success');
            }).catch(err => {
                showToast(err.message || '删除失败，请稍后重试', 'error');
            });
        }, false);

        // nav-4 添加标签表单提交
        contentEl.addEventListener('submit', function (e) {
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav4-add-tag-form') return;
            e.preventDefault();
            const fd = new FormData(formEl);
            const guid = fd.get('guid') || '';
            const tag = (fd.get('tag') || '').trim();
            const color = fd.get('color') || '#2da44e';

            if (!guid || !tag) {
                showToast('请输入标签名称', 'error');
                return;
            }

            const {URLS} = getConstants();
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('guid', guid);
            body.set('tag', tag);
            body.set('color', color);

            fetch(URLS.PERSONAL_ADD_TAG, {
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
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '添加失败');
                closeModal('nav4-add-tag-root');
                const {renderContent} = getNavigation();
                renderContent('nav-4');
                showToast('添加成功', 'success');
            }).catch(err => {
                showToast(err.message || '添加失败，请稍后重试', 'error');
            });
        }, false);

        // nav-4 编辑标签表单提交
        contentEl.addEventListener('submit', function (e) {
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav4-edit-tag-form') return;
            e.preventDefault();
            const fd = new FormData(formEl);
            const tagId = fd.get('tag_id') || '';
            const tag = (fd.get('tag') || '').trim();
            const color = fd.get('color') || '#2da44e';

            if (!tagId || !tag) {
                showToast('请输入标签名称', 'error');
                return;
            }

            const {URLS} = getConstants();
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('tag_id', tagId);
            body.set('tag', tag);
            body.set('color', color);

            fetch(URLS.PERSONAL_EDIT_TAG, {
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
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '编辑失败');
                closeModal('nav4-edit-tag-root');
                const {renderContent} = getNavigation();
                renderContent('nav-4');
                showToast('编辑成功', 'success');
            }).catch(err => {
                showToast(err.message || '编辑失败，请稍后重试', 'error');
            });
        }, false);

        // nav-4 添加设备按钮点击事件
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-add-device-btn');
            if (!btn) return;
            e.preventDefault();
            // 重置表单
            const form = document.getElementById('nav4-add-device-form');
            if (form) form.reset();
            openModal('nav4-add-device-root');
        }, false);

        // nav-4 编辑设备按钮点击事件
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-edit-device-btn');
            if (!btn) return;
            e.preventDefault();
            const peerId = btn.getAttribute('data-peer-id');
            const alias = btn.getAttribute('data-alias');

            // 填充表单
            const peerIdEl = document.getElementById('nav4-edit-device-peer-id');
            const aliasEl = document.getElementById('nav4-edit-device-alias');

            if (peerIdEl) peerIdEl.value = peerId;
            if (aliasEl) {
                aliasEl.value = alias || '';
                aliasEl.focus();
            }

            openModal('nav4-edit-device-root');
        }, false);

        // nav-4 删除设备按钮点击事件
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-delete-device-btn');
            if (!btn) return;
            e.preventDefault();
            const peerId = btn.getAttribute('data-peer-id');

            if (!confirm(`确定要从地址簿中删除该设备吗？`)) return;

            // 获取默认地址簿GUID
            const guid = document.getElementById('nav4-add-device-guid')?.value;
            if (!guid) return;

            const {URLS} = getConstants();
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('guid', guid);
            body.set('peer_id', peerId);

            fetch(URLS.PERSONAL_REMOVE_DEVICE, {
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
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '删除失败');
                const {renderContent} = getNavigation();
                renderContent('nav-4');
                showToast('删除成功', 'success');
            }).catch(err => {
                showToast(err.message || '删除失败，请稍后重试', 'error');
            });
        }, false);

        // nav-4 添加设备表单提交
        contentEl.addEventListener('submit', function (e) {
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav4-add-device-form') return;
            e.preventDefault();
            const fd = new FormData(formEl);
            const guid = fd.get('guid') || '';
            const peerId = (fd.get('peer_id') || '').trim();
            const alias = (fd.get('alias') || '').trim();

            if (!guid || !peerId) {
                showToast('请输入设备ID', 'error');
                return;
            }

            const {URLS} = getConstants();
            const csrf = getCookie('csrftoken');
            const body = new URLSearchParams();
            body.set('guid', guid);
            body.set('peer_id', peerId);
            if (alias) {
                body.set('alias', alias);
            }

            fetch(URLS.PERSONAL_ADD_DEVICE, {
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
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '添加失败');
                closeModal('nav4-add-device-root');
                const {renderContent} = getNavigation();
                renderContent('nav-4');
                showToast('添加成功', 'success');
            }).catch(err => {
                showToast(err.message || '添加失败，请稍后重试', 'error');
            });
        }, false);

        // nav-4 编辑设备表单提交
        contentEl.addEventListener('submit', function (e) {
            const formEl = e.target;
            if (!formEl || formEl.id !== 'nav4-edit-device-form') return;
            e.preventDefault();
            const fd = new FormData(formEl);
            const guid = fd.get('guid') || '';
            const peerId = fd.get('peer_id') || '';
            const alias = (fd.get('alias') || '').trim();
            const tagsSelect = document.getElementById('nav4-edit-device-tags');
            const selectedTags = Array.from(tagsSelect.selectedOptions).map(option => option.value).join(',');

            if (!guid || !peerId || !alias) {
                showToast('请输入设备别名', 'error');
                return;
            }

            const {URLS} = getConstants();
            const csrf = getCookie('csrftoken');

            // 更新别名
            const aliasBody = new URLSearchParams();
            aliasBody.set('guid', guid);
            aliasBody.set('peer_id', peerId);
            aliasBody.set('alias', alias);

            fetch(URLS.PERSONAL_UPDATE_ALIAS, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'X-CSRFToken': csrf
                },
                body: aliasBody.toString()
            }).then(resp => {
                if (!resp.ok) return parseFetchError(resp);
                return resp.json();
            }).then(data => {
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '更新别名失败');

                // 更新标签
                const tagsBody = new URLSearchParams();
                tagsBody.set('guid', guid);
                tagsBody.set('peer_id', peerId);
                tagsBody.set('tags', selectedTags);

                return fetch(URLS.PERSONAL_UPDATE_TAGS, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                        'X-CSRFToken': csrf
                    },
                    body: tagsBody.toString()
                });
            }).then(resp => {
                if (!resp.ok) return parseFetchError(resp);
                return resp.json();
            }).then(data => {
                if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '更新标签失败');

                closeModal('nav4-edit-device-root');
                const {renderContent} = getNavigation();
                renderContent('nav-4');
                showToast('更新成功', 'success');
            }).catch(err => {
                showToast(err.message || '更新失败，请稍后重试', 'error');
            });
        }, false);

        // nav-4 标签筛选设备功能
        contentEl.addEventListener('click', function (e) {
            const tagName = e.target.closest('.nav4-tag-name');
            if (!tagName) return;
            e.preventDefault();

            const tagText = tagName.textContent.trim();
            const deviceRows = document.querySelectorAll('#nav4-devices tbody tr');

            deviceRows.forEach(row => {
                const tagsCell = row.querySelector('td:nth-child(6)');
                const tagsText = tagsCell.textContent.trim();

                if (tagsText.includes(tagText) || tagsText === '无标签') {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }, false);

        // nav-4 设备搜索功能
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-search-device-btn');
            if (!btn) return;
            e.preventDefault();

            const searchInput = document.getElementById('nav4-device-search');
            const searchText = searchInput.value.trim().toLowerCase();
            const deviceRows = document.querySelectorAll('#nav4-devices tbody tr');

            deviceRows.forEach(row => {
                const aliasCell = row.querySelector('td:nth-child(1)');
                const deviceNameCell = row.querySelector('td:nth-child(2)');

                const aliasText = aliasCell.textContent.trim().toLowerCase();
                const deviceNameText = deviceNameCell.textContent.trim().toLowerCase();

                if (aliasText.includes(searchText) || deviceNameText.includes(searchText)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }, false);

        // nav-4 编辑地址簿设备信息
        contentEl.addEventListener('click', function (e) {
            const btn = e.target.closest('.nav4-edit-btn');
            if (!btn) return;
            e.preventDefault();
            const field = btn.getAttribute('data-field');
            const guid = btn.getAttribute('data-guid');
            const peerId = btn.getAttribute('data-peer-id');
            const cell = btn.closest('.nav4-editable-cell');
            if (!cell || !field || !guid || !peerId) return;
            if (cell.querySelector('input[type="text"]')) return;
            const {
                collectQueryOptions: collectQueryOptions4,
                fetchAndShowDetail: fetchAndShowDetail4,
                startInlineEdit: startInlineEdit4
            } = getNav4();
            startInlineEdit(cell, field, guid, peerId);
        }, false);

        // 添加设备到地址簿表单提交
        const addToBookForm = document.getElementById('nav2-add-to-book-form');
        if (addToBookForm) {
            addToBookForm.addEventListener('submit', function (e) {
                e.preventDefault();
                const peerId = document.getElementById('nav2-add-to-book-peer-id').value.trim();
                const guid = document.getElementById('nav2-add-to-book-guid').value.trim();
                const alias = document.getElementById('nav2-add-to-book-alias').value.trim();

                if (!guid) {
                    showToast('请选择地址簿', 'error');
                    return;
                }

                const csrf = getCookie('csrftoken');
                const body = new URLSearchParams();
                body.set('guid', guid);
                body.set('peer_id', peerId);
                if (alias) {
                    body.set('alias', alias);
                }

                fetch(URLS.PERSONAL_ADD_DEVICE, {
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
                    if (!data || data.ok !== true) throw new Error((data && (data.err_msg || data.error)) || '添加失败');
                    showToast('添加成功', 'success');
                    closeModal('nav2-add-to-book-root');
                }).catch(err => {
                    showToast(err.message || '添加失败，请稍后重试', 'error');
                });
            });
        }

        // ========== 导航内容加载完成事件 ==========

        // 监听内容加载完成，根据导航项决定是否开启 nav-2 自动刷新
        document.addEventListener('contentLoaded', function (e) {
            const key = e.detail?.key || '';
            const {
                collectQueryOptions,
                startInlineEdit,
                submitInlineEdit,
                cancelInlineEdit,
                toggleAutoRefresh
            } = getNav2();
            toggleAutoRefresh(key === 'nav-2');
        }, false);

        // 页面可见性变化
        document.addEventListener('visibilitychange', function () {
            // 页面可见时，如果 nav-2 正在运行，则恢复轮询
            if (!document.hidden) {
                // 由 nav2 模块处理
            }
        }, false);

        // 页面卸载前清理资源
        window.addEventListener('beforeunload', function () {
            const {
                collectQueryOptions,
                startInlineEdit,
                submitInlineEdit,
                cancelInlineEdit,
                toggleAutoRefresh
            } = getNav2();
            toggleAutoRefresh(false);
        }, false);
    }

    // 导出到全局
    APP.events = {
        init
    };

    window.APP = APP;

})(window);
