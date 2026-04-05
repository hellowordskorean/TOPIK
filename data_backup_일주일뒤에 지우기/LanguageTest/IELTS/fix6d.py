import json

with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_6.json', encoding='utf-8') as f:
    data6 = json.load(f)

R = {}

R["preliminary"] = [
  {"situation":"조사 초기 단계를 설명할 때","en":"Preliminary findings from the clinical trial suggest the drug is both safe and effective, though full results will not be available until next year.","ko":"임상시험의 예비 결과는 약물이 안전하고 효과적임을 시사하지만, 최종 결과는 내년이 되어야 확인될 거예요."},
  {"situation":"법원 절차를 설명할 때","en":"The judge scheduled a preliminary hearing to determine whether sufficient evidence existed to proceed to a full trial.","ko":"판사는 완전한 재판으로 진행할 충분한 증거가 있는지 판단하기 위해 예비 청문회를 일정에 넣었어요."},
  {"situation":"건축 설계 단계를 설명할 때","en":"The preliminary design was shared with the planning authority to receive early feedback before the full planning application was submitted.","ko":"전체 계획 신청서를 제출하기 전에 초기 피드백을 받기 위해 예비 설계안이 계획 당국과 공유됐어요."},
  {"situation":"협상 초기 단계를 설명할 때","en":"The two companies held preliminary discussions to explore whether a merger was feasible before commissioning formal due diligence.","ko":"두 회사는 공식 실사를 의뢰하기 전에 합병이 가능한지 탐색하기 위해 예비 논의를 가졌어요."},
  {"situation":"학술 연구를 설명할 때","en":"The preliminary analysis of survey data pointed to a strong correlation between sleep deprivation and reduced cognitive performance.","ko":"설문 데이터의 예비 분석은 수면 부족과 인지 성능 저하 사이의 강한 상관관계를 보여줬어요."},
  {"situation":"스포츠 경기를 설명할 때","en":"Eight teams are eliminated in the preliminary rounds before the main knockout stage begins, reducing the field from thirty-two to twenty-four.","ko":"32개 팀에서 24개 팀으로 줄이며 메인 토너먼트 단계가 시작되기 전에 예선전에서 여덟 팀이 탈락해요."},
  {"situation":"환경 영향 평가를 설명할 때","en":"A preliminary environmental assessment was completed to identify potential risks before the full impact study was commissioned.","ko":"완전한 영향 연구가 의뢰되기 전에 잠재적 위험을 파악하기 위해 예비 환경 평가가 완료됐어요."},
  {"situation":"회계 결과를 설명할 때","en":"The company released preliminary annual results showing a 12% increase in revenue, with full audited accounts to follow within six weeks.","ko":"회사는 매출이 12% 증가했음을 보여주는 예비 연간 실적을 발표했으며, 완전한 감사 계정은 6주 이내에 발표될 예정이에요."},
  {"situation":"의료 검진을 설명할 때","en":"A preliminary health screening identified elevated blood pressure in several employees, who were referred to occupational health for further evaluation.","ko":"예비 건강 검진에서 일부 직원들의 혈압이 높게 나와 추가 평가를 위해 산업보건팀에 의뢰됐어요."},
  {"situation":"법안 심의를 설명할 때","en":"The bill underwent a preliminary review by the constitutional committee before being scheduled for its first reading in the full parliament.","ko":"법안은 전체 의회에서 1독회 일정이 잡히기 전에 헌법위원회의 예비 검토를 거쳤어요."}
]

