import json

with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_6.json', encoding='utf-8') as f:
    data6 = json.load(f)

R = {}

R["fiscal"] = [
  {"situation":"예산 편성을 논의할 때","en":"The government announced a series of fiscal measures aimed at reducing the deficit without cutting frontline public services.","ko":"정부는 최전선 공공 서비스를 삭감하지 않으면서 재정 적자를 줄이기 위한 일련의 재정 조치를 발표했어요."},
  {"situation":"경제 정책을 분석할 때","en":"During a recession, expansionary fiscal policy -- increasing public spending and cutting taxes -- is typically used to stimulate demand.","ko":"경기 침체 시 공공 지출 증가와 세금 인하를 포함하는 확장적 재정 정책이 수요 진작에 일반적으로 사용돼요."},
  {"situation":"기업 회계연도를 설명할 때","en":"The company's fiscal year ends on 31 March, which means its annual results are released several months after those of competitors with a December year-end.","ko":"회사의 회계연도는 3월 31일에 종료되므로 12월 결산 경쟁사보다 몇 달 늦게 연간 실적을 발표해요."},
  {"situation":"국가 부채를 논의할 때","en":"Persistent fiscal deficits have left the country with a debt-to-GDP ratio that exceeds the threshold recommended by international financial institutions.","ko":"지속적인 재정 적자로 인해 국가의 GDP 대비 부채 비율이 국제 금융 기관이 권고하는 임계값을 초과했어요."},
  {"situation":"조세 정책을 논의할 때","en":"Critics argued that the proposed tax cuts were fiscally irresponsible, adding billions to the deficit without a credible plan for offsetting revenues.","ko":"비평가들은 제안된 세금 감면이 상쇄 수익에 대한 신뢰할 수 있는 계획 없이 수십억 달러를 적자에 추가하는 재정적으로 무책임한 조치라고 주장했어요."},
  {"situation":"지방 정부 재정을 논의할 때","en":"The municipal government faced a fiscal crisis after property tax revenues collapsed following the departure of its largest industrial employer.","ko":"지방 정부는 최대 산업 고용주가 떠난 후 재산세 수입이 급감하면서 재정 위기에 직면했어요."},
  {"situation":"국제 원조를 논의할 때","en":"The IMF conditioned its emergency loan on the recipient government adopting a credible fiscal consolidation programme within six months.","ko":"IMF는 수원국 정부가 6개월 이내에 신뢰할 수 있는 재정 건전화 프로그램을 채택하는 것을 긴급 대출의 조건으로 내세웠어요."},
  {"situation":"기업 재무 계획을 논의할 때","en":"The CFO warned that without tighter fiscal discipline at the divisional level, the group would struggle to meet its debt covenants.","ko":"CFO는 사업부 차원에서 더 엄격한 재정 규율 없이는 그룹이 채무 서약을 이행하기 어려울 것이라고 경고했어요."},
  {"situation":"연금 개혁을 논의할 때","en":"The ageing population presents a significant fiscal challenge, as a shrinking workforce must support an ever-growing number of retirees.","ko":"노령화 인구는 점점 줄어드는 노동력이 계속 늘어나는 은퇴자를 부양해야 한다는 점에서 상당한 재정적 도전을 제시해요."},
  {"situation":"의회 예산 심의를 설명할 때","en":"The fiscal committee approved the budget only after the finance minister agreed to cap discretionary spending at three percent of GDP.","ko":"재정위원회는 재무장관이 재량 지출을 GDP의 3%로 제한하기로 합의한 후에야 예산을 승인했어요."}
]

