import json
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', encoding='utf-8') as f:
    data7 = json.load(f)
R = {}

R["empirical"] = [
    {"situation": "과학 연구 방법론 및 실증적 증거", "en": "The theory was supported by empirical data collected from longitudinal studies spanning three decades.", "ko": "그 이론은 30년에 걸친 종단 연구에서 수집된 실증적 데이터에 의해 뒷받침되었다."},
    {"situation": "의학 임상 시험 및 증거 기반 의료", "en": "Evidence-based medicine requires that treatment decisions rest on sound empirical evidence rather than tradition.", "ko": "증거 기반 의학은 치료 결정이 전통이 아닌 타당한 실증적 증거에 기반할 것을 요구한다."},
    {"situation": "사회과학 연구 및 정량적 방법", "en": "The sociologist conducted empirical research using surveys across fifteen urban and rural communities.", "ko": "사회학자는 15개 도시 및 농촌 지역사회에 걸쳐 설문조사를 이용한 실증 연구를 수행했다."},
    {"situation": "경제학 이론 및 정책 평가", "en": "The economists sought empirical validation of the model by testing its predictions against historical trade data.", "ko": "경제학자들은 역사적 무역 데이터에 대한 모델의 예측을 검증함으로써 실증적 타당성을 확인하고자 했다."},
    {"situation": "교육학 연구 및 교수법 평가", "en": "Empirical studies have consistently shown that formative assessment improves long-term learning outcomes.", "ko": "실증 연구들은 형성 평가가 장기적인 학습 성과를 향상시킨다는 것을 일관되게 보여주었다."},
    {"situation": "심리학 실험 및 행동 연구", "en": "The psychologist designed an empirical experiment to test whether colour affects decision-making speed.", "ko": "심리학자는 색상이 의사결정 속도에 영향을 미치는지 검증하기 위한 실증 실험을 설계했다."},
    {"situation": "철학 및 인식론 논쟁", "en": "Empiricists argue that all genuine knowledge must ultimately derive from sensory experience.", "ko": "경험론자들은 모든 진정한 지식이 궁극적으로 감각적 경험에서 도출되어야 한다고 주장한다."},
    {"situation": "기후 변화 과학 및 기상 데이터", "en": "Empirical observations of rising sea temperatures provide compelling support for climate change models.", "ko": "해수면 온도 상승에 대한 실증적 관측은 기후 변화 모델에 대한 강력한 근거를 제공한다."},
    {"situation": "공공 정책 평가 및 정책 효과 분석", "en": "Policymakers increasingly rely on empirical analysis to assess the effectiveness of social welfare programmes.", "ko": "정책 입안자들은 사회 복지 프로그램의 효과를 평가하기 위해 점점 더 실증적 분석에 의존한다."},
    {"situation": "언어학 및 코퍼스 연구", "en": "Corpus linguistics provides an empirical basis for understanding how language is actually used in context.", "ko": "코퍼스 언어학은 언어가 실제로 맥락에서 어떻게 사용되는지 이해하기 위한 실증적 기반을 제공한다."}
]

