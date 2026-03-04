/**
 * 用户管理页面模块 (nav-3)
 *
 * 处理用户列表、编辑、重置密码、删除、创建等功能
 */

(function (window) {
    'use strict';

    const APP = window.APP || {};

    function getUtils() {
        return APP.utils || {};
    }

    function collectQueryOptions(formEl) {
        const {collectFormParams} = getUtils();
        return collectFormParams(formEl, ['q', 'page_size']);
    }

    // 导出到全局
    APP.nav3 = {
        collectQueryOptions
    };

    window.APP = APP;

})(window);