R["quarterly"] = [
  {"situation":"재무 보고를 설명할 때","en":"Listed companies are required to publish quarterly earnings reports so that shareholders and analysts can track financial performance throughout the year.","ko":"상장 기업들은 주주와 분석가들이 연간 재무 성과를 추적할 수 있도록 분기별 수익 보고서를 발행해야 해요."},
  {"situation":"성과 검토를 설명할 때","en":"The team holds quarterly reviews to assess progress against annual targets and adjust priorities based on changing market conditions.","ko":"팀은 연간 목표 대비 진행 상황을 평가하고 변화하는 시장 상황에 따라 우선순위를 조정하기 위해 분기별 검토를 실시해요."},
  {"situation":"세금 납부를 설명할 때","en":"Self-employed individuals must make quarterly tax payments to avoid penalties for underpayment at the end of the fiscal year.","ko":"자영업자들은 회계연도 말에 과소 납부에 대한 벌금을 피하기 위해 분기별 세금 납부를 해야 해요."},
  {"situation":"투자 포트폴리오 관리를 설명할 때","en":"The fund manager conducts quarterly rebalancing to ensure the portfolio's asset allocation remains aligned with the client's risk profile and investment objectives.","ko":"펀드 매니저는 포트폴리오의 자산 배분이 고객의 위험 프로필과 투자 목표에 일치하도록 분기별 재조정을 실시해요."},
  {"situation":"공급망 감사를 설명할 때","en":"Quarterly supplier audits enable the procurement team to identify compliance issues early and take corrective action before they escalate.","ko":"분기별 공급업체 감사는 구매팀이 규정 준수 문제를 조기에 파악하고 악화되기 전에 시정 조치를 취할 수 있게 해요."},
  {"situation":"지불 일정을 설명할 때","en":"The lease agreement specifies quarterly rental payments, due on the first business day of January, April, July, and October.","ko":"임대 계약은 1월, 4월, 7월, 10월의 첫 번째 영업일에 만기가 되는 분기별 임대료 납부를 명시해요."},
  {"situation":"규제 보고를 설명할 때","en":"Financial institutions must file quarterly liquidity reports with the central bank to demonstrate compliance with minimum reserve requirements.","ko":"금융 기관들은 최소 준비금 요건에 대한 규정 준수를 증명하기 위해 중앙은행에 분기별 유동성 보고서를 제출해야 해요."},
  {"situation":"마케팅 예산을 설명할 때","en":"The marketing department receives its budget on a quarterly basis, with unspent funds forfeited rather than carried over to the next period.","ko":"마케팅 부서는 분기별로 예산을 받으며, 미사용 자금은 다음 기간으로 이월되지 않고 반환돼요."},
  {"situation":"고객 만족도 조사를 설명할 때","en":"The company conducts quarterly customer satisfaction surveys to monitor service quality and respond promptly to emerging issues.","ko":"회사는 서비스 품질을 모니터링하고 새로운 문제에 신속하게 대응하기 위해 분기별 고객 만족도 조사를 실시해요."},
  {"situation":"이사회 보고를 설명할 때","en":"The CEO presents a quarterly business update to the board, covering revenue, operational risks, and strategic progress against the annual plan.","ko":"CEO는 연간 계획 대비 수익, 운영 위험, 전략적 진행 상황을 다루는 분기별 사업 업데이트를 이사회에 발표해요."}
]

R["renewable"] = [
  {"situation":"에너지 정책을 논의할 때","en":"The government pledged that renewable energy would account for seventy percent of the national electricity grid by 2035, up from thirty percent today.","ko":"정부는 재생 에너지가 오늘날 30%에서 2035년까지 국가 전력망의 70%를 차지할 것이라고 약속했어요."},
  {"situation":"기업 지속 가능성을 논의할 때","en":"The factory completed its transition to renewable electricity by installing a combination of rooftop solar panels and a long-term wind power purchase agreement.","ko":"공장은 지붕 태양광 패널과 장기 풍력 발전 구매 계약을 결합하여 재생 에너지 전력으로의 전환을 완료했어요."},
  {"situation":"투자 트렌드를 논의할 때","en":"Global investment in renewable energy surpassed fossil fuel investment for the first time in 2023, reflecting a fundamental shift in capital allocation priorities.","ko":"재생 에너지에 대한 전 세계 투자는 2023년 처음으로 화석 연료 투자를 초과했으며, 이는 자본 배분 우선순위의 근본적인 변화를 반영해요."},
  {"situation":"환경 논쟁을 논의할 때","en":"Critics of renewable energy point to the intermittency problem -- solar and wind generate power inconsistently, requiring expensive grid-scale storage solutions.","ko":"재생 에너지 비평가들은 간헐성 문제를 지적하는데, 태양광과 풍력은 불규칙적으로 전력을 생성하여 비용이 많이 드는 그리드 규모 저장 솔루션이 필요해요."},
  {"situation":"개발도상국 에너지를 논의할 때","en":"In remote communities without grid access, small-scale renewable installations offer a cost-effective alternative to diesel generators that require imported fuel.","ko":"전력망 접근이 없는 외딴 지역 사회에서 소규모 재생 에너지 시설은 수입 연료가 필요한 디젤 발전기에 대한 비용 효율적인 대안을 제공해요."},
  {"situation":"고용 창출을 논의할 때","en":"The renewable energy sector has become one of the fastest-growing sources of new employment in engineering, construction, and maintenance across the region.","ko":"재생 에너지 부문은 이 지역 전반에 걸쳐 엔지니어링, 건설, 유지보수 분야에서 가장 빠르게 성장하는 새로운 고용 원천 중 하나가 됐어요."},
  {"situation":"기후 목표를 논의할 때","en":"Meeting net-zero targets by 2050 will require an unprecedented acceleration in the deployment of renewable power generation capacity worldwide.","ko":"2050년까지 순제로 목표를 달성하려면 전 세계적으로 재생 에너지 발전 용량 배치를 전례 없이 가속화해야 할 거예요."},
  {"situation":"에너지 안보를 논의할 때","en":"Switching to domestically generated renewable energy reduces dependence on imported fossil fuels and shields the economy from global price shocks.","ko":"국내에서 생산된 재생 에너지로 전환하면 수입 화석 연료에 대한 의존도가 줄고 경제가 글로벌 가격 충격으로부터 보호돼요."},
  {"situation":"계약 종류를 설명할 때","en":"The agreement is structured as a renewable annual contract, giving both parties the option to renegotiate terms each year rather than being locked into fixed long-term conditions.","ko":"계약은 갱신 가능한 연간 계약으로 구성되어 있어 양측이 고정된 장기 조건에 묶이지 않고 매년 조건을 재협상할 수 있는 옵션을 부여해요."},
  {"situation":"교육 보조금을 설명할 때","en":"The scholarship is renewable annually provided the recipient maintains a grade point average above a specified threshold and remains enrolled full-time.","ko":"장학금은 수혜자가 지정된 임계값 이상의 학점 평균을 유지하고 전일제로 등록된 상태를 유지하는 한 매년 갱신 가능해요."}
]

