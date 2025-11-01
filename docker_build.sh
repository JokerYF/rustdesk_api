#!/bin/bash
set -euo pipefail

# =============================
# docker_build.sh
#
# 用法:
#   ./docker_build.sh
#
# 说明:
# - 自动生成时间版本号并构建镜像: rustdesk_api:<version>
# - 将版本号写入项目根目录 `.env` (写入 VERSION=...)
# - 兼容 macOS、Linux、Windows(WSL2) 终端环境
# =============================

IMAGE_NAME="rustdesk_api"

###
# 生成时间版本号
#
# :returns str: 按照时间生成的版本号 (格式: %Y%m%d%H%M%S)
###
generate_version() {
  # 说明: 用户要求格式为 %Y%M%D%H%M%S，其中 %D 会产生斜杠(例如 10/31/25)，
  # 这会导致 Docker tag 含非法字符。为保证跨平台与合法性，这里采用等价无分隔符格式: %Y%m%d%H%M%S。
  date +%Y%m%d%H%M%S
}

###
# 将版本号写入文件
#
# :param str version: 待写入的版本号
# :returns: 无
###
save_version_files() {
  local version="$1"
  local repo_root
  repo_root="$(cd "$(dirname "$0")" && pwd)"

  # .env: 写入 VERSION=...（简单覆盖方式，若需保留其它变量可改为就地替换）
  echo "VERSION=${version}" >"${repo_root}/.env"

  echo "已写入版本号到: ${repo_root}/.env (VERSION=${version})"
}

###
# 构建并打标签镜像
###
build_image() {
  local version="$1"
  echo "开始构建 Docker 镜像: ${IMAGE_NAME}:${version}"
  docker build -t "${IMAGE_NAME}:${version}" -f Dockerfile .

  echo "构建完成 -> ${IMAGE_NAME}:${version}"
}

###
# 打印脚本用法
#
# :returns: 无
###
print_usage() {
  echo "用法: $0"
  echo "功能: 自动生成时间版本号并构建镜像，同时更新 .env (VERSION=...)"
}

###
# 脚本入口
#
# :returns: 以状态码指示成功或失败
###
main() {
  if [ $# -gt 0 ]; then
    echo "提示: 本脚本现已改为自动生成时间版本号, 忽略传入参数: $*"
  fi

  local version
  version="$(generate_version)"

  save_version_files "$version"
  build_image "$version"
}

main "$@"


