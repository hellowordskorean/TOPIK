import json
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', encoding='utf-8') as f:
    data7 = json.load(f)
R = {}

R["rigorous"] = [
    {"situation": "학술 연구 및 방법론 평가", "en": "The journal accepted the paper after its methodology was judged to be rigorous and replicable.", "ko": "그 학술지는 방법론이 엄격하고 재현 가능하다고 판단된 후 논문을 수락했다."},
    {"situation": "법률 심사 및 헌법 검토", "en": "Courts apply rigorous scrutiny to laws that restrict fundamental rights, requiring a compelling justification.", "ko": "법원은 기본권을 제한하는 법률에 엄격한 심사를 적용하여 설득력 있는 정당화를 요구한다."},
    {"situation": "의약품 승인 및 임상 시험 기준", "en": "Rigorous clinical trials are essential before any new medication is approved for widespread use.", "ko": "모든 신약이 광범위한 사용에 승인되기 전에 엄격한 임상 시험이 필수적이다."},
    {"situation": "건설 공학 및 안전 기준", "en": "Rigorous structural testing ensures that buildings can withstand seismic activity in earthquake-prone zones.", "ko": "엄격한 구조 테스트는 지진이 잦은 지역에서 건물이 지진 활동을 견딜 수 있도록 보장한다."},
    {"situation": "교육 시스템 및 성취 기준", "en": "A rigorous academic curriculum challenges students to think critically and develop advanced analytical skills.", "ko": "엄격한 학업 교육과정은 학생들이 비판적으로 생각하고 고급 분석 능력을 개발하도록 도전시킨다."},
    {"situation": "기업 감사 및 재무 통제", "en": "Rigorous internal controls are central to preventing financial misstatement and detecting fraud at an early stage.", "ko": "엄격한 내부 통제는 재무 오류를 방지하고 초기 단계에서 사기를 탐지하는 데 핵심적이다."},
    {"situation": "스포츠 훈련 및 체력 프로그램", "en": "Elite athletes undergo rigorous physical conditioning programmes designed to maximise performance during competition.", "ko": "엘리트 선수들은 경기 중 성과를 극대화하도록 설계된 엄격한 체력 단련 프로그램을 거친다."},
    {"situation": "이민 심사 및 신원 조사", "en": "Applicants for sensitive government positions undergo rigorous background checks, including financial and security vetting.", "ko": "민감한 정부 직위 지원자들은 재정 및 보안 심사를 포함한 엄격한 신원 조사를 거친다."},
    {"situation": "환경 평가 및 인허가 절차", "en": "A rigorous environmental impact assessment is mandatory before any major infrastructure project can receive approval.", "ko": "주요 인프라 프로젝트가 승인을 받기 전에 엄격한 환경 영향 평가가 의무적이다."},
    {"situation": "소프트웨어 개발 및 코드 테스트", "en": "Rigorous software testing before deployment reduces the risk of system failures in critical applications.", "ko": "배포 전 엄격한 소프트웨어 테스트는 중요한 애플리케이션에서 시스템 장애의 위험을 줄인다."}
]

R["salient"] = [
    {"situation": "IELTS 에세이 작성 및 논증 선택", "en": "Candidates should identify the most salient points from the graph data rather than attempting to describe everything.", "ko": "수험생들은 모든 것을 묘사하려 하기보다 그래프 데이터에서 가장 두드러진 점들을 파악해야 한다."},
    {"situation": "학술 연구 및 발견 발표", "en": "The research paper highlighted the most salient findings in the abstract to allow readers to assess its relevance.", "ko": "그 연구 논문은 독자들이 관련성을 평가할 수 있도록 초록에서 가장 두드러진 발견들을 강조했다."},
    {"situation": "법정 변론 및 논점 정리", "en": "Counsel was instructed to focus on the most salient legal issues rather than raise every possible argument.", "ko": "변호인은 모든 가능한 주장을 제기하기보다 가장 핵심적인 법적 쟁점에 집중하도록 지시받았다."},
    {"situation": "마케팅 및 소비자 의사결정", "en": "Research into consumer behaviour shows that price and brand reputation are the most salient factors in purchasing decisions.", "ko": "소비자 행동 연구에 따르면 가격과 브랜드 평판이 구매 결정에서 가장 두드러진 요소이다."},
    {"situation": "정책 브리핑 및 의사결정 지원", "en": "A policy briefing should present the most salient evidence concisely, enabling ministers to take informed decisions.", "ko": "정책 브리핑은 장관들이 정보에 입각한 결정을 내릴 수 있도록 가장 두드러진 증거를 간결하게 제시해야 한다."},
    {"situation": "심리학 및 기억 연구", "en": "Emotionally charged events tend to be more salient in memory than routine occurrences.", "ko": "감정적으로 강렬한 사건들은 일상적인 사건들보다 기억에 더 두드러지는 경향이 있다."},
    {"situation": "경제 분석 및 위기 원인 진단", "en": "The report identified three salient factors that had contributed to the financial crisis: leverage, opacity, and regulatory failure.", "ko": "보고서는 금융 위기에 기여한 세 가지 두드러진 요소를 확인했다: 레버리지, 불투명성, 규제 실패."},
    {"situation": "언론 보도 및 뉴스 가치 판단", "en": "Editors must judge which facts are most salient to their readership when deciding how to frame a story.", "ko": "편집자들은 기사를 어떻게 구성할지 결정할 때 독자들에게 가장 두드러진 사실이 무엇인지 판단해야 한다."},
    {"situation": "과학 데이터 시각화 및 발표", "en": "Effective data visualisation highlights the most salient trends while filtering out background noise.", "ko": "효과적인 데이터 시각화는 배경 잡음을 걸러내면서 가장 두드러진 추세를 강조한다."},
    {"situation": "조직 경영 및 전략 계획", "en": "The strategy review identified the most salient competitive threats facing the organisation over the next five years.", "ko": "전략 검토는 향후 5년간 조직이 직면하는 가장 두드러진 경쟁 위협을 파악했다."}
]

