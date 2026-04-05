// Batch 2: IDs 14,15,17,21,22,23,24,25,26,27
// aggregate->market penetration, allegation->competitive advantage, amortization->return on investment
// annuity->cash flow management, annul->contract renewal, antecedent->succession planning
// antitrust->corporate governance, apportionment->accounts payable, arbitrage->foreign exchange
// arbitral->dispute resolution
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 14,
    word: "market penetration",
    pronunciation: "ˈmɑː.kɪt ˌpen.ɪˈtreɪ.ʃən",
    pos: "n.",
    meaning: "시장 침투, 시장 점유율 확대",
    synonyms: ["market expansion", "market share growth", "market development"],
    examples: [
      { situation: "신규 시장 전략을 수립할 때", en: "Our market penetration strategy focuses on aggressive pricing to attract first-time buyers.", ko: "우리의 시장 침투 전략은 처음 구매하는 고객을 유치하기 위한 공격적인 가격 책정에 초점을 맞추고 있어요." },
      { situation: "영업 성과를 분석할 때", en: "Market penetration in the Southeast Asian region increased from 8 to 22 percent over three years.", ko: "동남아시아 지역의 시장 침투율이 3년 만에 8%에서 22%로 증가했어요." },
      { situation: "제품 라인 확장을 논의할 때", en: "Launching a budget tier product line is the most effective market penetration tactic for price-sensitive segments.", ko: "저가 제품 라인을 출시하는 것이 가격에 민감한 세그먼트에 대한 가장 효과적인 시장 침투 전술이에요." },
      { situation: "투자자에게 성장 계획을 발표할 때", en: "Investors were encouraged by the company rapid market penetration in the enterprise software segment.", ko: "투자자들은 기업용 소프트웨어 부문에서 회사의 빠른 시장 침투에 고무됐어요." },
      { situation: "마케팅 채널 전략을 검토할 때", en: "Partnering with local distributors accelerated our market penetration in markets where we had no direct presence.", ko: "현지 유통업체와 파트너십을 맺음으로써 우리가 직접 진출하지 않은 시장에서의 시장 침투를 가속화했어요." },
      { situation: "경쟁사와 비교 분석을 할 때", en: "Despite heavy investment, our market penetration rate still lags behind the industry leader by 12 percentage points.", ko: "대규모 투자에도 불구하고 우리의 시장 침투율은 여전히 업계 선도 기업보다 12%p 뒤처지고 있어요." },
      { situation: "신제품 출시 계획을 세울 때", en: "A freemium pricing model proved to be the fastest route to market penetration for our new SaaS platform.", ko: "프리미엄 가격 모델은 우리의 새로운 SaaS 플랫폼의 시장 침투에 가장 빠른 경로임이 입증됐어요." },
      { situation: "글로벌 확장 전략을 논의할 때", en: "Market penetration in developed economies requires a different approach than in emerging markets.", ko: "선진 경제에서의 시장 침투는 신흥 시장과 다른 접근 방식을 필요로 해요." },
      { situation: "분기별 판매 실적을 보고할 때", en: "The Q3 report shows that market penetration in the retail channel exceeded our forecast by 15 percent.", ko: "3분기 보고서에 따르면 소매 채널에서의 시장 침투가 예상을 15% 초과했어요." },
      { situation: "5개년 사업 계획을 발표할 때", en: "Our five-year plan targets 35 percent market penetration across all core product categories.", ko: "우리의 5개년 계획은 모든 핵심 제품 카테고리에서 35% 시장 침투를 목표로 해요." }
    ],
    level: "800"
  },
  {
    id: 15,
    word: "competitive advantage",
    pronunciation: "kəmˈpet.ɪ.tɪv ədˈvɑːn.tɪdʒ",
    pos: "n.",
    meaning: "경쟁 우위",
    synonyms: ["competitive edge", "market differentiation", "strategic advantage"],
    examples: [
      { situation: "전략 기획 세션에서", en: "Our proprietary technology gives us a sustainable competitive advantage that rivals cannot easily replicate.", ko: "우리의 독점 기술은 경쟁사들이 쉽게 복제할 수 없는 지속 가능한 경쟁 우위를 제공해요." },
      { situation: "투자자 프레젠테이션을 준비할 때", en: "The CEO outlined three sources of competitive advantage: cost leadership, brand strength, and customer loyalty.", ko: "CEO는 비용 리더십, 브랜드 강점, 고객 충성도라는 세 가지 경쟁 우위 원천을 설명했어요." },
      { situation: "시장 분석 보고서를 작성할 때", en: "Maintaining a competitive advantage requires constant innovation and responsiveness to customer needs.", ko: "경쟁 우위를 유지하려면 지속적인 혁신과 고객 니즈에 대한 대응력이 필요해요." },
      { situation: "신제품 개발 전략을 논의할 때", en: "Our R&D investment is the foundation of our long-term competitive advantage in the medical device market.", ko: "R&D 투자는 의료 기기 시장에서 우리의 장기적 경쟁 우위의 토대예요." },
      { situation: "인재 영입 전략을 수립할 때", en: "Attracting and retaining top talent is increasingly recognized as a key competitive advantage.", ko: "최고 인재를 유치하고 유지하는 것이 핵심 경쟁 우위로 점점 더 인정받고 있어요." },
      { situation: "공급망 전략을 검토할 때", en: "Our vertically integrated supply chain provides a significant competitive advantage in terms of cost and speed-to-market.", ko: "수직 통합된 공급망은 비용과 시장 출시 속도 측면에서 상당한 경쟁 우위를 제공해요." },
      { situation: "브랜드 전략 회의에서", en: "Strong brand equity is one of the hardest competitive advantages for new entrants to overcome.", ko: "강한 브랜드 자산은 신규 진입자가 극복하기 가장 어려운 경쟁 우위 중 하나예요." },
      { situation: "경영 컨설팅 보고서를 발표할 때", en: "The consulting team identified data analytics capability as an emerging competitive advantage in the retail sector.", ko: "컨설팅팀은 데이터 분석 역량을 소매 부문에서 부상하는 경쟁 우위로 파악했어요." },
      { situation: "경쟁 환경 변화를 분석할 때", en: "Rapid technological change can erode an existing competitive advantage within just a few years.", ko: "빠른 기술 변화는 기존의 경쟁 우위를 불과 몇 년 내에 잠식할 수 있어요." },
      { situation: "연간 사업 계획을 수립할 때", en: "Each business unit must articulate how it plans to build or sustain its competitive advantage in the coming year.", ko: "각 사업부는 다음 해에 경쟁 우위를 구축하거나 유지할 계획을 명확히 설명해야 해요." }
    ],
    level: "800"
  },
  {
    id: 17,
    word: "return on investment",
    pronunciation: "rɪˈtɜːn ɒn ɪnˈvest.mənt",
    pos: "n.",
    meaning: "투자 수익률, ROI",
    synonyms: ["ROI", "investment return", "profitability ratio"],
    examples: [
      { situation: "마케팅 지출 효과를 평가할 때", en: "The campaign delivered a return on investment of 320 percent, far exceeding our initial projections.", ko: "그 캠페인은 320%의 투자 수익률을 달성해 초기 예상을 훨씬 초과했어요." },
      { situation: "자본 지출 승인을 요청할 때", en: "The project proposal must clearly demonstrate a positive return on investment within two years.", ko: "프로젝트 제안서는 2년 내에 긍정적인 투자 수익률을 달성한다는 것을 명확히 보여줘야 해요." },
      { situation: "신기술 도입을 검토할 때", en: "Calculating the return on investment for automation tools requires factoring in both direct and indirect savings.", ko: "자동화 도구의 투자 수익률을 계산할 때는 직접적 절감과 간접적 절감을 모두 고려해야 해요." },
      { situation: "교육 프로그램 예산을 요청할 때", en: "We track the return on investment of employee training by measuring productivity gains post-completion.", ko: "교육 완료 후 생산성 향상을 측정해 직원 교육의 투자 수익률을 추적해요." },
      { situation: "부동산 투자를 분석할 때", en: "The real estate division reported a strong return on investment from the recent commercial property acquisition.", ko: "부동산 사업부는 최근 상업용 부동산 인수로 강한 투자 수익률을 보고했어요." },
      { situation: "이사회에 투자 성과를 보고할 때", en: "The board evaluated each business unit based on its return on investment over the past three fiscal years.", ko: "이사회는 지난 3 회계연도에 걸친 투자 수익률을 기준으로 각 사업부를 평가했어요." },
      { situation: "전략적 파트너십을 평가할 때", en: "A joint marketing partnership is only worthwhile if both parties can demonstrate a measurable return on investment.", ko: "공동 마케팅 파트너십은 양측이 측정 가능한 투자 수익률을 입증할 수 있을 때만 가치가 있어요." },
      { situation: "신규 채용 비용을 분석할 때", en: "Reducing employee turnover significantly improves the return on investment of the talent acquisition process.", ko: "직원 이직률을 낮추면 인재 채용 프로세스의 투자 수익률이 크게 향상돼요." },
      { situation: "소셜 미디어 마케팅을 검토할 때", en: "Measuring the return on investment of social media marketing is challenging due to attribution complexity.", ko: "소셜 미디어 마케팅의 투자 수익률 측정은 기여도 분석의 복잡성으로 인해 어려워요." },
      { situation: "연간 예산 계획을 수립할 때", en: "Every budget line item should be linked to an expected return on investment to justify the expenditure.", ko: "모든 예산 항목은 지출을 정당화하기 위해 예상 투자 수익률과 연계되어야 해요." }
    ],
    level: "800"
  },
  {
    id: 21,
    word: "cash flow management",
    pronunciation: "kæʃ fləʊ ˈmæn.ɪdʒ.mənt",
    pos: "n.",
    meaning: "현금 흐름 관리",
    synonyms: ["liquidity management", "working capital management", "cash management"],
    examples: [
      { situation: "재무팀 월간 검토 회의에서", en: "Effective cash flow management is critical to avoiding liquidity crises during slow revenue periods.", ko: "효과적인 현금 흐름 관리는 매출이 부진한 기간에 유동성 위기를 피하는 데 매우 중요해요." },
      { situation: "스타트업 재정을 논의할 때", en: "The startup struggled with cash flow management because customers were paying invoices 60 to 90 days late.", ko: "스타트업은 고객들이 청구서를 60~90일 늦게 결제하는 바람에 현금 흐름 관리에 어려움을 겪었어요." },
      { situation: "CFO 보고를 준비할 때", en: "Our improved cash flow management reduced the need for short-term borrowing by 40 percent.", ko: "개선된 현금 흐름 관리 덕분에 단기 차입 필요성이 40% 줄었어요." },
      { situation: "공급업체 결제 조건을 협상할 때", en: "Negotiating extended payment terms with suppliers is a common cash flow management technique.", ko: "공급업체와 연장된 결제 조건을 협상하는 것은 일반적인 현금 흐름 관리 기법이에요." },
      { situation: "계절적 사업 변동을 대비할 때", en: "Retail businesses need robust cash flow management strategies to handle the seasonal fluctuations in revenue.", ko: "소매 기업은 계절적 매출 변동에 대처하기 위해 견고한 현금 흐름 관리 전략이 필요해요." },
      { situation: "성장 기업의 재무 계획을 수립할 때", en: "Even profitable companies can fail if they neglect cash flow management during rapid expansion.", ko: "수익성이 있는 기업도 급격한 확장 중에 현금 흐름 관리를 소홀히 하면 실패할 수 있어요." },
      { situation: "투자자에게 재무 건전성을 설명할 때", en: "Strong cash flow management demonstrates to investors that the business can fund its own growth.", ko: "강력한 현금 흐름 관리는 투자자들에게 사업이 자체적으로 성장에 자금을 조달할 수 있음을 보여줘요." },
      { situation: "예산 편성 과정에서", en: "The finance team developed a 13-week cash flow forecast to support short-term cash flow management decisions.", ko: "재무팀은 단기 현금 흐름 관리 결정을 지원하기 위해 13주 현금 흐름 예측을 개발했어요." },
      { situation: "은행 신용 한도를 검토할 때", en: "A revolving credit facility provides a safety net that complements our overall cash flow management strategy.", ko: "회전 신용 한도는 전반적인 현금 흐름 관리 전략을 보완하는 안전망을 제공해요." },
      { situation: "미수금 회수 절차를 개선할 때", en: "Implementing automated invoicing significantly improved our accounts receivable collection and cash flow management.", ko: "자동화된 청구서 발행을 도입하면서 매출채권 회수와 현금 흐름 관리가 크게 개선됐어요." }
    ],
    level: "800"
  },
  {
    id: 22,
    word: "contract renewal",
    pronunciation: "ˈkɒn.trækt rɪˈnjuː.əl",
    pos: "n.",
    meaning: "계약 갱신",
    synonyms: ["contract extension", "agreement renewal", "lease renewal"],
    examples: [
      { situation: "공급업체와 연간 계약을 재협상할 때", en: "The procurement team initiated contract renewal discussions three months before the current agreement expires.", ko: "조달팀은 현재 계약이 만료되기 3개월 전에 계약 갱신 협의를 시작했어요." },
      { situation: "고객과 서비스 계약을 연장할 때", en: "Successful account managers often close contract renewals by demonstrating clear ROI to the client.", ko: "성공적인 고객 담당 매니저들은 고객에게 명확한 ROI를 보여줌으로써 계약 갱신을 성사시켜요." },
      { situation: "임대 계약 갱신을 준비할 때", en: "The facilities manager reviewed lease terms well in advance to negotiate favorable contract renewal conditions.", ko: "시설 관리자는 유리한 계약 갱신 조건을 협상하기 위해 미리 임대 조건을 검토했어요." },
      { situation: "IT 라이선스 계약을 갱신할 때", en: "Software contract renewal often presents an opportunity to renegotiate pricing and add new service modules.", ko: "소프트웨어 계약 갱신은 종종 가격을 재협상하고 새로운 서비스 모듈을 추가할 기회를 제공해요." },
      { situation: "고객 이탈 방지 전략을 수립할 때", en: "Proactive customer outreach 90 days before contract renewal significantly reduces churn rates.", ko: "계약 갱신 90일 전에 고객에게 선제적으로 연락하면 이탈률이 크게 줄어요." },
      { situation: "법무팀 계약 검토 프로세스에서", en: "All contract renewals must be reviewed by the legal team to ensure updated compliance requirements are reflected.", ko: "모든 계약 갱신은 업데이트된 컴플라이언스 요건이 반영되도록 법무팀의 검토를 받아야 해요." },
      { situation: "영업팀 성과 지표를 논의할 때", en: "Contract renewal rate is one of the most important metrics for evaluating customer success performance.", ko: "계약 갱신율은 고객 성공 성과를 평가하는 가장 중요한 지표 중 하나예요." },
      { situation: "장기 파트너십 계약을 관리할 때", en: "We offered a multi-year contract renewal at a discounted rate to reward the client long-term commitment.", ko: "고객의 장기적 헌신에 보상하기 위해 할인된 요금으로 다년간 계약 갱신을 제안했어요." },
      { situation: "계약 만료일을 추적 관리할 때", en: "The CRM system sends automatic reminders to account managers 60 days before any contract renewal deadline.", ko: "CRM 시스템은 모든 계약 갱신 마감일 60일 전에 고객 담당 매니저에게 자동으로 알림을 보내요." },
      { situation: "고객 불만을 계약 갱신에 반영할 때", en: "During contract renewal negotiations, the client requested improved service level commitments based on past performance.", ko: "계약 갱신 협상 중에 고객은 과거 성과를 바탕으로 개선된 서비스 수준 약정을 요청했어요." }
    ],
    level: "800"
  },
  {
    id: 23,
    word: "succession planning",
    pronunciation: "səkˈseʃ.ən ˈplæn.ɪŋ",
    pos: "n.",
    meaning: "승계 계획, 후계자 양성 계획",
    synonyms: ["leadership pipeline", "talent development", "continuity planning"],
    examples: [
      { situation: "CEO 은퇴를 준비할 때", en: "The board initiated a formal succession planning process to identify the next CEO two years before the incumbent retires.", ko: "이사회는 현 CEO가 은퇴하기 2년 전에 차기 CEO를 발굴하기 위한 공식 승계 계획 절차를 시작했어요." },
      { situation: "핵심 인재 리텐션 전략을 수립할 때", en: "Succession planning helps retain high-potential employees by giving them a clear path to leadership roles.", ko: "승계 계획은 고잠재력 직원들에게 리더십 직위로의 명확한 경로를 제공함으로써 그들의 유지를 돕는 게 좋아요." },
      { situation: "HR 전략 보고서를 작성할 때", en: "Effective succession planning requires identifying critical roles and developing multiple candidates for each position.", ko: "효과적인 승계 계획은 핵심 직위를 파악하고 각 직위에 대한 여러 후보자를 개발하는 것을 필요로 해요." },
      { situation: "이사회 거버넌스 검토에서", en: "Regulators expect all financial institutions to maintain robust succession planning for key leadership positions.", ko: "규제당국은 모든 금융 기관이 핵심 리더십 직위에 대한 견고한 승계 계획을 유지하도록 기대해요." },
      { situation: "가족 기업 경영권 이전을 논의할 때", en: "The family business engaged an advisory firm to develop a formal succession planning framework for the next generation.", ko: "가족 기업은 다음 세대를 위한 공식 승계 계획 프레임워크를 개발하기 위해 자문 회사를 고용했어요." },
      { situation: "인재 개발 프로그램을 설계할 때", en: "Our succession planning program includes job rotation, mentoring, and executive coaching for top talent.", ko: "우리의 승계 계획 프로그램에는 최고 인재를 위한 직무 순환, 멘토링, 임원 코칭이 포함돼요." },
      { situation: "조직 위험을 평가할 때", en: "The HR audit revealed that succession planning coverage for senior management roles was insufficient.", ko: "HR 감사 결과 고위 관리직에 대한 승계 계획 커버리지가 불충분한 것으로 나타났어요." },
      { situation: "연간 인재 검토를 진행할 때", en: "During the annual talent review, managers nominate high performers to be included in the succession planning pool.", ko: "연간 인재 검토 시 관리자들은 승계 계획 후보군에 포함될 고성과자를 추천해요." },
      { situation: "기업 인수 후 통합 계획에서", en: "Post-acquisition integration includes aligning the succession planning processes of both organizations.", ko: "인수 후 통합에는 두 조직의 승계 계획 프로세스를 조율하는 것이 포함돼요." },
      { situation: "이사회 위원회 회의에서", en: "The compensation committee reviews succession planning progress quarterly to ensure the leadership pipeline remains strong.", ko: "보상 위원회는 리더십 파이프라인이 강하게 유지되도록 분기별로 승계 계획 진행 상황을 검토해요." }
    ],
    level: "800"
  },
  {
    id: 24,
    word: "corporate governance",
    pronunciation: "ˈkɔː.pər.ɪt ˈɡʌv.ə.nəns",
    pos: "n.",
    meaning: "기업 지배구조",
    synonyms: ["board oversight", "company governance", "organizational governance"],
    examples: [
      { situation: "주주총회를 준비할 때", en: "Good corporate governance builds trust with shareholders, employees, and the broader public.", ko: "좋은 기업 지배구조는 주주, 직원, 그리고 더 넓은 대중과의 신뢰를 구축해요." },
      { situation: "이사회 구성을 검토할 때", en: "The corporate governance framework requires that at least 50 percent of board members be independent directors.", ko: "기업 지배구조 프레임워크는 이사의 최소 50%가 독립 이사여야 한다고 요구해요." },
      { situation: "규제 준수를 점검할 때", en: "Regulatory authorities conduct periodic reviews to assess the quality of corporate governance at listed companies.", ko: "규제당국은 상장 기업의 기업 지배구조 품질을 평가하기 위해 주기적인 검토를 실시해요." },
      { situation: "ESG 보고서를 작성할 때", en: "Strong corporate governance is increasingly viewed as a core component of ESG performance by institutional investors.", ko: "강한 기업 지배구조는 기관 투자자들에 의해 ESG 성과의 핵심 요소로 점점 더 인정받고 있어요." },
      { situation: "이사 임명 절차를 논의할 때", en: "The nomination committee is responsible for recommending board appointments under the corporate governance guidelines.", ko: "후보 추천 위원회는 기업 지배구조 지침에 따라 이사회 임명을 추천할 책임이 있어요." },
      { situation: "내부 감사 보고서를 검토할 때", en: "Weaknesses in corporate governance were identified as a root cause of the accounting irregularities discovered during the audit.", ko: "감사 중 발견된 회계 불규칙성의 근본 원인으로 기업 지배구조의 취약점이 지목됐어요." },
      { situation: "외국인 투자를 유치할 때", en: "International investors typically require evidence of robust corporate governance before committing capital.", ko: "국제 투자자들은 일반적으로 자본을 투입하기 전에 견고한 기업 지배구조의 증거를 요구해요." },
      { situation: "기업 윤리 정책을 강화할 때", en: "Our corporate governance policy was updated to include mandatory ethics training for all board members.", ko: "우리의 기업 지배구조 정책은 모든 이사회 구성원에 대한 의무적인 윤리 교육을 포함하도록 업데이트됐어요." },
      { situation: "스캔들 이후 신뢰 회복을 논의할 때", en: "Following the scandal, the company overhauled its corporate governance structure to restore investor confidence.", ko: "스캔들 이후 회사는 투자자 신뢰를 회복하기 위해 기업 지배구조 구조를 전면 개편했어요." },
      { situation: "신규 상장을 준비할 때", en: "An IPO requires companies to meet stringent corporate governance standards set by the stock exchange.", ko: "IPO는 기업이 증권 거래소가 설정한 엄격한 기업 지배구조 기준을 충족하도록 요구해요." }
    ],
    level: "800"
  },
  {
    id: 25,
    word: "accounts payable",
    pronunciation: "əˈkaʊnts ˈpeɪ.ə.bəl",
    pos: "n.",
    meaning: "매입채무, 외상매입금",
    synonyms: ["trade payables", "vendor payables", "outstanding bills"],
    examples: [
      { situation: "재무 보고서를 준비할 때", en: "The accounts payable balance increased by 18 percent this quarter due to higher inventory purchases.", ko: "재고 구매 증가로 이번 분기 매입채무 잔액이 18% 증가했어요." },
      { situation: "공급업체 결제 일정을 관리할 때", en: "Our accounts payable team processes over 500 vendor invoices each week.", ko: "우리 매입채무팀은 매주 500건 이상의 공급업체 청구서를 처리해요." },
      { situation: "현금 흐름 분석을 할 때", en: "Extending accounts payable days by 10 days improved our short-term cash position significantly.", ko: "매입채무 지급일을 10일 연장함으로써 단기 현금 포지션이 크게 개선됐어요." },
      { situation: "내부 통제를 검토할 때", en: "A two-person approval process for all accounts payable transactions helps prevent unauthorized payments.", ko: "모든 매입채무 거래에 대한 2인 승인 프로세스는 무단 지급을 방지하는 데 도움이 돼요." },
      { situation: "ERP 시스템 도입을 논의할 때", en: "Automating the accounts payable process reduced invoice processing time from five days to one day.", ko: "매입채무 프로세스를 자동화하면서 청구서 처리 시간이 5일에서 1일로 단축됐어요." },
      { situation: "공급업체와 관계를 유지할 때", en: "Paying accounts payable on time strengthens supplier relationships and may qualify you for early payment discounts.", ko: "제때 매입채무를 결제하면 공급업체 관계가 강화되고 조기 결제 할인을 받을 수도 있어요." },
      { situation: "감사 절차를 진행할 때", en: "External auditors review accounts payable records to verify that all liabilities are accurately stated.", ko: "외부 감사인들은 모든 부채가 정확하게 기재됐는지 확인하기 위해 매입채무 기록을 검토해요." },
      { situation: "재무 담당자와 면접을 볼 때", en: "The accounts payable manager is responsible for ensuring that all invoices are coded correctly and paid on schedule.", ko: "매입채무 관리자는 모든 청구서가 올바르게 코딩되고 일정에 맞춰 지급되도록 할 책임이 있어요." },
      { situation: "월말 결산 작업을 할 때", en: "Month-end closing includes reconciling the accounts payable ledger against supplier statements.", ko: "월말 결산에는 공급업체 명세서와 매입채무 원장을 대조하는 작업이 포함돼요." },
      { situation: "재무비율 분석을 할 때", en: "A high accounts payable turnover ratio may indicate that a company is paying its suppliers too quickly.", ko: "높은 매입채무 회전율은 회사가 공급업체에 너무 빨리 결제하고 있음을 나타낼 수 있어요." }
    ],
    level: "800"
  },
  {
    id: 26,
    word: "foreign exchange",
    pronunciation: "ˈfɒr.ɪn ɪksˈtʃeɪndʒ",
    pos: "n.",
    meaning: "외환, 외국 환전",
    synonyms: ["FX", "currency exchange", "forex"],
    examples: [
      { situation: "해외 거래처에 결제할 때", en: "Foreign exchange risk must be carefully managed when conducting business across multiple currencies.", ko: "여러 통화로 사업을 할 때는 외환 위험을 신중하게 관리해야 해요." },
      { situation: "분기 재무 실적을 보고할 때", en: "Unfavorable foreign exchange movements reduced our reported revenue by 3 percent this quarter.", ko: "불리한 외환 변동으로 이번 분기 보고된 매출이 3% 감소했어요." },
      { situation: "해외 공급업체와 계약을 체결할 때", en: "We negotiated all contracts in US dollars to minimize foreign exchange exposure for both parties.", ko: "양측의 외환 노출을 최소화하기 위해 모든 계약을 미국 달러로 협상했어요." },
      { situation: "재무팀 환위험 관리 미팅에서", en: "The treasury team uses forward contracts to hedge against foreign exchange fluctuations on major contracts.", ko: "재무팀은 주요 계약의 외환 변동에 대비하기 위해 선물환 계약을 사용해요." },
      { situation: "글로벌 확장 계획을 수립할 때", en: "When expanding internationally, companies must account for foreign exchange volatility in their financial projections.", ko: "국제적으로 확장할 때 기업들은 재무 예측에 외환 변동성을 고려해야 해요." },
      { situation: "연간 재무 보고서를 작성할 때", en: "The annual report includes a sensitivity analysis showing the impact of a 10 percent foreign exchange rate change.", ko: "연간 보고서에는 10% 외환 환율 변동의 영향을 보여주는 민감도 분석이 포함돼요." },
      { situation: "은행 서비스를 선택할 때", en: "We switched banking partners to access more competitive foreign exchange rates for our international transfers.", ko: "국제 송금에 더 경쟁력 있는 외환 환율을 이용하기 위해 은행 파트너를 변경했어요." },
      { situation: "수출 기업 재무 전략을 논의할 때", en: "Export-oriented businesses are particularly vulnerable to foreign exchange rate swings.", ko: "수출 중심 기업들은 외환 환율 변동에 특히 취약해요." },
      { situation: "인수합병 가치를 평가할 때", en: "The acquisition valuation required careful consideration of foreign exchange translation effects on consolidated earnings.", ko: "인수 평가에는 연결 이익에 대한 외환 환산 효과를 신중하게 고려하는 것이 필요했어요." },
      { situation: "해외 급여 지급 시스템을 검토할 때", en: "Paying expatriate salaries requires a reliable foreign exchange conversion process to ensure accuracy.", ko: "주재원 급여를 지급하려면 정확성을 보장하기 위해 신뢰할 수 있는 외환 환전 프로세스가 필요해요." }
    ],
    level: "800"
  },
  {
    id: 27,
    word: "dispute resolution",
    pronunciation: "dɪˈspjuːt ˌrez.əˈluː.ʃən",
    pos: "n.",
    meaning: "분쟁 해결",
    synonyms: ["conflict resolution", "mediation", "arbitration"],
    examples: [
      { situation: "계약 분쟁이 발생했을 때", en: "The contract includes a dispute resolution clause requiring both parties to attempt mediation before litigation.", ko: "계약서에는 소송 전에 양측이 조정을 시도해야 한다는 분쟁 해결 조항이 포함되어 있어요." },
      { situation: "공급업체와 갈등이 생겼을 때", en: "We engaged a neutral third party to facilitate the dispute resolution process between our company and the supplier.", ko: "우리 회사와 공급업체 간의 분쟁 해결 과정을 촉진하기 위해 중립적인 제3자를 참여시켰어요." },
      { situation: "HR 갈등 관리 프로세스를 설명할 때", en: "The HR department has a structured dispute resolution process to handle workplace conflicts fairly and consistently.", ko: "HR 부서는 직장 내 갈등을 공정하고 일관되게 처리하기 위한 구조화된 분쟁 해결 프로세스를 갖추고 있어요." },
      { situation: "국제 계약을 검토할 때", en: "International contracts often specify which country law governs dispute resolution to avoid jurisdictional conflicts.", ko: "국제 계약은 종종 관할권 충돌을 피하기 위해 분쟁 해결을 관할하는 국가법을 명시해요." },
      { situation: "기업 고객과의 갈등을 관리할 때", en: "Offering a formal dispute resolution process demonstrates a commitment to fair dealing and builds client trust.", ko: "공식적인 분쟁 해결 프로세스를 제공하는 것은 공정한 거래에 대한 헌신을 보여주고 고객 신뢰를 구축해요." },
      { situation: "온라인 플랫폼 이용 약관을 설명할 때", en: "Our platform terms of service outline a three-step dispute resolution process for handling customer complaints.", ko: "우리 플랫폼의 서비스 이용 약관은 고객 불만 처리를 위한 3단계 분쟁 해결 프로세스를 개설해요." },
      { situation: "법적 비용 절감 방안을 논의할 때", en: "Choosing alternative dispute resolution methods such as mediation can save considerable time and legal costs.", ko: "조정과 같은 대안적 분쟁 해결 방법을 선택하면 상당한 시간과 법률 비용을 절약할 수 있어요." },
      { situation: "합작 투자 계약을 협상할 때", en: "The joint venture agreement specifies binding arbitration as the preferred dispute resolution mechanism.", ko: "합작 투자 계약은 선호하는 분쟁 해결 메커니즘으로 구속력 있는 중재를 명시해요." },
      { situation: "프랜차이즈 계약을 검토할 때", en: "Franchise agreements must include a clear dispute resolution framework to protect both franchisors and franchisees.", ko: "프랜차이즈 계약은 프랜차이저와 프랜차이지 모두를 보호하기 위해 명확한 분쟁 해결 프레임워크를 포함해야 해요." },
      { situation: "투자자와의 이견을 해소할 때", en: "The shareholders agreement includes an escalation pathway as part of the dispute resolution process.", ko: "주주 계약에는 분쟁 해결 프로세스의 일환으로 에스컬레이션 경로가 포함되어 있어요." }
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
console.log('Batch 2 done: IDs 14,15,17,21,22,23,24,25,26,27 replaced.');