R["holistic"] = [
  {"situation":"의료 접근법을 논의할 때","en":"A holistic approach to patient care addresses not only the physical symptoms but also the psychological and social factors that affect recovery.","ko":"환자 치료에 대한 전체론적 접근 방식은 신체적 증상뿐만 아니라 회복에 영향을 미치는 심리적, 사회적 요소도 다루어요."},
  {"situation":"교육 철학을 논의할 때","en":"Progressive educators argue that schools should adopt a holistic curriculum that develops critical thinking, emotional intelligence, and civic responsibility alongside academic subjects.","ko":"진보적 교육자들은 학교가 학문 과목과 함께 비판적 사고, 정서 지능, 시민 책임을 개발하는 전체론적 교육과정을 채택해야 한다고 주장해요."},
  {"situation":"도시 계획을 논의할 때","en":"The city's regeneration plan takes a holistic view of urban development, integrating housing, transport, green space, and community facilities in a single masterplan.","ko":"도시 재생 계획은 주거, 교통, 녹지 공간, 지역 사회 시설을 하나의 마스터플랜에 통합하는 도시 개발에 대한 전체론적 시각을 취해요."},
  {"situation":"환경 정책을 논의할 때","en":"Managing biodiversity loss requires a holistic strategy that addresses habitat destruction, pollution, invasive species, and climate change simultaneously.","ko":"생물 다양성 손실을 관리하려면 서식지 파괴, 오염, 침입종, 기후 변화를 동시에 다루는 전체론적 전략이 필요해요."},
  {"situation":"기업 전략을 논의할 때","en":"The consultancy firm recommended a holistic transformation programme that would align the company's culture, processes, and technology around a single customer-centric vision.","ko":"컨설팅 회사는 회사의 문화, 프로세스, 기술을 단일 고객 중심 비전을 중심으로 정렬하는 전체론적 변환 프로그램을 권고했어요."},
  {"situation":"복지 정책을 논의할 때","en":"Social workers advocate for a holistic assessment of families in crisis, recognising that poverty, mental health, and domestic instability are deeply interconnected.","ko":"사회복지사들은 빈곤, 정신 건강, 가정 불안정이 깊이 연결되어 있음을 인식하며 위기 가족에 대한 전체론적 평가를 지지해요."},
  {"situation":"스포츠 코칭을 논의할 때","en":"Elite coaches take a holistic approach to athlete development, paying equal attention to nutrition, sleep, mental resilience, and technical skills.","ko":"엘리트 코치들은 영양, 수면, 정신적 탄력성, 기술적 기술에 동등한 주의를 기울이는 선수 개발에 대한 전체론적 접근 방식을 취해요."},
  {"situation":"경영 교육을 논의할 때","en":"Leading business schools increasingly emphasise holistic leadership, preparing graduates to navigate ethical dilemmas as well as financial challenges.","ko":"선도적인 비즈니스 스쿨들은 점점 더 전체론적 리더십을 강조하여 졸업생들이 재무적 도전뿐만 아니라 윤리적 딜레마도 헤쳐 나갈 수 있도록 준비시켜요."},
  {"situation":"정신 건강 치료를 논의할 때","en":"A holistic treatment plan for depression might combine medication, cognitive behavioural therapy, lifestyle changes, and peer support groups.","ko":"우울증에 대한 전체론적 치료 계획은 약물 치료, 인지행동 치료, 생활 방식 변화, 동료 지원 그룹을 결합할 수 있어요."},
  {"situation":"지속 가능성 전략을 논의할 때","en":"The company's holistic sustainability framework considers environmental impact, supply chain ethics, employee wellbeing, and community investment as equally important pillars.","ko":"회사의 전체론적 지속 가능성 프레임워크는 환경 영향, 공급망 윤리, 직원 복지, 지역 사회 투자를 동등하게 중요한 기둥으로 간주해요."}
]

R["incremental"] = [
  {"situation":"소프트웨어 개발을 논의할 때","en":"Rather than launching a complete overhaul at once, the team chose an incremental approach, releasing small improvements every two weeks.","ko":"한 번에 완전한 개편을 출시하는 대신 팀은 2주마다 소규모 개선 사항을 출시하는 점진적인 접근 방식을 선택했어요."},
  {"situation":"과학 연구 진보를 논의할 때","en":"Most scientific progress is incremental rather than revolutionary, with each study adding a small piece to a much larger puzzle.","ko":"대부분의 과학적 진보는 혁명적이기보다는 점진적이며, 각 연구는 훨씬 더 큰 퍼즐에 작은 조각을 추가해요."},
  {"situation":"가격 전략을 논의할 때","en":"The airline adopted an incremental pricing model, charging separately for luggage, seat selection, and meals to keep the base fare artificially low.","ko":"항공사는 기본 요금을 인위적으로 낮게 유지하기 위해 수하물, 좌석 선택, 식사에 별도 요금을 부과하는 점진적 가격 책정 모델을 채택했어요."},
  {"situation":"정책 개혁을 논의할 때","en":"Some political analysts favour incremental reform over radical change, arguing that gradual adjustments are less likely to destabilise established institutions.","ko":"일부 정치 분석가들은 급진적 변화보다 점진적 개혁을 선호하며, 점진적 조정이 기존 기관을 불안정하게 만들 가능성이 낮다고 주장해요."},
  {"situation":"제조 효율성을 논의할 때","en":"The factory's lean manufacturing programme delivered incremental improvements in cycle time and defect rates over a five-year period.","ko":"공장의 린 제조 프로그램은 5년에 걸쳐 사이클 타임과 불량률에서 점진적인 개선을 제공했어요."},
  {"situation":"예산 증액을 논의할 때","en":"The department requested incremental budget increases over three years rather than a single large allocation, making the expenditure easier to justify and track.","ko":"부서는 단일 대규모 배정보다는 3년에 걸친 점진적인 예산 증가를 요청했으며, 이는 지출을 정당화하고 추적하기 더 쉽게 만들었어요."},
  {"situation":"기술 혁신을 논의할 때","en":"Critics argued that the new model represented merely incremental progress -- a modest refinement of existing features rather than a genuinely transformative product.","ko":"비평가들은 새 모델이 단순히 점진적 진보를 나타낼 뿐이라고 주장했으며, 진정으로 혁신적인 제품이 아닌 기존 기능의 완만한 개선에 불과하다고 했어요."},
  {"situation":"경력 개발을 논의할 때","en":"Career growth is rarely linear; it typically involves incremental skill-building, lateral moves, and occasional setbacks before significant advancement occurs.","ko":"경력 성장은 좀처럼 선형적이지 않으며, 일반적으로 상당한 발전이 이루어지기 전에 점진적인 기술 향상, 횡적 이동, 가끔의 좌절이 포함돼요."},
  {"situation":"에너지 전환을 논의할 때","en":"Some economists advocate incremental expansion of renewable capacity rather than abrupt phaseout of fossil fuels, citing concerns about energy security and grid stability.","ko":"일부 경제학자들은 에너지 안보와 전력망 안정성에 대한 우려를 이유로 화석 연료의 급격한 단계적 폐지보다 재생 에너지 용량의 점진적 확장을 지지해요."},
  {"situation":"의료 치료 개선을 논의할 때","en":"Incremental advances in surgical techniques over the past decade have dramatically reduced recovery times and improved patient outcomes.","ko":"지난 10년간 수술 기법의 점진적인 발전은 회복 시간을 크게 단축하고 환자 결과를 개선했어요."}
]

