// Batch 4: IDs 47,50,51,52,55,56,57,58,59,60
// candor->customer retention, carve-out->vendor management, caveat->non-compete clause
// cease and desist->supply chain optimization, circumvent->workforce planning, class action->initial public offering
// clawback->equity compensation, coalesce->consolidate, coercive->net promoter score, coherent->lead generation
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 47,
    word: "customer retention",
    pronunciation: "ˈkʌs.tə.mər rɪˈten.ʃən",
    pos: "n.",
    meaning: "고객 유지, 고객 리텐션",
    synonyms: ["client retention", "customer loyalty", "churn reduction"],
    examples: [
      { situation: "영업팀 전략 회의에서", en: "Customer retention is more cost-effective than acquisition, costing five times less on average.", ko: "고객 유지는 평균적으로 5배 더 저렴해 고객 확보보다 비용 효율이 높아요." },
      { situation: "구독 서비스 비즈니스를 운영할 때", en: "Our subscription model achieved a 92 percent customer retention rate in the first year after launch.", ko: "우리의 구독 모델은 출시 첫해에 92%의 고객 유지율을 달성했어요." },
      { situation: "고객 성공팀 목표를 설정할 때", en: "The customer success team is responsible for driving customer retention through proactive support and check-ins.", ko: "고객 성공팀은 선제적 지원과 점검을 통해 고객 유지를 촉진할 책임이 있어요." },
      { situation: "이탈 원인을 분석할 때", en: "Analyzing churn patterns helped us identify the key drivers of customer retention in each market segment.", ko: "이탈 패턴을 분석하면서 각 시장 세그먼트에서 고객 유지의 핵심 동인을 파악할 수 있었어요." },
      { situation: "CRM 시스템을 활용할 때", en: "Our CRM system tracks customer retention metrics and flags accounts at risk of cancellation 30 days in advance.", ko: "CRM 시스템은 고객 유지 지표를 추적하고 해지 위험 계정을 30일 전에 표시해요." },
      { situation: "로열티 프로그램을 설계할 때", en: "Introducing a tiered loyalty program increased customer retention among our highest-value accounts by 18 percent.", ko: "계층화된 로열티 프로그램을 도입해 최고 가치 계정의 고객 유지가 18% 증가했어요." },
      { situation: "연간 전략 계획을 수립할 때", en: "This year our growth strategy shifts focus toward customer retention rather than new customer acquisition.", ko: "올해 성장 전략은 신규 고객 확보보다 고객 유지에 집중하는 방향으로 전환돼요." },
      { situation: "제품 개선 우선순위를 결정할 때", en: "Product roadmap decisions are increasingly driven by customer retention data rather than just feature requests.", ko: "제품 로드맵 결정은 단순한 기능 요청이 아닌 고객 유지 데이터에 의해 점점 더 많이 주도돼요." },
      { situation: "영업 인센티브 구조를 설계할 때", en: "We restructured sales commissions to reward customer retention alongside new business development.", ko: "신규 사업 개발과 함께 고객 유지에도 보상하도록 영업 커미션을 재구성했어요." },
      { situation: "고객 피드백을 수집할 때", en: "Regular net promoter score surveys are an essential tool for monitoring customer retention health.", ko: "정기적인 순추천지수 설문은 고객 유지 상태를 모니터링하는 필수 도구예요." }
    ],
    level: "800"
  },
  {
    id: 50,
    word: "vendor management",
    pronunciation: "ˈven.dər ˈmæn.ɪdʒ.mənt",
    pos: "n.",
    meaning: "공급업체 관리",
    synonyms: ["supplier management", "third-party management", "procurement management"],
    examples: [
      { situation: "조달팀 업무를 설명할 때", en: "Effective vendor management ensures that suppliers deliver quality goods and services on time and within budget.", ko: "효과적인 공급업체 관리는 공급업체가 기한 내에 예산 내에서 품질 좋은 제품과 서비스를 납품하도록 해요." },
      { situation: "공급업체 성과를 평가할 때", en: "Our vendor management system scores each supplier quarterly on delivery performance, quality, and responsiveness.", ko: "공급업체 관리 시스템은 각 공급업체를 납품 성과, 품질, 대응성에 대해 분기별로 점수를 매겨요." },
      { situation: "IT 아웃소싱 위험을 관리할 때", en: "Centralizing vendor management for IT services reduced contract redundancies and lowered total spend by 12 percent.", ko: "IT 서비스 공급업체 관리를 중앙화하면서 계약 중복이 줄고 총 지출이 12% 감소했어요." },
      { situation: "규제 컴플라이언스를 점검할 때", en: "Our vendor management policy requires all third-party suppliers to complete an annual compliance assessment.", ko: "공급업체 관리 정책은 모든 제3자 공급업체가 연간 컴플라이언스 평가를 완료하도록 요구해요." },
      { situation: "구매 전략을 수립할 때", en: "Consolidating vendor management by reducing our supplier base from 120 to 50 achieved significant cost savings.", ko: "공급업체 기반을 120개에서 50개로 줄여 공급업체 관리를 통합하면서 상당한 비용 절감이 이루어졌어요." },
      { situation: "공급망 위험을 점검할 때", en: "Vendor management includes regular business continuity assessments to evaluate supplier resilience.", ko: "공급업체 관리에는 공급업체 탄력성을 평가하기 위한 정기적인 사업 연속성 평가가 포함돼요." },
      { situation: "신규 공급업체를 심사할 때", en: "The vendor management team conducts a thorough due diligence process before onboarding any new supplier.", ko: "공급업체 관리팀은 신규 공급업체를 온보딩하기 전에 철저한 실사 프로세스를 수행해요." },
      { situation: "공급업체 계약을 갱신할 때", en: "Annual vendor management reviews provide an opportunity to renegotiate terms and align on future expectations.", ko: "연간 공급업체 관리 검토는 조건을 재협상하고 미래 기대치를 조율할 기회를 제공해요." },
      { situation: "디지털 조달 플랫폼을 도입할 때", en: "Implementing a vendor management portal improved transparency and reduced invoice processing time significantly.", ko: "공급업체 관리 포털을 도입하면서 투명성이 향상되고 청구서 처리 시간이 크게 단축됐어요." },
      { situation: "ESG 목표를 공급망에 적용할 때", en: "Our vendor management framework now includes sustainability criteria to align suppliers with our ESG commitments.", ko: "공급업체 관리 프레임워크에 이제 공급업체를 ESG 약속에 맞추기 위한 지속 가능성 기준이 포함돼요." }
    ],
    level: "800"
  },
  {
    id: 51,
    word: "non-compete clause",
    pronunciation: "nɒn kəmˈpiːt klɔːz",
    pos: "n.",
    meaning: "경업 금지 조항",
    synonyms: ["non-competition agreement", "restrictive covenant", "exclusivity clause"],
    examples: [
      { situation: "임원 고용 계약을 협상할 때", en: "The employment contract includes a non-compete clause restricting the executive from joining a direct competitor for 12 months.", ko: "고용 계약에는 임원이 12개월간 직접 경쟁업체에 합류하는 것을 제한하는 경업 금지 조항이 포함돼요." },
      { situation: "M&A 계약서를 검토할 때", en: "The acquisition agreement includes a three-year non-compete clause binding all founding members of the target company.", ko: "인수 계약서에는 피인수 기업의 모든 창립 멤버를 구속하는 3년의 경업 금지 조항이 포함돼요." },
      { situation: "영업 직원 계약을 작성할 때", en: "Sales staff in sensitive roles are required to sign a non-compete clause covering the territories they manage.", ko: "민감한 역할의 영업 직원들은 자신이 관리하는 지역을 다루는 경업 금지 조항에 서명해야 해요." },
      { situation: "법무팀 계약 검토에서", en: "Our legal team reviewed the non-compete clause to ensure it is reasonable in scope, geography, and duration.", ko: "법무팀은 경업 금지 조항이 범위, 지역, 기간에서 합리적인지 확인하기 위해 검토했어요." },
      { situation: "프랜차이즈 계약을 체결할 때", en: "Franchise agreements typically include a non-compete clause preventing franchisees from operating rival businesses.", ko: "프랜차이즈 계약은 일반적으로 가맹점이 경쟁 사업을 운영하는 것을 방지하는 경업 금지 조항을 포함해요." },
      { situation: "퇴직 직원과 분쟁이 생겼을 때", en: "The company filed a legal claim against the former employee for violating the non-compete clause.", ko: "회사는 경업 금지 조항 위반으로 전 직원을 상대로 법적 청구를 제기했어요." },
      { situation: "HR 정책을 직원에게 설명할 때", en: "All new hires in product development are informed of the non-compete clause during the onboarding process.", ko: "제품 개발 부서의 모든 신입 직원들은 온보딩 과정에서 경업 금지 조항에 대해 안내받아요." },
      { situation: "컨설팅 계약을 체결할 때", en: "The consulting agreement contains a non-compete clause preventing the consultant from working with our direct competitors.", ko: "컨설팅 계약에는 컨설턴트가 직접 경쟁업체와 일하는 것을 방지하는 경업 금지 조항이 포함돼요." },
      { situation: "기업 인수 후 인력 관리를 할 때", en: "Key technical staff from the acquired company signed extended non-compete clauses as part of the retention package.", ko: "인수된 회사의 핵심 기술 직원들은 리텐션 패키지의 일환으로 연장된 경업 금지 조항에 서명했어요." },
      { situation: "계약 조건 협상에서", en: "The candidate negotiated a reduction in the non-compete clause from 24 months to 12 months before accepting the offer.", ko: "지원자는 제안을 수락하기 전에 경업 금지 조항을 24개월에서 12개월로 줄이는 협상을 했어요." }
    ],
    level: "800"
  },
  {
    id: 52,
    word: "supply chain optimization",
    pronunciation: "səˈplaɪ tʃeɪn ˌɒp.tɪ.maɪˈzeɪ.ʃən",
    pos: "n.",
    meaning: "공급망 최적화",
    synonyms: ["supply chain improvement", "logistics optimization", "procurement optimization"],
    examples: [
      { situation: "운영 효율화 프로젝트에서", en: "Supply chain optimization reduced our average delivery lead time from 14 days to 7 days.", ko: "공급망 최적화로 평균 납품 리드 타임이 14일에서 7일로 줄었어요." },
      { situation: "비용 절감 이니셔티브를 발표할 때", en: "The supply chain optimization program is expected to generate annual savings of five million dollars.", ko: "공급망 최적화 프로그램은 연간 500만 달러의 절감을 창출할 것으로 예상돼요." },
      { situation: "디지털 전환 전략에서", en: "Leveraging data analytics is central to our supply chain optimization efforts.", ko: "데이터 분석 활용이 우리의 공급망 최적화 노력의 핵심이에요." },
      { situation: "공급업체 관계를 검토할 때", en: "Supply chain optimization often involves consolidating the supplier base to improve negotiating power.", ko: "공급망 최적화는 종종 협상력을 높이기 위해 공급업체 기반을 통합하는 것을 포함해요." },
      { situation: "재고 관리를 개선할 때", en: "Just-in-time inventory practices are a key component of supply chain optimization.", ko: "적시 재고 관리 방식은 공급망 최적화의 핵심 요소예요." },
      { situation: "글로벌 공급망 위험을 분석할 때", en: "Post-pandemic supply chain optimization focused on building redundancy to avoid single-source dependency.", ko: "팬데믹 이후 공급망 최적화는 단일 공급원 의존을 피하기 위해 여유 용량을 구축하는 데 초점을 맞췄어요." },
      { situation: "물류 파트너를 평가할 때", en: "The operations team benchmarked logistics partners as part of the supply chain optimization review.", ko: "운영팀은 공급망 최적화 검토의 일환으로 물류 파트너들을 벤치마크했어요." },
      { situation: "제조 공정을 개선할 때", en: "Supply chain optimization in manufacturing helped reduce raw material waste by 22 percent.", ko: "제조 분야의 공급망 최적화로 원자재 낭비가 22% 줄었어요." },
      { situation: "이사회 전략 발표에서", en: "Supply chain optimization is one of three strategic priorities the CEO outlined for the next fiscal year.", ko: "공급망 최적화는 CEO가 다음 회계연도를 위해 제시한 세 가지 전략적 우선순위 중 하나예요." },
      { situation: "고객 서비스 개선을 논의할 때", en: "Supply chain optimization directly improved customer satisfaction by ensuring products were always in stock.", ko: "공급망 최적화는 제품이 항상 재고에 있도록 함으로써 고객 만족도를 직접적으로 향상시켰어요." }
    ],
    level: "800"
  },
  {
    id: 55,
    word: "workforce planning",
    pronunciation: "ˈwɜːk.fɔːs ˈplæn.ɪŋ",
    pos: "n.",
    meaning: "인력 계획",
    synonyms: ["headcount planning", "staffing planning", "human resource planning"],
    examples: [
      { situation: "연간 HR 전략을 수립할 때", en: "Workforce planning ensures the business has the right people in the right roles at the right time.", ko: "인력 계획은 사업이 적절한 시기에 적합한 직위에 올바른 사람들을 갖추도록 해요." },
      { situation: "사업 확장 계획을 지원할 때", en: "The new market entry requires detailed workforce planning to identify hiring needs across all functions.", ko: "신규 시장 진출은 모든 기능에 걸친 채용 필요를 파악하기 위한 상세한 인력 계획을 필요로 해요." },
      { situation: "예산 편성 과정에서", en: "Workforce planning data is essential for forecasting the personnel budget for the upcoming fiscal year.", ko: "인력 계획 데이터는 다음 회계연도의 인건비 예산을 예측하는 데 필수적이에요." },
      { situation: "기술 변화에 대응할 때", en: "Automation is reshaping workforce planning by reducing demand for routine tasks and increasing need for digital skills.", ko: "자동화는 루틴 업무에 대한 수요를 줄이고 디지털 기술에 대한 필요를 높임으로써 인력 계획을 재편하고 있어요." },
      { situation: "장기 성장 전략을 수립할 때", en: "Long-term workforce planning identified a potential skills gap in cybersecurity that needed to be addressed by 2027.", ko: "장기 인력 계획은 2027년까지 해결해야 할 사이버 보안 분야의 잠재적 기술 격차를 파악했어요." },
      { situation: "이사회에 인력 현황을 보고할 때", en: "The CHRO presented a comprehensive workforce planning report covering talent supply, demand, and gap analysis.", ko: "CHRO는 인재 공급, 수요, 격차 분석을 다루는 포괄적인 인력 계획 보고서를 발표했어요." },
      { situation: "계절적 사업 변동을 준비할 때", en: "Workforce planning for the holiday season begins in September to ensure adequate staffing across all locations.", ko: "모든 매장의 적절한 인력 배치를 보장하기 위해 연말 성수기 인력 계획은 9월에 시작돼요." },
      { situation: "컨설팅 프로젝트를 운영할 때", en: "Effective workforce planning in a consulting firm requires aligning staff availability with projected client demand.", ko: "컨설팅 회사에서 효과적인 인력 계획은 직원 가용성을 예상 고객 수요와 조율하는 것을 필요로 해요." },
      { situation: "인수 후 통합을 진행할 때", en: "Post-acquisition workforce planning identified duplicate roles across the two organizations.", ko: "인수 후 인력 계획은 두 조직에 걸친 중복 역할을 파악했어요." },
      { situation: "HR 기술 도구를 도입할 때", en: "We invested in workforce planning software to model various headcount scenarios for the board.", ko: "이사회를 위한 다양한 인원수 시나리오를 모델링하기 위해 인력 계획 소프트웨어에 투자했어요." }
    ],
    level: "800"
  },
  {
    id: 56,
    word: "initial public offering",
    pronunciation: "ɪˈnɪʃ.əl ˈpʌb.lɪk ˈɒf.ər.ɪŋ",
    pos: "n.",
    meaning: "기업 공개, IPO",
    synonyms: ["IPO", "stock market listing", "public float"],
    examples: [
      { situation: "회사 상장 준비를 할 때", en: "The company filed for an initial public offering after three consecutive years of profitability.", ko: "회사는 3년 연속 수익을 올린 후 기업 공개 신청을 했어요." },
      { situation: "투자 은행을 선택할 때", en: "We appointed two investment banks as lead underwriters to manage the initial public offering process.", ko: "기업 공개 프로세스를 관리하기 위해 두 투자 은행을 주관 인수업자로 지정했어요." },
      { situation: "직원들에게 주식 옵션을 설명할 때", en: "Employees who hold stock options will benefit significantly if the initial public offering is priced above expectations.", ko: "주식 옵션을 보유한 직원들은 기업 공개 가격이 기대치를 상회하면 상당한 혜택을 받게 돼요." },
      { situation: "IPO 로드쇼를 준비할 때", en: "The CEO and CFO spent two weeks on a global roadshow to pitch the initial public offering to institutional investors.", ko: "CEO와 CFO는 기관 투자자들에게 기업 공개를 홍보하기 위해 2주간 글로벌 로드쇼를 진행했어요." },
      { situation: "이사회 전략 결정을 논의할 때", en: "The board debated the timing of the initial public offering, weighing market conditions against the need for growth capital.", ko: "이사회는 성장 자본 필요성과 시장 상황을 고려해 기업 공개 시기를 논의했어요." },
      { situation: "법적 실사 과정에서", en: "The initial public offering prospectus must disclose all material risks, financial statements, and management information.", ko: "기업 공개 투자 설명서는 모든 중요한 위험, 재무제표, 경영진 정보를 공시해야 해요." },
      { situation: "벤처 자본가와의 미팅에서", en: "Venture capital investors were looking forward to the initial public offering as their primary exit strategy.", ko: "벤처 자본 투자자들은 기업 공개를 주요 출구 전략으로 기대하고 있었어요." },
      { situation: "상장 후 주가를 분석할 때", en: "The shares rose 40 percent on the first day of trading following a successful initial public offering.", ko: "성공적인 기업 공개에 이어 첫 거래일에 주가가 40% 상승했어요." },
      { situation: "공시 의무를 설명할 때", en: "After the initial public offering, the company became subject to quarterly earnings reporting and enhanced disclosure obligations.", ko: "기업 공개 이후 회사는 분기별 실적 보고 및 강화된 공시 의무를 지게 됐어요." },
      { situation: "직원 주식 배정 계획을 논의할 때", en: "An employee stock allocation program was created to allow staff to participate in the initial public offering.", ko: "직원들이 기업 공개에 참여할 수 있도록 직원 주식 배정 프로그램이 만들어졌어요." }
    ],
    level: "800"
  },
  {
    id: 57,
    word: "equity compensation",
    pronunciation: "ˈek.wɪ.ti ˌkɒm.penˈseɪ.ʃən",
    pos: "n.",
    meaning: "주식 보상",
    synonyms: ["stock compensation", "share-based pay", "equity incentive"],
    examples: [
      { situation: "임원 보상 패키지를 설계할 때", en: "Equity compensation aligns executive interests with long-term shareholder value creation.", ko: "주식 보상은 임원의 이해관계를 장기적인 주주 가치 창출과 일치시켜요." },
      { situation: "스타트업 직원 혜택을 설명할 때", en: "The startup offered competitive equity compensation to attract senior engineers despite a modest cash salary.", ko: "스타트업은 적은 현금 급여에도 시니어 엔지니어를 유치하기 위해 경쟁력 있는 주식 보상을 제공했어요." },
      { situation: "직원에게 옵션 베스팅 일정을 설명할 때", en: "Equity compensation typically vests over four years with a one-year cliff to encourage employee retention.", ko: "주식 보상은 일반적으로 직원 유지를 장려하기 위해 1년 클리프와 함께 4년에 걸쳐 귀속돼요." },
      { situation: "이사회에 보상 체계를 발표할 때", en: "The compensation committee approved an equity compensation plan that grants restricted stock units to key managers.", ko: "보상 위원회는 핵심 관리자들에게 양도 제한 조건부 주식을 부여하는 주식 보상 계획을 승인했어요." },
      { situation: "세금 효과를 설명할 때", en: "Employees should consult a tax advisor to understand the tax implications of their equity compensation grants.", ko: "직원들은 주식 보상 부여의 세금 영향을 이해하기 위해 세무사에게 상담해야 해요." },
      { situation: "인재 유치 전략을 논의할 때", en: "In the tech industry, equity compensation is often the deciding factor for candidates choosing between competing offers.", ko: "기술 업계에서 주식 보상은 종종 경쟁 제안 중에서 선택하는 후보자에게 결정적인 요소가 돼요." },
      { situation: "IPO 전후 보상 전략을 계획할 때", en: "Post-IPO equity compensation packages were redesigned to reflect the new public company constraints.", ko: "IPO 이후 주식 보상 패키지는 새로운 상장 회사의 제약을 반영하도록 재설계됐어요." },
      { situation: "글로벌 인재를 관리할 때", en: "Administering equity compensation across multiple jurisdictions requires careful compliance with local securities laws.", ko: "여러 관할권에 걸친 주식 보상 관리는 현지 증권법을 철저히 준수하는 것을 필요로 해요." },
      { situation: "M&A 협상에서", en: "The merger agreement addressed how outstanding equity compensation grants would be treated upon closing.", ko: "합병 계약은 마감 시 미지급 주식 보상 부여를 어떻게 처리할지 다루었어요." },
      { situation: "직원 재무 교육을 진행할 때", en: "We hold annual financial literacy workshops to help employees maximize the value of their equity compensation.", ko: "직원들이 주식 보상의 가치를 극대화할 수 있도록 연간 재무 교육 워크숍을 개최해요." }
    ],
    level: "800"
  },
  {
    id: 58,
    word: "consolidate",
    pronunciation: "kənˈsɒl.ɪ.deɪt",
    pos: "v.",
    meaning: "통합하다, 합병하다",
    synonyms: ["merge", "combine", "integrate"],
    examples: [
      { situation: "사업부를 합치는 전략을 논의할 때", en: "The company decided to consolidate its three regional offices into one national headquarters.", ko: "회사는 세 개의 지역 사무소를 하나의 전국 본부로 통합하기로 결정했어요." },
      { situation: "재무 보고서를 작성할 때", en: "The group finance team consolidated the financial statements of all 12 subsidiaries for the annual report.", ko: "그룹 재무팀은 연간 보고서를 위해 12개 자회사 전체의 재무제표를 통합했어요." },
      { situation: "공급업체 기반을 줄일 때", en: "We plan to consolidate our vendor relationships from 80 suppliers to 30 to improve efficiency and reduce costs.", ko: "효율성을 높이고 비용을 절감하기 위해 공급업체 관계를 80개에서 30개로 통합할 계획이에요." },
      { situation: "IT 인프라를 단순화할 때", en: "Consolidating onto a single cloud platform eliminated the complexity of managing multiple data centers.", ko: "단일 클라우드 플랫폼으로 통합하면서 여러 데이터 센터 관리의 복잡성이 제거됐어요." },
      { situation: "부채를 재구성할 때", en: "We consolidated all outstanding loans into a single term facility at a lower blended interest rate.", ko: "모든 미상환 대출을 더 낮은 혼합 금리의 단일 기간 대출로 통합했어요." },
      { situation: "시장에서 강한 위치를 차지할 때", en: "The acquisition allowed us to consolidate our position as the market leader in the Southeast Asian region.", ko: "인수를 통해 동남아시아 지역에서 시장 선도자로서의 지위를 공고히 할 수 있었어요." },
      { situation: "프로젝트 팀을 구성할 때", en: "Consolidating the project teams from both legacy organizations accelerated the integration timeline significantly.", ko: "두 레거시 조직의 프로젝트팀을 통합하면서 통합 일정이 크게 앞당겨졌어요." },
      { situation: "브랜드 포트폴리오를 정리할 때", en: "The marketing strategy was to consolidate the brand portfolio from six labels down to two flagship brands.", ko: "마케팅 전략은 브랜드 포트폴리오를 여섯 개 레이블에서 두 개의 주력 브랜드로 통합하는 것이었어요." },
      { situation: "비용 절감 계획을 실행할 때", en: "Consolidating procurement across divisions generated negotiating leverage and reduced total spend by 18 percent.", ko: "사업부 전반에 걸쳐 조달을 통합하면서 협상력이 생겨 총 지출이 18% 감소했어요." },
      { situation: "성장 후 안정화 단계에서", en: "After rapid expansion, the company entered a phase to consolidate its gains and improve profitability.", ko: "급격한 확장 이후 회사는 성과를 공고히 하고 수익성을 개선하는 단계에 진입했어요." }
    ],
    level: "800"
  },
  {
    id: 59,
    word: "net promoter score",
    pronunciation: "net prəˈməʊ.tər skɔːr",
    pos: "n.",
    meaning: "순추천지수, NPS",
    synonyms: ["NPS", "customer loyalty score", "customer advocacy metric"],
    examples: [
      { situation: "고객 만족도를 측정할 때", en: "Our net promoter score increased from 42 to 67 after we launched the new customer support platform.", ko: "새로운 고객 지원 플랫폼을 출시한 후 순추천지수가 42에서 67로 증가했어요." },
      { situation: "분기 비즈니스 리뷰에서", en: "The customer experience team presents net promoter score trends at every quarterly business review.", ko: "고객 경험팀은 매분기 비즈니스 리뷰에서 순추천지수 추세를 발표해요." },
      { situation: "제품 개선 우선순위를 설정할 때", en: "Low net promoter score responses are analyzed to identify which product issues require immediate attention.", ko: "낮은 순추천지수 응답을 분석해 즉각적인 주의가 필요한 제품 문제를 파악해요." },
      { situation: "경쟁사와 벤치마킹할 때", en: "Our net promoter score of 58 is well above the industry average of 32, indicating strong customer loyalty.", ko: "우리의 순추천지수 58은 업계 평균 32를 크게 상회해 강한 고객 충성도를 나타내요." },
      { situation: "영업팀 성과를 평가할 때", en: "Account managers are evaluated in part on the net promoter score of their assigned customer portfolio.", ko: "고객 담당 매니저들은 부분적으로 배정된 고객 포트폴리오의 순추천지수를 기준으로 평가받아요." },
      { situation: "고객 이탈을 예측할 때", en: "Customers who give a net promoter score of 6 or below are flagged for immediate retention outreach.", ko: "순추천지수 6점 이하를 준 고객들은 즉각적인 리텐션 연락을 위해 표시돼요." },
      { situation: "서비스 품질 개선을 추적할 때", en: "Monthly net promoter score tracking helps us spot emerging service quality issues before they escalate.", ko: "월별 순추천지수 추적은 문제가 심화되기 전에 새로운 서비스 품질 문제를 발견하는 데 도움이 돼요." },
      { situation: "투자자에게 고객 지표를 보고할 때", en: "Investors view net promoter score as a leading indicator of future revenue growth and customer lifetime value.", ko: "투자자들은 순추천지수를 미래 매출 성장과 고객 생애 가치의 선행 지표로 봐요." },
      { situation: "고객 경험 팀을 평가할 때", en: "The net promoter score improved by 15 points following the rollout of the new self-service support portal.", ko: "새 셀프 서비스 지원 포털 출시 후 순추천지수가 15점 향상됐어요." },
      { situation: "이사회에 사업 현황을 보고할 때", en: "The board monitors net promoter score alongside revenue and operating margin as a key indicator of business health.", ko: "이사회는 사업 건전성의 핵심 지표로 매출 및 영업이익률과 함께 순추천지수를 모니터링해요." }
    ],
    level: "800"
  },
  {
    id: 60,
    word: "lead generation",
    pronunciation: "liːd ˌdʒen.əˈreɪ.ʃən",
    pos: "n.",
    meaning: "리드 발굴, 잠재 고객 확보",
    synonyms: ["prospect development", "demand generation", "pipeline building"],
    examples: [
      { situation: "영업팀 목표를 설정할 때", en: "The marketing team is responsible for lead generation, while sales is responsible for conversion.", ko: "마케팅팀은 리드 발굴을, 영업팀은 전환을 담당해요." },
      { situation: "디지털 마케팅 전략을 수립할 때", en: "Content marketing has become our most cost-effective lead generation channel, contributing 40 percent of qualified leads.", ko: "콘텐츠 마케팅이 적격 리드의 40%를 기여하며 가장 비용 효율적인 리드 발굴 채널이 됐어요." },
      { situation: "영업 파이프라인을 분석할 때", en: "Insufficient lead generation in Q2 is the primary reason for the forecasted revenue shortfall in Q4.", ko: "2분기의 불충분한 리드 발굴이 4분기 매출 부족 예측의 주요 원인이에요." },
      { situation: "마케팅 자동화를 도입할 때", en: "Marketing automation tools significantly improved our lead generation efficiency and reduced cost per lead.", ko: "마케팅 자동화 도구가 리드 발굴 효율성을 크게 높이고 리드당 비용을 줄였어요." },
      { situation: "전시회 참가를 계획할 때", en: "Industry trade shows remain an important lead generation activity for our enterprise sales team.", ko: "업계 무역 박람회는 기업 영업팀을 위한 중요한 리드 발굴 활동으로 남아 있어요." },
      { situation: "영업과 마케팅 협업을 강화할 때", en: "Aligning sales and marketing on lead generation criteria improves conversion rates and reduces wasted effort.", ko: "영업과 마케팅이 리드 발굴 기준을 맞추면 전환율이 높아지고 낭비되는 노력이 줄어요." },
      { situation: "CRM 시스템을 활용할 때", en: "Our CRM tracks every lead generation source so we can calculate the ROI of each marketing channel.", ko: "CRM은 각 마케팅 채널의 ROI를 계산할 수 있도록 모든 리드 발굴 소스를 추적해요." },
      { situation: "B2B 영업 전략을 논의할 때", en: "LinkedIn campaigns have proven to be the most effective lead generation tool for targeting C-suite decision makers.", ko: "링크드인 캠페인은 C레벨 의사 결정자를 대상으로 하는 가장 효과적인 리드 발굴 도구임이 입증됐어요." },
      { situation: "영업 인력 확충 계획을 논의할 때", en: "Hiring additional business development representatives will scale our outbound lead generation capacity.", ko: "사업 개발 담당자를 추가 채용하면 아웃바운드 리드 발굴 역량이 확장될 거예요." },
      { situation: "예산 배분을 결정할 때", en: "We are shifting 20 percent of the advertising budget toward lead generation to build a stronger pipeline.", ko: "더 강한 파이프라인을 구축하기 위해 광고 예산의 20%를 리드 발굴로 전환하고 있어요." }
    ],
    level: "800"
  }
];

const idMap = {};
newEntries.forEach(e => { idMap[e.id] = e; });

data.words = data.words.map(w => {
  if (idMap[w.id]) return idMap[w.id];
  return w;
});

fs.writeFileSync('toeic_800.json', JSON.stringify(data, null, 2), 'utf8');
console.log('Batch 4 done: IDs 47,50,51,52,55,56,57,58,59,60 replaced.');
