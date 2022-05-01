task_up() {
    DIRS=$(find . -type f -name main.py -maxdepth 2 | sed "s|/main.py||g")
    for dir in $DIRS
    do
        docker-compose -f $dir/docker-compose.yml up -d
    done
}

task_down() {
    DIRS=$(find . -type f -name main.py -maxdepth 2 | sed "s|/main.py||g")
    for dir in $DIRS
    do
        docker-compose -f $dir/docker-compose.yml down
    done
}