R["scalable"] = [
  {"situation":"스타트업 비즈니스 모델을 논의할 때","en":"Investors were attracted to the startup precisely because its software-as-a-service model was highly scalable, requiring no additional infrastructure costs as user numbers grew.","ko":"투자자들은 사용자 수가 증가해도 추가 인프라 비용이 필요 없는 고도로 확장 가능한 SaaS 모델 때문에 스타트업에 끌렸어요."},
  {"situation":"클라우드 인프라를 설명할 때","en":"Cloud computing allows organisations to deploy scalable infrastructure that can be rapidly expanded during peak demand and scaled back during quieter periods.","ko":"클라우드 컴퓨팅을 통해 조직은 최대 수요 시 신속하게 확장하고 조용한 기간에 축소할 수 있는 확장 가능한 인프라를 배치할 수 있어요."},
  {"situation":"제조 공정을 설명할 때","en":"Before committing to full production, the team ran a pilot to confirm that the manufacturing process was genuinely scalable beyond the controlled laboratory setting.","ko":"전면 생산에 착수하기 전에 팀은 제조 공정이 통제된 실험실 환경을 넘어 진정으로 확장 가능한지 확인하기 위한 파일럿을 실시했어요."},
  {"situation":"사회 프로그램을 논의할 때","en":"The pilot scheme proved highly effective in the trial city, but policymakers questioned whether it was scalable to the national level given funding constraints.","ko":"파일럿 계획은 시범 도시에서 매우 효과적인 것으로 증명됐지만, 정책 입안자들은 자금 제약을 감안할 때 국가 차원으로 확장 가능한지에 의문을 제기했어요."},
  {"situation":"교육 기술을 논의할 때","en":"Online learning platforms are potentially scalable to millions of students simultaneously, which is why they attract significant venture capital investment.","ko":"온라인 학습 플랫폼은 수백만 명의 학생들에게 동시에 확장 가능하며, 이것이 상당한 벤처 캐피털 투자를 유치하는 이유예요."},
  {"situation":"의료 개입을 논의할 때","en":"Community health workers have shown impressive results in rural areas, but the model may not be scalable without substantial investment in training and supervision.","ko":"지역 보건 요원들은 농촌 지역에서 인상적인 결과를 보여줬지만, 교육과 감독에 상당한 투자 없이는 모델이 확장 가능하지 않을 수 있어요."},
  {"situation":"IT 솔루션을 설명할 때","en":"The engineering team designed the database architecture to be inherently scalable, ensuring it could handle ten times the current transaction volume without redesign.","ko":"엔지니어링 팀은 재설계 없이 현재 거래량의 10배를 처리할 수 있도록 본질적으로 확장 가능한 데이터베이스 아키텍처를 설계했어요."},
  {"situation":"재생 에너지 배치를 논의할 때","en":"Modular nuclear reactor designs aim to provide a scalable low-carbon power source that can be deployed incrementally as demand grows.","ko":"모듈형 원자로 설계는 수요 증가에 따라 점진적으로 배치할 수 있는 확장 가능한 저탄소 전력 공급원을 제공하는 것을 목표로 해요."},
  {"situation":"프랜차이즈 모델을 설명할 때","en":"The franchise model proved remarkably scalable; the brand expanded from a single cafe to over five hundred outlets in twelve countries within a decade.","ko":"프랜차이즈 모델은 놀랍도록 확장 가능한 것으로 증명됐으며, 브랜드는 10년 만에 단일 카페에서 12개국에 500개 이상의 매장으로 확장됐어요."},
  {"situation":"농업 기술을 논의할 때","en":"The irrigation technology works well in controlled trials, but farmers question whether it is truly scalable across the diverse terrain and water availability of the entire region.","ko":"관개 기술은 통제된 시험에서 잘 작동하지만, 농부들은 전체 지역의 다양한 지형과 용수 가용성에 걸쳐 진정으로 확장 가능한지 의문을 제기해요."}
]