R["enforceable"] = [
    {"situation": "계약법 및 법적 구속력", "en": "For an agreement to be legally enforceable, it must contain consideration, offer, and acceptance.", "ko": "계약이 법적으로 집행 가능하려면 약인, 청약, 승낙을 포함해야 한다."},
    {"situation": "국제 조약 및 협약 이행", "en": "Critics argue that the climate agreement lacks enforceable mechanisms to ensure countries meet their targets.", "ko": "비평가들은 기후 협약에 국가들이 목표를 달성하도록 보장하는 집행 가능한 메커니즘이 없다고 주장한다."},
    {"situation": "지적재산권 및 특허 보호", "en": "The patent must be registered in each jurisdiction for its rights to be legally enforceable in that territory.", "ko": "특허권이 해당 영토에서 법적으로 집행 가능하려면 각 관할권에서 등록되어야 한다."},
    {"situation": "노동법 및 단체협약", "en": "The collective bargaining agreement was declared enforceable by the labour tribunal after both parties signed it.", "ko": "단체협약은 양측이 서명한 후 노동 재판소에 의해 집행 가능한 것으로 선언되었다."},
    {"situation": "경쟁법 및 반독점 규정", "en": "Regulators sought to make the competition code more enforceable by increasing financial penalties.", "ko": "규제 당국은 재정적 처벌을 강화함으로써 경쟁법을 더 집행 가능하게 만들고자 했다."},
    {"situation": "부동산 거래 및 임대 계약", "en": "A verbal tenancy agreement is rarely enforceable without written evidence of the agreed terms.", "ko": "구두 임대 계약은 합의된 조건의 서면 증거 없이는 거의 집행 가능하지 않다."},
    {"situation": "가족법 및 양육 합의", "en": "A parenting plan becomes legally enforceable once it is formalised as a court order.", "ko": "양육 계획은 법원 명령으로 공식화되면 법적으로 집행 가능해진다."},
    {"situation": "사이버법 및 데이터 보호 규정", "en": "Data protection regulations are enforceable only if regulators have adequate investigative powers and resources.", "ko": "데이터 보호 규정은 규제 당국이 충분한 조사 권한과 자원을 보유할 때만 집행 가능하다."},
    {"situation": "스포츠법 및 선수 계약", "en": "Non-compete clauses in sports contracts are enforceable only within reasonable geographical and time limits.", "ko": "스포츠 계약의 경업 금지 조항은 합리적인 지리적·시간적 한계 내에서만 집행 가능하다."},
    {"situation": "중재 및 분쟁 해결 메커니즘", "en": "Arbitration awards are enforceable in over one hundred and fifty countries under the New York Convention.", "ko": "중재 판정은 뉴욕 협약에 따라 150개국 이상에서 집행 가능하다."}
]

R["equitable"] = [
    {"situation": "사회 정의 및 자원 배분", "en": "Advocates called for a more equitable distribution of public healthcare resources across urban and rural areas.", "ko": "지지자들은 도시와 농촌 지역에 걸쳐 공공 의료 자원의 보다 공평한 분배를 촉구했다."},
    {"situation": "교육 정책 및 기회 균등", "en": "An equitable education system ensures that socioeconomic background does not determine academic outcomes.", "ko": "공평한 교육 시스템은 사회경제적 배경이 학업 성과를 결정하지 않도록 보장한다."},
    {"situation": "법률 및 형평법 원칙", "en": "The court awarded equitable relief in the form of an injunction, rather than monetary compensation.", "ko": "법원은 금전적 보상 대신 금지 명령 형태의 형평법적 구제를 판결했다."},
    {"situation": "세금 제도 및 누진세 구조", "en": "Economists debate whether a flat tax rate is equitable given differences in disposable income.", "ko": "경제학자들은 가처분 소득의 차이를 고려할 때 단일 세율이 공평한지를 논쟁한다."},
    {"situation": "국제 무역 협정 및 공정 거래", "en": "Developing nations argued that the trade terms were not equitable and disadvantaged their agricultural sectors.", "ko": "개발도상국들은 무역 조건이 공평하지 않으며 자국의 농업 부문에 불리하다고 주장했다."},
    {"situation": "노동 시장 및 임금 공정성", "en": "The task force recommended measures to ensure equitable pay across genders and ethnic groups.", "ko": "태스크포스는 성별 및 민족 집단 간에 공평한 임금을 보장하기 위한 조치를 권고했다."},
    {"situation": "기업 지배 구조 및 소수 주주 보호", "en": "Minority shareholders sought an equitable buyout price that reflected the true value of their stake.", "ko": "소수 주주들은 자신의 지분의 진정한 가치를 반영하는 공평한 매입 가격을 요구했다."},
    {"situation": "도시 계획 및 주거 접근성", "en": "Planners aimed to create an equitable city where affordable housing was available in all neighbourhoods.", "ko": "도시 계획가들은 모든 지역에서 저렴한 주택을 이용할 수 있는 공평한 도시를 만들고자 했다."},
    {"situation": "기후 변화 협상 및 책임 분담", "en": "Equitable burden-sharing in climate policy requires acknowledging historical emissions and development needs.", "ko": "기후 정책에서 공평한 부담 분담은 역사적 배출량과 개발 필요성을 인정하는 것을 요구한다."},
    {"situation": "의료 윤리 및 환자 접근성", "en": "An equitable health system prioritises care according to clinical need rather than the ability to pay.", "ko": "공평한 의료 시스템은 지불 능력이 아닌 임상적 필요에 따라 의료를 우선시한다."}
]

