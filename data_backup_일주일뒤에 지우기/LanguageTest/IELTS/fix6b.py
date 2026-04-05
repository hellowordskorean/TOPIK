import json

with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_6.json', encoding='utf-8') as f:
    data6 = json.load(f)

replacements_6 = {}

replacements_6["binding"] = [
  {"situation":"계약 조건을 협의할 때","en":"Both parties signed a binding agreement that clearly specified penalties for any failure to meet the agreed delivery schedule.","ko":"양측은 합의된 납기 일정을 준수하지 못할 경우의 위약금을 명확히 규정한 구속력 있는 계약서에 서명했어요."},
  {"situation":"국제 조약을 설명할 때","en":"The Paris Agreement is politically binding on its signatories, though enforcement mechanisms remain a subject of ongoing debate.","ko":"파리협정은 서명국들에게 정치적으로 구속력이 있지만, 이행 메커니즘은 여전히 지속적인 논쟁의 주제예요."},
  {"situation":"중재 결과를 설명할 때","en":"The arbitration panel issued a binding ruling that required the company to pay full compensation within ninety days.","ko":"중재 패널은 회사가 90일 이내에 전액 배상을 지급하도록 요구하는 구속력 있는 판결을 내렸어요."},
  {"situation":"기업 정책을 설명할 때","en":"The code of ethics is binding on all employees, from entry-level staff to board directors, without exception.","ko":"윤리 강령은 신입 직원부터 이사회 임원에 이르기까지 예외 없이 모든 직원에게 구속력이 있어요."},
  {"situation":"법적 효력을 설명할 때","en":"A verbal agreement may be legally binding under certain circumstances, but written contracts provide far greater protection for both parties.","ko":"구두 계약은 특정 상황에서 법적 구속력을 가질 수 있지만, 서면 계약이 양측 모두에게 훨씬 더 큰 보호를 제공해요."},
  {"situation":"규제 요건을 논의할 때","en":"The regulator issued binding guidelines that all financial institutions must incorporate into their anti-money-laundering procedures by year-end.","ko":"규제당국은 모든 금융 기관이 연말까지 자금세탁 방지 절차에 통합해야 하는 구속력 있는 지침을 발표했어요."},
  {"situation":"공모 입찰 조건을 설명할 때","en":"Once submitted, a tender offer becomes binding on the bidder for a specified period, preventing withdrawal without financial penalty.","ko":"제출된 입찰 제안은 지정된 기간 동안 입찰자에게 구속력을 가지며, 재정적 불이익 없이 철회할 수 없어요."},
  {"situation":"이사회 결의를 설명할 때","en":"A resolution passed at an extraordinary general meeting is binding on all shareholders, including those who voted against it.","ko":"임시 주주총회에서 통과된 결의는 반대표를 던진 주주를 포함하여 모든 주주에게 구속력이 있어요."},
  {"situation":"공급업체 계약을 검토할 때","en":"The procurement team ensured that all supplier contracts included binding confidentiality clauses to protect sensitive commercial information.","ko":"구매팀은 모든 공급업체 계약에 민감한 상업 정보를 보호하기 위한 구속력 있는 비밀유지 조항이 포함되도록 했어요."},
  {"situation":"소비자 보호 규정을 설명할 때","en":"Consumer protection law makes standard-form contracts binding only to the extent that the terms are fair and clearly communicated at the point of sale.","ko":"소비자 보호법은 표준 계약서가 판매 시점에 공정하고 명확하게 전달된 조건의 범위 내에서만 구속력을 갖도록 규정해요."}
]