R["substantial"] = [
  {"situation":"재정적 변화를 설명할 때","en":"The acquisition required a substantial capital outlay, but the board was convinced that the long-term returns would justify the initial investment.","ko":"인수에는 상당한 자본 지출이 필요했지만, 이사회는 장기적인 수익이 초기 투자를 정당화할 것이라고 확신했어요."},
  {"situation":"법적 피해를 설명할 때","en":"The court awarded substantial damages to the claimant after finding that the defendant's negligence had caused lasting harm to her professional reputation.","ko":"법원은 피고의 과실이 그녀의 직업적 명성에 지속적인 피해를 입혔다는 것을 발견한 후 청구인에게 상당한 손해배상을 판결했어요."},
  {"situation":"연구 결과를 설명할 때","en":"The meta-analysis found substantial evidence across forty separate studies that regular aerobic exercise significantly reduces the risk of cardiovascular disease.","ko":"메타 분석은 40개의 별도 연구에 걸쳐 규칙적인 유산소 운동이 심혈관 질환의 위험을 크게 줄인다는 상당한 증거를 발견했어요."},
  {"situation":"정치적 지지를 설명할 때","en":"The reform bill passed with substantial cross-party support, signalling a rare moment of consensus on an issue that had previously divided the legislature.","ko":"개혁 법안은 상당한 초당적 지지를 받아 통과됐으며, 이는 이전에 입법부를 분열시켰던 문제에 대한 드문 합의의 순간을 알렸어요."},
  {"situation":"환경 변화를 설명할 때","en":"Scientists have documented substantial declines in Arctic sea ice extent over the past four decades, with the rate of loss accelerating since the 1990s.","ko":"과학자들은 지난 40년 동안 북극 해빙 범위의 상당한 감소를 기록했으며, 손실 속도는 1990년대 이후 가속화됐어요."},
  {"situation":"임금 격차를 설명할 때","en":"Despite recent improvements, a substantial gender pay gap persists in many sectors, with women earning on average fifteen percent less than their male counterparts.","ko":"최근의 개선에도 불구하고, 여성이 남성 동료에 비해 평균 15% 적게 버는 등 많은 분야에서 상당한 성별 임금 격차가 지속되고 있어요."},
  {"situation":"교육 성과를 설명할 때","en":"Children who attended high-quality early childhood education programmes showed substantial improvements in literacy and numeracy scores compared to those who did not.","ko":"고품질 유아 교육 프로그램에 참석한 아이들은 그렇지 않은 아이들에 비해 문해력과 수리력 점수에서 상당한 향상을 보였어요."},
  {"situation":"기업 성장을 설명할 때","en":"The company achieved substantial revenue growth in its Asian operations, which now represent over a third of global sales compared to less than ten percent five years ago.","ko":"회사는 아시아 사업에서 상당한 매출 성장을 달성했으며, 이제 아시아 사업은 5년 전 10% 미만에서 글로벌 매출의 3분의 1 이상을 차지해요."},
  {"situation":"공중 보건 영향을 설명할 때","en":"The smoking ban in public places produced substantial health benefits, with hospital admissions for heart attacks falling by nearly fifteen percent within a year.","ko":"공공장소 흡연 금지는 상당한 건강상 이점을 가져왔으며, 심장 발작으로 인한 병원 입원이 1년 이내에 거의 15% 감소했어요."},
  {"situation":"주택 위기를 설명할 때","en":"A substantial shortfall in affordable housing supply relative to demand has pushed rents to historic highs in major urban centres across the country.","ko":"수요 대비 저렴한 주택 공급의 상당한 부족이 전국 주요 도심의 임대료를 역사적 최고치로 끌어올렸어요."}
]