R["integrated"] = [
  {"situation":"기술 시스템을 설명할 때","en":"The company replaced its legacy software with a fully integrated ERP platform that linked finance, HR, and supply chain functions in real time.","ko":"회사는 재무, HR, 공급망 기능을 실시간으로 연결하는 완전히 통합된 ERP 플랫폼으로 레거시 소프트웨어를 교체했어요."},
  {"situation":"교육 정책을 논의할 때","en":"Integrated schools that bring together students from different socioeconomic backgrounds have been shown to reduce attainment gaps over time.","ko":"다양한 사회경제적 배경을 가진 학생들을 함께 모은 통합 학교는 시간이 지남에 따라 성취도 격차를 줄이는 것으로 나타났어요."},
  {"situation":"마케팅 전략을 설명할 때","en":"An integrated marketing campaign uses the same core message across television, social media, print, and in-store promotions to reinforce brand awareness.","ko":"통합 마케팅 캠페인은 브랜드 인지도를 강화하기 위해 TV, 소셜 미디어, 인쇄물, 매장 내 프로모션에 걸쳐 동일한 핵심 메시지를 사용해요."},
  {"situation":"의료 서비스를 논의할 때","en":"An integrated care model co-ordinates primary, community, and hospital services so patients move seamlessly through different stages of treatment.","ko":"통합 의료 모델은 1차, 지역 사회, 병원 서비스를 조율하여 환자들이 다양한 치료 단계를 원활하게 이동할 수 있도록 해요."},
  {"situation":"환경 관리를 논의할 때","en":"Integrated watershed management considers the entire river catchment as a single system, balancing the competing demands of agriculture, urban use, and conservation.","ko":"통합 유역 관리는 전체 강 유역을 단일 시스템으로 고려하여 농업, 도시 사용, 보전의 경쟁적 수요 간의 균형을 맞춰요."},
  {"situation":"공급망을 설명할 때","en":"Vertical integration gave the company full control over its supply chain, from raw material extraction through manufacturing to final retail distribution.","ko":"수직 통합은 회사에 원자재 추출부터 제조를 거쳐 최종 소매 유통에 이르기까지 공급망에 대한 완전한 통제권을 부여했어요."},
  {"situation":"이민 정책을 논의할 때","en":"Successful integration of immigrants requires an integrated policy framework that addresses language learning, housing, employment, and social inclusion simultaneously.","ko":"이민자의 성공적인 통합은 언어 학습, 주거, 고용, 사회적 포용을 동시에 다루는 통합적 정책 프레임워크를 필요로 해요."},
  {"situation":"방위 산업을 설명할 때","en":"Modern warfare increasingly relies on integrated command systems that allow ground forces, air support, and naval units to share intelligence in real time.","ko":"현대 전쟁은 점점 더 지상군, 항공 지원, 해군 부대가 실시간으로 정보를 공유할 수 있는 통합 지휘 시스템에 의존해요."},
  {"situation":"도시 교통을 논의할 때","en":"An integrated transport network that seamlessly connects buses, trains, cycling infrastructure, and pedestrian routes can significantly reduce private car dependency.","ko":"버스, 기차, 자전거 인프라, 보행자 경로를 원활하게 연결하는 통합 교통 네트워크는 개인 자동차 의존도를 크게 줄일 수 있어요."},
  {"situation":"에너지 정책을 논의할 때","en":"An integrated energy strategy must balance the intermittency of renewables with reliable baseload capacity to ensure grid stability throughout the year.","ko":"통합 에너지 전략은 연중 전력망 안정성을 보장하기 위해 재생 에너지의 간헐성과 안정적인 기저부하 용량 사이의 균형을 맞춰야 해요."}
]

