import json
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', encoding='utf-8') as f:
    data7 = json.load(f)
R = {}

R["imminent"] = [
    {"situation": "기상 재해 및 긴급 경보", "en": "Authorities issued an imminent flood warning as water levels in the reservoir reached critical capacity.", "ko": "저수지의 수위가 임계 용량에 도달하자 당국은 긴박한 홍수 경보를 발령했다."},
    {"situation": "의료 응급 및 환자 상태 악화", "en": "The attending physician recognised signs of imminent respiratory failure and ordered immediate intubation.", "ko": "담당 의사는 긴박한 호흡 부전의 징후를 인식하고 즉각적인 삽관을 지시했다."},
    {"situation": "외교 위기 및 분쟁 예방", "en": "Foreign ministers convened an emergency session in response to imminent military escalation along the border.", "ko": "외무장관들은 국경을 따라 긴박하게 고조되는 군사적 긴장에 대응하기 위해 긴급 회의를 소집했다."},
    {"situation": "기업 파산 및 재정 위기", "en": "The board acknowledged that bankruptcy was imminent unless emergency refinancing could be secured within days.", "ko": "이사회는 며칠 내에 긴급 재융자를 확보하지 못하면 파산이 임박했다고 인정했다."},
    {"situation": "법률 및 인신 보호 영장", "en": "The defence argued that imminent danger to the client justified an emergency application to the court.", "ko": "변호인은 의뢰인에 대한 임박한 위험이 법원에 대한 긴급 신청을 정당화한다고 주장했다."},
    {"situation": "기술 발전 및 혁신 예측", "en": "Industry analysts predicted that the widespread adoption of quantum computing was imminent within the next decade.", "ko": "산업 분석가들은 향후 10년 내에 양자 컴퓨팅의 광범위한 채택이 임박했다고 예측했다."},
    {"situation": "환경 위기 및 생태계 붕괴", "en": "Scientists warned that the collapse of the coral reef system was imminent without drastic intervention.", "ko": "과학자들은 대대적인 개입 없이는 산호초 생태계의 붕괴가 임박했다고 경고했다."},
    {"situation": "사이버 보안 및 공격 경보", "en": "The cyber security team identified indicators of an imminent ransomware attack and initiated lockdown protocols.", "ko": "사이버 보안팀은 임박한 랜섬웨어 공격의 징후를 확인하고 봉쇄 프로토콜을 시작했다."},
    {"situation": "건강 관리 및 노인 의료", "en": "Palliative care nurses are trained to recognise signs that death is imminent and to provide appropriate comfort.", "ko": "완화 치료 간호사들은 죽음이 임박했음을 나타내는 징후를 인식하고 적절한 편안함을 제공하도록 훈련받는다."},
    {"situation": "선거 정치 및 정책 변화", "en": "With an election imminent, the government fast-tracked popular spending pledges to boost its polling numbers.", "ko": "선거가 임박하자 정부는 지지율을 높이기 위해 인기 있는 지출 공약을 빠르게 추진했다."}
]