R["sustainable"] = [
  {"situation":"환경 비즈니스를 논의할 때","en":"The company redesigned its packaging to reduce plastic use by eighty percent, making its supply chain significantly more sustainable and cutting long-term costs.","ko":"회사는 포장을 재설계하여 플라스틱 사용을 80% 줄였으며, 공급망을 크게 더 지속 가능하게 만들고 장기 비용을 절감했어요."},
  {"situation":"농업 실천을 논의할 때","en":"Sustainable farming methods that maintain soil health and minimise chemical inputs can deliver comparable yields to intensive agriculture over longer time horizons.","ko":"토양 건강을 유지하고 화학 투입물을 최소화하는 지속 가능한 농업 방법은 더 긴 시간 지평에 걸쳐 집약적 농업과 비교 가능한 수확량을 제공할 수 있어요."},
  {"situation":"도시 개발을 논의할 때","en":"Critics questioned whether the city's rapid expansion was truly sustainable, pointing to rising water scarcity, traffic congestion, and urban heat island effects.","ko":"비평가들은 증가하는 물 부족, 교통 혼잡, 도시 열섬 효과를 지적하며 도시의 빠른 확장이 진정으로 지속 가능한지에 의문을 제기했어요."},
  {"situation":"경제 성장 모델을 논의할 때","en":"Some economists argue that perpetual GDP growth is not sustainable on a finite planet and that new measures of wellbeing are needed to guide policy.","ko":"일부 경제학자들은 유한한 지구에서 영구적인 GDP 성장이 지속 가능하지 않으며 정책을 안내하기 위한 새로운 복지 측정 지표가 필요하다고 주장해요."},
  {"situation":"공중 보건 전략을 논의할 때","en":"A sustainable healthcare system must invest in preventive medicine, as treatment-focused models become financially unmanageable as populations age.","ko":"지속 가능한 의료 시스템은 예방 의학에 투자해야 하는데, 치료 중심 모델은 인구가 고령화됨에 따라 재정적으로 감당할 수 없게 되기 때문이에요."},
  {"situation":"국제 개발을 논의할 때","en":"The UN's Sustainable Development Goals represent an ambitious attempt to co-ordinate global action on poverty, inequality, and climate change simultaneously.","ko":"유엔의 지속 가능한 개발 목표는 빈곤, 불평등, 기후 변화에 대한 전 세계적 행동을 동시에 조율하려는 야심찬 시도를 나타내요."},
  {"situation":"패션 산업을 논의할 때","en":"Consumer demand for sustainable fashion is rising, prompting major brands to audit their supply chains for labour abuses and excessive water consumption.","ko":"지속 가능한 패션에 대한 소비자 수요가 증가함에 따라 주요 브랜드들이 노동 착취와 과도한 물 소비를 위해 공급망을 감사하도록 촉구받고 있어요."},
  {"situation":"에너지 전환을 논의할 때","en":"Transitioning to a sustainable energy system requires massive upfront investment in renewable infrastructure, but the long-run savings in fuel costs are considerable.","ko":"지속 가능한 에너지 시스템으로의 전환은 재생 에너지 인프라에 대한 대규모 초기 투자가 필요하지만, 연료 비용의 장기적인 절감은 상당해요."},
  {"situation":"어업 관리를 논의할 때","en":"Sustainable fisheries management requires strict catch limits and enforcement mechanisms to prevent the collapse of marine ecosystems that millions depend on for food.","ko":"지속 가능한 어업 관리는 수백만 명이 식량으로 의존하는 해양 생태계의 붕괴를 방지하기 위한 엄격한 어획 제한과 집행 메커니즘이 필요해요."},
  {"situation":"투자 전략을 논의할 때","en":"ESG investors argue that sustainable business practices reduce long-term risk and deliver superior returns compared to companies that ignore environmental and social factors.","ko":"ESG 투자자들은 지속 가능한 비즈니스 관행이 장기적 위험을 줄이고 환경 및 사회적 요인을 무시하는 기업에 비해 우수한 수익을 제공한다고 주장해요."}
]

