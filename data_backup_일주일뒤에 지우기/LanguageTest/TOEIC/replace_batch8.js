// Batch 8: IDs 147,148,152,157,159,160,161,162,170,172
// exclusive dealing->content marketing, exculpate->search engine optimization, exonerate->pay-per-click
// fiduciary->board of directors, forbearance->credit facility, forensic->root cause analysis
// forfeiture->collateral requirement, formidable->price-to-earnings ratio, imminent->burn rate
// impasse->escalation procedure
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 147,
    word: "content marketing",
    pronunciation: "ˈkɒn.tent ˈmɑː.kɪ.tɪŋ",
    pos: "n.",
    meaning: "콘텐츠 마케팅",
    synonyms: ["inbound marketing", "content strategy", "thought leadership marketing"],
    examples: [
      { situation: "디지털 마케팅 전략을 수립할 때", en: "Content marketing has become our primary channel for generating qualified leads in the B2B sector.", ko: "콘텐츠 마케팅이 B2B 부문에서 적격 리드를 창출하는 주요 채널이 됐어요." },
      { situation: "마케팅 예산을 배분할 때", en: "We shifted 30 percent of our advertising budget to content marketing after seeing higher ROI from blog and video content.", ko: "블로그와 비디오 콘텐츠에서 더 높은 ROI를 확인한 후 광고 예산의 30%를 콘텐츠 마케팅으로 전환했어요." },
      { situation: "브랜드 인지도를 높이려 할 때", en: "Content marketing builds brand awareness by providing valuable information rather than overt product promotion.", ko: "콘텐츠 마케팅은 노골적인 제품 홍보보다 가치 있는 정보를 제공함으로써 브랜드 인지도를 구축해요." },
      { situation: "SEO 전략과 연계할 때", en: "High-quality content marketing improves organic search rankings by attracting backlinks from authoritative sources.", ko: "고품질 콘텐츠 마케팅은 권위 있는 소스의 백링크를 유치함으로써 유기적 검색 순위를 향상시켜요." },
      { situation: "고객 교육 전략을 계획할 때", en: "Our content marketing strategy includes case studies, white papers, and webinars that educate prospects about industry challenges.", ko: "콘텐츠 마케팅 전략에는 잠재 고객에게 업계 문제를 교육하는 사례 연구, 백서, 웨비나가 포함돼요." },
      { situation: "영업 주기를 단축하려 할 때", en: "Effective content marketing nurtures leads through the funnel, shortening the average sales cycle by 20 percent.", ko: "효과적인 콘텐츠 마케팅은 퍼널을 통해 리드를 육성해 평균 영업 주기를 20% 단축해요." },
      { situation: "소셜 미디어를 활용할 때", en: "Repurposing long-form content into social media snippets is a cost-effective content marketing tactic.", ko: "장문 콘텐츠를 소셜 미디어 스니펫으로 재활용하는 것은 비용 효율적인 콘텐츠 마케팅 전술이에요." },
      { situation: "콘텐츠 캘린더를 관리할 때", en: "A consistent content marketing calendar ensures we publish relevant content aligned with the buying cycle.", ko: "일관된 콘텐츠 마케팅 캘린더는 구매 주기에 맞는 관련 콘텐츠를 게시하도록 해요." },
      { situation: "마케팅 팀 성과를 평가할 때", en: "Content marketing performance is measured through organic traffic, engagement rates, and conversion attribution.", ko: "콘텐츠 마케팅 성과는 유기적 트래픽, 참여율, 전환 기여도를 통해 측정돼요." },
      { situation: "경쟁사와 차별화 전략을 수립할 때", en: "In a crowded market, original research-based content marketing sets us apart as a trusted industry resource.", ko: "치열한 경쟁 시장에서 독창적인 연구 기반 콘텐츠 마케팅이 우리를 신뢰할 수 있는 업계 자원으로 차별화해요." }
    ],
    level: "800"
  },
  {
    id: 148,
    word: "search engine optimization",
    pronunciation: "sɜːtʃ ˈen.dʒɪn ˌɒp.tɪ.maɪˈzeɪ.ʃən",
    pos: "n.",
    meaning: "검색 엔진 최적화, SEO",
    synonyms: ["SEO", "organic search optimization", "web visibility optimization"],
    examples: [
      { situation: "웹사이트 트래픽을 늘리려 할 때", en: "Investing in search engine optimization helped us triple our organic website traffic within 12 months.", ko: "검색 엔진 최적화에 투자하면서 12개월 내에 유기적 웹사이트 트래픽을 세 배로 늘릴 수 있었어요." },
      { situation: "디지털 마케팅 예산을 논의할 때", en: "Search engine optimization delivers a higher long-term ROI compared to paid search advertising.", ko: "검색 엔진 최적화는 유료 검색 광고에 비해 더 높은 장기적 ROI를 제공해요." },
      { situation: "콘텐츠 전략을 수립할 때", en: "All blog posts are written with search engine optimization in mind, targeting keywords with high search volume.", ko: "모든 블로그 게시물은 검색량이 많은 키워드를 타겟으로 검색 엔진 최적화를 염두에 두고 작성돼요." },
      { situation: "경쟁사와 온라인 가시성을 비교할 때", en: "A search engine optimization audit revealed that our competitor outranks us for 60 percent of our target keywords.", ko: "검색 엔진 최적화 감사 결과 경쟁사가 우리의 목표 키워드 60%에서 우리를 앞선다는 것이 드러났어요." },
      { situation: "웹사이트 재설계를 계획할 때", en: "Any website redesign must be approached carefully to avoid disrupting existing search engine optimization rankings.", ko: "웹사이트 재설계는 기존의 검색 엔진 최적화 순위를 방해하지 않도록 신중하게 접근해야 해요." },
      { situation: "마케팅 대행사를 선택할 때", en: "We hired a specialist agency to handle our search engine optimization strategy and monthly reporting.", ko: "검색 엔진 최적화 전략과 월간 보고를 담당하기 위해 전문 대행사를 고용했어요." },
      { situation: "글로벌 시장에 진출할 때", en: "International search engine optimization requires localized keyword research and content for each target market.", ko: "국제 검색 엔진 최적화는 각 목표 시장을 위한 현지화된 키워드 리서치와 콘텐츠를 필요로 해요." },
      { situation: "마케팅 채널 효과를 분석할 때", en: "Organic traffic from search engine optimization now accounts for 45 percent of all new customer acquisitions.", ko: "검색 엔진 최적화의 유기적 트래픽이 이제 모든 신규 고객 획득의 45%를 차지해요." },
      { situation: "제품 페이지를 최적화할 때", en: "Improving product page search engine optimization led to a 35 percent increase in organic conversions.", ko: "제품 페이지 검색 엔진 최적화를 개선하면서 유기적 전환이 35% 증가했어요." },
      { situation: "전사 디지털 전략을 수립할 때", en: "Search engine optimization is a foundational element of our overall digital marketing strategy.", ko: "검색 엔진 최적화는 전반적인 디지털 마케팅 전략의 기초적인 요소예요." }
    ],
    level: "800"
  },
  {
    id: 152,
    word: "pay-per-click",
    pronunciation: "ˈpeɪ pər klɪk",
    pos: "n.",
    meaning: "클릭당 지불 광고, PPC",
    synonyms: ["PPC", "paid search", "cost-per-click advertising"],
    examples: [
      { situation: "디지털 광고 전략을 수립할 때", en: "Our pay-per-click campaigns generated 500 qualified leads last month at an average cost of twelve dollars per click.", ko: "지난달 PPC 캠페인이 클릭당 평균 12달러의 비용으로 500개의 적격 리드를 창출했어요." },
      { situation: "광고 예산을 배분할 때", en: "We allocate 40 percent of the digital marketing budget to pay-per-click to ensure consistent lead flow.", ko: "일관된 리드 흐름을 보장하기 위해 디지털 마케팅 예산의 40%를 PPC에 배분해요." },
      { situation: "신제품 출시 캠페인을 계획할 때", en: "A targeted pay-per-click campaign was launched alongside the product release to capture high-intent searchers.", ko: "높은 구매 의도를 가진 검색자를 포착하기 위해 제품 출시와 함께 타겟 PPC 캠페인을 시작했어요." },
      { situation: "마케팅 ROI를 분석할 때", en: "Tracking pay-per-click performance at the keyword level allows us to optimize spend toward the highest converting terms.", ko: "키워드 수준에서 PPC 성과를 추적하면 전환율이 가장 높은 검색어로 지출을 최적화할 수 있어요." },
      { situation: "경쟁사 광고 전략을 분석할 때", en: "Competitor analysis revealed they were bidding aggressively on our branded terms in pay-per-click auctions.", ko: "경쟁사 분석에서 그들이 PPC 경매에서 우리 브랜드 검색어에 공격적으로 입찰하고 있음이 드러났어요." },
      { situation: "계절적 프로모션을 실행할 때", en: "We increase pay-per-click budgets by 50 percent during peak season to capture seasonal demand.", ko: "계절적 수요를 포착하기 위해 성수기에 PPC 예산을 50% 늘려요." },
      { situation: "고객 확보 비용을 최적화할 때", en: "Improving landing page quality scores reduced our pay-per-click cost-per-acquisition by 25 percent.", ko: "방문 페이지 품질 점수를 향상시켜 PPC 고객 획득당 비용을 25% 줄였어요." },
      { situation: "A/B 테스트를 진행할 때", en: "Pay-per-click platforms enable rapid A/B testing of ad copy to identify the most effective messaging.", ko: "PPC 플랫폼은 가장 효과적인 메시지를 파악하기 위해 광고 문구의 빠른 A/B 테스트를 가능하게 해요." },
      { situation: "리타겟팅 전략을 논의할 때", en: "Pay-per-click retargeting campaigns re-engage visitors who browsed our website but did not convert.", ko: "PPC 리타겟팅 캠페인은 우리 웹사이트를 탐색했지만 전환하지 않은 방문자들을 다시 참여시켜요." },
      { situation: "신규 시장 진입을 테스트할 때", en: "We use pay-per-click as a rapid market validation tool before committing to full-scale entry.", ko: "전면 진입을 결정하기 전에 빠른 시장 검증 도구로 PPC를 사용해요." }
    ],
    level: "800"
  },
  {
    id: 157,
    word: "board of directors",
    pronunciation: "bɔːd əv daɪˈrek.tərz",
    pos: "n.",
    meaning: "이사회",
    synonyms: ["board", "governing board", "corporate board"],
    examples: [
      { situation: "기업 지배구조를 설명할 때", en: "The board of directors is responsible for overseeing management and protecting shareholder interests.", ko: "이사회는 경영진을 감독하고 주주 이익을 보호할 책임이 있어요." },
      { situation: "주요 전략적 결정을 논의할 때", en: "Any acquisition above fifty million dollars requires approval from the board of directors.", ko: "5천만 달러를 초과하는 모든 인수는 이사회의 승인이 필요해요." },
      { situation: "이사회 구성을 검토할 때", en: "The board of directors currently has nine members, including four independent directors with diverse industry backgrounds.", ko: "이사회는 현재 다양한 업계 배경을 가진 4명의 독립 이사를 포함해 9명의 구성원으로 이루어져 있어요." },
      { situation: "연간 주주총회를 준비할 때", en: "The annual general meeting provides shareholders with an opportunity to elect members to the board of directors.", ko: "주주총회는 주주들에게 이사회 구성원을 선임할 기회를 제공해요." },
      { situation: "경영진과 이사회 관계를 설명할 때", en: "The CEO reports to the board of directors and presents quarterly business updates at formal board meetings.", ko: "CEO는 이사회에 보고하며 공식 이사회 회의에서 분기별 사업 업데이트를 발표해요." },
      { situation: "이사회 위원회를 설명할 때", en: "The board of directors has three standing committees: audit, compensation, and nominations.", ko: "이사회에는 세 개의 상설 위원회가 있어요. 감사, 보상, 후보 추천 위원회예요." },
      { situation: "기업 위기를 관리할 때", en: "During the crisis, the board of directors convened an emergency session to evaluate the company strategic options.", ko: "위기 상황에서 이사회는 회사의 전략적 선택을 평가하기 위해 긴급 회의를 소집했어요." },
      { situation: "신규 이사를 임명할 때", en: "The board of directors appointed a technology expert as a new independent director to strengthen digital oversight.", ko: "이사회는 디지털 감독을 강화하기 위해 기술 전문가를 새로운 독립 이사로 임명했어요." },
      { situation: "ESG 정책을 수립할 때", en: "The board of directors approved a new sustainability policy committing to net-zero emissions by 2040.", ko: "이사회는 2040년까지 탄소 중립을 약속하는 새로운 지속 가능성 정책을 승인했어요." },
      { situation: "투자자에게 신뢰를 심어줄 때", en: "A diverse and experienced board of directors signals strong governance to potential investors.", ko: "다양하고 경험 있는 이사회는 잠재적 투자자들에게 강한 지배구조를 나타내요." }
    ],
    level: "800"
  },
  {
    id: 159,
    word: "credit facility",
    pronunciation: "ˈkred.ɪt fəˈsɪl.ɪ.ti",
    pos: "n.",
    meaning: "신용 공여, 대출 한도",
    synonyms: ["loan facility", "credit arrangement", "borrowing facility"],
    examples: [
      { situation: "기업 자금 조달 옵션을 논의할 때", en: "The company secured a 50-million-dollar revolving credit facility to support its working capital needs.", ko: "회사는 운전자본 필요를 지원하기 위해 5천만 달러의 회전 신용 공여를 확보했어요." },
      { situation: "CFO 분기 보고에서", en: "Our credit facility remains fully undrawn, which provides a strong liquidity buffer against market uncertainty.", ko: "신용 공여는 완전히 미사용 상태로 유지되어 시장 불확실성에 대한 강한 유동성 완충을 제공해요." },
      { situation: "인수 자금을 조달할 때", en: "We drew down on the credit facility to fund the acquisition while awaiting proceeds from the bond issuance.", ko: "채권 발행 수익을 기다리는 동안 인수 자금을 조달하기 위해 신용 공여를 활용했어요." },
      { situation: "은행과 관계를 관리할 때", en: "Our primary banking relationship includes a committed credit facility at a competitive interest margin.", ko: "주거래 은행 관계에는 경쟁력 있는 이자 마진으로 약정된 신용 공여가 포함돼요." },
      { situation: "재무 건전성을 평가할 때", en: "Maintaining an undrawn credit facility demonstrates to investors that the company has access to emergency liquidity.", ko: "미인출 신용 공여를 유지하는 것은 회사가 긴급 유동성에 접근할 수 있음을 투자자들에게 보여줘요." },
      { situation: "대출 약정을 협의할 때", en: "The credit facility agreement includes financial covenants such as minimum interest coverage and maximum leverage ratios.", ko: "신용 공여 계약에는 최소 이자 보상 비율과 최대 레버리지 비율과 같은 재무 약정이 포함돼요." },
      { situation: "유동성 위기에 대비할 때", en: "Access to a committed credit facility is a critical component of any robust liquidity management strategy.", ko: "약정 신용 공여에 대한 접근은 모든 견고한 유동성 관리 전략의 중요한 구성 요소예요." },
      { situation: "M&A 실사 과정에서", en: "The acquirer reviewed the target company existing credit facility to understand any change-of-control provisions.", ko: "인수자는 변경 통제 조항을 파악하기 위해 피인수 기업의 기존 신용 공여를 검토했어요." },
      { situation: "이자율 변화에 대응할 때", en: "The variable-rate credit facility benefited the company during the period of historically low interest rates.", ko: "변동금리 신용 공여는 역사적으로 낮은 금리 기간에 회사에 이익이 됐어요." },
      { situation: "재무 리포트를 분석할 때", en: "The annual report disclosed all material terms of the credit facility including maturity date, interest rate, and covenants.", ko: "연간 보고서는 만기일, 금리, 약정을 포함한 신용 공여의 모든 중요 조건을 공시했어요." }
    ],
    level: "800"
  },
  {
    id: 160,
    word: "root cause analysis",
    pronunciation: "ruːt kɔːz əˈnæl.ɪ.sɪs",
    pos: "n.",
    meaning: "근본 원인 분석",
    synonyms: ["problem analysis", "failure analysis", "causal analysis"],
    examples: [
      { situation: "품질 문제가 반복될 때", en: "Conducting a thorough root cause analysis prevented the same production defect from recurring.", ko: "철저한 근본 원인 분석을 수행해 같은 생산 결함의 재발을 방지했어요." },
      { situation: "IT 시스템 장애를 처리할 때", en: "The IT team performed a root cause analysis after the server outage that disrupted operations for six hours.", ko: "IT팀은 6시간 동안 운영을 중단시킨 서버 장애 이후 근본 원인 분석을 수행했어요." },
      { situation: "고객 불만을 해결할 때", en: "A root cause analysis of customer complaints revealed that 70 percent stemmed from a single process step.", ko: "고객 불만에 대한 근본 원인 분석에서 70%가 단일 프로세스 단계에서 비롯된다는 것이 드러났어요." },
      { situation: "안전 사고를 조사할 때", en: "All workplace safety incidents trigger a formal root cause analysis to identify and address contributing factors.", ko: "모든 직장 안전 사고는 기여 요인을 파악하고 해결하기 위한 공식 근본 원인 분석을 촉발해요." },
      { situation: "프로세스 개선 팀에서", en: "The Lean team used a five-why root cause analysis to trace the delivery delay back to a scheduling issue.", ko: "린 팀은 납품 지연을 일정 문제로 소급 추적하기 위해 5-Why 근본 원인 분석을 사용했어요." },
      { situation: "규제 위반에 대응할 때", en: "Regulators require a documented root cause analysis and corrective action plan within 60 days of any compliance breach.", ko: "규제당국은 컴플라이언스 위반 후 60일 이내에 문서화된 근본 원인 분석과 시정 조치 계획을 요구해요." },
      { situation: "팀 회고 세션에서", en: "A post-project root cause analysis identified poor communication as the main driver of missed milestones.", ko: "프로젝트 후 근본 원인 분석에서 빈약한 커뮤니케이션이 이정표 미달의 주요 원인임을 파악했어요." },
      { situation: "지속적 개선 문화를 구축할 때", en: "Embedding root cause analysis into our quality management system promoted a culture of continuous improvement.", ko: "품질 관리 시스템에 근본 원인 분석을 내재화하면서 지속적 개선 문화를 촉진했어요." },
      { situation: "서비스 장애를 예방할 때", en: "Without root cause analysis, organizations risk repeatedly patching symptoms rather than solving the underlying problem.", ko: "근본 원인 분석 없이는 조직이 근본적인 문제를 해결하는 대신 증상을 반복적으로 패치할 위험이 있어요." },
      { situation: "이사회에 문제를 보고할 때", en: "The board requested a comprehensive root cause analysis of the margin decline before approving remediation plans.", ko: "이사회는 개선 계획을 승인하기 전에 마진 감소에 대한 포괄적인 근본 원인 분석을 요청했어요." }
    ],
    level: "800"
  },
  {
    id: 161,
    word: "collateral requirement",
    pronunciation: "kəˈlæt.ər.əl rɪˈkwaɪər.mənt",
    pos: "n.",
    meaning: "담보 요건",
    synonyms: ["security requirement", "collateral demand", "pledge requirement"],
    examples: [
      { situation: "은행 대출을 신청할 때", en: "The bank outlined its collateral requirement before approving the commercial loan application.", ko: "은행은 사업 대출 신청을 승인하기 전에 담보 요건을 설명했어요." },
      { situation: "자금 조달 구조를 협의할 때", en: "Meeting the collateral requirement was challenging for the startup as it had limited hard assets.", ko: "유형 자산이 제한적인 스타트업에게는 담보 요건을 충족하는 것이 어려웠어요." },
      { situation: "파생 상품 거래를 할 때", en: "Derivative contracts require posting collateral to the counterparty when the trade moves out of the money.", ko: "파생 상품 계약은 거래가 손실 상태가 될 때 상대방에게 담보를 제공하도록 요구해요." },
      { situation: "임대 계약을 검토할 때", en: "The landlord revised the collateral requirement after reviewing the company audited financial statements.", ko: "임대인은 회사의 감사된 재무제표를 검토한 후 담보 요건을 수정했어요." },
      { situation: "무역 금융 계약을 체결할 때", en: "Letter of credit instruments can satisfy a collateral requirement in cross-border trade transactions.", ko: "신용장은 국제 무역 거래에서 담보 요건을 충족할 수 있어요." },
      { situation: "기업 신용 등급이 낮을 때", en: "Companies with lower credit ratings typically face stricter collateral requirements when accessing capital markets.", ko: "신용 등급이 낮은 기업들은 자본 시장에 접근할 때 일반적으로 더 엄격한 담보 요건에 직면해요." },
      { situation: "M&A 거래를 구조화할 때", en: "The acquisition financing was arranged with a collateral requirement secured against the target company assets.", ko: "인수 금융은 피인수 기업의 자산을 담보로 하는 담보 요건과 함께 구성됐어요." },
      { situation: "신용 라인을 유지할 때", en: "Failure to maintain the required asset coverage ratio will trigger additional collateral requirements under the loan agreement.", ko: "요구되는 자산 커버리지 비율을 유지하지 못하면 대출 계약에 따른 추가 담보 요건이 촉발될 거예요." },
      { situation: "공급업체와 신용 조건을 설정할 때", en: "The supplier imposed a collateral requirement on new accounts until a satisfactory payment history was established.", ko: "공급업체는 만족스러운 결제 이력이 수립될 때까지 신규 계정에 담보 요건을 부과했어요." },
      { situation: "재무 계획을 수립할 때", en: "Understanding the collateral requirement upfront prevents surprises that could delay funding approval.", ko: "담보 요건을 미리 이해하면 자금 승인을 지연시킬 수 있는 놀라운 상황을 방지해요." }
    ],
    level: "800"
  },
  {
    id: 162,
    word: "price-to-earnings ratio",
    pronunciation: "praɪs tuː ˈɜː.nɪŋz ˈreɪ.ʃɪ.əʊ",
    pos: "n.",
    meaning: "주가수익비율, P/E 비율",
    synonyms: ["P/E ratio", "earnings multiple", "valuation multiple"],
    examples: [
      { situation: "주식 가치 평가를 할 때", en: "The company shares trade at a price-to-earnings ratio of 25, which is above the sector average of 18.", ko: "회사 주식은 업계 평균 18배를 상회하는 주가수익비율 25배에 거래되고 있어요." },
      { situation: "인수 가격을 분석할 때", en: "The acquirer paid a price-to-earnings ratio of 30 times, reflecting the target company strong growth prospects.", ko: "인수자는 피인수 기업의 강한 성장 전망을 반영해 주가수익비율 30배를 지급했어요." },
      { situation: "투자 결정을 내릴 때", en: "Value investors look for stocks trading at a low price-to-earnings ratio relative to their growth potential.", ko: "가치 투자자들은 성장 잠재력 대비 낮은 주가수익비율로 거래되는 주식을 찾아요." },
      { situation: "투자자 설명회를 준비할 때", en: "Management presented a peer comparison showing that our price-to-earnings ratio was at a discount to the industry.", ko: "경영진은 우리의 주가수익비율이 업계 대비 할인된 상태임을 보여주는 동종 비교를 발표했어요." },
      { situation: "시장 상황을 분석할 때", en: "Rising interest rates often compress price-to-earnings ratios across equity markets as future earnings are discounted more.", ko: "금리 상승은 미래 수익이 더 많이 할인됨에 따라 주식 시장 전반의 주가수익비율을 압박하는 경우가 많아요." },
      { situation: "기업 공개 가격을 설정할 때", en: "The IPO was priced at a price-to-earnings ratio that reflected the company growth stage and market comparables.", ko: "IPO는 회사의 성장 단계와 시장 비교 가능 기업을 반영한 주가수익비율로 가격이 책정됐어요." },
      { situation: "포트폴리오 리뷰를 진행할 때", en: "Portfolio managers use price-to-earnings ratio as one metric to assess whether stocks are overvalued or undervalued.", ko: "포트폴리오 관리자들은 주식이 과대 평가 또는 저평가되어 있는지 평가하는 한 가지 지표로 주가수익비율을 사용해요." },
      { situation: "경영 성과를 주주에게 보고할 때", en: "Our improving profitability has contributed to a rising price-to-earnings ratio over the past three years.", ko: "수익성 향상이 지난 3년간 주가수익비율 상승에 기여했어요." },
      { situation: "섹터 간 비교를 할 때", en: "Technology companies typically command higher price-to-earnings ratios than industrial firms due to expected growth.", ko: "기술 기업들은 예상 성장률 때문에 일반적으로 산업재 회사들보다 더 높은 주가수익비율을 형성해요." },
      { situation: "재무 분석가와 논의할 때", en: "The analyst downgraded the stock, citing a price-to-earnings ratio that no longer justified the growth premium.", ko: "애널리스트는 성장 프리미엄을 더 이상 정당화하지 못하는 주가수익비율을 이유로 주식 등급을 하향 조정했어요." }
    ],
    level: "800"
  },
  {
    id: 170,
    word: "burn rate",
    pronunciation: "bɜːn reɪt",
    pos: "n.",
    meaning: "번 레이트, 자금 소진 속도",
    synonyms: ["cash burn", "monthly expenditure rate", "spending rate"],
    examples: [
      { situation: "스타트업 재무를 검토할 때", en: "The startup has a monthly burn rate of two hundred thousand dollars and twelve months of runway remaining.", ko: "스타트업은 월 20만 달러의 번 레이트와 12개월의 런웨이가 남아 있어요." },
      { situation: "투자자에게 재무 현황을 보고할 때", en: "Investors expect the founding team to track and report the burn rate alongside key growth metrics.", ko: "투자자들은 창업팀이 핵심 성장 지표와 함께 번 레이트를 추적하고 보고할 것으로 기대해요." },
      { situation: "자금 조달 시기를 결정할 때", en: "Understanding the current burn rate is critical when deciding the right timing for the next fundraising round.", ko: "다음 자금 조달 라운드의 적절한 시기를 결정할 때 현재 번 레이트를 이해하는 것이 중요해요." },
      { situation: "비용 절감 계획을 수립할 때", en: "The board recommended reducing the burn rate by 30 percent to extend the company runway by six months.", ko: "이사회는 회사의 런웨이를 6개월 연장하기 위해 번 레이트를 30% 줄이도록 권고했어요." },
      { situation: "채용 계획을 조정할 때", en: "Rapid hiring increased the burn rate significantly, prompting a review of the headcount plan.", ko: "빠른 채용이 번 레이트를 크게 높여 인원 계획 검토를 촉구했어요." },
      { situation: "벤처 캐피탈과 미팅에서", en: "The investor asked for a detailed breakdown of the burn rate by department before proceeding to term sheets.", ko: "투자자는 텀 시트 작성을 진행하기 전에 부서별 번 레이트의 상세 분석을 요청했어요." },
      { situation: "경제 침체에 대응할 때", en: "During the downturn, management focused on reducing the burn rate to survive until market conditions improved.", ko: "침체기 동안 경영진은 시장 상황이 개선될 때까지 생존하기 위해 번 레이트 감소에 집중했어요." },
      { situation: "예산 편성 과정에서", en: "The annual budget is designed to maintain a burn rate that allows 18 months of operating runway.", ko: "연간 예산은 18개월의 운영 런웨이를 허용하는 번 레이트를 유지하도록 설계됐어요." },
      { situation: "SaaS 기업 지표를 분석할 때", en: "A declining burn rate combined with growing revenue signals improving unit economics for the business.", ko: "감소하는 번 레이트와 성장하는 매출의 결합은 사업의 개선되는 단위 경제학을 신호해요." },
      { situation: "피봇 결정을 논의할 때", en: "The founding team decided to pivot the product strategy after realizing the current burn rate was unsustainable.", ko: "창업팀은 현재 번 레이트가 지속 불가능하다는 것을 깨달은 후 제품 전략을 피봇하기로 결정했어요." }
    ],
    level: "800"
  },
  {
    id: 172,
    word: "escalation procedure",
    pronunciation: "ˌes.kəˈleɪ.ʃən prəˈsiː.dʒər",
    pos: "n.",
    meaning: "에스컬레이션 절차, 상위 보고 절차",
    synonyms: ["escalation process", "issue escalation", "escalation path"],
    examples: [
      { situation: "고객 불만 처리 시스템을 설계할 때", en: "Our escalation procedure ensures that unresolved customer complaints reach a senior manager within 24 hours.", ko: "에스컬레이션 절차는 해결되지 않은 고객 불만이 24시간 내에 시니어 매니저에게 전달되도록 해요." },
      { situation: "IT 지원 티켓을 관리할 때", en: "Critical system outages follow a predefined escalation procedure that immediately alerts the on-call CTO.", ko: "중요한 시스템 장애는 즉시 당직 CTO에게 경보를 보내는 사전 정의된 에스컬레이션 절차를 따라요." },
      { situation: "계약 분쟁을 단계적으로 해결할 때", en: "The contract includes an escalation procedure requiring disputes to be addressed first at the account manager level.", ko: "계약에는 분쟁을 먼저 고객 담당 매니저 수준에서 다루도록 요구하는 에스컬레이션 절차가 포함돼요." },
      { situation: "신입 직원에게 규정을 교육할 때", en: "All new employees are trained on the escalation procedure for reporting potential compliance violations.", ko: "모든 신규 직원은 잠재적 컴플라이언스 위반 보고를 위한 에스컬레이션 절차에 대해 교육받아요." },
      { situation: "프로젝트 위험을 관리할 때", en: "When a project milestone is at risk, the escalation procedure requires notifying the steering committee within 48 hours.", ko: "프로젝트 이정표가 위험에 처하면 에스컬레이션 절차는 48시간 내에 운영 위원회에 통보하도록 요구해요." },
      { situation: "안전 사고를 처리할 때", en: "Any workplace safety incident triggers the escalation procedure, notifying HR and senior leadership immediately.", ko: "모든 직장 안전 사고는 즉시 HR과 고위 리더십에 통보하는 에스컬레이션 절차를 촉발해요." },
      { situation: "SLA 위반에 대응할 때", en: "Repeated SLA breaches automatically activate the escalation procedure to bring in senior account management.", ko: "반복적인 SLA 위반은 시니어 고객 관리를 참여시키기 위한 에스컬레이션 절차를 자동으로 활성화해요." },
      { situation: "이사회 보고 체계를 구축할 때", en: "The escalation procedure defines which risk categories require immediate board notification versus quarterly reporting.", ko: "에스컬레이션 절차는 즉각적인 이사회 통보가 필요한 위험 카테고리와 분기별 보고가 필요한 것을 정의해요." },
      { situation: "팀 갈등을 해결할 때", en: "If direct discussion fails to resolve a team conflict, the escalation procedure involves HR mediation.", ko: "직접적인 논의로 팀 갈등을 해결하지 못하면 에스컬레이션 절차에 HR 조정이 포함돼요." },
      { situation: "위기 관리 계획을 수립할 때", en: "A well-documented escalation procedure reduces response time during crises by removing ambiguity about who to notify.", ko: "잘 문서화된 에스컬레이션 절차는 누구에게 통보해야 하는지에 대한 모호성을 제거해 위기 대응 시간을 단축해요." }
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
console.log('Batch 8 done: IDs 147,148,152,157,159,160,161,162,170,172 replaced.');