R["implicit"] = [
    {"situation": "계약법 및 묵시적 조건", "en": "An implicit duty of good faith is read into commercial contracts even when not explicitly stated.", "ko": "선의의 묵시적 의무는 명시적으로 언급되지 않아도 상업 계약에 포함된 것으로 해석된다."},
    {"situation": "언어학 및 의사소통 분석", "en": "Much of human communication relies on implicit meaning that is understood through shared cultural context.", "ko": "인간 의사소통의 많은 부분은 공유된 문화적 맥락을 통해 이해되는 묵시적 의미에 의존한다."},
    {"situation": "심리학 및 편향 연구", "en": "Implicit bias tests reveal attitudes that individuals may hold unconsciously, affecting their decisions.", "ko": "묵시적 편향 검사는 개인이 무의식적으로 보유할 수 있으며 의사결정에 영향을 미치는 태도를 드러낸다."},
    {"situation": "학술 논문 및 가정 명시화", "en": "The researcher acknowledged that her model rested on implicit assumptions about rational economic behaviour.", "ko": "연구자는 자신의 모델이 합리적인 경제적 행동에 관한 묵시적 가정에 의존한다는 것을 인정했다."},
    {"situation": "고용 관계 및 직장 문화", "en": "The company's culture contained implicit expectations about working hours that were never formally documented.", "ko": "회사의 문화에는 공식적으로 문서화된 적이 없는 근무 시간에 관한 묵시적 기대가 포함되어 있었다."},
    {"situation": "신뢰 및 대인 관계", "en": "There is an implicit trust between a doctor and patient that forms the foundation of effective medical care.", "ko": "효과적인 의료의 기반을 형성하는 의사와 환자 사이의 묵시적 신뢰가 있다."},
    {"situation": "문학 분석 및 텍스트 해석", "en": "The novelist's implicit critique of colonialism is woven through the narrative without ever being stated directly.", "ko": "소설가의 식민주의에 대한 묵시적 비판은 직접적으로 서술되지 않고 서사 전체에 걸쳐 짜여져 있다."},
    {"situation": "교육 정책 및 교육과정 설계", "en": "Some educators argue that implicit curriculum messages can reinforce gender stereotypes in the classroom.", "ko": "일부 교육자들은 묵시적 교육과정 메시지가 교실에서 성별 고정관념을 강화할 수 있다고 주장한다."},
    {"situation": "프로그래밍 언어 및 타입 시스템", "en": "Some programming languages use implicit type conversion, which can lead to unexpected behaviour if not understood.", "ko": "일부 프로그래밍 언어는 묵시적 타입 변환을 사용하는데, 이를 이해하지 못하면 예상치 못한 동작이 발생할 수 있다."},
    {"situation": "사회 규범 및 윤리적 기대", "en": "There is an implicit social contract in democratic societies that citizens respect the rule of law.", "ko": "민주주의 사회에서 시민들이 법의 지배를 존중한다는 묵시적 사회 계약이 있다."}
]

R["incumbent"] = [
    {"situation": "선거 정치 및 현직 후보", "en": "The incumbent president sought re-election on a platform of economic stability and foreign policy continuity.", "ko": "현직 대통령은 경제적 안정과 외교 정책의 연속성을 기반으로 재선을 추구했다."},
    {"situation": "직업적 의무 및 법적 책임", "en": "It is incumbent on all licensed professionals to keep their qualifications and knowledge up to date.", "ko": "모든 면허를 가진 전문가들은 자격증과 지식을 최신 상태로 유지할 의무가 있다."},
    {"situation": "기업 경쟁 및 시장 지위", "en": "Incumbent telecoms operators faced growing pressure from low-cost digital competitors entering the market.", "ko": "기존 통신 사업자들은 시장에 진입하는 저비용 디지털 경쟁자들로부터 증가하는 압박에 직면했다."},
    {"situation": "정부 기관 및 규제 의무", "en": "It is incumbent on regulatory agencies to act transparently and consistently in their enforcement decisions.", "ko": "규제 기관은 집행 결정에서 투명하고 일관되게 행동할 의무가 있다."},
    {"situation": "노동법 및 고용주 책임", "en": "It is incumbent on employers to provide a safe working environment regardless of the size of the organisation.", "ko": "고용주는 조직의 규모에 관계없이 안전한 근무 환경을 제공할 의무가 있다."},
    {"situation": "의료 윤리 및 환자 권리", "en": "It is incumbent on healthcare providers to explain all treatment options clearly to patients before obtaining consent.", "ko": "의료 제공자들은 동의를 받기 전에 모든 치료 옵션을 환자에게 명확하게 설명할 의무가 있다."},
    {"situation": "학문적 무결성 및 연구 윤리", "en": "It is incumbent on researchers to disclose potential conflicts of interest in published findings.", "ko": "연구자들은 발표된 연구 결과에서 잠재적 이해 충돌을 공개할 의무가 있다."},
    {"situation": "기후 변화 및 세대 간 책임", "en": "It is incumbent on present generations to address climate change so as not to burden future populations.", "ko": "현재 세대는 미래 세대에 부담을 주지 않기 위해 기후 변화를 해결할 의무가 있다."},
    {"situation": "국제법 및 국가 의무", "en": "It is incumbent on signatory states to honour their treaty obligations in both letter and spirit.", "ko": "서명국들은 조약 의무를 문자 그대로, 그리고 정신적으로도 준수할 의무가 있다."},
    {"situation": "학교 교육 및 시민 의식 교육", "en": "It is incumbent on schools to instil civic values that prepare students for active participation in democracy.", "ko": "학교는 학생들이 민주주의에 적극적으로 참여할 수 있도록 준비시키는 시민 가치를 심어줄 의무가 있다."}
]

