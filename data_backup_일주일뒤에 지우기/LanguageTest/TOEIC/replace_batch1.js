// Batch 1: IDs 1,2,3,5,6,7,8,10,11,13 (SEC filing->streamline, abeyance->benchmark, abrogation->leverage, acquiescence->onboarding, actuary->performance appraisal, acumen->business acumen, ad valorem->cost-benefit analysis, adjudicate->key performance indicator, abatement->change management, affidavit->risk mitigation)
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 1,
    word: "streamline",
    pronunciation: "ˈstriːm.laɪn",
    pos: "v.",
    meaning: "간소화하다, 효율화하다",
    synonyms: ["simplify", "optimize", "efficiency"],
    examples: [
      { situation: "업무 프로세스를 개선할 때", en: "We need to streamline the approval process to reduce turnaround time.", ko: "처리 시간을 줄이기 위해 승인 프로세스를 간소화해야 해요." },
      { situation: "팀 회의에서 효율화를 논의할 때", en: "The new software will help us streamline our invoicing and payment workflow.", ko: "새 소프트웨어가 청구서 발행 및 결제 워크플로우를 효율화하는 데 도움이 될 거예요." },
      { situation: "조직 구조조정을 계획할 때", en: "Management decided to streamline the organizational structure by merging two departments.", ko: "경영진은 두 부서를 합쳐 조직 구조를 간소화하기로 결정했어요." },
      { situation: "고객 서비스 절차를 개선할 때", en: "Streamlining the onboarding process improved customer satisfaction scores significantly.", ko: "온보딩 프로세스를 간소화하자 고객 만족도 점수가 크게 향상됐어요." },
      { situation: "공급망 최적화 프로젝트에서", en: "Our goal this quarter is to streamline the supply chain by reducing the number of vendors.", ko: "이번 분기 목표는 공급업체 수를 줄여 공급망을 간소화하는 거예요." },
      { situation: "디지털 전환 계획을 발표할 때", en: "Digital transformation initiatives are designed to streamline operations across all business units.", ko: "디지털 전환 이니셔티브는 모든 사업부의 운영을 효율화하기 위해 설계됐어요." },
      { situation: "비용 절감 방안을 보고할 때", en: "By streamlining procurement, we cut operational costs by 15 percent last year.", ko: "조달 과정을 효율화함으로써 지난해 운영 비용을 15% 절감했어요." },
      { situation: "프로젝트 관리 개선을 논의할 때", en: "We are working to streamline project reporting so stakeholders receive updates automatically.", ko: "이해관계자들이 자동으로 업데이트를 받을 수 있도록 프로젝트 보고 절차를 간소화하고 있어요." },
      { situation: "IT 시스템 통합 작업 중", en: "Consolidating our three legacy platforms will streamline data management considerably.", ko: "세 개의 레거시 플랫폼을 통합하면 데이터 관리가 상당히 효율화될 거예요." },
      { situation: "신제품 출시 준비를 할 때", en: "The product team streamlined the launch checklist to focus on the most critical deliverables.", ko: "제품팀은 가장 중요한 산출물에 집중하기 위해 출시 체크리스트를 간소화했어요." }
    ],
    level: "800"
  },
  {
    id: 2,
    word: "benchmark",
    pronunciation: "ˈbentʃ.mɑːrk",
    pos: "n./v.",
    meaning: "기준, 벤치마크; 기준으로 삼다",
    synonyms: ["standard", "reference point", "yardstick"],
    examples: [
      { situation: "성과 기준을 설정할 때", en: "We use industry benchmarks to evaluate whether our productivity metrics are competitive.", ko: "업계 벤치마크를 활용해 우리의 생산성 지표가 경쟁력 있는지 평가해요." },
      { situation: "경쟁사 분석을 할 때", en: "The sales team benchmarked our pricing against three major competitors before adjusting the rate card.", ko: "영업팀은 요율표를 조정하기 전에 주요 경쟁사 세 곳과 가격을 비교 분석했어요." },
      { situation: "투자 성과를 평가할 때", en: "Our fund consistently outperforms the benchmark index by two percentage points annually.", ko: "우리 펀드는 연간 2%p씩 벤치마크 지수를 꾸준히 상회하고 있어요." },
      { situation: "품질 관리 회의에서", en: "Quality assurance teams must benchmark their processes against ISO standards every two years.", ko: "품질 보증팀은 2년마다 ISO 기준에 맞춰 프로세스를 벤치마크해야 해요." },
      { situation: "KPI 목표를 수립할 때", en: "Setting clear benchmarks for each KPI helps the team stay aligned with annual targets.", ko: "각 KPI에 명확한 벤치마크를 설정하면 팀이 연간 목표에 맞게 정렬하는 데 도움이 돼요." },
      { situation: "경영 컨설팅 프로젝트에서", en: "The consulting firm benchmarked our operational efficiency against best-in-class industry leaders.", ko: "컨설팅 회사는 최고 수준의 업계 선도 기업들과 우리의 운영 효율성을 벤치마크했어요." },
      { situation: "HR 보상 체계를 검토할 때", en: "Salary benchmarking ensures our compensation packages remain attractive in a competitive market.", ko: "급여 벤치마킹은 경쟁 시장에서 우리의 보상 패키지가 매력적으로 유지되도록 해요." },
      { situation: "IT 인프라 성능을 측정할 때", en: "The IT team ran a series of benchmark tests before migrating workloads to the cloud.", ko: "IT팀은 워크로드를 클라우드로 마이그레이션하기 전에 일련의 벤치마크 테스트를 실행했어요." },
      { situation: "신규 시장 진출 전략을 수립할 때", en: "Management set a benchmark of 10 percent market share within the first 18 months of launch.", ko: "경영진은 출시 후 첫 18개월 이내에 시장 점유율 10%를 벤치마크로 설정했어요." },
      { situation: "공급업체 평가를 할 때", en: "Vendor performance is measured against agreed benchmarks on delivery time, quality, and cost.", ko: "공급업체 성과는 납기, 품질, 비용에 관한 합의된 벤치마크 기준으로 측정돼요." }
    ],
    level: "800"
  },
  {
    id: 3,
    word: "leverage",
    pronunciation: "ˈlev.ər.ɪdʒ",
    pos: "v./n.",
    meaning: "활용하다; 영향력, 레버리지",
    synonyms: ["utilize", "capitalize on", "harness"],
    examples: [
      { situation: "강점을 전략적으로 활용할 때", en: "We can leverage our existing customer base to accelerate the rollout of the new product line.", ko: "기존 고객 기반을 활용해 신제품 라인 출시를 가속화할 수 있어요." },
      { situation: "파트너십 협상을 할 때", en: "The company leveraged its strong brand recognition to negotiate better distribution agreements.", ko: "회사는 강한 브랜드 인지도를 활용해 더 유리한 유통 계약을 협상했어요." },
      { situation: "데이터 분석을 비즈니스에 적용할 때", en: "Our marketing team leverages data analytics to personalize campaigns and improve conversion rates.", ko: "마케팅팀은 데이터 분석을 활용해 캠페인을 개인화하고 전환율을 높이고 있어요." },
      { situation: "자금 조달 전략을 논의할 때", en: "The CFO proposed leveraging low interest rates to refinance the company long-term debt.", ko: "CFO는 낮은 금리를 활용해 회사의 장기 부채를 재융자하자고 제안했어요." },
      { situation: "기술 투자 효과를 극대화할 때", en: "By leveraging cloud computing, the startup reduced its IT infrastructure costs by 40 percent.", ko: "클라우드 컴퓨팅을 활용함으로써 스타트업은 IT 인프라 비용을 40% 절감했어요." },
      { situation: "영업팀 전략 회의에서", en: "Sales representatives are trained to leverage testimonials and case studies when closing enterprise deals.", ko: "영업 담당자들은 기업 거래를 성사시킬 때 고객 추천사와 사례 연구를 활용하도록 교육받아요." },
      { situation: "협상 테이블에서 유리한 조건을 얻을 때", en: "Our long-term contract gives us significant leverage when renegotiating pricing with suppliers.", ko: "장기 계약이 공급업체와 가격을 재협상할 때 우리에게 상당한 협상력을 부여해요." },
      { situation: "M&A 기회를 검토할 때", en: "The private equity firm plans to leverage the acquisition to enter three new regional markets.", ko: "사모펀드 회사는 인수를 활용해 세 개의 새로운 지역 시장에 진입할 계획이에요." },
      { situation: "직원 네트워크를 채용에 활용할 때", en: "HR is encouraging managers to leverage their professional networks for talent acquisition.", ko: "HR은 인재 채용을 위해 관리자들이 전문 네트워크를 활용하도록 장려하고 있어요." },
      { situation: "기존 기술력을 사업 확장에 쓸 때", en: "We plan to leverage our proprietary technology platform to offer new SaaS solutions to mid-market clients.", ko: "독점 기술 플랫폼을 활용해 중간 시장 고객들에게 새로운 SaaS 솔루션을 제공할 계획이에요." }
    ],
    level: "800"
  },
  {
    id: 5,
    word: "onboarding",
    pronunciation: "ˈɒn.bɔː.dɪŋ",
    pos: "n.",
    meaning: "신규 직원 입사 교육, 온보딩",
    synonyms: ["orientation", "induction", "integration training"],
    examples: [
      { situation: "신입 직원 교육 프로그램을 설명할 때", en: "A structured onboarding program helps new hires become productive much faster.", ko: "체계적인 온보딩 프로그램은 신입 직원이 훨씬 빠르게 업무 효율을 높이는 데 도움이 돼요." },
      { situation: "HR 프로세스 개선 회의에서", en: "We are redesigning our onboarding process to include a 90-day integration plan for all new employees.", ko: "모든 신규 직원을 위한 90일 통합 계획을 포함하도록 온보딩 프로세스를 재설계하고 있어요." },
      { situation: "원격 근무 직원 관리를 논의할 때", en: "Remote onboarding requires extra effort to ensure new team members feel connected to the company culture.", ko: "원격 온보딩은 신규 팀원들이 회사 문화에 연결감을 느낄 수 있도록 추가적인 노력이 필요해요." },
      { situation: "신규 고객 계정을 담당할 때", en: "The customer success team leads the onboarding for all enterprise accounts to ensure smooth implementation.", ko: "고객 성공팀은 원활한 구현을 보장하기 위해 모든 기업 계정의 온보딩을 이끌어요." },
      { situation: "직원 유지율을 분석할 때", en: "Research shows that effective onboarding increases employee retention rates by up to 82 percent.", ko: "연구에 따르면 효과적인 온보딩이 직원 유지율을 최대 82%까지 높인다고 해요." },
      { situation: "소프트웨어 구현 프로젝트에서", en: "The vendor provided a dedicated onboarding specialist to guide our team through the software setup.", ko: "공급업체는 소프트웨어 설정 과정에서 우리 팀을 안내하기 위해 전담 온보딩 전문가를 파견했어요." },
      { situation: "입사 첫날 일정을 안내할 때", en: "New employees receive a comprehensive onboarding kit that includes a laptop, system access, and a welcome guide.", ko: "신입 직원들은 노트북, 시스템 접근 권한, 환영 가이드가 포함된 종합 온보딩 키트를 받아요." },
      { situation: "관리자 교육 세션에서", en: "Managers play a critical role in onboarding by setting clear expectations during the first week.", ko: "관리자들은 첫 주에 명확한 기대치를 설정함으로써 온보딩에서 중요한 역할을 해요." },
      { situation: "직원 경험 설문 결과를 검토할 때", en: "Survey results indicated that 70 percent of new employees felt the onboarding process was thorough and well-organized.", ko: "설문 결과에 따르면 신입 직원의 70%가 온보딩 과정이 철저하고 잘 조직되어 있다고 느꼈어요." },
      { situation: "파트너 회사 직원을 교육할 때", en: "We extended our onboarding program to include key personnel from our newly acquired subsidiary.", ko: "새로 인수한 자회사의 핵심 인력을 포함하도록 온보딩 프로그램을 확대했어요." }
    ],
    level: "800"
  },
  {
    id: 6,
    word: "performance appraisal",
    pronunciation: "pəˈfɔː.məns əˈpreɪ.zəl",
    pos: "n.",
    meaning: "성과 평가",
    synonyms: ["performance review", "employee evaluation", "annual review"],
    examples: [
      { situation: "연간 평가 일정을 공지할 때", en: "All managers must complete performance appraisals for their direct reports by the end of this month.", ko: "모든 관리자는 이달 말까지 직속 부하 직원의 성과 평가를 완료해야 해요." },
      { situation: "승진 여부를 결정할 때", en: "The promotion committee reviews performance appraisal scores before making final recommendations.", ko: "승진 위원회는 최종 추천을 하기 전에 성과 평가 점수를 검토해요." },
      { situation: "직원과 피드백 면담을 할 때", en: "During the performance appraisal, the manager provided specific feedback on both strengths and areas for improvement.", ko: "성과 평가 동안 관리자는 강점과 개선이 필요한 부분 모두에 대해 구체적인 피드백을 제공했어요." },
      { situation: "HR 정책을 설명할 때", en: "Our company conducts performance appraisals twice a year to keep employees aligned with business goals.", ko: "우리 회사는 직원들이 사업 목표에 맞게 정렬되도록 연 2회 성과 평가를 실시해요." },
      { situation: "보상 체계와 연계할 때", en: "Salary increases and bonuses are directly tied to performance appraisal outcomes.", ko: "급여 인상과 보너스는 성과 평가 결과와 직접 연동되어 있어요." },
      { situation: "역량 개발 계획을 수립할 때", en: "The performance appraisal process includes a development plan section to support employee growth.", ko: "성과 평가 프로세스에는 직원 성장을 지원하기 위한 개발 계획 섹션이 포함되어 있어요." },
      { situation: "새로운 평가 시스템을 도입할 때", en: "We are transitioning from annual to quarterly performance appraisals to provide more timely feedback.", ko: "보다 시기적절한 피드백을 제공하기 위해 연간에서 분기별 성과 평가로 전환하고 있어요." },
      { situation: "저성과자 관리 계획을 논의할 때", en: "Employees who receive a low score in their performance appraisal are placed on a 60-day improvement plan.", ko: "성과 평가에서 낮은 점수를 받은 직원들은 60일 개선 계획에 배치돼요." },
      { situation: "인재 관리 전략 회의에서", en: "Performance appraisal data is used to identify high-potential employees for the leadership succession program.", ko: "성과 평가 데이터는 리더십 승계 프로그램을 위한 고잠재력 직원을 파악하는 데 사용돼요." },
      { situation: "원격 근무 팀 관리를 논의할 때", en: "Conducting fair and objective performance appraisals for remote teams requires clear, measurable KPIs.", ko: "원격 팀에 대한 공정하고 객관적인 성과 평가를 실시하려면 명확하고 측정 가능한 KPI가 필요해요." }
    ],
    level: "800"
  },
  {
    id: 7,
    word: "business acumen",
    pronunciation: "ˈbɪz.nɪs ˈæk.jʊ.mən",
    pos: "n.",
    meaning: "비즈니스 감각, 사업 통찰력",
    synonyms: ["commercial awareness", "business insight", "strategic thinking"],
    examples: [
      { situation: "리더십 역량을 평가할 때", en: "Strong business acumen is one of the most valued leadership competencies in our organization.", ko: "강한 비즈니스 감각은 우리 조직에서 가장 중요하게 여기는 리더십 역량 중 하나예요." },
      { situation: "채용 인터뷰를 진행할 때", en: "The interviewer tested the candidate business acumen with a series of market sizing questions.", ko: "면접관은 시장 규모 측정 질문들로 지원자의 비즈니스 감각을 테스트했어요." },
      { situation: "임원 개발 프로그램을 논의할 때", en: "The executive development program is designed to sharpen business acumen across all functional areas.", ko: "임원 개발 프로그램은 모든 기능 분야에 걸쳐 비즈니스 감각을 키우도록 설계됐어요." },
      { situation: "신규 사업 기회를 평가할 때", en: "Her business acumen allowed her to identify a profitable niche that competitors had overlooked.", ko: "그녀의 비즈니스 감각 덕분에 경쟁사들이 간과한 수익성 있는 틈새 시장을 발견할 수 있었어요." },
      { situation: "영업 팀장 역량을 평가할 때", en: "Employees with strong business acumen tend to make better decisions when allocating resources under pressure.", ko: "비즈니스 감각이 뛰어난 직원들은 압박 상황에서 자원을 배분할 때 더 나은 결정을 내리는 경향이 있어요." },
      { situation: "멘토링 프로그램을 소개할 때", en: "The mentorship program pairs junior staff with senior leaders to help develop their business acumen.", ko: "멘토링 프로그램은 신입 직원의 비즈니스 감각을 키우기 위해 그들을 시니어 리더와 연결해요." },
      { situation: "투자자 미팅 후 피드백을 줄 때", en: "Investors were impressed by the founder business acumen and deep understanding of the competitive landscape.", ko: "투자자들은 창업자의 비즈니스 감각과 경쟁 환경에 대한 깊은 이해에 깊은 인상을 받았어요." },
      { situation: "경영학 교육의 필요성을 강조할 때", en: "Technical skills alone are not enough; today engineers also need strong business acumen to advance.", ko: "기술적 능력만으로는 충분하지 않아요. 오늘날의 엔지니어들도 발전하기 위해 강한 비즈니스 감각이 필요해요." },
      { situation: "부서 간 협업 문화를 만들 때", en: "Cross-functional training programs help employees develop the business acumen needed to collaborate effectively.", ko: "부서 간 교육 프로그램은 직원들이 효과적으로 협업하는 데 필요한 비즈니스 감각을 개발하는 데 도움이 돼요." },
      { situation: "연간 전략 계획 발표에서", en: "The CEO business acumen was evident in how she navigated the company through the economic downturn without layoffs.", ko: "CEO의 비즈니스 감각은 그녀가 정리해고 없이 경기 침체를 헤쳐나간 방식에서 분명하게 드러났어요." }
    ],
    level: "800"
  },
  {
    id: 8,
    word: "cost-benefit analysis",
    pronunciation: "kɒst ˈben.ɪ.fɪt əˈnæl.ɪ.sɪs",
    pos: "n.",
    meaning: "비용-편익 분석",
    synonyms: ["ROI assessment", "feasibility evaluation", "cost analysis"],
    examples: [
      { situation: "신규 투자 타당성을 검토할 때", en: "Before approving the project, the board requested a detailed cost-benefit analysis.", ko: "프로젝트를 승인하기 전에 이사회는 상세한 비용-편익 분석을 요청했어요." },
      { situation: "소프트웨어 도입을 검토할 때", en: "The IT team conducted a cost-benefit analysis to justify the investment in the new ERP system.", ko: "IT팀은 새로운 ERP 시스템에 대한 투자를 정당화하기 위해 비용-편익 분석을 실시했어요." },
      { situation: "아웃소싱 여부를 결정할 때", en: "A cost-benefit analysis showed that outsourcing the logistics function would save the company two million dollars annually.", ko: "비용-편익 분석 결과 물류 기능을 아웃소싱하면 연간 200만 달러를 절약할 수 있는 것으로 나타났어요." },
      { situation: "운영 효율화 방안을 평가할 때", en: "Every process improvement initiative must be supported by a cost-benefit analysis before implementation.", ko: "모든 프로세스 개선 이니셔티브는 시행 전에 비용-편익 분석으로 뒷받침되어야 해요." },
      { situation: "사무실 이전 계획을 논의할 때", en: "The facilities team prepared a cost-benefit analysis comparing the current lease with three alternative locations.", ko: "시설팀은 현재 임대와 세 가지 대안 위치를 비교하는 비용-편익 분석을 준비했어요." },
      { situation: "마케팅 예산 배분을 결정할 때", en: "A cost-benefit analysis of digital versus traditional advertising helped us reallocate the budget more effectively.", ko: "디지털 대 전통 광고 지출에 대한 비용-편익 분석은 예산을 더 효과적으로 재배분하는 데 도움이 됐어요." },
      { situation: "인력 채용 대 자동화를 검토할 때", en: "The cost-benefit analysis revealed that automating the data entry process would break even within 14 months.", ko: "비용-편익 분석 결과 데이터 입력 프로세스 자동화는 14개월 내에 손익분기점에 도달할 것으로 나타났어요." },
      { situation: "공장 확장 투자를 검토할 때", en: "Our operations director presented a cost-benefit analysis supporting a 30 percent expansion of the production facility.", ko: "운영 이사는 생산 시설의 30% 확장을 지지하는 비용-편익 분석을 발표했어요." },
      { situation: "환경 규제 준수 비용을 평가할 때", en: "The cost-benefit analysis of compliance with new environmental regulations showed long-term savings through energy efficiency.", ko: "새로운 환경 규제 준수에 대한 비용-편익 분석은 에너지 효율을 통한 장기적 절감을 보여줬어요." },
      { situation: "경영진 전략 오프사이트에서", en: "Senior management relies on cost-benefit analysis to prioritize capital expenditure projects each fiscal year.", ko: "고위 경영진은 매 회계연도마다 자본 지출 프로젝트의 우선순위를 정하기 위해 비용-편익 분석에 의존해요." }
    ],
    level: "800"
  },
  {
    id: 10,
    word: "key performance indicator",
    pronunciation: "kiː pəˈfɔː.məns ˈɪn.dɪ.keɪ.tər",
    pos: "n.",
    meaning: "핵심 성과 지표, KPI",
    synonyms: ["KPI", "performance metric", "success indicator"],
    examples: [
      { situation: "목표 설정 회의에서", en: "The department head asked each team to define three key performance indicators for the upcoming quarter.", ko: "부서장은 각 팀에게 다음 분기를 위한 세 가지 핵심 성과 지표를 정의하도록 요청했어요." },
      { situation: "월간 성과 보고서를 검토할 때", en: "All key performance indicators are tracked on a real-time dashboard accessible to senior management.", ko: "모든 핵심 성과 지표는 고위 경영진이 접근할 수 있는 실시간 대시보드에서 추적돼요." },
      { situation: "영업팀 성과를 평가할 때", en: "The sales team key performance indicators include monthly revenue, customer acquisition cost, and churn rate.", ko: "영업팀의 핵심 성과 지표에는 월별 매출, 고객 획득 비용, 이탈률이 포함돼요." },
      { situation: "전략적 목표를 측정할 때", en: "Each key performance indicator should be specific, measurable, and directly linked to a strategic objective.", ko: "각 핵심 성과 지표는 구체적이고 측정 가능하며 전략적 목표와 직접 연계되어야 해요." },
      { situation: "이사회 보고를 준비할 때", en: "The quarterly report summarizes progress against key performance indicators agreed at the start of the fiscal year.", ko: "분기 보고서는 회계연도 초에 합의된 핵심 성과 지표 대비 진행 상황을 요약해요." },
      { situation: "새로운 사업부를 출범할 때", en: "Before launching the new division, leadership established key performance indicators to measure its success within year one.", ko: "새 사업부를 출범하기 전에 리더십은 1년 내 성공을 측정하기 위한 핵심 성과 지표를 수립했어요." },
      { situation: "고객 서비스 품질을 관리할 때", en: "Customer satisfaction score and response time are two of the most important key performance indicators for our support team.", ko: "고객 만족도 점수와 응답 시간은 우리 지원팀의 가장 중요한 핵심 성과 지표 두 가지예요." },
      { situation: "공급망 성과를 모니터링할 때", en: "On-time delivery rate is a critical key performance indicator for evaluating our logistics partners.", ko: "정시 납품률은 물류 파트너를 평가하는 중요한 핵심 성과 지표예요." },
      { situation: "마케팅 캠페인 결과를 분석할 때", en: "The marketing team monitors key performance indicators such as click-through rate, conversion rate, and cost per lead.", ko: "마케팅팀은 클릭률, 전환율, 리드당 비용과 같은 핵심 성과 지표를 모니터링해요." },
      { situation: "조직 문화 개선 이니셔티브에서", en: "Employee engagement and absenteeism rate are key performance indicators used to assess workplace culture initiatives.", ko: "직원 참여도와 결근률은 직장 문화 이니셔티브를 평가하는 데 사용되는 핵심 성과 지표예요." }
    ],
    level: "800"
  },
  {
    id: 11,
    word: "change management",
    pronunciation: "tʃeɪndʒ ˈmæn.ɪdʒ.mənt",
    pos: "n.",
    meaning: "변화 관리",
    synonyms: ["organizational change", "transformation management", "transition planning"],
    examples: [
      { situation: "조직 개편 프로젝트를 시작할 때", en: "Effective change management is essential when merging two teams with different work cultures.", ko: "서로 다른 업무 문화를 가진 두 팀을 합칠 때 효과적인 변화 관리가 필수적이에요." },
      { situation: "새로운 시스템 도입을 준비할 때", en: "The change management plan included training sessions, communication updates, and a feedback mechanism.", ko: "변화 관리 계획에는 교육 세션, 커뮤니케이션 업데이트, 피드백 메커니즘이 포함됐어요." },
      { situation: "저항을 극복하는 전략을 논의할 때", en: "Without proper change management, even the best digital transformation initiatives can fail due to employee resistance.", ko: "적절한 변화 관리 없이는 최고의 디지털 전환 이니셔티브도 직원 저항으로 실패할 수 있어요." },
      { situation: "이사회에 전환 계획을 보고할 때", en: "The change management strategy was presented to the board to ensure executive-level support for the transformation.", ko: "전환에 대한 경영진 수준의 지원을 확보하기 위해 변화 관리 전략이 이사회에 발표됐어요." },
      { situation: "합병 후 통합 작업을 진행할 때", en: "Post-merger change management focused on harmonizing HR policies, IT systems, and reporting structures.", ko: "합병 후 변화 관리는 HR 정책, IT 시스템, 보고 구조의 조화에 초점을 맞췄어요." },
      { situation: "외부 컨설턴트를 고용할 때", en: "We engaged a specialized change management consultant to guide employees through the ERP system migration.", ko: "직원들이 ERP 시스템 마이그레이션을 원활히 진행할 수 있도록 전문 변화 관리 컨설턴트를 고용했어요." },
      { situation: "변화에 대한 직원 불안을 해소할 때", en: "Town hall meetings are a key change management tool for addressing employee concerns during restructuring.", ko: "타운홀 미팅은 구조조정 시 직원 우려를 해소하기 위한 핵심 변화 관리 도구예요." },
      { situation: "프로젝트 위험 평가를 할 때", en: "The project risk register identified inadequate change management as one of the top three risks to project success.", ko: "프로젝트 위험 등록부는 부적절한 변화 관리를 프로젝트 성공에 대한 상위 세 가지 위험 중 하나로 식별했어요." },
      { situation: "사내 교육 프로그램을 설계할 때", en: "Change management training was added to the leadership curriculum to prepare managers for future transitions.", ko: "미래의 전환에 대비해 관리자들을 준비시키기 위해 변화 관리 교육이 리더십 커리큘럼에 추가됐어요." },
      { situation: "디지털 혁신 프로젝트 진행 중", en: "Successful change management requires clear communication of the reasons for change and expected benefits.", ko: "성공적인 변화 관리는 변화의 이유와 기대되는 혜택에 대한 명확한 커뮤니케이션을 필요로 해요." }
    ],
    level: "800"
  },
  {
    id: 13,
    word: "risk mitigation",
    pronunciation: "rɪsk ˌmɪt.ɪˈɡeɪ.ʃən",
    pos: "n.",
    meaning: "위험 완화, 리스크 경감",
    synonyms: ["risk reduction", "risk management", "contingency planning"],
    examples: [
      { situation: "프로젝트 킥오프 미팅에서", en: "Risk mitigation strategies must be defined before the project officially kicks off.", ko: "프로젝트가 공식적으로 시작되기 전에 위험 완화 전략을 정의해야 해요." },
      { situation: "공급망 리스크를 관리할 때", en: "Diversifying our supplier base is a key risk mitigation measure against single-source disruptions.", ko: "공급업체 기반을 다양화하는 것은 단일 공급원 중단에 대한 핵심 위험 완화 조치예요." },
      { situation: "보험 정책을 검토할 때", en: "Purchasing comprehensive business insurance is an essential risk mitigation tool for any company.", ko: "종합 비즈니스 보험을 구매하는 것은 모든 회사에 필수적인 위험 완화 도구예요." },
      { situation: "사이버 보안 계획을 수립할 때", en: "Our IT department developed a cybersecurity framework as part of our overall risk mitigation plan.", ko: "IT 부서는 전반적인 위험 완화 계획의 일환으로 사이버 보안 프레임워크를 개발했어요." },
      { situation: "투자 포트폴리오를 검토할 때", en: "Hedging strategies are commonly used for risk mitigation in foreign exchange-exposed businesses.", ko: "헤지 전략은 외환 위험에 노출된 기업에서 위험 완화를 위해 일반적으로 사용돼요." },
      { situation: "규제 컴플라이언스를 점검할 때", en: "Regular compliance audits are a proactive risk mitigation approach that prevents costly violations.", ko: "정기적인 컴플라이언스 감사는 비용이 많이 드는 위반을 예방하는 사전적 위험 완화 방식이에요." },
      { situation: "계약 협상 중에", en: "The legal team inserted a force majeure clause into the contract as a risk mitigation measure.", ko: "법무팀은 위험 완화 조치로 계약서에 불가항력 조항을 삽입했어요." },
      { situation: "이사회 위험 검토 세션에서", en: "The board reviewed the enterprise risk register and approved a new risk mitigation budget for the coming year.", ko: "이사회는 기업 위험 등록부를 검토하고 내년도 새로운 위험 완화 예산을 승인했어요." },
      { situation: "사업 연속성 계획을 수립할 때", en: "Business continuity planning is a critical risk mitigation strategy for companies operating in volatile markets.", ko: "사업 연속성 계획은 변동성이 큰 시장에서 운영하는 기업을 위한 중요한 위험 완화 전략이에요." },
      { situation: "신흥 시장 진출을 준비할 때", en: "Conducting thorough due diligence is essential for risk mitigation when entering an unfamiliar market.", ko: "낯선 시장에 진입할 때 철저한 실사를 수행하는 것이 위험 완화에 필수적이에요." }
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
console.log('Batch 1 done: IDs 1,2,3,5,6,7,8,10,11,13 replaced.');
