// Batch 10: IDs 195,196,199,200,203,204,206,207,209,210
// meticulous->agile methodology, microeconomic->cybersecurity, moratorium->crowdfunding
// nascent->conversion rate, nuance->bounce rate, obligor->payroll processing
// omnibus->benefits administration, ordinance->retirement plan, paradigm->health insurance
// pecuniary->wire transfer
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 195,
    word: "agile methodology",
    pronunciation: "ˈædʒ.aɪl meˈθɒd.ə.lə.dʒi",
    pos: "n.",
    meaning: "애자일 방법론",
    synonyms: ["agile framework", "scrum methodology", "iterative development"],
    examples: [
      { situation: "소프트웨어 개발 팀 운영 방식을 설명할 때", en: "Adopting agile methodology allowed the team to deliver working software every two weeks instead of every six months.", ko: "애자일 방법론을 도입하면서 팀이 6개월마다 대신 2주마다 작동하는 소프트웨어를 납품할 수 있게 됐어요." },
      { situation: "프로젝트 관리 방식을 선택할 때", en: "The project manager chose agile methodology over traditional waterfall due to frequently changing requirements.", ko: "프로젝트 관리자는 자주 변경되는 요구사항 때문에 전통적인 워터폴보다 애자일 방법론을 선택했어요." },
      { situation: "팀 생산성을 개선하려 할 때", en: "Agile methodology improved team productivity by reducing documentation overhead and promoting collaboration.", ko: "애자일 방법론은 문서화 부담을 줄이고 협업을 촉진함으로써 팀 생산성을 향상시켰어요." },
      { situation: "비IT 부서에 애자일을 적용할 때", en: "Marketing adopted agile methodology to manage campaign work, enabling faster response to market changes.", ko: "마케팅 부서는 시장 변화에 더 빠르게 대응할 수 있도록 캠페인 업무를 관리하기 위해 애자일 방법론을 채택했어요." },
      { situation: "제품 개발 속도를 높이려 할 때", en: "Agile methodology enables teams to respond quickly to customer feedback by delivering incremental improvements.", ko: "애자일 방법론은 팀이 점진적 개선을 제공함으로써 고객 피드백에 신속하게 대응할 수 있도록 해요." },
      { situation: "원격 팀 운영 방식을 개선할 때", en: "Our distributed engineering team applies agile methodology through daily virtual stand-ups and bi-weekly sprint reviews.", ko: "분산된 엔지니어링 팀은 일일 가상 스탠드업과 격주 스프린트 검토를 통해 애자일 방법론을 적용해요." },
      { situation: "관리자 교육 프로그램에서", en: "Managers received training on agile methodology to better support their teams during the digital transformation.", ko: "관리자들은 디지털 전환 중에 팀을 더 잘 지원하기 위해 애자일 방법론에 대한 교육을 받았어요." },
      { situation: "기업 전환을 이끌 때", en: "Scaling agile methodology across the enterprise required standardizing practices while allowing team-level flexibility.", ko: "기업 전반에 걸쳐 애자일 방법론을 확장하려면 팀 수준의 유연성을 허용하면서 관행을 표준화하는 것이 필요했어요." },
      { situation: "투자자에게 개발 접근법을 설명할 때", en: "The startup pitch emphasized agile methodology as a key factor in their ability to iterate quickly based on user data.", ko: "스타트업 피치는 사용자 데이터를 기반으로 빠르게 반복하는 능력의 핵심 요인으로 애자일 방법론을 강조했어요." },
      { situation: "소프트웨어 납품 품질을 높이려 할 때", en: "Agile methodology reduced the bug rate in production releases by building quality checks into every sprint cycle.", ko: "애자일 방법론은 모든 스프린트 주기에 품질 점검을 내재화함으로써 프로덕션 릴리스의 버그 비율을 줄였어요." }
    ],
    level: "800"
  },
  {
    id: 196,
    word: "cybersecurity",
    pronunciation: "ˌsaɪ.bəˈsek.jʊər.ɪ.ti",
    pos: "n.",
    meaning: "사이버 보안",
    synonyms: ["information security", "digital security", "cyber defense"],
    examples: [
      { situation: "IT 전략을 수립할 때", en: "Cybersecurity has become a top priority for boards of directors as digital threats continue to evolve.", ko: "디지털 위협이 계속 진화함에 따라 사이버 보안이 이사회의 최우선 사항이 됐어요." },
      { situation: "보안 침해 사고를 대응할 때", en: "The cybersecurity team responded to the breach within minutes, isolating the affected systems to limit data exposure.", ko: "사이버 보안팀이 몇 분 내에 침해에 대응해 데이터 노출을 제한하기 위해 영향받은 시스템을 격리했어요." },
      { situation: "임직원 교육 프로그램을 설계할 때", en: "Annual cybersecurity training is mandatory for all employees to reduce the risk of phishing and social engineering attacks.", ko: "피싱 및 소셜 엔지니어링 공격 위험을 줄이기 위해 연간 사이버 보안 교육이 모든 직원에게 의무화됐어요." },
      { situation: "IT 예산을 편성할 때", en: "The board approved a 20 percent increase in the cybersecurity budget to strengthen endpoint and network protection.", ko: "이사회는 엔드포인트 및 네트워크 보호를 강화하기 위해 사이버 보안 예산을 20% 늘리는 것을 승인했어요." },
      { situation: "공급업체 위험을 평가할 때", en: "Our vendor onboarding process includes a cybersecurity assessment to ensure third-party partners meet our security standards.", ko: "공급업체 온보딩 프로세스에는 제3자 파트너가 우리의 보안 기준을 충족하는지 확인하기 위한 사이버 보안 평가가 포함돼요." },
      { situation: "원격 근무 환경을 보호할 때", en: "Transitioning to remote work expanded the cybersecurity perimeter, requiring stronger endpoint protection policies.", ko: "원격 근무로의 전환이 사이버 보안 경계를 확장해 더 강력한 엔드포인트 보호 정책을 필요로 했어요." },
      { situation: "컴플라이언스 요건을 충족할 때", en: "Cybersecurity compliance with GDPR and ISO 27001 is audited annually by an independent third party.", ko: "GDPR 및 ISO 27001에 대한 사이버 보안 컴플라이언스는 독립적인 제3자에 의해 매년 감사받아요." },
      { situation: "M&A 실사를 진행할 때", en: "Cybersecurity due diligence revealed critical vulnerabilities in the target company infrastructure.", ko: "사이버 보안 실사에서 피인수 기업 인프라의 심각한 취약점이 드러났어요." },
      { situation: "위기 대응 계획을 수립할 때", en: "A cybersecurity incident response plan ensures the company can quickly contain breaches and restore operations.", ko: "사이버 보안 인시던트 대응 계획은 회사가 침해를 신속하게 억제하고 운영을 복구할 수 있도록 해요." },
      { situation: "디지털 전환 전략에서", en: "As businesses become more digital, cybersecurity must be integrated into every aspect of the technology strategy.", ko: "기업들이 더 디지털화됨에 따라 사이버 보안이 기술 전략의 모든 측면에 통합되어야 해요." }
    ],
    level: "800"
  },
  {
    id: 199,
    word: "crowdfunding",
    pronunciation: "ˈkraʊd.fʌnd.ɪŋ",
    pos: "n.",
    meaning: "크라우드펀딩",
    synonyms: ["crowd financing", "community funding", "public fundraising"],
    examples: [
      { situation: "스타트업 자금 조달 전략을 논의할 때", en: "The hardware startup raised 500,000 dollars through a crowdfunding campaign before approaching traditional investors.", ko: "하드웨어 스타트업은 전통적인 투자자에게 접근하기 전에 크라우드펀딩 캠페인을 통해 50만 달러를 모금했어요." },
      { situation: "신제품 수요를 검증할 때", en: "Crowdfunding is an effective way to validate market demand before investing in full-scale production.", ko: "크라우드펀딩은 전면적 생산에 투자하기 전에 시장 수요를 검증하는 효과적인 방법이에요." },
      { situation: "마케팅 전략으로 활용할 때", en: "A successful crowdfunding campaign builds an early community of loyal customers who become brand advocates.", ko: "성공적인 크라우드펀딩 캠페인은 브랜드 지지자가 되는 충성 고객의 초기 커뮤니티를 구축해요." },
      { situation: "소셜 미디어와 연계할 때", en: "The crowdfunding campaign went viral on social media, attracting backers from 35 different countries.", ko: "크라우드펀딩 캠페인이 소셜 미디어에서 바이럴되어 35개국의 후원자들을 유치했어요." },
      { situation: "다양한 플랫폼을 비교할 때", en: "Choosing the right crowdfunding platform depends on whether the project is product-based, creative, or equity-oriented.", ko: "올바른 크라우드펀딩 플랫폼을 선택하는 것은 프로젝트가 제품 기반, 창작, 또는 지분 지향적인지에 달려 있어요." },
      { situation: "지역 사회 프로젝트를 지원할 때", en: "Local businesses are increasingly using crowdfunding to fund expansions and renovations with community support.", ko: "지역 기업들이 지역사회 지원으로 확장 및 리노베이션 자금을 조달하기 위해 크라우드펀딩을 점점 더 많이 사용하고 있어요." },
      { situation: "투자자 유치 준비를 할 때", en: "A crowdfunding campaign that exceeds its target demonstrates social proof that can impress institutional investors.", ko: "목표를 초과 달성하는 크라우드펀딩 캠페인은 기관 투자자들에게 인상을 줄 수 있는 사회적 증거를 보여줘요." },
      { situation: "규제 요건을 이해할 때", en: "Equity crowdfunding is subject to securities regulations that vary significantly by country.", ko: "지분형 크라우드펀딩은 국가마다 상당히 다른 증권 규정의 적용을 받아요." },
      { situation: "실패한 캠페인을 분석할 때", en: "A poorly executed crowdfunding campaign can damage brand credibility if promises to backers are not fulfilled.", ko: "잘못 실행된 크라우드펀딩 캠페인은 후원자들에 대한 약속이 이행되지 않으면 브랜드 신뢰성을 손상시킬 수 있어요." },
      { situation: "소기업 자금 조달 옵션을 설명할 때", en: "For small businesses without credit history, crowdfunding offers an alternative to traditional bank loans.", ko: "신용 이력이 없는 소기업들에게 크라우드펀딩은 전통적인 은행 대출의 대안을 제공해요." }
    ],
    level: "800"
  },
  {
    id: 200,
    word: "conversion rate",
    pronunciation: "kənˈvɜː.ʃən reɪt",
    pos: "n.",
    meaning: "전환율",
    synonyms: ["conversion ratio", "close rate", "success rate"],
    examples: [
      { situation: "디지털 마케팅 성과를 분석할 때", en: "Our website conversion rate improved from 1.5 to 3.2 percent after redesigning the product pages.", ko: "제품 페이지를 재설계한 후 웹사이트 전환율이 1.5%에서 3.2%로 향상됐어요." },
      { situation: "영업 성과를 평가할 때", en: "The sales team conversion rate from qualified lead to closed deal stands at 22 percent this quarter.", ko: "이번 분기 적격 리드에서 성사 거래까지의 영업팀 전환율은 22%예요." },
      { situation: "이메일 마케팅 효과를 측정할 때", en: "Personalizing email subject lines increased the conversion rate by 18 percent compared to the previous campaign.", ko: "이메일 제목 줄을 개인화하면서 이전 캠페인에 비해 전환율이 18% 증가했어요." },
      { situation: "A/B 테스트를 설계할 때", en: "The A/B test measured conversion rate differences between two checkout page designs over a 14-day period.", ko: "A/B 테스트는 14일 기간 동안 두 가지 결제 페이지 디자인 간의 전환율 차이를 측정했어요." },
      { situation: "광고 캠페인을 최적화할 때", en: "By improving ad targeting, we doubled the conversion rate while reducing cost per acquisition by 30 percent.", ko: "광고 타겟팅을 개선함으로써 고객 획득 비용을 30% 줄이면서 전환율을 두 배로 높였어요." },
      { situation: "가격 전략을 검토할 때", en: "Offering a free trial increased our conversion rate from trial to paid subscription by 40 percent.", ko: "무료 체험을 제공하면서 체험에서 유료 구독으로의 전환율이 40% 증가했어요." },
      { situation: "영업 파이프라인을 분석할 때", en: "Tracking conversion rate at each stage of the funnel identifies where prospects are most likely to drop off.", ko: "퍼널의 각 단계에서 전환율을 추적하면 잠재 고객이 가장 많이 이탈할 가능성이 있는 지점을 파악해요." },
      { situation: "콜 센터 성과를 관리할 때", en: "The inbound call team improved their conversion rate from inquiry to sale by refining the consultation script.", ko: "인바운드 콜 팀이 상담 스크립트를 개선해 문의에서 판매로의 전환율을 향상시켰어요." },
      { situation: "랜딩 페이지를 최적화할 때", en: "A clear call-to-action button placement improved landing page conversion rate by 25 percent in user testing.", ko: "명확한 행동 유도 버튼 배치가 사용자 테스트에서 랜딩 페이지 전환율을 25% 향상시켰어요." },
      { situation: "투자자에게 성장 지표를 설명할 때", en: "Investors track conversion rate alongside customer acquisition cost to assess the unit economics of the business.", ko: "투자자들은 사업의 단위 경제학을 평가하기 위해 고객 획득 비용과 함께 전환율을 추적해요." }
    ],
    level: "800"
  },
  {
    id: 203,
    word: "bounce rate",
    pronunciation: "baʊns reɪt",
    pos: "n.",
    meaning: "이탈률",
    synonyms: ["exit rate", "single-page visit rate", "abandonment rate"],
    examples: [
      { situation: "웹사이트 성과를 분석할 때", en: "Our homepage bounce rate of 75 percent indicates that visitors are not finding what they are looking for quickly enough.", ko: "홈페이지 이탈률 75%는 방문자들이 원하는 것을 충분히 빠르게 찾지 못하고 있음을 나타내요." },
      { situation: "콘텐츠 품질을 평가할 때", en: "Pages with lower bounce rates tend to have more relevant content and faster loading times.", ko: "이탈률이 낮은 페이지는 더 관련성 있는 콘텐츠와 더 빠른 로딩 시간을 갖는 경향이 있어요." },
      { situation: "디지털 마케팅 캠페인을 최적화할 때", en: "Targeting more specific keywords reduced the bounce rate from paid search campaigns by 20 percentage points.", ko: "더 구체적인 키워드를 타겟팅하면서 유료 검색 캠페인의 이탈률이 20%p 감소했어요." },
      { situation: "이메일 마케팅을 관리할 때", en: "A high email bounce rate indicates outdated contact lists that need to be cleaned and verified.", ko: "높은 이메일 이탈률은 정리 및 검증이 필요한 오래된 연락처 목록을 나타내요." },
      { situation: "랜딩 페이지 효과를 측정할 때", en: "Redesigning the landing page reduced the bounce rate from 68 to 42 percent, significantly improving lead capture.", ko: "랜딩 페이지를 재설계하면서 이탈률이 68%에서 42%로 감소해 리드 캡처가 크게 향상됐어요." },
      { situation: "모바일 사용자 경험을 개선할 때", en: "Mobile users had a higher bounce rate due to slow loading times, which was resolved by optimizing image sizes.", ko: "모바일 사용자들은 느린 로딩 시간으로 더 높은 이탈률을 보였으며 이미지 크기 최적화로 해결됐어요." },
      { situation: "SEO 전략에 반영할 때", en: "Search engines factor in bounce rate as a signal of content relevance when ranking pages in search results.", ko: "검색 엔진은 검색 결과에서 페이지 순위를 매길 때 콘텐츠 관련성의 신호로 이탈률을 고려해요." },
      { situation: "사용자 경험 개선을 논의할 때", en: "A high bounce rate on product pages often signals that the information provided does not match buyer expectations.", ko: "제품 페이지의 높은 이탈률은 종종 제공된 정보가 구매자의 기대와 일치하지 않음을 나타내요." },
      { situation: "마케팅 보고서를 작성할 때", en: "Monthly analytics reports include bounce rate trends segmented by traffic source and device type.", ko: "월간 분석 보고서에는 트래픽 소스 및 기기 유형별로 세분화된 이탈률 추세가 포함돼요." },
      { situation: "A/B 테스트 결과를 해석할 때", en: "The test variant with a video introduction had a significantly lower bounce rate than the text-only control version.", ko: "동영상 소개가 있는 테스트 변형이 텍스트만 있는 대조 버전보다 훨씬 낮은 이탈률을 보였어요." }
    ],
    level: "800"
  },
  {
    id: 204,
    word: "payroll processing",
    pronunciation: "ˈpeɪ.rəʊl ˈprəʊ.ses.ɪŋ",
    pos: "n.",
    meaning: "급여 처리",
    synonyms: ["salary processing", "payroll administration", "wage processing"],
    examples: [
      { situation: "HR 운영 효율화를 논의할 때", en: "Automating payroll processing reduced errors and saved the HR team 20 hours of manual work each month.", ko: "급여 처리를 자동화하면서 오류가 줄고 HR팀의 매월 20시간의 수동 작업이 절감됐어요." },
      { situation: "신규 직원 입사 절차를 설명할 때", en: "New employees must complete their tax forms within the first week to be included in the monthly payroll processing cycle.", ko: "신규 직원들은 월간 급여 처리 주기에 포함되기 위해 첫 주 내에 세금 신고서를 작성해야 해요." },
      { situation: "아웃소싱 여부를 결정할 때", en: "Many small businesses outsource payroll processing to specialist providers to ensure compliance with tax laws.", ko: "많은 소기업들이 세금 법규 준수를 보장하기 위해 전문 제공업체에 급여 처리를 아웃소싱해요." },
      { situation: "글로벌 팀을 운영할 때", en: "Managing payroll processing across 15 countries requires expertise in local tax regulations and employment law.", ko: "15개국에 걸쳐 급여 처리를 관리하려면 현지 세금 규정과 고용법에 대한 전문 지식이 필요해요." },
      { situation: "급여 오류를 해결할 때", en: "A payroll processing error affected 50 employees and required immediate corrective action to issue supplemental payments.", ko: "급여 처리 오류가 50명의 직원에게 영향을 미쳐 추가 지급을 위한 즉각적인 시정 조치가 필요했어요." },
      { situation: "시스템 업그레이드를 계획할 때", en: "Integrating payroll processing with the HR information system improved data accuracy and reporting capabilities.", ko: "급여 처리를 HR 정보 시스템과 통합하면서 데이터 정확성과 보고 역량이 향상됐어요." },
      { situation: "컴플라이언스를 유지할 때", en: "Timely and accurate payroll processing is a legal obligation that carries penalties if deadlines are missed.", ko: "적시에 정확한 급여 처리는 마감일을 놓치면 처벌이 따르는 법적 의무예요." },
      { situation: "비용 효율성을 분석할 때", en: "Switching to cloud-based payroll processing reduced annual administration costs by 35 percent.", ko: "클라우드 기반 급여 처리로 전환하면서 연간 관리 비용이 35% 감소했어요." },
      { situation: "직원에게 급여 정책을 설명할 때", en: "The payroll processing schedule specifies that salaries are transferred on the last business day of each month.", ko: "급여 처리 일정은 급여가 매월 마지막 영업일에 이체된다고 명시해요." },
      { situation: "M&A 이후 직원을 통합할 때", en: "Post-acquisition payroll processing integration required aligning two different pay cycles and compensation structures.", ko: "인수 후 급여 처리 통합에는 두 가지 다른 지급 주기와 보상 구조를 조율하는 것이 필요했어요." }
    ],
    level: "800"
  },
  {
    id: 206,
    word: "benefits administration",
    pronunciation: "ˈben.ɪ.fɪts ədˌmɪn.ɪˈstreɪ.ʃən",
    pos: "n.",
    meaning: "복리후생 관리",
    synonyms: ["employee benefits management", "HR benefits", "perks administration"],
    examples: [
      { situation: "HR 시스템을 도입할 때", en: "Centralizing benefits administration on a single platform reduced processing time and improved employee self-service.", ko: "단일 플랫폼에 복리후생 관리를 중앙화하면서 처리 시간이 줄고 직원 셀프 서비스가 향상됐어요." },
      { situation: "직원 복리후생 패키지를 검토할 때", en: "Effective benefits administration ensures employees fully understand and utilize the benefits available to them.", ko: "효과적인 복리후생 관리는 직원들이 자신에게 제공되는 복리후생을 완전히 이해하고 활용하도록 해요." },
      { situation: "오픈 에볼루션 기간을 관리할 때", en: "During the annual open enrollment, the benefits administration team hosts information sessions to guide employee selections.", ko: "연간 오픈 에롤먼트 기간 동안 복리후생 관리팀은 직원 선택을 안내하기 위한 정보 세션을 개최해요." },
      { situation: "비용을 통제하려 할 때", en: "Streamlining benefits administration helped identify underutilized benefits and reallocate the budget more effectively.", ko: "복리후생 관리를 간소화하면서 활용도가 낮은 복리후생을 파악하고 예산을 더 효과적으로 재배분하는 데 도움이 됐어요." },
      { situation: "아웃소싱을 고려할 때", en: "Outsourcing benefits administration to a third-party provider freed up internal HR resources for strategic initiatives.", ko: "복리후생 관리를 제3자 공급업체에 아웃소싱하면서 전략적 이니셔티브를 위한 내부 HR 자원이 확보됐어요." },
      { situation: "글로벌 인력을 관리할 때", en: "International benefits administration requires adapting offerings to meet local legal requirements and cultural expectations.", ko: "국제 복리후생 관리는 현지 법적 요건과 문화적 기대를 충족하도록 혜택을 조정하는 것을 필요로 해요." },
      { situation: "직원 경험을 개선할 때", en: "A well-run benefits administration process enhances the employee experience and reduces unnecessary HR queries.", ko: "잘 운영된 복리후생 관리 프로세스는 직원 경험을 향상시키고 불필요한 HR 문의를 줄여요." },
      { situation: "신규 복리후생을 도입할 때", en: "Adding mental health benefits required updates to the benefits administration system and employee communication plans.", ko: "정신 건강 복리후생을 추가하면서 복리후생 관리 시스템과 직원 커뮤니케이션 계획에 업데이트가 필요했어요." },
      { situation: "컴플라이언스를 확보할 때", en: "Benefits administration teams must stay current with changing healthcare and pension legislation to remain compliant.", ko: "복리후생 관리팀은 컴플라이언스를 유지하기 위해 변화하는 건강보험 및 연금 법률을 최신 상태로 파악해야 해요." },
      { situation: "입사 시 신입 직원에게 설명할 때", en: "Benefits administration orientation helps new employees enroll in health insurance, retirement plans, and other programs.", ko: "복리후생 관리 오리엔테이션은 신규 직원들이 건강 보험, 퇴직 연금 및 기타 프로그램에 등록하는 데 도움을 줘요." }
    ],
    level: "800"
  },
  {
    id: 207,
    word: "retirement plan",
    pronunciation: "rɪˈtaɪər.mənt plæn",
    pos: "n.",
    meaning: "퇴직 연금, 은퇴 계획",
    synonyms: ["pension plan", "401k plan", "superannuation"],
    examples: [
      { situation: "직원 복리후생을 설명할 때", en: "The company retirement plan includes employer matching contributions of up to 4 percent of salary.", ko: "회사 퇴직 연금에는 급여의 최대 4%에 해당하는 고용주 매칭 기여금이 포함돼요." },
      { situation: "채용 오퍼를 논의할 때", en: "The generous retirement plan was a deciding factor for the candidate accepting the job over a higher-paying competitor offer.", ko: "넉넉한 퇴직 연금이 지원자가 더 높은 급여의 경쟁사 제안보다 이 일자리를 수락하는 결정적인 요인이었어요." },
      { situation: "재무 복리후생 교육을 진행할 때", en: "Financial wellness workshops help employees understand how to maximize their retirement plan contributions.", ko: "재무 건강 워크숍은 직원들이 퇴직 연금 기여금을 극대화하는 방법을 이해하도록 도와요." },
      { situation: "연금 정책을 업데이트할 때", en: "The HR team revised the retirement plan to allow employee contributions of up to 15 percent of their annual salary.", ko: "HR팀은 직원들이 연봉의 최대 15%까지 기여할 수 있도록 퇴직 연금을 수정했어요." },
      { situation: "이사회에 복리후생 비용을 보고할 때", en: "The total cost of employer contributions to the retirement plan represents approximately 3 percent of total payroll.", ko: "퇴직 연금에 대한 고용주 기여금의 총 비용은 총 급여의 약 3%를 차지해요." },
      { situation: "직원 유지율을 분석할 때", en: "Improving the retirement plan vesting schedule helped reduce early employee departures by 12 percent.", ko: "퇴직 연금 권리 귀속 일정을 개선하면서 초기 직원 퇴사가 12% 줄었어요." },
      { situation: "글로벌 인력을 관리할 때", en: "Each country has different regulations governing retirement plans, requiring a localized approach for international offices.", ko: "각 국가는 퇴직 연금을 규율하는 다른 규정이 있어 국제 사무소에 현지화된 접근 방식이 필요해요." },
      { situation: "재무 계획 교육을 할 때", en: "Starting contributions to a retirement plan early in a career dramatically increases long-term wealth accumulation.", ko: "경력 초기에 퇴직 연금에 기여를 시작하면 장기적인 자산 축적이 극적으로 증가해요." },
      { situation: "규제 준수를 확보할 때", en: "Annual retirement plan audits ensure the company meets all fiduciary responsibilities under pension legislation.", ko: "연간 퇴직 연금 감사는 회사가 연금 법규에 따른 모든 수탁 책임을 충족하는지 확인해요." },
      { situation: "인재 경쟁력을 강화할 때", en: "Offering a defined benefit retirement plan remains a significant competitive advantage in attracting experienced professionals.", ko: "확정 급여형 퇴직 연금을 제공하는 것은 경험 있는 전문가 유치에 있어 여전히 상당한 경쟁 우위로 남아요." }
    ],
    level: "800"
  },
  {
    id: 209,
    word: "health insurance",
    pronunciation: "helθ ɪnˈʃʊər.əns",
    pos: "n.",
    meaning: "건강 보험",
    synonyms: ["medical insurance", "healthcare coverage", "medical benefits"],
    examples: [
      { situation: "직원 복리후생 패키지를 제안할 때", en: "The company covers 80 percent of the monthly health insurance premium for all full-time employees.", ko: "회사는 모든 정규직 직원의 월 건강 보험료의 80%를 부담해요." },
      { situation: "채용 협상을 진행할 때", en: "The candidate negotiated to include family health insurance coverage as part of the employment offer.", ko: "지원자는 가족 건강 보험 보장을 고용 제안의 일부로 포함하도록 협상했어요." },
      { situation: "HR 복리후생 정책을 검토할 때", en: "Our health insurance plan was upgraded this year to include mental health counseling and preventive care benefits.", ko: "올해 건강 보험 계획이 정신 건강 상담과 예방적 돌봄 혜택을 포함하도록 업그레이드됐어요." },
      { situation: "비용 관리를 논의할 때", en: "Rising health insurance costs have prompted many companies to explore self-insured health plan options.", ko: "건강 보험 비용 상승이 많은 기업들이 자가 보험 건강 계획 옵션을 탐색하도록 촉구했어요." },
      { situation: "소기업 경쟁력을 높이려 할 때", en: "Offering comprehensive health insurance helps small businesses compete with larger employers for talent.", ko: "포괄적인 건강 보험을 제공하면 소기업들이 인재를 위해 대기업들과 경쟁하는 데 도움이 돼요." },
      { situation: "국제 직원을 관리할 때", en: "Expatriate employees are covered by an international health insurance policy that provides global coverage.", ko: "주재원들은 글로벌 보장을 제공하는 국제 건강 보험 정책으로 보장돼요." },
      { situation: "직원 정보 공지를 할 때", en: "The HR department sent a detailed guide explaining the changes to the health insurance plan for the new year.", ko: "HR 부서는 새해 건강 보험 계획 변경 사항을 설명하는 상세한 안내서를 발송했어요." },
      { situation: "비용 분석을 할 때", en: "Health insurance represents approximately 8 percent of total compensation cost per employee.", ko: "건강 보험은 직원 1인당 총 보상 비용의 약 8%를 차지해요." },
      { situation: "신규 직원 온보딩 중에", en: "During onboarding, new employees select their health insurance options with support from the HR benefits team.", ko: "온보딩 중에 신규 직원들은 HR 복리후생팀의 지원을 받아 건강 보험 옵션을 선택해요." },
      { situation: "직원 만족도를 높이려 할 때", en: "Improving health insurance coverage was identified as the top driver of employee satisfaction in the annual survey.", ko: "건강 보험 보장 개선이 연간 설문에서 직원 만족도의 최고 동인으로 파악됐어요." }
    ],
    level: "800"
  },
  {
    id: 210,
    word: "wire transfer",
    pronunciation: "ˈwaɪər ˌtræns.fər",
    pos: "n.",
    meaning: "전신 송금, 계좌 이체",
    synonyms: ["bank transfer", "electronic funds transfer", "SWIFT transfer"],
    examples: [
      { situation: "해외 공급업체에 결제할 때", en: "Payment was made via wire transfer to the overseas supplier within the agreed 30-day payment terms.", ko: "합의된 30일 결제 조건 내에 전신 송금으로 해외 공급업체에 결제가 이루어졌어요." },
      { situation: "인수 거래를 마무리할 때", en: "The acquisition closing required a same-day wire transfer of 50 million dollars to the seller escrow account.", ko: "인수 마감에는 판매자 에스크로 계좌로의 5천만 달러 당일 전신 송금이 필요했어요." },
      { situation: "급여를 처리할 때", en: "All international employee salaries are disbursed through wire transfer to minimize currency conversion costs.", ko: "통화 전환 비용을 최소화하기 위해 모든 국제 직원 급여가 전신 송금을 통해 지급돼요." },
      { situation: "자금 세탁 방지 절차를 따를 때", en: "Large wire transfers above 10,000 dollars require additional documentation to comply with anti-money laundering regulations.", ko: "1만 달러를 초과하는 대규모 전신 송금은 자금 세탁 방지 규정을 준수하기 위한 추가 서류가 필요해요." },
      { situation: "재무 담당자가 결제를 승인할 때", en: "All wire transfers above 25,000 dollars require dual authorization from the finance director and CFO.", ko: "2만 5천 달러를 초과하는 모든 전신 송금은 재무 이사와 CFO의 이중 승인이 필요해요." },
      { situation: "사기 방지 절차를 설명할 때", en: "The company fell victim to a CEO fraud scheme where attackers impersonated executives to authorize wire transfers.", ko: "회사는 공격자들이 전신 송금을 승인하기 위해 임원들을 사칭한 CEO 사기 계획의 피해자가 됐어요." },
      { situation: "실시간 결제 시스템을 비교할 때", en: "Wire transfers remain the preferred method for large B2B payments due to their reliability and audit trail.", ko: "전신 송금은 신뢰성과 감사 추적 때문에 대규모 B2B 결제의 선호 방법으로 남아 있어요." },
      { situation: "은행 수수료를 분석할 때", en: "International wire transfer fees can add up significantly for companies making frequent cross-border payments.", ko: "국제 전신 송금 수수료는 빈번한 국경 간 결제를 하는 회사들에게 상당히 쌓일 수 있어요." },
      { situation: "긴급 결제를 처리할 때", en: "An emergency wire transfer was arranged to cover the supplier invoice that was overdue by two weeks.", ko: "2주 연체된 공급업체 청구서를 처리하기 위해 긴급 전신 송금이 준비됐어요." },
      { situation: "투자 자금을 이동할 때", en: "The investor instructed the custodian to initiate a wire transfer to fund the new investment portfolio.", ko: "투자자는 새로운 투자 포트폴리오에 자금을 조달하기 위해 수탁자에게 전신 송금을 시작하도록 지시했어요." }
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
console.log('Batch 10 done: IDs 195,196,199,200,203,204,206,207,209,210 replaced.');