replacements_6["comprehensive"] = [
  {"situation":"보험 상품을 설명할 때","en":"The company took out a comprehensive insurance policy that covered property damage, public liability, and business interruption under a single premium.","ko":"회사는 단일 보험료로 재산 피해, 공공 책임, 영업 중단을 모두 보장하는 포괄적인 보험 상품에 가입했어요."},
  {"situation":"정책 검토 보고서를 논의할 때","en":"The minister commissioned a comprehensive review of the healthcare system to identify inefficiencies and propose structural reforms.","ko":"장관은 비효율성을 파악하고 구조 개혁을 제안하기 위해 의료 시스템에 대한 포괄적인 검토를 의뢰했어요."},
  {"situation":"교육과정 개혁을 논의할 때","en":"The new curriculum offers a comprehensive foundation in STEM subjects while preserving space for the arts and physical education.","ko":"새 교육과정은 예술과 체육을 위한 공간을 유지하면서 STEM 과목에 대한 포괄적인 기반을 제공해요."},
  {"situation":"환경 규제를 설명할 때","en":"Environmentalists called for a comprehensive ban on single-use plastics rather than the piecemeal restrictions already in place.","ko":"환경론자들은 이미 시행 중인 부분적 규제보다는 일회용 플라스틱에 대한 포괄적인 금지를 촉구했어요."},
  {"situation":"실사 절차를 설명할 때","en":"Before completing the acquisition, the legal team conducted a comprehensive due diligence review covering financial, legal, and operational risks.","ko":"인수를 완료하기 전에 법무팀은 재무, 법적, 운영상 위험을 포괄하는 포괄적인 실사 검토를 실시했어요."},
  {"situation":"훈련 프로그램을 설명할 때","en":"New recruits undergo a comprehensive onboarding programme covering company culture, system access, and role-specific technical training.","ko":"신입사원들은 회사 문화, 시스템 접근권, 직무별 기술 교육을 포괄하는 종합적인 온보딩 프로그램을 이수해요."},
  {"situation":"리스크 관리 전략을 논의할 때","en":"A comprehensive risk management framework identifies potential threats at the strategic, operational, and project levels simultaneously.","ko":"포괄적인 리스크 관리 프레임워크는 전략적, 운영적, 프로젝트 수준의 잠재적 위협을 동시에 파악해요."},
  {"situation":"데이터 보안 정책을 설명할 때","en":"The IT department implemented a comprehensive cybersecurity policy addressing access controls, data encryption, and incident response procedures.","ko":"IT 부서는 접근 통제, 데이터 암호화, 사고 대응 절차를 다루는 포괄적인 사이버 보안 정책을 시행했어요."},
  {"situation":"투자자에게 보고할 때","en":"The annual report provided a comprehensive overview of the company's financial performance, strategic priorities, and sustainability commitments.","ko":"연간 보고서는 회사의 재무 성과, 전략적 우선순위, 지속 가능성 약속에 대한 포괄적인 개요를 제공했어요."},
  {"situation":"법안 내용을 설명할 때","en":"The proposed legislation takes a comprehensive approach to immigration reform, addressing border security, visa processing, and integration support simultaneously.","ko":"제안된 법안은 국경 보안, 비자 처리, 통합 지원을 동시에 다루는 포괄적인 이민 개혁 방안을 제시해요."}
]