R["solvent"] = [
    {"situation": "기업 재정 및 지급 능력 평가", "en": "The creditors needed assurance that the company remained solvent before agreeing to extend additional credit.", "ko": "채권자들은 추가 신용 연장에 동의하기 전에 회사가 지급 능력을 유지하고 있다는 확신이 필요했다."},
    {"situation": "화학 및 용매 특성 활용", "en": "Acetone is widely used as a solvent in industrial cleaning processes due to its ability to dissolve organic compounds.", "ko": "아세톤은 유기 화합물을 용해하는 능력으로 인해 산업용 세척 공정에서 용매로 널리 사용된다."},
    {"situation": "공공 연금 및 재정 건전성", "en": "The pension scheme remained solvent due to conservative investment strategies and timely government contributions.", "ko": "연금 제도는 보수적인 투자 전략과 시기 적절한 정부 기여금 덕분에 지급 능력을 유지했다."},
    {"situation": "보험 산업 및 건전성 규제", "en": "Insurance companies are required to demonstrate that they are solvent under a range of stress scenarios.", "ko": "보험 회사들은 다양한 스트레스 시나리오 하에서 지급 능력이 있음을 입증해야 한다."},
    {"situation": "인쇄 및 잉크 제조 공정", "en": "The formulation of printing inks requires carefully selected solvents to achieve the correct viscosity and drying time.", "ko": "인쇄 잉크의 배합은 올바른 점도와 건조 시간을 달성하기 위해 신중하게 선택된 용매를 필요로 한다."},
    {"situation": "은행 규제 및 예금자 보호", "en": "Deposit guarantee schemes are triggered only when a bank is no longer solvent and cannot meet withdrawal demands.", "ko": "예금 보증 제도는 은행이 더 이상 지급 능력이 없고 인출 요구를 충족할 수 없을 때만 발동된다."},
    {"situation": "환경 과학 및 오염 물질", "en": "Many industrial solvents are classified as hazardous substances requiring controlled disposal to prevent groundwater contamination.", "ko": "많은 산업용 용매는 지하수 오염을 방지하기 위해 통제된 처리가 필요한 위험 물질로 분류된다."},
    {"situation": "도산법 및 이사 의무", "en": "A company must not incur new debts when its directors have reason to believe it is no longer solvent.", "ko": "이사들이 회사가 더 이상 지급 능력이 없다고 믿을 이유가 있을 때 회사는 새로운 부채를 발생시켜서는 안 된다."},
    {"situation": "부동산 개발 및 자금 조달", "en": "Lenders require property developers to demonstrate they are financially solvent before releasing construction funds.", "ko": "대출 기관은 건설 자금을 방출하기 전에 부동산 개발업자가 재정적으로 지급 능력이 있음을 증명하도록 요구한다."},
    {"situation": "국가 부채 및 국제 금융 위기", "en": "Despite austerity measures, investors doubted whether the government would remain solvent without external assistance.", "ko": "긴축 조치에도 불구하고 투자자들은 외부 지원 없이 정부가 지급 능력을 유지할 수 있을지 의심했다."}
]

