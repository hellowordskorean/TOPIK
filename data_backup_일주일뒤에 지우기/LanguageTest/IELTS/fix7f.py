import json
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', encoding='utf-8') as f:
    data7 = json.load(f)
R = {}

R["pervasive"] = [
    {"situation": "사회 문화 및 기술 영향", "en": "The pervasive influence of social media has fundamentally altered how people form and maintain relationships.", "ko": "소셜 미디어의 만연한 영향력은 사람들이 관계를 형성하고 유지하는 방식을 근본적으로 변화시켰다."},
    {"situation": "직장 내 차별 및 편견", "en": "Research revealed that gender bias in hiring remained pervasive despite equal opportunities legislation.", "ko": "연구는 기회 균등 법제에도 불구하고 채용에서의 성별 편견이 만연해 있다는 것을 밝혔다."},
    {"situation": "공중 보건 및 만성 질환", "en": "Sedentary lifestyles have become pervasive in modern societies, contributing to rising rates of obesity and diabetes.", "ko": "좌식 생활 방식이 현대 사회에 만연해져 비만과 당뇨병 비율 증가에 기여하고 있다."},
    {"situation": "사이버 보안 및 디지털 위협", "en": "Phishing attacks have become so pervasive that organisations now devote significant resources to staff awareness training.", "ko": "피싱 공격이 너무 만연해져 조직들은 이제 직원 인식 교육에 상당한 자원을 투입한다."},
    {"situation": "경제 불평등 및 사회 구조", "en": "Poverty in certain urban districts is pervasive and deeply entrenched, resisting conventional policy interventions.", "ko": "특정 도시 지역의 빈곤은 만연하고 깊이 뿌리내려져 있어 기존의 정책 개입에 저항한다."},
    {"situation": "오염 및 환경 오염", "en": "Microplastic contamination has become pervasive in marine ecosystems, threatening biodiversity at every level of the food chain.", "ko": "미세 플라스틱 오염이 해양 생태계에 만연해져 먹이 사슬의 모든 수준에서 생물 다양성을 위협하고 있다."},
    {"situation": "부패 및 거버넌스 문제", "en": "Pervasive corruption undermines investor confidence and discourages foreign direct investment in the region.", "ko": "만연한 부패는 투자자 신뢰를 약화시키고 그 지역의 외국인 직접 투자를 억제한다."},
    {"situation": "학교 따돌림 및 청소년 문화", "en": "Studies indicate that online bullying has become pervasive among teenagers, with serious implications for mental health.", "ko": "연구에 따르면 온라인 따돌림이 청소년들 사이에서 만연해져 정신 건강에 심각한 영향을 미치고 있다."},
    {"situation": "언론 자유 및 언론 환경", "en": "State propaganda became pervasive after the government assumed control of the main broadcasting outlets.", "ko": "정부가 주요 방송 매체를 통제하게 된 후 국가 선전이 만연해졌다."},
    {"situation": "직장 문화 및 번아웃 현상", "en": "Burnout has become pervasive in knowledge-intensive industries where performance demands are relentless.", "ko": "번아웃은 성과 요구가 끊임없는 지식 집약적 산업에서 만연해졌다."}
]