R["uncertain"] = [
  {"situation":"경제 전망을 논의할 때","en":"The central bank adopted a cautious stance in an uncertain macroeconomic environment, holding interest rates steady while signalling readiness to act if conditions deteriorated.","ko":"중앙은행은 불확실한 거시경제 환경에서 신중한 입장을 취했으며, 금리를 유지하면서 상황이 악화되면 행동할 준비가 되어 있음을 신호로 보냈어요."},
  {"situation":"투자 결정을 논의할 때","en":"Investors are reluctant to commit capital in an uncertain regulatory environment, preferring to wait for greater policy clarity before expanding operations.","ko":"투자자들은 불확실한 규제 환경에서 자본을 투자하기를 꺼리며, 운영을 확장하기 전에 더 명확한 정책을 기다리는 것을 선호해요."},
  {"situation":"과학적 연구를 논의할 때","en":"The long-term health effects of the compound remain uncertain, and researchers have called for further longitudinal studies before any policy recommendations can be made.","ko":"화합물의 장기 건강 영향은 여전히 불확실하며, 연구자들은 어떠한 정책 권고도 내리기 전에 추가 종단 연구를 촉구했어요."},
  {"situation":"개인 진로를 논의할 때","en":"Graduates entering the job market during an economic downturn face an uncertain employment outlook, with many taking temporary or lower-skilled positions.","ko":"경기 침체 중에 취업 시장에 진입하는 졸업생들은 불확실한 고용 전망에 직면하며, 많은 이들이 임시직이나 낮은 기술 직위를 선택해요."},
  {"situation":"분쟁 해결을 논의할 때","en":"With the outcome of the appeal uncertain, both parties chose to explore mediation as a faster and less costly route to resolution.","ko":"항소 결과가 불확실한 상태에서 양측은 해결에 더 빠르고 비용이 적게 드는 경로로 조정을 탐색하기로 했어요."},
  {"situation":"기후 변화 영향을 논의할 때","en":"While the direction of climate change is clear, the exact regional impacts remain uncertain, making adaptation planning particularly challenging.","ko":"기후 변화의 방향은 명확하지만, 정확한 지역적 영향은 여전히 불확실하여 적응 계획이 특히 어려워요."},
  {"situation":"의료 치료를 논의할 때","en":"The prognosis remained uncertain after initial treatment, and the oncologist recommended a watchful waiting approach rather than immediate further intervention.","ko":"초기 치료 후 예후가 불확실한 상태로 남아 있어 종양학자는 즉각적인 추가 개입보다는 주의 깊은 대기 접근 방식을 권고했어요."},
  {"situation":"스타트업 환경을 논의할 때","en":"Operating in an uncertain and fast-changing market, the startup built scenario planning into its quarterly strategy reviews to remain prepared for multiple outcomes.","ko":"불확실하고 빠르게 변화하는 시장에서 운영되는 스타트업은 여러 결과에 대비하기 위해 분기별 전략 검토에 시나리오 계획을 통합했어요."},
  {"situation":"정치적 상황을 논의할 때","en":"The country's political future remained deeply uncertain following the inconclusive election result, with no party holding sufficient seats to form a stable government.","ko":"어떤 정당도 안정적인 정부를 구성하기에 충분한 의석을 확보하지 못해 불명확한 선거 결과 이후 국가의 정치적 미래는 깊이 불확실한 상태로 남았어요."},
  {"situation":"공중 보건 위기를 논의할 때","en":"In the early weeks of the outbreak, public health officials faced uncertain data and had to make critical decisions without the benefit of full epidemiological information.","ko":"발병 초기 몇 주 동안 공중 보건 당국자들은 불확실한 데이터에 직면했으며 완전한 역학 정보의 혜택 없이 중요한 결정을 내려야 했어요."}
]

R["unique"] = [
  {"situation":"제품 차별화를 논의할 때","en":"The startup's unique selling proposition was its AI-powered personalisation engine, which tailored content recommendations to individual users with far greater precision than rivals.","ko":"스타트업의 독자적인 판매 제안은 경쟁사보다 훨씬 더 정확하게 개별 사용자에게 콘텐츠 추천을 맞춤화하는 AI 기반 개인화 엔진이었어요."},
  {"situation":"문화 유산을 논의할 때","en":"The city's unique architectural heritage -- a blend of colonial, indigenous, and modernist styles -- attracts millions of visitors annually and underpins the local tourism economy.","ko":"식민지, 토착, 현대주의 양식이 혼합된 도시의 독특한 건축 유산은 매년 수백만 명의 방문객을 유치하고 지역 관광 경제를 뒷받침해요."},
  {"situation":"과학 현상을 설명할 때","en":"The Galapagos Islands offer a unique natural laboratory for studying evolution, as the isolation of each island allowed species to develop along distinct trajectories.","ko":"갈라파고스 제도는 각 섬의 격리가 종들이 별개의 궤적으로 발전할 수 있게 했기 때문에 진화를 연구하는 독특한 자연 실험실을 제공해요."},
  {"situation":"개인 역량을 논의할 때","en":"Recruiters advised graduates to clearly articulate their unique combination of technical skills and cross-cultural communication experience during interviews.","ko":"채용 담당자들은 졸업생들에게 면접 중에 기술적 기술과 다문화 소통 경험의 독특한 조합을 명확하게 표현하도록 조언했어요."},
  {"situation":"법적 사례를 논의할 때","en":"The case raised unique constitutional questions that had never been tested before, prompting the Supreme Court to convene an extended panel of nine justices.","ko":"이 사건은 이전에 한 번도 시험된 적 없는 독특한 헌법적 질문을 제기했으며, 대법원이 9명의 판사로 구성된 확대 패널을 소집하도록 촉구했어요."},
  {"situation":"경쟁 시장을 논의할 때","en":"The company spent several years building a unique customer data set that competitors would find prohibitively expensive to replicate, creating a durable competitive moat.","ko":"회사는 경쟁사들이 복제하기에 비용이 너무 많이 드는 독특한 고객 데이터 세트를 구축하는 데 수년을 보냈으며, 이는 지속적인 경쟁 해자를 만들었어요."},
  {"situation":"역사적 사건을 논의할 때","en":"The moon landing represented a unique convergence of scientific ambition, political rivalry, and engineering ingenuity that is unlikely to be replicated in quite the same way.","ko":"달 착륙은 과학적 야망, 정치적 경쟁, 공학적 창의성의 독특한 수렴을 나타냈으며 동일한 방식으로 재현될 가능성이 낮아요."},
  {"situation":"생태계 보전을 논의할 때","en":"The Congo Basin's unique biodiversity -- home to species found nowhere else on Earth -- makes its protection a priority for international conservation organisations.","ko":"지구상 어디에도 없는 종들의 서식지인 콩고 분지의 독특한 생물 다양성은 국제 보전 기관들에게 그 보호를 우선 과제로 만들어요."},
  {"situation":"의료 사례를 논의할 때","en":"The patient's case was unique in the clinical literature, combining symptoms from two conditions that had never previously been documented in the same individual.","ko":"환자의 사례는 임상 문헌에서 독특했으며, 이전에 같은 개인에서 기록된 적 없는 두 가지 상태의 증상을 결합했어요."},
  {"situation":"팀 강점을 논의할 때","en":"The team's unique strength lay in its diversity -- engineers, social scientists, and legal experts brought complementary perspectives that produced more robust solutions.","ko":"팀의 독특한 강점은 다양성에 있었으며, 엔지니어, 사회과학자, 법률 전문가들이 더 강력한 솔루션을 만들어내는 보완적인 관점을 가져왔어요."}
]

