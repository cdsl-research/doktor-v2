task_up() {
    DIRS=$(find . -type f -name main.py -maxdepth 2 | sed "s|/main.py||g")
    for dir in $DIRS
    do
        docker compose -f $dir/docker-compose.yml up -d --build
    done
}

task_down() {
    DIRS=$(find . -type f -name main.py -maxdepth 2 | sed "s|/main.py||g")
    for dir in $DIRS
    do
        docker compose -f $dir/docker-compose.yml down
    done
}

task_logging() {
    mkdir logs/ || true
    DIRS=$(find deploy/ -maxdepth 1 -mindepth 1 -type d | sed "s|deploy/||g")
    for dir in $DIRS
    do
        kubectl logs deploy/${dir}-app-deploy -c istio-proxy -n ${dir} | grep HTTP > logs/${dir}-deploy.log
    done
}