R["sophisticated"] = [
    {"situation": "금융 상품 및 투자 전략", "en": "Sophisticated investors are permitted by regulators to participate in high-risk products not available to the general public.", "ko": "정교한 투자자들은 규제 당국에 의해 일반 대중이 이용할 수 없는 고위험 상품에 참여하도록 허용된다."},
    {"situation": "기술 개발 및 인공지능 시스템", "en": "Modern language models are remarkably sophisticated, capable of generating coherent text across diverse topics.", "ko": "현대의 언어 모델들은 다양한 주제에 걸쳐 일관성 있는 텍스트를 생성할 수 있는 놀랍도록 정교한 시스템이다."},
    {"situation": "의학 진단 기술 및 영상 장비", "en": "Sophisticated imaging technology allows physicians to detect tumours at far earlier stages than was previously possible.", "ko": "정교한 영상 기술은 의사들이 이전에 가능했던 것보다 훨씬 이른 단계에서 종양을 탐지할 수 있게 한다."},
    {"situation": "법적 논증 및 소송 전략", "en": "The case required sophisticated legal arguments drawing on constitutional law, treaty obligations, and human rights principles.", "ko": "그 사건은 헌법, 조약 의무, 인권 원칙을 활용하는 정교한 법률 논증을 필요로 했다."},
    {"situation": "사이버 공격 및 보안 위협", "en": "State-sponsored hackers deploy increasingly sophisticated malware capable of evading conventional security software.", "ko": "국가 지원 해커들은 기존 보안 소프트웨어를 피할 수 있는 점점 더 정교한 악성 소프트웨어를 배치한다."},
    {"situation": "경제 모델링 및 예측 분석", "en": "Sophisticated econometric models incorporate dozens of variables to forecast the impact of interest rate changes.", "ko": "정교한 계량 경제학 모델들은 금리 변화의 영향을 예측하기 위해 수십 개의 변수를 통합한다."},
    {"situation": "마케팅 전략 및 소비자 세분화", "en": "The campaign was designed for a sophisticated urban audience familiar with the brand's premium positioning.", "ko": "그 캠페인은 브랜드의 프리미엄 포지셔닝에 익숙한 정교한 도시 청중을 위해 설계되었다."},
    {"situation": "도시 인프라 및 스마트 시티", "en": "Sophisticated traffic management systems use real-time data to reduce congestion and emissions in major cities.", "ko": "정교한 교통 관리 시스템은 실시간 데이터를 사용하여 주요 도시의 혼잡과 배출을 줄인다."},
    {"situation": "회계 사기 및 기업 부정 행위", "en": "The fraud was so sophisticated that it eluded detection by both internal and external auditors for five years.", "ko": "그 사기는 너무나 정교해서 5년간 내부 및 외부 감사인 모두에게 발견되지 않았다."},
    {"situation": "학습 능력 및 고차원 사고", "en": "Sophisticated thinkers are able to hold contradictory positions simultaneously while evaluating their relative merits.", "ko": "정교한 사고가들은 상반되는 입장들의 상대적 장점을 평가하면서 동시에 그것들을 유지할 수 있다."}
]

R["strategic"] = [
    {"situation": "기업 계획 및 경쟁 우위", "en": "The board approved a strategic plan to expand into new markets over the next five years.", "ko": "이사회는 향후 5년에 걸쳐 새로운 시장으로 확장하는 전략 계획을 승인했다."},
    {"situation": "군사 안보 및 국방 계획", "en": "The defence ministry identified five strategic priorities to address evolving threats to national security.", "ko": "국방부는 국가 안보에 대한 진화하는 위협에 대응하기 위한 5가지 전략적 우선순위를 파악했다."},
    {"situation": "국제 외교 및 동맹 형성", "en": "The two nations formed a strategic partnership to coordinate trade policy and share intelligence resources.", "ko": "두 나라는 무역 정책을 조정하고 정보 자원을 공유하기 위한 전략적 파트너십을 형성했다."},
    {"situation": "교육 정책 및 인력 계획", "en": "A strategic investment in STEM education is essential to meet future labour market demands.", "ko": "미래 노동 시장 수요를 충족시키기 위해 STEM 교육에 대한 전략적 투자가 필수적이다."},
    {"situation": "환경 정책 및 탄소 중립 목표", "en": "Renewable energy has shifted from a niche concern to a strategic national priority in most developed countries.", "ko": "재생 에너지는 대부분의 선진국에서 틈새 관심사에서 전략적 국가 우선순위로 전환되었다."},
    {"situation": "공급망 관리 및 원자재 확보", "en": "Securing a reliable supply of critical minerals has become a strategic imperative for technology manufacturers.", "ko": "중요 광물의 안정적인 공급을 확보하는 것이 기술 제조업체들에게 전략적 필수 사항이 되었다."},
    {"situation": "인수합병 및 시너지 효과", "en": "The acquisition was described as strategic because it gave the company access to a complementary technology platform.", "ko": "그 인수는 회사에 보완적인 기술 플랫폼에 대한 접근을 제공했기 때문에 전략적이라고 묘사되었다."},
    {"situation": "도시 개발 및 토지 이용 계획", "en": "Locating the hospital on the outskirts was a strategic decision to ensure access for residents across the region.", "ko": "병원을 외곽에 위치시킨 것은 지역 전체 주민들의 접근성을 보장하기 위한 전략적 결정이었다."},
    {"situation": "인적자원 관리 및 리더십 개발", "en": "Investing in leadership development is a strategic priority for organisations facing succession challenges.", "ko": "리더십 개발에 투자하는 것은 승계 문제에 직면한 조직들의 전략적 우선순위이다."},
    {"situation": "비영리 단체 및 사회적 영향 측정", "en": "Strategic partnerships with the private sector enable non-profit organisations to scale their social impact programmes.", "ko": "민간 부문과의 전략적 파트너십은 비영리 단체들이 사회적 영향 프로그램을 확대할 수 있게 한다."}
]