R["indefeasible"] = [
    {"situation": "헌법법 및 기본권", "en": "The right to a fair trial is considered indefeasible and cannot be suspended even in times of national emergency.", "ko": "공정한 재판을 받을 권리는 불가침적인 것으로 여겨지며 국가 비상 사태에도 정지될 수 없다."},
    {"situation": "토지 등록 및 부동산권", "en": "Once registered, an indefeasible title to land provides the holder with absolute protection against adverse claims.", "ko": "등록되면 토지에 대한 불가침적 소유권은 보유자에게 불리한 청구에 대한 절대적인 보호를 제공한다."},
    {"situation": "철학 및 자연권 이론", "en": "Some philosophers argue that individuals possess indefeasible rights that no government may legitimately override.", "ko": "일부 철학자들은 개인이 어떠한 정부도 합법적으로 무시할 수 없는 불가침적 권리를 보유한다고 주장한다."},
    {"situation": "신탁법 및 수익자 권리", "en": "The beneficiary's indefeasible interest in the trust fund was protected even after the trustee became insolvent.", "ko": "수탁자가 파산한 후에도 신탁 기금에 대한 수익자의 불가침적 이익은 보호되었다."},
    {"situation": "국제 인권법 및 비훼손성", "en": "Under international law, the prohibition on torture is regarded as an indefeasible norm that admits no exceptions.", "ko": "국제법에 따르면 고문 금지는 예외를 허용하지 않는 불가침적 규범으로 여겨진다."},
    {"situation": "계약법 및 권리 포기 불가능성", "en": "The clause confirmed that the licensor's indefeasible right to terminate the agreement for breach could not be waived.", "ko": "해당 조항은 위반을 이유로 계약을 해지할 라이선서의 불가침적 권리가 포기될 수 없음을 확인했다."},
    {"situation": "회사법 및 주주 권리", "en": "Certain minority shareholder protections are indefeasible and cannot be removed by a majority resolution.", "ko": "특정 소수 주주 보호는 불가침적이며 다수결 결의에 의해 제거될 수 없다."},
    {"situation": "이민법 및 망명 권리", "en": "The right to seek asylum has been described as indefeasible under the 1951 Refugee Convention.", "ko": "망명을 신청할 권리는 1951년 난민 협약에 따라 불가침적인 것으로 묘사되어 왔다."},
    {"situation": "가족법 및 양육권", "en": "Courts have held that a child's indefeasible right to know their identity cannot be extinguished by adoption.", "ko": "법원은 자신의 정체성을 알 아이의 불가침적 권리가 입양에 의해 소멸될 수 없다고 판결했다."},
    {"situation": "토착민 권리 및 토지 소유권", "en": "Indigenous communities claimed an indefeasible ancestral title over the disputed territory predating colonial law.", "ko": "원주민 공동체들은 식민지 법률에 선행하는 분쟁 영토에 대한 불가침적 선조적 소유권을 주장했다."}
]

