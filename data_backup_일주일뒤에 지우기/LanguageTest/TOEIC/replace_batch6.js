// Batch 6: IDs 84,86,90,91,92,96,99,100,103,105
// correlate->data analytics, covenant not to compete->stock buyback, culminate->milestone
// culpable->executive compensation, cumulative dividend->shareholder value, debenture->line of credit
// defeasance->statement of work, deficiency judgment->angel investor, delineate->intellectual property
// demise->deliverable
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 84,
    word: "data analytics",
    pronunciation: "ˈdeɪ.tə ˌæn.əˈlɪt.ɪks",
    pos: "n.",
    meaning: "데이터 분석",
    synonyms: ["data analysis", "business intelligence", "data insights"],
    examples: [
      { situation: "비즈니스 의사 결정에 데이터를 활용할 때", en: "Our data analytics team identified a 15 percent efficiency gain opportunity in the logistics process.", ko: "데이터 분석팀이 물류 프로세스에서 15%의 효율성 향상 기회를 발견했어요." },
      { situation: "마케팅 캠페인 성과를 측정할 때", en: "Data analytics revealed that email campaigns outperform social media for our target demographic.", ko: "데이터 분석 결과 우리의 타겟 인구층에게 이메일 캠페인이 소셜 미디어보다 성과가 좋은 것으로 나타났어요." },
      { situation: "고객 행동을 이해하려 할 때", en: "Advanced data analytics helps us predict customer churn before it occurs and take preventive action.", ko: "고급 데이터 분석은 고객 이탈이 발생하기 전에 예측하고 예방 조치를 취하는 데 도움이 돼요." },
      { situation: "운영 비용을 최적화할 때", en: "We applied data analytics to our supply chain and reduced inventory holding costs by 20 percent.", ko: "공급망에 데이터 분석을 적용해 재고 보유 비용을 20% 줄였어요." },
      { situation: "이사회에 전략적 인사이트를 보고할 때", en: "The board relies on data analytics dashboards to monitor business performance against strategic objectives.", ko: "이사회는 전략적 목표 대비 사업 성과를 모니터링하기 위해 데이터 분석 대시보드에 의존해요." },
      { situation: "채용 프로세스를 개선할 때", en: "Data analytics has transformed HR by enabling evidence-based decisions on recruitment and workforce planning.", ko: "데이터 분석은 채용 및 인력 계획에 대한 증거 기반 결정을 가능케 함으로써 HR을 변화시켰어요." },
      { situation: "금융 리스크를 관리할 때", en: "Banks use data analytics to assess credit risk and detect fraudulent transactions in real time.", ko: "은행들은 신용 위험을 평가하고 실시간으로 사기 거래를 감지하기 위해 데이터 분석을 사용해요." },
      { situation: "제품 개발 방향을 결정할 때", en: "User behavior data analytics informed the product team which features to prioritize in the next sprint.", ko: "사용자 행동 데이터 분석이 제품팀에게 다음 스프린트에서 어떤 기능을 우선시할지 알려줬어요." },
      { situation: "디지털 전환 계획을 수립할 때", en: "Investing in data analytics capabilities is a foundational step in any digital transformation journey.", ko: "데이터 분석 역량에 투자하는 것은 모든 디지털 전환 여정의 기초적인 단계예요." },
      { situation: "경쟁 우위를 분석할 때", en: "Companies that excel at data analytics consistently outperform their peers in revenue growth and profitability.", ko: "데이터 분석에 뛰어난 기업들은 매출 성장과 수익성에서 지속적으로 동종 업계를 능가해요." }
    ],
    level: "800"
  },
  {
    id: 86,
    word: "stock buyback",
    pronunciation: "stɒk ˈbaɪ.bæk",
    pos: "n.",
    meaning: "자사주 매입",
    synonyms: ["share repurchase", "buyback program", "treasury stock purchase"],
    examples: [
      { situation: "자본 배분 전략을 논의할 때", en: "The board approved a five-billion-dollar stock buyback to return excess capital to shareholders.", ko: "이사회는 잉여 자본을 주주에게 환원하기 위해 50억 달러 규모의 자사주 매입을 승인했어요." },
      { situation: "주가 방어 전략을 수립할 때", en: "Companies often initiate a stock buyback when management believes the shares are undervalued by the market.", ko: "경영진이 주가가 시장에서 저평가되어 있다고 판단할 때 자사주 매입을 개시하는 경우가 많아요." },
      { situation: "주당 이익 개선을 설명할 때", en: "The stock buyback reduced the total share count by 8 percent, boosting earnings per share.", ko: "자사주 매입으로 총 주식 수가 8% 감소해 주당 이익이 높아졌어요." },
      { situation: "투자자들에게 재무 전략을 설명할 때", en: "Analysts debated whether the company should prioritize a stock buyback or invest in organic growth.", ko: "애널리스트들은 회사가 자사주 매입을 우선시해야 할지 유기적 성장에 투자해야 할지 논의했어요." },
      { situation: "잉여 현금 흐름을 활용할 때", en: "With strong free cash flow and no major acquisition targets, management opted for a stock buyback.", ko: "강한 잉여 현금 흐름과 주요 인수 목표가 없는 상황에서 경영진은 자사주 매입을 선택했어요." },
      { situation: "주주총회를 준비할 때", en: "The stock buyback program was one of three capital allocation decisions presented to shareholders at the annual meeting.", ko: "자사주 매입 프로그램은 주주총회에서 주주들에게 발표된 세 가지 자본 배분 결정 중 하나였어요." },
      { situation: "경쟁사와 전략을 비교할 때", en: "Unlike its competitor which chose a stock buyback, our company reinvested profits into R&D.", ko: "자사주 매입을 선택한 경쟁사와 달리 우리 회사는 이익을 R&D에 재투자했어요." },
      { situation: "세금 효율적인 배당 대안을 검토할 때", en: "A stock buyback can be more tax-efficient than dividends for shareholders in higher tax brackets.", ko: "자사주 매입은 높은 세금 구간에 있는 주주들에게 배당보다 더 세금 효율적일 수 있어요." },
      { situation: "공시 의무를 이행할 때", en: "The company filed an 8-K disclosure announcing the commencement of the stock buyback program.", ko: "회사는 자사주 매입 프로그램의 시작을 알리는 8-K 공시를 제출했어요." },
      { situation: "이사회 재무 결정을 보고할 때", en: "The stock buyback was funded through the company revolving credit facility rather than new equity issuance.", ko: "자사주 매입은 신규 주식 발행이 아닌 회사의 회전 신용 한도를 통해 자금이 조달됐어요." }
    ],
    level: "800"
  },
  {
    id: 90,
    word: "milestone",
    pronunciation: "ˈmaɪl.stəʊn",
    pos: "n.",
    meaning: "중요한 단계, 이정표",
    synonyms: ["key deliverable", "checkpoint", "benchmark goal"],
    examples: [
      { situation: "프로젝트 계획을 발표할 때", en: "The project plan includes five key milestones, the first of which is completing the requirements analysis.", ko: "프로젝트 계획에는 5개의 주요 이정표가 포함되며, 첫 번째는 요구사항 분석 완료예요." },
      { situation: "진행 상황을 보고할 때", en: "We are pleased to announce that the team has reached the beta testing milestone ahead of schedule.", ko: "팀이 예정보다 앞서 베타 테스트 이정표에 도달했음을 기쁘게 발표해요." },
      { situation: "계약 기반 결제를 처리할 때", en: "Payments to the contractor are tied to the achievement of specific project milestones.", ko: "도급업체에 대한 결제는 특정 프로젝트 이정표 달성과 연동돼요." },
      { situation: "스타트업 성장을 평가할 때", en: "Reaching one million active users was a major milestone that attracted the attention of Series B investors.", ko: "활성 사용자 100만 명 달성은 시리즈 B 투자자들의 주목을 받은 주요 이정표였어요." },
      { situation: "팀 성과를 축하할 때", en: "The CEO sent a company-wide email to celebrate the milestone of delivering 10,000 orders in a single day.", ko: "CEO는 하루에 1만 건의 주문을 납품한 이정표를 축하하기 위해 전사 이메일을 발송했어요." },
      { situation: "투자자에게 발전 현황을 알릴 때", en: "The startup provided quarterly milestone updates to its investors as part of the reporting obligations.", ko: "스타트업은 보고 의무의 일환으로 투자자들에게 분기별 이정표 업데이트를 제공했어요." },
      { situation: "범위 변경을 협의할 때", en: "Any changes to the project scope may impact the agreed milestone dates and must be approved in advance.", ko: "프로젝트 범위에 대한 변경 사항은 합의된 이정표 날짜에 영향을 줄 수 있으므로 사전에 승인받아야 해요." },
      { situation: "상품 출시 타임라인을 관리할 때", en: "Missing the launch milestone by more than two weeks would significantly impact our holiday season revenue.", ko: "출시 이정표를 2주 이상 놓치면 연말 성수기 매출에 상당한 영향을 미칠 거예요." },
      { situation: "팀 역량을 구축할 때", en: "Completing the leadership training program is a milestone that unlocks eligibility for promotion consideration.", ko: "리더십 교육 프로그램을 완료하는 것은 승진 고려 자격을 얻는 이정표예요." },
      { situation: "M&A 계약 이행을 관리할 때", en: "The acquisition agreement defines earnout milestones the seller must achieve to receive the deferred payment.", ko: "인수 계약은 판매자가 연기된 결제를 받기 위해 달성해야 하는 성과 연동 결제 이정표를 정의해요." }
    ],
    level: "800"
  },
  {
    id: 91,
    word: "executive compensation",
    pronunciation: "ɪɡˈzek.jʊ.tɪv ˌkɒm.penˈseɪ.ʃən",
    pos: "n.",
    meaning: "임원 보상",
    synonyms: ["C-suite pay", "senior management remuneration", "executive pay package"],
    examples: [
      { situation: "주주총회에서 임원 급여를 논의할 때", en: "Shareholders voted to approve the executive compensation package at the annual general meeting.", ko: "주주들은 주주총회에서 임원 보상 패키지를 승인하는 투표를 했어요." },
      { situation: "보상 위원회 보고서를 작성할 때", en: "The compensation committee benchmarks executive compensation against peer companies in the same industry.", ko: "보상 위원회는 같은 업계 동종 기업들과 임원 보상을 벤치마크해요." },
      { situation: "기업 지배구조를 검토할 때", en: "Transparency in executive compensation reporting is now a mandatory requirement under the corporate governance code.", ko: "임원 보상 보고의 투명성은 이제 기업 지배구조 규범에 따른 의무 요건이에요." },
      { situation: "ESG 등급을 평가할 때", en: "Institutional investors increasingly scrutinize executive compensation for alignment with ESG objectives.", ko: "기관 투자자들은 ESG 목표와의 일치 여부에 대해 임원 보상을 점점 더 면밀히 검토하고 있어요." },
      { situation: "인재 유치 전략을 논의할 때", en: "Competitive executive compensation is essential for attracting and retaining top-tier leadership talent.", ko: "경쟁력 있는 임원 보상은 최고 수준의 리더십 인재를 유치하고 유지하는 데 필수적이에요." },
      { situation: "M&A 협상에서 인력 유지를 논의할 때", en: "Post-merger executive compensation was a key negotiating point to ensure leadership continuity.", ko: "리더십 연속성을 보장하기 위해 합병 후 임원 보상이 주요 협상 포인트였어요." },
      { situation: "주주 가치와 연계할 때", en: "Executive compensation is increasingly structured to link pay to long-term shareholder value rather than short-term earnings.", ko: "임원 보상은 단기 이익보다 장기적 주주 가치에 보수를 연계하는 방향으로 점점 더 구조화되고 있어요." },
      { situation: "이사회에 보상 전략을 보고할 때", en: "The board approved a revised executive compensation framework with a greater proportion tied to performance metrics.", ko: "이사회는 성과 지표에 연동된 비율이 더 높은 수정된 임원 보상 프레임워크를 승인했어요." },
      { situation: "입법 변화에 대응할 때", en: "New regulations require listed companies to disclose the ratio of CEO pay to median employee compensation.", ko: "새로운 규정은 상장 기업들이 CEO 보수와 직원 중간 보수 비율을 공시하도록 요구해요." },
      { situation: "투자자 설명회를 준비할 때", en: "Proxy advisors recommended voting against the executive compensation plan due to its excessive cash bonus component.", ko: "위임장 자문사는 지나친 현금 보너스 구성 요소 때문에 임원 보상 계획에 반대 투표를 권고했어요." }
    ],
    level: "800"
  },
  {
    id: 92,
    word: "shareholder value",
    pronunciation: "ˈʃeər.həʊl.dər ˈvæl.juː",
    pos: "n.",
    meaning: "주주 가치",
    synonyms: ["stockholder value", "equity value", "investor return"],
    examples: [
      { situation: "경영 전략을 발표할 때", en: "Every strategic decision we make is evaluated against its potential impact on long-term shareholder value.", ko: "우리가 내리는 모든 전략적 결정은 장기적 주주 가치에 미치는 잠재적 영향에 따라 평가돼요." },
      { situation: "M&A 거래를 평가할 때", en: "The board rejected the acquisition because it would have diluted shareholder value in the short term.", ko: "이사회는 단기적으로 주주 가치를 희석시킬 것이라는 이유로 인수를 거부했어요." },
      { situation: "분기 실적을 발표할 때", en: "The CFO outlined how the new cost reduction program would enhance shareholder value over the next three years.", ko: "CFO는 새로운 비용 절감 프로그램이 향후 3년에 걸쳐 주주 가치를 어떻게 향상시킬지 설명했어요." },
      { situation: "이사회 역할을 설명할 때", en: "The primary duty of the board of directors is to maximize shareholder value within the bounds of the law.", ko: "이사회의 주요 의무는 법의 범위 내에서 주주 가치를 극대화하는 거예요." },
      { situation: "기업 문화 변화를 이끌 때", en: "A short-term focus on shareholder value can sometimes conflict with building a sustainable business culture.", ko: "주주 가치에 대한 단기적 집중은 때로 지속 가능한 기업 문화 구축과 충돌할 수 있어요." },
      { situation: "투자자 관계 활동에서", en: "The investor relations team communicates how management decisions contribute to shareholder value creation.", ko: "투자자 관계팀은 경영 결정이 주주 가치 창출에 어떻게 기여하는지 커뮤니케이션해요." },
      { situation: "ESG 전략과 연계할 때", en: "Research increasingly shows that strong ESG performance correlates with superior long-term shareholder value.", ko: "연구에 따르면 강한 ESG 성과가 우수한 장기적 주주 가치와 상관관계가 있다는 것이 점점 더 드러나고 있어요." },
      { situation: "구조조정 결정을 설명할 때", en: "The restructuring program was initiated to restore shareholder value after two consecutive years of declining returns.", ko: "2년 연속 수익 감소 후 주주 가치를 회복하기 위해 구조조정 프로그램이 시작됐어요." },
      { situation: "합병 시너지를 평가할 때", en: "Analysts estimate the merger will create over two billion dollars of incremental shareholder value within five years.", ko: "애널리스트들은 합병이 5년 내에 20억 달러 이상의 추가적인 주주 가치를 창출할 것으로 추정해요." },
      { situation: "자본 배분을 결정할 때", en: "The capital allocation framework prioritizes investments that deliver the highest risk-adjusted shareholder value.", ko: "자본 배분 프레임워크는 가장 높은 위험 조정 주주 가치를 제공하는 투자를 우선시해요." }
    ],
    level: "800"
  },
  {
    id: 96,
    word: "line of credit",
    pronunciation: "laɪn əv ˈkred.ɪt",
    pos: "n.",
    meaning: "신용 한도, 한도 대출",
    synonyms: ["credit line", "revolving credit", "credit facility"],
    examples: [
      { situation: "단기 자금을 조달할 때", en: "We drew on our line of credit to cover the seasonal increase in inventory purchases.", ko: "계절적 재고 구매 증가를 충당하기 위해 신용 한도를 활용했어요." },
      { situation: "은행과 대출 조건을 협의할 때", en: "The company negotiated a 10-million-dollar revolving line of credit with its primary commercial bank.", ko: "회사는 주거래 상업 은행과 1,000만 달러의 회전 신용 한도를 협상했어요." },
      { situation: "현금 흐름 관리 도구를 검토할 때", en: "Having a line of credit in place provides a safety net for unexpected cash flow shortfalls.", ko: "신용 한도를 보유하면 예상치 못한 현금 흐름 부족에 대한 안전망이 생겨요." },
      { situation: "스타트업 성장 자금을 논의할 때", en: "The startup secured a line of credit backed by its accounts receivable to fund expansion.", ko: "스타트업은 확장 자금을 조달하기 위해 매출채권을 담보로 신용 한도를 확보했어요." },
      { situation: "공급업체 결제 일정을 조율할 때", en: "We used our line of credit to bridge the gap between paying suppliers and collecting from customers.", ko: "공급업체에 결제하고 고객으로부터 수금하는 사이의 간격을 메우기 위해 신용 한도를 사용했어요." },
      { situation: "대출 조건을 재검토할 때", en: "The bank reviewed our line of credit terms annually based on our financial statements and credit history.", ko: "은행은 재무제표와 신용 이력을 바탕으로 신용 한도 조건을 매년 검토했어요." },
      { situation: "CFO 보고를 준비할 때", en: "As of quarter end, we had utilized 60 percent of our available line of credit.", ko: "분기 말 기준으로 사용 가능한 신용 한도의 60%를 활용했어요." },
      { situation: "신용 등급이 중요한 이유를 설명할 때", en: "Maintaining a strong credit rating is essential for securing favorable line of credit terms.", ko: "유리한 신용 한도 조건을 확보하려면 강한 신용 등급을 유지하는 것이 필수적이에요." },
      { situation: "기업 인수 자금을 준비할 때", en: "The acquisition was partly financed by drawing on the company existing line of credit.", ko: "인수 자금의 일부는 회사의 기존 신용 한도를 활용해 조달됐어요." },
      { situation: "재무 비율을 분석할 때", en: "Using a line of credit for operational costs rather than capital investment may signal a liquidity concern.", ko: "자본 투자가 아닌 운영 비용에 신용 한도를 사용하는 것은 유동성 우려를 나타낼 수 있어요." }
    ],
    level: "800"
  },
  {
    id: 99,
    word: "statement of work",
    pronunciation: "ˈsteɪt.mənt əv wɜːk",
    pos: "n.",
    meaning: "작업 명세서, SOW",
    synonyms: ["SOW", "project scope document", "work order"],
    examples: [
      { situation: "컨설팅 회사와 계약을 시작할 때", en: "Before work begins, the consulting firm and the client agree on a detailed statement of work.", ko: "작업이 시작되기 전에 컨설팅 회사와 고객은 상세한 작업 명세서에 동의해요." },
      { situation: "프로젝트 범위를 명확히 할 때", en: "The statement of work defines the deliverables, timelines, and acceptance criteria for the engagement.", ko: "작업 명세서는 계약의 산출물, 일정, 수락 기준을 정의해요." },
      { situation: "청구 분쟁을 방지할 때", en: "A clear statement of work prevents disputes about what services are included in the contract price.", ko: "명확한 작업 명세서는 계약 가격에 어떤 서비스가 포함되는지에 대한 분쟁을 방지해요." },
      { situation: "프로젝트 범위 변경을 관리할 때", en: "Any work outside the original statement of work must be captured in a change order and approved by both parties.", ko: "원래 작업 명세서 범위 밖의 모든 작업은 변경 요청서에 포함되고 양측이 승인해야 해요." },
      { situation: "여러 공급업체를 관리할 때", en: "Each vendor operates under its own statement of work, which is governed by the master service agreement.", ko: "각 공급업체는 기본 서비스 계약에 의해 관리되는 자체 작업 명세서에 따라 운영돼요." },
      { situation: "고객에게 기대치를 설정할 때", en: "A well-written statement of work sets realistic expectations and reduces the risk of client dissatisfaction.", ko: "잘 작성된 작업 명세서는 현실적인 기대치를 설정하고 고객 불만 위험을 줄여요." },
      { situation: "IT 개발 프로젝트를 시작할 때", en: "The software development statement of work includes user stories, sprint schedules, and a testing protocol.", ko: "소프트웨어 개발 작업 명세서에는 사용자 스토리, 스프린트 일정, 테스트 프로토콜이 포함돼요." },
      { situation: "법무팀 계약 검토에서", en: "Legal counsel reviewed the statement of work to ensure all deliverables and timelines were clearly described.", ko: "법률 고문은 모든 산출물과 일정이 명확하게 기술되도록 작업 명세서를 검토했어요." },
      { situation: "프리랜서 계약을 체결할 때", en: "Even for short freelance engagements, a statement of work protects both the client and the service provider.", ko: "짧은 프리랜서 계약에서도 작업 명세서는 고객과 서비스 공급자 모두를 보호해요." },
      { situation: "프로젝트 완료를 확인할 때", en: "Sign-off on the statement of work deliverables triggers the final payment milestone.", ko: "작업 명세서 산출물에 대한 서명이 최종 결제 이정표를 촉발해요." }
    ],
    level: "800"
  },
  {
    id: 100,
    word: "angel investor",
    pronunciation: "ˈeɪn.dʒəl ɪnˈves.tər",
    pos: "n.",
    meaning: "엔젤 투자자",
    synonyms: ["early-stage investor", "seed investor", "private investor"],
    examples: [
      { situation: "스타트업 초기 자금 조달을 설명할 때", en: "The startup raised its first round of funding from an angel investor who believed in the founder vision.", ko: "스타트업은 창업자의 비전을 믿은 엔젤 투자자로부터 첫 번째 자금 조달 라운드를 진행했어요." },
      { situation: "창업 자금 조달 전략을 논의할 때", en: "Many successful companies were built with early support from an angel investor before securing venture capital.", ko: "많은 성공적인 기업들이 벤처 자본을 확보하기 전에 엔젤 투자자의 초기 지원을 받아 성장했어요." },
      { situation: "투자자 네트워크를 구축할 때", en: "The founder presented the business concept to a group of angel investors at a startup pitch event.", ko: "창업자는 스타트업 피치 행사에서 엔젤 투자자 그룹에게 사업 개념을 발표했어요." },
      { situation: "초기 투자 조건을 협상할 때", en: "The angel investor offered a convertible note rather than equity, which is common in early-stage deals.", ko: "엔젤 투자자는 초기 단계 거래에서 일반적인 전환 사채를 주식 대신 제안했어요." },
      { situation: "스타트업 생태계를 설명할 때", en: "Angel investors typically fill the funding gap between friends-and-family rounds and professional venture capital.", ko: "엔젤 투자자들은 일반적으로 가족·지인 라운드와 전문 벤처 자본 사이의 자금 조달 간격을 메워요." },
      { situation: "투자자 가치 제안을 설명할 때", en: "An experienced angel investor brings not only capital but also mentorship and industry connections.", ko: "경험 많은 엔젤 투자자는 자본뿐만 아니라 멘토링과 업계 연결도 제공해요." },
      { situation: "비즈니스 계획서를 작성할 때", en: "The pitch deck was designed to appeal to angel investors by clearly articulating the market opportunity and exit strategy.", ko: "피치 덱은 시장 기회와 출구 전략을 명확히 설명해 엔젤 투자자들의 관심을 끌도록 설계됐어요." },
      { situation: "초기 투자 결과를 분석할 때", en: "The angel investor received a significant return when the company was acquired three years after the initial investment.", ko: "엔젤 투자자는 초기 투자 3년 후 회사가 인수되면서 상당한 수익을 얻었어요." },
      { situation: "투자 리스크를 설명할 때", en: "Angel investing carries high risk as most startups fail, but the potential returns on successful companies can be very large.", ko: "대부분의 스타트업이 실패하기 때문에 엔젤 투자는 높은 위험을 수반하지만 성공한 기업의 잠재적 수익은 매우 클 수 있어요." },
      { situation: "투자자 설명회를 진행할 때", en: "The angel investor asked detailed questions about the go-to-market strategy and the founding team credentials.", ko: "엔젤 투자자는 시장 진출 전략과 창업팀의 자격에 대해 자세한 질문을 했어요." }
    ],
    level: "800"
  },
  {
    id: 103,
    word: "intellectual property",
    pronunciation: "ˌɪn.tɪˌlek.tʃu.əl ˈprɒp.ə.ti",
    pos: "n.",
    meaning: "지적 재산권",
    synonyms: ["IP", "intangible assets", "proprietary rights"],
    examples: [
      { situation: "기술 기업 자산을 평가할 때", en: "The company intellectual property portfolio, including 45 patents, was a key driver of the acquisition premium.", ko: "45개의 특허를 포함한 회사의 지적 재산권 포트폴리오가 인수 프리미엄의 주요 동인이었어요." },
      { situation: "직원 계약을 검토할 때", en: "All employment contracts include a clause assigning intellectual property created on company time to the employer.", ko: "모든 고용 계약에는 회사 근무 시간에 만들어진 지적 재산권을 고용주에게 귀속시키는 조항이 포함돼요." },
      { situation: "파트너십 협정을 체결할 때", en: "The joint development agreement clearly defines how intellectual property created during the collaboration will be owned.", ko: "공동 개발 협약은 협력 중에 만들어진 지적 재산권의 소유 방식을 명확하게 정의해요." },
      { situation: "해외 시장에 진출할 때", en: "Registering intellectual property in all target markets before launching protects the company from local imitators.", ko: "출시 전에 모든 목표 시장에 지적 재산권을 등록하면 현지 모방업체로부터 회사를 보호해요." },
      { situation: "아웃소싱 계약을 체결할 때", en: "The outsourcing contract specifies that all intellectual property developed by the vendor belongs to our company.", ko: "아웃소싱 계약은 공급업체가 개발한 모든 지적 재산권이 우리 회사에 귀속된다고 명시해요." },
      { situation: "법적 분쟁을 관리할 때", en: "The company filed a lawsuit alleging that the competitor had infringed on its core intellectual property.", ko: "회사는 경쟁사가 핵심 지적 재산권을 침해했다고 주장하며 소송을 제기했어요." },
      { situation: "라이선스 계약을 협상할 때", en: "Licensing intellectual property to a third party can generate significant royalty revenue without operational complexity.", ko: "지적 재산권을 제3자에게 라이선스하면 운영 복잡성 없이 상당한 로열티 수익을 창출할 수 있어요." },
      { situation: "실사 과정에서", en: "Due diligence on intellectual property involves verifying ownership, identifying infringement risks, and valuing the IP portfolio.", ko: "지적 재산권에 대한 실사에는 소유권 확인, 침해 위험 파악, IP 포트폴리오 평가가 포함돼요." },
      { situation: "직원 교육을 진행할 때", en: "All staff working on product development receive training on intellectual property protection best practices.", ko: "제품 개발에 종사하는 모든 직원은 지적 재산권 보호 모범 사례에 대한 교육을 받아요." },
      { situation: "브랜드 전략을 수립할 때", en: "Our trademark registrations are a critical component of our intellectual property protection strategy.", ko: "상표 등록은 우리의 지적 재산권 보호 전략의 중요한 구성 요소예요." }
    ],
    level: "800"
  },
  {
    id: 105,
    word: "deliverable",
    pronunciation: "dɪˈlɪv.ər.ə.bəl",
    pos: "n.",
    meaning: "결과물, 납품물",
    synonyms: ["output", "product", "work product"],
    examples: [
      { situation: "프로젝트 킥오프 미팅에서", en: "Each team member received a clear list of deliverables with deadlines at the project kickoff meeting.", ko: "프로젝트 킥오프 미팅에서 각 팀원은 마감일이 있는 명확한 결과물 목록을 받았어요." },
      { situation: "고객과 기대치를 설정할 때", en: "The project manager reviewed all deliverables with the client to ensure mutual understanding before work began.", ko: "작업이 시작되기 전에 프로젝트 관리자가 상호 이해를 보장하기 위해 고객과 모든 결과물을 검토했어요." },
      { situation: "프로젝트 진행 상황을 보고할 때", en: "Three out of five deliverables have been completed on time and within the agreed quality standards.", ko: "5개의 결과물 중 3개가 합의된 품질 기준 내에서 제때 완료됐어요." },
      { situation: "계약서를 검토할 때", en: "The contract lists all deliverables along with acceptance criteria and the consequences of missing deadlines.", ko: "계약서에는 모든 결과물과 수락 기준, 마감일을 놓쳤을 때의 결과가 명시돼요." },
      { situation: "컨설팅 프로젝트를 관리할 때", en: "The final deliverable from the consulting engagement is a 90-day implementation roadmap.", ko: "컨설팅 계약의 최종 결과물은 90일 구현 로드맵이에요." },
      { situation: "범위 변경을 요청받을 때", en: "Adding new requirements mid-project will affect the agreed deliverables and may require a change order.", ko: "프로젝트 중간에 새로운 요구사항을 추가하면 합의된 결과물에 영향을 미치고 변경 요청이 필요할 수 있어요." },
      { situation: "성과를 평가할 때", en: "The team was recognized for submitting all deliverables ahead of schedule without compromising quality.", ko: "팀은 품질을 저해하지 않으면서 모든 결과물을 예정보다 일찍 제출해 인정받았어요." },
      { situation: "결제 조건과 연계할 때", en: "Invoices are issued upon client acceptance of each major deliverable.", ko: "각 주요 결과물에 대한 고객 수락 시 청구서가 발행돼요." },
      { situation: "스프린트 계획 회의에서", en: "The sprint planning session identified six deliverables to be completed in the two-week development cycle.", ko: "스프린트 계획 세션에서 2주 개발 주기에 완료해야 할 6개의 결과물을 파악했어요." },
      { situation: "품질 검토를 진행할 때", en: "Each deliverable is reviewed by a senior team member before being submitted to the client for acceptance.", ko: "각 결과물은 고객 수락을 위해 제출되기 전에 시니어 팀원의 검토를 받아요." }
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
console.log('Batch 6 done: IDs 84,86,90,91,92,96,99,100,103,105 replaced.');