replacements_6["confidential"] = [
  {"situation":"기밀 정보를 취급할 때","en":"All documents marked confidential must be stored in encrypted folders and may only be accessed by authorised personnel.","ko":"기밀로 표시된 모든 문서는 암호화된 폴더에 보관되어야 하며 승인된 직원만 접근할 수 있어요."},
  {"situation":"계약 협상을 논의할 때","en":"The terms of the settlement were kept strictly confidential, with both parties bound by a non-disclosure agreement.","ko":"합의 조건은 양측이 비밀유지 계약에 구속되어 철저히 기밀로 유지됐어요."},
  {"situation":"직원 성과 평가를 설명할 때","en":"Performance appraisal results are treated as strictly confidential and are shared only between the employee and their direct line manager.","ko":"성과 평가 결과는 엄격히 기밀로 처리되며 직원과 직속 관리자 사이에서만 공유돼요."},
  {"situation":"의료 기록 관리를 설명할 때","en":"Patient records are confidential by law, and any unauthorised disclosure can result in significant legal liability for the healthcare provider.","ko":"환자 기록은 법적으로 기밀이며, 무단 공개는 의료 제공자에게 상당한 법적 책임을 초래할 수 있어요."},
  {"situation":"법률 자문을 논의할 때","en":"Communications between a lawyer and their client are confidential under the principle of legal professional privilege.","ko":"변호사와 의뢰인 간의 소통은 법적 전문가 특권 원칙에 따라 기밀이에요."},
  {"situation":"내부 고발 제도를 설명할 때","en":"The company set up a confidential whistleblowing hotline that allowed employees to report misconduct without fear of retaliation.","ko":"회사는 직원들이 보복에 대한 두려움 없이 비위를 신고할 수 있는 기밀 내부 고발 핫라인을 설치했어요."},
  {"situation":"데이터 보호 정책을 설명할 때","en":"Under GDPR, businesses must treat customer personal data as confidential and obtain explicit consent before using it for marketing purposes.","ko":"GDPR에 따라 기업은 고객 개인 데이터를 기밀로 취급해야 하며 마케팅 목적으로 사용하기 전에 명시적 동의를 얻어야 해요."},
  {"situation":"M&A 거래를 논의할 때","en":"All information shared during the due diligence phase was confidential and could not be disclosed to third parties without written consent.","ko":"실사 단계에서 공유된 모든 정보는 기밀이었으며 서면 동의 없이 제3자에게 공개될 수 없었어요."},
  {"situation":"언론 보도를 다룰 때","en":"The spokesperson declined to comment on the leaked memo, stating only that internal personnel matters were confidential.","ko":"대변인은 유출된 메모에 대한 논평을 거부하며 내부 인사 문제는 기밀이라고만 밝혔어요."},
  {"situation":"신제품 개발을 논의할 때","en":"The R&D team worked under strict confidential protocols to prevent competitors from learning about the product launch before the official announcement.","ko":"R&D팀은 공식 발표 전에 경쟁사가 제품 출시에 대해 알지 못하도록 엄격한 기밀 프로토콜 하에 작업했어요."}
]

replacements_6["consistent"] = [
  {"situation":"브랜드 관리를 논의할 때","en":"Maintaining a consistent brand voice across all communication channels is essential for building long-term customer recognition and trust.","ko":"모든 커뮤니케이션 채널에서 일관된 브랜드 보이스를 유지하는 것은 장기적인 고객 인지도와 신뢰를 구축하는 데 필수적이에요."},
  {"situation":"성과 평가를 논의할 때","en":"Consistent performance over multiple quarters is a more reliable indicator of an employee's potential than a single exceptional result.","ko":"여러 분기에 걸친 일관된 성과는 단 한 번의 탁월한 결과보다 직원의 잠재력을 보여주는 더 신뢰할 수 있는 지표예요."},
  {"situation":"공급망 품질 관리를 논의할 때","en":"The manufacturer struggled to deliver consistent product quality after switching to cheaper raw materials sourced from a new supplier.","ko":"제조업체는 새 공급업체에서 조달한 저렴한 원자재로 전환한 후 일관된 제품 품질을 유지하는 데 어려움을 겪었어요."},
  {"situation":"법 집행의 공정성을 논의할 때","en":"Legal scholars argued that sentencing was not consistent across different jurisdictions, leading to inequitable outcomes for similar offences.","ko":"법학자들은 양형이 관할 구역마다 일관되지 않아 유사한 범죄에 대해 불공평한 결과가 나온다고 주장했어요."},
  {"situation":"학교 교육 수준을 논의할 때","en":"A centralised curriculum helps ensure that educational standards remain consistent across schools in wealthy and disadvantaged districts alike.","ko":"중앙화된 교육과정은 부유한 지역과 취약한 지역 모두의 학교에서 교육 수준이 일관되게 유지되도록 돕는 데 유용해요."},
  {"situation":"금융 보고를 논의할 때","en":"Auditors noted that the company's accounting treatment had not been consistent year on year, making it difficult to compare performance across periods.","ko":"감사인들은 회사의 회계 처리가 매년 일관되지 않아 기간별 성과를 비교하기 어렵다고 지적했어요."},
  {"situation":"고객 서비스 표준을 논의할 때","en":"Franchises are built on the premise that customers receive a consistent experience regardless of which location they visit.","ko":"프랜차이즈는 고객이 어떤 지점을 방문하든 일관된 경험을 받는다는 전제 위에 구축돼요."},
  {"situation":"과학 연구 방법론을 논의할 때","en":"The study's findings were credible because they were consistent with results from three independent replications conducted in different laboratories.","ko":"이 연구의 결과는 서로 다른 실험실에서 수행된 세 번의 독립적인 재현 결과와 일치하여 신뢰할 수 있었어요."},
  {"situation":"팀 관리를 논의할 때","en":"A consistent management style builds trust within teams because employees know what to expect and how decisions will be made.","ko":"일관된 관리 스타일은 직원들이 무엇을 기대하고 어떻게 결정이 내려질지 알기 때문에 팀 내 신뢰를 구축해요."},
  {"situation":"정책 시행을 논의할 때","en":"For regulations to be effective, enforcement must be consistent -- selective application undermines the rule of law and creates unfair competitive advantages.","ko":"규제가 효과적이려면 집행이 일관적이어야 하며, 선택적 적용은 법치주의를 훼손하고 불공정한 경쟁 우위를 만들어요."}
]

