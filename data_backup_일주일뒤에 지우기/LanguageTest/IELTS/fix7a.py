import json

with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', encoding='utf-8') as f:
    data7 = json.load(f)

R = {}

R["adversarial"] = [
  {"situation":"법정 소송 구조를 설명할 때","en":"Common law jurisdictions rely on an adversarial court system in which opposing counsel present evidence and arguments before a neutral judge or jury.","ko":"관습법 관할구역은 중립적인 판사나 배심원단 앞에서 반대측 법률 대리인이 증거와 논거를 제시하는 대립적 법원 시스템에 의존해요."},
  {"situation":"노사 관계를 논의할 때","en":"Decades of adversarial labour relations left a legacy of distrust that made it difficult for management and unions to collaborate even when their interests converged.","ko":"수십 년간의 대립적인 노사 관계는 불신의 유산을 남겨 이해관계가 일치할 때조차도 경영진과 노조가 협력하기 어렵게 만들었어요."},
  {"situation":"외교 협상을 논의할 때","en":"The summit failed to produce a joint communique because both delegations arrived with adversarial briefing notes that precluded genuine compromise.","ko":"양 대표단이 진정한 타협을 막는 대립적인 브리핑 노트를 가지고 도착했기 때문에 정상회담은 공동 성명 작성에 실패했어요."},
  {"situation":"기업 지배구조를 논의할 때","en":"An adversarial relationship between the board and the CEO undermines strategic coherence, as energy is spent on internal conflict rather than competitive positioning.","ko":"이사회와 CEO 사이의 대립적인 관계는 에너지가 경쟁적 포지셔닝이 아닌 내부 갈등에 소비되면서 전략적 일관성을 약화시켜요."},
  {"situation":"규제 관계를 논의할 때","en":"The regulator adopted a more collaborative approach after studies showed that adversarial enforcement was producing technical compliance without substantive improvement.","ko":"연구에서 대립적인 집행이 실질적인 개선 없는 형식적 준수를 만들어내고 있음이 나타나자 규제당국은 더 협력적인 접근 방식을 채택했어요."},
  {"situation":"국제 관계를 논의할 때","en":"The two superpowers maintained an adversarial posture throughout the Cold War, yet managed to avoid direct military conflict through carefully calibrated deterrence.","ko":"두 강대국은 냉전 내내 대립적인 자세를 유지했지만, 세심하게 조정된 억지력을 통해 직접적인 군사 충돌을 피할 수 있었어요."},
  {"situation":"심리학적 연구를 설명할 때","en":"Children raised in adversarial household environments often develop defensive communication patterns that persist into adulthood and affect personal relationships.","ko":"대립적인 가정 환경에서 자란 아이들은 종종 성인기까지 지속되어 개인 관계에 영향을 미치는 방어적 소통 패턴을 발전시켜요."},
  {"situation":"구매 협상을 논의할 때","en":"Old-school procurement teams that take an adversarial stance in supplier negotiations often find that vendors cut quality margins to compensate for squeezed prices.","ko":"공급업체 협상에서 대립적인 입장을 취하는 구식 구매팀은 공급업체가 압박된 가격을 보상하기 위해 품질 마진을 줄인다는 것을 종종 발견해요."},
  {"situation":"학술 토론을 논의할 때","en":"The adversarial format of traditional academic debates, where participants are assigned positions rather than advocating their genuine views, has fallen out of favour in many institutions.","ko":"참가자들이 진정한 견해를 옹호하는 대신 입장을 배정받는 전통적인 학술 토론의 대립적 형식은 많은 기관에서 선호도가 줄었어요."},
  {"situation":"경쟁 전략을 논의할 때","en":"Some industries thrive on adversarial competition, where rivals actively attempt to destroy each other's market share rather than coexisting in a stable oligopoly.","ko":"일부 산업은 경쟁자들이 안정적인 과점에서 공존하는 것이 아니라 서로의 시장 점유율을 파괴하려 적극적으로 시도하는 대립적 경쟁에서 번성해요."}
]

