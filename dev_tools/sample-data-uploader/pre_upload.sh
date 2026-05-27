#!/bin/bash 

get_svc_port () {
  echo $(kubectl get svc -n $1 | grep app | awk -F: '{print $2}' | grep -o '3[0-9]\+')
}

# kubectl get svc -n paper | grep app | awk -F: '{print $2}' | grep -o '3[0-9]\+'

result=$(get_svc_port "paper")
echo $result
export PAPER_ENDPOINT="http://d2124001-kube-2.a910.tak-cslab.org:$result"

result=$(get_svc_port "author")
echo $result
export AUTHOR_ENDPOINT="http://d2124001-kube-2.a910.tak-cslab.org:$result"

result=$(get_svc_port "thumbnail")
echo $result
export THUMBNAIL_ENDPOINT="http://d2124001-kube-2.a910.tak-cslab.org:$result"

result=$(get_svc_port "fulltext")
echo $result
export FULLTEXT_ENDPOINT="http://d2124001-kube-2.a910.tak-cslab.org:$result"