R["exhaustive"] = [
    {"situation": "법률 연구 및 판례 검토", "en": "Counsel conducted an exhaustive review of case law before presenting the argument in court.", "ko": "변호인은 법정에서 주장을 제시하기 전에 판례를 철저히 검토했다."},
    {"situation": "학술 문헌 고찰 및 연구 방법", "en": "The literature review was exhaustive, covering publications from seventeen countries across four decades.", "ko": "문헌 고찰은 4십 년에 걸쳐 17개국의 출판물을 다루는 철저한 것이었다."},
    {"situation": "감사 및 재무 실사", "en": "Auditors carried out an exhaustive examination of the firm's accounts before confirming its solvency.", "ko": "감사인들은 회사의 지급 능력을 확인하기 전에 회사 계정에 대한 철저한 검사를 수행했다."},
    {"situation": "형사 수사 및 증거 수집", "en": "Detectives undertook an exhaustive search of the premises before concluding that no further evidence remained.", "ko": "형사들은 더 이상의 증거가 없다는 결론을 내리기 전에 해당 건물을 철저히 수색했다."},
    {"situation": "과학 실험 및 데이터 분석", "en": "The researchers performed exhaustive trials across multiple laboratory conditions to validate their hypothesis.", "ko": "연구자들은 가설을 검증하기 위해 다양한 실험실 조건에서 철저한 실험을 수행했다."},
    {"situation": "IELTS 시험 준비 및 학습 전략", "en": "An exhaustive vocabulary list is impractical; candidates should focus on high-frequency academic terms instead.", "ko": "철저한 어휘 목록은 비실용적이다. 수험생들은 대신 고빈도 학술 용어에 집중해야 한다."},
    {"situation": "정책 분석 및 옵션 평가", "en": "The policy brief provided an exhaustive assessment of all regulatory options available to the minister.", "ko": "정책 보고서는 장관이 이용할 수 있는 모든 규제 옵션에 대한 철저한 평가를 제공했다."},
    {"situation": "소비자 불만 처리 및 기업 책임", "en": "The company confirmed that an exhaustive internal investigation had found no evidence of product tampering.", "ko": "회사는 철저한 내부 조사 결과 제품 변조의 증거가 없었다고 확인했다."},
    {"situation": "의료 진단 및 감별 진단", "en": "The physician ordered exhaustive tests to rule out rare conditions before arriving at a definitive diagnosis.", "ko": "의사는 확정적인 진단에 도달하기 전에 희귀 질환을 배제하기 위해 철저한 검사를 지시했다."},
    {"situation": "소프트웨어 개발 및 품질 보증", "en": "The QA team performed exhaustive regression testing to ensure no existing features were broken by the update.", "ko": "QA 팀은 업데이트로 인해 기존 기능이 손상되지 않았는지 확인하기 위해 철저한 회귀 테스트를 수행했다."}
]

R["expeditious"] = [
    {"situation": "법원 절차 및 사법 효율성", "en": "The judge called for a more expeditious resolution of the case, given the defendant's extended pre-trial detention.", "ko": "판사는 피고의 장기 재판 전 구금을 고려하여 사건의 신속한 해결을 촉구했다."},
    {"situation": "무역 통관 및 세관 절차", "en": "Customs authorities introduced a streamlined process to enable the expeditious clearance of perishable goods.", "ko": "세관 당국은 부패 가능한 상품의 신속한 통관을 가능하게 하기 위한 간소화된 절차를 도입했다."},
    {"situation": "응급 의료 및 병원 처치", "en": "Expeditious treatment of stroke symptoms is critical to minimising permanent neurological damage.", "ko": "뇌졸중 증상의 신속한 치료는 영구적인 신경학적 손상을 최소화하는 데 중요하다."},
    {"situation": "기업 인수 및 실사 일정", "en": "Both parties agreed on an expeditious due diligence process to close the deal before the fiscal year end.", "ko": "양측은 회계연도 말 전에 거래를 마무리하기 위한 신속한 실사 절차에 동의했다."},
    {"situation": "외교 분쟁 해결 및 협상", "en": "The two governments called for an expeditious diplomatic resolution to avoid further escalation of the dispute.", "ko": "두 정부는 분쟁의 추가 확산을 방지하기 위해 신속한 외교적 해결을 촉구했다."},
    {"situation": "재난 대응 및 구호 물자 배포", "en": "Expeditious delivery of food and medical supplies was hampered by damaged infrastructure after the earthquake.", "ko": "지진 이후 손상된 기반 시설로 인해 식량과 의료 물자의 신속한 전달이 방해를 받았다."},
    {"situation": "이민 심사 및 비자 발급", "en": "The embassy offered an expeditious visa processing service for applicants with urgent medical or business needs.", "ko": "대사관은 긴급한 의료 또는 사업 필요가 있는 신청자들을 위한 신속 비자 처리 서비스를 제공했다."},
    {"situation": "건설 프로젝트 및 규제 승인", "en": "Developers submitted a request for expeditious planning approval to meet the housing project deadline.", "ko": "개발자들은 주택 사업 마감일을 맞추기 위해 신속한 계획 승인 요청을 제출했다."},
    {"situation": "형사 사법 및 수사 기간", "en": "The prosecutor's office was instructed to conduct a more expeditious investigation following public pressure.", "ko": "검찰청은 여론의 압력에 따라 보다 신속한 수사를 진행하도록 지시받았다."},
    {"situation": "공급망 관리 및 물류 효율성", "en": "The logistics manager implemented new routing software to facilitate expeditious delivery across regional warehouses.", "ko": "물류 매니저는 지역 창고 전체에 신속한 배송을 촉진하기 위해 새로운 경로 설정 소프트웨어를 도입했다."}
]