R["interim"] = [
  {"situation":"임시 경영진 임명을 설명할 때","en":"The board appointed an interim CEO to steady the business while a formal search for a permanent replacement was conducted.","ko":"이사회는 정식 후임자 채용이 진행되는 동안 사업을 안정시키기 위해 임시 CEO를 임명했어요."},
  {"situation":"프로젝트 진행 상황을 보고할 때","en":"An interim progress report was submitted to the client after the first phase of the project was completed, ahead of the final deliverable.","ko":"최종 결과물에 앞서 프로젝트 첫 번째 단계가 완료된 후 임시 진행 보고서가 고객에게 제출됐어요."},
  {"situation":"법적 조치를 설명할 때","en":"The court granted an interim injunction to halt the construction work pending a full hearing on the planning dispute.","ko":"법원은 계획 분쟁에 대한 완전한 심리가 있을 때까지 공사를 중단하기 위한 임시 금지 명령을 내렸어요."},
  {"situation":"재무 결과를 보고할 때","en":"The company released its interim results for the first half of the year, showing a fifteen percent increase in revenue compared to the same period last year.","ko":"회사는 상반기 임시 실적을 발표했으며, 전년 동기 대비 매출이 15% 증가했음을 보여줬어요."},
  {"situation":"정책 공백을 설명할 때","en":"An interim framework was adopted to regulate the emerging drone delivery sector while permanent legislation was being drafted.","ko":"영구 법안이 작성되는 동안 신흥 드론 배달 부문을 규제하기 위한 임시 프레임워크가 채택됐어요."},
  {"situation":"정치 권력 이양을 설명할 때","en":"Following the president's resignation, an interim government was sworn in to manage the country's affairs until early elections could be organised.","ko":"대통령 사임 이후, 조기 선거가 조직될 때까지 국가 업무를 관리하기 위해 임시 정부가 취임했어요."},
  {"situation":"협상 기간 중 조치를 설명할 때","en":"The two sides reached an interim agreement to maintain existing trade terms while longer-term negotiations on a comprehensive deal continued.","ko":"양측은 포괄적인 협정에 대한 장기 협상이 계속되는 동안 기존 무역 조건을 유지하기 위한 임시 합의에 도달했어요."},
  {"situation":"의료 시설 운영을 설명할 때","en":"An interim facility was set up in a community centre to handle the overflow of patients while the hospital underwent refurbishment.","ko":"병원이 수리되는 동안 환자 초과를 처리하기 위해 지역 사회 센터에 임시 시설이 설치됐어요."},
  {"situation":"HR 정책을 설명할 때","en":"During the reorganisation, several staff were placed on interim contracts until the new structure and roles were formally confirmed.","ko":"구조조정 중에 새 구조와 역할이 공식적으로 확정될 때까지 일부 직원들이 임시 계약으로 배치됐어요."},
  {"situation":"규제 준수를 설명할 때","en":"The company issued an interim compliance statement confirming it had taken corrective action after a regulatory audit flagged procedural gaps.","ko":"회사는 규제 감사에서 절차적 허점이 발견된 후 시정 조치를 취했음을 확인하는 임시 준수 성명을 발표했어요."}
]

R["mandatory"] = [
  {"situation":"직장 안전 요건을 설명할 때","en":"Attendance at the annual fire safety training is mandatory for all staff, and failure to complete it within the required timeframe may result in disciplinary action.","ko":"연간 소방 안전 교육 참석은 모든 직원에게 의무이며, 요구된 기간 내에 완료하지 않으면 징계 조치를 받을 수 있어요."},
  {"situation":"교육 정책을 논의할 때","en":"The government extended mandatory schooling to age eighteen, arguing that a longer period of formal education improves long-term employment prospects.","ko":"정부는 의무 교육을 18세까지 연장했으며, 더 긴 정규 교육 기간이 장기적인 취업 전망을 개선한다고 주장했어요."},
  {"situation":"공중 보건 조치를 설명할 때","en":"Mandatory vaccination programmes have been credited with the near-elimination of several childhood diseases that once caused widespread disability and death.","ko":"의무 예방접종 프로그램은 한때 광범위한 장애와 사망을 초래했던 여러 소아 질환을 거의 근절하는 데 기여했어요."},
  {"situation":"금융 규제를 설명할 때","en":"Mandatory disclosure requirements oblige listed companies to publish material information promptly so that all investors have equal access to market-sensitive data.","ko":"의무 공시 요건은 상장 기업이 모든 투자자가 시장 민감 데이터에 동등하게 접근할 수 있도록 중요한 정보를 즉시 공개하도록 의무화해요."},
  {"situation":"이민 절차를 설명할 때","en":"A mandatory security check is conducted on all applicants for permanent residency, regardless of their country of origin or prior visa status.","ko":"의무적인 보안 검사는 출신 국가나 이전 비자 상태에 관계없이 영주권 신청자 모두에 대해 실시돼요."},
  {"situation":"기업 지배구조를 설명할 때","en":"New corporate governance rules make it mandatory for listed companies to have at least one third of board seats filled by independent non-executive directors.","ko":"새로운 기업 지배구조 규칙은 상장 기업이 이사회 좌석의 최소 3분의 1을 독립 비상임 이사로 채우도록 의무화해요."},
  {"situation":"환경 규제를 설명할 때","en":"Mandatory environmental impact assessments are required before any major infrastructure project can receive planning permission.","ko":"모든 주요 인프라 프로젝트가 계획 허가를 받기 전에 의무적인 환경 영향 평가가 요구돼요."},
  {"situation":"법원 명령을 설명할 때","en":"The judge issued a mandatory injunction ordering the defendant to restore the disputed land to its original condition within sixty days.","ko":"판사는 피고에게 60일 이내에 분쟁 토지를 원래 상태로 복원하도록 명령하는 의무적 금지 명령을 내렸어요."},
  {"situation":"소비자 보호를 설명할 때","en":"Mandatory product safety testing ensures that all goods sold in the domestic market meet the minimum standards required to protect consumers from harm.","ko":"의무적인 제품 안전 테스트는 국내 시장에서 판매되는 모든 상품이 소비자를 해로움으로부터 보호하는 데 필요한 최소 기준을 충족하도록 보장해요."},
  {"situation":"계약 조건을 설명할 때","en":"The service level agreement includes mandatory response times that the supplier must meet, with financial penalties applied for each hour of non-compliance.","ko":"서비스 수준 계약에는 공급업체가 준수해야 하는 의무적인 응답 시간이 포함되어 있으며, 미준수 시간마다 재정적 벌금이 부과돼요."}
]