R["plausible"] = [
    {"situation": "법정 변론 및 방어 전략", "en": "The defence attorney argued that a plausible alternative explanation existed for the physical evidence found at the scene.", "ko": "변호인은 현장에서 발견된 물적 증거에 대한 그럴듯한 대안적 설명이 존재한다고 주장했다."},
    {"situation": "경제 예측 및 시나리오 분석", "en": "The bank presented three plausible economic scenarios ranging from mild recession to robust recovery.", "ko": "은행은 완만한 경기 침체에서 강력한 경기 회복까지 세 가지 그럴듯한 경제 시나리오를 제시했다."},
    {"situation": "과학 이론 및 가설 검증", "en": "Scientists consider a hypothesis plausible when it is consistent with known evidence and theoretically coherent.", "ko": "과학자들은 가설이 알려진 증거와 일치하고 이론적으로 일관성이 있을 때 그럴듯하다고 간주한다."},
    {"situation": "미디어 허위 정보 및 팩트 체크", "en": "Misinformation is particularly dangerous when it is superficially plausible and aligns with existing audience beliefs.", "ko": "허위 정보는 표면적으로 그럴듯하고 기존의 청중 믿음과 일치할 때 특히 위험하다."},
    {"situation": "역사 해석 및 사학 방법론", "en": "Historians must offer plausible interpretations supported by documentary evidence rather than speculation.", "ko": "역사학자들은 추측이 아닌 문서 증거에 의해 뒷받침되는 그럴듯한 해석을 제공해야 한다."},
    {"situation": "기후 변화 및 원인 분석", "en": "Scientists have demonstrated that human activity provides the most plausible explanation for observed global warming.", "ko": "과학자들은 인간 활동이 관측된 지구 온난화에 대한 가장 그럴듯한 설명을 제공한다는 것을 입증했다."},
    {"situation": "기업 전략 및 위기 대응", "en": "The CEO was required to provide a plausible explanation to shareholders for the company's unexpected profit warning.", "ko": "CEO는 회사의 예상치 못한 이익 경고에 대해 주주들에게 그럴듯한 설명을 제공해야 했다."},
    {"situation": "의료 진단 및 감별 진단 과정", "en": "The physician listed all plausible diagnoses before ordering tests to systematically rule each one out.", "ko": "의사는 각 진단을 체계적으로 배제하기 위해 검사를 지시하기 전에 모든 그럴듯한 진단을 나열했다."},
    {"situation": "외교 협상 및 상대방 의도 분석", "en": "Analysts debated whether the government's concession offer represented a plausible shift in policy or a tactical manoeuvre.", "ko": "분석가들은 정부의 양보 제안이 정책의 그럴듯한 변화인지 전략적 기동인지를 논쟁했다."},
    {"situation": "IELTS 에세이 및 논증 구성", "en": "An IELTS essay argument must be plausible and substantiated with relevant examples to achieve a high band score.", "ko": "IELTS 에세이 논증은 높은 밴드 점수를 달성하기 위해 그럴듯하고 관련 예시로 뒷받침되어야 한다."}
]

R["pragmatic"] = [
    {"situation": "정치 협상 및 타협 전략", "en": "A pragmatic approach to coalition government requires each party to compromise on secondary policy goals.", "ko": "연립 정부에 대한 실용적인 접근 방식은 각 정당이 부차적인 정책 목표에서 타협할 것을 요구한다."},
    {"situation": "비즈니스 전략 및 자원 배분", "en": "Management took a pragmatic decision to prioritise core products rather than pursue costly diversification.", "ko": "경영진은 비용이 많이 드는 다각화를 추구하는 대신 핵심 제품을 우선시하는 실용적인 결정을 내렸다."},
    {"situation": "교육 정책 및 학교 개혁", "en": "A pragmatic education policy balances aspirational goals with the realities of school funding and teacher shortages.", "ko": "실용적인 교육 정책은 포부 있는 목표와 학교 재정 및 교사 부족의 현실을 균형 있게 다룬다."},
    {"situation": "의료 자원 배분 및 우선순위 결정", "en": "Triage protocols demand pragmatic decisions about resource allocation when demand outstrips supply.", "ko": "중증도 분류 프로토콜은 수요가 공급을 초과할 때 자원 배분에 관한 실용적인 결정을 요구한다."},
    {"situation": "환경 정책 및 현실적 목표 설정", "en": "Critics acknowledged that the government's pragmatic emission targets were achievable, if not ideally ambitious.", "ko": "비평가들은 정부의 실용적인 배출 목표가 이상적으로 야심차지는 않지만 달성 가능하다고 인정했다."},
    {"situation": "법률 개혁 및 입법 절차", "en": "Lawmakers favoured a pragmatic, incremental approach to reform rather than sweeping structural overhaul.", "ko": "입법자들은 포괄적인 구조적 개편보다 실용적이고 점진적인 개혁 접근 방식을 선호했다."},
    {"situation": "외교 정책 및 국제 관계", "en": "The foreign minister advocated a pragmatic foreign policy that prioritised national interest over ideological alignment.", "ko": "외무장관은 이념적 정렬보다 국익을 우선시하는 실용적인 외교 정책을 지지했다."},
    {"situation": "기술 개발 및 소프트웨어 설계", "en": "Engineers adopted a pragmatic solution to the compatibility problem rather than redesigning the entire system.", "ko": "엔지니어들은 전체 시스템을 재설계하는 대신 호환성 문제에 대한 실용적인 해결책을 채택했다."},
    {"situation": "IELTS 시험 준비 및 학습 전략", "en": "A pragmatic revision strategy focuses on areas where improvement will most significantly raise the overall band score.", "ko": "실용적인 복습 전략은 개선이 전체 밴드 점수를 가장 크게 향상시킬 영역에 집중한다."},
    {"situation": "사회 복지 및 정책 실행", "en": "Social workers must often be pragmatic, adapting policy guidelines to the specific needs of individual clients.", "ko": "사회복지사들은 종종 실용적이어야 하며, 개별 고객의 특정 필요에 맞게 정책 지침을 조정해야 한다."}
]

