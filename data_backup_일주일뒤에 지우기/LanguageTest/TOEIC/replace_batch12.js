// Batch 12: IDs 230,231,232,233,240,241,243,244,249,250
// quantum->account management, quid pro quo->upselling, rationale->cross-selling
// recapitalization->pipeline management, relinquish->lease agreement, remuneration->operating leverage
// repudiate->property management, rescission->net 30, retrospective->net 60, right of first refusal->interest rate swap
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 230,
    word: "account management",
    pronunciation: "əˈkaʊnt ˈmæn.ɪdʒ.mənt",
    pos: "n.",
    meaning: "고객 관리, 계정 관리",
    synonyms: ["client management", "customer relationship management", "key account management"],
    examples: [
      { situation: "B2B 영업팀 역할을 설명할 때", en: "Strong account management builds long-term relationships that reduce customer churn and increase expansion revenue.", ko: "강한 고객 관리는 고객 이탈을 줄이고 확장 매출을 높이는 장기적 관계를 구축해요." },
      { situation: "고객 포트폴리오를 전략적으로 관리할 때", en: "Effective account management requires understanding each client business objectives and aligning solutions accordingly.", ko: "효과적인 고객 관리는 각 고객의 사업 목표를 이해하고 그에 맞게 솔루션을 조율하는 것을 필요로 해요." },
      { situation: "영업팀 구조를 설계할 때", en: "We separated account management from new business development to allow each team to focus on its core competency.", ko: "각 팀이 핵심 역량에 집중할 수 있도록 고객 관리를 신규 사업 개발과 분리했어요." },
      { situation: "고객 포트폴리오를 검토할 때", en: "The account management team conducts quarterly business reviews with all top-tier clients.", ko: "고객 관리팀은 모든 최상위 고객과 분기별 사업 검토를 실시해요." },
      { situation: "CRM 시스템 활용을 논의할 때", en: "Our CRM platform supports account management by tracking all interactions, contracts, and renewal dates.", ko: "CRM 플랫폼은 모든 상호작용, 계약, 갱신일을 추적함으로써 고객 관리를 지원해요." },
      { situation: "수익 확장 전략을 수립할 때", en: "Account management focuses on identifying upselling and cross-selling opportunities within the existing client base.", ko: "고객 관리는 기존 고객 기반 내에서 업셀링 및 크로스셀링 기회를 파악하는 데 집중해요." },
      { situation: "고객 리텐션 목표를 설정할 때", en: "Account management performance is measured on net revenue retention, which factors in both expansions and churn.", ko: "고객 관리 성과는 확장과 이탈 모두를 고려한 순 매출 유지율로 측정돼요." },
      { situation: "고객 불만을 해결할 때", en: "The account manager acted quickly to resolve the service issue before it escalated to a contract cancellation.", ko: "고객 관리자는 서비스 문제가 계약 취소로 확대되기 전에 신속하게 해결했어요." },
      { situation: "팀 교육을 계획할 때", en: "Account management training covers consultative selling, negotiation skills, and executive-level communication.", ko: "고객 관리 교육은 컨설팅형 영업, 협상 기술, 임원급 커뮤니케이션을 다뤄요." },
      { situation: "수익 예측을 수립할 때", en: "Accurate revenue forecasting requires account management teams to maintain up-to-date renewal and expansion pipelines.", ko: "정확한 매출 예측은 고객 관리팀이 최신 갱신 및 확장 파이프라인을 유지하도록 요구해요." }
    ],
    level: "800"
  },
  {
    id: 231,
    word: "upselling",
    pronunciation: "ˈʌp.sel.ɪŋ",
    pos: "n.",
    meaning: "업셀링, 상위 제품 판매 유도",
    synonyms: ["premium upgrade selling", "add-on selling", "value escalation selling"],
    examples: [
      { situation: "영업 전략 회의에서", en: "Upselling existing customers is more cost-effective than acquiring new ones, with five times better conversion rates.", ko: "기존 고객에게 업셀링하는 것은 신규 고객 획득보다 비용 효율적이며 전환율이 5배 더 높아요." },
      { situation: "고객 성공팀 목표를 설정할 때", en: "Our customer success team generates 30 percent of total revenue through upselling and account expansion.", ko: "고객 성공팀이 업셀링과 계정 확장을 통해 총 매출의 30%를 창출해요." },
      { situation: "제품 패키지 전략을 수립할 때", en: "Tiered pricing is designed to facilitate upselling by making the premium tier visually appealing and clearly better value.", ko: "계층화된 가격은 프리미엄 계층을 시각적으로 매력적이고 명확하게 더 나은 가치로 만들어 업셀링을 용이하게 하도록 설계돼요." },
      { situation: "영업팀 교육을 진행할 때", en: "Upselling training focuses on identifying moments when a customer is ready for a more comprehensive solution.", ko: "업셀링 교육은 고객이 더 포괄적인 솔루션을 받을 준비가 된 순간을 파악하는 데 집중해요." },
      { situation: "고객 온보딩 과정에서", en: "Customer onboarding is an opportunity for upselling additional features that address needs identified during setup.", ko: "고객 온보딩은 설정 중에 파악된 필요를 해결하는 추가 기능을 업셀링할 기회예요." },
      { situation: "레스토랑이나 서비스업 사례를 들 때", en: "The checkout upselling prompt offering an extended warranty increased attachment rate by 22 percent.", ko: "연장 보증을 제안하는 결제 업셀링 프롬프트가 부가 비율을 22% 높였어요." },
      { situation: "수익 모델을 분석할 때", en: "Upselling to a higher subscription tier accounts for 18 percent of our monthly recurring revenue growth.", ko: "더 높은 구독 계층으로의 업셀링이 월간 반복 매출 성장의 18%를 차지해요." },
      { situation: "영업 과정 적절한 타이밍을 설명할 때", en: "Upselling is most effective when it solves a genuine problem the customer is currently experiencing.", ko: "업셀링은 고객이 현재 겪고 있는 실제 문제를 해결할 때 가장 효과적이에요." },
      { situation: "CRM 도구를 활용할 때", en: "Our CRM flags upselling triggers when customers reach usage limits or request features in a higher tier.", ko: "CRM은 고객이 사용 한도에 도달하거나 더 높은 계층의 기능을 요청할 때 업셀링 트리거를 표시해요." },
      { situation: "팀 성과를 측정할 때", en: "Upselling revenue is tracked separately from new business to measure the effectiveness of account management efforts.", ko: "업셀링 매출은 고객 관리 노력의 효과를 측정하기 위해 신규 사업과 별도로 추적돼요." }
    ],
    level: "800"
  },
  {
    id: 232,
    word: "cross-selling",
    pronunciation: "ˈkrɒs.sel.ɪŋ",
    pos: "n.",
    meaning: "크로스셀링, 교차 판매",
    synonyms: ["complementary product selling", "bundle selling", "adjacent product selling"],
    examples: [
      { situation: "수익 성장 전략을 논의할 때", en: "Cross-selling complementary products to existing customers increased average order value by 25 percent.", ko: "기존 고객에게 보완적 제품을 크로스셀링하면서 평균 주문 금액이 25% 증가했어요." },
      { situation: "은행이나 금융 서비스를 설명할 때", en: "Banks are skilled at cross-selling by offering loan products to existing savings account holders.", ko: "은행은 기존 예금 계좌 보유자에게 대출 상품을 제안하는 크로스셀링에 능숙해요." },
      { situation: "고객 데이터를 활용할 때", en: "Data analytics enables intelligent cross-selling by predicting which products each customer is most likely to need next.", ko: "데이터 분석은 각 고객이 다음에 필요할 가능성이 가장 높은 제품을 예측함으로써 지능적인 크로스셀링을 가능하게 해요." },
      { situation: "영업팀 교육을 할 때", en: "Sales representatives are trained on cross-selling to ensure customers are aware of the full product portfolio.", ko: "영업 담당자들은 고객들이 전체 제품 포트폴리오를 인식할 수 있도록 크로스셀링에 대해 교육받아요." },
      { situation: "온라인 쇼핑 경험을 설계할 때", en: "The e-commerce platform shows cross-selling recommendations based on items currently in the shopping cart.", ko: "이커머스 플랫폼은 현재 장바구니에 있는 항목을 기반으로 크로스셀링 추천을 표시해요." },
      { situation: "파트너십 전략을 수립할 때", en: "Cross-selling between our insurance and investment products is a key driver of wallet share growth.", ko: "우리의 보험과 투자 상품 간의 크로스셀링이 지갑 점유율 성장의 핵심 동인이에요." },
      { situation: "고객 생애 가치를 높이려 할 때", en: "Effective cross-selling increases customer lifetime value by deepening product adoption and dependency.", ko: "효과적인 크로스셀링은 제품 채택 및 의존도를 심화함으로써 고객 생애 가치를 높여요." },
      { situation: "M&A 시너지를 설명할 때", en: "The merger creates significant cross-selling opportunities by combining two complementary product lines.", ko: "합병은 두 가지 보완적인 제품 라인을 결합함으로써 상당한 크로스셀링 기회를 창출해요." },
      { situation: "영업 보상 체계를 설계할 때", en: "The commission structure rewards cross-selling to encourage reps to introduce a broader range of solutions.", ko: "수수료 구조는 담당자들이 더 광범위한 솔루션을 소개하도록 장려하기 위해 크로스셀링에 보상해요." },
      { situation: "인수 후 통합을 논의할 때", en: "Post-acquisition cross-selling programs were launched within 90 days to realize synergies from the combined customer base.", ko: "결합된 고객 기반에서 시너지를 실현하기 위해 인수 후 90일 내에 크로스셀링 프로그램이 시작됐어요." }
    ],
    level: "800"
  },
  {
    id: 233,
    word: "pipeline management",
    pronunciation: "ˈpaɪp.laɪn ˈmæn.ɪdʒ.mənt",
    pos: "n.",
    meaning: "영업 파이프라인 관리",
    synonyms: ["sales pipeline management", "opportunity management", "deal pipeline oversight"],
    examples: [
      { situation: "영업팀 성과를 관리할 때", en: "Effective pipeline management ensures the team has enough qualified opportunities to consistently hit revenue targets.", ko: "효과적인 파이프라인 관리는 팀이 매출 목표를 지속적으로 달성하기에 충분한 적격 기회를 보유하도록 해요." },
      { situation: "CRM 도구를 활용할 때", en: "Our CRM supports pipeline management by providing real-time visibility into deal stage, size, and close probability.", ko: "CRM은 거래 단계, 규모, 성사 확률에 대한 실시간 가시성을 제공함으로써 파이프라인 관리를 지원해요." },
      { situation: "영업 예측을 수립할 때", en: "Accurate pipeline management enables finance to build reliable quarterly revenue forecasts.", ko: "정확한 파이프라인 관리는 재무 부서가 신뢰할 수 있는 분기별 매출 예측을 구축할 수 있게 해요." },
      { situation: "영업 코칭을 진행할 때", en: "Pipeline management reviews are held weekly so the sales manager can coach reps on deal progression tactics.", ko: "영업 관리자가 담당자에게 거래 진행 전술을 코칭할 수 있도록 파이프라인 관리 검토가 매주 진행돼요." },
      { situation: "파이프라인 커버리지를 분석할 때", en: "A healthy pipeline management ratio requires three times the quarterly revenue target in qualified opportunities.", ko: "건전한 파이프라인 관리 비율은 적격 기회에서 분기별 매출 목표의 3배를 필요로 해요." },
      { situation: "영업 주기를 단축하려 할 때", en: "Improving pipeline management by adding stage-specific exit criteria helped reduce our average sales cycle by 20 days.", ko: "단계별 이탈 기준을 추가해 파이프라인 관리를 개선하면서 평균 영업 주기가 20일 단축됐어요." },
      { situation: "거래 손실 분석을 할 때", en: "Pipeline management analysis showed that deals stalling in the proposal stage were the main cause of revenue shortfalls.", ko: "파이프라인 관리 분석에서 제안 단계에서 정체된 거래가 매출 부족의 주요 원인임을 보여줬어요." },
      { situation: "영업 자동화 도구를 도입할 때", en: "Automation tools improve pipeline management by eliminating manual data entry and surfacing at-risk deals.", ko: "자동화 도구는 수동 데이터 입력을 제거하고 위험한 거래를 표시함으로써 파이프라인 관리를 개선해요." },
      { situation: "다중 지역 영업을 조율할 때", en: "Global pipeline management requires consistent stage definitions and reporting standards across all regional teams.", ko: "글로벌 파이프라인 관리는 모든 지역 팀에 걸쳐 일관된 단계 정의와 보고 기준을 필요로 해요." },
      { situation: "이사회에 영업 건강성을 보고할 때", en: "Pipeline management dashboards give senior leadership real-time insight into sales health and forecast accuracy.", ko: "파이프라인 관리 대시보드는 고위 리더십에게 영업 건강성과 예측 정확도에 대한 실시간 인사이트를 제공해요." }
    ],
    level: "800"
  },
  {
    id: 240,
    word: "lease agreement",
    pronunciation: "liːs əˈɡriː.mənt",
    pos: "n.",
    meaning: "임대 계약",
    synonyms: ["rental agreement", "tenancy agreement", "leasing contract"],
    examples: [
      { situation: "사무실 공간을 확보할 때", en: "The company signed a five-year lease agreement for new office space in the central business district.", ko: "회사는 중심 업무 지구의 새로운 사무실 공간에 대한 5년 임대 계약에 서명했어요." },
      { situation: "임대 조건을 협상할 때", en: "The lease agreement was negotiated to include three months of rent-free period as a tenant improvement incentive.", ko: "임차인 개선 인센티브로 3개월 무임 기간을 포함하도록 임대 계약을 협상했어요." },
      { situation: "장비를 임대할 때", en: "An operating lease agreement for the new photocopiers was structured over 36 months with a buyout option.", ko: "새 복사기에 대한 운용 임대 계약은 매입 옵션을 포함해 36개월로 구성됐어요." },
      { situation: "부동산 비용을 분석할 때", en: "The lease agreement terms were reviewed as part of the cost reduction initiative to assess early termination options.", ko: "조기 종료 옵션을 평가하기 위해 비용 절감 이니셔티브의 일환으로 임대 계약 조건을 검토했어요." },
      { situation: "재무 보고를 준비할 때", en: "Under new accounting standards, all significant lease agreements must be recognized on the balance sheet.", ko: "새로운 회계 기준에 따라 모든 중요한 임대 계약은 대차대조표에 인식되어야 해요." },
      { situation: "사업 확장 계획을 세울 때", en: "Securing a lease agreement for the new warehouse was a prerequisite for launching the regional distribution center.", ko: "새 창고에 대한 임대 계약을 확보하는 것이 지역 유통 센터 출범의 선행 조건이었어요." },
      { situation: "퇴거 절차를 이행할 때", en: "The lease agreement outlines specific restoration requirements the tenant must fulfill before vacating the premises.", ko: "임대 계약은 임차인이 건물을 비우기 전에 이행해야 하는 구체적인 원상 복구 요건을 개요로 해요." },
      { situation: "비용 관리를 검토할 때", en: "Renegotiating the lease agreement saved the company 200,000 dollars annually in occupancy costs.", ko: "임대 계약을 재협상하면서 회사의 연간 점유 비용이 20만 달러 절약됐어요." },
      { situation: "임대 갱신을 준비할 때", en: "The facilities manager flagged the lease agreement expiration 12 months in advance to allow adequate time for negotiation.", ko: "시설 관리자는 협상을 위한 충분한 시간을 확보하기 위해 임대 계약 만료를 12개월 전에 표시했어요." },
      { situation: "M&A 실사를 진행할 때", en: "All lease agreements were reviewed during due diligence to assess change-of-control provisions and transfer rights.", ko: "변경 통제 조항과 양도 권리를 평가하기 위해 실사 중에 모든 임대 계약이 검토됐어요." }
    ],
    level: "800"
  },
  {
    id: 241,
    word: "operating leverage",
    pronunciation: "ˈɒp.ər.eɪ.tɪŋ ˈlev.ər.ɪdʒ",
    pos: "n.",
    meaning: "영업 레버리지",
    synonyms: ["operational leverage", "fixed cost leverage", "revenue scalability"],
    examples: [
      { situation: "수익성 분석을 할 때", en: "High operating leverage means that a small increase in revenue leads to a much larger increase in operating profit.", ko: "높은 영업 레버리지는 매출의 작은 증가가 영업이익의 훨씬 더 큰 증가로 이어진다는 것을 의미해요." },
      { situation: "사업 모델을 투자자에게 설명할 때", en: "Our SaaS business model has significant operating leverage because most costs are fixed infrastructure and R&D.", ko: "우리의 SaaS 비즈니스 모델은 대부분의 비용이 고정 인프라 및 R&D이기 때문에 상당한 영업 레버리지를 가지고 있어요." },
      { situation: "성장 전략의 경제성을 평가할 때", en: "As revenue scales, operating leverage allows margins to expand rapidly without proportional cost increases.", ko: "매출이 확장됨에 따라 영업 레버리지는 비례적인 비용 증가 없이 마진이 빠르게 확대되도록 해요." },
      { situation: "비용 구조를 분석할 때", en: "A company with high fixed costs has greater operating leverage, making it more sensitive to revenue fluctuations.", ko: "고정 비용이 높은 회사는 더 큰 영업 레버리지를 가지고 있어 매출 변동에 더 민감해요." },
      { situation: "제조업과 SaaS 비즈니스를 비교할 때", en: "Manufacturing companies typically have lower operating leverage than software companies due to variable cost structures.", ko: "제조 회사는 가변 비용 구조 때문에 소프트웨어 회사보다 일반적으로 낮은 영업 레버리지를 가져요." },
      { situation: "이사회에 이익 확장 계획을 설명할 때", en: "The CFO demonstrated that operating leverage would drive EBITDA margins from 20 to 35 percent by year four.", ko: "CFO는 영업 레버리지가 4년차까지 EBITDA 마진을 20%에서 35%로 높일 것임을 보여줬어요." },
      { situation: "경기 침체 위험을 평가할 때", en: "High operating leverage can amplify losses during revenue downturns, making contingency planning critical.", ko: "높은 영업 레버리지는 매출 감소 시 손실을 증폭시킬 수 있어 비상 계획이 중요해요." },
      { situation: "M&A 가치 창출을 분석할 때", en: "Acquiring a competitor creates operating leverage by spreading fixed costs over a larger combined revenue base.", ko: "경쟁사를 인수하면 더 큰 결합 매출 기반에 고정 비용을 분산시켜 영업 레버리지를 창출해요." },
      { situation: "성장 투자를 정당화할 때", en: "Investing in automation builds operating leverage by replacing variable labor costs with fixed technology costs.", ko: "자동화에 투자하면 가변적인 인건비를 고정 기술 비용으로 대체함으로써 영업 레버리지를 구축해요." },
      { situation: "재무 모델을 검토할 때", en: "The financial model shows that operating leverage kicks in at 70 percent of capacity utilization.", ko: "재무 모델은 영업 레버리지가 용량 활용도의 70%에서 시작된다는 것을 보여줘요." }
    ],
    level: "800"
  },
  {
    id: 243,
    word: "property management",
    pronunciation: "ˈprɒp.ə.ti ˈmæn.ɪdʒ.mənt",
    pos: "n.",
    meaning: "부동산 관리",
    synonyms: ["real estate management", "facilities management", "building management"],
    examples: [
      { situation: "사무실 운영을 관리할 때", en: "Outsourcing property management to a specialist firm freed up internal resources to focus on core business activities.", ko: "전문 회사에 부동산 관리를 아웃소싱하면서 내부 자원이 핵심 사업 활동에 집중할 수 있게 됐어요." },
      { situation: "투자 부동산을 운영할 때", en: "Good property management maximizes rental income while minimizing vacancy rates and maintenance costs.", ko: "좋은 부동산 관리는 공실률과 유지 비용을 최소화하면서 임대 수입을 극대화해요." },
      { situation: "임차인 관계를 유지할 때", en: "Responsive property management builds positive tenant relationships and improves lease renewal rates.", ko: "응답성 있는 부동산 관리는 긍정적인 임차인 관계를 구축하고 임대 갱신율을 높여요." },
      { situation: "건물 유지 보수를 계획할 때", en: "The property management company implemented a preventive maintenance schedule to reduce emergency repair costs.", ko: "부동산 관리 회사는 긴급 수리 비용을 줄이기 위해 예방적 유지 보수 일정을 구현했어요." },
      { situation: "법적 준수를 확보할 때", en: "Property management includes ensuring the building meets all health, safety, and fire regulation requirements.", ko: "부동산 관리에는 건물이 모든 보건, 안전, 소방 규정 요건을 충족하도록 하는 것이 포함돼요." },
      { situation: "비용 효율화를 논의할 때", en: "Centralizing property management across all 15 office locations generated significant economies of scale.", ko: "15개 사무실 위치 전반에 걸쳐 부동산 관리를 중앙화하면서 상당한 규모의 경제가 창출됐어요." },
      { situation: "부동산 포트폴리오를 평가할 때", en: "The investment committee reviewed the property management performance report before deciding on portfolio expansion.", ko: "투자 위원회는 포트폴리오 확장을 결정하기 전에 부동산 관리 성과 보고서를 검토했어요." },
      { situation: "임대 수익률을 개선할 때", en: "Upgrading common areas and amenities was recommended by the property management team to attract premium tenants.", ko: "프리미엄 임차인을 유치하기 위해 공용 구역과 편의 시설을 업그레이드하도록 부동산 관리팀이 권고했어요." },
      { situation: "입주자 서비스를 향상할 때", en: "Digital property management platforms improve tenant experience through online maintenance requests and payment portals.", ko: "디지털 부동산 관리 플랫폼은 온라인 유지 보수 요청 및 결제 포털을 통해 임차인 경험을 향상시켜요." },
      { situation: "환경 규제를 준수할 때", en: "Modern property management increasingly focuses on energy efficiency and sustainability to reduce operating costs.", ko: "현대의 부동산 관리는 운영 비용을 줄이기 위해 에너지 효율성과 지속 가능성에 점점 더 집중해요." }
    ],
    level: "800"
  },
  {
    id: 244,
    word: "net 30",
    pronunciation: "net θɜː.ti",
    pos: "n.",
    meaning: "결제 기한 30일, 넷 30",
    synonyms: ["30-day payment terms", "net 30 days", "payment due in 30 days"],
    examples: [
      { situation: "새 고객에게 청구서를 발행할 때", en: "All new accounts start on net 30 payment terms until a satisfactory payment history is established.", ko: "모든 신규 계정은 만족스러운 결제 이력이 수립될 때까지 결제 기한 30일 조건으로 시작해요." },
      { situation: "공급업체와 조건을 협상할 때", en: "The supplier offered a 2 percent discount for paying early, instead of the standard net 30 terms.", ko: "공급업체는 표준 결제 기한 30일 조건 대신 조기 결제 시 2% 할인을 제공했어요." },
      { situation: "청구서 발행 정책을 설명할 때", en: "Our standard invoice payment terms are net 30 from the date of delivery, not the invoice date.", ko: "표준 청구서 결제 조건은 청구서 날짜가 아닌 납품일로부터 결제 기한 30일이에요." },
      { situation: "현금 흐름 관리를 논의할 때", en: "Switching from net 30 to net 15 for small accounts improved our cash conversion cycle significantly.", ko: "소형 계정에 대해 결제 기한 30일에서 15일로 전환하면서 현금 전환 주기가 크게 개선됐어요." },
      { situation: "연체 계정을 관리할 때", en: "Accounts that consistently pay beyond net 30 are flagged for credit review and may face stricter terms.", ko: "결제 기한 30일을 지속적으로 초과하는 계정은 신용 검토를 위해 표시되고 더 엄격한 조건을 받을 수 있어요." },
      { situation: "대기업과 거래할 때", en: "Many large corporations impose net 30 payment terms on their suppliers regardless of the supplier preference.", ko: "많은 대기업들은 공급업체 선호도에 관계없이 공급업체에 결제 기한 30일 조건을 부과해요." },
      { situation: "팩토링 서비스를 이용할 때", en: "Invoice factoring converts net 30 receivables into immediate cash at a small discount.", ko: "청구서 팩토링은 소액 할인으로 결제 기한 30일 매출채권을 즉시 현금으로 전환해요." },
      { situation: "고객 신용 정책을 수립할 때", en: "The credit policy allows net 30 for established clients but requires advance payment from new or high-risk accounts.", ko: "신용 정책은 기존 고객에게 결제 기한 30일을 허용하지만 신규 또는 고위험 계정에는 선결제를 요구해요." },
      { situation: "계약서의 결제 조항을 검토할 때", en: "The service contract specifies net 30 payment terms and a 1.5 percent monthly late fee for overdue balances.", ko: "서비스 계약은 결제 기한 30일과 연체 잔액에 대한 월 1.5%의 연체 수수료를 명시해요." },
      { situation: "소기업 현금 흐름 문제를 다룰 때", en: "For small businesses, managing cash flow under net 30 terms requires careful monitoring of receivables collection.", ko: "소기업의 경우 결제 기한 30일 조건에서 현금 흐름을 관리하려면 매출채권 회수를 신중하게 모니터링해야 해요." }
    ],
    level: "800"
  },
  {
    id: 249,
    word: "net 60",
    pronunciation: "net ˈsɪks.ti",
    pos: "n.",
    meaning: "결제 기한 60일, 넷 60",
    synonyms: ["60-day payment terms", "net 60 days", "extended payment terms"],
    examples: [
      { situation: "대기업과 공급 계약을 체결할 때", en: "The large retailer requested net 60 payment terms, which required us to assess the impact on our cash flow.", ko: "대형 소매업체가 결제 기한 60일 조건을 요청했고 이것이 현금 흐름에 미치는 영향을 평가해야 했어요." },
      { situation: "현금 흐름 전략을 논의할 때", en: "Offering net 60 to key accounts helped us win a large contract but required us to draw on our credit facility.", ko: "핵심 계정에 결제 기한 60일을 제공하면서 대형 계약을 수주할 수 있었지만 신용 공여를 활용해야 했어요." },
      { situation: "공급업체 조건을 표준화할 때", en: "We aligned all supplier payment terms to net 60 to improve cash flow and reduce the frequency of payments.", ko: "현금 흐름을 개선하고 결제 빈도를 줄이기 위해 모든 공급업체 결제 조건을 결제 기한 60일로 조정했어요." },
      { situation: "소기업에 미치는 영향을 설명할 때", en: "Net 60 payment terms can be a strain on small suppliers who may not have sufficient credit facilities to bridge the gap.", ko: "결제 기한 60일 조건은 간격을 메울 충분한 신용 공여가 없을 수 있는 소규모 공급업체에게 부담이 될 수 있어요." },
      { situation: "공급업체 조건 개선을 협상할 때", en: "The supplier accepted net 60 in exchange for a guaranteed minimum order volume of 500 units per month.", ko: "공급업체는 월 500개의 보장된 최소 주문량과 교환으로 결제 기한 60일을 수락했어요." },
      { situation: "조달 전략을 수립할 때", en: "Our procurement team standardized on net 60 terms to align supplier payment cycles with our revenue collection timeline.", ko: "조달팀은 공급업체 결제 주기를 매출 수금 일정에 맞추기 위해 결제 기한 60일 조건을 표준화했어요." },
      { situation: "운전 자본을 최적화할 때", en: "Extending to net 60 for major suppliers was a key lever in our working capital optimization program.", ko: "주요 공급업체에 대해 결제 기한 60일로 연장하는 것이 운전자본 최적화 프로그램의 핵심 레버였어요." },
      { situation: "분기말 현금 포지션을 관리할 때", en: "Managing accounts payable under net 60 terms helped smooth our quarter-end cash position.", ko: "결제 기한 60일 조건에서 매입채무를 관리하면서 분기말 현금 포지션을 안정화하는 데 도움이 됐어요." },
      { situation: "글로벌 조달을 할 때", en: "International suppliers often require net 60 or longer terms to compensate for the added costs of cross-border logistics.", ko: "국제 공급업체들은 국경 간 물류의 추가 비용을 보상하기 위해 종종 결제 기한 60일 이상을 요구해요." },
      { situation: "조기 결제 할인 프로그램을 도입할 때", en: "A dynamic discounting program rewards suppliers for accepting payment before the net 60 due date.", ko: "동적 할인 프로그램은 공급업체가 결제 기한 60일 전에 결제를 수락하는 것에 보상해요." }
    ],
    level: "800"
  },
  {
    id: 250,
    word: "interest rate swap",
    pronunciation: "ˈɪn.trəst reɪt swɒp",
    pos: "n.",
    meaning: "금리 스왑",
    synonyms: ["rate swap", "fixed-floating swap", "derivative instrument"],
    examples: [
      { situation: "금리 위험을 관리할 때", en: "The company entered into an interest rate swap to convert its variable-rate loan into a fixed-rate obligation.", ko: "회사는 변동금리 대출을 고정금리 의무로 전환하기 위해 금리 스왑을 체결했어요." },
      { situation: "CFO가 재무 전략을 발표할 때", en: "The CFO used an interest rate swap to lock in current low rates and protect future cash flows from rising borrowing costs.", ko: "CFO는 현재 낮은 금리를 고정하고 미래 현금 흐름을 차입 비용 상승으로부터 보호하기 위해 금리 스왑을 이용했어요." },
      { situation: "파생 상품 전략을 검토할 때", en: "Interest rate swaps are the most widely used derivative instrument for managing interest rate risk in corporate treasuries.", ko: "금리 스왑은 기업 재무에서 금리 위험을 관리하기 위해 가장 널리 사용되는 파생 상품 도구예요." },
      { situation: "대출 약정을 분석할 때", en: "The bank proposed an interest rate swap alongside the term loan to help the borrower manage rate volatility.", ko: "은행은 차주가 금리 변동성을 관리할 수 있도록 기간 대출과 함께 금리 스왑을 제안했어요." },
      { situation: "회계 처리를 설명할 때", en: "Interest rate swap contracts must be marked to market and disclosed in the financial statements as a derivative liability.", ko: "금리 스왑 계약은 시가 평가되고 파생 부채로 재무제표에 공시되어야 해요." },
      { situation: "헤징 전략에 대해 이사회에 보고할 때", en: "The board approved the use of interest rate swaps as part of the treasury hedging policy.", ko: "이사회는 재무 헤징 정책의 일환으로 금리 스왑 사용을 승인했어요." },
      { situation: "고정금리 대출을 원할 때", en: "By combining a floating-rate loan with an interest rate swap, the company achieved an effective fixed rate of 3.5 percent.", ko: "변동금리 대출과 금리 스왑을 결합함으로써 회사는 3.5%의 실질 고정금리를 달성했어요." },
      { situation: "금리 상승 환경에서 대비할 때", en: "In a rising interest rate environment, an interest rate swap provides certainty over future debt service costs.", ko: "금리 상승 환경에서 금리 스왑은 미래 부채 상환 비용에 대한 확실성을 제공해요." },
      { situation: "M&A 자금 조달을 구조화할 때", en: "The acquisition financing package included a term loan hedged with an interest rate swap to fix the effective rate.", ko: "인수 자금 조달 패키지에는 실질 금리를 고정하기 위해 금리 스왑으로 헤지된 기간 대출이 포함됐어요." },
      { situation: "재무 복잡성을 설명할 때", en: "An interest rate swap is an agreement between two parties to exchange interest payments based on different rate structures.", ko: "금리 스왑은 다른 금리 구조를 기반으로 이자 지급을 교환하기로 한 두 당사자 간의 협약이에요." }
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
console.log('Batch 12 done: IDs 230,231,232,233,240,241,243,244,249,250 replaced.');