R["measurable"] = [
  {"situation":"성과 목표를 설정할 때","en":"Effective performance objectives must be measurable so that progress can be tracked objectively and discussed meaningfully during appraisals.","ko":"효과적인 성과 목표는 측정 가능해야 하며, 그래야 진행 상황을 객관적으로 추적하고 평가 중에 의미 있게 논의할 수 있어요."},
  {"situation":"정책 효과를 평가할 때","en":"Critics argued that the government's poverty reduction strategy lacked measurable targets, making it impossible to assess whether it was actually working.","ko":"비평가들은 정부의 빈곤 감소 전략에 측정 가능한 목표가 없어 실제로 효과가 있는지 평가하기가 불가능하다고 주장했어요."},
  {"situation":"마케팅 ROI를 설명할 때","en":"Digital marketing has transformed advertising by making the impact of each campaign measurable through metrics such as click-through rates and conversion ratios.","ko":"디지털 마케팅은 클릭률과 전환율 같은 지표를 통해 각 캠페인의 영향을 측정 가능하게 만들어 광고를 변화시켰어요."},
  {"situation":"환경 목표를 설명할 때","en":"The company committed to achieving measurable reductions in its carbon footprint, pledging to cut emissions by forty percent within a decade.","ko":"회사는 탄소 발자국에서 측정 가능한 감소를 달성하기로 약속하며 10년 내에 배출량을 40% 줄이겠다고 서약했어요."},
  {"situation":"의료 치료 효과를 논의할 때","en":"The new therapy produced measurable improvements in patient mobility after just twelve weeks of regular treatment, according to clinical assessments.","ko":"임상 평가에 따르면 새로운 치료법은 정기적 치료 12주 만에 환자 이동성에서 측정 가능한 개선을 가져왔어요."},
  {"situation":"교육 성과를 논의할 때","en":"The literacy programme delivered measurable gains in reading and comprehension scores among primary school children in the first year of implementation.","ko":"문해력 프로그램은 시행 첫 해에 초등학생들의 읽기 및 이해력 점수에서 측정 가능한 향상을 가져왔어요."},
  {"situation":"과학 연구를 논의할 때","en":"For a hypothesis to be scientifically valid, it must generate measurable, testable predictions that can be confirmed or refuted through controlled experimentation.","ko":"가설이 과학적으로 유효하려면 통제된 실험을 통해 확인하거나 반박할 수 있는 측정 가능하고 테스트 가능한 예측을 생성해야 해요."},
  {"situation":"프로젝트 관리를 논의할 때","en":"The project manager insisted that each milestone be tied to a measurable output, such as a completed report or a deployed software module.","ko":"프로젝트 관리자는 각 마일스톤이 완성된 보고서나 배포된 소프트웨어 모듈과 같은 측정 가능한 결과물과 연결되어야 한다고 주장했어요."},
  {"situation":"사회 프로그램 평가를 논의할 때","en":"Donors increasingly require NGOs to demonstrate measurable social impact before releasing funding for programme renewal.","ko":"기부자들은 NGO에 프로그램 갱신을 위한 자금 지원 전에 측정 가능한 사회적 영향을 보여줄 것을 점점 더 요구해요."},
  {"situation":"비즈니스 성과를 논의할 때","en":"Customer satisfaction surveys provide measurable data on service quality, helping management identify areas that need immediate attention.","ko":"고객 만족도 설문조사는 서비스 품질에 대한 측정 가능한 데이터를 제공하여 경영진이 즉각적인 주의가 필요한 영역을 식별하는 데 도움을 줘요."}
]