R["explicit"] = [
    {"situation": "법률 및 계약 조건 명시", "en": "The contract contained explicit provisions governing liability in the event of product failure.", "ko": "계약서에는 제품 고장 시 책임을 규정하는 명시적 조항이 포함되어 있었다."},
    {"situation": "교육 지도법 및 학습 지원", "en": "Research shows that explicit instruction in phonics is more effective than discovery-based approaches for early readers.", "ko": "연구에 따르면 파닉스에 대한 명시적 교수법이 초기 독자들에게 발견 학습 방식보다 더 효과적이다."},
    {"situation": "동의 및 윤리적 기준", "en": "Medical ethics requires that patients give explicit informed consent before undergoing invasive procedures.", "ko": "의료 윤리는 환자가 침습적 시술을 받기 전에 명시적인 사전 동의를 제공할 것을 요구한다."},
    {"situation": "미디어 및 콘텐츠 등급 분류", "en": "The film received an adult rating due to explicit scenes depicting drug use and extreme violence.", "ko": "그 영화는 마약 사용과 극심한 폭력을 묘사하는 노골적인 장면으로 인해 성인 등급을 받았다."},
    {"situation": "정책 문서 및 규정 명확성", "en": "The government issued explicit guidelines on data handling to reduce ambiguity among regulated entities.", "ko": "정부는 규제 대상 기관들 사이의 모호성을 줄이기 위해 데이터 처리에 관한 명시적 지침을 발표했다."},
    {"situation": "학술 논증 및 전제 명료화", "en": "An effective academic argument makes its underlying assumptions explicit rather than leaving them implicit.", "ko": "효과적인 학술 논증은 기저 가정을 암묵적으로 두지 않고 명시적으로 드러낸다."},
    {"situation": "컴퓨터 프로그래밍 및 코드 명확성", "en": "Explicit type declarations make code easier to read and reduce the likelihood of runtime errors.", "ko": "명시적 타입 선언은 코드를 읽기 쉽게 만들고 런타임 오류 가능성을 줄인다."},
    {"situation": "자녀 양육 및 경계 설정", "en": "Child psychologists recommend that parents set explicit boundaries and explain the reasons behind household rules.", "ko": "아동 심리학자들은 부모가 명시적 경계를 설정하고 가정 규칙의 이유를 설명할 것을 권장한다."},
    {"situation": "저작권 및 지식재산 사용 허가", "en": "Reproducing copyrighted material without explicit permission from the rights holder constitutes infringement.", "ko": "저작권 보유자의 명시적 허가 없이 저작권 있는 자료를 복제하는 것은 침해에 해당한다."},
    {"situation": "IELTS 쓰기 과제 및 논증 표현", "en": "Candidates are advised to state their position explicitly in the introduction rather than implying it through examples.", "ko": "수험생들은 예시를 통해 암시하기보다 서론에서 자신의 입장을 명시적으로 서술하도록 권고된다."}
]