R["inherent"] = [
    {"situation": "리스크 관리 및 금융 투자", "en": "Every financial investment carries an inherent degree of risk that cannot be entirely eliminated.", "ko": "모든 금융 투자에는 완전히 제거할 수 없는 고유한 위험 수준이 존재한다."},
    {"situation": "법철학 및 권리 이론", "en": "The doctrine holds that individuals possess inherent dignity that must be respected by all legal systems.", "ko": "그 원칙은 개인이 모든 법률 체계가 존중해야 하는 고유한 존엄성을 보유한다고 주장한다."},
    {"situation": "과학 기술 및 시스템 한계", "en": "There are inherent limitations in predictive modelling due to the complexity of natural systems.", "ko": "자연 시스템의 복잡성으로 인해 예측 모델링에는 고유한 한계가 존재한다."},
    {"situation": "의료 및 치료 부작용", "en": "Surgeons must inform patients of the inherent risks associated with any major operative procedure.", "ko": "외과의는 모든 주요 수술 절차와 관련된 고유한 위험에 대해 환자에게 알려야 한다."},
    {"situation": "조직 문화 및 리더십 역량", "en": "Some management theorists argue that certain leadership qualities are inherent rather than learned.", "ko": "일부 경영 이론가들은 특정 리더십 자질이 학습된 것이 아니라 고유한 것이라고 주장한다."},
    {"situation": "환경 과학 및 생태계 기능", "en": "Wetlands have an inherent capacity to filter pollutants and regulate water flow in river systems.", "ko": "습지는 강 시스템에서 오염 물질을 여과하고 수류를 조절하는 고유한 능력을 갖고 있다."},
    {"situation": "국제 무역 및 비교 우위", "en": "Economists note that every country has inherent comparative advantages that shape its trade specialisation.", "ko": "경제학자들은 모든 국가가 무역 전문화를 형성하는 고유한 비교 우위를 갖고 있다고 지적한다."},
    {"situation": "언어 습득 및 인지 과학", "en": "Chomsky proposed that humans have an inherent capacity for language that is biologically encoded in the brain.", "ko": "촘스키는 인간이 뇌에 생물학적으로 인코딩된 고유한 언어 능력을 갖고 있다고 제안했다."},
    {"situation": "사회 정책 및 불평등 구조", "en": "Critics argue that there are inherent inequalities built into market economies that require redistribution mechanisms.", "ko": "비평가들은 재분배 메커니즘을 필요로 하는 고유한 불평등이 시장 경제에 내재되어 있다고 주장한다."},
    {"situation": "기업 윤리 및 이해 충돌", "en": "There is an inherent conflict of interest when an auditor has financial ties to the company it reviews.", "ko": "감사인이 검토하는 회사와 재정적 관계가 있을 때 고유한 이해 충돌이 존재한다."}
]