R["ancillary"] = [
  {"situation":"의료 서비스를 논의할 때","en":"Ancillary services such as physiotherapy, dietetics, and occupational therapy are essential complements to surgical care but are frequently underfunded.","ko":"물리치료, 영양학, 작업치료와 같은 보조 서비스는 수술 치료의 필수적인 보완 요소이지만 종종 자금 부족에 시달려요."},
  {"situation":"법적 문서를 논의할 때","en":"The acquisition agreement required completion of several ancillary documents, including a shareholders' deed, a deed of adherence, and a transitional services agreement.","ko":"인수 계약은 주주 약정서, 준수 약정서, 전환 서비스 계약을 포함한 여러 부수적 문서의 작성을 요구했어요."},
  {"situation":"비즈니스 수익 모델을 논의할 때","en":"Low-cost airlines rely heavily on ancillary revenue streams -- baggage fees, seat upgrades, and onboard food -- to compensate for rock-bottom base fares.","ko":"저비용 항공사들은 최저가 기본 요금을 보상하기 위해 수하물 수수료, 좌석 업그레이드, 기내 음식 등의 부수적 수입원에 크게 의존해요."},
  {"situation":"군사 작전을 논의할 때","en":"The mission's primary objective was the extraction of intelligence assets; all other activities were ancillary to this overriding operational goal.","ko":"임무의 주요 목표는 정보 자산의 추출이었으며, 다른 모든 활동은 이 최우선 작전 목표에 부수적인 것이었어요."},
  {"situation":"에너지 인프라를 논의할 때","en":"Ancillary services such as frequency regulation and voltage control are essential for maintaining grid stability when renewable energy output fluctuates unpredictably.","ko":"주파수 조정 및 전압 제어와 같은 보조 서비스는 재생 에너지 출력이 예측할 수 없이 변동할 때 전력망 안정성을 유지하는 데 필수적이에요."},
  {"situation":"교육 지원 서비스를 논의할 때","en":"Schools increasingly recognise that ancillary services such as counselling, mentoring, and family liaison work are just as important as classroom instruction.","ko":"학교들은 상담, 멘토링, 가족 연락 업무와 같은 보조 서비스가 교실 수업만큼 중요하다는 것을 점점 더 인식하고 있어요."},
  {"situation":"IT 시스템을 논의할 때","en":"The core banking platform operates alongside a range of ancillary systems for fraud detection, compliance reporting, and customer relationship management.","ko":"핵심 뱅킹 플랫폼은 사기 탐지, 준수 보고, 고객 관계 관리를 위한 다양한 보조 시스템과 함께 운영돼요."},
  {"situation":"법원 절차를 논의할 때","en":"Ancillary proceedings, such as asset tracing and freezing orders, can be initiated in parallel with the main litigation to preserve the value of any eventual award.","ko":"자산 추적 및 동결 명령과 같은 부수적 절차는 최종 판결의 가치를 보존하기 위해 주요 소송과 병행하여 시작될 수 있어요."},
  {"situation":"헬스케어 인력을 논의할 때","en":"Ancillary healthcare workers -- including porters, cleaners, and catering staff -- are often overlooked despite being critical to infection control and patient experience.","ko":"운반원, 청소부, 급식 직원을 포함한 보조 의료 인력은 감염 통제와 환자 경험에 중요함에도 불구하고 종종 간과돼요."},
  {"situation":"영화 산업을 논의할 때","en":"Studio executives increasingly depend on ancillary markets -- streaming rights, merchandise, and theme park licensing -- to recoup the cost of expensive blockbuster productions.","ko":"스튜디오 임원들은 비용이 많이 드는 블록버스터 제작 비용을 회수하기 위해 스트리밍 권리, 상품, 테마파크 라이선스와 같은 부수적 시장에 점점 더 의존해요."}
]

