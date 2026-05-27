#!/bin/bash 

endpoint_base="http://192.168.40.1"

get_svc_port () {
  echo $(kubectl get svc -n $1 | grep app | awk -F: '{print $2}' | grep -oE '3[0-9]{4}')
}

# kubectl get svc -n paper | grep app | awk -F: '{print $2}' | grep -o '3[0-9]\+'

result=$(get_svc_port "paper")
echo $result
export PAPER_ENDPOINT="$endpoint_base:$result"

result=$(get_svc_port "author")
echo $result
export AUTHOR_ENDPOINT="$endpoint_base:$result"

result=$(get_svc_port "thumbnail")
echo $result
export THUMBNAIL_ENDPOINT="$endpoint_base:$result"

result=$(get_svc_port "fulltext")
echo $result
export FULLTEXT_ENDPOINT="$endpoint_base:$result"
