// Batch 5: IDs 62,63,64,65,69,71,74,75,79,81
// commencement->rollout, commensurate->performance bonus, commingling->payment terms
// compelling->sales funnel, compulsory->business continuity, conciliation->quality assurance
// consent decree->purchase order, constructive dismissal->remote work policy, contravene->scalable
// conveyance->letter of intent
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 62,
    word: "rollout",
    pronunciation: "ˈrəʊl.aʊt",
    pos: "n.",
    meaning: "출시, 단계적 배포",
    synonyms: ["launch", "deployment", "release"],
    examples: [
      { situation: "신제품 출시 계획을 발표할 때", en: "The product rollout is scheduled for Q3 and will begin with our top 10 markets.", ko: "제품 출시는 3분기로 예정되어 있으며 우리의 상위 10개 시장부터 시작될 거예요." },
      { situation: "IT 시스템 업데이트를 계획할 때", en: "The software rollout will be phased over six weeks to minimize disruption to daily operations.", ko: "소프트웨어 배포는 일상적인 운영에 대한 방해를 최소화하기 위해 6주에 걸쳐 단계적으로 진행될 거예요." },
      { situation: "신규 정책을 직원에게 전달할 때", en: "The HR team is managing the rollout of the new flexible working policy across all global offices.", ko: "HR팀은 모든 글로벌 사무소에 걸쳐 새로운 유연 근무 정책의 출시를 관리하고 있어요." },
      { situation: "마케팅 캠페인을 시작할 때", en: "The marketing campaign rollout is coordinated with the product launch to maximize media impact.", ko: "마케팅 캠페인 출시는 미디어 영향을 극대화하기 위해 제품 출시와 조율돼요." },
      { situation: "글로벌 확장 계획을 논의할 때", en: "The international rollout strategy prioritizes markets where we already have distribution partnerships.", ko: "국제 출시 전략은 이미 유통 파트너십이 있는 시장을 우선시해요." },
      { situation: "교육 프로그램을 시작할 때", en: "The compliance training rollout begins next Monday and must be completed by all staff within 30 days.", ko: "컴플라이언스 교육 출시는 다음 월요일에 시작되며 30일 이내에 모든 직원이 완료해야 해요." },
      { situation: "파일럿 프로그램 결과를 검토할 때", en: "Following a successful pilot, we are ready for the nationwide rollout of the new loyalty program.", ko: "성공적인 파일럿에 이어 새로운 로열티 프로그램의 전국적 출시 준비가 됐어요." },
      { situation: "기술 업그레이드를 진행할 때", en: "The IT department developed a detailed rollout plan to upgrade all workstations to the new operating system.", ko: "IT 부서는 모든 워크스테이션을 새 운영 체제로 업그레이드하기 위한 상세한 배포 계획을 개발했어요." },
      { situation: "이해관계자에게 진행 현황을 보고할 때", en: "Weekly rollout status reports are sent to all project stakeholders to keep everyone aligned on progress.", ko: "진행 상황에 대해 모든 사람이 정렬될 수 있도록 주간 출시 현황 보고서가 모든 프로젝트 이해관계자에게 전송돼요." },
      { situation: "고객 피드백을 수집할 때", en: "We gather customer feedback at each phase of the rollout to make real-time improvements.", ko: "실시간 개선을 위해 출시의 각 단계에서 고객 피드백을 수집해요." }
    ],
    level: "800"
  },
  {
    id: 63,
    word: "performance bonus",
    pronunciation: "pəˈfɔː.məns ˈbəʊ.nəs",
    pos: "n.",
    meaning: "성과 보너스",
    synonyms: ["incentive bonus", "merit pay", "results-based bonus"],
    examples: [
      { situation: "보상 체계를 설명할 때", en: "All employees are eligible for a performance bonus of up to 20 percent of their annual salary based on KPI achievement.", ko: "모든 직원은 KPI 달성에 따라 연봉의 최대 20%에 해당하는 성과 보너스를 받을 수 있어요." },
      { situation: "연간 성과 평가 후", en: "The performance bonus for this year reflects the exceptional results delivered during the product launch.", ko: "올해 성과 보너스는 제품 출시 중에 달성한 탁월한 결과를 반영해요." },
      { situation: "영업팀 인센티브를 설계할 때", en: "Sales representatives receive a quarterly performance bonus tied to their revenue targets and customer satisfaction scores.", ko: "영업 담당자들은 매출 목표와 고객 만족도 점수에 연동된 분기별 성과 보너스를 받아요." },
      { situation: "인재 유치 협상에서", en: "The candidate accepted the offer partly due to the attractive performance bonus structure in the compensation package.", ko: "지원자는 보상 패키지의 매력적인 성과 보너스 구조 때문에 제안을 부분적으로 수락했어요." },
      { situation: "팀 성과 목표를 설정할 때", en: "Team members share a collective performance bonus when the group exceeds its annual revenue target.", ko: "팀이 연간 매출 목표를 초과하면 팀원들이 집단적 성과 보너스를 공유해요." },
      { situation: "HR 정책 변경을 공지할 때", en: "Starting next year, performance bonuses will be calculated using a revised scoring framework aligned with company strategy.", ko: "내년부터 성과 보너스는 회사 전략에 맞춰 수정된 채점 프레임워크를 사용해 계산될 거예요." },
      { situation: "예산 계획에서 비용을 예측할 때", en: "The finance team accrues for performance bonuses monthly based on year-to-date KPI performance.", ko: "재무팀은 연초 누적 KPI 성과를 기준으로 매월 성과 보너스를 발생시켜요." },
      { situation: "이사회에 보상 전략을 보고할 때", en: "The compensation committee approved a 15 percent increase in the performance bonus pool for the current year.", ko: "보상 위원회는 올해 성과 보너스 풀을 15% 늘리는 것을 승인했어요." },
      { situation: "저성과자 관리 계획을 논의할 때", en: "Employees on a performance improvement plan are not eligible for a performance bonus during the review period.", ko: "성과 개선 계획에 있는 직원들은 검토 기간 동안 성과 보너스를 받을 수 없어요." },
      { situation: "연말 정산 시즌에", en: "Performance bonuses are paid in February following the completion of the annual appraisal process.", ko: "성과 보너스는 연간 평가 프로세스 완료 후 2월에 지급돼요." }
    ],
    level: "800"
  },
  {
    id: 64,
    word: "payment terms",
    pronunciation: "ˈpeɪ.mənt tɜːmz",
    pos: "n.",
    meaning: "결제 조건",
    synonyms: ["billing terms", "invoice terms", "settlement terms"],
    examples: [
      { situation: "신규 공급업체와 계약을 협상할 때", en: "We negotiated payment terms of net 60 days, which improved our cash flow significantly.", ko: "60일 결제 조건을 협상했고, 이것이 현금 흐름을 크게 개선했어요." },
      { situation: "고객에게 청구서를 발행할 때", en: "All invoices clearly state the payment terms, including the due date and accepted payment methods.", ko: "모든 청구서에는 만기일과 허용된 결제 방법을 포함한 결제 조건이 명확하게 명시돼요." },
      { situation: "계약서를 검토할 때", en: "The contract specifies payment terms of net 30 with a 2 percent early payment discount.", ko: "계약서는 2% 조기 결제 할인이 있는 30일 결제 조건을 명시해요." },
      { situation: "연체 고객을 관리할 때", en: "Customers who consistently fail to meet payment terms may be placed on a prepayment requirement.", ko: "결제 조건을 지속적으로 충족하지 못하는 고객들은 선결제 요건에 배치될 수 있어요." },
      { situation: "신용 정책을 수립할 때", en: "The credit committee reviews and approves payment terms for all accounts above a certain transaction value.", ko: "신용 위원회는 특정 거래 금액 이상의 모든 계정에 대한 결제 조건을 검토하고 승인해요." },
      { situation: "중소기업과 비즈니스를 할 때", en: "We offer more flexible payment terms to small business clients to support their cash flow management.", ko: "중소기업 고객들의 현금 흐름 관리를 지원하기 위해 더 유연한 결제 조건을 제공해요." },
      { situation: "공급업체 관계를 강화할 때", en: "Shortening payment terms for strategic suppliers helped us build stronger partnerships.", ko: "전략적 공급업체에 대한 결제 조건을 단축하면서 더 강한 파트너십을 구축하는 데 도움이 됐어요." },
      { situation: "수출 계약을 체결할 때", en: "International contracts often use letters of credit to secure payment terms across different legal jurisdictions.", ko: "국제 계약은 종종 다른 법적 관할권에 걸쳐 결제 조건을 보장하기 위해 신용장을 사용해요." },
      { situation: "재무 시스템을 업그레이드할 때", en: "The new ERP system automatically applies the correct payment terms to each vendor invoice.", ko: "새 ERP 시스템은 각 공급업체 청구서에 올바른 결제 조건을 자동으로 적용해요." },
      { situation: "공급업체와 분쟁을 해결할 때", en: "The dispute arose because the supplier claimed the agreed payment terms had not been honored.", ko: "공급업체가 합의된 결제 조건이 지켜지지 않았다고 주장하면서 분쟁이 발생했어요." }
    ],
    level: "800"
  },
  {
    id: 65,
    word: "sales funnel",
    pronunciation: "seɪlz ˈfʌn.əl",
    pos: "n.",
    meaning: "영업 깔때기, 세일즈 퍼널",
    synonyms: ["sales pipeline", "conversion funnel", "revenue funnel"],
    examples: [
      { situation: "영업 전략 회의에서", en: "Understanding each stage of the sales funnel helps the team identify where prospects are dropping off.", ko: "영업 퍼널의 각 단계를 이해하면 팀이 잠재 고객이 이탈하는 지점을 파악하는 데 도움이 돼요." },
      { situation: "CRM 보고서를 분석할 때", en: "The CRM dashboard shows how many opportunities are at each stage of our sales funnel.", ko: "CRM 대시보드는 영업 퍼널의 각 단계에 얼마나 많은 기회가 있는지 보여줘요." },
      { situation: "마케팅 캠페인을 기획할 때", en: "Top-of-funnel content marketing attracts new prospects into our sales funnel at a low cost per lead.", ko: "퍼널 상단 콘텐츠 마케팅은 낮은 리드당 비용으로 영업 퍼널에 새로운 잠재 고객을 유치해요." },
      { situation: "영업 성과를 개선할 때", en: "Improving the middle stages of the sales funnel increased our overall conversion rate by 25 percent.", ko: "영업 퍼널의 중간 단계를 개선하면서 전체 전환율이 25% 증가했어요." },
      { situation: "B2B 영업 관리를 할 때", en: "Enterprise sales funnels are typically longer due to multiple stakeholders and procurement processes.", ko: "기업 영업 퍼널은 여러 이해관계자와 조달 프로세스로 인해 일반적으로 더 길어요." },
      { situation: "영업팀 코칭을 진행할 때", en: "Sales managers review the sales funnel weekly to identify stalled deals and coach reps on how to advance them.", ko: "영업 관리자들은 주간 영업 퍼널을 검토해 정체된 거래를 파악하고 담당자에게 진전 방법을 코칭해요." },
      { situation: "마케팅 ROI를 분석할 때", en: "Tracking leads through every stage of the sales funnel allows us to calculate the true ROI of each campaign.", ko: "영업 퍼널의 모든 단계에서 리드를 추적하면 각 캠페인의 실제 ROI를 계산할 수 있어요." },
      { situation: "자동화 도구를 도입할 때", en: "Marketing automation tools nurture leads through the sales funnel with personalized content at each stage.", ko: "마케팅 자동화 도구는 각 단계에서 개인화된 콘텐츠로 영업 퍼널을 통해 리드를 육성해요." },
      { situation: "영업 예측을 수립할 때", en: "The sales funnel data is used to build revenue forecasts for the next two quarters.", ko: "영업 퍼널 데이터는 다음 두 분기의 매출 예측을 구축하는 데 사용돼요." },
      { situation: "신입 영업 직원을 교육할 때", en: "New sales representatives are trained on the company sales funnel methodology during their first two weeks.", ko: "신입 영업 담당자들은 처음 두 주 동안 회사의 영업 퍼널 방법론에 대해 교육받아요." }
    ],
    level: "800"
  },
  {
    id: 69,
    word: "business continuity",
    pronunciation: "ˈbɪz.nɪs ˌkɒn.tɪˈnjuː.ɪ.ti",
    pos: "n.",
    meaning: "사업 연속성",
    synonyms: ["operational continuity", "business resilience", "continuity planning"],
    examples: [
      { situation: "재해 복구 계획을 수립할 때", en: "Our business continuity plan ensures that critical operations can resume within four hours of a major disruption.", ko: "사업 연속성 계획은 주요 혼란 발생 후 4시간 내에 중요한 운영이 재개될 수 있도록 해요." },
      { situation: "팬데믹 대응 전략을 논의할 때", en: "The pandemic tested every aspect of our business continuity framework and exposed several gaps.", ko: "팬데믹은 사업 연속성 프레임워크의 모든 측면을 테스트해 여러 취약점을 드러냈어요." },
      { situation: "IT 복구 절차를 검토할 때", en: "Annual business continuity drills ensure that the recovery team can execute the plan effectively under pressure.", ko: "연간 사업 연속성 훈련은 복구팀이 압박 상황에서 효과적으로 계획을 실행할 수 있도록 해요." },
      { situation: "공급망 리스크를 관리할 때", en: "Business continuity planning for supply chains requires identifying alternative suppliers for all critical components.", ko: "공급망에 대한 사업 연속성 계획은 모든 중요한 부품에 대한 대안 공급업체를 파악하는 것을 필요로 해요." },
      { situation: "이사회 위험 검토 세션에서", en: "The board reviewed the updated business continuity plan and requested annual testing of all critical recovery procedures.", ko: "이사회는 업데이트된 사업 연속성 계획을 검토하고 모든 중요한 복구 절차의 연간 테스트를 요청했어요." },
      { situation: "보험 정책을 갱신할 때", en: "Business continuity insurance covers lost revenue and additional expenses incurred during an operational disruption.", ko: "사업 연속성 보험은 운영 혼란 기간에 발생하는 손실된 매출과 추가 비용을 보장해요." },
      { situation: "원격 근무 인프라를 구축할 때", en: "Moving to cloud-based systems significantly enhanced our business continuity capabilities during unplanned outages.", ko: "클라우드 기반 시스템으로 전환하면서 예상치 못한 중단 시 사업 연속성 역량이 크게 향상됐어요." },
      { situation: "규제 요건을 충족할 때", en: "Financial institutions are required to maintain and test a documented business continuity plan annually.", ko: "금융 기관은 문서화된 사업 연속성 계획을 유지하고 매년 테스트해야 해요." },
      { situation: "사이버 공격에 대비할 때", en: "Cybersecurity incidents are now treated as a business continuity risk and included in the recovery planning framework.", ko: "사이버 보안 사고는 이제 사업 연속성 위험으로 취급되어 복구 계획 프레임워크에 포함돼요." },
      { situation: "M&A 실사 과정에서", en: "Reviewing the target company business continuity plan was a key component of the due diligence process.", ko: "피인수 기업의 사업 연속성 계획 검토가 실사 프로세스의 핵심 구성 요소였어요." }
    ],
    level: "800"
  },
  {
    id: 71,
    word: "quality assurance",
    pronunciation: "ˈkwɒl.ɪ.ti əˈʃʊər.əns",
    pos: "n.",
    meaning: "품질 보증",
    synonyms: ["QA", "quality control", "quality management"],
    examples: [
      { situation: "제품 출시 전 점검을 할 때", en: "Our quality assurance team conducts rigorous testing before any product is approved for release.", ko: "품질 보증팀은 어떤 제품이 출시 승인을 받기 전에 엄격한 테스트를 수행해요." },
      { situation: "고객 불만을 해결할 때", en: "The surge in customer complaints triggered an urgent review of our quality assurance processes.", ko: "고객 불만 급증으로 품질 보증 프로세스에 대한 긴급 검토가 촉발됐어요." },
      { situation: "소프트웨어 개발 팀에서", en: "Quality assurance engineers run automated test scripts after each code deployment to catch regressions.", ko: "품질 보증 엔지니어들은 회귀 오류를 발견하기 위해 각 코드 배포 후 자동화된 테스트 스크립트를 실행해요." },
      { situation: "ISO 인증을 취득할 때", en: "Achieving ISO 9001 certification requires demonstrating a mature quality assurance management system.", ko: "ISO 9001 인증 취득은 성숙한 품질 보증 관리 시스템을 갖추고 있음을 입증해야 해요." },
      { situation: "제조 공정을 관리할 때", en: "Quality assurance checkpoints at each production stage reduced defect rates by 35 percent.", ko: "각 생산 단계의 품질 보증 점검 지점이 불량률을 35% 줄였어요." },
      { situation: "콜센터 성과를 관리할 때", en: "Call recordings are reviewed by the quality assurance team to ensure agents follow the correct scripts and procedures.", ko: "품질 보증팀이 통화 녹음을 검토해 상담원들이 올바른 스크립트와 절차를 따르는지 확인해요." },
      { situation: "서비스 업체를 감사할 때", en: "Third-party quality assurance audits are conducted annually to validate supplier compliance with our standards.", ko: "공급업체가 우리의 기준을 준수하는지 검증하기 위해 연간 제3자 품질 보증 감사를 실시해요." },
      { situation: "신규 직원을 교육할 때", en: "Quality assurance principles are embedded in the training curriculum for all new production staff.", ko: "품질 보증 원칙은 모든 신규 생산 직원을 위한 교육 커리큘럼에 내재화돼요." },
      { situation: "고객 신뢰를 구축할 때", en: "Our robust quality assurance program is a key differentiator in a market where product reliability is paramount.", ko: "견고한 품질 보증 프로그램은 제품 신뢰성이 가장 중요한 시장에서 핵심 차별화 요소예요." },
      { situation: "계약 조건을 협상할 때", en: "The client contract includes quarterly quality assurance reviews to verify that service standards are being met.", ko: "고객 계약에는 서비스 기준이 충족되고 있는지 확인하기 위한 분기별 품질 보증 검토가 포함돼요." }
    ],
    level: "800"
  },
  {
    id: 74,
    word: "purchase order",
    pronunciation: "ˈpɜː.tʃəs ˈɔː.dər",
    pos: "n.",
    meaning: "구매 주문서",
    synonyms: ["PO", "procurement order", "buying order"],
    examples: [
      { situation: "공급업체에 물품을 주문할 때", en: "A purchase order must be issued and approved before any goods or services can be procured from a supplier.", ko: "공급업체로부터 물품이나 서비스를 조달하기 전에 구매 주문서가 발행되고 승인되어야 해요." },
      { situation: "내부 통제 절차를 설명할 때", en: "Our internal controls require a three-way match between the purchase order, delivery receipt, and supplier invoice.", ko: "내부 통제는 구매 주문서, 납품 영수증, 공급업체 청구서 간의 3방향 대조를 요구해요." },
      { situation: "예산 집행을 모니터링할 때", en: "All open purchase orders are tracked in the ERP system to monitor budget commitments in real time.", ko: "예산 약정을 실시간으로 모니터링하기 위해 모든 미결 구매 주문서가 ERP 시스템에서 추적돼요." },
      { situation: "소규모 구매를 처리할 때", en: "Purchases below five hundred dollars can be processed without a formal purchase order under the petty cash policy.", ko: "500달러 미만의 구매는 소액 현금 정책에 따라 공식 구매 주문서 없이 처리될 수 있어요." },
      { situation: "공급업체와 납품 일정을 조율할 때", en: "The purchase order confirms the agreed quantity, unit price, and expected delivery date.", ko: "구매 주문서는 합의된 수량, 단가, 예상 납품 일을 확인해요." },
      { situation: "전자 조달 시스템을 도입할 때", en: "Migrating to an e-procurement system reduced purchase order processing time from three days to four hours.", ko: "전자 조달 시스템으로 전환하면서 구매 주문서 처리 시간이 3일에서 4시간으로 줄었어요." },
      { situation: "공급업체 청구서를 처리할 때", en: "The accounts payable team cannot process an invoice unless a matching purchase order exists in the system.", ko: "매입채무팀은 시스템에 일치하는 구매 주문서가 없으면 청구서를 처리할 수 없어요." },
      { situation: "감사 준비를 할 때", en: "Auditors require documentation showing that every purchase order was properly authorized before commitment.", ko: "감사인들은 모든 구매 주문서가 약정 전에 적절하게 승인됐음을 보여주는 문서를 요구해요." },
      { situation: "계약 분쟁을 해결할 때", en: "The signed purchase order serves as a binding commitment and can be used as evidence in case of dispute.", ko: "서명된 구매 주문서는 구속력 있는 약정으로 기능하며 분쟁 시 증거로 사용될 수 있어요." },
      { situation: "재고 관리를 개선할 때", en: "Automating purchase order generation based on inventory levels prevents stockouts and overstocking.", ko: "재고 수준에 따라 구매 주문서 생성을 자동화하면 품절과 과잉 재고를 방지해요." }
    ],
    level: "800"
  },
  {
    id: 75,
    word: "remote work policy",
    pronunciation: "rɪˈməʊt wɜːk ˈpɒl.ɪ.si",
    pos: "n.",
    meaning: "원격 근무 정책",
    synonyms: ["work-from-home policy", "telecommuting policy", "flexible work policy"],
    examples: [
      { situation: "팬데믹 이후 업무 방식을 재정립할 때", en: "The company updated its remote work policy to allow employees to work from home up to three days per week.", ko: "회사는 직원들이 주당 최대 3일 재택 근무를 할 수 있도록 원격 근무 정책을 업데이트했어요." },
      { situation: "새로운 직원에게 규정을 안내할 때", en: "All new hires receive a copy of the remote work policy during their onboarding session.", ko: "모든 신입 직원은 온보딩 세션 중에 원격 근무 정책 사본을 받아요." },
      { situation: "팀 생산성을 관리할 때", en: "The remote work policy requires employees to be available during core hours from 9 AM to 3 PM regardless of location.", ko: "원격 근무 정책은 위치에 관계없이 직원들이 오전 9시에서 오후 3시의 핵심 시간대에 업무를 수행하도록 요구해요." },
      { situation: "HR 정책을 검토할 때", en: "The HR team conducted a survey before updating the remote work policy to understand employee preferences.", ko: "HR팀은 직원 선호도를 파악하기 위해 원격 근무 정책을 업데이트하기 전에 설문을 실시했어요." },
      { situation: "보안 리스크를 관리할 때", en: "The remote work policy includes mandatory use of a VPN and encrypted devices to protect company data.", ko: "원격 근무 정책에는 회사 데이터를 보호하기 위한 VPN 및 암호화된 기기의 의무 사용이 포함돼요." },
      { situation: "인재 유치 전략을 논의할 때", en: "A flexible remote work policy has become a key differentiator in attracting top talent in competitive markets.", ko: "유연한 원격 근무 정책이 경쟁 시장에서 최고 인재를 유치하는 핵심 차별화 요소가 됐어요." },
      { situation: "관리자들에게 지침을 제공할 때", en: "Managers received training on how to fairly apply the remote work policy across their teams.", ko: "관리자들은 팀 전반에 걸쳐 원격 근무 정책을 공정하게 적용하는 방법에 대한 교육을 받았어요." },
      { situation: "비용 절감 방안을 논의할 때", en: "Introducing a permanent remote work policy enabled the company to reduce its office footprint by 30 percent.", ko: "영구적인 원격 근무 정책을 도입하면서 회사가 사무실 공간을 30% 줄일 수 있었어요." },
      { situation: "팀 협업 방식을 개선할 때", en: "The remote work policy was updated to require monthly in-person team meetings to maintain collaboration.", ko: "협업을 유지하기 위해 원격 근무 정책이 월간 대면 팀 회의를 의무화하도록 업데이트됐어요." },
      { situation: "국제 팀을 관리할 때", en: "The global remote work policy must account for different time zones, tax regulations, and employment laws.", ko: "글로벌 원격 근무 정책은 서로 다른 시간대, 세금 규정, 고용법을 고려해야 해요." }
    ],
    level: "800"
  },
  {
    id: 79,
    word: "scalable",
    pronunciation: "ˈskeɪ.lə.bəl",
    pos: "adj.",
    meaning: "확장 가능한",
    synonyms: ["expandable", "flexible", "growth-ready"],
    examples: [
      { situation: "스타트업 기술 인프라를 검토할 때", en: "Investors want to see a scalable business model before committing to a Series B round.", ko: "투자자들은 시리즈 B 라운드에 참여하기 전에 확장 가능한 비즈니스 모델을 보고 싶어해요." },
      { situation: "클라우드 솔루션을 선택할 때", en: "We chose a cloud-based platform because it is scalable and can handle rapid growth without hardware upgrades.", ko: "하드웨어 업그레이드 없이 빠른 성장을 처리할 수 있는 확장 가능한 클라우드 기반 플랫폼을 선택했어요." },
      { situation: "프로세스 설계를 논의할 때", en: "Building scalable processes from day one prevents costly redesigns as the company grows.", ko: "처음부터 확장 가능한 프로세스를 구축하면 회사 성장에 따른 비용이 많이 드는 재설계를 방지해요." },
      { situation: "사업 성장 계획을 발표할 때", en: "Our scalable distribution network can accommodate a threefold increase in order volume without significant additional investment.", ko: "확장 가능한 유통 네트워크는 추가적인 상당한 투자 없이도 주문량의 3배 증가를 수용할 수 있어요." },
      { situation: "IT 아키텍처를 설계할 때", en: "The new microservices architecture is more scalable than the monolithic system it replaced.", ko: "새로운 마이크로서비스 아키텍처는 대체된 모놀리식 시스템보다 더 확장 가능해요." },
      { situation: "제품 전략을 수립할 때", en: "A scalable product design means we can enter new markets without rebuilding the core platform.", ko: "확장 가능한 제품 설계는 핵심 플랫폼을 재구축하지 않고도 새로운 시장에 진입할 수 있음을 의미해요." },
      { situation: "M&A 인수 심사를 할 때", en: "Due diligence revealed that the target company infrastructure was not scalable enough to support our growth plans.", ko: "실사 결과 피인수 기업의 인프라가 우리의 성장 계획을 지원하기에 충분히 확장 가능하지 않은 것으로 나타났어요." },
      { situation: "영업팀 성장 전략에서", en: "We need a scalable sales process that allows us to onboard 100 new clients per month without increasing headcount.", ko: "인원 증가 없이 월 100명의 신규 고객을 온보딩할 수 있는 확장 가능한 영업 프로세스가 필요해요." },
      { situation: "파트너십 제안을 평가할 때", en: "The partner program is designed to be scalable, accommodating everything from small agencies to global consultancies.", ko: "파트너 프로그램은 소규모 대행사에서 글로벌 컨설팅 회사까지 모두 수용하는 확장 가능한 방식으로 설계됐어요." },
      { situation: "콘텐츠 마케팅 접근법을 논의할 때", en: "Creating a scalable content production workflow enabled us to triple output without hiring additional staff.", ko: "확장 가능한 콘텐츠 제작 워크플로우를 구축하면서 추가 직원 채용 없이 산출물을 3배로 늘릴 수 있었어요." }
    ],
    level: "800"
  },
  {
    id: 81,
    word: "letter of intent",
    pronunciation: "ˈlet.ər əv ɪnˈtent",
    pos: "n.",
    meaning: "의향서, LOI",
    synonyms: ["LOI", "memorandum of understanding", "heads of terms"],
    examples: [
      { situation: "M&A 초기 협상 단계에서", en: "Both parties signed a letter of intent outlining the key terms of the proposed acquisition.", ko: "양측은 제안된 인수의 주요 조건을 개요로 한 의향서에 서명했어요." },
      { situation: "임대 계약을 준비할 때", en: "The landlord accepted our letter of intent and agreed to begin drafting the formal lease agreement.", ko: "임대인은 우리의 의향서를 수락하고 공식 임대 계약서 초안 작성을 시작하는 데 동의했어요." },
      { situation: "공급업체와 장기 계약을 논의할 때", en: "We issued a letter of intent to secure pricing commitments from the supplier while formal negotiations continued.", ko: "공식 협상이 계속되는 동안 공급업체로부터 가격 약정을 확보하기 위해 의향서를 발행했어요." },
      { situation: "합작 투자를 설립할 때", en: "The joint venture partners exchanged a letter of intent before commissioning legal teams to draft the partnership agreement.", ko: "합작 투자 파트너들은 법무팀에 파트너십 계약서 초안을 의뢰하기 전에 의향서를 교환했어요." },
      { situation: "채용 제안을 공식화할 때", en: "Some companies issue a letter of intent to a preferred candidate before preparing the formal employment contract.", ko: "일부 회사는 공식 고용 계약서를 준비하기 전에 선호 후보자에게 의향서를 발행해요." },
      { situation: "부동산 거래를 시작할 때", en: "A letter of intent was submitted to the property owner to express our interest in purchasing the commercial building.", ko: "상업용 건물 구매에 대한 관심을 표명하기 위해 부동산 소유자에게 의향서를 제출했어요." },
      { situation: "투자 유치를 논의할 때", en: "The startup received a letter of intent from a venture capital firm indicating interest in leading the Series A round.", ko: "스타트업은 시리즈 A 라운드를 주도하는 데 관심이 있음을 나타내는 벤처 자본 회사의 의향서를 받았어요." },
      { situation: "인수 협상에서 독점 기간을 확보할 때", en: "The letter of intent included a 45-day exclusivity period during which the seller would not negotiate with other buyers.", ko: "의향서에는 판매자가 다른 구매자와 협상하지 않는 45일 독점 기간이 포함됐어요." },
      { situation: "계약 전 법적 구속력을 논의할 때", en: "Legal counsel clarified which sections of the letter of intent were binding and which were merely indicative.", ko: "법률 고문은 의향서의 어느 섹션이 구속력이 있고 어느 섹션이 단순히 지시적인지를 명확히 했어요." },
      { situation: "파트너십 조건을 사전에 합의할 때", en: "Signing a letter of intent allowed both sides to align on deal structure before spending resources on due diligence.", ko: "의향서에 서명함으로써 양측은 실사에 자원을 투입하기 전에 거래 구조를 조율할 수 있었어요." }
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
console.log('Batch 5 done: IDs 62,63,64,65,69,71,74,75,79,81 replaced.');