R["mutual"] = [
  {"situation":"사업 파트너십을 논의할 때","en":"The joint venture was built on a foundation of mutual benefit, with each partner contributing distinct capabilities and sharing the resulting profits equally.","ko":"합작 투자는 상호 이익의 토대 위에 구축됐으며, 각 파트너가 고유한 역량을 제공하고 결과 이익을 동등하게 공유했어요."},
  {"situation":"외교 관계를 논의할 때","en":"The two nations agreed to establish a framework for mutual recognition of professional qualifications, allowing engineers and doctors to work across borders more easily.","ko":"양국은 직업 자격의 상호 인정 프레임워크 구축에 합의하여 엔지니어와 의사들이 국경을 넘어 더 쉽게 일할 수 있게 됐어요."},
  {"situation":"팀 협업을 논의할 때","en":"A team environment built on mutual respect ensures that disagreements can be aired constructively without damaging working relationships.","ko":"상호 존중에 기반한 팀 환경은 의견 불일치가 업무 관계를 해치지 않고 건설적으로 표출될 수 있도록 보장해요."},
  {"situation":"분쟁 해결을 논의할 때","en":"The mediator helped both parties reach a mutual agreement that avoided costly litigation and preserved the commercial relationship for the future.","ko":"조정인은 양측이 비용이 많이 드는 소송을 피하고 미래를 위한 상업적 관계를 유지하는 상호 합의에 도달하도록 도왔어요."},
  {"situation":"보험 구조를 설명할 때","en":"A mutual insurance company is owned by its policyholders rather than external shareholders, meaning profits are returned to members rather than distributed as dividends.","ko":"상호 보험 회사는 외부 주주가 아닌 보험 가입자가 소유하므로, 이익이 배당금으로 분배되는 것이 아니라 회원들에게 반환돼요."},
  {"situation":"국제 협약을 논의할 때","en":"The treaty established a framework for mutual legal assistance, enabling signatories to share evidence and extradite suspects across national borders.","ko":"조약은 상호 법률 지원 프레임워크를 확립하여 서명국들이 국경을 넘어 증거를 공유하고 용의자를 인도할 수 있게 했어요."},
  {"situation":"교육 협력을 논의할 때","en":"The two universities signed a mutual exchange agreement enabling undergraduate students to spend a semester abroad without paying additional tuition fees.","ko":"두 대학교는 학부생들이 추가 등록금 없이 해외에서 한 학기를 보낼 수 있도록 하는 상호 교환 협정에 서명했어요."},
  {"situation":"투자자 관계를 논의할 때","en":"Mutual funds pool capital from many individual investors, enabling access to diversified portfolios that would be unaffordable for any single investor acting alone.","ko":"뮤추얼 펀드는 많은 개인 투자자로부터 자본을 모아 단독으로 행동하는 어떤 단일 투자자에게도 감당할 수 없는 다각화된 포트폴리오에 대한 접근을 가능하게 해요."},
  {"situation":"의료 연구 협력을 논의할 때","en":"The hospitals signed a mutual data-sharing agreement, allowing researchers on both sides to access anonymised patient records for comparative outcome studies.","ko":"병원들은 상호 데이터 공유 협정에 서명하여 양측 연구자들이 비교 결과 연구를 위해 익명화된 환자 기록에 접근할 수 있게 했어요."},
  {"situation":"지역 사회 협력을 논의할 때","en":"The programme fosters mutual support networks among immigrant families, pairing new arrivals with established community members who can offer practical guidance.","ko":"이 프로그램은 이민자 가족 간의 상호 지원 네트워크를 육성하여 신규 이민자들을 실용적인 지침을 제공할 수 있는 기존 지역 사회 구성원과 연결해요."}
]

