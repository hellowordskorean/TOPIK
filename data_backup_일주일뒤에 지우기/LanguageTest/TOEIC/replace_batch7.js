// Batch 7: IDs 106,115,122,126,128,129,130,132,134,135
// demurrage->commission structure, dilutive->gross margin, dissolution->nearshoring
// domicile->hybrid work model, due process->flexible scheduling, duress->overtime compensation
// earnest money->security deposit, economic moat->competitive advantage (-> brand ambassador instead)
// empirical->corrective action plan, encroachment->territory management
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 106,
    word: "commission structure",
    pronunciation: "kəˈmɪʃ.ən ˈstrʌk.tʃər",
    pos: "n.",
    meaning: "수수료 구조, 커미션 체계",
    synonyms: ["sales commission plan", "incentive pay structure", "variable compensation model"],
    examples: [
      { situation: "영업 직원을 채용할 때", en: "The commission structure offers a base salary plus a tiered percentage of all closed deals.", ko: "수수료 구조는 기본급에 성사된 모든 거래의 단계별 비율을 더하는 방식으로 제공돼요." },
      { situation: "영업팀 동기 부여 전략을 논의할 때", en: "A well-designed commission structure motivates the sales team to prioritize high-value accounts.", ko: "잘 설계된 수수료 구조는 영업팀이 고가치 계정을 우선시하도록 동기를 부여해요." },
      { situation: "보상 체계를 재설계할 때", en: "We are revamping the commission structure to better align sales behavior with long-term customer retention goals.", ko: "장기적인 고객 유지 목표와 영업 행동을 더 잘 일치시키기 위해 수수료 구조를 개편하고 있어요." },
      { situation: "HR 정책을 설명할 때", en: "The new commission structure introduces an accelerator that doubles the rate once a rep exceeds 120 percent of quota.", ko: "새 수수료 구조는 담당자가 할당량의 120%를 초과하면 비율이 두 배가 되는 가속기를 도입해요." },
      { situation: "채용 제안을 협상할 때", en: "The candidate asked detailed questions about the commission structure before accepting the sales role.", ko: "지원자는 영업 직무를 수락하기 전에 수수료 구조에 대해 자세한 질문을 했어요." },
      { situation: "영업 성과를 분석할 때", en: "Reviewing the commission structure revealed that top earners consistently focused on enterprise deals over SMB accounts.", ko: "수수료 구조를 검토하면 최고 수익자들이 중소기업 계정보다 기업 거래에 지속적으로 집중한다는 것이 드러났어요." },
      { situation: "재무팀에 비용을 예측할 때", en: "The finance team modeled the impact of the new commission structure on total sales compensation costs.", ko: "재무팀은 새로운 수수료 구조가 총 영업 보상 비용에 미치는 영향을 모델링했어요." },
      { situation: "파트너 채널을 운영할 때", en: "The partner commission structure rewards channel partners based on deal size, margin, and customer satisfaction scores.", ko: "파트너 수수료 구조는 거래 규모, 마진, 고객 만족도 점수를 기준으로 채널 파트너에게 보상해요." },
      { situation: "팀별 협력을 장려할 때", en: "The revised commission structure includes a team bonus component to encourage collaboration across regions.", ko: "개정된 수수료 구조는 지역 간 협력을 장려하기 위해 팀 보너스 구성 요소를 포함해요." },
      { situation: "목표 달성률을 검토할 때", en: "Quota attainment data informed changes to the commission structure to ensure it remained motivating for all reps.", ko: "할당량 달성률 데이터가 모든 담당자에게 동기 부여가 계속 되도록 수수료 구조 변경에 반영됐어요." }
    ],
    level: "800"
  },
  {
    id: 115,
    word: "gross margin",
    pronunciation: "ɡrəʊs ˈmɑː.dʒɪn",
    pos: "n.",
    meaning: "매출 총이익률",
    synonyms: ["gross profit margin", "gross profit percentage", "product margin"],
    examples: [
      { situation: "재무 성과를 보고할 때", en: "Our gross margin improved from 42 to 48 percent this year due to better procurement terms.", ko: "더 나은 조달 조건 덕분에 올해 매출 총이익률이 42%에서 48%로 향상됐어요." },
      { situation: "가격 전략을 수립할 때", en: "We need to review our pricing model to protect the gross margin as raw material costs rise.", ko: "원자재 비용이 상승하면서 매출 총이익률을 보호하기 위해 가격 모델을 검토해야 해요." },
      { situation: "신제품의 수익성을 평가할 때", en: "The new product line was approved because it carries a gross margin 15 points higher than our existing portfolio.", ko: "신제품 라인은 기존 포트폴리오보다 매출 총이익률이 15%p 높기 때문에 승인됐어요." },
      { situation: "경쟁사와 비교 분석을 할 때", en: "Our gross margin of 55 percent significantly exceeds the industry average of 38 percent.", ko: "우리의 매출 총이익률 55%는 업계 평균 38%를 크게 상회해요." },
      { situation: "이사회에 사업 현황을 보고할 때", en: "Gross margin is the first metric the board reviews when assessing overall business health.", ko: "매출 총이익률은 이사회가 전반적인 사업 건전성을 평가할 때 가장 먼저 검토하는 지표예요." },
      { situation: "비용 절감 계획을 평가할 때", en: "Reducing manufacturing costs by 10 percent would add approximately three points to our gross margin.", ko: "제조 비용을 10% 절감하면 매출 총이익률이 약 3%p 향상될 거예요." },
      { situation: "인수 대상 기업을 평가할 때", en: "The target company consistently delivered a gross margin above 60 percent, making it an attractive acquisition.", ko: "피인수 기업은 꾸준히 60% 이상의 매출 총이익률을 달성해 매력적인 인수 대상이 됐어요." },
      { situation: "투자자에게 사업 모델을 설명할 때", en: "Our SaaS business model generates a gross margin of over 70 percent, enabling significant reinvestment in growth.", ko: "우리의 SaaS 비즈니스 모델은 70% 이상의 매출 총이익률을 창출해 성장에 대한 상당한 재투자를 가능하게 해요." },
      { situation: "할인 정책의 영향을 분석할 때", en: "Aggressive discounting in Q4 helped drive volume but compressed gross margin by four percentage points.", ko: "4분기의 공격적인 할인이 판매량 증대에 도움이 됐지만 매출 총이익률을 4%p 압박했어요." },
      { situation: "사업 계획을 수립할 때", en: "The five-year business plan projects gross margin expansion from 45 to 52 percent through product mix improvement.", ko: "5개년 사업 계획은 제품 믹스 개선을 통해 매출 총이익률이 45%에서 52%로 확대될 것으로 예상해요." }
    ],
    level: "800"
  },
  {
    id: 122,
    word: "nearshoring",
    pronunciation: "ˈnɪər.ʃɔː.rɪŋ",
    pos: "n.",
    meaning: "니어쇼어링, 인근 국가 아웃소싱",
    synonyms: ["regional outsourcing", "proximity sourcing", "nearshore outsourcing"],
    examples: [
      { situation: "공급망 전략을 재검토할 때", en: "The company shifted from offshore manufacturing to nearshoring to reduce lead times and improve supply chain resilience.", ko: "리드 타임을 줄이고 공급망 탄력성을 높이기 위해 회사가 해외 제조에서 니어쇼어링으로 전환했어요." },
      { situation: "인건비와 물류 비용을 비교할 때", en: "Nearshoring may cost more than offshoring in labor terms but offers significant savings in shipping and logistics.", ko: "니어쇼어링은 인건비 측면에서 오프쇼어링보다 더 많은 비용이 들 수 있지만 배송 및 물류에서 상당한 절감을 제공해요." },
      { situation: "운영 전략 회의에서", en: "Nearshoring IT development to Poland reduced time zone challenges and improved collaboration with the headquarters team.", ko: "폴란드로 IT 개발을 니어쇼어링하면서 시간대 문제가 줄고 본사팀과의 협업이 개선됐어요." },
      { situation: "공급망 위험을 완화할 때", en: "Post-pandemic nearshoring initiatives are driven by the need to build more resilient and visible supply chains.", ko: "팬데믹 이후 니어쇼어링 이니셔티브는 더 탄력적이고 가시성 있는 공급망을 구축해야 할 필요에 의해 추진돼요." },
      { situation: "고객 서비스 모델을 검토할 때", en: "We opened a nearshoring customer support center in Mexico to better serve our North American client base.", ko: "북미 고객 기반을 더 잘 지원하기 위해 멕시코에 니어쇼어링 고객 지원 센터를 열었어요." },
      { situation: "비용-편익 분석을 할 때", en: "The nearshoring cost-benefit analysis factored in tariff savings, reduced freight costs, and faster delivery times.", ko: "니어쇼어링 비용-편익 분석은 관세 절감, 운임 감소, 더 빠른 납품 시간을 고려했어요." },
      { situation: "글로벌 소싱 전략을 수립할 때", en: "Our nearshoring strategy focuses on building partnerships with manufacturers in Eastern Europe and North Africa.", ko: "우리의 니어쇼어링 전략은 동유럽과 북아프리카의 제조업체들과 파트너십을 구축하는 데 초점을 맞춰요." },
      { situation: "소프트웨어 개발팀 구조를 논의할 때", en: "Nearshoring software development provides access to skilled engineers at competitive rates with minimal communication barriers.", ko: "소프트웨어 개발을 니어쇼어링하면 최소한의 커뮤니케이션 장벽으로 경쟁력 있는 요금으로 숙련된 엔지니어들에게 접근할 수 있어요." },
      { situation: "환경 및 지속 가능성 목표를 논의할 때", en: "Nearshoring reduces carbon footprint compared to long-haul offshore production by minimizing ocean freight.", ko: "니어쇼어링은 해양 운송을 최소화함으로써 원거리 해외 생산에 비해 탄소 발자국을 줄여요." },
      { situation: "이사회 전략 검토에서", en: "The board endorsed a nearshoring strategy to balance cost efficiency with supply chain flexibility.", ko: "이사회는 비용 효율성과 공급망 유연성의 균형을 맞추기 위한 니어쇼어링 전략을 승인했어요." }
    ],
    level: "800"
  },
  {
    id: 126,
    word: "hybrid work model",
    pronunciation: "ˈhaɪ.brɪd wɜːk ˈmɒd.əl",
    pos: "n.",
    meaning: "하이브리드 근무 모델",
    synonyms: ["blended work model", "flexible work arrangement", "mixed work model"],
    examples: [
      { situation: "팬데믹 이후 근무 방식을 재정립할 때", en: "The company adopted a hybrid work model that requires employees to be in the office three days per week.", ko: "회사는 직원들이 주 3일 사무실에 출근하도록 하는 하이브리드 근무 모델을 채택했어요." },
      { situation: "사무실 공간 전략을 검토할 때", en: "Implementing a hybrid work model allowed us to reduce office space by 40 percent and lower occupancy costs.", ko: "하이브리드 근무 모델을 도입하면서 사무실 공간을 40% 줄이고 임차 비용을 절감할 수 있었어요." },
      { situation: "인재 유치 전략을 논의할 때", en: "Offering a hybrid work model is now a standard expectation for candidates in professional services roles.", ko: "하이브리드 근무 모델 제공은 이제 전문 서비스 직무 지원자들의 표준 기대치가 됐어요." },
      { situation: "팀 협업을 관리할 때", en: "The team lead schedules collaborative workshops on office days to maximize the benefits of the hybrid work model.", ko: "팀 리더는 하이브리드 근무 모델의 혜택을 극대화하기 위해 사무실 근무일에 협업 워크숍을 예약해요." },
      { situation: "직원 참여도를 모니터링할 때", en: "Employee engagement surveys show that 78 percent of staff prefer the hybrid work model over full-time office attendance.", ko: "직원 참여도 설문 결과에 따르면 직원의 78%가 전일제 사무실 출근보다 하이브리드 근무 모델을 선호해요." },
      { situation: "관리자에게 지침을 제공할 때", en: "Managers must ensure equal opportunities for remote and in-office employees under the hybrid work model.", ko: "관리자들은 하이브리드 근무 모델에서 원격 및 사무실 근무 직원들에게 동등한 기회를 보장해야 해요." },
      { situation: "글로벌 팀 협업을 개선할 때", en: "Our hybrid work model includes core collaboration hours to ensure global teams can work together despite time zone differences.", ko: "하이브리드 근무 모델에는 글로벌 팀이 시간대 차이에도 불구하고 함께 일할 수 있도록 핵심 협업 시간이 포함돼요." },
      { situation: "생산성을 측정하고 관리할 때", en: "Transitioning to a hybrid work model required investment in project management tools to track productivity effectively.", ko: "하이브리드 근무 모델로 전환하면서 생산성을 효과적으로 추적하기 위한 프로젝트 관리 도구에 투자가 필요했어요." },
      { situation: "사내 문화를 유지할 때", en: "Preserving a strong company culture under a hybrid work model requires intentional and regular in-person interactions.", ko: "하이브리드 근무 모델에서 강한 기업 문화를 유지하려면 의도적이고 정기적인 대면 상호 작용이 필요해요." },
      { situation: "IT 인프라를 강화할 때", en: "Supporting a hybrid work model requires robust cybersecurity measures and reliable video conferencing infrastructure.", ko: "하이브리드 근무 모델을 지원하려면 강력한 사이버 보안 조치와 신뢰할 수 있는 화상 회의 인프라가 필요해요." }
    ],
    level: "800"
  },
  {
    id: 128,
    word: "flexible scheduling",
    pronunciation: "ˈflek.sɪ.bəl ˈsked.juː.lɪŋ",
    pos: "n.",
    meaning: "유연 근무 일정",
    synonyms: ["flextime", "flexible hours", "agile scheduling"],
    examples: [
      { situation: "HR 복리후생 패키지를 설명할 때", en: "Flexible scheduling is one of the most valued benefits we offer to support work-life balance.", ko: "유연 근무 일정은 일과 생활의 균형을 지원하기 위해 우리가 제공하는 가장 소중한 혜택 중 하나예요." },
      { situation: "다양한 팀원의 필요를 수용할 때", en: "Flexible scheduling accommodates employees with childcare responsibilities without affecting team productivity.", ko: "유연 근무 일정은 팀 생산성에 영향을 미치지 않으면서 육아 책임이 있는 직원들을 수용해요." },
      { situation: "채용 경쟁력을 강화할 때", en: "Offering flexible scheduling helped us attract talent from a wider geographic pool who previously could not commute daily.", ko: "유연 근무 일정을 제공하면서 이전에는 매일 통근할 수 없었던 더 넓은 지역의 인재를 유치할 수 있었어요." },
      { situation: "글로벌 팀을 운영할 때", en: "Flexible scheduling is essential for global teams working across multiple time zones to ensure adequate overlap.", ko: "여러 시간대에 걸쳐 일하는 글로벌 팀에게는 적절한 겹치는 시간을 보장하기 위해 유연 근무 일정이 필수적이에요." },
      { situation: "프로젝트 마감일을 관리할 때", en: "The team used flexible scheduling to absorb the extra workload during the product launch crunch period.", ko: "팀은 제품 출시 집중 기간 동안 추가 업무량을 흡수하기 위해 유연 근무 일정을 활용했어요." },
      { situation: "직원 유지율을 높이려 할 때", en: "Introducing flexible scheduling reduced absenteeism by 18 percent in the first year of implementation.", ko: "유연 근무 일정을 도입하면서 도입 첫해에 결근률이 18% 감소했어요." },
      { situation: "관리자 교육 세션에서", en: "Managers are trained to evaluate performance by outcomes rather than hours worked under a flexible scheduling model.", ko: "유연 근무 일정 모델에서 관리자들은 근무 시간이 아닌 성과로 성과를 평가하도록 교육받아요." },
      { situation: "제조업 현장에서 교대 근무를 조율할 때", en: "Flexible scheduling in the factory reduced overtime costs by optimizing shift coverage based on production needs.", ko: "공장에서의 유연 근무 일정은 생산 필요에 따라 교대 배치를 최적화함으로써 초과 근무 비용을 줄였어요." },
      { situation: "고객 서비스 운영 시간을 확장할 때", en: "Flexible scheduling enabled us to extend customer support coverage from 8 hours to 18 hours per day.", ko: "유연 근무 일정 덕분에 고객 지원 커버리지를 하루 8시간에서 18시간으로 확장할 수 있었어요." },
      { situation: "직원 복지 프로그램을 설계할 때", en: "Flexible scheduling is a core element of our employee wellbeing strategy, alongside mental health support and paid leave.", ko: "유연 근무 일정은 정신 건강 지원 및 유급 휴가와 함께 직원 복지 전략의 핵심 요소예요." }
    ],
    level: "800"
  },
  {
    id: 129,
    word: "overtime compensation",
    pronunciation: "ˌəʊ.vəˈtaɪm ˌkɒm.penˈseɪ.ʃən",
    pos: "n.",
    meaning: "초과 근무 수당",
    synonyms: ["overtime pay", "extra hours pay", "overtime wages"],
    examples: [
      { situation: "급여 정책을 직원에게 안내할 때", en: "All non-exempt employees are entitled to overtime compensation at 1.5 times their regular hourly rate.", ko: "모든 비적용 제외 직원들은 정규 시간당 임금의 1.5배에 해당하는 초과 근무 수당을 받을 자격이 있어요." },
      { situation: "프로젝트 초과 비용을 분석할 때", en: "The project ran three weeks over schedule, resulting in significant overtime compensation costs for the team.", ko: "프로젝트가 3주 일정을 초과하면서 팀에 대한 상당한 초과 근무 수당 비용이 발생했어요." },
      { situation: "노동법을 준수할 때", en: "Failure to pay overtime compensation in accordance with labor law can result in costly legal penalties.", ko: "노동법에 따라 초과 근무 수당을 지급하지 않으면 비용이 많이 드는 법적 처벌을 받을 수 있어요." },
      { situation: "예산 편성 과정에서", en: "The operations team must forecast overtime compensation needs in the annual budget to avoid unexpected cost overruns.", ko: "운영팀은 예상치 못한 비용 초과를 피하기 위해 연간 예산에 초과 근무 수당 필요를 예측해야 해요." },
      { situation: "인력 계획을 최적화할 때", en: "Reducing reliance on overtime compensation by hiring part-time staff during peak periods lowered total labor costs.", ko: "성수기에 시간제 직원을 채용해 초과 근무 수당에 대한 의존도를 줄임으로써 총 인건비가 낮아졌어요." },
      { situation: "급여 담당자가 처리할 때", en: "Overtime compensation is calculated automatically by our HR system based on hours submitted in the timesheet.", ko: "초과 근무 수당은 타임시트에 제출된 시간을 기반으로 HR 시스템이 자동으로 계산해요." },
      { situation: "신규 직원에게 복리후생을 설명할 때", en: "Our overtime compensation policy exceeds the minimum legal requirement to recognize the extra effort of our employees.", ko: "직원들의 추가적인 노력을 인정하기 위해 우리의 초과 근무 수당 정책은 최소 법적 요건을 초과해요." },
      { situation: "비용 통제 회의에서", en: "Department heads must obtain prior approval before authorizing overtime compensation for their teams.", ko: "부서장들은 팀의 초과 근무 수당을 승인하기 전에 사전 승인을 받아야 해요." },
      { situation: "계절적 수요를 관리할 때", en: "During the holiday season, overtime compensation costs typically represent 15 percent of total payroll expenses.", ko: "연말 성수기에 초과 근무 수당 비용은 일반적으로 총 급여 비용의 15%를 차지해요." },
      { situation: "감사 보고서를 검토할 때", en: "The payroll audit found discrepancies in overtime compensation records for two departments.", ko: "급여 감사에서 두 부서의 초과 근무 수당 기록에 불일치가 발견됐어요." }
    ],
    level: "800"
  },
  {
    id: 130,
    word: "security deposit",
    pronunciation: "sɪˈkjʊər.ɪ.ti dɪˈpɒz.ɪt",
    pos: "n.",
    meaning: "보증금",
    synonyms: ["damage deposit", "bond deposit", "surety deposit"],
    examples: [
      { situation: "사무실 임대 계약을 체결할 때", en: "The landlord requires a security deposit equivalent to three months of rent before signing the lease.", ko: "임대인은 임대 계약서 서명 전에 3개월치 임대료에 해당하는 보증금을 요구해요." },
      { situation: "신규 거래처 신용을 설정할 때", en: "Customers with limited credit history may be required to pay a security deposit before receiving goods on account.", ko: "신용 이력이 제한적인 고객들은 외상으로 물품을 받기 전에 보증금을 납부해야 할 수 있어요." },
      { situation: "부동산 임대 협상을 할 때", en: "We negotiated the security deposit down from three months to one month by providing a strong financial guarantee.", ko: "강력한 재정 보증을 제공해 보증금을 3개월에서 1개월로 낮추는 협상을 했어요." },
      { situation: "임대 계약이 종료될 때", en: "The security deposit will be refunded within 30 days after the tenant vacates, less any deductions for damages.", ko: "보증금은 손해 배상을 위한 공제를 제외하고 임차인이 퇴거한 후 30일 이내에 환불돼요." },
      { situation: "회계 처리를 설명할 때", en: "Security deposits paid by tenants are recorded as liabilities on the landlord balance sheet.", ko: "임차인이 납부한 보증금은 임대인 대차대조표에 부채로 기록돼요." },
      { situation: "장비 임대 계약을 체결할 때", en: "Renting heavy equipment typically requires a security deposit to cover potential damage or loss.", ko: "중장비 임대는 일반적으로 잠재적 손해나 분실을 담보하기 위한 보증금을 요구해요." },
      { situation: "법적 분쟁을 예방할 때", en: "A detailed move-in inspection report protects both parties when the security deposit is returned at lease end.", ko: "상세한 입주 검사 보고서는 임대 종료 시 보증금이 반환될 때 양측을 보호해요." },
      { situation: "공급업체 계약을 관리할 때", en: "The utility provider required a security deposit from new commercial accounts before activating services.", ko: "유틸리티 공급업체는 서비스를 활성화하기 전에 신규 상업 계정으로부터 보증금을 요구했어요." },
      { situation: "현금 흐름에 미치는 영향을 설명할 때", en: "Paying a large security deposit upfront tied up working capital that could have been used for operational expenses.", ko: "큰 보증금을 선불로 납부하면서 운영 비용에 사용할 수 있었던 운전자본이 묶였어요." },
      { situation: "임대 조건을 비교할 때", en: "When comparing office leases, always factor in the security deposit requirement as part of the total upfront cost.", ko: "사무실 임대를 비교할 때는 항상 보증금 요건을 총 선불 비용의 일부로 고려해야 해요." }
    ],
    level: "800"
  },
  {
    id: 132,
    word: "brand ambassador",
    pronunciation: "brænd æmˈbæs.ə.dər",
    pos: "n.",
    meaning: "브랜드 앰배서더, 브랜드 홍보 대사",
    synonyms: ["brand advocate", "brand spokesperson", "brand representative"],
    examples: [
      { situation: "마케팅 파트너십을 발표할 때", en: "The company appointed a popular athlete as brand ambassador to increase visibility among younger demographics.", ko: "젊은 인구층에서의 인지도를 높이기 위해 회사는 인기 운동선수를 브랜드 앰배서더로 임명했어요." },
      { situation: "직원 브랜딩 전략을 논의할 때", en: "Satisfied employees are the most authentic brand ambassadors a company can have.", ko: "만족한 직원들은 회사가 가질 수 있는 가장 진정성 있는 브랜드 앰배서더예요." },
      { situation: "소셜 미디어 마케팅 전략을 수립할 때", en: "Our brand ambassador program encourages customers with large social followings to promote our products.", ko: "브랜드 앰배서더 프로그램은 소셜 팔로워가 많은 고객들이 우리 제품을 홍보하도록 장려해요." },
      { situation: "파트너십 계약을 협상할 때", en: "The brand ambassador contract specifies the number of social media posts, events, and exclusivity requirements.", ko: "브랜드 앰배서더 계약은 소셜 미디어 게시물 수, 행사, 독점 요건을 명시해요." },
      { situation: "채용 브랜딩을 강화할 때", en: "Current employees acting as brand ambassadors on LinkedIn attracted 30 percent more applicants to our open roles.", ko: "링크드인에서 브랜드 앰배서더로 활동하는 현직 직원들이 채용 공고에 30% 더 많은 지원자를 유치했어요." },
      { situation: "고객 충성도 프로그램을 설계할 때", en: "Top-tier loyalty program members are invited to become official brand ambassadors and participate in product launches.", ko: "최상위 로열티 프로그램 회원들은 공식 브랜드 앰배서더가 되어 제품 출시에 참여하도록 초대받아요." },
      { situation: "마케팅 ROI를 평가할 때", en: "The brand ambassador campaign generated five times more engagement than traditional paid advertising at half the cost.", ko: "브랜드 앰배서더 캠페인은 절반의 비용으로 전통적인 유료 광고보다 5배 많은 참여를 창출했어요." },
      { situation: "위기 커뮤니케이션을 관리할 때", en: "During the product recall, trusted brand ambassadors helped maintain customer confidence by sharing honest responses.", ko: "제품 리콜 기간 동안 신뢰받는 브랜드 앰배서더들이 정직한 응답을 공유해 고객 신뢰를 유지하는 데 도움이 됐어요." },
      { situation: "글로벌 시장에 진출할 때", en: "We identified local influencers to serve as brand ambassadors in each new international market we entered.", ko: "우리가 진출한 각각의 새로운 국제 시장에서 현지 인플루언서를 브랜드 앰배서더로 발굴했어요." },
      { situation: "파트너십 성과를 평가할 때", en: "The brand ambassador program contributed to a 22 percent increase in brand awareness in the target segment.", ko: "브랜드 앰배서더 프로그램이 목표 세그먼트에서 브랜드 인지도를 22% 높이는 데 기여했어요." }
    ],
    level: "800"
  },
  {
    id: 134,
    word: "corrective action plan",
    pronunciation: "kəˈrek.tɪv ˈæk.ʃən plæn",
    pos: "n.",
    meaning: "시정 조치 계획",
    synonyms: ["improvement plan", "remediation plan", "corrective measures"],
    examples: [
      { situation: "품질 문제를 해결할 때", en: "After the audit findings, management issued a corrective action plan addressing all identified compliance gaps.", ko: "감사 결과 이후 경영진은 파악된 모든 컴플라이언스 격차를 해결하는 시정 조치 계획을 발행했어요." },
      { situation: "저성과 직원을 관리할 때", en: "The manager developed a corrective action plan with specific targets and a 90-day review period for the underperforming employee.", ko: "관리자는 저성과 직원을 위한 구체적인 목표와 90일 검토 기간이 있는 시정 조치 계획을 개발했어요." },
      { situation: "공급업체 문제를 해결할 때", en: "The supplier was issued a formal corrective action plan after delivering three consecutive batches below the agreed quality standard.", ko: "공급업체가 합의된 품질 기준 미달의 배치를 3회 연속 납품한 후 공식 시정 조치 계획을 발행받았어요." },
      { situation: "규제 위반에 대응할 때", en: "The regulator required submission of a corrective action plan within 30 days of identifying the compliance violation.", ko: "규제당국은 컴플라이언스 위반 파악 후 30일 이내에 시정 조치 계획 제출을 요구했어요." },
      { situation: "프로젝트 지연을 해결할 때", en: "The project sponsor requested a corrective action plan to bring the delayed project back on track.", ko: "프로젝트 스폰서는 지연된 프로젝트를 정상 궤도에 올려놓기 위한 시정 조치 계획을 요청했어요." },
      { situation: "고객 불만을 처리할 때", en: "Following the service failure, we provided the client with a detailed corrective action plan and a timeline for resolution.", ko: "서비스 실패 이후 고객에게 상세한 시정 조치 계획과 해결 일정을 제공했어요." },
      { situation: "내부 감사 결과를 따를 때", en: "Internal audit recommendations are tracked through a corrective action plan until full resolution is confirmed.", ko: "내부 감사 권고 사항은 완전한 해결이 확인될 때까지 시정 조치 계획을 통해 추적돼요." },
      { situation: "안전 사고를 예방할 때", en: "The workplace safety incident triggered an immediate corrective action plan to prevent recurrence.", ko: "직장 안전 사고로 재발을 방지하기 위한 즉각적인 시정 조치 계획이 촉발됐어요." },
      { situation: "이사회에 문제 해결 현황을 보고할 때", en: "The board receives a monthly update on open corrective action plans to monitor progress on critical issues.", ko: "이사회는 중요한 문제에 대한 진행 상황을 모니터링하기 위해 미결 시정 조치 계획에 대한 월간 업데이트를 받아요." },
      { situation: "ISO 인증 유지를 위해", en: "Maintaining ISO certification requires documenting and closing out all corrective action plans within specified timeframes.", ko: "ISO 인증을 유지하려면 모든 시정 조치 계획을 지정된 시간 내에 문서화하고 완료해야 해요." }
    ],
    level: "800"
  },
  {
    id: 135,
    word: "territory management",
    pronunciation: "ˈter.ɪ.tər.i ˈmæn.ɪdʒ.mənt",
    pos: "n.",
    meaning: "영역 관리, 담당 구역 관리",
    synonyms: ["sales territory management", "regional account management", "geographic coverage"],
    examples: [
      { situation: "영업팀 구조를 설계할 때", en: "Effective territory management ensures that each sales representative has a balanced and achievable quota.", ko: "효과적인 영역 관리는 각 영업 담당자가 균형 잡히고 달성 가능한 할당량을 갖도록 해요." },
      { situation: "신규 영업 지역을 배분할 때", en: "We redesigned our territory management approach to reduce overlap and ensure every prospect is covered.", ko: "중복을 줄이고 모든 잠재 고객이 커버되도록 영역 관리 방식을 재설계했어요." },
      { situation: "영업 성과를 분석할 때", en: "Territory management analysis revealed significant revenue potential in the underserved Midwest region.", ko: "영역 관리 분석에서 서비스가 부족한 중서부 지역에 상당한 매출 잠재력이 있음을 발견했어요." },
      { situation: "CRM을 활용해 계정을 관리할 때", en: "Our CRM system supports territory management by mapping accounts, activities, and pipeline by geographic region.", ko: "CRM 시스템은 지역별로 계정, 활동, 파이프라인을 매핑해 영역 관리를 지원해요." },
      { situation: "확장 계획을 수립할 때", en: "As part of our expansion plan, territory management was updated to include five new metropolitan areas.", ko: "확장 계획의 일환으로 영역 관리가 5개의 새로운 대도시 지역을 포함하도록 업데이트됐어요." },
      { situation: "영업 담당자를 훈련할 때", en: "New sales hires receive territory management training to understand their account list and competitive landscape.", ko: "신규 영업 직원들은 담당 계정 목록과 경쟁 환경을 이해하기 위해 영역 관리 교육을 받아요." },
      { situation: "자원을 효율적으로 배분할 때", en: "Good territory management maximizes sales productivity by matching representative effort to market potential.", ko: "좋은 영역 관리는 담당자의 노력을 시장 잠재력에 맞춤으로써 영업 생산성을 극대화해요." },
      { situation: "이직 후 업무를 인수인계할 때", en: "When a sales representative leaves, territory management protocols ensure a smooth handover to avoid client disruption.", ko: "영업 담당자가 퇴사할 때 영역 관리 프로토콜은 고객 혼란을 방지하기 위한 원활한 인수인계를 보장해요." },
      { situation: "파트너 채널을 운영할 때", en: "Territory management for channel partners prevents conflicts between direct sales and partner-led accounts.", ko: "채널 파트너를 위한 영역 관리는 직접 영업과 파트너 주도 계정 간의 충돌을 방지해요." },
      { situation: "연간 판매 계획을 수립할 때", en: "Territory management reviews are conducted annually to realign coverage with changes in market size and customer concentration.", ko: "영역 관리 검토는 시장 규모와 고객 집중도의 변화에 맞게 커버리지를 재조정하기 위해 매년 실시돼요." }
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
console.log('Batch 7 done: IDs 106,115,122,126,128,129,130,132,134,135 replaced.');