R["forensic"] = [
    {"situation": "범죄 수사 및 법의학 증거", "en": "Forensic analysis of the crime scene yielded DNA evidence that ultimately led to a conviction.", "ko": "범죄 현장에 대한 법의학적 분석은 궁극적으로 유죄 판결로 이어진 DNA 증거를 산출했다."},
    {"situation": "회계 감사 및 재정 부정 수사", "en": "Forensic accountants were engaged to trace the movement of funds through a complex network of offshore entities.", "ko": "법의학 회계사들은 복잡한 역외 기업 네트워크를 통한 자금 이동을 추적하기 위해 고용되었다."},
    {"situation": "법률 및 전문가 증언", "en": "The defence engaged a forensic psychiatrist to assess whether the defendant was fit to stand trial.", "ko": "변호인은 피고가 재판에 참여하기에 적합한지를 평가하기 위해 법의 정신과 의사를 선임했다."},
    {"situation": "디지털 수사 및 사이버 범죄", "en": "Digital forensic investigators retrieved deleted emails that proved critical to the fraud prosecution.", "ko": "디지털 법의학 수사관들은 사기 기소에 결정적으로 중요한 삭제된 이메일을 복구했다."},
    {"situation": "기업 분쟁 및 소송 지원", "en": "A forensic review of the company's internal communications revealed evidence of deliberate misrepresentation.", "ko": "회사의 내부 커뮤니케이션에 대한 법의학적 검토는 의도적 허위 진술의 증거를 밝혀냈다."},
    {"situation": "환경 과학 및 오염 원인 규명", "en": "Forensic environmental testing identified the factory as the primary source of river contamination.", "ko": "법의학적 환경 테스트는 공장을 강 오염의 주요 원인으로 확인했다."},
    {"situation": "고고학 및 역사 유물 분석", "en": "Forensic techniques applied to the skeletal remains revealed that the individual had died from repeated trauma.", "ko": "골격 유해에 적용된 법의학적 기술은 해당 인물이 반복적인 외상으로 사망했음을 밝혔다."},
    {"situation": "학문적 토론 및 논증 방식", "en": "The professor approached the text with forensic precision, dismantling the author's argument clause by clause.", "ko": "교수는 법의학적 정밀함으로 텍스트에 접근하여 저자의 논증을 절별로 해체했다."},
    {"situation": "도로 교통 사고 및 원인 분석", "en": "Forensic reconstruction of the accident established that the vehicle had been travelling well above the speed limit.", "ko": "사고의 법의학적 재현은 차량이 제한 속도를 훨씬 초과하여 주행하고 있었음을 확인했다."},
    {"situation": "보험 청구 및 사기 방지", "en": "The insurer commissioned a forensic investigation after inconsistencies emerged in the claimant's account.", "ko": "보험사는 청구인의 진술에 불일치가 나타난 후 법의학적 조사를 의뢰했다."}
]

R["formidable"] = [
    {"situation": "스포츠 경쟁 및 상대 평가", "en": "The defending champions were considered a formidable opponent, having won the title for three consecutive years.", "ko": "디펜딩 챔피언은 3년 연속 우승을 차지하여 강력한 상대로 여겨졌다."},
    {"situation": "비즈니스 경쟁 및 시장 진입 장벽", "en": "New entrants faced formidable barriers including high capital requirements and established brand loyalty.", "ko": "신규 진입자들은 높은 자본 요건과 확립된 브랜드 충성도를 포함한 강력한 진입 장벽에 직면했다."},
    {"situation": "국제 안보 및 군사력", "en": "The alliance presented a formidable collective defence capability that deterred potential aggressors.", "ko": "그 동맹은 잠재적 침략자들을 억제하는 강력한 집단 방위 역량을 보여주었다."},
    {"situation": "학문 연구 및 연구 도전 과제", "en": "Replicating natural photosynthesis in a laboratory setting remains a formidable scientific challenge.", "ko": "자연 광합성을 실험실 환경에서 복제하는 것은 여전히 강력한 과학적 도전으로 남아 있다."},
    {"situation": "법률 소송 및 법정 변론", "en": "The lead counsel had a formidable reputation for cross-examination, rattling even the most composed witnesses.", "ko": "수석 변호인은 반대 심문으로 강력한 명성을 갖고 있어 가장 침착한 증인들도 흔들리게 했다."},
    {"situation": "환경 문제 및 정책 개혁의 어려움", "en": "Reducing plastic waste at scale presents a formidable logistical and political challenge for governments.", "ko": "대규모 플라스틱 폐기물 감소는 정부에 강력한 물류적·정치적 도전을 제기한다."},
    {"situation": "의료 기술 개발 및 질병 치료", "en": "Antibiotic resistance represents a formidable threat to global public health that demands urgent action.", "ko": "항생제 내성은 긴급한 조치를 요구하는 세계 공중 보건에 대한 강력한 위협을 나타낸다."},
    {"situation": "직업 선택 및 전문성 개발", "en": "Qualifying as a barrister requires passing a formidable set of examinations under significant time pressure.", "ko": "법정 변호사 자격을 취득하기 위해서는 상당한 시간 압박 하에 강력한 일련의 시험을 통과해야 한다."},
    {"situation": "역사 분석 및 제국주의 세력", "en": "At its peak, the empire commanded a formidable naval fleet that dominated trade routes across three continents.", "ko": "전성기에 그 제국은 세 대륙에 걸친 무역로를 지배하는 강력한 해군 함대를 보유했다."},
    {"situation": "교육 및 지식 습득 어려움", "en": "Mastering a tonal language as an adult learner presents a formidable phonological challenge.", "ko": "성인 학습자로서 성조 언어를 익히는 것은 강력한 음운론적 도전을 제기한다."}
]