R["antitrust"] = [
  {"situation":"독점 규제를 논의할 때","en":"The antitrust authority blocked the proposed merger after determining that it would reduce the number of competitors in the market from five to just two.","ko":"반독점 당국은 시장의 경쟁자 수가 5개에서 단 2개로 줄어들 것이라고 판단한 후 제안된 합병을 차단했어요."},
  {"situation":"빅테크 규제를 논의할 때","en":"Regulators in multiple jurisdictions have launched antitrust investigations into the major technology platforms, alleging that they use their dominant position to stifle competition.","ko":"여러 관할구역의 규제당국들은 주요 기술 플랫폼들이 지배적 지위를 이용해 경쟁을 억제한다는 혐의로 반독점 조사를 시작했어요."},
  {"situation":"가격 담합을 논의할 때","en":"The executives faced criminal antitrust charges after investigators uncovered evidence of a secret cartel that had fixed prices in the air freight market for nearly a decade.","ko":"조사관들이 거의 10년 동안 항공 화물 시장에서 가격을 고정한 비밀 카르텔의 증거를 발견한 후 임원들은 형사 반독점 혐의를 받았어요."},
  {"situation":"M&A 승인 절차를 논의할 때","en":"Completing the transaction required antitrust clearance from regulators in sixteen countries, a process that took nearly two years and required significant structural remedies.","ko":"거래를 완료하기 위해 16개국 규제당국으로부터 반독점 승인을 받아야 했으며, 이 과정은 거의 2년이 걸렸고 상당한 구조적 개선 조치가 필요했어요."},
  {"situation":"시장 지배력을 논의할 때","en":"Critics argued that the platform's practice of favouring its own products in search results constituted antitrust behaviour that disadvantaged third-party sellers.","ko":"비평가들은 플랫폼이 검색 결과에서 자사 제품을 우대하는 관행이 제3자 판매자들에게 불이익을 주는 반독점 행위를 구성한다고 주장했어요."},
  {"situation":"글로벌 기업 전략을 논의할 때","en":"The global pharmaceutical company restructured its licensing arrangements to address antitrust concerns that the existing terms were preventing generic drug manufacturers from entering the market.","ko":"글로벌 제약 회사는 기존 조건이 제네릭 의약품 제조업체의 시장 진입을 막고 있다는 반독점 우려를 해결하기 위해 라이선스 약정을 재구성했어요."},
  {"situation":"법적 원칙을 설명할 때","en":"Antitrust law is designed to protect consumers and foster innovation by ensuring that no single firm can achieve a level of market dominance that eliminates competitive pressure.","ko":"반독점법은 어떤 단일 기업도 경쟁 압력을 제거하는 수준의 시장 지배력을 달성할 수 없도록 보장함으로써 소비자를 보호하고 혁신을 촉진하도록 설계됐어요."},
  {"situation":"병원 합병을 논의할 때","en":"The hospital merger faced antitrust scrutiny because the two institutions jointly held over seventy percent of the regional market for several specialist surgical procedures.","ko":"두 기관이 여러 전문 수술 시술에 대해 지역 시장의 70% 이상을 공동으로 보유했기 때문에 병원 합병은 반독점 심사에 직면했어요."},
  {"situation":"경제사를 논의할 때","en":"The breakup of Standard Oil in 1911 remains the most famous antitrust case in American history, demonstrating that even the most powerful corporations are not immune to regulatory action.","ko":"1911년 스탠더드 오일 분할은 미국 역사상 가장 유명한 반독점 사례로 남아 있으며, 가장 강력한 기업조차도 규제 조치에 면역되지 않음을 보여줘요."},
  {"situation":"경쟁 정책을 논의할 때","en":"Economists debate whether antitrust policy should focus narrowly on consumer prices or adopt a broader framework that considers effects on workers, suppliers, and market diversity.","ko":"경제학자들은 반독점 정책이 소비자 가격에만 집중해야 하는지, 아니면 근로자, 공급업체, 시장 다양성에 대한 영향을 고려하는 더 넓은 프레임워크를 채택해야 하는지 논쟁해요."}
]