R["probationary"] = [
    {"situation": "고용 계약 및 신규 직원 평가", "en": "New employees typically undergo a three-month probationary period during which performance is closely monitored.", "ko": "신입 직원들은 일반적으로 성과가 면밀히 모니터링되는 3개월의 수습 기간을 거친다."},
    {"situation": "형사 사법 및 보호 관찰", "en": "The judge sentenced the offender to twelve months of probationary supervision rather than a custodial term.", "ko": "판사는 범죄자에게 구금형 대신 12개월의 수습 감독 판결을 내렸다."},
    {"situation": "대학 입학 및 학업 조건부 허가", "en": "Students admitted on a probationary basis must achieve a minimum grade point average by the end of their first semester.", "ko": "조건부로 입학한 학생들은 첫 학기 말까지 최소 학점 평균을 달성해야 한다."},
    {"situation": "면허 정지 및 전문직 징계", "en": "The medical board placed the doctor on probationary registration after concerns about his clinical judgment were raised.", "ko": "의사 협회는 그의 임상적 판단에 대한 우려가 제기된 후 해당 의사를 수습 등록 상태로 두었다."},
    {"situation": "청소년 사법 및 소년 범죄", "en": "First-time juvenile offenders may receive a probationary sentence designed to rehabilitate rather than punish.", "ko": "초범 청소년 범죄자들은 처벌보다 재활을 목적으로 하는 수습 판결을 받을 수 있다."},
    {"situation": "교육 기관 및 교사 채용", "en": "Newly qualified teachers typically serve a probationary year under the mentorship of an experienced colleague.", "ko": "새로 자격을 취득한 교사들은 일반적으로 경험 많은 동료의 멘토링 하에 수습 기간 1년을 근무한다."},
    {"situation": "이민 및 임시 체류 허가", "en": "Newly arrived immigrants on a probationary visa must demonstrate language proficiency and employment within two years.", "ko": "수습 비자를 가진 신규 이민자들은 2년 내에 언어 능력과 취업을 입증해야 한다."},
    {"situation": "운전 면허 및 신규 운전자 규정", "en": "Probationary licence holders face stricter blood alcohol limits and are prohibited from driving unsupervised at night.", "ko": "수습 면허 보유자들은 더 엄격한 혈중 알코올 한도에 직면하며 야간에 감독 없이 운전하는 것이 금지된다."},
    {"situation": "기업 파트너십 및 신규 파트너 평가", "en": "The partnership agreement included a twelve-month probationary phase before the new partner could hold full voting rights.", "ko": "파트너십 계약에는 신규 파트너가 완전한 의결권을 갖기 전 12개월의 수습 단계가 포함되어 있었다."},
    {"situation": "스포츠 및 팀 선발 기준", "en": "Players signed on a probationary contract had to prove their fitness and form before being offered a permanent deal.", "ko": "수습 계약으로 서명한 선수들은 영구 계약을 제안받기 전에 체력과 컨디션을 증명해야 했다."}
]

R["proprietary"] = [
    {"situation": "지적재산권 및 영업 비밀 보호", "en": "The company refused to disclose the proprietary formula that gave its product a competitive advantage.", "ko": "회사는 제품에 경쟁 우위를 부여하는 독점적 제조법을 공개하기를 거부했다."},
    {"situation": "소프트웨어 라이선스 및 오픈 소스", "en": "Organisations often weigh the benefits of proprietary software against the flexibility of open-source alternatives.", "ko": "조직들은 독점 소프트웨어의 이점과 오픈 소스 대안의 유연성을 종종 비교 고려한다."},
    {"situation": "의약품 개발 및 특허 보호 기간", "en": "Once the proprietary patent expires, generic manufacturers are free to produce cheaper versions of the drug.", "ko": "독점 특허가 만료되면 제네릭 제조업체들은 저렴한 버전의 약품을 자유롭게 생산할 수 있다."},
    {"situation": "금융 서비스 및 투자 알고리즘", "en": "The hedge fund's proprietary trading algorithm was protected as a trade secret and never shared externally.", "ko": "헤지 펀드의 독점 거래 알고리즘은 영업 비밀로 보호되었으며 외부에 공유된 적이 없었다."},
    {"situation": "기술 표준화 및 상호 운용성", "en": "Reliance on proprietary technology standards can create vendor lock-in and reduce competition.", "ko": "독점 기술 표준에 대한 의존은 공급업체 종속을 만들고 경쟁을 감소시킬 수 있다."},
    {"situation": "식품 산업 및 브랜드 레시피", "en": "The restaurant chain built its global success on proprietary recipes developed over several decades.", "ko": "그 레스토랑 체인은 수십 년에 걸쳐 개발된 독점 레시피를 기반으로 글로벌 성공을 구축했다."},
    {"situation": "반독점 규제 및 시장 지배력", "en": "Regulators examined whether the firm's proprietary data gave it an unfair advantage over smaller competitors.", "ko": "규제 당국은 해당 회사의 독점 데이터가 소규모 경쟁업체들에 대한 불공정한 이점을 제공하는지를 조사했다."},
    {"situation": "바이오테크 연구 및 유전자 특허", "en": "The biotech company held proprietary rights over several gene-editing techniques that were widely licensed.", "ko": "바이오테크 회사는 널리 라이선스된 여러 유전자 편집 기술에 대한 독점적 권리를 보유했다."},
    {"situation": "항공 우주 산업 및 방위 계약", "en": "The defence contractor maintained strict confidentiality over its proprietary aircraft design specifications.", "ko": "방산업체는 독점적인 항공기 설계 사양에 대한 엄격한 기밀을 유지했다."},
    {"situation": "소비자 전자 제품 및 생태계 전략", "en": "Technology giants have built large user bases by offering proprietary ecosystems that integrate hardware, software, and services.", "ko": "기술 대기업들은 하드웨어, 소프트웨어, 서비스를 통합하는 독점 생태계를 제공함으로써 대규모 사용자 기반을 구축했다."}
]

