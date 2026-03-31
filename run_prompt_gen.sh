#!/bin/bash
# 전체 프롬프트 생성 러너 - 백그라운드 실행용
# 사용법: bash run_prompt_gen.sh
# 또는:   bash run_prompt_gen.sh > data/prompt_gen_full.log 2>&1 &

set -e
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  전체 프롬프트 생성 시작"
echo "  $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 전체 한번에 실행 (이미 완성된 건 자동 스킵)
python3 generate_prompts.py --start 1 --end 1800 --batch-save 10 --max-fix-rounds 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  전체 완료!"
echo "  $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
