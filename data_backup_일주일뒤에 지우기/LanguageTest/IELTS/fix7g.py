import json
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', encoding='utf-8') as f:
    data7 = json.load(f)
R = {}

R["redundant"] = [
    {"situation": "고용 및 정리해고", "en": "Over two thousand workers were made redundant when the automotive plant automated its assembly lines.", "ko": "자동차 공장이 조립 라인을 자동화하면서 2천 명 이상의 근로자가 해고되었다."},
    {"situation": "기술 시스템 및 중복 설계", "en": "Engineers built redundant power supplies into the server infrastructure to ensure uninterrupted operation.", "ko": "엔지니어들은 중단 없는 운영을 보장하기 위해 서버 인프라에 이중 전원 공급 장치를 구축했다."},
    {"situation": "언어학 및 담화 분석", "en": "Certain phrases in the draft report were identified as redundant and were removed to improve concision.", "ko": "초안 보고서의 특정 문구들이 중복된 것으로 파악되어 간결성을 향상시키기 위해 제거되었다."},
    {"situation": "IELTS 쓰기 및 에세이 편집", "en": "IELTS examiners penalise redundant phrases such as 'in my personal opinion' since 'in my opinion' already conveys the same meaning.", "ko": "IELTS 시험관들은 '제 개인적인 의견으로는'과 같은 중복 표현에 감점을 주는데, 이는 '제 의견으로는'이 이미 같은 의미를 전달하기 때문이다."},
    {"situation": "정보 기술 및 데이터 백업", "en": "A redundant backup system was installed to prevent data loss in the event of a primary server failure.", "ko": "주 서버 장애 시 데이터 손실을 방지하기 위해 이중 백업 시스템이 설치되었다."},
    {"situation": "법률 문서 및 중복 조항", "en": "The solicitor advised removing the redundant clause since it repeated the obligation already stated in section four.", "ko": "변호사는 4조에 이미 명시된 의무를 반복하는 중복 조항을 제거할 것을 권고했다."},
    {"situation": "조직 재구조화 및 역할 통합", "en": "Following the merger, several management positions were declared redundant due to overlapping responsibilities.", "ko": "합병 이후 책임이 중복되어 몇몇 관리직이 잉여 직위로 선언되었다."},
    {"situation": "항공우주 공학 및 안전 시스템", "en": "Commercial aircraft incorporate redundant hydraulic systems to maintain control even if one circuit fails.", "ko": "상업용 항공기는 하나의 회로가 고장나더라도 제어를 유지하기 위해 이중 유압 시스템을 탑재하고 있다."},
    {"situation": "소프트웨어 개발 및 코드 품질", "en": "Code reviews identified several redundant functions that had been duplicated across different modules of the application.", "ko": "코드 검토에서 애플리케이션의 여러 모듈에 걸쳐 중복된 여러 불필요한 함수가 발견되었다."},
    {"situation": "교육 정책 및 교육과정 개선", "en": "The curriculum review found several redundant units whose content was already fully covered in other modules.", "ko": "교육과정 검토에서 내용이 다른 모듈에서 이미 완전히 다루어진 여러 불필요한 단원이 발견되었다."}
]

R["regulatory"] = [
    {"situation": "금융 서비스 및 은행 감독", "en": "Banks must comply with strict regulatory capital requirements to maintain financial stability.", "ko": "은행들은 금융 안정성을 유지하기 위해 엄격한 규제 자본 요건을 준수해야 한다."},
    {"situation": "의약품 승인 및 임상 시험", "en": "The drug manufacturer submitted clinical trial data to satisfy the regulatory requirements for market authorisation.", "ko": "제약 회사는 시장 승인을 위한 규제 요건을 충족시키기 위해 임상 시험 데이터를 제출했다."},
    {"situation": "환경 보호 및 배출 기준", "en": "Companies that breach regulatory emission limits face substantial fines and potential suspension of operations.", "ko": "규제 배출 한도를 위반하는 회사들은 상당한 벌금과 운영 정지 가능성에 직면한다."},
    {"situation": "통신 산업 및 주파수 할당", "en": "Telecommunications companies must obtain regulatory approval before deploying new network infrastructure.", "ko": "통신 회사들은 새로운 네트워크 인프라를 배치하기 전에 규제 승인을 받아야 한다."},
    {"situation": "인수합병 및 경쟁 당국 심사", "en": "The merger was delayed by regulatory scrutiny from multiple competition authorities across three jurisdictions.", "ko": "합병은 세 관할권에 걸친 여러 경쟁 당국의 규제 심사로 인해 지연되었다."},
    {"situation": "데이터 보호 및 개인 정보 법규", "en": "Companies processing personal data of EU citizens must navigate a complex regulatory framework under GDPR.", "ko": "EU 시민의 개인 데이터를 처리하는 기업들은 GDPR에 따른 복잡한 규제 틀을 탐색해야 한다."},
    {"situation": "에너지 산업 및 전력 시장 규제", "en": "The electricity market underwent regulatory reform to introduce competition and reduce consumer bills.", "ko": "전력 시장은 경쟁을 도입하고 소비자 요금을 줄이기 위한 규제 개혁을 거쳤다."},
    {"situation": "식품 안전 및 위생 기준", "en": "Food producers must meet regulatory hygiene and labelling standards before their products can be legally sold.", "ko": "식품 생산자들은 제품을 합법적으로 판매하기 전에 규제 위생 및 표시 기준을 충족해야 한다."},
    {"situation": "항공 산업 및 안전 인증", "en": "Aircraft must pass rigorous regulatory certification before they are approved for commercial passenger service.", "ko": "항공기는 상업 여객 서비스에 승인되기 전에 엄격한 규제 인증을 통과해야 한다."},
    {"situation": "핀테크 및 디지털 금융 감독", "en": "Regulators worldwide are developing regulatory sandboxes to allow fintech firms to test products in a controlled environment.", "ko": "전 세계 규제 당국들은 핀테크 기업들이 통제된 환경에서 제품을 테스트할 수 있도록 규제 샌드박스를 개발하고 있다."}
]

