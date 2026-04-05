// Batch 3: IDs 30,31,32,37,38,39,40,41,42,46
// asset stripping->outsourcing, attrition->employee turnover, augment->talent acquisition
// bespoke->service level agreement, bifurcate->accounts receivable, bilateral->stakeholder engagement
// blackout period->digital transformation, blue chip->brand equity, bond covenant->master service agreement
// callable bond->severance package
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 30,
    word: "outsourcing",
    pronunciation: "ˈaʊt.sɔː.sɪŋ",
    pos: "n./v.",
    meaning: "아웃소싱, 외부 위탁",
    synonyms: ["subcontracting", "third-party sourcing", "offloading"],
    examples: [
      { situation: "비용 절감 전략을 논의할 때", en: "Outsourcing the customer support function reduced our operating costs by 25 percent.", ko: "고객 지원 기능을 아웃소싱하면서 운영 비용이 25% 절감됐어요." },
      { situation: "핵심 역량에 집중하기 위해", en: "By outsourcing non-core activities, the company was able to focus resources on product innovation.", ko: "비핵심 활동을 아웃소싱함으로써 회사는 제품 혁신에 자원을 집중할 수 있었어요." },
      { situation: "IT 서비스 전략을 검토할 때", en: "Many companies are outsourcing their IT infrastructure management to specialized cloud providers.", ko: "많은 기업들이 전문 클라우드 공급업체에 IT 인프라 관리를 아웃소싱하고 있어요." },
      { situation: "공급업체 선정 회의에서", en: "Before outsourcing payroll processing, we conducted a thorough vendor assessment to ensure data security.", ko: "급여 처리를 아웃소싱하기 전에 데이터 보안을 보장하기 위해 철저한 공급업체 평가를 실시했어요." },
      { situation: "해외 사업 확장을 계획할 때", en: "Outsourcing manufacturing to lower-cost regions helped us remain price-competitive in international markets.", ko: "저비용 지역으로 제조를 아웃소싱하면서 국제 시장에서 가격 경쟁력을 유지할 수 있었어요." },
      { situation: "HR 정책 변경을 논의할 때", en: "The decision to outsource the recruitment process was met with mixed reactions from the internal HR team.", ko: "채용 과정을 아웃소싱하기로 한 결정에 대해 내부 HR팀은 엇갈린 반응을 보였어요." },
      { situation: "리스크 관리 계획을 수립할 때", en: "Outsourcing key functions creates dependency risks that must be managed through robust contract terms.", ko: "핵심 기능을 아웃소싱하면 견고한 계약 조건으로 관리해야 하는 의존성 위험이 생겨요." },
      { situation: "비용 구조 분석을 할 때", en: "The finance team modeled three outsourcing scenarios to identify the option with the best cost-benefit profile.", ko: "재무팀은 최선의 비용-편익 프로필을 가진 옵션을 파악하기 위해 세 가지 아웃소싱 시나리오를 모델링했어요." },
      { situation: "서비스 품질을 유지하면서 위탁할 때", en: "Outsourcing does not mean losing quality control; we maintain strict SLAs with all our service providers.", ko: "아웃소싱이 품질 관리를 잃는 것을 의미하지는 않아요. 우리는 모든 서비스 공급자와 엄격한 SLA를 유지해요." },
      { situation: "경영 컨설팅 보고서에서", en: "The consultant recommended outsourcing logistics to a third-party provider to unlock capital tied up in warehouse assets.", ko: "컨설턴트는 창고 자산에 묶인 자본을 해제하기 위해 물류를 제3자 공급업체에 아웃소싱할 것을 권고했어요." }
    ],
    level: "800"
  },
  {
    id: 31,
    word: "employee turnover",
    pronunciation: "ɪmˈplɔɪ.iː ˈtɜːn.əʊ.vər",
    pos: "n.",
    meaning: "직원 이직률, 인력 교체율",
    synonyms: ["staff turnover", "attrition rate", "workforce churn"],
    examples: [
      { situation: "HR 보고서를 발표할 때", en: "High employee turnover in the sales department prompted management to review the compensation structure.", ko: "영업 부서의 높은 직원 이직률로 인해 경영진이 보상 구조를 검토하게 됐어요." },
      { situation: "비용 분석을 할 때", en: "The cost of employee turnover, including recruitment and training, can exceed 50 percent of an annual salary.", ko: "채용 및 교육을 포함한 직원 이직 비용은 연봉의 50%를 초과할 수 있어요." },
      { situation: "직원 만족도를 논의할 때", en: "Implementing flexible work policies significantly reduced employee turnover by 20 percent within one year.", ko: "유연 근무 정책을 도입하면서 1년 내 직원 이직률이 20% 크게 줄었어요." },
      { situation: "리텐션 전략을 수립할 때", en: "Understanding the root causes of employee turnover is essential before designing any retention program.", ko: "리텐션 프로그램을 설계하기 전에 직원 이직률의 근본 원인을 이해하는 것이 필수적이에요." },
      { situation: "이사회에 인력 현황을 보고할 때", en: "Employee turnover in the technology sector averages around 20 percent annually, well above the industry norm.", ko: "기술 부문의 직원 이직률은 연간 평균 약 20%로 업계 평균을 훨씬 웃돌아요." },
      { situation: "신규 관리자 교육에서", en: "Managers are trained to identify early warning signs of employee disengagement that often lead to turnover.", ko: "관리자들은 종종 이직으로 이어지는 직원 이탈의 초기 경고 신호를 파악하도록 교육받아요." },
      { situation: "퇴직 인터뷰를 분석할 때", en: "Exit interview data revealed that poor management practices were the leading driver of employee turnover.", ko: "퇴직 면접 데이터는 열악한 관리 관행이 직원 이직의 주요 원인임을 밝혔어요." },
      { situation: "채용 계획을 수립할 때", en: "The HR team projects employee turnover for the next quarter to plan recruitment campaigns in advance.", ko: "HR팀은 채용 캠페인을 미리 계획하기 위해 다음 분기 직원 이직률을 예측해요." },
      { situation: "직장 문화 개선 이니셔티브에서", en: "Investing in career development programs is one of the most effective ways to reduce employee turnover.", ko: "경력 개발 프로그램에 투자하는 것은 직원 이직률을 낮추는 가장 효과적인 방법 중 하나예요." },
      { situation: "경쟁사와 비교할 때", en: "Our employee turnover rate is 12 percent, compared to the industry average of 18 percent.", ko: "우리의 직원 이직률은 12%로 업계 평균 18%보다 낮아요." }
    ],
    level: "800"
  },
  {
    id: 32,
    word: "talent acquisition",
    pronunciation: "ˈtæl.ənt ˌæk.wɪˈzɪʃ.ən",
    pos: "n.",
    meaning: "인재 채용, 인재 확보",
    synonyms: ["recruitment", "hiring", "staffing"],
    examples: [
      { situation: "채용팀 전략 회의에서", en: "Talent acquisition has become more competitive as companies compete for a shrinking pool of skilled professionals.", ko: "숙련된 전문가 풀이 줄어들면서 기업들이 경쟁하는 인재 채용이 더욱 치열해졌어요." },
      { situation: "HR 예산을 편성할 때", en: "The talent acquisition budget was increased by 30 percent to support the company rapid expansion plans.", ko: "회사의 빠른 확장 계획을 지원하기 위해 인재 채용 예산이 30% 증가했어요." },
      { situation: "채용 브랜딩 전략을 수립할 때", en: "A strong employer brand is the most cost-effective talent acquisition tool available to large organizations.", ko: "강한 고용주 브랜드는 대형 조직이 활용할 수 있는 가장 비용 효율적인 인재 채용 도구예요." },
      { situation: "스타트업 성장 계획을 논의할 때", en: "Rapid talent acquisition during the growth phase requires a well-structured onboarding process to maintain quality.", ko: "성장 단계에서의 빠른 인재 채용은 품질을 유지하기 위해 잘 구조화된 온보딩 프로세스를 필요로 해요." },
      { situation: "기술 인재 부족 현상을 다룰 때", en: "To address the talent shortage, the company partnered with universities for proactive talent acquisition.", ko: "인재 부족 문제를 해결하기 위해 회사는 선제적 인재 채용을 위해 대학들과 파트너십을 맺었어요." },
      { situation: "채용 자동화 도구를 도입할 때", en: "AI-powered tools are transforming talent acquisition by automating resume screening and initial candidate assessment.", ko: "AI 기반 도구들이 이력서 선별과 초기 후보자 평가를 자동화함으로써 인재 채용을 변화시키고 있어요." },
      { situation: "다양성 채용 목표를 설정할 때", en: "Our talent acquisition strategy includes specific diversity targets for senior leadership roles.", ko: "우리의 인재 채용 전략에는 고위 리더십 직위에 대한 구체적인 다양성 목표가 포함돼요." },
      { situation: "인재 파이프라인을 구축할 때", en: "Building a talent pipeline through internship programs ensures a steady supply for future talent acquisition needs.", ko: "인턴십 프로그램을 통해 인재 파이프라인을 구축하면 미래 인재 채용 필요를 위한 안정적인 공급이 보장돼요." },
      { situation: "글로벌 팀을 구성할 때", en: "International talent acquisition requires understanding local labor laws and cultural expectations in each market.", ko: "국제 인재 채용은 각 시장의 현지 노동법과 문화적 기대를 이해하는 것을 필요로 해요." },
      { situation: "M&A 이후 통합 계획에서", en: "Post-merger talent acquisition plans were developed to fill gaps created by voluntary departures during the transition.", ko: "전환 기간 중 자발적 이탈로 생긴 공백을 메우기 위해 합병 후 인재 채용 계획이 수립됐어요." }
    ],
    level: "800"
  },
  {
    id: 37,
    word: "service level agreement",
    pronunciation: "ˈsɜː.vɪs ˈlev.əl əˈɡriː.mənt",
    pos: "n.",
    meaning: "서비스 수준 협약, SLA",
    synonyms: ["SLA", "service contract", "performance agreement"],
    examples: [
      { situation: "IT 서비스 공급업체와 계약할 때", en: "The service level agreement guarantees 99.9 percent system uptime with a four-hour response time for critical issues.", ko: "서비스 수준 협약은 중요한 문제에 대해 4시간 응답 시간으로 99.9% 시스템 가동 시간을 보장해요." },
      { situation: "아웃소싱 계약을 협상할 때", en: "Before signing the outsourcing contract, we negotiated a comprehensive service level agreement covering all key deliverables.", ko: "아웃소싱 계약서에 서명하기 전에 모든 핵심 산출물을 포함하는 포괄적인 서비스 수준 협약을 협상했어요." },
      { situation: "공급업체 성과를 관리할 때", en: "Vendor performance is reviewed monthly against the metrics defined in the service level agreement.", ko: "공급업체 성과는 서비스 수준 협약에 정의된 지표에 따라 매월 검토돼요." },
      { situation: "고객 지원 팀의 기준을 설정할 때", en: "The customer support team is required to meet a first-response time of two hours as per our service level agreement.", ko: "고객 지원팀은 서비스 수준 협약에 따라 2시간의 첫 응답 시간을 충족해야 해요." },
      { situation: "계약 위반을 처리할 때", en: "Failure to meet the service level agreement terms triggers automatic penalty deductions from the vendor invoice.", ko: "서비스 수준 협약 조건을 충족하지 못하면 공급업체 청구서에서 자동 위약금 공제가 발생해요." },
      { situation: "내부 부서 간 서비스를 규정할 때", en: "Internal service level agreements between IT and finance departments help clarify expected response times for system requests.", ko: "IT와 재무 부서 간의 내부 서비스 수준 협약은 시스템 요청에 대한 예상 응답 시간을 명확히 하는 데 도움이 돼요." },
      { situation: "계약 갱신 협상 중에", en: "During the contract renewal, we renegotiated the service level agreement to include stronger data security provisions.", ko: "계약 갱신 중에 더 강력한 데이터 보안 조항을 포함하도록 서비스 수준 협약을 재협상했어요." },
      { situation: "클라우드 서비스를 도입할 때", en: "Cloud service providers typically offer tiered service level agreements based on the criticality of the workload.", ko: "클라우드 서비스 공급자들은 일반적으로 워크로드의 중요도에 따라 계층화된 서비스 수준 협약을 제공해요." },
      { situation: "프로젝트 킥오프 미팅에서", en: "Establishing a clear service level agreement at project kickoff prevents misunderstandings about deliverable timelines.", ko: "프로젝트 킥오프 시 명확한 서비스 수준 협약을 수립하면 납품 일정에 관한 오해를 방지해요." },
      { situation: "서비스 품질 개선을 논의할 때", en: "Client feedback showed that adherence to the service level agreement was the single most important factor in satisfaction.", ko: "고객 피드백은 서비스 수준 협약 준수가 만족도에서 가장 중요한 단일 요소임을 보여줬어요." }
    ],
    level: "800"
  },
  {
    id: 38,
    word: "accounts receivable",
    pronunciation: "əˈkaʊnts rɪˈsiː.və.bəl",
    pos: "n.",
    meaning: "매출채권, 미수금",
    synonyms: ["trade receivables", "outstanding invoices", "debtor accounts"],
    examples: [
      { situation: "재무 상태를 보고할 때", en: "Our accounts receivable balance grew by 15 percent this quarter, reflecting strong sales activity.", ko: "강한 영업 활동을 반영해 이번 분기 매출채권 잔액이 15% 증가했어요." },
      { situation: "현금 흐름을 개선할 때", en: "Reducing accounts receivable days from 45 to 30 would significantly improve our working capital position.", ko: "매출채권 회수일을 45일에서 30일로 줄이면 운전자본 포지션이 크게 개선될 거예요." },
      { situation: "신용 정책을 검토할 때", en: "The finance director tightened credit terms to prevent accounts receivable from growing beyond a manageable level.", ko: "재무 이사는 매출채권이 관리 가능한 수준을 초과하지 않도록 신용 조건을 강화했어요." },
      { situation: "감사 준비를 할 때", en: "External auditors request an aged accounts receivable report to assess the collectability of outstanding balances.", ko: "외부 감사인들은 미지급 잔액의 회수 가능성을 평가하기 위해 연령별 매출채권 보고서를 요청해요." },
      { situation: "ERP 시스템 기능을 설명할 때", en: "The new ERP system automates accounts receivable reminders, reducing late payments by 30 percent.", ko: "새 ERP 시스템은 매출채권 리마인더를 자동화해 연체 결제를 30% 줄였어요." },
      { situation: "팩토링 서비스를 검토할 때", en: "We used invoice factoring to convert accounts receivable into immediate cash to fund the product launch.", ko: "제품 출시 자금을 마련하기 위해 청구서 팩토링을 이용해 매출채권을 즉시 현금으로 전환했어요." },
      { situation: "신용 위험을 관리할 때", en: "The accounts receivable team monitors overdue accounts closely to minimize bad debt write-offs.", ko: "매출채권팀은 대손 상각을 최소화하기 위해 연체 계정을 면밀히 모니터링해요." },
      { situation: "회계 연수를 진행할 때", en: "Understanding accounts receivable is fundamental to managing the cash conversion cycle effectively.", ko: "매출채권을 이해하는 것은 현금 전환 주기를 효과적으로 관리하는 데 기본적이에요." },
      { situation: "월말 결산을 할 때", en: "Month-end closing procedures include reconciling accounts receivable to the general ledger.", ko: "월말 결산 절차에는 매출채권을 총계정원장과 대조하는 것이 포함돼요." },
      { situation: "대출 담보를 협의할 때", en: "The bank accepted accounts receivable as collateral for the short-term revolving credit facility.", ko: "은행은 단기 회전 신용 한도에 대한 담보로 매출채권을 수락했어요." }
    ],
    level: "800"
  },
  {
    id: 39,
    word: "stakeholder engagement",
    pronunciation: "ˈsteɪk.həʊl.dər ɪnˈɡeɪdʒ.mənt",
    pos: "n.",
    meaning: "이해관계자 참여, 이해관계자 소통",
    synonyms: ["stakeholder communication", "stakeholder management", "stakeholder relations"],
    examples: [
      { situation: "신규 프로젝트를 시작할 때", en: "Effective stakeholder engagement from the outset prevents costly misalignments later in the project.", ko: "초기부터 효과적인 이해관계자 참여는 프로젝트 후반에 발생하는 비용이 많이 드는 불일치를 방지해요." },
      { situation: "회사 정책 변경을 발표할 때", en: "A structured stakeholder engagement plan ensures all affected groups are informed and consulted before major decisions.", ko: "구조화된 이해관계자 참여 계획은 주요 결정 전에 영향받는 모든 그룹이 고지받고 협의되도록 해요." },
      { situation: "CSR 활동을 계획할 때", en: "Community stakeholder engagement is central to our corporate social responsibility strategy.", ko: "지역사회 이해관계자 참여는 우리 기업 사회적 책임 전략의 핵심이에요." },
      { situation: "변화 관리 프로세스에서", en: "The project manager scheduled regular stakeholder engagement sessions to maintain buy-in throughout the rollout.", ko: "프로젝트 관리자는 출시 전반에 걸쳐 지지를 유지하기 위해 정기적인 이해관계자 참여 세션을 예약했어요." },
      { situation: "규제 승인을 받기 위해", en: "Proactive stakeholder engagement with regulators helped us obtain approval three months ahead of schedule.", ko: "규제당국과의 선제적 이해관계자 참여 덕분에 예정보다 3개월 앞서 승인을 받을 수 있었어요." },
      { situation: "대규모 구조조정을 알릴 때", en: "During the restructuring, we prioritized transparent stakeholder engagement to minimize uncertainty and rumors.", ko: "구조조정 중에 불확실성과 소문을 최소화하기 위해 투명한 이해관계자 참여를 우선시했어요." },
      { situation: "ESG 보고서를 작성할 때", en: "Our ESG report details the stakeholder engagement activities conducted over the past 12 months.", ko: "우리의 ESG 보고서는 지난 12개월간 수행된 이해관계자 참여 활동을 자세히 설명해요." },
      { situation: "제품 개발 초기 단계에서", en: "Early customer stakeholder engagement during product development reduces the risk of building features nobody wants.", ko: "제품 개발 중 초기 고객 이해관계자 참여는 아무도 원하지 않는 기능을 만드는 위험을 줄여요." },
      { situation: "인수합병 과정에서", en: "A comprehensive stakeholder engagement strategy is critical during mergers to retain key talent and customers.", ko: "합병 중에 핵심 인재와 고객을 유지하기 위해 포괄적인 이해관계자 참여 전략이 중요해요." },
      { situation: "투자자 관계 활동에서", en: "Quarterly earnings calls are a key stakeholder engagement tool for communicating financial performance to investors.", ko: "분기별 실적 발표는 투자자들에게 재무 성과를 전달하기 위한 핵심 이해관계자 참여 도구예요." }
    ],
    level: "800"
  },
  {
    id: 40,
    word: "digital transformation",
    pronunciation: "ˈdɪdʒ.ɪ.təl ˌtræns.fəˈmeɪ.ʃən",
    pos: "n.",
    meaning: "디지털 전환",
    synonyms: ["digitalization", "technology transformation", "digital modernization"],
    examples: [
      { situation: "경영 전략 발표에서", en: "Our three-year digital transformation roadmap prioritizes cloud migration, automation, and data analytics.", ko: "우리의 3개년 디지털 전환 로드맵은 클라우드 마이그레이션, 자동화, 데이터 분석을 우선시해요." },
      { situation: "이사회에 기술 투자를 설명할 때", en: "The board approved a significant budget for digital transformation to maintain competitiveness in the market.", ko: "이사회는 시장에서 경쟁력을 유지하기 위해 디지털 전환에 상당한 예산을 승인했어요." },
      { situation: "제조업 혁신을 논의할 때", en: "Digital transformation of the factory floor has reduced production errors by 40 percent.", ko: "공장 현장의 디지털 전환으로 생산 오류가 40% 줄었어요." },
      { situation: "고객 경험 개선 프로젝트에서", en: "Digital transformation has enabled us to deliver a seamless omnichannel experience to our customers.", ko: "디지털 전환 덕분에 고객들에게 원활한 옴니채널 경험을 제공할 수 있게 됐어요." },
      { situation: "직원 교육 필요성을 설명할 때", en: "Successful digital transformation requires upskilling the workforce to work effectively with new technologies.", ko: "성공적인 디지털 전환은 직원들이 새로운 기술과 효과적으로 일할 수 있도록 역량을 높이는 것을 필요로 해요." },
      { situation: "업무 프로세스를 자동화할 때", en: "Digital transformation of our back-office processes eliminated manual errors and freed up 200 hours of staff time monthly.", ko: "백오피스 프로세스의 디지털 전환으로 수동 오류가 제거되고 월 200시간의 직원 시간이 확보됐어요." },
      { situation: "경쟁사와 기술 수준을 비교할 때", en: "Companies that delayed digital transformation struggled to adapt when the pandemic accelerated the shift to online commerce.", ko: "디지털 전환을 미룬 기업들은 팬데믹이 온라인 상거래로의 전환을 가속화했을 때 적응하는 데 어려움을 겪었어요." },
      { situation: "공급망 관리를 개선할 때", en: "Digital transformation of supply chain management improved real-time visibility and reduced delivery lead times.", ko: "공급망 관리의 디지털 전환으로 실시간 가시성이 향상되고 납품 리드 타임이 단축됐어요." },
      { situation: "IT 예산 배분을 논의할 때", en: "Over 60 percent of our IT budget is now allocated to digital transformation initiatives rather than legacy system maintenance.", ko: "IT 예산의 60% 이상이 이제 레거시 시스템 유지보수 대신 디지털 전환 이니셔티브에 배분돼요." },
      { situation: "컨설팅 회사와 협력할 때", en: "We partnered with a consulting firm to develop a phased digital transformation strategy aligned with our growth objectives.", ko: "성장 목표에 맞는 단계적 디지털 전환 전략을 개발하기 위해 컨설팅 회사와 파트너십을 맺었어요." }
    ],
    level: "800"
  },
  {
    id: 41,
    word: "brand equity",
    pronunciation: "brænd ˈek.wɪ.ti",
    pos: "n.",
    meaning: "브랜드 자산, 브랜드 가치",
    synonyms: ["brand value", "brand strength", "brand worth"],
    examples: [
      { situation: "마케팅 전략 회의에서", en: "Consistent brand messaging over decades has built substantial brand equity that supports premium pricing.", ko: "수십 년에 걸친 일관된 브랜드 메시지는 프리미엄 가격 책정을 지지하는 상당한 브랜드 자산을 구축했어요." },
      { situation: "M&A 가치 평가를 할 때", en: "The acquisition price reflected a significant premium attributable to the target company strong brand equity.", ko: "인수 가격은 피인수 기업의 강한 브랜드 자산에 기인한 상당한 프리미엄을 반영했어요." },
      { situation: "신제품 출시를 계획할 때", en: "Launching the new product under our existing brand leverages accumulated brand equity to reduce marketing costs.", ko: "기존 브랜드로 신제품을 출시하면 마케팅 비용을 줄이기 위해 축적된 브랜드 자산을 활용해요." },
      { situation: "브랜드 위기를 관리할 때", en: "A single product recall can severely damage brand equity that took years to build.", ko: "단 한 번의 제품 리콜이 수년에 걸쳐 구축한 브랜드 자산을 심각하게 손상시킬 수 있어요." },
      { situation: "소비자 조사 결과를 분석할 때", en: "Consumer surveys are used to measure brand equity dimensions including awareness, loyalty, and perceived quality.", ko: "소비자 설문은 인지도, 충성도, 인식된 품질을 포함한 브랜드 자산 차원을 측정하는 데 사용돼요." },
      { situation: "광고 투자 효과를 설명할 때", en: "Long-term advertising investment builds brand equity by creating strong emotional associations in the consumer mind.", ko: "장기적 광고 투자는 소비자 마음속에 강한 감정적 연상을 만들어 브랜드 자산을 구축해요." },
      { situation: "글로벌 시장 진출을 준비할 때", en: "Our high brand equity in domestic markets gave us a strong foundation for international expansion.", ko: "국내 시장에서의 높은 브랜드 자산은 우리에게 해외 확장을 위한 강한 토대를 제공했어요." },
      { situation: "파트너십 계약을 협상할 때", en: "The licensing partner was willing to pay a premium fee due to the licensor strong brand equity in the target market.", ko: "라이선스 파트너는 목표 시장에서 라이선서의 강한 브랜드 자산 때문에 프리미엄 수수료를 기꺼이 지불했어요." },
      { situation: "디지털 마케팅 성과를 평가할 때", en: "Social media engagement metrics are increasingly used as proxies for measuring brand equity among younger demographics.", ko: "소셜 미디어 참여 지표는 젊은 인구층 사이에서 브랜드 자산을 측정하는 대리 지표로 점점 더 많이 사용돼요." },
      { situation: "연간 마케팅 보고서에서", en: "Despite the competitive market, our brand equity scores improved by 8 points compared to last year.", ko: "경쟁적인 시장임에도 불구하고 우리의 브랜드 자산 점수가 지난해 대비 8점 향상됐어요." }
    ],
    level: "800"
  },
  {
    id: 42,
    word: "master service agreement",
    pronunciation: "ˈmɑː.stər ˈsɜː.vɪs əˈɡriː.mənt",
    pos: "n.",
    meaning: "기본 서비스 계약, MSA",
    synonyms: ["MSA", "framework agreement", "umbrella contract"],
    examples: [
      { situation: "신규 공급업체와 계약을 체결할 때", en: "We establish a master service agreement with each vendor before issuing any individual project statements of work.", ko: "개별 프로젝트 작업 명세서를 발행하기 전에 각 공급업체와 기본 서비스 계약을 체결해요." },
      { situation: "법무팀 계약 검토 절차에서", en: "The master service agreement covers standard terms including liability, confidentiality, and intellectual property ownership.", ko: "기본 서비스 계약은 책임, 기밀 유지, 지적 재산 소유권을 포함한 표준 조건을 다루어요." },
      { situation: "여러 프로젝트를 동시에 진행할 때", en: "Having a master service agreement in place significantly speeds up contracting for new project engagements.", ko: "기본 서비스 계약이 마련되어 있으면 새로운 프로젝트 참여에 대한 계약이 크게 빨라져요." },
      { situation: "컨설팅 회사를 채용할 때", en: "Our consulting partner operates under a master service agreement that has been in place for five years.", ko: "우리 컨설팅 파트너는 5년째 유지되고 있는 기본 서비스 계약 하에 운영돼요." },
      { situation: "리스크 관리 관점에서 계약을 검토할 때", en: "A well-drafted master service agreement reduces legal risk by establishing consistent terms across all engagements.", ko: "잘 작성된 기본 서비스 계약은 모든 계약에 걸쳐 일관된 조건을 확립함으로써 법적 위험을 줄여요." },
      { situation: "계약 갱신을 협상할 때", en: "The master service agreement is reviewed annually and updated to reflect changes in regulatory requirements.", ko: "기본 서비스 계약은 매년 검토되고 규제 요건의 변경 사항을 반영하도록 업데이트돼요." },
      { situation: "IT 아웃소싱 계약을 구조화할 때", en: "The IT outsourcing arrangement is governed by a master service agreement supplemented by quarterly statements of work.", ko: "IT 아웃소싱 계약은 분기별 작업 명세서로 보완된 기본 서비스 계약에 의해 관리돼요." },
      { situation: "구매팀에서 공급업체 조건을 표준화할 때", en: "Standardizing vendor relationships through master service agreements reduces negotiation time and ensures consistency.", ko: "기본 서비스 계약을 통해 공급업체 관계를 표준화하면 협상 시간이 줄고 일관성이 보장돼요." },
      { situation: "인수 후 공급업체 계약을 통합할 때", en: "Post-acquisition, we transitioned all inherited vendor contracts onto our standard master service agreement template.", ko: "인수 후 상속받은 모든 공급업체 계약을 우리의 표준 기본 서비스 계약 템플릿으로 전환했어요." },
      { situation: "분쟁이 발생했을 때", en: "In the event of a dispute, the master service agreement specifies the governing law and dispute resolution process.", ko: "분쟁 발생 시 기본 서비스 계약은 준거법과 분쟁 해결 절차를 명시해요." }
    ],
    level: "800"
  },
  {
    id: 46,
    word: "severance package",
    pronunciation: "ˈsev.ər.əns ˈpæk.ɪdʒ",
    pos: "n.",
    meaning: "퇴직 위로금 패키지, 퇴직금",
    synonyms: ["separation package", "termination benefits", "redundancy pay"],
    examples: [
      { situation: "구조조정 계획을 발표할 때", en: "All affected employees will receive a severance package that includes three months of salary and career counseling.", ko: "영향받는 모든 직원은 3개월 급여와 경력 상담을 포함하는 퇴직 위로금 패키지를 받게 돼요." },
      { situation: "HR 정책을 검토할 때", en: "Our severance package policy provides one week of pay for every year of service, up to a maximum of 26 weeks.", ko: "우리의 퇴직 위로금 패키지 정책은 최대 26주까지 근무 1년당 1주의 급여를 제공해요." },
      { situation: "임원 계약을 협상할 때", en: "Executive employment contracts typically include a severance package worth 12 to 24 months of total compensation.", ko: "임원 고용 계약은 일반적으로 총 보상의 12~24개월에 해당하는 퇴직 위로금 패키지를 포함해요." },
      { situation: "인력 감축 공지를 준비할 때", en: "The severance package was designed to minimize financial hardship for employees during their transition period.", ko: "퇴직 위로금 패키지는 전환 기간 동안 직원들의 경제적 어려움을 최소화하도록 설계됐어요." },
      { situation: "노동 법규를 준수할 때", en: "Employment lawyers reviewed the severance package to ensure full compliance with local labor regulations.", ko: "노동 변호사들은 퇴직 위로금 패키지가 현지 노동 규정을 완전히 준수하는지 검토했어요." },
      { situation: "M&A 이후 인력 조정을 할 때", en: "Post-merger workforce rationalization required the company to offer competitive severance packages to retain goodwill.", ko: "합병 후 인력 합리화로 인해 회사는 신뢰를 유지하기 위해 경쟁력 있는 퇴직 위로금 패키지를 제공해야 했어요." },
      { situation: "직원 퇴직 협상을 진행할 때", en: "The employee and HR team negotiated the severance package terms over two meetings before reaching agreement.", ko: "직원과 HR팀은 두 번의 회의를 거쳐 퇴직 위로금 패키지 조건에 합의했어요." },
      { situation: "이사회에 구조조정 비용을 보고할 때", en: "The total cost of severance packages for the 150 affected employees is estimated at four million dollars.", ko: "영향받는 150명 직원에 대한 퇴직 위로금 패키지의 총 비용은 400만 달러로 추정돼요." },
      { situation: "성과 부진으로 계약을 종료할 때", en: "Even in cases of performance-based termination, the company offered a basic severance package as a goodwill gesture.", ko: "성과 기반 계약 종료의 경우에도 회사는 호의의 표시로 기본 퇴직 위로금 패키지를 제공했어요." },
      { situation: "자발적 조기 퇴직 프로그램을 운영할 때", en: "The voluntary early retirement program came with an enhanced severance package to encourage participation.", ko: "자발적 조기 퇴직 프로그램에는 참여를 장려하기 위해 강화된 퇴직 위로금 패키지가 포함됐어요." }
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
console.log('Batch 3 done: IDs 30,31,32,37,38,39,40,41,42,46 replaced.');
