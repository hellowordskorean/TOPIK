const fs = require('fs');
const filePath = 'D:\\MakingApps\\Youtube\\Hellowords\\data\\TOEIC\\toeic_800.json';
const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

const idMap = {
  251: {
    "id": 251,
    "word": "rigorous",
    "pronunciation": "/ˈrɪɡ.ər.əs/",
    "pos": "adjective",
    "meaning": "엄격한, 철저한",
    "synonyms": ["thorough", "stringent", "meticulous"],
    "examples": [
      { "situation": "품질 관리 기준 설명", "en": "The factory applies rigorous quality checks before shipping any product.", "ko": "공장은 어떤 제품이든 출하 전에 엄격한 품질 검사를 실시합니다." },
      { "situation": "신규 직원 교육 과정", "en": "New analysts must complete a rigorous training program before handling client accounts.", "ko": "신규 분석가는 고객 계정을 담당하기 전에 철저한 교육 프로그램을 이수해야 합니다." },
      { "situation": "감사 절차 논의", "en": "External auditors conducted a rigorous review of the company's financial statements.", "ko": "외부 감사인이 회사의 재무제표를 철저히 검토했습니다." },
      { "situation": "규정 준수 요건 설명", "en": "The pharmaceutical industry follows rigorous regulatory standards for drug approval.", "ko": "제약 산업은 약품 승인을 위해 엄격한 규제 기준을 따릅니다." },
      { "situation": "프로젝트 테스트 단계 보고", "en": "A rigorous testing phase ensured the software launched without critical bugs.", "ko": "철저한 테스트 단계 덕분에 소프트웨어가 심각한 오류 없이 출시되었습니다." },
      { "situation": "채용 면접 과정 설명", "en": "Candidates go through a rigorous interview process that includes case studies.", "ko": "지원자들은 사례 연구를 포함한 엄격한 면접 과정을 거칩니다." },
      { "situation": "연구 방법론 검토", "en": "The market research team uses rigorous methods to ensure data accuracy.", "ko": "시장 조사팀은 데이터 정확성을 보장하기 위해 엄격한 방법론을 사용합니다." },
      { "situation": "공급업체 심사 절차", "en": "All vendors undergo rigorous vetting before being added to the approved supplier list.", "ko": "모든 공급업체는 승인된 공급업체 목록에 추가되기 전에 엄격한 심사를 받습니다." },
      { "situation": "투자 결정 기준 설명", "en": "The investment committee applies rigorous criteria when evaluating new opportunities.", "ko": "투자위원회는 새로운 기회를 평가할 때 엄격한 기준을 적용합니다." },
      { "situation": "성과 평가 체계 소개", "en": "Our rigorous performance evaluation system ensures fair and objective assessments.", "ko": "우리의 철저한 성과 평가 체계는 공정하고 객관적인 평가를 보장합니다." }
    ],
    "level": "800"
  },
  252: {
    "id": 252,
    "word": "salient",
    "pronunciation": "/ˈseɪ.li.ənt/",
    "pos": "adjective",
    "meaning": "두드러진, 핵심적인",
    "synonyms": ["prominent", "key", "noteworthy"],
    "examples": [
      { "situation": "회의 핵심 포인트 정리", "en": "The manager highlighted the most salient points from the quarterly earnings report.", "ko": "매니저는 분기 실적 보고서에서 가장 핵심적인 사항을 강조했습니다." },
      { "situation": "제안서 검토 회의", "en": "Please summarize the salient features of your proposal before the board meeting.", "ko": "이사회 회의 전에 제안서의 핵심 특징을 요약해 주십시오." },
      { "situation": "신제품 마케팅 브리핑", "en": "The salient advantage of this product is its energy efficiency compared to competitors.", "ko": "이 제품의 두드러진 장점은 경쟁사 대비 에너지 효율성입니다." },
      { "situation": "계약 검토 중 주요 조항 파악", "en": "The legal team identified the most salient clauses in the partnership agreement.", "ko": "법무팀은 파트너십 계약서에서 가장 핵심적인 조항을 파악했습니다." },
      { "situation": "전략 계획 발표", "en": "Our strategy document outlines the salient risks facing the business next year.", "ko": "전략 문서는 내년 사업이 직면한 핵심 리스크를 설명합니다." },
      { "situation": "고객 피드백 분석", "en": "The salient theme in customer feedback was the need for faster response times.", "ko": "고객 피드백에서 두드러진 주제는 더 빠른 응답 시간의 필요성이었습니다." },
      { "situation": "경쟁 분석 보고서 작성", "en": "Analysts noted several salient differences between our product and those of rivals.", "ko": "분석가들은 우리 제품과 경쟁사 제품 사이의 여러 두드러진 차이점을 지적했습니다." },
      { "situation": "임원 보고 자료 준비", "en": "The executive summary should capture only the salient findings from the full report.", "ko": "요약 보고서는 전체 보고서에서 핵심적인 결과만 담아야 합니다." },
      { "situation": "신입 직원 오리엔테이션", "en": "The HR manager explained the salient points of the company's workplace policy.", "ko": "인사 담당자는 회사 직장 정책의 핵심 내용을 설명했습니다." },
      { "situation": "투자자 설명회 준비", "en": "The CFO prepared slides covering the salient financial metrics for investor day.", "ko": "CFO는 투자자의 날을 위한 핵심 재무 지표를 담은 슬라이드를 준비했습니다." }
    ],
    "level": "800"
  },
  255: {
    "id": 255,
    "word": "securitization",
    "pronunciation": "/sɪˌkjʊər.ɪ.taɪˈzeɪ.ʃən/",
    "pos": "noun",
    "meaning": "자산 유동화, 증권화",
    "synonyms": ["asset-backed financing", "structured finance", "collateralization"],
    "examples": [
      { "situation": "대출 채권 관리 전략 논의", "en": "The bank used securitization to convert its mortgage loans into tradeable securities.", "ko": "은행은 자산 유동화를 통해 모기지 대출을 거래 가능한 증권으로 전환했습니다." },
      { "situation": "금융 상품 설명 회의", "en": "Securitization allows companies to raise capital by pooling financial assets.", "ko": "자산 유동화를 통해 기업은 금융 자산을 묶어 자본을 조달할 수 있습니다." },
      { "situation": "리스크 관리 세미나", "en": "The securitization of auto loans helped the lender free up capital for new lending.", "ko": "자동차 대출 유동화는 대출 기관이 신규 대출을 위한 자본을 확보하는 데 도움이 되었습니다." },
      { "situation": "채권 투자 전략 설명", "en": "Investors can gain exposure to diversified loan portfolios through securitization products.", "ko": "투자자는 자산 유동화 상품을 통해 다양화된 대출 포트폴리오에 접근할 수 있습니다." },
      { "situation": "부동산 금융 구조 검토", "en": "Commercial real estate developers often rely on securitization to fund large projects.", "ko": "상업용 부동산 개발자들은 대규모 프로젝트 자금 조달을 위해 종종 자산 유동화에 의존합니다." },
      { "situation": "신용 등급 분석 보고", "en": "The rating agency assessed the risk profile of the securitization vehicle.", "ko": "신용 평가 기관은 자산 유동화 특수목적법인의 위험 프로파일을 평가했습니다." },
      { "situation": "규제 검토 회의", "en": "Post-financial crisis regulations imposed stricter oversight on securitization practices.", "ko": "금융 위기 이후 규정은 자산 유동화 관행에 대한 더 엄격한 감독을 부과했습니다." },
      { "situation": "기업 재무 전략 기획", "en": "The treasurer explored securitization as a way to diversify the company's funding sources.", "ko": "재무 담당자는 회사의 자금 조달원을 다양화하는 방법으로 자산 유동화를 검토했습니다." },
      { "situation": "투자은행 서비스 소개", "en": "Our investment banking team specializes in structuring securitization transactions.", "ko": "우리 투자은행 팀은 자산 유동화 거래 구조화를 전문으로 합니다." },
      { "situation": "재무 보고서 분석", "en": "The company disclosed its securitization arrangements in the annual report footnotes.", "ko": "회사는 연간 보고서 각주에 자산 유동화 약정을 공개했습니다." }
    ],
    "level": "800"
  },
  257: {
    "id": 257,
    "word": "sequester",
    "pronunciation": "/sɪˈkwes.tər/",
    "pos": "verb",
    "meaning": "격리하다, 예산을 삭감하다",
    "synonyms": ["isolate", "set aside", "segregate"],
    "examples": [
      { "situation": "예산 삭감 논의", "en": "The government decided to sequester discretionary spending to reduce the deficit.", "ko": "정부는 재정 적자 감소를 위해 재량 지출을 강제 삭감하기로 결정했습니다." },
      { "situation": "프로젝트 자금 관리", "en": "The finance team chose to sequester funds for the product launch in a separate account.", "ko": "재무팀은 제품 출시 자금을 별도 계좌에 분리 보관하기로 했습니다." },
      { "situation": "기밀 정보 보안 정책", "en": "Sensitive data must be sequestered from the general network to prevent breaches.", "ko": "민감한 데이터는 침해를 방지하기 위해 일반 네트워크에서 격리해야 합니다." },
      { "situation": "연구개발 예산 편성", "en": "The board voted to sequester R&D funds to ensure they are not redirected elsewhere.", "ko": "이사회는 R&D 자금이 다른 곳으로 전용되지 않도록 분리 보관하기로 의결했습니다." },
      { "situation": "팀 격리 근무 방침", "en": "Development teams were sequestered during the final sprint to minimize distractions.", "ko": "개발팀은 집중력을 유지하기 위해 마지막 스프린트 기간 동안 격리되어 근무했습니다." },
      { "situation": "재무 위기 대응 전략", "en": "Emergency reserves were sequestered to cover potential liabilities during the crisis.", "ko": "위기 동안 잠재적 부채를 충당하기 위해 비상 준비금이 분리 적립되었습니다." },
      { "situation": "내부 감사 절차", "en": "Auditors can sequester documents needed as evidence during an internal review.", "ko": "감사인은 내부 검토 중 증거로 필요한 문서를 격리 보관할 수 있습니다." },
      { "situation": "HR 부서 기밀 유지", "en": "HR must sequester employee records to protect confidentiality under data protection law.", "ko": "HR은 개인정보 보호법에 따라 직원 기록을 격리 보관하여 기밀을 유지해야 합니다." },
      { "situation": "규정 준수 검토 회의", "en": "The compliance officer decided to sequester certain accounts pending the investigation.", "ko": "준법감시인은 조사가 진행되는 동안 일부 계좌를 동결하기로 결정했습니다." },
      { "situation": "자금 운용 계획 수립", "en": "The CFO suggested sequestering a portion of profits for future capital expenditures.", "ko": "CFO는 미래 자본 지출을 위해 이익의 일부를 별도 적립할 것을 제안했습니다." }
    ],
    "level": "800"
  },
  263: {
    "id": 263,
    "word": "specific performance",
    "pronunciation": "/spɪˈsɪf.ɪk pərˈfɔːr.məns/",
    "pos": "noun",
    "meaning": "특정 이행 (계약 조항의 이행 강제)",
    "synonyms": ["contractual fulfillment", "obligatory completion", "performance obligation"],
    "examples": [
      { "situation": "계약 이행 분쟁 논의", "en": "The client demanded specific performance of the contract after the supplier failed to deliver.", "ko": "공급업체가 납품에 실패하자 고객은 계약의 특정 이행을 요구했습니다." },
      { "situation": "법무팀 계약 검토", "en": "The agreement included a clause requiring specific performance in case of a breach.", "ko": "계약서에는 위반 발생 시 특정 이행을 요구하는 조항이 포함되어 있었습니다." },
      { "situation": "공급업체 계약 협상", "en": "Specific performance clauses ensure critical deliverables cannot be replaced by monetary compensation.", "ko": "특정 이행 조항은 중요한 납품물이 금전 보상으로 대체될 수 없도록 보장합니다." },
      { "situation": "부동산 거래 계약 체결", "en": "In real estate deals, buyers often seek specific performance to compel the sale of the property.", "ko": "부동산 거래에서 구매자는 종종 매각을 강제하기 위해 특정 이행을 요구합니다." },
      { "situation": "독점 서비스 계약 관리", "en": "The firm relied on specific performance to enforce the exclusive distribution agreement.", "ko": "회사는 독점 유통 계약을 집행하기 위해 특정 이행에 의존했습니다." },
      { "situation": "고가 자산 거래 계약", "en": "Courts may order specific performance when the subject matter is unique and irreplaceable.", "ko": "법원은 해당 사안이 고유하고 대체 불가능한 경우 특정 이행을 명령할 수 있습니다." },
      { "situation": "파트너십 계약 위반 처리", "en": "The partner sought specific performance to enforce the joint venture agreement.", "ko": "파트너는 합작 투자 계약을 집행하기 위해 특정 이행을 요구했습니다." },
      { "situation": "IT 프로젝트 계약 관리", "en": "The software contract included specific performance provisions for milestone deliveries.", "ko": "소프트웨어 계약에는 마일스톤 납품에 대한 특정 이행 조항이 포함되어 있었습니다." },
      { "situation": "국제 계약 분쟁 해결", "en": "International contracts often specify which jurisdiction will enforce specific performance obligations.", "ko": "국제 계약은 어떤 관할권이 특정 이행 의무를 집행할지를 규정하는 경우가 많습니다." },
      { "situation": "서비스 수준 계약 논의", "en": "Service level agreements may include specific performance requirements tied to uptime guarantees.", "ko": "서비스 수준 계약은 가동 시간 보장과 연계된 특정 이행 요건을 포함할 수 있습니다." }
    ],
    "level": "800"
  },
  265: {
    "id": 265,
    "word": "statute of limitations",
    "pronunciation": "/ˈstætʃ.uːt əv ˌlɪm.ɪˈteɪ.ʃənz/",
    "pos": "noun",
    "meaning": "소멸 시효, 청구 가능 기한",
    "synonyms": ["filing deadline", "claim period", "time limit for action"],
    "examples": [
      { "situation": "법무팀 계약 위반 대응", "en": "The company must file its breach-of-contract claim before the statute of limitations expires.", "ko": "회사는 소멸 시효가 만료되기 전에 계약 위반 청구를 제기해야 합니다." },
      { "situation": "고용 분쟁 처리", "en": "The employee was informed that the statute of limitations on wrongful termination claims is two years.", "ko": "직원은 부당 해고 청구의 소멸 시효가 2년임을 통보받았습니다." },
      { "situation": "세금 신고 오류 수정", "en": "Tax authorities have a limited window under the statute of limitations to audit past returns.", "ko": "세무 당국은 소멸 시효에 따라 과거 신고서를 감사할 수 있는 제한된 기간이 있습니다." },
      { "situation": "미수금 회수 전략", "en": "The accounts receivable team tracks the statute of limitations to avoid losing collection rights.", "ko": "매출 채권팀은 회수 권리를 잃지 않기 위해 소멸 시효를 추적합니다." },
      { "situation": "보험 청구 기한 관리", "en": "Policyholders must submit insurance claims within the statute of limitations to receive coverage.", "ko": "보험 가입자는 보장을 받기 위해 소멸 시효 내에 보험 청구를 제출해야 합니다." },
      { "situation": "계약서 법적 검토", "en": "The legal team added clauses to preserve rights beyond the standard statute of limitations.", "ko": "법무팀은 표준 소멸 시효를 넘어 권리를 보존하는 조항을 추가했습니다." },
      { "situation": "공급업체 클레임 대응", "en": "The vendor's warranty claim was rejected because the statute of limitations had already passed.", "ko": "공급업체의 품질 보증 청구는 소멸 시효가 이미 지나 거절되었습니다." },
      { "situation": "투자 사기 조사", "en": "Investigators worked quickly to gather evidence before the statute of limitations ran out.", "ko": "수사관들은 소멸 시효가 만료되기 전에 증거를 수집하기 위해 신속히 움직였습니다." },
      { "situation": "기업 법적 리스크 관리", "en": "Risk managers monitor potential claims to ensure action is taken before statutes of limitations expire.", "ko": "리스크 매니저는 소멸 시효 만료 전에 조치를 취할 수 있도록 잠재 청구를 모니터링합니다." },
      { "situation": "합병 후 책임 검토", "en": "Post-merger, the acquiring company reviewed all pending claims relative to applicable statutes of limitations.", "ko": "합병 후 인수 기업은 적용 소멸 시효와 관련된 모든 계류 중인 청구를 검토했습니다." }
    ],
    "level": "800"
  },
  266: {
    "id": 266,
    "word": "stipulate",
    "pronunciation": "/ˈstɪp.jʊ.leɪt/",
    "pos": "verb",
    "meaning": "명시하다, 규정하다",
    "synonyms": ["specify", "require", "mandate"],
    "examples": [
      { "situation": "계약서 조건 협의", "en": "The contract stipulates that all invoices must be paid within 30 days of receipt.", "ko": "계약서는 모든 청구서가 수령 후 30일 이내에 지불되어야 한다고 명시합니다." },
      { "situation": "서비스 수준 협약 작성", "en": "The SLA stipulates a minimum uptime of 99.9% for the hosted platform.", "ko": "SLA는 호스팅 플랫폼의 최소 가동 시간을 99.9%로 규정합니다." },
      { "situation": "고용 계약 검토", "en": "The employment agreement stipulates a three-month notice period before resignation.", "ko": "고용 계약서는 퇴직 전 3개월 통지 기간을 명시합니다." },
      { "situation": "공급업체 계약 협상", "en": "We stipulated that all delivered goods must meet ISO quality standards.", "ko": "우리는 납품된 모든 상품이 ISO 품질 기준을 충족해야 한다고 규정했습니다." },
      { "situation": "파트너십 계약 체결", "en": "The joint venture agreement stipulates how profits will be divided between the two parties.", "ko": "합작 투자 계약은 두 당사자 간 이익 배분 방법을 명시합니다." },
      { "situation": "규정 준수 정책 공지", "en": "Company policy stipulates that all employees must complete annual compliance training.", "ko": "회사 정책은 모든 직원이 연간 준법 교육을 이수해야 한다고 규정합니다." },
      { "situation": "임대 계약 조건 검토", "en": "The lease agreement stipulates that tenants must obtain approval before making renovations.", "ko": "임대 계약서는 세입자가 리모델링 전에 승인을 받아야 한다고 명시합니다." },
      { "situation": "구매 주문서 조건 설정", "en": "Purchase orders typically stipulate delivery schedules and acceptable quality thresholds.", "ko": "구매 주문서는 일반적으로 납품 일정과 허용 가능한 품질 기준을 명시합니다." },
      { "situation": "비밀유지 계약 협의", "en": "The NDA stipulates that confidential information may not be shared with third parties.", "ko": "비밀유지 계약서는 기밀 정보가 제3자와 공유될 수 없다고 규정합니다." },
      { "situation": "프로젝트 계획 수립", "en": "The project charter stipulates the scope, timeline, and budget for the initiative.", "ko": "프로젝트 헌장은 사업의 범위, 일정 및 예산을 명시합니다." }
    ],
    "level": "800"
  },
  268: {
    "id": 268,
    "word": "suboptimal",
    "pronunciation": "/ˌsʌb.ɒpˈtɪ.məl/",
    "pos": "adjective",
    "meaning": "차선의, 최적이 아닌",
    "synonyms": ["inefficient", "below standard", "less than ideal"],
    "examples": [
      { "situation": "프로세스 개선 회의", "en": "The current approval workflow is suboptimal and causes unnecessary delays.", "ko": "현재 승인 워크플로우는 최적이 아니어서 불필요한 지연을 초래합니다." },
      { "situation": "성과 검토 보고", "en": "Suboptimal inventory management led to both stockouts and overstock situations.", "ko": "차선의 재고 관리로 인해 재고 부족과 과잉 재고 상황이 모두 발생했습니다." },
      { "situation": "IT 시스템 업그레이드 논의", "en": "The legacy system produces suboptimal results due to outdated processing capabilities.", "ko": "레거시 시스템은 노후화된 처리 능력으로 인해 최적이 아닌 결과를 산출합니다." },
      { "situation": "영업팀 전략 검토", "en": "Suboptimal lead qualification is causing sales teams to waste time on low-value prospects.", "ko": "차선의 리드 검증으로 인해 영업팀이 가치가 낮은 잠재 고객에게 시간을 낭비하고 있습니다." },
      { "situation": "공급망 효율성 분석", "en": "Analysts identified suboptimal routing as a major contributor to high logistics costs.", "ko": "분석가들은 차선의 경로 설정이 높은 물류 비용의 주요 원인임을 확인했습니다." },
      { "situation": "회의 효율성 개선 제안", "en": "Holding daily status meetings is suboptimal; weekly updates would suffice.", "ko": "매일 상태 회의를 여는 것은 최적이 아닙니다. 주간 업데이트로 충분할 것입니다." },
      { "situation": "고객 서비스 품질 검토", "en": "Suboptimal response times are negatively impacting our customer satisfaction scores.", "ko": "최적이 아닌 응답 시간이 고객 만족도 점수에 부정적인 영향을 미치고 있습니다." },
      { "situation": "팀 구성 재편 논의", "en": "The current team structure is suboptimal for cross-functional collaboration.", "ko": "현재 팀 구조는 부서 간 협업에 최적화되어 있지 않습니다." },
      { "situation": "마케팅 캠페인 결과 분석", "en": "Suboptimal targeting resulted in low conversion rates despite a substantial ad spend.", "ko": "차선의 타겟팅으로 인해 상당한 광고 지출에도 불구하고 낮은 전환율이 나타났습니다." },
      { "situation": "원가 절감 전략 논의", "en": "Suboptimal procurement practices were identified as a key area for cost savings.", "ko": "최적이 아닌 구매 관행이 비용 절감의 핵심 영역으로 파악되었습니다." }
    ],
    "level": "800"
  },
  276: {
    "id": 276,
    "word": "taxonomy",
    "pronunciation": "/tækˈsɒn.ə.mi/",
    "pos": "noun",
    "meaning": "분류 체계, 분류학",
    "synonyms": ["classification system", "categorization", "framework"],
    "examples": [
      { "situation": "제품 카탈로그 구조 설계", "en": "The e-commerce team developed a clear taxonomy for organizing thousands of product listings.", "ko": "이커머스 팀은 수천 개의 제품 목록을 정리하기 위한 명확한 분류 체계를 개발했습니다." },
      { "situation": "콘텐츠 관리 시스템 구축", "en": "A well-designed content taxonomy makes it easier for users to find relevant information.", "ko": "잘 설계된 콘텐츠 분류 체계는 사용자가 관련 정보를 쉽게 찾을 수 있도록 합니다." },
      { "situation": "데이터 분류 체계 수립", "en": "The IT team created a data taxonomy to standardize how information is stored and retrieved.", "ko": "IT팀은 정보 저장 및 검색 방식을 표준화하기 위해 데이터 분류 체계를 만들었습니다." },
      { "situation": "인재 관리 시스템 도입", "en": "HR established a job taxonomy to define roles and career progression paths clearly.", "ko": "HR은 역할과 경력 개발 경로를 명확히 정의하기 위해 직무 분류 체계를 수립했습니다." },
      { "situation": "리스크 관리 프레임워크 개발", "en": "A risk taxonomy helps companies categorize and prioritize potential threats systematically.", "ko": "리스크 분류 체계는 기업이 잠재적 위협을 체계적으로 분류하고 우선순위를 정하는 데 도움이 됩니다." },
      { "situation": "마케팅 세분화 전략 수립", "en": "The marketing team built a customer taxonomy based on behavior, demographics, and purchase history.", "ko": "마케팅 팀은 행동, 인구 통계 및 구매 이력을 기반으로 고객 분류 체계를 구축했습니다." },
      { "situation": "소프트웨어 개발 문서화", "en": "The development team agreed on a code taxonomy to ensure consistent naming conventions.", "ko": "개발팀은 일관된 명명 규칙을 보장하기 위해 코드 분류 체계에 합의했습니다." },
      { "situation": "지식 관리 시스템 구축", "en": "A knowledge taxonomy enables employees to locate internal resources efficiently.", "ko": "지식 분류 체계는 직원들이 내부 리소스를 효율적으로 찾을 수 있도록 합니다." },
      { "situation": "재무 보고 체계 표준화", "en": "Financial reporting follows a standard taxonomy to ensure comparability across companies.", "ko": "재무 보고는 회사 간 비교 가능성을 보장하기 위해 표준 분류 체계를 따릅니다." },
      { "situation": "공급망 관리 개선", "en": "The procurement team introduced a vendor taxonomy to streamline supplier evaluations.", "ko": "구매팀은 공급업체 평가를 간소화하기 위해 공급업체 분류 체계를 도입했습니다." }
    ],
    "level": "800"
  },
  280: {
    "id": 280,
    "word": "transient",
    "pronunciation": "/ˈtræn.zi.ənt/",
    "pos": "adjective",
    "meaning": "일시적인, 단기간의",
    "synonyms": ["temporary", "short-lived", "fleeting"],
    "examples": [
      { "situation": "인플레이션 전망 논의", "en": "Analysts described the spike in inflation as transient, expecting it to ease within months.", "ko": "분석가들은 인플레이션 급등을 일시적인 현상으로 보고 수개월 내에 완화될 것으로 예상했습니다." },
      { "situation": "IT 시스템 오류 분석", "en": "The system error was transient and resolved itself without manual intervention.", "ko": "시스템 오류는 일시적인 것이었으며 수동 개입 없이 자동으로 해결되었습니다." },
      { "situation": "시장 변동성 평가", "en": "Market volatility can be transient, driven by short-term sentiment rather than fundamentals.", "ko": "시장 변동성은 일시적일 수 있으며, 기본 요소보다는 단기적인 심리에 의해 주도됩니다." },
      { "situation": "직원 이직률 분석", "en": "High turnover in the call center was attributed to a transient workforce with limited engagement.", "ko": "콜센터의 높은 이직률은 참여도가 낮은 일시적인 인력 때문으로 분석되었습니다." },
      { "situation": "공급망 차질 대응", "en": "Supply chain disruptions proved transient as logistics networks gradually normalized.", "ko": "물류 네트워크가 점차 정상화되면서 공급망 차질이 일시적인 것으로 판명되었습니다." },
      { "situation": "프로젝트 자원 배분 논의", "en": "The additional headcount approved for Q3 is transient and will not be renewed next quarter.", "ko": "3분기에 승인된 추가 인력은 일시적이며 다음 분기에 갱신되지 않을 것입니다." },
      { "situation": "고객 불만 사항 처리", "en": "The product defects were transient and confined to a single batch from one supplier.", "ko": "제품 결함은 일시적인 것이었으며 한 공급업체의 단일 배치에 국한되었습니다." },
      { "situation": "재무 성과 변동 설명", "en": "Management attributed the revenue dip to transient factors unrelated to core operations.", "ko": "경영진은 수익 감소를 핵심 운영과 무관한 일시적 요인 탓으로 돌렸습니다." },
      { "situation": "계절적 수요 변화 대응", "en": "Seasonal staffing needs are transient, peaking in Q4 and declining sharply after the holidays.", "ko": "계절적 인력 수요는 일시적이며, 4분기에 최고조에 달했다가 연휴 후 급격히 감소합니다." },
      { "situation": "투자 리스크 평가", "en": "The investment committee considered whether the regulatory risk was transient or structural.", "ko": "투자위원회는 규제 리스크가 일시적인 것인지 구조적인 것인지를 검토했습니다." }
    ],
    "level": "800"
  }
};

data.words = data.words.map(w => idMap[w.id] || w);
fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
console.log('Batch 13 done: IDs 251,252,255,257,263,265,266,268,276,280 replaced.');