R["arbitral"] = [
  {"situation":"국제 상사 중재를 설명할 때","en":"The dispute was referred to arbitral proceedings under ICC rules, with the seat of arbitration designated as Geneva and the governing law specified as English law.","ko":"분쟁은 ICC 규칙에 따른 중재 절차에 회부됐으며, 중재지는 제네바로, 준거법은 영국법으로 지정됐어요."},
  {"situation":"중재 판정 집행을 설명할 때","en":"Under the New York Convention, arbitral awards rendered in one signatory state are enforceable in the courts of over 170 other countries without re-litigation of the merits.","ko":"뉴욕 협약에 따라 한 서명국에서 내려진 중재 판정은 170개국 이상의 법원에서 본안 재소송 없이 집행 가능해요."},
  {"situation":"투자자-국가 분쟁을 설명할 때","en":"The investor-state arbitral tribunal held that the government's sudden revocation of the mining licence constituted an indirect expropriation without adequate compensation.","ko":"투자자-국가 중재 재판소는 정부의 채굴 허가 갑작스러운 취소가 적절한 보상 없는 간접 수용에 해당한다고 판결했어요."},
  {"situation":"중재 조항을 설명할 때","en":"The arbitral clause in the employment contract required all disputes to be resolved through binding arbitration rather than through the courts, limiting employees' rights to litigate.","ko":"고용 계약의 중재 조항은 모든 분쟁을 법원이 아닌 구속력 있는 중재를 통해 해결하도록 요구하여 직원들의 소송 권리를 제한했어요."},
  {"situation":"중재인 선정을 설명할 때","en":"Each party appointed one co-arbitrator, and those two arbitrators jointly selected a presiding arbitrator to chair the arbitral tribunal.","ko":"각 당사자가 공동 중재인 1명을 임명했으며, 두 중재인은 공동으로 중재 재판소를 주재할 의장 중재인을 선정했어요."},
  {"situation":"중재 판정 취소를 설명할 때","en":"The losing party applied to set aside the arbitral award, arguing that the tribunal had exceeded its jurisdiction by ruling on matters not covered by the arbitration agreement.","ko":"패소 당사자는 재판소가 중재 합의에 포함되지 않은 사안에 대해 판결함으로써 관할권을 초과했다고 주장하며 중재 판정 취소를 신청했어요."},
  {"situation":"절차적 공정성을 설명할 때","en":"Arbitral proceedings must comply with fundamental principles of natural justice: both parties must have a fair opportunity to present their case and respond to opposing submissions.","ko":"중재 절차는 자연적 정의의 기본 원칙을 준수해야 하며, 양 당사자는 자신의 사안을 제시하고 반대측 의견에 답변할 공정한 기회를 가져야 해요."},
  {"situation":"중재 비용을 설명할 때","en":"The arbitral tribunal ordered the unsuccessful claimant to bear the full costs of the proceedings, amounting to over three million dollars in legal fees and arbitrator compensation.","ko":"중재 재판소는 패소한 청구인이 법률 수수료와 중재인 보상 비용을 합산하여 300만 달러 이상의 절차 비용 전액을 부담하도록 명령했어요."},
  {"situation":"기밀 유지를 설명할 때","en":"One advantage of arbitral proceedings over court litigation is confidentiality: the hearings, evidence, and final award are not matters of public record.","ko":"중재 절차가 법원 소송에 비해 갖는 한 가지 이점은 기밀성이에요: 심리, 증거, 최종 판정은 공개 기록 사항이 아니에요."},
  {"situation":"긴급 중재를 설명할 때","en":"The claimant applied for emergency arbitral relief to obtain an interim injunction preventing the respondent from disposing of key assets pending the main hearing.","ko":"청구인은 주요 심리 전에 피청구인이 핵심 자산을 처분하는 것을 막기 위한 임시 금지 명령을 얻기 위해 긴급 중재 구제를 신청했어요."}
]

