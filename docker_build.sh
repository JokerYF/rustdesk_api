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
# - 将版本号写入项目根目录 `.env` (写入 APP_VERSION=...)
# - 兼容 macOS、Linux、Windows(WSL2) 终端环境
# =============================

IMAGE_NAME="rustdesk_api"

###
# 更新或新增 .env 变量
#
# :param str env_file: .env 文件路径
# :param str key: 变量名
# :param str value: 变量值
# :returns: 无
###
upsert_env_var() {
  local env_file="$1"
  local key="$2"
  local value="$3"

  # 若存在同名 key，则原位替换；否则追加
  if grep -q "^${key}=" "$env_file" 2>/dev/null; then
    # 以 key= 开头的整行替换为 key=value（仅替换首个匹配）
    awk -v k="$key" -v v="$value" 'BEGIN{OFS="="} $0 ~ ("^"k"=") {$0=k"="v} {print}' "$env_file" >"${env_file}.tmp" && mv "${env_file}.tmp" "$env_file"
  else
    printf "%s\n" "${key}=${value}" >>"$env_file"
  fi
}

###
# 生成时间版本号
#
# :returns str: 带前缀的时间版本号 (格式: dev_%Y%m%d%H%M%S)
###
generate_version() {
#  echo "dev_$(date +%Y%m%d%H%M%S)"
  echo "dev"
}

###
# 将版本号写入文件
#
# :param str version: 待写入的版本号
# :returns: 无
###
save_version_files() {
  local version="$1"; shift || true
  local repo_root
  repo_root="$(cd "$(dirname "$0")" && pwd)"
  local env_file="${repo_root}/.env"

  # 确保 .env 存在（不清空，保留已有变量）
  touch "$env_file"

  # 基础写入：APP_VERSION；DEBUG 默认 true（可被后续传参覆盖）
  upsert_env_var "$env_file" "APP_VERSION" "$version"
  upsert_env_var "$env_file" "DEBUG" "true"

  # 处理额外传入的 KEY=VALUE 参数，覆盖或追加
  local kv
  for kv in "$@"; do
    case "$kv" in
      *=*)
        local key="${kv%%=*}"
        local val="${kv#*=}"
        # 去除可能的首尾空白（兼容 BSD/macOS 与 GNU sed）
        key="$(printf "%s" "$key" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
        val="$(printf "%s" "$val" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
        [ -n "$key" ] && upsert_env_var "$env_file" "$key" "$val"
        ;;
      *)
        echo "警告: 忽略无效参数(需为 KEY=VALUE 形式): $kv" >&2
        ;;
    esac
  done

  echo "已更新: ${env_file} (APP_VERSION=${version})"
}

###
# 构建并打标签镜像
###
build_image() {
  local version="$1"
  echo "开始构建 Docker 镜像: ${IMAGE_NAME}:${version}"
  docker build \
    --build-arg APP_VERSION="${version}" \
    -t "${IMAGE_NAME}:${version}" \
    -f Dockerfile .

  echo "构建完成 -> ${IMAGE_NAME}:${version}"
}

###
# 打印脚本用法
#
# :returns: 无
###
print_usage() {
  echo "用法: $0 [KEY=VALUE ...]"
  echo "功能: 自动生成时间版本号并构建镜像，同时更新 .env (APP_VERSION=..., DEBUG=...)"
  echo "示例: $0 DEBUG=false API_BASE_URL=https://example.com"
}

###
# 脚本入口
#
# :returns: 以状态码指示成功或失败
###
main() {
  local version
  version="$(generate_version)"

  # 收集 KEY=VALUE 形式的附加参数
  local extras=()
  local arg
  for arg in "$@"; do
    case "$arg" in
      -h|--help)
        print_usage
        return 0
        ;;
      *=*)
        extras+=("$arg")
        ;;
      *)
        echo "警告: 忽略无效参数(需为 KEY=VALUE 或 --help): $arg" >&2
        ;;
    esac
  done

  save_version_files "$version" "${extras[@]:-}"
  build_image "$version"
}

main "$@"


