// Batch 11: IDs 211,213,215,216,217,219,220,221,225,229
// per capita->hedging strategy, perpetuity->enterprise value, plausible->due diligence
// prerequisite->term sheet, pragmatic->closing conditions, predatory pricing->code review
// proponent->deployment pipeline, pro rata->quota attainment, promissory note->personal guarantee
// punitive damages->customer churn
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 211,
    word: "hedging strategy",
    pronunciation: "ˈhedʒ.ɪŋ ˈstræt.ɪ.dʒi",
    pos: "n.",
    meaning: "헤징 전략, 위험 회피 전략",
    synonyms: ["risk hedging", "currency hedging", "financial risk management"],
    examples: [
      { situation: "외환 위험을 관리할 때", en: "The CFO implemented a hedging strategy using forward contracts to protect margins from currency fluctuations.", ko: "CFO는 통화 변동으로부터 마진을 보호하기 위해 선물환 계약을 이용한 헤징 전략을 구현했어요." },
      { situation: "원자재 비용 변동에 대비할 때", en: "Our hedging strategy locks in commodity prices six months in advance to provide cost predictability.", ko: "헤징 전략은 비용 예측 가능성을 제공하기 위해 6개월 전에 원자재 가격을 고정해요." },
      { situation: "이자율 위험을 완화할 때", en: "The treasury team uses interest rate swaps as part of its hedging strategy to reduce exposure to rising borrowing costs.", ko: "재무팀은 차입 비용 상승에 대한 노출을 줄이기 위해 헤징 전략의 일환으로 금리 스왑을 사용해요." },
      { situation: "투자 포트폴리오를 보호할 때", en: "A well-designed hedging strategy can reduce portfolio volatility without significantly limiting upside returns.", ko: "잘 설계된 헤징 전략은 상승 수익을 크게 제한하지 않고 포트폴리오 변동성을 줄일 수 있어요." },
      { situation: "글로벌 사업의 재무 리스크를 분석할 때", en: "For companies with significant international revenues, a hedging strategy is essential to protect reported earnings.", ko: "상당한 국제 매출이 있는 회사들에게는 보고된 이익을 보호하기 위한 헤징 전략이 필수적이에요." },
      { situation: "이사회에 재무 전략을 발표할 때", en: "The board approved the new hedging strategy that targets coverage of 75 percent of next year foreign currency exposure.", ko: "이사회는 내년 외환 노출의 75% 커버리지를 목표로 하는 새로운 헤징 전략을 승인했어요." },
      { situation: "파생 상품을 도입할 때", en: "Options contracts were added to the hedging strategy to allow participation in favorable market movements.", ko: "유리한 시장 움직임에 참여할 수 있도록 헤징 전략에 옵션 계약이 추가됐어요." },
      { situation: "공급망 비용을 안정화할 때", en: "The hedging strategy for energy costs reduced the impact of oil price spikes on manufacturing expenses.", ko: "에너지 비용에 대한 헤징 전략은 유가 급등이 제조 비용에 미치는 영향을 줄였어요." },
      { situation: "M&A 가치 평가 시 환율 위험을 검토할 때", en: "The hedging strategy for the cross-border acquisition protected deal value from exchange rate movements during the closing period.", ko: "국경 간 인수에 대한 헤징 전략은 마감 기간 동안 환율 변동으로부터 거래 가치를 보호했어요." },
      { situation: "재무 컨설팅을 받을 때", en: "The financial adviser recommended a hedging strategy combining natural hedges with derivative instruments.", ko: "재무 어드바이저는 자연 헤지와 파생 상품을 결합한 헤징 전략을 권고했어요." }
    ],
    level: "800"
  },
  {
    id: 213,
    word: "enterprise value",
    pronunciation: "ˈen.tər.praɪz ˈvæl.juː",
    pos: "n.",
    meaning: "기업 가치, EV",
    synonyms: ["EV", "total firm value", "company value"],
    examples: [
      { situation: "기업 인수 가격을 결정할 때", en: "The acquirer offered a price equivalent to eight times the target company enterprise value to EBITDA.", ko: "인수자는 피인수 기업의 기업 가치 대 EBITDA의 8배에 해당하는 가격을 제시했어요." },
      { situation: "재무 모델링을 할 때", en: "Enterprise value is calculated by adding market capitalization to net debt and minority interests.", ko: "기업 가치는 시가총액에 순부채와 소수 지분을 더해 계산해요." },
      { situation: "기업 가치와 시가총액을 비교할 때", en: "Enterprise value is a more comprehensive measure than market capitalization as it accounts for a company debt load.", ko: "기업 가치는 회사의 부채 부담을 고려하기 때문에 시가총액보다 더 포괄적인 척도예요." },
      { situation: "비교 가치 평가를 분석할 때", en: "Comparing enterprise value multiples across industry peers helps identify undervalued acquisition targets.", ko: "업계 동종 기업들의 기업 가치 배수를 비교하면 저평가된 인수 대상을 파악하는 데 도움이 돼요." },
      { situation: "M&A 실사 과정에서", en: "Our valuation team computed enterprise value using both a discounted cash flow model and a comparable transactions analysis.", ko: "가치 평가팀은 할인 현금 흐름 모델과 비교 거래 분석 모두를 사용해 기업 가치를 계산했어요." },
      { situation: "투자자에게 성장 잠재력을 설명할 때", en: "Growing enterprise value over time is a key indicator that management is creating sustainable long-term value.", ko: "기업 가치를 시간이 지남에 따라 성장시키는 것은 경영진이 지속 가능한 장기적 가치를 창출하고 있다는 핵심 지표예요." },
      { situation: "레버리지 바이아웃을 구조화할 때", en: "Private equity firms use enterprise value as the base for determining the debt capacity in a leveraged buyout.", ko: "사모펀드 회사들은 레버리지 바이아웃에서 부채 용량을 결정하는 기준으로 기업 가치를 사용해요." },
      { situation: "주식 애널리스트 보고서를 검토할 때", en: "The analyst raised the price target after revising upward the enterprise value to revenue multiple for the sector.", ko: "애널리스트는 해당 부문의 기업 가치 대 매출 배수를 상향 조정한 후 목표 주가를 높였어요." },
      { situation: "기업 전략을 수립할 때", en: "Management tracks enterprise value growth as the ultimate measure of strategic execution success.", ko: "경영진은 전략 실행 성공의 궁극적인 척도로 기업 가치 성장을 추적해요." },
      { situation: "회사 매각을 준비할 때", en: "Maximizing enterprise value before a sale requires improving margins, reducing debt, and demonstrating growth momentum.", ko: "매각 전 기업 가치를 극대화하려면 마진을 개선하고 부채를 줄이고 성장 모멘텀을 보여줘야 해요." }
    ],
    level: "800"
  },
  {
    id: 215,
    word: "due diligence",
    pronunciation: "djuː ˈdɪl.ɪ.dʒəns",
    pos: "n.",
    meaning: "실사, 기업 조사",
    synonyms: ["due care investigation", "business investigation", "vetting process"],
    examples: [
      { situation: "M&A 거래 전에", en: "The acquiring company conducted six weeks of due diligence before finalizing the acquisition agreement.", ko: "인수 회사는 인수 계약을 확정하기 전에 6주간의 실사를 수행했어요." },
      { situation: "신규 공급업체를 심사할 때", en: "Our vendor onboarding process requires due diligence covering financial stability, compliance record, and operational capacity.", ko: "공급업체 온보딩 프로세스는 재무 안정성, 컴플라이언스 기록, 운영 역량을 다루는 실사를 요구해요." },
      { situation: "투자 결정을 내릴 때", en: "Venture capital investors perform due diligence on the management team, market size, and technology before investing.", ko: "벤처 자본 투자자들은 투자 전에 경영팀, 시장 규모, 기술에 대해 실사를 수행해요." },
      { situation: "파트너십을 체결하기 전에", en: "Completing due diligence on the potential partner revealed undisclosed liabilities that changed the deal terms.", ko: "잠재적 파트너에 대한 실사를 완료하면서 거래 조건을 바꾼 미공개 부채가 드러났어요." },
      { situation: "법적 위험을 평가할 때", en: "Legal due diligence examines pending litigation, regulatory violations, and intellectual property ownership.", ko: "법적 실사는 계류 중인 소송, 규제 위반, 지적 재산권 소유를 검토해요." },
      { situation: "부동산 투자를 검토할 때", en: "Before purchasing the commercial property, the team completed financial, environmental, and structural due diligence.", ko: "상업용 부동산을 구매하기 전에 팀은 재무적, 환경적, 구조적 실사를 완료했어요." },
      { situation: "이사회에 투자안을 제출할 때", en: "The investment committee required a comprehensive due diligence report before approving the capital commitment.", ko: "투자 위원회는 자본 약정을 승인하기 전에 포괄적인 실사 보고서를 요구했어요." },
      { situation: "인사 채용 리스크를 관리할 때", en: "Background checks are a form of due diligence performed on senior executives before finalizing employment.", ko: "신원 조회는 채용을 확정하기 전에 고위 임원에 대해 수행하는 실사의 한 형태예요." },
      { situation: "핀테크 기업을 평가할 때", en: "Technology due diligence assesses the scalability, security, and intellectual property status of the target platform.", ko: "기술 실사는 목표 플랫폼의 확장성, 보안, 지적 재산권 상태를 평가해요." },
      { situation: "거래 실패를 예방하려 할 때", en: "Thorough due diligence reduces the risk of post-acquisition surprises that can destroy deal value.", ko: "철저한 실사는 거래 가치를 파괴할 수 있는 인수 후 놀라움의 위험을 줄여요." }
    ],
    level: "800"
  },
  {
    id: 216,
    word: "term sheet",
    pronunciation: "tɜːm ʃiːt",
    pos: "n.",
    meaning: "투자 조건 제안서, 텀 시트",
    synonyms: ["heads of terms", "investment proposal", "deal term summary"],
    examples: [
      { situation: "스타트업 투자 협상을 할 때", en: "The venture capital firm issued a term sheet outlining a 5-million-dollar Series A investment at a 20-million-dollar valuation.", ko: "벤처 자본 회사는 2천만 달러 가치 평가에 500만 달러 시리즈 A 투자를 개요로 하는 텀 시트를 발행했어요." },
      { situation: "M&A 초기 단계에서", en: "Both parties signed the non-binding term sheet before instructing legal teams to prepare the definitive acquisition agreement.", ko: "양측은 법무팀에 최종 인수 계약서 준비를 지시하기 전에 비구속적 텀 시트에 서명했어요." },
      { situation: "투자 조건을 협상할 때", en: "The founders negotiated the anti-dilution provisions in the term sheet before agreeing to the investment.", ko: "창업자들은 투자에 동의하기 전에 텀 시트의 반희석화 조항을 협상했어요." },
      { situation: "여러 투자자 제안을 비교할 때", en: "Comparing term sheets from three investors helped the startup identify the most founder-friendly offer.", ko: "세 투자자의 텀 시트를 비교하면서 스타트업이 창업자에게 가장 우호적인 제안을 파악하는 데 도움이 됐어요." },
      { situation: "변호사를 고용하여 검토받을 때", en: "The startup hired a specialist attorney to review the term sheet before proceeding to final negotiations.", ko: "스타트업은 최종 협상을 진행하기 전에 텀 시트를 검토하기 위해 전문 변호사를 고용했어요." },
      { situation: "이사회 운영 조항을 논의할 때", en: "The term sheet included board composition requirements, giving the investor the right to appoint one director.", ko: "텀 시트에는 투자자에게 이사 1명을 임명할 권리를 부여하는 이사회 구성 요건이 포함됐어요." },
      { situation: "투자자 관계를 구축할 때", en: "Receiving a term sheet from a reputable investor adds credibility and helps attract additional co-investors.", ko: "평판 있는 투자자로부터 텀 시트를 받으면 신뢰성이 높아지고 추가 공동 투자자를 유치하는 데 도움이 돼요." },
      { situation: "인수 협상 전략을 수립할 때", en: "The term sheet established a 60-day exclusivity period for completing due diligence and negotiating final documents.", ko: "텀 시트는 실사 완료와 최종 문서 협상을 위한 60일 독점 기간을 수립했어요." },
      { situation: "조건을 이해하려 할 때", en: "Liquidation preference terms in a term sheet determine the order in which investors are paid in an exit scenario.", ko: "텀 시트의 청산 우선권 조건은 출구 시나리오에서 투자자들이 지급받는 순서를 결정해요." },
      { situation: "가치 평가를 논의할 때", en: "Disagreements over valuation are the most common reason term sheet negotiations stall before closing.", ko: "가치 평가에 대한 의견 불일치가 마감 전에 텀 시트 협상이 중단되는 가장 흔한 이유예요." }
    ],
    level: "800"
  },
  {
    id: 217,
    word: "closing conditions",
    pronunciation: "ˈkləʊ.zɪŋ kənˈdɪʃ.ənz",
    pos: "n.",
    meaning: "거래 완결 조건",
    synonyms: ["conditions precedent", "deal completion requirements", "transaction conditions"],
    examples: [
      { situation: "M&A 계약을 검토할 때", en: "The acquisition agreement specifies closing conditions including regulatory approval and lender consent.", ko: "인수 계약은 규제 승인과 대출자 동의를 포함한 거래 완결 조건을 명시해요." },
      { situation: "거래 완결 일정을 수립할 때", en: "Satisfying all closing conditions is estimated to take between 60 and 90 days from signing.", ko: "모든 거래 완결 조건을 충족하는 데는 서명 후 60~90일이 걸릴 것으로 추정돼요." },
      { situation: "법무팀 계약 검토에서", en: "Legal counsel prepared a checklist of all closing conditions to track completion progress on a daily basis.", ko: "법률 고문은 매일 완료 진행 상황을 추적하기 위해 모든 거래 완결 조건 체크리스트를 준비했어요." },
      { situation: "규제 승인을 기다릴 때", en: "Antitrust clearance is typically the most time-consuming of all closing conditions in large mergers.", ko: "독점 금지 허가는 일반적으로 대규모 합병에서 모든 거래 완결 조건 중 가장 시간이 많이 걸려요." },
      { situation: "거래 위험을 평가할 때", en: "Failure to satisfy material closing conditions by the agreed deadline gives either party the right to terminate.", ko: "합의된 마감일까지 중요한 거래 완결 조건을 충족하지 못하면 어느 쪽에든 종료 권리가 생겨요." },
      { situation: "고용 계약을 체결할 때", en: "The employment contract is contingent on the successful completion of all closing conditions, including a background check.", ko: "고용 계약은 신원 조회를 포함한 모든 거래 완결 조건의 성공적인 완료에 달려 있어요." },
      { situation: "파이낸싱을 확보할 때", en: "One of the closing conditions requires the buyer to demonstrate committed financing before the deal proceeds.", ko: "거래 완결 조건 중 하나는 거래가 진행되기 전에 구매자가 약정된 자금 조달을 입증하도록 요구해요." },
      { situation: "현재 진행 상황을 이해관계자에게 보고할 때", en: "Management provided the board with a weekly update on the status of each outstanding closing condition.", ko: "경영진은 이사회에 각 미결 거래 완결 조건의 상태에 대한 주간 업데이트를 제공했어요." },
      { situation: "복잡한 합작 투자를 설립할 때", en: "The joint venture closing conditions included transferring key contracts and obtaining partner entity approvals.", ko: "합작 투자 거래 완결 조건에는 주요 계약 이전과 파트너 법인 승인 취득이 포함됐어요." },
      { situation: "거래 타임라인을 압박받을 때", en: "Both parties agreed to waive certain closing conditions to accelerate the timeline due to competitive pressure.", ko: "경쟁적 압박 때문에 타임라인을 가속화하기 위해 양측은 특정 거래 완결 조건을 포기하는 데 동의했어요." }
    ],
    level: "800"
  },
  {
    id: 219,
    word: "code review",
    pronunciation: "kəʊd rɪˈvjuː",
    pos: "n.",
    meaning: "코드 리뷰",
    synonyms: ["peer code review", "software review", "technical review"],
    examples: [
      { situation: "소프트웨어 품질을 관리할 때", en: "All code changes must pass a code review by at least two senior engineers before merging into the main branch.", ko: "모든 코드 변경 사항은 메인 브랜치에 병합되기 전에 최소 두 명의 시니어 엔지니어의 코드 리뷰를 통과해야 해요." },
      { situation: "신규 개발자를 온보딩할 때", en: "Participating in code reviews is one of the fastest ways for new developers to learn the team coding standards.", ko: "코드 리뷰에 참여하는 것은 신규 개발자들이 팀 코딩 기준을 빠르게 배우는 방법 중 하나예요." },
      { situation: "버그 비율을 줄이려 할 때", en: "Implementing mandatory code reviews reduced the number of production bugs by 35 percent over six months.", ko: "필수 코드 리뷰를 구현하면서 6개월 만에 프로덕션 버그 수가 35% 감소했어요." },
      { situation: "보안 취약점을 발견할 때", en: "Security-focused code reviews identify vulnerabilities such as SQL injection and authentication weaknesses early in development.", ko: "보안 중심 코드 리뷰는 개발 초기에 SQL 인젝션 및 인증 취약점과 같은 취약점을 파악해요." },
      { situation: "팀 지식을 공유할 때", en: "Code reviews spread knowledge across the team by ensuring no single engineer owns a critical part of the codebase.", ko: "코드 리뷰는 어떤 단일 엔지니어도 코드베이스의 중요한 부분을 독점하지 않도록 함으로써 팀 전반에 지식을 전파해요." },
      { situation: "스프린트 계획에 시간을 배분할 때", en: "Sprint planning allocates dedicated time for code reviews to prevent them from becoming a bottleneck.", ko: "스프린트 계획은 코드 리뷰가 병목 현상이 되지 않도록 전용 시간을 배분해요." },
      { situation: "원격 팀에서 협업할 때", en: "Asynchronous code reviews using pull request comments enable distributed teams to collaborate effectively.", ko: "풀 리퀘스트 댓글을 사용한 비동기 코드 리뷰는 분산된 팀이 효과적으로 협업할 수 있게 해요." },
      { situation: "코드 품질 기준을 수립할 때", en: "The engineering team created a code review checklist covering readability, test coverage, and security standards.", ko: "엔지니어링팀은 가독성, 테스트 커버리지, 보안 기준을 다루는 코드 리뷰 체크리스트를 만들었어요." },
      { situation: "마감일 압박을 받을 때", en: "Skipping code reviews to meet a deadline often creates technical debt that costs more to fix later.", ko: "마감일을 맞추기 위해 코드 리뷰를 건너뛰면 나중에 수정하는 데 더 많은 비용이 드는 기술 부채가 생겨요." },
      { situation: "자동화 도구를 보완으로 활용할 때", en: "Automated testing tools complement but do not replace the judgment and knowledge sharing that code reviews provide.", ko: "자동화된 테스트 도구는 코드 리뷰가 제공하는 판단력과 지식 공유를 보완하지만 대체하지는 않아요." }
    ],
    level: "800"
  },
  {
    id: 220,
    word: "deployment pipeline",
    pronunciation: "dɪˈplɔɪ.mənt ˈpaɪp.laɪn",
    pos: "n.",
    meaning: "배포 파이프라인",
    synonyms: ["CI/CD pipeline", "release pipeline", "continuous delivery pipeline"],
    examples: [
      { situation: "소프트웨어 릴리스 프로세스를 설명할 때", en: "Our deployment pipeline automates testing, builds, and release approvals to accelerate software delivery.", ko: "배포 파이프라인은 소프트웨어 납품을 가속화하기 위해 테스트, 빌드, 릴리스 승인을 자동화해요." },
      { situation: "DevOps 관행을 도입할 때", en: "Building a robust deployment pipeline was the first step in our DevOps transformation.", ko: "견고한 배포 파이프라인을 구축하는 것이 DevOps 전환의 첫 번째 단계였어요." },
      { situation: "릴리스 빈도를 높이려 할 때", en: "With a fully automated deployment pipeline, the team went from weekly to daily releases within six months.", ko: "완전히 자동화된 배포 파이프라인으로 팀이 6개월 내에 주간에서 일간 릴리스로 전환됐어요." },
      { situation: "프로덕션 사고를 예방할 때", en: "A well-configured deployment pipeline runs comprehensive tests automatically to catch issues before they reach production.", ko: "잘 구성된 배포 파이프라인은 프로덕션에 도달하기 전에 문제를 발견하기 위해 자동으로 포괄적인 테스트를 실행해요." },
      { situation: "클라우드로 마이그레이션할 때", en: "Migrating to the cloud required rebuilding the deployment pipeline to support containerized microservices.", ko: "클라우드로 마이그레이션하면서 컨테이너화된 마이크로서비스를 지원하기 위해 배포 파이프라인을 재구축해야 했어요." },
      { situation: "여러 환경을 관리할 때", en: "The deployment pipeline promotes code from development through testing, staging, and finally production environments.", ko: "배포 파이프라인은 코드를 개발에서 테스트, 스테이징, 최종적으로 프로덕션 환경으로 승격시켜요." },
      { situation: "보안 기준을 강화할 때", en: "Security scans were integrated into the deployment pipeline to detect vulnerabilities at every stage of the build process.", ko: "빌드 프로세스의 모든 단계에서 취약점을 감지하기 위해 보안 스캔이 배포 파이프라인에 통합됐어요." },
      { situation: "팀 속도를 측정할 때", en: "Monitoring deployment pipeline metrics such as lead time and deployment frequency helps identify bottlenecks.", ko: "리드 타임 및 배포 빈도와 같은 배포 파이프라인 지표를 모니터링하면 병목 현상을 파악하는 데 도움이 돼요." },
      { situation: "컴플라이언스 요건을 충족할 때", en: "The deployment pipeline includes an audit trail that documents who approved each release and when it was deployed.", ko: "배포 파이프라인에는 각 릴리스를 누가 승인했는지 및 언제 배포됐는지를 문서화하는 감사 추적이 포함돼요." },
      { situation: "인수 후 기술 통합을 할 때", en: "Post-acquisition, harmonizing the deployment pipelines of both companies reduced release cycle time by 40 percent.", ko: "인수 후 두 회사의 배포 파이프라인을 조화시키면서 릴리스 주기 시간이 40% 단축됐어요." }
    ],
    level: "800"
  },
  {
    id: 221,
    word: "quota attainment",
    pronunciation: "ˈkwəʊ.tə əˈteɪn.mənt",
    pos: "n.",
    meaning: "할당량 달성, 목표 달성률",
    synonyms: ["quota achievement", "target attainment", "sales target fulfillment"],
    examples: [
      { situation: "영업팀 성과를 평가할 때", en: "The team average quota attainment for Q3 was 112 percent, driven by three major enterprise deals.", ko: "세 개의 주요 기업 거래에 힘입어 3분기 팀 평균 할당량 달성률이 112%였어요." },
      { situation: "영업 인센티브를 설계할 때", en: "Commission rates accelerate significantly once a rep reaches 100 percent quota attainment.", ko: "담당자가 할당량 달성률 100%에 도달하면 커미션율이 크게 가속돼요." },
      { situation: "영업 예측을 수립할 때", en: "Tracking quota attainment by week allows the sales manager to identify deals that need additional support.", ko: "주별로 할당량 달성률을 추적하면 영업 관리자가 추가 지원이 필요한 거래를 파악할 수 있어요." },
      { situation: "영업팀 구조를 최적화할 때", en: "Low quota attainment rates among a specific team prompted a review of territory size and account assignments.", ko: "특정 팀의 낮은 할당량 달성률이 영역 크기 및 계정 배정 검토를 촉구했어요." },
      { situation: "이사회에 영업 성과를 보고할 때", en: "Quota attainment across the sales organization dropped to 78 percent in Q4 due to increased competition.", ko: "경쟁 심화로 4분기 영업 조직 전반의 할당량 달성률이 78%로 하락했어요." },
      { situation: "영업팀을 채용할 때", en: "Candidates with a consistent track record of over 100 percent quota attainment are preferred for senior sales roles.", ko: "할당량 달성률 100% 이상의 일관된 실적을 보유한 후보자들이 시니어 영업 직위에 선호돼요." },
      { situation: "영업 코칭 세션에서", en: "The sales manager reviewed quota attainment trends to identify reps who need coaching on pipeline management.", ko: "영업 관리자는 파이프라인 관리 코칭이 필요한 담당자를 파악하기 위해 할당량 달성률 추세를 검토했어요." },
      { situation: "연간 목표를 재설정할 때", en: "Setting unrealistic quotas leads to low quota attainment, which demotivates the team and increases turnover.", ko: "비현실적인 할당량 설정은 팀 사기를 저하시키고 이직률을 높이는 낮은 할당량 달성률로 이어져요." },
      { situation: "영업과 마케팅을 조율할 때", en: "Improved marketing lead quality contributed directly to a 15-point increase in the team quota attainment rate.", ko: "개선된 마케팅 리드 품질이 팀 할당량 달성률의 15%p 증가에 직접 기여했어요." },
      { situation: "CRM 데이터를 분석할 때", en: "CRM analytics provide real-time quota attainment dashboards that help reps stay on track throughout the quarter.", ko: "CRM 분석은 담당자들이 분기 내내 목표에 맞게 유지하는 데 도움이 되는 실시간 할당량 달성률 대시보드를 제공해요." }
    ],
    level: "800"
  },
  {
    id: 225,
    word: "personal guarantee",
    pronunciation: "ˈpɜː.sən.əl ˌɡær.ənˈtiː",
    pos: "n.",
    meaning: "개인 보증",
    synonyms: ["personal surety", "individual guarantee", "personal liability pledge"],
    examples: [
      { situation: "소기업 대출을 신청할 때", en: "The bank required a personal guarantee from the business owner before approving the commercial loan.", ko: "은행은 사업 대출을 승인하기 전에 사업주로부터 개인 보증을 요구했어요." },
      { situation: "임대 계약을 체결할 때", en: "The landlord insisted on a personal guarantee from the company directors as the business had a limited credit history.", ko: "임대인은 회사의 신용 이력이 제한적이기 때문에 회사 이사들의 개인 보증을 요구했어요." },
      { situation: "법적 의무를 이해할 때", en: "Signing a personal guarantee means you are personally liable for the debt if the business cannot repay it.", ko: "개인 보증에 서명하는 것은 사업체가 상환하지 못할 경우 부채에 개인적으로 책임이 있음을 의미해요." },
      { situation: "신규 공급업체와 신용 조건을 설정할 때", en: "For startups with limited credit history, suppliers often require a personal guarantee from the founder.", ko: "신용 이력이 제한적인 스타트업의 경우 공급업체들은 종종 창업자의 개인 보증을 요구해요." },
      { situation: "대출 조건을 재협상할 때", en: "As the company track record strengthened, the bank agreed to remove the personal guarantee from the loan agreement.", ko: "회사의 실적이 강화됨에 따라 은행은 대출 계약에서 개인 보증을 제거하는 데 동의했어요." },
      { situation: "파트너십 위험을 평가할 때", en: "Directors should carefully consider the implications of signing a personal guarantee before agreeing to business loans.", ko: "이사들은 사업 대출에 동의하기 전에 개인 보증 서명의 의미를 신중하게 고려해야 해요." },
      { situation: "프랜차이즈 계약을 검토할 때", en: "Most franchise agreements require the franchisee to provide a personal guarantee covering the lease obligations.", ko: "대부분의 프랜차이즈 계약은 가맹점이 임대 의무를 포함하는 개인 보증을 제공하도록 요구해요." },
      { situation: "사업 구조를 설계할 때", en: "Forming a limited liability company does not necessarily protect directors from personal guarantee obligations.", ko: "유한 책임 회사를 설립한다고 해서 반드시 이사들이 개인 보증 의무로부터 보호받는 것은 아니에요." },
      { situation: "파산 위험을 설명할 때", en: "If the company enters liquidation, creditors holding a personal guarantee can pursue the director personal assets.", ko: "회사가 청산에 들어가면 개인 보증을 보유한 채권자들이 이사의 개인 자산을 추구할 수 있어요." },
      { situation: "금융 전문가에게 조언을 구할 때", en: "Before signing a personal guarantee, consult a legal adviser to understand the full scope of your liability.", ko: "개인 보증에 서명하기 전에 책임의 전체 범위를 이해하기 위해 법률 자문가와 상담하세요." }
    ],
    level: "800"
  },
  {
    id: 229,
    word: "customer churn",
    pronunciation: "ˈkʌs.tə.mər tʃɜːn",
    pos: "n.",
    meaning: "고객 이탈",
    synonyms: ["customer attrition", "client churn", "customer loss rate"],
    examples: [
      { situation: "구독 서비스 성과를 분석할 때", en: "Reducing customer churn from 8 to 4 percent annually would nearly double our revenue growth rate.", ko: "고객 이탈을 연간 8%에서 4%로 줄이면 매출 성장률이 거의 두 배가 될 거예요." },
      { situation: "고객 성공팀 목표를 설정할 때", en: "The customer success team is measured primarily on its ability to reduce customer churn across all account tiers.", ko: "고객 성공팀은 주로 모든 계정 계층에서 고객 이탈을 줄이는 능력으로 평가받아요." },
      { situation: "이탈 원인을 분석할 때", en: "Post-churn interviews revealed that poor product usability was the primary driver of customer churn.", ko: "이탈 후 인터뷰에서 제품 사용성 저하가 고객 이탈의 주요 원인임이 드러났어요." },
      { situation: "투자자에게 SaaS 지표를 설명할 때", en: "Investors closely monitor customer churn as a leading indicator of product-market fit and customer satisfaction.", ko: "투자자들은 제품-시장 적합성과 고객 만족도의 선행 지표로 고객 이탈을 면밀히 모니터링해요." },
      { situation: "가격 인상 영향을 예측할 때", en: "Price sensitivity analysis estimated that a 15 percent price increase would result in 6 percent customer churn.", ko: "가격 민감도 분석에서 15%의 가격 인상이 6%의 고객 이탈로 이어질 것으로 추정됐어요." },
      { situation: "제품 개선 우선순위를 결정할 때", en: "Feature development was reprioritized based on customer churn data showing which pain points caused cancellations.", ko: "어떤 문제점이 취소를 야기했는지 보여주는 고객 이탈 데이터를 바탕으로 기능 개발이 재우선순위화됐어요." },
      { situation: "조기 개입 프로그램을 설계할 때", en: "Health score monitoring allows customer success managers to intervene early and prevent customer churn.", ko: "건강 점수 모니터링은 고객 성공 관리자들이 조기에 개입해 고객 이탈을 방지할 수 있게 해요." },
      { situation: "LTV를 계산할 때", en: "Customer lifetime value is inversely related to customer churn - the lower the churn, the higher the lifetime value.", ko: "고객 생애 가치는 고객 이탈과 반비례 관계에 있어요. 이탈률이 낮을수록 생애 가치가 높아요." },
      { situation: "마케팅 ROI를 계산할 때", en: "High customer churn makes it difficult to recoup customer acquisition costs and achieve positive ROI.", ko: "높은 고객 이탈은 고객 획득 비용을 회수하고 긍정적인 ROI를 달성하기 어렵게 만들어요." },
      { situation: "이사회에 사업 건전성을 보고할 때", en: "The board flagged elevated customer churn as a risk that required immediate product and service improvements.", ko: "이사회는 즉각적인 제품 및 서비스 개선이 필요한 위험으로 높은 고객 이탈을 지적했어요." }
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
console.log('Batch 11 done: IDs 211,213,215,216,217,219,220,221,225,229 replaced.');