R["bespoke"] = [
  {"situation":"맞춤형 서비스를 설명할 때","en":"The wealth management firm offered bespoke investment portfolios tailored to each client's unique financial goals, risk tolerance, and tax circumstances.","ko":"자산 관리 회사는 각 고객의 독특한 재무 목표, 위험 허용도, 세금 상황에 맞춘 맞춤형 투자 포트폴리오를 제공했어요."},
  {"situation":"맞춤 제작 의류를 설명할 때","en":"Savile Row is renowned for bespoke tailoring, where garments are cut and stitched entirely to a customer's individual measurements over multiple fittings.","ko":"새빌 로는 맞춤 재단으로 유명하며, 여러 번의 피팅을 거쳐 고객의 개별 치수에 맞춰 의류를 재단하고 바느질해요."},
  {"situation":"소프트웨어 개발을 설명할 때","en":"The company commissioned a bespoke software platform after finding that no off-the-shelf solution could handle the complexity of its multi-currency, multi-jurisdiction reporting requirements.","ko":"회사는 기성 솔루션이 복잡한 다중 통화, 다중 관할구역 보고 요건을 처리할 수 없다는 것을 발견한 후 맞춤형 소프트웨어 플랫폼을 의뢰했어요."},
  {"situation":"건축 설계를 설명할 때","en":"Rather than selecting from a catalogue of standard house designs, the couple worked with an architect to create a bespoke home that maximised the natural light of the unusual plot.","ko":"표준 주택 설계 카탈로그에서 선택하는 대신 부부는 건축가와 협력하여 독특한 부지의 자연 채광을 극대화하는 맞춤형 주택을 만들었어요."},
  {"situation":"교육 프로그램을 설명할 때","en":"The organisation developed a bespoke leadership training programme for its top 200 managers, combining executive coaching, peer learning, and board-level mentoring.","ko":"조직은 임원 코칭, 동료 학습, 이사회 수준의 멘토링을 결합하여 상위 200명의 관리자를 위한 맞춤형 리더십 교육 프로그램을 개발했어요."},
  {"situation":"금융 상품을 설명할 때","en":"The investment bank structured a bespoke derivative that allowed the client to hedge its exposure to a specific basket of emerging market currencies not covered by standard instruments.","ko":"투자은행은 고객이 표준 상품으로 헤지할 수 없는 특정 신흥 시장 통화 바스켓에 대한 노출을 헤지할 수 있도록 맞춤형 파생상품을 구조화했어요."},
  {"situation":"법률 서비스를 설명할 때","en":"Complex cross-border transactions require bespoke legal advice that integrates multiple jurisdictions' requirements rather than simply applying a standard template.","ko":"복잡한 국경 간 거래는 단순히 표준 템플릿을 적용하는 것이 아니라 여러 관할구역의 요건을 통합하는 맞춤형 법률 자문이 필요해요."},
  {"situation":"가구 제작을 설명할 때","en":"The interior designer commissioned a bespoke bookcase that fitted precisely into the alcove, making use of every centimetre of an awkwardly shaped space.","ko":"인테리어 디자이너는 어색하게 생긴 공간의 모든 센티미터를 활용하여 벽감에 정확히 맞는 맞춤형 책장을 의뢰했어요."},
  {"situation":"의료 치료를 설명할 때","en":"Advances in genomic medicine have made bespoke cancer treatments possible, with therapies designed around the specific genetic mutations found in an individual patient's tumour.","ko":"유전체 의학의 발전으로 개별 환자의 종양에서 발견된 특정 유전자 돌연변이를 중심으로 설계된 치료법을 통한 맞춤형 암 치료가 가능해졌어요."},
  {"situation":"기업 이벤트를 설명할 때","en":"The event management company created a bespoke conference experience for the multinational client, incorporating real-time translation, cultural briefings, and individually tailored delegate packs.","ko":"이벤트 관리 회사는 실시간 번역, 문화 브리핑, 개별 맞춤형 대표단 패키지를 포함하여 다국적 고객을 위한 맞춤형 컨퍼런스 경험을 만들었어요."}
]