R["insolvent"] = [
    {"situation": "기업 파산 및 법적 절차", "en": "The company was formally declared insolvent after failing to meet its debt obligations for three consecutive quarters.", "ko": "회사는 3분기 연속 채무 이행에 실패한 후 공식적으로 파산 선언을 받았다."},
    {"situation": "금융 감독 및 은행 규제", "en": "Central banks monitor systemic risk to prevent large institutions from becoming insolvent during economic downturns.", "ko": "중앙은행은 경기 침체 시 대형 기관이 파산하지 않도록 시스템 리스크를 모니터링한다."},
    {"situation": "채권자 보호 및 부채 회수", "en": "Creditors are prioritised according to legal rank when an insolvent firm's assets are distributed.", "ko": "파산 기업의 자산이 분배될 때 채권자들은 법적 순위에 따라 우선순위가 결정된다."},
    {"situation": "공공 연금 및 재정 건전성", "en": "Actuaries warned that the pension fund would become insolvent within twenty years unless contribution rates were raised.", "ko": "보험계리사들은 기여율이 인상되지 않으면 연금 기금이 20년 내에 파산할 것이라고 경고했다."},
    {"situation": "이사 의무 및 도산 전 행위", "en": "Directors who continue trading while their company is insolvent may face personal liability for creditor losses.", "ko": "회사가 파산한 상태에서 계속 거래하는 이사들은 채권자 손실에 대한 개인적 책임에 직면할 수 있다."},
    {"situation": "무역 신용 및 공급자 위험", "en": "Suppliers monitor their clients' financial health closely to avoid exposure when a buyer becomes insolvent.", "ko": "공급자들은 구매자가 파산할 때 노출을 피하기 위해 고객의 재정 건전성을 면밀히 모니터링한다."},
    {"situation": "부동산 개발 및 건설 리스크", "en": "The developer became insolvent during construction, leaving hundreds of buyers without completed homes.", "ko": "개발업자는 건설 중 파산하여 수백 명의 구매자들이 완공된 주택 없이 남겨졌다."},
    {"situation": "국가 재정 및 주권 부채 위기", "en": "Some economists argued that the country was effectively insolvent and required an international rescue package.", "ko": "일부 경제학자들은 그 나라가 사실상 파산 상태이며 국제 구제 패키지가 필요하다고 주장했다."},
    {"situation": "보험 회사 및 지급 능력 요건", "en": "Regulatory capital requirements are designed to prevent insurance companies from becoming insolvent.", "ko": "규제 자본 요건은 보험 회사가 파산하지 않도록 설계되었다."},
    {"situation": "개인 재정 및 파산 신청", "en": "Individuals who are insolvent may apply for bankruptcy protection to manage debt repayment in an orderly way.", "ko": "파산한 개인은 채무 상환을 질서 있게 관리하기 위해 파산 보호를 신청할 수 있다."}
]

R["intangible"] = [
    {"situation": "회계 및 기업 가치 평가", "en": "Intangible assets such as brand equity and customer relationships are increasingly important in company valuations.", "ko": "브랜드 자산 및 고객 관계와 같은 무형 자산은 기업 가치 평가에서 점점 더 중요해지고 있다."},
    {"situation": "지적재산권 및 기술 혁신", "en": "The pharmaceutical firm's most valuable intangible assets were its proprietary drug formulations and patents.", "ko": "제약 회사의 가장 가치 있는 무형 자산은 독점적인 약물 제형과 특허였다."},
    {"situation": "조직 문화 및 직원 동기", "en": "Companies increasingly recognise that intangible benefits such as flexible working can attract and retain talent.", "ko": "기업들은 유연 근무와 같은 무형의 혜택이 인재를 유치하고 유지할 수 있다는 것을 점점 더 인식하고 있다."},
    {"situation": "문화 유산 보존 및 UNESCO", "en": "UNESCO's intangible cultural heritage programme protects traditions, languages, and performing arts at risk of disappearing.", "ko": "유네스코의 무형 문화유산 프로그램은 사라질 위기에 처한 전통, 언어, 공연 예술을 보호한다."},
    {"situation": "경제학 및 인적 자본 이론", "en": "Education produces intangible returns such as civic participation and social cohesion alongside measurable wage gains.", "ko": "교육은 측정 가능한 임금 증가와 함께 시민 참여 및 사회적 결속력과 같은 무형의 수익을 창출한다."},
    {"situation": "법률 및 손해 배상 산정", "en": "Courts often struggle to place a monetary value on intangible losses such as emotional distress and reputational harm.", "ko": "법원은 종종 정신적 고통과 명예 훼손과 같은 무형 손실에 금전적 가치를 부여하는 데 어려움을 겪는다."},
    {"situation": "스포츠 및 팀 정신", "en": "The coach attributed the team's success to intangible qualities like collective resilience and mutual trust.", "ko": "코치는 팀의 성공을 집단적 회복력과 상호 신뢰와 같은 무형의 자질 덕분으로 돌렸다."},
    {"situation": "마케팅 및 브랜드 전략", "en": "A luxury brand derives much of its value from intangible associations with heritage, craftsmanship, and exclusivity.", "ko": "럭셔리 브랜드는 유산, 장인 정신, 독점성과의 무형적 연관성에서 가치의 많은 부분을 도출한다."},
    {"situation": "공공 복지 및 삶의 질 측정", "en": "Policymakers are challenged by the difficulty of measuring intangible factors such as happiness and social connectedness.", "ko": "정책 입안자들은 행복과 사회적 연대감 같은 무형적 요소를 측정하는 어려움에 직면한다."},
    {"situation": "인수합병 및 무형 자산 평가", "en": "Goodwill represents an intangible asset acquired in a business combination that exceeds the fair value of net assets.", "ko": "영업권은 순자산의 공정 가치를 초과하는 기업 결합에서 취득한 무형 자산을 나타낸다."}
]