R["versatile"] = [
  {"situation":"직원 역량을 논의할 때","en":"Her versatile skill set -- combining deep technical expertise with strong commercial instincts -- made her an exceptionally valuable member of the cross-functional team.","ko":"심층 기술 전문 지식과 강력한 상업적 직관을 결합한 그녀의 다재다능한 기술 세트는 기능 간 팀의 매우 귀중한 구성원으로 만들었어요."},
  {"situation":"재료 공학을 논의할 때","en":"Carbon fibre is an extraordinarily versatile material: it is stronger than steel, lighter than aluminium, and is now used in everything from aircraft to prosthetics.","ko":"탄소 섬유는 매우 다재다능한 재료로, 강철보다 강하고 알루미늄보다 가벼우며 이제 항공기에서 보조기까지 모든 것에 사용돼요."},
  {"situation":"소프트웨어 도구를 논의할 때","en":"Python has become the dominant language in data science partly because it is so versatile, supporting everything from statistical analysis to machine learning to web scraping.","ko":"파이썬은 통계 분석에서 머신 러닝, 웹 스크래핑까지 모든 것을 지원할 만큼 다재다능하기 때문에 데이터 과학의 지배적인 언어가 됐어요."},
  {"situation":"농업 작물을 논의할 때","en":"Cassava is a versatile crop that can be processed into flour, starch, animal feed, and biofuel, making it valuable both as a food security staple and an industrial commodity.","ko":"카사바는 밀가루, 전분, 동물 사료, 바이오 연료로 가공될 수 있는 다재다능한 작물로, 식량 안보 주식이자 산업 원자재로서 가치가 있어요."},
  {"situation":"교육 방법론을 논의할 때","en":"Project-based learning is versatile enough to be adapted to virtually any subject, from mathematics to history, while simultaneously developing teamwork and critical thinking.","ko":"프로젝트 기반 학습은 수학에서 역사까지 사실상 어떤 과목에도 적용될 수 있을 만큼 다재다능하며, 동시에 팀워크와 비판적 사고를 개발해요."},
  {"situation":"건축 설계를 논의할 때","en":"The modular building system was praised for its versatility, enabling architects to create everything from affordable housing blocks to bespoke commercial office spaces.","ko":"모듈식 건물 시스템은 건축가들이 저렴한 주택 블록에서 맞춤형 상업 사무 공간까지 모든 것을 만들 수 있게 하는 다재다능함으로 찬사를 받았어요."},
  {"situation":"배우의 재능을 논의할 때","en":"Critics praised the actor for her remarkable versatility, noting that she was equally convincing in Shakespearean tragedy and contemporary romantic comedy.","ko":"비평가들은 셰익스피어 비극과 현대 로맨틱 코미디에서 동등하게 설득력 있다고 언급하며 그녀의 뛰어난 다재다능함을 칭찬했어요."},
  {"situation":"군사 장비를 논의할 때","en":"The helicopter proved so versatile in combat operations that it was adapted for medevac, reconnaissance, and close air support roles within a single deployment.","ko":"헬리콥터는 전투 작전에서 매우 다재다능한 것으로 증명되어 단일 배치 내에서 의료후송, 정찰, 근접 항공 지원 역할로 개조됐어요."},
  {"situation":"금융 상품을 논의할 때","en":"Exchange-traded funds are versatile investment vehicles that can be used for long-term wealth accumulation, short-term speculation, or portfolio hedging strategies.","ko":"상장지수펀드는 장기 자산 축적, 단기 투기, 포트폴리오 헤지 전략에 사용할 수 있는 다재다능한 투자 수단이에요."},
  {"situation":"요리 재료를 논의할 때","en":"Chickpeas are among the most versatile legumes: high in protein and fibre, they can be roasted as a snack, blended into hummus, or added to curries and salads.","ko":"병아리콩은 가장 다재다능한 콩류 중 하나로, 단백질과 섬유질이 풍부하며 스낵으로 구워먹거나 후무스로 갈거나 카레와 샐러드에 추가할 수 있어요."}
]

