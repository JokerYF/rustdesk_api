/**
 * 导航管理模块
 *
 * 处理侧边栏导航的激活、内容渲染等核心功能
 */

(function (window) {
    'use strict';

    const APP = window.APP || {};

    // 延迟获取依赖，避免模块加载顺序问题
    function getUtils() {
        return APP.utils || {};
    }

    function getConstants() {
        return {
            STORAGE_KEY: APP.STORAGE_KEY || 'homeActiveNavKey',
            URLS: APP.URLS || {}
        };
    }

    /**
     * 根据key激活侧边导航链接
     *
     * :param {string} itemKey: 导航项标识
     * :returns: 被激活的链接元素
     * :rtype: HTMLAnchorElement|null
     */
    function activateLinkByKey(itemKey) {
        const allLinks = document.querySelectorAll('.nav a');
        allLinks.forEach(a => a.classList.remove('active'));
        const target = document.querySelector(`.nav a[data-key="${itemKey}"]`);
        if (target) {
            target.classList.add('active');
        }
        return target;
    }

    /**
     * 更新页面标题
     *
     * :param {string} itemKey: 导航项标识
     * :returns: 无
     * :rtype: void
     */
    function updatePageTitle(itemKey) {
        const titleMap = {
            'nav-1': '首页',
            'nav-2': '设备管理',
            'nav-3': '用户管理',
            'nav-4': '地址簿'
        };
        const pageTitle = titleMap[itemKey] || '控制台';
        document.title = `${pageTitle} - RustDeskApi`;
    }

    /**
     * 渲染右侧内容
     *
     * :param {string} itemKey: 导航项标识
     * :param {Object} options: 额外查询参数
     * :returns: 无
     * :rtype: void
     */
    function renderContent(itemKey, options = {}) {
        const {URLS} = getConstants();
        const content = document.getElementById('content');
        const emptyHint = document.getElementById('empty-hint');
        if (emptyHint) {
            emptyHint.remove();
        }
        content.setAttribute('aria-busy', 'true');
        const params = new URLSearchParams({key: itemKey});
        Object.entries(options || {}).forEach(([k, v]) => {
            if (v !== undefined && v !== null && String(v).trim() !== '') {
                params.append(k, v);
            }
        });
        fetch(`${URLS.NAV_CONTENT}?${params.toString()}`, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(resp => {
            if (resp.redirected && resp.url && resp.url.indexOf(URLS.LOGIN) !== -1) {
                window.location.href = `${URLS.LOGIN}?next=${encodeURIComponent(URLS.HOME)}`;
                return Promise.reject(new Error('redirected_to_login'));
            }
            if (!resp.ok) {
                if (resp.status === 401 || resp.status === 403) {
                    window.location.href = `${URLS.LOGIN}?next=${encodeURIComponent(URLS.HOME)}`;
                    return Promise.reject(new Error('unauthorized_to_login'));
                }
                throw new Error(`HTTP ${resp.status}`);
            }
            return resp.text();
        }).then(html => {
            content.innerHTML = html;
            // 触发内容加载完成事件
            const event = new CustomEvent('contentLoaded', {detail: {key: itemKey}});
            document.dispatchEvent(event);
        }).catch(err => {
            if (err && err.message !== 'redirected_to_login' && err.message !== 'unauthorized_to_login') {
                console.warn('renderContent: 内容加载失败', err);
            }
            content.innerHTML = '<p class="content-empty">加载失败，请稍后重试</p>';
        }).finally(() => {
            content.setAttribute('aria-busy', 'false');
        });
    }

    /**
     * 处理导航点击
     *
     * :param {MouseEvent} event: 点击事件
     * :returns: 无
     * :rtype: void
     */
    function handleNavClick(event) {
        event.preventDefault();
        const {STORAGE_KEY} = getConstants();
        const link = event.currentTarget;
        const key = link.dataset.key;
        activateLinkByKey(key);
        updatePageTitle(key);
        renderContent(key);
        try {
            localStorage.setItem(STORAGE_KEY, key);
        } catch (e) {
        }
    }

    /**
     * 初始化默认视图
     *
     * :returns: 无
     * :rtype: void
     */
    function initializeDefaultView() {
        const {STORAGE_KEY} = getConstants();
        let keyFromStorage = null;
        try {
            keyFromStorage = localStorage.getItem(STORAGE_KEY);
        } catch (e) {
            keyFromStorage = null;
        }
        let defaultKey = keyFromStorage;
        if (!defaultKey) {
            const firstLink = document.querySelector('.nav a');
            defaultKey = firstLink ? firstLink.dataset.key : 'nav-1';
        }
        activateLinkByKey(defaultKey);
        updatePageTitle(defaultKey);
        renderContent(defaultKey);
    }

    /**
     * 初始化导航系统
     *
     * :returns: 无
     * :rtype: void
     */
    function init() {
        document.querySelectorAll('.nav a').forEach(a => {
            a.addEventListener('click', handleNavClick, false);
        });
        initializeDefaultView();
    }

    // 导出到全局
    APP.navigation = {
        activateLinkByKey,
        updatePageTitle,
        renderContent,
        handleNavClick,
        initializeDefaultView,
        init
    };

    window.APP = APP;

})(window);

