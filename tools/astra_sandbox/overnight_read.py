from pathlib import Path
import sys
jobs = {
 'support': [('organism_v6/reflection.py', [(1,55),(90,180)]), ('organism_v6/gym_backend.py',[(1,75)]), ('organism_v6/reasoning_gym_gym.py',[(1,65)]), ('organism_v6/agentic_parent.py',[(1,90)]), ('organism_v6/lora_svd_init.py',[(1,85)])],
 'scripts': [('gpu/write_ab.sh',[(1,100)]),('gpu/memory_dose.sh',[(1,100)]),('gpu/rg_band.sh',[(1,55)])],
 'memos': [('research_notes/astra_memos/2026-09-10_q1_memo.md',[(64,126)]),('research_notes/astra_memos/2026-09-11_q4_debate.md',[(23,85)]),('research_notes/astra_memos/2026-09-11_q7_paper_review.md',[(1,85)]),('research_notes/astra_memos/2026-09-11_q5_oneshot_design.md',[(107,130),(188,213),(255,290)])],
}
for path, spans in jobs[sys.argv[1]]:
 lines=Path(path).read_text().splitlines()
 print('\nFILE',path,'lines',len(lines))
 for start,end in spans:
  for i in range(start-1,min(end,len(lines))): print(f'{i+1}: {lines[i]}')