replacements_6["decisive"] = [
  {"situation":"위기 리더십을 논의할 때","en":"The CEO's decisive response to the product recall -- pulling the item from shelves within 24 hours -- helped preserve the company's reputation.","ko":"제품 리콜에 대한 CEO의 단호한 대응은 회사의 명성을 지키는 데 도움이 됐어요."},
  {"situation":"군사 전략을 논의할 때","en":"Historians credit the general's decisive action at the critical moment with turning the tide of the entire campaign.","ko":"역사학자들은 결정적인 순간에 내린 장군의 단호한 행동이 전체 전황을 바꾸는 데 기여했다고 평가해요."},
  {"situation":"정책 결정을 논의할 때","en":"Voters grew frustrated with an administration they perceived as indecisive, demanding more decisive leadership on economic policy.","ko":"유권자들은 우유부단하다고 느끼는 행정부에 좌절감을 느끼며 경제 정책에 대한 더 단호한 리더십을 요구했어요."},
  {"situation":"스포츠 경기를 분석할 때","en":"The manager's decisive substitution in the second half proved to be the turning point, completely changing the team's attacking dynamic.","ko":"후반전에 내린 감독의 단호한 선수 교체는 팀의 공격 역동성을 완전히 바꾸는 전환점이 됐어요."},
  {"situation":"비즈니스 협상을 논의할 때","en":"In fast-moving markets, the ability to make decisive commitments quickly can be a significant competitive advantage over slower-moving rivals.","ko":"빠르게 움직이는 시장에서 신속하게 단호한 결정을 내리는 능력은 느린 경쟁사에 비해 상당한 경쟁 우위가 될 수 있어요."},
  {"situation":"역사적 사건을 분석할 때","en":"The decisive victory at the Battle of Midway fundamentally shifted the balance of naval power in the Pacific theatre.","ko":"미드웨이 해전에서의 결정적인 승리는 태평양 전선에서의 해군력 균형을 근본적으로 변화시켰어요."},
  {"situation":"의료 결정을 논의할 때","en":"In emergency medicine, doctors must be decisive under pressure, making life-or-death judgements with limited information and minimal time.","ko":"응급 의학에서 의사들은 압박 속에서 단호해야 하며, 제한된 정보와 최소한의 시간으로 생사의 판단을 내려야 해요."},
  {"situation":"경영 스타일을 논의할 때","en":"Her decisive management style earned both admiration and criticism -- some valued her clarity, while others felt excluded from decision-making.","ko":"그녀의 단호한 경영 스타일은 찬사와 비판을 동시에 받았으며, 일부는 그녀의 명확함을 높이 샀지만 다른 이들은 의사결정에서 소외감을 느꼈어요."},
  {"situation":"선거 결과를 분석할 때","en":"The incumbent won a decisive majority, securing over sixty percent of the popular vote and carrying all but two states.","ko":"현직 대통령은 전체 득표율의 60% 이상을 얻고 두 개 주를 제외한 모든 주를 차지하는 결정적인 다수를 확보했어요."},
  {"situation":"과학적 증거를 논의할 때","en":"The clinical trial provided decisive evidence that the drug was both safe and effective, clearing the path for regulatory approval.","ko":"임상시험은 약물이 안전하고 효과적이라는 결정적인 증거를 제공하여 규제 승인의 길을 열었어요."}
]