R["nominal"] = [
  {"situation":"임금과 실질 가치를 설명할 때","en":"Although workers received a nominal pay rise of three percent, the increase was effectively wiped out by an inflation rate of four point five percent.","ko":"직원들은 3%의 명목 임금 인상을 받았지만, 이 인상분은 4.5%의 인플레이션율로 인해 사실상 사라졌어요."},
  {"situation":"회사 수수료를 설명할 때","en":"The platform charges a nominal fee of one dollar per transaction, making it accessible to small businesses that cannot afford premium payment processing services.","ko":"플랫폼은 거래당 1달러의 명목 수수료를 부과하여 프리미엄 결제 처리 서비스를 감당할 수 없는 소기업들이 이용할 수 있게 해요."},
  {"situation":"법인 소유 구조를 설명할 때","en":"The shares were held by a nominee director in a nominal capacity, with the actual beneficial owner remaining undisclosed for confidentiality reasons.","ko":"주식은 명목상의 능력으로 명의 이사가 보유했으며, 실제 수익적 소유자는 기밀 유지를 위해 공개되지 않았어요."},
  {"situation":"경제 지표를 설명할 때","en":"Economists distinguish between nominal GDP, which measures output at current prices, and real GDP, which adjusts for the effects of inflation.","ko":"경제학자들은 현재 가격으로 생산량을 측정하는 명목 GDP와 인플레이션 효과를 조정한 실질 GDP를 구분해요."},
  {"situation":"가격 결정 전략을 설명할 때","en":"Setting a nominal cover price for the magazine helped maintain the perception of value while the business model relied primarily on advertising revenue.","ko":"잡지의 명목 판매 가격을 설정하는 것은 비즈니스 모델이 주로 광고 수입에 의존하는 동안 가치에 대한 인식을 유지하는 데 도움이 됐어요."},
  {"situation":"이자율을 설명할 때","en":"The central bank cut the nominal interest rate to near zero, but the real rate remained positive due to persistently low inflation expectations.","ko":"중앙은행은 명목 금리를 거의 제로 수준으로 인하했지만, 지속적으로 낮은 인플레이션 기대로 인해 실질 금리는 플러스를 유지했어요."},
  {"situation":"지분 구조를 설명할 때","en":"Although he held a nominal stake of less than one percent, his historical involvement with the company created a reputational conflict of interest.","ko":"그는 1% 미만의 명목 지분을 보유했지만, 회사와의 역사적 연관으로 인해 명성 측면에서 이해 충돌이 발생했어요."},
  {"situation":"규제 준수를 설명할 때","en":"Paying a nominal fine without admitting liability allowed the company to settle the regulatory investigation quickly and move on.","ko":"책임을 인정하지 않고 명목상의 벌금을 납부함으로써 회사는 규제 조사를 신속하게 해결하고 앞으로 나아갈 수 있었어요."},
  {"situation":"프로젝트 비용을 설명할 때","en":"The office renovation was delivered at nominal cost because a sponsor covered the majority of expenses in exchange for branding rights at the venue.","ko":"스폰서가 장소 내 브랜딩 권리의 대가로 대부분의 비용을 부담했기 때문에 사무실 리노베이션은 명목 비용으로 완료됐어요."},
  {"situation":"임시 리더십을 설명할 때","en":"He served as nominal chairman during the transition period, lending his name to give the fledgling organisation credibility while real authority rested with the executive committee.","ko":"그는 전환 기간 동안 명목 의장으로 봉사했으며, 실제 권한이 집행위원회에 있는 동안 신생 조직에 신뢰성을 부여하기 위해 자신의 이름을 빌려줬어요."}
]

R["operational"] = [
  {"situation":"기업 효율성을 논의할 때","en":"Following the merger, the board prioritised operational efficiency by consolidating overlapping functions and eliminating redundant management layers.","ko":"합병 이후 이사회는 중복 기능을 통합하고 불필요한 관리 계층을 제거하여 운영 효율성을 우선시했어요."},
  {"situation":"리스크 관리를 논의할 때","en":"The bank's operational risk framework identifies process failures, IT outages, and human error as the primary sources of non-financial loss.","ko":"은행의 운영 리스크 프레임워크는 프로세스 실패, IT 중단, 인적 오류를 비재무적 손실의 주요 원천으로 식별해요."},
  {"situation":"신규 시설 가동을 설명할 때","en":"The new manufacturing plant became fully operational after an 18-month construction and commissioning phase, increasing total production capacity by thirty percent.","ko":"새 제조 공장은 18개월의 건설 및 시운전 단계를 거쳐 완전히 가동되었으며, 총 생산 능력을 30% 증가시켰어요."},
  {"situation":"공급망 관리를 논의할 때","en":"Operational disruptions in the semiconductor supply chain had cascading effects on automotive and electronics manufacturers worldwide.","ko":"반도체 공급망의 운영 혼란은 전 세계 자동차 및 전자 제조업체에 연쇄적인 영향을 미쳤어요."},
  {"situation":"재난 대응을 논의할 때","en":"Emergency management agencies rehearse operational protocols regularly so that co-ordination between different agencies is smooth during an actual crisis.","ko":"비상 관리 기관들은 실제 위기 시 다양한 기관 간의 조율이 원활하도록 운영 프로토콜을 정기적으로 훈련해요."},
  {"situation":"군사 작전을 설명할 때","en":"The commanding officer briefed the unit on the operational objectives for the exercise, specifying communication protocols and rules of engagement.","ko":"지휘관은 통신 프로토콜과 교전 규칙을 명시하며 훈련에 대한 운영 목표를 부대에 브리핑했어요."},
  {"situation":"스타트업 성장을 논의할 때","en":"Many startups struggle to transition from a scrappy founding team to a structured organisation with clear operational processes and accountability frameworks.","ko":"많은 스타트업들이 투지 있는 창업팀에서 명확한 운영 프로세스와 책임 프레임워크를 갖춘 구조화된 조직으로 전환하는 데 어려움을 겪어요."},
  {"situation":"IT 시스템을 설명할 때","en":"The legacy system was kept operational during the migration to the new platform to ensure continuity of service for customers.","ko":"고객에 대한 서비스 연속성을 보장하기 위해 새 플랫폼으로의 마이그레이션 중에 레거시 시스템이 운영 상태로 유지됐어요."},
  {"situation":"병원 운영을 논의할 때","en":"Hospitals must maintain robust operational protocols for infection control, triage, and patient discharge to prevent bottlenecks and protect staff safety.","ko":"병원은 병목 현상을 방지하고 직원 안전을 보호하기 위해 감염 통제, 분류, 환자 퇴원에 대한 강력한 운영 프로토콜을 유지해야 해요."},
  {"situation":"비용 구조를 분석할 때","en":"The airline reduced its cost base by shifting to a lower operational cost model, standardising its fleet and outsourcing non-core ground handling services.","ko":"항공사는 항공기를 표준화하고 비핵심 지상 처리 서비스를 아웃소싱하여 더 낮은 운영 비용 모델로 전환함으로써 비용 기반을 줄였어요."}
]

