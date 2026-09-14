"""Author's explicit question and full-text response readings, not a model judge."""

import json
from pathlib import Path


ROOT = Path('research_notes/analysis/orch_math_record_20260914_attempt1')
GOLD_REASONS = [
    '30*1.2*0.5=18 inches; successive percentages have different bases.',
    '600 men and1200 women leave200 of2000 participants.',
    '90 meal subtotal plus9 tax leaves140-99=41 gratuity.',
    'Jenny wins9 of10 Mark games and5 of20 Jill games:14.',
    '150 adoption+12*250 training+300 uncovered certification=3450.',
    '120 initial,72 after40percent sale,54 after selling quarter of72.',
    '(40*2-30)*.7+24=59.',
    '1800 sold at10 dollars yields18000 less15000 creditors=3000.',
    '42/.15*.2=56 tip.',
    '90000 downpayment/15000 annual savings=6 years.',
    '240 retained first round+160 second round=400.',
    '(150-50)*1.2=120 month-end balance.',
    'Four diners*12+2*6=60;60*1.2+5=77.',
    'Eight standard*5 plus4 special*6=64 minutes.',
    'Standard additive-volume abstraction:2 powder/(2+4*(16-4))=4percent.',
    '1500/.12=12500 principal.',
    '(8*18+2*27)*5=990 daily-shift overtime.',
    'Only one professional wage15/hour is specified;1260 assumes the second has equal wage. Under-specified, no admission.',
    'Seven hours/10minutes=42 sold pizzas use21kg;1kg left makes2.',
    '(64+76+91+80+89)/5=80.',
    'Initial2+2*4+3*3+2*.5=20 inches.',
    '30 outbound+.5hour*20mph=40 miles.',
    '1*(20+10)+2*(20+7)+3*(20+9)=171.',
    '35+36+9+35=115 miles from four segments.',
    '3*8+2*9+10*5=92.',
    '(220+110)/110=3hours with Red Deer between the cities.',
    '8*7.5*20*2=2400.',
    'Net fill1.6-.1=1.5;60/1.5=40 minutes.',
    'Monday10,Tuesday fixed2,Wednesday12 leave8hours for4 poodles.',
    '(15+46+33+30)*2=248 miles.',
    'Moving13hours*60=780;stationary break contributes zero.',
    'Conditional on the stated rumor:6needed-4normal=2inches;24hours/year=2/month. Not a factual biological assertion.',
    '60 berries minus20 rotten leaves40; half kept,20 sold.',
    'Emily16,Melissa8,Debora20,total44.',
    '(5*1+5*3)/2=10 kept.',
    'Gold6 is wrong:lemon12 leaves18;mango6 leaves12 orange. Preserve gold6 oracle but exclude all targets.',
    'NY2000,CA1000,TX600,total3600; hypothetical dataset quantities only.',
    '150points/5=30 qualifies10000; ordinal routing not conceptual fraction reasoning.',
    '6+8-2+12=24inches=2feet; melt2 is total over2days.',
    '48-12-6=30donuts.',
    '5*94-(90+98+92+94)=96.',
    'Half of9minus half of3=3dollars incremental cost.',
    'Biology100split into4ratio units:25boys.',
    '54-30=24group sandwiches/4=6requesters;double gives12customers.',
    '36present;onequarter outside classroom=9canteen.',
    'Half60income=30saved/month;150/30=5months.',
    '(22-6)*1.5=24cans.',
    '21*(1-1/3)=14; fraction consumed jointly by two birds.',
    'Printing17.5+pens10.5=28;40-28=12change.',
    '(3*.5+2)*8=28.',
    'Threehalvings make8pieces/sheet;5*8/10=4days.',
    'Capital5/.2=25eggs sold;30-25=5left.',
    '50cakes-12=38;2cans/cake=76. Name/pronoun drift does not alter explicitly remaining cakes.',
    '3*14+5*7=77hours.',
    '1dog+4cats+8rabbits+24hares=37.',
    '3pieces/day*72days/8pieces=27pies.',
    'Pairs7oz each;7pairs/bag*3bags*4oz/apple=84oz apples.',
    '155250/1000*100=15525.',
    '72*7/84=6 full-bottle equivalents.',
    '32-15=17given;Lea12 vsMae5,difference7.',
    '1200/(3*40)=10bags.',
    '120initial-7*(8+6)=22pens+pencils.',
    'Reading40 as collective teammates points/game:(20+40)*5=300; not an individual teammate score.',
    '14*450+5*120+200=7100.',
]


def gold_review():
    tasks = json.loads((ROOT / 'TASKS.json').read_text())['tasks']
    assert len(tasks) == len(GOLD_REASONS) == 64
    decisions = {}
    for position, (task, reason) in enumerate(zip(tasks, GOLD_REASONS)):
        status = 'AMBIGUOUS' if position == 17 else 'SUSPECT' if position == 35 else 'VALID'
        decisions[task['id']] = dict(question_sha256=task['question_sha256'], status=status,
                                     reason=reason, reviewer='MATH-RECORD author question-only arithmetic reading')
    (ROOT / 'GOLD_REVIEW.json').write_text(json.dumps(decisions, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    gold_review()
