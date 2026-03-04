/**
 * 工具函数模块
 *
 * 包含通用的辅助函数：Toast提示、错误处理、Cookie操作等
 */

(function (window) {
    'use strict';

    const APP = window.APP || {};

    /**
     * 获取Toast容器
     *
     * :returns: Toast容器DOM元素
     * :rtype: HTMLElement
     */
    function getToastContainer() {
        let c = document.querySelector('.toast-container');
        if (!c) {
            c = document.createElement('div');
            c.className = 'toast-container';
            document.body.appendChild(c);
        }
        return c;
    }

    /**
     * 显示Toast提示
     *
     * :param {string} message: 提示消息
     * :param {string} type: 提示类型（error|success|info）
     * :param {number} timeoutMs: 显示时长（毫秒）
     * :returns: 无
     * :rtype: void
     */
    function showToast(message, type = 'error', timeoutMs = 3000) {
        const container = getToastContainer();
        const div = document.createElement('div');
        const kind = (type === 'success' || type === 'info') ? type : 'error';
        div.className = `toast toast--${kind}`;
        div.textContent = message || '发生错误';
        container.appendChild(div);
        requestAnimationFrame(() => div.classList.add('toast--show'));
        setTimeout(() => {
            div.classList.remove('toast--show');
            setTimeout(() => div.remove(), 200);
        }, timeoutMs);
    }

    /**
     * 解码消息文本
     *
     * :param {string} raw: 原始文本
     * :param {string} fallbackText: 备用文本
     * :returns: 解码后的文本
     * :rtype: string
     */
    function decodeMessage(raw, fallbackText = '发生错误') {
        let msg = String(raw || '').trim();
        if (!msg) return fallbackText;
        if (msg[0] === '{' || msg[0] === '[') {
            try {
                const data = JSON.parse(msg);
                msg = String((data && (data.err_msg || data.error || data.message || data.detail)) || '').trim() || fallbackText;
            } catch (e) {
                console.warn('decodeMessage: JSON解析失败', e);
            }
        }
        if (/%[0-9A-Fa-f]{2}/.test(msg)) {
            try {
                msg = decodeURIComponent(msg);
            } catch (e) {
                console.warn('decodeMessage: URI解码失败', e);
            }
        }
        try {
            const ta = document.createElement('textarea');
            ta.innerHTML = msg;
            msg = ta.value || ta.textContent || msg;
        } catch (e) {
            console.warn('decodeMessage: HTML实体解码失败', e);
        }
        msg = String(msg || '').trim();
        return msg || fallbackText;
    }

    /**
     * 解析请求错误
     *
     * :param {Response} resp: Fetch Response对象
     * :returns: Promise that rejects with Error
     * :rtype: Promise
     */
    function parseFetchError(resp) {
        const statusText = `HTTP ${resp.status}`;
        return resp.clone().json().then(d => {
            const msg = (d && (d.err_msg || d.error || d.message || d.detail)) ? String(d.err_msg || d.error || d.message || d.detail) : statusText;
            throw new Error(decodeMessage(msg, statusText));
        }).catch(() => {
            return resp.clone().text().then(t => {
                const txt = (t || '').trim();
                throw new Error(decodeMessage(txt, statusText));
            });
        });
    }

    /**
     * 从Cookie中获取指定键的值
     *
     * :param {string} name: Cookie名称
     * :returns: Cookie值或null
     * :rtype: string|null
     */
    function getCookie(name) {
        let val = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const c = cookies[i].trim();
                if (c.substring(0, name.length + 1) === (name + '=')) {
                    val = decodeURIComponent(c.substring(name.length + 1));
                    break;
                }
            }
        }
        return val;
    }

    /**
     * HTML转义，防止XSS
     *
     * :param {string} str: 需要转义的字符串
     * :returns: 转义后的安全字符串
     * :rtype: string
     */
    function escapeHTML(str) {
        const s = String(str ?? '');
        if (!s) return s;
        return s
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /**
     * 通用fetch请求封装，自动处理CSRF、错误解析和JSON响应
     *
     * :param {string} url: 请求URL
     * :param {Object} options: fetch选项，可包含 method、body、headers 等
     * :returns: 解析后的响应数据
     * :rtype: Promise<Object>
     */
    function fetchJSON(url, options = {}) {
        const defaults = {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        };
        const merged = Object.assign({}, defaults, options);
        merged.headers = Object.assign({}, defaults.headers, options.headers || {});
        if (merged.method === 'POST' && !merged.headers['Content-Type']) {
            merged.headers['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8';
        }
        if (merged.method === 'POST' && !merged.headers['X-CSRFToken']) {
            merged.headers['X-CSRFToken'] = getCookie('csrftoken');
        }
        return fetch(url, merged).then(function (resp) {
            if (!resp.ok) return parseFetchError(resp);
            return resp.json();
        }).then(function (data) {
            if (!data || data.ok !== true) {
                throw new Error((data && (data.err_msg || data.error)) || '操作失败');
            }
            return data;
        });
    }

    /**
     * POST表单数据的便捷封装
     *
     * :param {string} url: 请求URL
     * :param {Object} params: 键值对参数
     * :returns: 解析后的响应数据
     * :rtype: Promise<Object>
     */
    function postForm(url, params) {
        const body = new URLSearchParams();
        Object.keys(params).forEach(function (k) {
            if (params[k] !== undefined && params[k] !== null) {
                body.set(k, params[k]);
            }
        });
        return fetchJSON(url, {
            method: 'POST',
            body: body.toString()
        });
    }

    /**
     * 通用表单参数收集
     *
     * :param {HTMLFormElement} formEl: 表单元素
     * :param {Array<string>} fields: 要收集的字段名列表
     * :returns: 非空参数的键值对
     * :rtype: Object
     */
    function collectFormParams(formEl, fields) {
        const params = {};
        if (!formEl) return params;
        const formData = new FormData(formEl);
        fields.forEach(function (k) {
            const v = formData.get(k);
            if (v !== null && String(v).trim() !== '') {
                params[k] = String(v).trim();
            }
        });
        return params;
    }

    // 导出到全局
    APP.utils = {
        showToast,
        decodeMessage,
        parseFetchError,
        getCookie,
        escapeHTML,
        fetchJSON,
        postForm,
        collectFormParams
    };

    window.APP = APP;

})(window);