R["overarching"] = [
  {"situation":"전략 목표를 설명할 때","en":"The overarching goal of the five-year plan is to reduce carbon emissions by fifty percent while maintaining economic growth above two percent annually.","ko":"5개년 계획의 포괄적인 목표는 연간 2% 이상의 경제 성장을 유지하면서 탄소 배출량을 50% 줄이는 거예요."},
  {"situation":"정부 정책 구조를 설명할 때","en":"An overarching legislative framework is needed to co-ordinate the various ministries responsible for digital infrastructure, data privacy, and cybersecurity.","ko":"디지털 인프라, 데이터 프라이버시, 사이버 보안을 담당하는 다양한 부처를 조율하기 위한 포괄적인 입법 프레임워크가 필요해요."},
  {"situation":"교육 시스템 개혁을 논의할 때","en":"Without an overarching vision for what education should achieve, individual policy reforms risk being incoherent and pulling in different directions.","ko":"교육이 무엇을 달성해야 하는지에 대한 포괄적인 비전 없이는 개별 정책 개혁이 일관성을 잃고 서로 다른 방향으로 끌릴 위험이 있어요."},
  {"situation":"기업 전략을 논의할 때","en":"The CEO's presentation outlined an overarching strategy of global diversification, with specific regional plans nested beneath a single corporate umbrella.","ko":"CEO의 발표는 단일 기업 우산 아래 특정 지역 계획을 포함하는 글로벌 다각화의 포괄적인 전략을 개요로 제시했어요."},
  {"situation":"연구 프레임워크를 설명할 때","en":"The overarching research question addressed how demographic change affects labour market outcomes, with three sub-studies examining specific age groups.","ko":"포괄적인 연구 질문은 인구 변화가 노동 시장 결과에 어떤 영향을 미치는지를 다뤘으며, 세 개의 하위 연구가 특정 연령 집단을 조사했어요."},
  {"situation":"국제 협약을 논의할 때","en":"The United Nations Framework Convention on Climate Change provides the overarching legal architecture within which the Paris Agreement and other accords operate.","ko":"유엔 기후변화협약은 파리협정 및 기타 협약이 운영되는 포괄적인 법적 구조를 제공해요."},
  {"situation":"공중 보건 정책을 논의할 때","en":"An overarching public health strategy should address the social determinants of health rather than treating individual diseases in isolation.","ko":"포괄적인 공중 보건 전략은 개별 질환을 따로 치료하는 대신 건강의 사회적 결정 요인을 다루어야 해요."},
  {"situation":"도시 계획을 논의할 때","en":"The city's overarching master plan balances housing supply, environmental protection, and transport connectivity across a twenty-year development horizon.","ko":"도시의 포괄적인 마스터플랜은 20년 개발 지평에 걸쳐 주택 공급, 환경 보호, 교통 연결성의 균형을 맞추고 있어요."},
  {"situation":"교육 과정 설계를 논의할 때","en":"The overarching aim of the revised curriculum is to cultivate lifelong learners who can adapt to rapidly changing technological and social environments.","ko":"개정된 교육과정의 포괄적인 목적은 급격히 변화하는 기술적, 사회적 환경에 적응할 수 있는 평생 학습자를 육성하는 거예요."},
  {"situation":"팀 목표를 설명할 때","en":"Individual project milestones should always be aligned with the overarching business objective; otherwise teams risk delivering outputs that serve no strategic purpose.","ko":"개별 프로젝트 마일스톤은 항상 포괄적인 비즈니스 목표와 일치해야 하며, 그렇지 않으면 팀이 전략적 목적이 없는 결과물을 제공할 위험이 있어요."}
]

count = 0
for w in data6['words']:
    if w['word'] in R:
        w['examples'] = R[w['word']]
        count += 1

print(f"Updated {count} words")
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_6.json', 'w', encoding='utf-8') as f:
    json.dump(data6, f, ensure_ascii=False, indent=2)
print("Saved ielts_6.json batch 3")