R["viable"] = [
  {"situation":"사업 계획을 논의할 때","en":"The investor declined to fund the project after the financial model showed it would not be commercially viable without substantial ongoing government subsidies.","ko":"재무 모델이 상당한 지속적인 정부 보조금 없이는 상업적으로 실행 가능하지 않을 것임을 보여준 후 투자자는 프로젝트 자금 지원을 거절했어요."},
  {"situation":"기술 대안을 논의할 때","en":"Hydrogen fuel cells have emerged as a viable alternative to battery electric vehicles for heavy-duty transport applications where weight and range are critical.","ko":"수소 연료 전지는 무게와 주행거리가 중요한 대형 운송 응용 분야에서 배터리 전기차의 실행 가능한 대안으로 등장했어요."},
  {"situation":"정책 옵션을 논의할 때","en":"Universal basic income is increasingly discussed as a viable policy response to the job displacement expected from widespread automation.","ko":"보편적 기본 소득은 광범위한 자동화로 예상되는 일자리 대체에 대한 실행 가능한 정책 대응으로 점점 더 많이 논의되고 있어요."},
  {"situation":"외과 시술을 논의할 때","en":"Surgeons told the patient that given her age and general health, a minimally invasive procedure was the only viable surgical option.","ko":"외과의들은 환자에게 나이와 전반적인 건강 상태를 고려할 때 최소 침습 시술이 유일한 실행 가능한 수술 옵션이라고 말했어요."},
  {"situation":"농업 기후 적응을 논의할 때","en":"Shifting to drought-resistant crop varieties is the most viable adaptation strategy for farmers in regions where annual rainfall is projected to decline significantly.","ko":"건조에 강한 작물 품종으로의 전환은 연간 강수량이 크게 감소할 것으로 예상되는 지역 농부들에게 가장 실행 가능한 적응 전략이에요."},
  {"situation":"도시 교통을 논의할 때","en":"Light rail is considered more viable than an underground metro for medium-sized cities because the construction costs are substantially lower relative to ridership potential.","ko":"경전철은 탑승 잠재력에 비해 건설 비용이 훨씬 낮기 때문에 중규모 도시에서 지하철보다 더 실행 가능한 것으로 간주돼요."},
  {"situation":"평화 협상을 논의할 때","en":"Analysts disagreed on whether a two-state solution remained viable given the extent of settlement construction that had occurred over the previous two decades.","ko":"분석가들은 지난 20년간 발생한 정착촌 건설의 규모를 감안할 때 두 국가 해결책이 여전히 실행 가능한지에 대해 의견이 일치하지 않았어요."},
  {"situation":"재생 에너지를 논의할 때","en":"Battery storage technology has advanced to the point where solar-plus-storage systems are now commercially viable without subsidy in many parts of the world.","ko":"배터리 저장 기술은 세계 많은 지역에서 태양광 + 저장 시스템이 이제 보조금 없이 상업적으로 실행 가능한 지점까지 발전했어요."},
  {"situation":"스타트업 생존을 논의할 때","en":"The startup was given six months to demonstrate a viable path to profitability, after which the investors would decide whether to commit to a Series B funding round.","ko":"스타트업은 수익성에 대한 실행 가능한 경로를 입증할 6개월을 부여받았으며, 그 후 투자자들은 시리즈 B 자금 조달에 참여할지 결정할 거예요."},
  {"situation":"역사적 국가 분리를 논의할 때","en":"By the late 1980s, the economic case for keeping the currency union together had weakened to the point where dissolution was being openly discussed as a viable option.","ko":"1980년대 말까지 통화 동맹을 유지하기 위한 경제적 논거는 해산이 실행 가능한 옵션으로 공개적으로 논의될 정도로 약화됐어요."}
]

count = 0
for w in data6['words']:
    if w['word'] in R:
        w['examples'] = R[w['word']]
        count += 1

print(f"Updated {count} words")
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_6.json', 'w', encoding='utf-8') as f:
    json.dump(data6, f, ensure_ascii=False, indent=2)
print("Saved ielts_6.json batch 4")