R["granular"] = [
    {"situation": "데이터 분석 및 비즈니스 인텔리전스", "en": "Granular sales data enabled the retail chain to identify which products underperformed in specific regions.", "ko": "세분화된 판매 데이터는 소매 체인이 특정 지역에서 실적이 저조한 제품을 파악할 수 있게 했다."},
    {"situation": "정책 평가 및 공공 행정", "en": "The report called for more granular measurement of poverty indicators to capture regional disparities.", "ko": "보고서는 지역 격차를 파악하기 위해 빈곤 지표를 더 세분화하여 측정할 것을 촉구했다."},
    {"situation": "재정 회계 및 비용 추적", "en": "A granular breakdown of operating costs revealed that logistics accounted for forty percent of total expenditure.", "ko": "운영 비용의 세분화된 분류는 물류가 총 지출의 40%를 차지함을 밝혔다."},
    {"situation": "기후 과학 및 환경 모델링", "en": "Climate scientists require granular atmospheric data to improve the accuracy of regional weather models.", "ko": "기후 과학자들은 지역 기상 모델의 정확성을 향상시키기 위해 세분화된 대기 데이터가 필요하다."},
    {"situation": "의료 전자 기록 및 환자 데이터", "en": "A granular patient record system allows clinicians to track medication dosages and outcomes over time.", "ko": "세분화된 환자 기록 시스템은 임상의가 시간에 따른 약물 투여량과 결과를 추적할 수 있게 한다."},
    {"situation": "법령 및 규제 세부 사항", "en": "Effective regulation requires granular specifications to prevent companies from exploiting vague language.", "ko": "효과적인 규제는 기업들이 모호한 언어를 악용하지 못하도록 세분화된 명세를 요구한다."},
    {"situation": "공급망 관리 및 재고 추적", "en": "A granular view of inventory levels across all warehouses enabled faster response to supply shortages.", "ko": "모든 창고의 재고 수준에 대한 세분화된 시각은 공급 부족에 대한 더 빠른 대응을 가능하게 했다."},
    {"situation": "소비자 행동 연구 및 마케팅 세분화", "en": "Granular consumer segmentation allows marketers to personalise campaigns at the individual level.", "ko": "세분화된 소비자 세분화는 마케터들이 개인 수준에서 캠페인을 개인화할 수 있게 한다."},
    {"situation": "교육 평가 및 학습 분석", "en": "Granular assessment data helps teachers identify exactly where individual students are struggling.", "ko": "세분화된 평가 데이터는 교사들이 개별 학생들이 어디에서 어려움을 겪고 있는지 정확히 파악하도록 돕는다."},
    {"situation": "사이버 보안 및 네트워크 모니터링", "en": "Granular logging of network activity allows security teams to detect and trace anomalous behaviour rapidly.", "ko": "네트워크 활동의 세분화된 로깅은 보안팀이 비정상적인 행동을 신속하게 감지하고 추적할 수 있게 한다."}
]

count = 0
for w in data7['words']:
    if w['word'] in R:
        w['examples'] = R[w['word']]
        count += 1
print(f"Updated {count} words")
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', 'w', encoding='utf-8') as f:
    json.dump(data7, f, ensure_ascii=False, indent=2)
print("Saved ielts_7.json batch 3")