R["residual"] = [
    {"situation": "법률 및 유산 상속", "en": "The residual estate was divided equally among the deceased's three children after all debts and legacies were settled.", "ko": "모든 부채와 유산이 처리된 후 잔여 재산은 고인의 세 자녀에게 균등하게 분배되었다."},
    {"situation": "환경 공학 및 오염 처리", "en": "Even after extensive remediation, some residual contamination remained in the soil around the former industrial site.", "ko": "광범위한 정화 작업 후에도 이전 산업 부지 주변 토양에 일부 잔여 오염이 남아 있었다."},
    {"situation": "의학 및 종양 치료 후 평가", "en": "Follow-up scans indicated residual tumour cells, requiring an additional course of targeted therapy.", "ko": "추적 스캔에서 잔여 종양 세포가 발견되어 추가 표적 치료가 필요했다."},
    {"situation": "통계학 및 회귀 분석", "en": "A plot of residual values helps statisticians assess whether a regression model has been correctly specified.", "ko": "잔차 값의 플롯은 통계학자들이 회귀 모델이 올바르게 설정되었는지 평가하는 데 도움이 된다."},
    {"situation": "보험 및 청구 처리 이후 잔여 가치", "en": "After the insurance payout, the policyholder retained residual ownership of the salvaged vehicle.", "ko": "보험금 지급 후 보험 계약자는 구조된 차량의 잔여 소유권을 보유했다."},
    {"situation": "연금 및 투자 펀드 구조", "en": "Residual income from the investment portfolio supplemented the pensioner's state benefit.", "ko": "투자 포트폴리오에서 나오는 잔여 수입은 연금 수급자의 국가 급여를 보완했다."},
    {"situation": "건설 프로젝트 및 계약 청산", "en": "The contractor's residual liability for defects persisted for six years after the project was completed.", "ko": "결함에 대한 계약자의 잔여 책임은 프로젝트가 완료된 후 6년간 지속되었다."},
    {"situation": "화학 공정 및 폐기물 처리", "en": "Strict protocols govern the safe disposal of residual chemical compounds following pharmaceutical manufacturing.", "ko": "엄격한 프로토콜이 의약품 제조 후 잔여 화학 화합물의 안전한 폐기를 규제한다."},
    {"situation": "정치학 및 사회 변화", "en": "A residual distrust of government institutions persisted among communities that had experienced historical injustice.", "ko": "역사적 불의를 경험한 지역사회에서는 정부 기관에 대한 잔여적 불신이 지속되었다."},
    {"situation": "기업 청산 및 채권자 우선순위", "en": "In liquidation, residual assets are distributed to ordinary shareholders only after all creditors have been repaid.", "ko": "청산 시 잔여 자산은 모든 채권자에게 상환된 후에만 일반 주주에게 분배된다."}
]