replacements_6["dedicated"] = [
  {"situation":"직원 헌신을 칭찬할 때","en":"The project was completed ahead of schedule largely thanks to a dedicated team that worked through weekends without complaint.","ko":"프로젝트가 예정보다 일찍 완료된 것은 주말에도 불평 없이 일한 헌신적인 팀 덕분이에요."},
  {"situation":"시설 전용 용도를 설명할 때","en":"The hospital opened a dedicated cancer treatment centre equipped with the latest radiation therapy technology.","ko":"병원은 최신 방사선 치료 기술을 갖춘 전용 암 치료 센터를 개설했어요."},
  {"situation":"사회적 기여를 논의할 때","en":"She spent thirty years as a dedicated teacher in under-resourced schools, refusing higher-paying opportunities in the private sector.","ko":"그녀는 민간 부문의 더 높은 급여 기회를 거절하며 자원이 부족한 학교에서 30년간 헌신적인 교사로 일했어요."},
  {"situation":"IT 인프라를 설명할 때","en":"For high-volume transaction processing, the bank maintains a dedicated server environment separate from its general-purpose systems.","ko":"대용량 거래 처리를 위해 은행은 범용 시스템과 분리된 전용 서버 환경을 유지해요."},
  {"situation":"연구 자원 배분을 논의할 때","en":"The university established a dedicated research institute focused exclusively on climate adaptation strategies for coastal communities.","ko":"대학교는 해안 지역 사회의 기후 적응 전략에만 집중하는 전용 연구소를 설립했어요."},
  {"situation":"고객 서비스 구조를 설명할 때","en":"Enterprise clients are assigned a dedicated account manager who serves as their primary point of contact for all service-related issues.","ko":"기업 고객에게는 모든 서비스 관련 문제의 주요 연락 창구 역할을 하는 전담 계정 관리자가 배정돼요."},
  {"situation":"직원 표창을 논의할 때","en":"The award recognised employees who had shown exceptional dedication to community service outside their normal working hours.","ko":"이 상은 정규 근무 시간 외에도 지역 사회 봉사에 탁월한 헌신을 보인 직원들을 표창하기 위해 만들어졌어요."},
  {"situation":"소프트웨어 팀 구조를 설명할 때","en":"Each product line has a dedicated development team responsible for maintaining code quality, fixing bugs, and shipping new features.","ko":"각 제품 라인에는 코드 품질 유지, 버그 수정, 새 기능 출시를 담당하는 전담 개발팀이 있어요."},
  {"situation":"공공 서비스 전달을 논의할 때","en":"The government created a dedicated task force to coordinate the national response to the growing housing affordability crisis.","ko":"정부는 점점 심각해지는 주택 가격 적정성 위기에 대한 국가적 대응을 조율하기 위해 전담 태스크포스를 구성했어요."},
  {"situation":"외교관의 역할을 논의할 때","en":"A dedicated diplomat with decades of experience, she was credited with brokering the peace agreement that ended a fifteen-year regional conflict.","ko":"수십 년의 경험을 가진 헌신적인 외교관인 그녀는 15년간의 지역 분쟁을 종식시킨 평화 협정을 중재한 공로를 인정받았어요."}
]

