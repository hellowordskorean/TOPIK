// Batch 9: IDs 173,175,176,177,178,183,184,189,190,191
// implicit->user experience, indefeasible->product roadmap, indemnification->sprint planning
// indemnify->backlog management, inherent->user story, interlocutory->incident management
// ipso facto->post-mortem, lucrative->bootstrapping, macroeconomic->market capitalization, malfeasance->EBITDA
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('toeic_800.json', 'utf8'));

const newEntries = [
  {
    id: 173,
    word: "user experience",
    pronunciation: "ˈjuː.zər ɪkˈspɪər.ɪ.əns",
    pos: "n.",
    meaning: "사용자 경험, UX",
    synonyms: ["UX", "customer experience", "usability"],
    examples: [
      { situation: "제품 설계 전략을 논의할 때", en: "Investing in user experience design reduced our app abandonment rate by 40 percent.", ko: "사용자 경험 디자인에 투자하면서 앱 이탈률이 40% 감소했어요." },
      { situation: "웹사이트 리디자인을 계획할 때", en: "A user experience audit identified five critical friction points in the checkout flow.", ko: "사용자 경험 감사에서 결제 흐름의 다섯 가지 중요한 마찰 포인트를 파악했어요." },
      { situation: "고객 만족도를 높이려 할 때", en: "Companies that prioritize user experience consistently outperform competitors in customer retention metrics.", ko: "사용자 경험을 우선시하는 기업들은 고객 유지 지표에서 지속적으로 경쟁사를 능가해요." },
      { situation: "개발팀과 디자인팀이 협업할 때", en: "Our user experience team works alongside engineers to ensure that technical constraints do not compromise usability.", ko: "사용자 경험팀은 기술적 제약이 사용성을 저해하지 않도록 엔지니어들과 함께 일해요." },
      { situation: "A/B 테스트를 진행할 때", en: "User experience testing showed that a simplified navigation menu increased engagement by 22 percent.", ko: "사용자 경험 테스트에서 간소화된 탐색 메뉴가 참여도를 22% 높인다는 것을 보여줬어요." },
      { situation: "B2B 소프트웨어를 평가할 때", en: "Enterprise buyers increasingly evaluate user experience as a key procurement criterion alongside features and price.", ko: "기업 구매자들은 기능과 가격과 함께 사용자 경험을 핵심 조달 기준으로 점점 더 평가하고 있어요." },
      { situation: "고객 피드백을 분석할 때", en: "User interviews revealed that poor user experience in the mobile app was driving customers to use competitor platforms.", ko: "사용자 인터뷰에서 모바일 앱의 낮은 사용자 경험이 고객들을 경쟁사 플랫폼으로 몰아가고 있음이 드러났어요." },
      { situation: "디지털 전환 프로젝트에서", en: "User experience improvements were central to the digital transformation effort, increasing adoption rates across departments.", ko: "사용자 경험 개선이 디지털 전환 노력의 핵심이 되어 부서 전반에 걸쳐 채택률을 높였어요." },
      { situation: "접근성 요건을 충족할 때", en: "Improving user experience for people with disabilities expanded our addressable market and strengthened our brand reputation.", ko: "장애인을 위한 사용자 경험을 개선하면서 잠재 시장이 확대되고 브랜드 명성이 강화됐어요." },
      { situation: "제품 로드맵을 우선순위화할 때", en: "User experience research directly informs our product roadmap by identifying which pain points to address first.", ko: "사용자 경험 연구는 먼저 해결할 문제점을 파악함으로써 제품 로드맵에 직접 정보를 제공해요." }
    ],
    level: "800"
  },
  {
    id: 175,
    word: "product roadmap",
    pronunciation: "ˈprɒd.ʌkt ˈrəʊd.mæp",
    pos: "n.",
    meaning: "제품 로드맵",
    synonyms: ["development roadmap", "feature roadmap", "product plan"],
    examples: [
      { situation: "제품 전략 발표를 준비할 때", en: "The product roadmap outlines planned features for the next 12 months, prioritized by customer value and business impact.", ko: "제품 로드맵은 고객 가치와 사업 영향에 따라 우선순위가 정해진 향후 12개월의 계획된 기능을 개요로 해요." },
      { situation: "개발팀 계획을 공유할 때", en: "The quarterly product roadmap review aligns engineering, sales, and marketing on upcoming capabilities.", ko: "분기별 제품 로드맵 검토는 개발, 영업, 마케팅이 다가오는 기능에 대해 일치하도록 해요." },
      { situation: "투자자에게 성장 계획을 발표할 때", en: "Investors were impressed by the depth of the product roadmap, which showed three years of innovation ahead.", ko: "투자자들은 3년의 혁신을 앞서 보여주는 제품 로드맵의 깊이에 깊은 인상을 받았어요." },
      { situation: "고객 요구사항을 수집할 때", en: "Customer feedback is the primary input used to shape and prioritize the product roadmap.", ko: "고객 피드백이 제품 로드맵을 구성하고 우선순위를 정하는 데 사용되는 주요 입력이에요." },
      { situation: "경쟁사와 차별화 전략을 수립할 때", en: "Our product roadmap includes three features that no competitor currently offers, reinforcing our market position.", ko: "제품 로드맵에는 현재 어떤 경쟁사도 제공하지 않는 세 가지 기능이 포함돼 시장 위치를 강화해요." },
      { situation: "범위 변경 요청을 관리할 때", en: "All new feature requests are evaluated against the existing product roadmap before being added to the backlog.", ko: "모든 새로운 기능 요청은 백로그에 추가되기 전에 기존 제품 로드맵에 대해 평가돼요." },
      { situation: "크로스 펑셔널 팀을 조율할 때", en: "Sharing the product roadmap with all departments ensures cross-functional alignment on priorities and timelines.", ko: "모든 부서와 제품 로드맵을 공유하면 우선순위와 일정에 대한 부서 간 조율이 보장돼요." },
      { situation: "영업팀에게 미래 기능을 설명할 때", en: "Sales can use the product roadmap to reassure prospects that their key feature requests are planned for future releases.", ko: "영업팀은 제품 로드맵을 사용해 잠재 고객의 주요 기능 요청이 향후 릴리스에 계획되어 있다고 안심시킬 수 있어요." },
      { situation: "스프린트 계획을 수립할 때", en: "Sprint tasks are pulled from items on the product roadmap that have been broken down into actionable user stories.", ko: "스프린트 작업은 실행 가능한 사용자 스토리로 분해된 제품 로드맵 항목에서 끌어와요." },
      { situation: "인수 후 통합을 계획할 때", en: "Post-acquisition, the product roadmaps of both companies were merged into a single unified development plan.", ko: "인수 후 두 회사의 제품 로드맵이 하나의 통합된 개발 계획으로 합쳐졌어요." }
    ],
    level: "800"
  },
  {
    id: 176,
    word: "sprint planning",
    pronunciation: "sprɪnt ˈplæn.ɪŋ",
    pos: "n.",
    meaning: "스프린트 계획, 스프린트 기획",
    synonyms: ["iteration planning", "agile planning", "development sprint planning"],
    examples: [
      { situation: "애자일 개발 방법론을 따를 때", en: "Sprint planning is held at the start of each two-week cycle to define the team goals and task assignments.", ko: "팀 목표와 작업 배정을 정의하기 위해 매 2주 주기 시작 시 스프린트 계획이 열려요." },
      { situation: "백로그를 관리할 때", en: "During sprint planning, the team selects the highest-priority items from the product backlog to complete in the sprint.", ko: "스프린트 계획 중에 팀은 스프린트에서 완료할 제품 백로그의 최우선 항목을 선택해요." },
      { situation: "개발 속도를 측정할 때", en: "Tracking story points across sprints helps the team refine estimates during sprint planning sessions.", ko: "스프린트 전반에 걸쳐 스토리 포인트를 추적하면 스프린트 계획 세션에서 팀이 추정치를 개선하는 데 도움이 돼요." },
      { situation: "이해관계자의 기대를 관리할 때", en: "Sprint planning outcomes are shared with stakeholders so they know what to expect at the end of each cycle.", ko: "스프린트 계획 결과는 이해관계자들과 공유되어 각 주기 말에 무엇을 기대할지 알 수 있어요." },
      { situation: "교차 기능 팀 협업에서", en: "Effective sprint planning requires input from product, design, and engineering to ensure shared understanding.", ko: "효과적인 스프린트 계획은 공유된 이해를 보장하기 위해 제품, 디자인, 엔지니어링의 참여를 필요로 해요." },
      { situation: "우선순위를 변경해야 할 때", en: "Changes in business priorities may require adjusting sprint planning to accommodate urgent feature requests.", ko: "사업 우선순위의 변화는 긴급한 기능 요청을 수용하기 위해 스프린트 계획을 조정하도록 요구할 수 있어요." },
      { situation: "신규 팀원이 합류할 때", en: "New team members attend sprint planning sessions to learn the team workflow and contribute to capacity estimations.", ko: "신규 팀원들은 팀 워크플로우를 배우고 용량 추정에 기여하기 위해 스프린트 계획 세션에 참석해요." },
      { situation: "릴리스 일정을 계획할 때", en: "Sprint planning data allows the product manager to accurately forecast release dates based on team velocity.", ko: "스프린트 계획 데이터를 통해 제품 관리자가 팀 속도를 기반으로 릴리스 날짜를 정확하게 예측할 수 있어요." },
      { situation: "품질을 보장할 때", en: "Sprint planning includes time allocation for testing and code review to maintain consistent quality standards.", ko: "스프린트 계획에는 일관된 품질 기준을 유지하기 위한 테스트 및 코드 검토 시간 배분이 포함돼요." },
      { situation: "원격 팀과 협업할 때", en: "We conduct virtual sprint planning sessions using online collaboration tools to coordinate distributed teams.", ko: "분산된 팀을 조율하기 위해 온라인 협업 도구를 사용해 가상 스프린트 계획 세션을 진행해요." }
    ],
    level: "800"
  },
  {
    id: 177,
    word: "backlog management",
    pronunciation: "ˈbæk.lɒɡ ˈmæn.ɪdʒ.mənt",
    pos: "n.",
    meaning: "백로그 관리",
    synonyms: ["product backlog refinement", "task queue management", "backlog grooming"],
    examples: [
      { situation: "제품 개발팀 운영을 설명할 때", en: "Effective backlog management ensures the development team always has clearly defined and prioritized work ready.", ko: "효과적인 백로그 관리는 개발팀이 항상 명확하게 정의되고 우선순위가 정해진 작업을 준비할 수 있도록 해요." },
      { situation: "제품 관리자의 역할을 설명할 때", en: "The product manager is responsible for backlog management, including writing user stories and prioritizing features.", ko: "제품 관리자는 사용자 스토리 작성 및 기능 우선순위 결정을 포함한 백로그 관리를 담당해요." },
      { situation: "개발 우선순위를 논의할 때", en: "Backlog management sessions are held weekly to review, refine, and reprioritize items before sprint planning.", ko: "스프린트 계획 전에 항목을 검토, 개선, 재우선순위화하기 위해 주간 백로그 관리 세션이 열려요." },
      { situation: "스프린트 속도를 개선할 때", en: "Poor backlog management can slow down development by leaving engineers without clear tasks or acceptance criteria.", ko: "불량한 백로그 관리는 엔지니어들에게 명확한 작업이나 수락 기준이 없어 개발을 지연시킬 수 있어요." },
      { situation: "이해관계자 요청을 처리할 때", en: "All stakeholder feature requests go into the backlog and are subject to the standard backlog management process.", ko: "모든 이해관계자 기능 요청은 백로그에 들어가고 표준 백로그 관리 프로세스를 거쳐요." },
      { situation: "기술 부채를 관리할 때", en: "Backlog management must balance new feature development against addressing technical debt to maintain code quality.", ko: "백로그 관리는 코드 품질을 유지하기 위해 신규 기능 개발과 기술 부채 해결의 균형을 맞춰야 해요." },
      { situation: "팀 역량을 계획할 때", en: "Accurate backlog management allows the engineering manager to forecast resource needs and hiring timelines.", ko: "정확한 백로그 관리는 엔지니어링 관리자가 자원 필요와 채용 일정을 예측할 수 있게 해요." },
      { situation: "고객 피드백을 통합할 때", en: "Customer support tickets are regularly reviewed and translated into backlog items through our backlog management process.", ko: "고객 지원 티켓이 백로그 관리 프로세스를 통해 정기적으로 검토되고 백로그 항목으로 변환돼요." },
      { situation: "대규모 팀을 조율할 때", en: "With multiple product teams, centralized backlog management prevents duplication of effort and conflicting development priorities.", ko: "여러 제품팀의 경우 중앙화된 백로그 관리는 중복 노력과 상충하는 개발 우선순위를 방지해요." },
      { situation: "린 방법론을 적용할 때", en: "Limiting work in progress is a key principle of effective backlog management under a lean development approach.", ko: "진행 중인 작업을 제한하는 것은 린 개발 접근 방식에서 효과적인 백로그 관리의 핵심 원칙이에요." }
    ],
    level: "800"
  },
  {
    id: 178,
    word: "user story",
    pronunciation: "ˈjuː.zər ˈstɔː.ri",
    pos: "n.",
    meaning: "사용자 스토리",
    synonyms: ["feature requirement", "agile story", "use case narrative"],
    examples: [
      { situation: "애자일 팀에서 기능을 정의할 때", en: "Each user story describes a feature from the perspective of the end user to ensure we build the right thing.", ko: "각 사용자 스토리는 올바른 것을 구축하도록 최종 사용자의 관점에서 기능을 설명해요." },
      { situation: "백로그를 정제할 때", en: "During backlog refinement, the team breaks down epics into individual user stories with clear acceptance criteria.", ko: "백로그 정제 중에 팀은 에픽을 명확한 수락 기준이 있는 개별 사용자 스토리로 분해해요." },
      { situation: "제품 요구사항을 문서화할 때", en: "A well-written user story follows the format: As a user, I want to perform an action so that I achieve a goal.", ko: "잘 작성된 사용자 스토리는 다음 형식을 따라요. 사용자로서 나는 목표를 달성하기 위해 어떤 행동을 하고 싶다." },
      { situation: "개발 추정을 할 때", en: "The development team estimated each user story in story points based on relative complexity and effort.", ko: "개발팀은 상대적인 복잡성과 노력을 기반으로 각 사용자 스토리를 스토리 포인트로 추정했어요." },
      { situation: "QA 테스트를 준비할 때", en: "Acceptance criteria within each user story define the conditions that must be met for the story to be considered complete.", ko: "각 사용자 스토리 내의 수락 기준은 스토리가 완료된 것으로 간주되기 위해 충족되어야 하는 조건을 정의해요." },
      { situation: "고객 요구사항을 개발팀에 전달할 때", en: "User stories bridge the communication gap between business stakeholders and the engineering team.", ko: "사용자 스토리는 비즈니스 이해관계자와 엔지니어링 팀 간의 커뮤니케이션 간격을 메워요." },
      { situation: "스프린트 검토를 준비할 때", en: "At the end of each sprint, completed user stories are demonstrated to the product owner for acceptance.", ko: "각 스프린트 말에 완료된 사용자 스토리가 수락을 위해 제품 소유자에게 시연돼요." },
      { situation: "기술 부채를 줄이려 할 때", en: "Some user stories are written specifically to address technical debt rather than new user-facing features.", ko: "일부 사용자 스토리는 새로운 사용자 대면 기능이 아닌 기술 부채를 해결하기 위해 특별히 작성돼요." },
      { situation: "팀 협업을 개선할 때", en: "Writing user stories collaboratively with the product owner and engineers improves shared understanding of requirements.", ko: "제품 소유자와 엔지니어들과 협력적으로 사용자 스토리를 작성하면 요구사항에 대한 공유된 이해가 향상돼요." },
      { situation: "제품 범위를 관리할 때", en: "Scope creep can be controlled by requiring all new requirements to be formalized as user stories before development begins.", ko: "범위 확장은 모든 새로운 요구사항이 개발 시작 전에 사용자 스토리로 공식화되도록 요구함으로써 통제할 수 있어요." }
    ],
    level: "800"
  },
  {
    id: 183,
    word: "incident management",
    pronunciation: "ˈɪn.sɪ.dənt ˈmæn.ɪdʒ.mənt",
    pos: "n.",
    meaning: "인시던트 관리, 사고 관리",
    synonyms: ["issue management", "event management", "problem management"],
    examples: [
      { situation: "IT 운영 팀에서 장애를 처리할 때", en: "Our incident management process classifies outages by severity and defines response times for each level.", ko: "인시던트 관리 프로세스는 장애를 심각도에 따라 분류하고 각 수준에 대한 응답 시간을 정의해요." },
      { situation: "서비스 중단에 대응할 때", en: "The incident management team restored full service within two hours of the initial outage notification.", ko: "인시던트 관리팀은 최초 장애 알림 후 2시간 내에 완전한 서비스를 복구했어요." },
      { situation: "IT 운영 성숙도를 평가할 때", en: "A mature incident management framework reduces mean time to resolution and minimizes business impact.", ko: "성숙한 인시던트 관리 프레임워크는 평균 해결 시간을 줄이고 사업 영향을 최소화해요." },
      { situation: "사이버 보안 사고에 대응할 때", en: "Cybersecurity incident management requires a specialized playbook that covers detection, containment, and recovery steps.", ko: "사이버 보안 인시던트 관리는 감지, 격리, 복구 단계를 다루는 전문화된 플레이북을 필요로 해요." },
      { situation: "SLA를 준수할 때", en: "Effective incident management is essential for meeting the response time commitments in our service level agreements.", ko: "효과적인 인시던트 관리는 서비스 수준 협약의 응답 시간 약정을 충족하는 데 필수적이에요." },
      { situation: "ITSM 도구를 도입할 때", en: "We implemented an ITSM platform to centralize incident management and improve cross-team coordination.", ko: "인시던트 관리를 중앙화하고 팀 간 조율을 개선하기 위해 ITSM 플랫폼을 구현했어요." },
      { situation: "사후 분석을 진행할 때", en: "All critical incidents undergo a formal post-incident review as part of the incident management lifecycle.", ko: "모든 중요한 인시던트는 인시던트 관리 생명 주기의 일환으로 공식적인 사후 검토를 거쳐요." },
      { situation: "규제 요건을 충족할 때", en: "Financial regulators require documented incident management procedures and evidence of regular testing.", ko: "금융 규제당국은 문서화된 인시던트 관리 절차와 정기적인 테스트 증거를 요구해요." },
      { situation: "고객 커뮤니케이션을 관리할 때", en: "Incident management protocols include a communication template to update customers during service disruptions.", ko: "인시던트 관리 프로토콜에는 서비스 중단 중 고객을 업데이트하기 위한 커뮤니케이션 템플릿이 포함돼요." },
      { situation: "지속적 개선을 추구할 때", en: "Lessons learned from each incident are fed back into the incident management process to prevent recurrence.", ko: "각 인시던트에서 얻은 교훈이 재발 방지를 위해 인시던트 관리 프로세스에 피드백돼요." }
    ],
    level: "800"
  },
  {
    id: 184,
    word: "post-mortem",
    pronunciation: "ˌpəʊstˈmɔː.tɪm",
    pos: "n.",
    meaning: "사후 검토, 포스트모텀",
    synonyms: ["retrospective review", "lessons learned session", "after-action review"],
    examples: [
      { situation: "프로젝트가 완료되거나 실패했을 때", en: "The team held a post-mortem after the product launch to document what went well and what could be improved.", ko: "팀은 제품 출시 후 잘 된 점과 개선할 수 있는 점을 문서화하기 위해 사후 검토를 실시했어요." },
      { situation: "IT 장애가 발생한 이후", en: "A post-mortem analysis of the server outage identified three contributing factors that the team immediately addressed.", ko: "서버 장애에 대한 사후 검토 분석에서 팀이 즉시 해결한 세 가지 기여 요인을 파악했어요." },
      { situation: "영업 거래 실패를 분석할 때", en: "Sales leadership conducted a post-mortem on every lost deal over 100,000 dollars to extract learning opportunities.", ko: "영업 리더십은 학습 기회를 추출하기 위해 10만 달러 이상의 모든 실패한 거래에 대해 사후 검토를 실시했어요." },
      { situation: "사건 재발을 방지하려 할 때", en: "A blameless post-mortem culture encourages honest reflection without fear of punishment, leading to better outcomes.", ko: "책임을 추궁하지 않는 사후 검토 문화는 처벌에 대한 두려움 없이 솔직한 반성을 장려해 더 나은 결과로 이어져요." },
      { situation: "조직 학습을 강화할 때", en: "Post-mortem findings are documented and shared company-wide to prevent the same mistakes in other teams.", ko: "사후 검토 결과는 다른 팀에서 같은 실수를 방지하기 위해 문서화되고 회사 전반에 공유돼요." },
      { situation: "고객 프로젝트를 마무리할 때", en: "At project close, a post-mortem with the client identified improvements for future engagements.", ko: "프로젝트 완료 시 고객과의 사후 검토에서 향후 계약을 위한 개선 사항을 파악했어요." },
      { situation: "마케팅 캠페인을 평가할 때", en: "The marketing team runs a post-mortem after every major campaign to capture insights before planning the next one.", ko: "마케팅팀은 다음 캠페인을 계획하기 전에 인사이트를 수집하기 위해 모든 주요 캠페인 후 사후 검토를 실시해요." },
      { situation: "제품 출시 문제를 다룰 때", en: "A rushed post-mortem that focuses on blame rather than root causes fails to prevent future incidents.", ko: "근본 원인보다 책임에 집중하는 성급한 사후 검토는 미래 인시던트를 방지하는 데 실패해요." },
      { situation: "스타트업 실패 요인을 분석할 때", en: "Conducting an honest post-mortem after a failed fundraising round helped the founders refine their pitch strategy.", ko: "실패한 자금 조달 라운드 이후 솔직한 사후 검토를 수행하면서 창업자들이 피치 전략을 개선하는 데 도움이 됐어요." },
      { situation: "팀 회고 문화를 구축할 때", en: "Scheduling regular post-mortem sessions builds a culture of continuous learning and psychological safety.", ko: "정기적인 사후 검토 세션을 계획하면 지속적인 학습과 심리적 안전의 문화를 구축해요." }
    ],
    level: "800"
  },
  {
    id: 189,
    word: "bootstrapping",
    pronunciation: "ˈbuːt.stræp.ɪŋ",
    pos: "n.",
    meaning: "자기 자본으로 창업하기, 부트스트래핑",
    synonyms: ["self-funding", "organic growth funding", "self-financing"],
    examples: [
      { situation: "스타트업 자금 전략을 논의할 때", en: "Bootstrapping allowed the founder to maintain full ownership and avoid investor pressure during the early growth phase.", ko: "부트스트래핑 덕분에 창업자는 초기 성장 단계에서 완전한 소유권을 유지하고 투자자 압력을 피할 수 있었어요." },
      { situation: "창업 비용 관리를 설명할 때", en: "By bootstrapping for two years, the company demonstrated product-market fit before seeking external investment.", ko: "2년간 부트스트래핑함으로써 회사는 외부 투자를 구하기 전에 제품-시장 적합성을 입증했어요." },
      { situation: "투자자 없이 성장한 사례를 소개할 때", en: "The bootstrapped startup reached profitability within 18 months without taking a single dollar of outside funding.", ko: "부트스트랩한 스타트업은 외부 자금을 단 한 푼도 받지 않고 18개월 내에 수익성에 도달했어요." },
      { situation: "투자 대안을 검토할 때", en: "Bootstrapping requires disciplined cost management and a focus on generating revenue from day one.", ko: "부트스트래핑은 규율 있는 비용 관리와 첫날부터 매출 창출에 집중하는 것을 필요로 해요." },
      { situation: "기업가 정신을 가르칠 때", en: "Many successful companies, including some tech giants, started by bootstrapping before scaling with venture capital.", ko: "일부 기술 대기업을 포함한 많은 성공적인 기업들이 벤처 자본으로 확장하기 전에 부트스트래핑으로 시작했어요." },
      { situation: "현금 흐름을 관리할 때", en: "Bootstrapping forces entrepreneurs to be creative about customer acquisition and lean on organic growth channels.", ko: "부트스트래핑은 기업가들이 고객 확보에 창의적이 되고 유기적 성장 채널에 의존하도록 만들어요." },
      { situation: "사업 계획서를 작성할 때", en: "The business plan outlined a bootstrapping strategy for the first year, with a Series A fundraise planned for year two.", ko: "사업 계획서는 1년째 부트스트래핑 전략을 개요로 하고 2년째 시리즈 A 자금 조달을 계획했어요." },
      { situation: "창업 생태계를 비교할 때", en: "In markets with limited venture capital, bootstrapping is often the only viable path to building a sustainable business.", ko: "벤처 자본이 제한적인 시장에서 부트스트래핑은 종종 지속 가능한 사업을 구축하는 유일한 실행 가능한 경로예요." },
      { situation: "성장 전략을 재검토할 때", en: "After two failed fundraising attempts, management decided to return to bootstrapping and focus on profitability.", ko: "두 번의 실패한 자금 조달 시도 후 경영진은 부트스트래핑으로 돌아가 수익성에 집중하기로 결정했어요." },
      { situation: "자금 조달 라운드를 준비할 때", en: "Investors viewed the company bootstrapping history as proof of capital efficiency and founder resilience.", ko: "투자자들은 회사의 부트스트래핑 역사를 자본 효율성과 창업자 탄력성의 증거로 봤어요." }
    ],
    level: "800"
  },
  {
    id: 190,
    word: "market capitalization",
    pronunciation: "ˈmɑː.kɪt ˌkæp.ɪ.tʃuˈleɪ.ʃən",
    pos: "n.",
    meaning: "시가총액",
    synonyms: ["market cap", "equity value", "company market value"],
    examples: [
      { situation: "회사 규모를 비교할 때", en: "With a market capitalization of over one trillion dollars, the company joined the exclusive club of mega-cap stocks.", ko: "시가총액 1조 달러를 넘어서며 회사가 초대형주의 독점 클럽에 합류했어요." },
      { situation: "투자 등급을 분류할 때", en: "Institutional investors often categorize stocks by market capitalization into large-cap, mid-cap, and small-cap segments.", ko: "기관 투자자들은 종종 시가총액에 따라 주식을 대형주, 중형주, 소형주로 분류해요." },
      { situation: "인수 가격을 협상할 때", en: "The bid represented a 30 percent premium over the target company current market capitalization.", ko: "그 입찰은 피인수 기업의 현재 시가총액에 30%의 프리미엄을 더한 금액이었어요." },
      { situation: "기업 가치를 평가할 때", en: "Market capitalization is calculated by multiplying the current share price by the total number of outstanding shares.", ko: "시가총액은 현재 주가에 총 발행 주식 수를 곱하여 계산해요." },
      { situation: "지수 구성을 설명할 때", en: "Companies must meet minimum market capitalization requirements to be included in the S&P 500 index.", ko: "기업들은 S&P 500 지수에 포함되기 위해 최소 시가총액 요건을 충족해야 해요." },
      { situation: "주식 시장 동향을 분석할 때", en: "The technology sector now accounts for over 30 percent of total market capitalization in US equity markets.", ko: "기술 부문이 이제 미국 주식 시장 전체 시가총액의 30% 이상을 차지해요." },
      { situation: "IPO 성공을 평가할 때", en: "On its first day of trading, the company achieved a market capitalization of 15 billion dollars, exceeding analyst forecasts.", ko: "첫 거래일에 회사는 애널리스트 예상을 초과하는 150억 달러의 시가총액을 달성했어요." },
      { situation: "기업 전략을 수립할 때", en: "Growing market capitalization is often cited as a key objective in corporate strategy presentations to shareholders.", ko: "시가총액 성장은 주주들을 대상으로 하는 기업 전략 발표에서 핵심 목표로 자주 언급돼요." },
      { situation: "포트폴리오 다각화를 검토할 때", en: "Diversifying across different market capitalization tiers reduces portfolio concentration risk.", ko: "다양한 시가총액 계층에 걸쳐 다각화하면 포트폴리오 집중 위험이 줄어요." },
      { situation: "비교 가치 평가를 할 때", en: "The enterprise value-to-EBITDA multiple is often considered more meaningful than market capitalization for comparative analysis.", ko: "기업 가치 대 EBITDA 배수는 비교 분석에서 시가총액보다 더 의미 있는 것으로 종종 간주돼요." }
    ],
    level: "800"
  },
  {
    id: 191,
    word: "EBITDA",
    pronunciation: "iː.bɪt.dɑː",
    pos: "n.",
    meaning: "이자·세금·감가상각 차감 전 이익, EBITDA",
    synonyms: ["operating earnings", "adjusted earnings", "earnings before interest and taxes"],
    examples: [
      { situation: "기업 수익성을 비교할 때", en: "EBITDA is widely used to compare profitability between companies before the impact of financing and accounting decisions.", ko: "EBITDA는 금융 및 회계 결정의 영향 전에 기업 간 수익성을 비교하는 데 널리 사용돼요." },
      { situation: "M&A 가치 평가를 할 때", en: "The acquisition was priced at eight times EBITDA, which was within the expected range for the sector.", ko: "인수는 EBITDA의 8배로 가격이 책정됐으며 이는 해당 부문의 예상 범위 내였어요." },
      { situation: "대출 약정을 협의할 때", en: "The loan agreement requires total debt to not exceed four times EBITDA at any reporting period.", ko: "대출 계약은 모든 보고 기간에 총 부채가 EBITDA의 4배를 초과하지 않도록 요구해요." },
      { situation: "CFO 분기 보고에서", en: "EBITDA grew by 18 percent year-on-year, driven by cost efficiencies and higher revenue volume.", ko: "비용 효율성과 더 높은 매출 규모에 힘입어 EBITDA가 전년 대비 18% 성장했어요." },
      { situation: "투자자 설명회를 준비할 때", en: "Management highlighted adjusted EBITDA to exclude one-time restructuring charges and give a clearer view of operating performance.", ko: "경영진은 일회성 구조조정 비용을 제외하고 운영 성과의 명확한 뷰를 제공하기 위해 조정 EBITDA를 강조했어요." },
      { situation: "사업부 성과를 평가할 때", en: "Each business unit is evaluated on its EBITDA contribution to the overall group performance.", ko: "각 사업부는 전체 그룹 성과에 대한 EBITDA 기여도로 평가받아요." },
      { situation: "부채 재조정을 논의할 때", en: "Improving EBITDA through operational efficiency enabled the company to refinance its debt at more favorable terms.", ko: "운영 효율성을 통해 EBITDA를 개선하면서 회사가 더 유리한 조건으로 부채를 재융자할 수 있었어요." },
      { situation: "인수 후 통합 성과를 측정할 때", en: "Post-acquisition synergies were reflected in a significant increase in combined EBITDA within the first year.", ko: "인수 후 시너지는 첫해에 결합 EBITDA의 상당한 증가에 반영됐어요." },
      { situation: "기업 매각을 준비할 때", en: "Sellers typically present trailing twelve-month EBITDA as the primary financial metric to potential buyers.", ko: "매도자들은 일반적으로 잠재적 구매자에게 주요 재무 지표로 최근 12개월 EBITDA를 제시해요." },
      { situation: "재무 모델을 구축할 때", en: "Financial analysts build EBITDA bridge models to explain the year-over-year variance in operating performance.", ko: "재무 애널리스트들은 운영 성과의 전년 대비 차이를 설명하기 위해 EBITDA 브리지 모델을 구축해요." }
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
console.log('Batch 9 done: IDs 173,175,176,177,178,183,184,189,190,191 replaced.');
