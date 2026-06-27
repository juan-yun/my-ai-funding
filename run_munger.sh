source .env


corp_str=$(grep match logs/below20_tickers.log | awk -F: '{print $7}' | awk -F= '{print $2}' | awk -F, '{print $1}'|tr -d '"'|tr -d "'")
mapfile -t corp_list <<< "$corp_str"

max_parallel=4 # 最大并发20个
running=0

for corp in "${corp_list[@]}"; do
    # 如果当前运行任务达到上限，等待任意一个任务结束
    if [[ $running -ge $max_parallel ]]; then
        wait -n
        running=$((running - 1))
    fi
    sleep $(awk 'BEGIN{print rand()*10}')
    echo "now start to analysis $corp financial data"
    nohup python src/main.py --tickers "$corp" --initial-cash 10000 --show-agent-graph --analysts charlie_munger --model Qwen/Qwen2.5-72B-Instruct --show-reasoning --start-date 2026-01-01 --end-date 2026-06-27 1>logs_0627/$corp.log 2>&1 &

    running=$((running + 1))
done

wait
echo "all tasks done"
