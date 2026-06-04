
source .env

python src/main.py --tickers AAPL,MSFT,NVDA,GOOGL,TLSA --initial-cash 1000 --show-agent-graph --analysts charlie_munger --model DeepSeekR1  --show-reasoning


#python src/main.py --tickers AAPL --initial-cash 1000 --analysts charlie_munger --model DeepSeekR1  --show-reasoning --show-agent-graph --show-reasoning
#
#python src/main.py --tickers MSFT --initial-cash 1000 --analysts charlie_munger --model DeepSeekR1  --show-reasoning --show-agent-graph --show-reasoning
#
#python src/main.py --tickers GOOGL --initial-cash 1000 --analysts charlie_munger --model DeepSeekR1  --show-reasoning --show-agent-graph --show-reasoning
#
#python src/main.py --tickers TLSA --initial-cash 1000 --analysts charlie_munger --model DeepSeekR1  --show-reasoning --show-agent-graph --show-reasoning
#
#python src/main.py --tickers NVDA --initial-cash 1000 --analysts charlie_munger --model DeepSeekR1  --show-reasoning --show-agent-graph  --show-reasoning