R["interlocutory"] = [
    {"situation": "민사 소송 및 임시 명령", "en": "The claimant sought an interlocutory injunction to prevent the defendant from disposing of assets before trial.", "ko": "청구인은 피고가 재판 전에 자산을 처분하지 못하도록 막기 위한 임시 금지 명령을 신청했다."},
    {"situation": "항소 절차 및 중간 판결", "en": "An interlocutory appeal was filed to challenge the trial court's ruling on the admissibility of evidence.", "ko": "증거의 허용 가능성에 관한 원심 법원의 결정에 이의를 제기하기 위해 중간 항소가 제기되었다."},
    {"situation": "지적재산권 분쟁 및 임시 조치", "en": "The rights holder obtained an interlocutory order preventing the rival from selling the allegedly infringing product.", "ko": "권리 보유자는 경쟁사가 침해 주장 제품을 판매하지 못하도록 하는 임시 명령을 받았다."},
    {"situation": "건설 계약 분쟁 및 공사 중단", "en": "The court granted an interlocutory relief to halt construction pending a full hearing on the contract dispute.", "ko": "법원은 계약 분쟁에 대한 완전한 심리가 열릴 때까지 공사를 중단시키는 임시 구제를 허가했다."},
    {"situation": "가족법 및 이혼 절차", "en": "An interlocutory order for maintenance was granted to provide financial support to the spouse during divorce proceedings.", "ko": "이혼 절차 중 배우자에게 재정 지원을 제공하기 위한 임시 부양료 명령이 내려졌다."},
    {"situation": "국제 중재 및 긴급 조치", "en": "Parties to arbitration may seek interlocutory measures from a court if the arbitral tribunal has not yet been constituted.", "ko": "중재 당사자들은 중재 재판소가 아직 구성되지 않은 경우 법원에 임시 조치를 신청할 수 있다."},
    {"situation": "환경 소송 및 긴급 금지 명령", "en": "Environmental lawyers secured an interlocutory injunction halting mining operations pending an environmental impact assessment.", "ko": "환경 변호사들은 환경 영향 평가가 진행되는 동안 광산 작업을 중단시키는 임시 금지 명령을 확보했다."},
    {"situation": "데이터 보호 및 규제 집행", "en": "The regulator applied for interlocutory relief to freeze the company's data processing activities during an investigation.", "ko": "규제 당국은 조사 중 회사의 데이터 처리 활동을 동결하기 위한 임시 구제를 신청했다."},
    {"situation": "회사법 및 주주 분쟁", "en": "Minority shareholders applied for an interlocutory order preventing the majority from passing a dilutive resolution.", "ko": "소수 주주들은 다수주주가 희석적 결의를 통과시키지 못하도록 하는 임시 명령을 신청했다."},
    {"situation": "스포츠법 및 선수 자격 정지", "en": "The athlete obtained an interlocutory ruling suspending the doping ban pending full arbitration proceedings.", "ko": "선수는 완전한 중재 절차가 진행되는 동안 도핑 금지 조치를 정지하는 임시 결정을 받았다."}
]

count = 0
for w in data7['words']:
    if w['word'] in R:
        w['examples'] = R[w['word']]
        count += 1
print(f"Updated {count} words")
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', 'w', encoding='utf-8') as f:
    json.dump(data7, f, ensure_ascii=False, indent=2)
print("Saved ielts_7.json batch 4")
