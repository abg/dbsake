#!/bin/bash

## This script will upload files to a rackspace cloud files container.
## Credentials should be placed in ~/.rscloud and sourced by this script.

authenticate() {
    local user=$1
    local apikey=$2
    local payload="
    {
        \"auth\": {
            \"RAX-KSKEY:apiKeyCredentials\": {
                \"username\": \"$user\",
                \"apiKey\": \"$apikey\"
            }
        }
    }"
    jq '.' <<<"${payload}" | \
    curl -s \
         -X POST \
         -H "Content-type: application/json" \
         -d @- \
         "${auth_url}"
}

service_url() {
    local region=$1
    local name=$2
    jq -r ".access.serviceCatalog[] | 
           select(.type == \"${name}\").endpoints[] |
           select(.region == \"${region}\").publicURL" <<< "${registry}"
}

upload() {
    local path=$1
    local mimetype=$(file -bi "${path}")
    local rpath="${path#./}"
    local cpath=$(readlink -f ${path})
    local url="${cfurl}/${container}/${rpath}"
    echo "${url} [${mimetype}]"
    local config="
    request = PUT
    upload-file = \"${cpath}\"
    header = \"X-Auth-Token: ${token}\"
    header = \"Content-Type: ${mimetype}\"
    header = \"Cache-Control: public, max-age=900\"
    url = \"${url}\""
    curl -s -K - <<< "${config}"
}

user=unknown
apikey=unknown
path=$1
container=${2:-get.dbsake.net}
auth_url="https://identity.api.rackspacecloud.com/v2.0/tokens"

[ -e ~/.rscloud ] && . ~/.rscloud

registry=$(authenticate "$user" "$apikey")
echo "Authenticated with user=$user"
token=$(jq -r '.access.token.id' <<< "$registry")
cfurl=$(service_url "IAD" 'object-store')
echo "Found Swift CDN endpoint (IAD): $cfurl"
parallelism=8

export token cfurl container
export -f upload

find "${path:-.}" -type f -print0 | \
    xargs -0 -I{} -n 1 -P "${parallelism:-1}" bash -c "upload '{}'"
