
source .env
corp_list=(
"MMM"
#"NOK" 
#"F" 
#"ERIC" 
#"AMD"
) #"GOOGL" "AAPL")

# 遍历数组的所有元素
for corp in "${corp_list[@]}"; do
    echo "now start to analysis $corp financial data"
    nohup python src/main.py --tickers $corp --initial-cash 1000 --show-agent-graph --analysts charlie_munger --model Qwen/Qwen2.5-72B-Instruct --show-reasoning --start_date 2026-01-01 --end_date 2026_06_27 1>logs/$corp.log 2>&1 &
done

#nohup python src/main.py --tickers NOK --initial-cash 1000 --show-agent-graph --analysts charlie_munger --model Qwen/Qwen2.5-72B-Instruct --show-reasoning 1>logs/NOK .log 2>&1 &
#