R["resilient"] = [
    {"situation": "경제 시스템 및 위기 대응력", "en": "Diversified economies tend to be more resilient to global shocks than those dependent on a single export commodity.", "ko": "다각화된 경제는 단일 수출 상품에 의존하는 경제보다 세계적인 충격에 더 탄력적인 경향이 있다."},
    {"situation": "심리학 및 스트레스 대처 능력", "en": "Resilient individuals are able to draw on internal resources and social support to recover from adversity.", "ko": "탄력적인 개인들은 역경에서 회복하기 위해 내부 자원과 사회적 지원을 활용할 수 있다."},
    {"situation": "생태학 및 환경 복원력", "en": "Ecologists study how resilient ecosystems recover their structure and function after disturbances such as wildfire.", "ko": "생태학자들은 탄력적인 생태계가 산불과 같은 교란 후에 어떻게 구조와 기능을 회복하는지를 연구한다."},
    {"situation": "인프라 개발 및 자연재해 대비", "en": "Engineers designed a resilient water supply network capable of withstanding major flooding events.", "ko": "엔지니어들은 주요 홍수 사태를 견딜 수 있는 탄력적인 급수 네트워크를 설계했다."},
    {"situation": "금융 시스템 및 은행 안정성", "en": "Stress tests are designed to verify that banks remain resilient under simulated adverse economic conditions.", "ko": "스트레스 테스트는 은행들이 모의 악조건 경제 상황에서도 탄력적으로 유지되는지 검증하기 위해 설계되었다."},
    {"situation": "기업 경영 및 공급망 충격", "en": "Companies that built resilient supply chains weathered the pandemic disruption far better than those that had not.", "ko": "탄력적인 공급망을 구축한 기업들은 그렇지 않은 기업들보다 팬데믹 혼란을 훨씬 잘 견뎌냈다."},
    {"situation": "도시 계획 및 기후 적응", "en": "Resilient city planning incorporates green infrastructure and flood defences to adapt to changing weather patterns.", "ko": "탄력적인 도시 계획은 변화하는 기상 패턴에 적응하기 위해 녹색 인프라와 홍수 방어를 통합한다."},
    {"situation": "교육 및 학습 어려움 극복", "en": "Resilient learners persist despite setbacks, viewing mistakes as opportunities for growth rather than failure.", "ko": "탄력적인 학습자들은 좌절에도 불구하고 지속하며, 실수를 실패가 아닌 성장의 기회로 본다."},
    {"situation": "사이버 보안 및 시스템 복구 능력", "en": "Organisations must build resilient IT architectures that can recover rapidly from cyber attacks or system failures.", "ko": "조직들은 사이버 공격이나 시스템 장애로부터 신속하게 복구할 수 있는 탄력적인 IT 아키텍처를 구축해야 한다."},
    {"situation": "공동체 개발 및 지역 사회 역량", "en": "Community resilience programmes focus on strengthening local capacity to manage emergencies without external support.", "ko": "지역사회 회복력 프로그램은 외부 지원 없이 긴급 상황을 관리하기 위한 지역 역량 강화에 초점을 맞춘다."}
]

R["retrospective"] = [
    {"situation": "법률 및 소급 적용 금지 원칙", "en": "The principle against retrospective legislation protects individuals from being penalised under laws that did not exist when they acted.", "ko": "소급 입법에 반대하는 원칙은 개인이 자신이 행동했을 때 존재하지 않았던 법률에 따라 처벌받는 것을 보호한다."},
    {"situation": "의학 연구 및 코호트 연구 설계", "en": "A retrospective study analysed the medical records of patients treated over the previous ten years.", "ko": "소급 연구는 지난 10년간 치료를 받은 환자들의 의료 기록을 분석했다."},
    {"situation": "경영 평가 및 프로젝트 검토", "en": "A retrospective review of the project identified avoidable delays caused by insufficient stakeholder communication.", "ko": "프로젝트에 대한 소급 검토에서 불충분한 이해관계자 소통으로 인한 예방 가능한 지연이 확인되었다."},
    {"situation": "세금 및 세무 조사", "en": "The tax authority issued a retrospective assessment covering income that had not been declared for three previous years.", "ko": "세무 당국은 이전 3년간 신고되지 않은 소득을 포함한 소급 세금 평가를 발부했다."},
    {"situation": "예술 및 경력 조망 전시", "en": "The gallery mounted a retrospective exhibition celebrating the artist's six-decade career.", "ko": "갤러리는 예술가의 60년 경력을 기념하는 회고 전시회를 개최했다."},
    {"situation": "보험 청구 및 보장 범위 소급", "en": "The policy provided retrospective cover for incidents that had occurred before the renewal date.", "ko": "그 보험 정책은 갱신일 이전에 발생한 사건에 대한 소급 보장을 제공했다."},
    {"situation": "회계 기준 및 재무제표 수정", "en": "A change in accounting policy must be applied retrospectively by restating prior-period financial statements.", "ko": "회계 정책의 변경은 이전 기간 재무제표를 수정함으로써 소급 적용해야 한다."},
    {"situation": "복지 정책 및 급여 지급 소급", "en": "The court ordered retrospective payment of benefits that had been wrongfully withheld for two years.", "ko": "법원은 2년간 부당하게 보류된 급여의 소급 지급을 명령했다."},
    {"situation": "형사 사법 및 사면 제도", "en": "A retrospective pardon was granted to individuals convicted under a law that was subsequently found to be unconstitutional.", "ko": "이후 위헌으로 판명된 법률에 따라 유죄 판결을 받은 개인들에게 소급 사면이 부여되었다."},
    {"situation": "교육 성취도 분석 및 학습 평가", "en": "A retrospective analysis of student performance data revealed a strong correlation between attendance and final grades.", "ko": "학생 성과 데이터에 대한 소급 분석은 출석률과 최종 성적 사이의 강한 상관관계를 밝혔다."}
]

count = 0
for w in data7['words']:
    if w['word'] in R:
        w['examples'] = R[w['word']]
        count += 1
print(f"Updated {count} words")
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', 'w', encoding='utf-8') as f:
    json.dump(data7, f, ensure_ascii=False, indent=2)
print("Saved ielts_7.json batch 7")
