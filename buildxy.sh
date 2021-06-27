#!/usr/bin/env bash

set -euo pipefail

if [ -z "${CONTAINER_NAME:-}" ] ; then
  echo "ERROR: CONTAINER_NAME is not set" >&2
  exit 1
fi

BUILDXY_MODE=${BUILDXY_MODE:-push}

if [ "$BUILDXY_MODE" != "build" ] && [ "$BUILDXY_MODE" != "push" ] ; then
  echo "ERROR: unknown BUILDXY_MODE '$BUILDXY_MODE'" >&2
  exit 1
fi

PLATFORMS=${PLATFORMS:-linux/amd64}
CONTAINER_REGISTRY=${CONTAINER_REGISTRY:-docker.io}
CONTAINER_TAG=${CONTAINER_TAG:-${GITHUB_HEAD_REF:-$(git rev-parse --abbrev-ref HEAD 2> /dev/null || true)}}

# shellcheck disable=SC2001
CONTAINER_TAG=$(sed 's/[^a-zA-Z0-9]\+/-/g' <<< "$CONTAINER_TAG")

if [ "$CONTAINER_TAG" = "main" ] || [ "$CONTAINER_TAG" = "master" ] ; then
  CONTAINER_TAG="latest"
fi

metadata_changed() {
  tag="$1"

  metadata_diff=$(container-diff diff --json --type metadata remote://"$tag" daemon://"$tag" 2> /dev/null || true)
  if [ -n "$metadata_diff" ] ; then
    metadata_diff=$(jq '.[0].Diff.Adds + .[0].Diff.Dels' <<< "$metadata_diff")
    if [ "$metadata_diff" = "[]" ] ; then
      return 1
    fi
  fi

  return 0
}

files_changed() {
  tag="$1"

  file_diff=$(container-diff diff --json --type file remote://"$tag" daemon://"$tag" 2> /dev/null || true)
  if [ -n "$file_diff" ] ; then
    file_diff=$(jq '.[0].Diff.Adds + .[0].Diff.Dels + .[0].Diff.Mods' <<< "$file_diff")
    if [ "$file_diff" = "[]" ] ; then
      return 1
    fi
  fi

  return 0
}

maybe_push() {
  tag="$1"

  if metadata_changed "$tag" || files_changed "$tag" ; then
    docker push "$tag"
  else
    echo "INFO: $tag is unchanged, skipping push" >&2
  fi
}

buildx_argv=(
  --pull
  --platform "$PLATFORMS"
  --load
  --cache-from "${CONTAINER_REGISTRY}/${CONTAINER_NAME}:${CONTAINER_TAG}.cache"
  --cache-from "${CONTAINER_REGISTRY}/${CONTAINER_NAME}:latest.cache"
)

if [ -n "${EXTRA_BUILD_ARGS:-}" ] ; then
  readarray -t -d '' extra_build_args < <(xargs printf '%s\0' <<< "$EXTRA_BUILD_ARGS")
  buildx_argv+=("${extra_build_args[@]}")
fi

if [ -n "${REGISTRY_USERNAME:-}" ] && [ -n "${REGISTRY_PASSWORD:-}" ] ; then
  docker login "$CONTAINER_REGISTRY" --username "$REGISTRY_USERNAME" --password-stdin <<< "$REGISTRY_PASSWORD"
fi

#for tag in latest "$CONTAINER_TAG" ; do
#  cache_from="${CONTAINER_NAME}:${tag}.cache"
#  if docker pull --quiet "$cache_from" 2> /dev/null ; then
#    echo "INFO: using cache from $cache_from" >&2
#    buildx_argv+=(--cache_from "$cache_from")
#  else
#    echo "INFO: $cache_from not in registry" >&2
#  fi
#done

if [ "$BUILDXY_MODE" = "push" ] ; then
  buildx_argv+=(--cache-to "type=registry,ref=${CONTAINER_REGISTRY}/${CONTAINER_NAME}:${CONTAINER_TAG}.cache,mode=max")
fi

docker buildx create --name "buildxy-$$" \
  --driver docker-container \
  --buildkitd-flags "--allow-insecure-entitlement security.insecure --allow-insecure-entitlement network.host" \
  --use > /dev/null

cleanup_builder() {
  docker buildx rm "buildxy-$$"
}

trap cleanup_builder EXIT


docker buildx build \
  --tag "${CONTAINER_REGISTRY}/${CONTAINER_NAME}:${CONTAINER_TAG}" \
  "${buildx_argv[@]}" "$@" .

if [ "$BUILDXY_MODE" = "push" ] ; then
  maybe_push "${CONTAINER_REGISTRY}/${CONTAINER_NAME}:${CONTAINER_TAG}"
fi