R["bilateral"] = [
  {"situation":"무역 협정을 논의할 때","en":"The bilateral free trade agreement eliminated tariffs on over ninety percent of goods traded between the two countries, boosting exports by an estimated twenty percent within five years.","ko":"양자 자유 무역 협정은 양국 간 거래되는 상품의 90% 이상에 대한 관세를 철폐하여 5년 이내에 수출을 약 20% 증가시켰어요."},
  {"situation":"외교 관계를 논의할 때","en":"Following a brief diplomatic rupture over fishing rights, bilateral relations between the two neighbouring states were restored through intensive back-channel negotiations.","ko":"어업권을 둘러싼 짧은 외교적 단절 이후 두 인접 국가 간의 양자 관계는 집중적인 비공개 협상을 통해 회복됐어요."},
  {"situation":"방위 협력을 논의할 때","en":"The two allies signed a bilateral defence pact that obligated each party to come to the other's aid in the event of an armed attack on either country's territory.","ko":"두 동맹국은 어느 한 국가의 영토에 대한 무력 공격 시 상대방을 지원할 의무를 명시한 양자 방위 협정에 서명했어요."},
  {"situation":"환경 협력을 논의할 때","en":"The bilateral environmental agreement committed both governments to shared monitoring of air and water quality across their shared border region.","ko":"양자 환경 협정은 양국 정부가 공동 국경 지역의 대기 및 수질 공동 모니터링을 이행하도록 약속했어요."},
  {"situation":"투자 보호를 논의할 때","en":"Bilateral investment treaties provide foreign investors with protections against expropriation and guarantee access to international arbitration in the event of a dispute with the host state.","ko":"양자 투자 조약은 외국 투자자들에게 수용에 대한 보호를 제공하고 투자 유치국과의 분쟁 시 국제 중재에 접근할 수 있도록 보장해요."},
  {"situation":"의료 협력을 논의할 때","en":"The bilateral health agreement enabled both countries to share epidemiological data and co-ordinate cross-border contact tracing during infectious disease outbreaks.","ko":"양자 보건 협정은 양국이 역학 데이터를 공유하고 감염병 발생 시 국경 간 접촉자 추적을 조율할 수 있게 했어요."},
  {"situation":"학술 교류를 논의할 때","en":"The bilateral academic exchange programme allowed up to fifty students from each country to study at the partner institution each year with full tuition fee waivers.","ko":"양자 학술 교류 프로그램은 각국에서 최대 50명의 학생이 매년 파트너 기관에서 전액 등록금 면제로 공부할 수 있게 했어요."},
  {"situation":"원조 협력을 논의할 때","en":"Bilateral aid programmes are often criticised for advancing the donor country's strategic interests rather than prioritising the genuine development needs of the recipient.","ko":"양자 원조 프로그램은 종종 수원국의 진정한 개발 필요를 우선시하는 대신 공여국의 전략적 이익을 증진한다는 비판을 받아요."},
  {"situation":"통화 스왑을 논의할 때","en":"The central banks established a bilateral currency swap arrangement, allowing either party to access the other's currency to manage liquidity pressures without depleting reserves.","ko":"두 중앙은행은 양자 통화 스왑 약정을 체결하여 어느 한 쪽이 준비금을 소진하지 않고 유동성 압박을 관리하기 위해 상대방의 통화에 접근할 수 있게 했어요."},
  {"situation":"의학 임상시험을 논의할 때","en":"In a bilateral study of the treatment, patients in both the active and placebo groups were monitored over twelve months to assess long-term safety and efficacy outcomes.","ko":"치료에 대한 양측 연구에서 활성 집단과 위약 집단 모두의 환자들이 장기 안전성과 효능 결과를 평가하기 위해 12개월 동안 모니터링됐어요."}
]

count = 0
for w in data7['words']:
    if w['word'] in R:
        w['examples'] = R[w['word']]
        count += 1

print(f"Updated {count} words")
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', 'w', encoding='utf-8') as f:
    json.dump(data7, f, ensure_ascii=False, indent=2)
print("Saved ielts_7.json batch 1")