R["prudent"] = [
    {"situation": "재정 계획 및 개인 저축", "en": "Financial advisers recommend maintaining a prudent level of savings to cover at least six months of living expenses.", "ko": "재정 고문들은 최소 6개월치 생활비를 충당할 수 있는 신중한 수준의 저축을 유지할 것을 권고한다."},
    {"situation": "기업 리스크 관리 및 투자", "en": "A prudent investment policy diversifies exposure across asset classes to reduce concentration risk.", "ko": "신중한 투자 정책은 집중 위험을 줄이기 위해 자산 클래스 전반에 걸쳐 노출을 다양화한다."},
    {"situation": "공중 보건 및 예방 의학", "en": "It is prudent to maintain vaccination programmes even when a disease has been largely controlled.", "ko": "질병이 대체로 통제된 경우에도 예방 접종 프로그램을 유지하는 것이 신중하다."},
    {"situation": "법률 및 계약 협상", "en": "It is prudent to seek independent legal advice before signing any long-term commercial contract.", "ko": "장기 상업 계약에 서명하기 전에 독립적인 법률 자문을 구하는 것이 신중하다."},
    {"situation": "정부 예산 및 재정 정책", "en": "Prudent fiscal management requires setting aside reserves during economic booms to fund downturns.", "ko": "신중한 재정 관리는 경기 침체 시 자금을 지원하기 위해 경기 호황 동안 준비금을 따로 마련할 것을 요구한다."},
    {"situation": "환경 정책 및 예방 원칙", "en": "A prudent approach to environmental risk involves acting before scientific uncertainty is fully resolved.", "ko": "환경 위험에 대한 신중한 접근 방식은 과학적 불확실성이 완전히 해결되기 전에 행동하는 것을 포함한다."},
    {"situation": "의사결정 및 불확실성 관리", "en": "It is prudent to consider worst-case scenarios when planning for large-scale infrastructure projects.", "ko": "대규모 인프라 프로젝트 계획 시 최악의 시나리오를 고려하는 것이 신중하다."},
    {"situation": "보험 및 위험 평가", "en": "Prudent underwriters assess a full range of risk factors before setting premium levels for insurance policies.", "ko": "신중한 보험 인수인들은 보험료 수준을 설정하기 전에 전체 위험 요소를 평가한다."},
    {"situation": "사이버 보안 및 데이터 보호", "en": "It is prudent for organisations to conduct regular security audits rather than waiting for breaches to occur.", "ko": "조직들이 침해가 발생하기를 기다리지 않고 정기적인 보안 감사를 실시하는 것이 신중하다."},
    {"situation": "외교 정책 및 국제 분쟁", "en": "A prudent foreign policy avoids provocative actions that could escalate regional tensions unnecessarily.", "ko": "신중한 외교 정책은 지역 긴장을 불필요하게 고조시킬 수 있는 도발적인 행동을 피한다."}
]

count = 0
for w in data7['words']:
    if w['word'] in R:
        w['examples'] = R[w['word']]
        count += 1
print(f"Updated {count} words")
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', 'w', encoding='utf-8') as f:
    json.dump(data7, f, ensure_ascii=False, indent=2)
print("Saved ielts_7.json batch 6")
