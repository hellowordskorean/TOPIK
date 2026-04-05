const fs = require('fs');
const filePath = 'D:\\MakingApps\\Youtube\\Hellowords\\data\\TOEIC\\toeic_800.json';
const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

const idMap = {
  282: {
    "id": 282,
    "word": "tranche",
    "pronunciation": "/trɑːnʃ/",
    "pos": "noun",
    "meaning": "분할 지급분, 트랑슈 (자금 배분의 단위)",
    "synonyms": ["installment", "portion", "segment"],
    "examples": [
      { "situation": "투자 자금 집행 계획", "en": "The venture capital firm will release funding in three tranches based on milestone achievements.", "ko": "벤처캐피털 회사는 마일스톤 달성을 기준으로 세 번의 트랑슈로 자금을 집행할 것입니다." },
      { "situation": "대출 상환 일정 협의", "en": "The loan is structured in tranches to align disbursements with project phases.", "ko": "대출은 지급을 프로젝트 단계에 맞추기 위해 트랑슈로 구성되어 있습니다." },
      { "situation": "채권 발행 구조 설명", "en": "The bond offering was divided into tranches with different risk profiles and interest rates.", "ko": "채권 발행은 다양한 위험 프로파일과 이자율을 가진 트랑슈로 나뉘었습니다." },
      { "situation": "스타트업 투자 계약 체결", "en": "The second tranche of investment will be released after the startup reaches 10,000 users.", "ko": "두 번째 투자 트랑슈는 스타트업이 사용자 1만 명에 도달한 후 집행됩니다." },
      { "situation": "구조화 금융 상품 설명", "en": "Institutional investors often purchase specific tranches based on their risk tolerance.", "ko": "기관 투자자들은 리스크 허용 수준에 따라 특정 트랑슈를 매입하는 경우가 많습니다." },
      { "situation": "정부 보조금 집행 계획", "en": "Infrastructure grants are distributed in tranches tied to construction progress reports.", "ko": "인프라 보조금은 건설 진행 보고서에 연계된 트랑슈로 지급됩니다." },
      { "situation": "프로젝트 파이낸싱 구조 설명", "en": "Project finance deals typically release funds in tranches as construction milestones are met.", "ko": "프로젝트 파이낸싱 거래는 일반적으로 건설 마일스톤이 달성될 때마다 트랑슈로 자금을 집행합니다." },
      { "situation": "사모 펀드 출자 일정 논의", "en": "Limited partners received capital calls in tranches over the fund's investment period.", "ko": "유한 파트너들은 펀드 투자 기간 동안 트랑슈로 자본 출자 요청을 받았습니다." },
      { "situation": "인수합병 자금 조달 구조", "en": "The acquisition was financed through a tranche of senior debt and a mezzanine tranche.", "ko": "인수는 선순위 부채 트랑슈와 메자닌 트랑슈를 통해 자금이 조달되었습니다." },
      { "situation": "부동산 개발 자금 관리", "en": "The developer received the final tranche of construction financing upon project completion.", "ko": "개발업자는 프로젝트 완공 시 건설 자금의 최종 트랑슈를 수령했습니다." }
    ],
    "level": "800"
  },
  285: {
    "id": 285,
    "word": "unilateral",
    "pronunciation": "/ˌjuː.nɪˈlæt.ər.əl/",
    "pos": "adjective",
    "meaning": "일방적인, 단독의",
    "synonyms": ["one-sided", "independent", "sole"],
    "examples": [
      { "situation": "계약 변경 사항 통보", "en": "The supplier made a unilateral decision to change pricing without notifying the client.", "ko": "공급업체는 고객에게 통보 없이 일방적으로 가격을 변경하는 결정을 내렸습니다." },
      { "situation": "회사 정책 변경 발표", "en": "Management issued a unilateral directive to end remote work with immediate effect.", "ko": "경영진은 즉각적인 효력으로 재택근무를 종료하는 일방적인 지시를 내렸습니다." },
      { "situation": "파트너십 계약 해지 통보", "en": "Terminating the partnership unilaterally breached several clauses in the agreement.", "ko": "파트너십을 일방적으로 해지하는 것은 계약서의 여러 조항을 위반하는 행위였습니다." },
      { "situation": "무역 협상 협의", "en": "Imposing tariffs unilaterally without negotiation can damage bilateral trade relations.", "ko": "협상 없이 일방적으로 관세를 부과하면 양자 무역 관계를 해칠 수 있습니다." },
      { "situation": "이사회 의사 결정 논의", "en": "The CEO was cautioned against making unilateral decisions that require board approval.", "ko": "CEO는 이사회 승인이 필요한 일방적인 결정을 내리지 말라는 주의를 받았습니다." },
      { "situation": "서비스 조건 변경 안내", "en": "The platform updated its terms of service unilaterally, prompting user backlash.", "ko": "플랫폼은 일방적으로 서비스 약관을 업데이트하여 사용자들의 반발을 샀습니다." },
      { "situation": "급여 조정 정책 논의", "en": "Any unilateral changes to compensation packages must be reviewed by the HR committee.", "ko": "보상 패키지에 대한 모든 일방적인 변경은 HR 위원회의 검토를 받아야 합니다." },
      { "situation": "공급망 계약 재협상", "en": "A unilateral modification to delivery terms can expose the company to legal liability.", "ko": "납품 조건의 일방적인 수정은 회사에 법적 책임을 노출시킬 수 있습니다." },
      { "situation": "투자 결정 승인 절차", "en": "Approval protocols prevent unilateral spending decisions above a set threshold.", "ko": "승인 프로토콜은 설정된 한도를 초과하는 일방적인 지출 결정을 방지합니다." },
      { "situation": "노사 관계 협의", "en": "Labor law prohibits employers from making unilateral changes to collective bargaining agreements.", "ko": "노동법은 고용주가 단체 협약을 일방적으로 변경하는 것을 금지합니다." }
    ],
    "level": "800"
  },
  286: {
    "id": 286,
    "word": "unprecedented",
    "pronunciation": "/ʌnˈpres.ɪ.den.tɪd/",
    "pos": "adjective",
    "meaning": "전례 없는, 유례없는",
    "synonyms": ["extraordinary", "unparalleled", "groundbreaking"],
    "examples": [
      { "situation": "기업 성장 실적 보고", "en": "The company achieved unprecedented revenue growth of 200% in a single fiscal year.", "ko": "회사는 단일 회계연도에 200%라는 전례 없는 매출 성장을 달성했습니다." },
      { "situation": "시장 변화 분석", "en": "The pandemic caused unprecedented disruption across global supply chains.", "ko": "팬데믹은 전 세계 공급망에 전례 없는 혼란을 야기했습니다." },
      { "situation": "제품 출시 성과 발표", "en": "The new product launch generated unprecedented demand, selling out within hours.", "ko": "신제품 출시는 전례 없는 수요를 창출하여 몇 시간 만에 매진되었습니다." },
      { "situation": "기술 혁신 발표", "en": "The AI system demonstrated unprecedented accuracy in processing natural language queries.", "ko": "AI 시스템은 자연어 쿼리 처리에서 전례 없는 정확도를 보여주었습니다." },
      { "situation": "경쟁 환경 분석 보고", "en": "The merger created unprecedented market concentration, drawing regulatory scrutiny.", "ko": "합병은 전례 없는 시장 집중도를 만들어 규제 당국의 조사를 받았습니다." },
      { "situation": "위기 대응 전략 논의", "en": "Management was forced to take unprecedented measures to stabilize cash flow.", "ko": "경영진은 현금 흐름을 안정시키기 위해 전례 없는 조치를 취해야 했습니다." },
      { "situation": "투자자 보고", "en": "The IPO attracted unprecedented investor interest, oversubscribed by ten times.", "ko": "기업공개는 전례 없는 투자자 관심을 끌었으며 10배 초과 청약되었습니다." },
      { "situation": "경제 상황 설명", "en": "Interest rates remained at unprecedented lows for more than a decade.", "ko": "금리는 10년 이상 전례 없는 저수준을 유지했습니다." },
      { "situation": "조직 변화 발표", "en": "The restructuring plan represented an unprecedented transformation of the organization.", "ko": "구조 조정 계획은 조직의 전례 없는 변혁을 나타냈습니다." },
      { "situation": "고객 성공 사례 발표", "en": "Client satisfaction scores reached an unprecedented high following the service redesign.", "ko": "서비스 재설계 후 고객 만족도 점수가 전례 없는 최고치에 도달했습니다." }
    ],
    "level": "800"
  },
  287: {
    "id": 287,
    "word": "usury",
    "pronunciation": "/ˈjuː.ʒər.i/",
    "pos": "noun",
    "meaning": "고리대금, 불법적으로 높은 이자",
    "synonyms": ["predatory lending", "excessive interest", "loan sharking"],
    "examples": [
      { "situation": "소비자 금융 규정 논의", "en": "Consumer protection laws are designed to prevent usury by capping interest rates.", "ko": "소비자 보호법은 이자율 상한을 설정하여 고리대금을 방지하기 위해 설계되었습니다." },
      { "situation": "대출 상품 심사 과정", "en": "The lender was investigated for usury after charging interest rates above the legal limit.", "ko": "대출 기관은 법적 한도를 초과하는 이자율을 부과한 후 고리대금 혐의로 조사를 받았습니다." },
      { "situation": "신용 정책 검토 회의", "en": "Financial regulators have defined usury thresholds to protect vulnerable borrowers.", "ko": "금융 규제 당국은 취약한 차용자를 보호하기 위해 고리대금 기준을 정의했습니다." },
      { "situation": "마이크로파이낸스 규정 논의", "en": "Some payday loan practices have been criticized as usury due to their extremely high rates.", "ko": "일부 단기 대출 관행은 극도로 높은 금리로 인해 고리대금으로 비판받고 있습니다." },
      { "situation": "기업 윤리 정책 수립", "en": "The company committed to ethical lending by ensuring it never engages in usury.", "ko": "회사는 고리대금에 절대 관여하지 않겠다고 약속하며 윤리적 대출을 실천했습니다." },
      { "situation": "소액 대출 사업 검토", "en": "Regulators cracked down on online platforms accused of charging usury-level interest.", "ko": "규제 당국은 고리대금 수준의 이자를 부과했다는 혐의를 받은 온라인 플랫폼을 단속했습니다." },
      { "situation": "국제 금융 비교 분석", "en": "Different countries define usury differently, creating challenges for cross-border lenders.", "ko": "국가마다 고리대금의 정의가 달라 국제 대출 기관에 어려움을 줍니다." },
      { "situation": "소비자 권익 보호 교육", "en": "Consumer advocacy groups educate borrowers on how to identify and avoid usury.", "ko": "소비자 권익 단체는 차용자들이 고리대금을 식별하고 피하는 방법을 교육합니다." },
      { "situation": "채권 회수 방식 검토", "en": "Debt collection using usury tactics can expose a company to serious legal liability.", "ko": "고리대금 전술을 사용한 채권 회수는 회사를 심각한 법적 책임에 노출시킬 수 있습니다." },
      { "situation": "금융 서비스 감사 결과 발표", "en": "The audit revealed that certain loan products bordered on usury under state law.", "ko": "감사 결과 특정 대출 상품이 주법상 고리대금에 가깝다는 사실이 밝혀졌습니다." }
    ],
    "level": "800"
  },
  299: {
    "id": 299,
    "word": "zealous",
    "pronunciation": "/ˈzel.əs/",
    "pos": "adjective",
    "meaning": "열성적인, 열정적인",
    "synonyms": ["enthusiastic", "dedicated", "fervent"],
    "examples": [
      { "situation": "신규 직원 채용 면접", "en": "The hiring manager was impressed by the candidate's zealous approach to customer service.", "ko": "채용 담당자는 지원자의 고객 서비스에 대한 열성적인 태도에 깊은 인상을 받았습니다." },
      { "situation": "영업팀 성과 평가", "en": "A zealous sales team helped the company exceed its annual revenue target by 30%.", "ko": "열성적인 영업팀 덕분에 회사는 연간 매출 목표를 30% 초과 달성했습니다." },
      { "situation": "팀 리더십 개발 프로그램", "en": "Zealous employees who show initiative are often fast-tracked for leadership roles.", "ko": "주도성을 보이는 열성적인 직원들은 종종 리더십 역할로 빠르게 발탁됩니다." },
      { "situation": "고객 지원 팀 운영 방침", "en": "Our support team is zealous about resolving issues before customers escalate their concerns.", "ko": "우리 지원팀은 고객이 불만을 escalate하기 전에 문제를 해결하는 데 열성적입니다." },
      { "situation": "제품 혁신 프로젝트 참여", "en": "Zealous innovators within the company proposed the product feature that became its best seller.", "ko": "회사 내 열성적인 혁신가들이 베스트셀러가 된 제품 기능을 제안했습니다." },
      { "situation": "규정 준수 교육 강조", "en": "The compliance officer is zealous about ensuring all staff understand the latest regulations.", "ko": "준법감시인은 모든 직원이 최신 규정을 이해하도록 하는 데 열성적입니다." },
      { "situation": "마케팅 캠페인 기획", "en": "The marketing team's zealous execution of the campaign led to record-high brand awareness.", "ko": "마케팅팀의 열성적인 캠페인 실행이 역대 최고의 브랜드 인지도를 이끌었습니다." },
      { "situation": "프로젝트 마감 압박 상황", "en": "A zealous project manager kept the team motivated through a challenging product launch.", "ko": "열성적인 프로젝트 매니저는 어려운 제품 출시 과정에서 팀의 동기를 유지시켰습니다." },
      { "situation": "고객 관계 관리 전략", "en": "Zealous account managers build strong long-term relationships with key clients.", "ko": "열성적인 어카운트 매니저들은 핵심 고객과 강력한 장기적 관계를 구축합니다." },
      { "situation": "신시장 개척 전략 발표", "en": "The company's zealous expansion into Asian markets paid off with a 40% revenue increase.", "ko": "회사의 아시아 시장에 대한 열성적인 확장은 40% 매출 증가로 결실을 맺었습니다." }
    ],
    "level": "800"
  }
};

data.words = data.words.map(w => idMap[w.id] || w);
fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
console.log('Batch 14 done: IDs 282,285,286,287,299 replaced.');