R["suboptimal"] = [
    {"situation": "경제학 및 시장 실패", "en": "When externalities are ignored, market outcomes tend to be suboptimal from a social welfare perspective.", "ko": "외부 효과가 무시될 때, 시장 결과는 사회 복지 관점에서 최적이 아닌 경향이 있다."},
    {"situation": "의료 의사결정 및 치료 선택", "en": "Incomplete patient records can lead to suboptimal treatment decisions, particularly in emergency situations.", "ko": "불완전한 환자 기록은 특히 응급 상황에서 최적이 아닌 치료 결정으로 이어질 수 있다."},
    {"situation": "조직 경영 및 의사소통 문제", "en": "Poor cross-departmental communication resulted in suboptimal coordination of the product launch.", "ko": "부서 간 소통 미흡은 제품 출시의 최적이 아닌 조정으로 이어졌다."},
    {"situation": "알고리즘 최적화 및 컴퓨터 과학", "en": "The algorithm produced a suboptimal solution when applied to datasets containing missing values.", "ko": "그 알고리즘은 누락된 값을 포함하는 데이터셋에 적용될 때 최적이 아닌 해결책을 산출했다."},
    {"situation": "국제 협상 및 정책 타협", "en": "Analysts described the climate agreement as suboptimal but acknowledged it represented the best achievable consensus.", "ko": "분석가들은 기후 협약을 최적이 아닌 것으로 묘사했지만 달성 가능한 최선의 합의를 나타낸다고 인정했다."},
    {"situation": "교육 자원 배분 및 학교 성과", "en": "Schools in underfunded areas often produce suboptimal academic results due to staff shortages and inadequate facilities.", "ko": "자금이 부족한 지역의 학교들은 교직원 부족과 불충분한 시설로 인해 종종 최적이 아닌 학업 성과를 낸다."},
    {"situation": "공급망 관리 및 재고 최적화", "en": "Overstocking and stockouts are both signs of suboptimal inventory management within the supply chain.", "ko": "과잉 재고와 재고 부족은 모두 공급망 내 최적이 아닌 재고 관리의 신호이다."},
    {"situation": "도시 교통 및 대중교통 효율성", "en": "The fragmented ownership of bus and rail services led to suboptimal integration of the public transport network.", "ko": "버스 및 철도 서비스의 분산된 소유권은 대중교통 네트워크의 최적이 아닌 통합으로 이어졌다."},
    {"situation": "규제 정책 및 인센티브 설계", "en": "Badly designed incentives can produce suboptimal behaviours that undermine the goals of the regulatory framework.", "ko": "잘못 설계된 인센티브는 규제 틀의 목표를 훼손하는 최적이 아닌 행동을 야기할 수 있다."},
    {"situation": "팀 성과 및 협업 부재", "en": "Without clearly defined roles, teams often deliver suboptimal results due to duplicated effort and unclear accountability.", "ko": "명확하게 정의된 역할이 없으면 팀들은 중복된 노력과 불명확한 책임으로 인해 종종 최적이 아닌 결과를 낸다."}
]

count = 0
for w in data7['words']:
    if w['word'] in R:
        w['examples'] = R[w['word']]
        count += 1
print(f"Updated {count} words")
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', 'w', encoding='utf-8') as f:
    json.dump(data7, f, ensure_ascii=False, indent=2)
print("Saved ielts_7.json batch 8")