replacements_6["deliberate"] = [
  {"situation":"회사의 의도적 전략을 논의할 때","en":"The company made a deliberate decision to exit the mass-market segment and reposition itself as a premium brand.","ko":"회사는 대중 시장 세그먼트에서 철수하고 프리미엄 브랜드로 재포지셔닝하는 의도적인 결정을 내렸어요."},
  {"situation":"법적 의도를 분석할 때","en":"The prosecution argued that the destruction of documents was deliberate and constituted an attempt to obstruct justice.","ko":"검찰은 문서 폐기가 고의적이었으며 사법 방해 시도에 해당한다고 주장했어요."},
  {"situation":"설계 선택을 설명할 때","en":"The architect made a deliberate choice to use exposed concrete, embracing its industrial aesthetic rather than concealing it behind plasterwork.","ko":"건축가는 콘크리트를 석고로 가리는 대신 산업적 미학을 살리는 의도적인 선택으로 노출 콘크리트를 사용했어요."},
  {"situation":"커뮤니케이션 전략을 논의할 때","en":"The politician's vague answer was widely seen as deliberate -- a calculated move to avoid committing to a position before the election.","ko":"그 정치인의 모호한 답변은 선거 전에 입장을 밝히지 않으려는 계산된 행동으로 의도적인 것으로 널리 인식됐어요."},
  {"situation":"교육 방법론을 논의할 때","en":"Deliberate practice, rather than mere repetition, is what separates elite performers from average ones in any skill domain.","ko":"단순한 반복이 아닌 의도적 연습이 어떤 기술 분야에서든 탁월한 수행자와 평범한 수행자를 구분하는 요소예요."},
  {"situation":"범죄 수사를 논의할 때","en":"Investigators concluded that the fire was deliberate after finding evidence of multiple ignition points and accelerant residues throughout the building.","ko":"수사관들은 건물 전체에서 여러 발화 지점과 촉진제 잔류물 증거를 발견한 후 화재가 의도적이었다는 결론을 내렸어요."},
  {"situation":"관리자의 의사결정 방식을 논의할 때","en":"Her deliberate, methodical approach to decision-making meant that she rarely acted on impulse and almost never had to reverse course.","ko":"의사결정에 대한 그녀의 신중하고 체계적인 접근 방식은 충동적으로 행동하는 일이 거의 없었으며 방향을 바꿔야 할 경우도 거의 없었음을 의미해요."},
  {"situation":"마케팅 전략을 분석할 때","en":"The brand's deliberate use of minimalist packaging was intended to signal premium quality and environmental responsibility simultaneously.","ko":"브랜드의 의도적인 미니멀리스트 포장 사용은 프리미엄 품질과 환경적 책임을 동시에 나타내려는 것이었어요."},
  {"situation":"스포츠 코칭을 논의할 때","en":"The coach stressed that improvement required deliberate, focused effort -- simply playing more games would not sharpen the skills that needed attention.","ko":"코치는 향상을 위해 의도적이고 집중된 노력이 필요하다고 강조했으며, 단순히 경기를 더 많이 하는 것으로는 주의가 필요한 기술이 향상되지 않는다고 했어요."},
  {"situation":"외교적 조치를 분석할 때","en":"The ambassador's deliberate public silence on the issue was interpreted as tacit disapproval of the government's handling of the crisis.","ko":"그 문제에 대한 대사의 의도적인 공개적 침묵은 정부의 위기 처리에 대한 암묵적인 반대로 해석됐어요."}
]

count = 0
for w in data6['words']:
    if w['word'] in replacements_6:
        w['examples'] = replacements_6[w['word']]
        count += 1

print(f"Updated {count} words")
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_6.json', 'w', encoding='utf-8') as f:
    json.dump(data6, f, ensure_ascii=False, indent=2)
print("Saved ielts_6.json batch 2")
