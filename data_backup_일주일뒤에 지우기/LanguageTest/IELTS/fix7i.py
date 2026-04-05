import json
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', encoding='utf-8') as f:
    data7 = json.load(f)
R = {}

R["tangible"] = [
    {"situation": "정책 평가 및 결과 측정", "en": "The minister was pressed to demonstrate tangible outcomes from the healthcare reform after two years of implementation.", "ko": "장관은 2년간의 시행 후 의료 개혁으로 인한 실질적인 성과를 보여줄 것을 압박받았다."},
    {"situation": "기업 성과 및 투자 수익", "en": "Shareholders demanded tangible evidence of progress before approving the next phase of capital expenditure.", "ko": "주주들은 다음 단계의 자본 지출을 승인하기 전에 발전의 실질적인 증거를 요구했다."},
    {"situation": "자산 관리 및 재무 보고", "en": "Tangible assets such as property and machinery are depreciated on the balance sheet over their useful lives.", "ko": "부동산 및 기계와 같은 유형 자산은 유효 수명에 걸쳐 대차대조표에서 감가상각된다."},
    {"situation": "환경 정책 및 기후 행동", "en": "The community wanted to see tangible progress on air quality improvements before accepting further industrial development.", "ko": "지역 사회는 추가 산업 개발을 수용하기 전에 대기질 개선에 관한 실질적인 진전을 보고 싶었다."},
    {"situation": "외교 협상 및 합의 성과", "en": "The summit produced tangible commitments on trade and security, not merely vague declarations of intent.", "ko": "그 정상회담은 단순한 모호한 의향 선언이 아닌 무역과 안보에 관한 실질적인 약속을 만들어냈다."},
    {"situation": "교육 개혁 및 학습 성과", "en": "Tangible improvements in literacy rates were recorded within three years of introducing the new reading curriculum.", "ko": "새로운 독서 교육과정을 도입한 후 3년 내에 문해율의 실질적인 향상이 기록되었다."},
    {"situation": "사회 정의 및 불평등 해소", "en": "Advocates demanded tangible action on economic inequality rather than symbolic gestures or rhetorical commitments.", "ko": "지지자들은 상징적인 제스처나 수사적 약속이 아닌 경제적 불평등에 대한 실질적인 행동을 요구했다."},
    {"situation": "기술 혁신 및 사업화", "en": "The research project's findings were translated into tangible commercial applications within five years.", "ko": "그 연구 프로젝트의 발견들은 5년 내에 실질적인 상업 응용 프로그램으로 전환되었다."},
    {"situation": "법적 구제 및 손해배상 유형", "en": "Beyond tangible financial losses, the claimant sought compensation for non-material harm to her professional reputation.", "ko": "실질적인 재정적 손실 외에도 청구인은 자신의 직업적 명성에 대한 비물질적 피해에 대한 보상을 구했다."},
    {"situation": "스포츠 경기 및 팀 개선", "en": "The new coaching strategy brought tangible improvements to the team's defensive record within a single season.", "ko": "새로운 코칭 전략은 단 한 시즌 만에 팀의 수비 기록에 실질적인 향상을 가져왔다."}
]

R["transient"] = [
    {"situation": "경제학 및 일시적 충격 분석", "en": "Economists debated whether the spike in inflation was transient or indicated a deeper structural shift.", "ko": "경제학자들은 인플레이션 급등이 일시적인 것인지 더 깊은 구조적 변화를 나타내는지를 논쟁했다."},
    {"situation": "의학 및 일시적 증상", "en": "The patient experienced a transient ischaemic attack, which resolved within hours but signalled elevated stroke risk.", "ko": "환자는 수 시간 내에 해소되었지만 높아진 뇌졸중 위험을 신호한 일과성 허혈 발작을 경험했다."},
    {"situation": "사회학 및 이주 노동자 연구", "en": "The hotel industry has long relied on a transient workforce, with staff turning over rapidly between seasons.", "ko": "호텔 산업은 오랫동안 시즌 사이에 직원이 빠르게 교체되는 일시적 노동력에 의존해 왔다."},
    {"situation": "철학 및 존재의 덧없음", "en": "Buddhist philosophy holds that all worldly phenomena are transient, arising and passing away without permanence.", "ko": "불교 철학은 모든 세속적 현상이 일시적이며 영속성 없이 생겨나고 사라진다고 주장한다."},
    {"situation": "도시 개발 및 임시 인구", "en": "Cities with transient student populations face challenges in planning public transport and housing provision.", "ko": "일시적인 학생 인구를 보유한 도시들은 대중교통과 주택 공급 계획에서 어려움에 직면한다."},
    {"situation": "기후 과학 및 기상 현상", "en": "Some researchers argue that certain extreme weather events are transient anomalies rather than signs of permanent change.", "ko": "일부 연구자들은 특정 극단적인 기상 현상이 영구적인 변화의 징후가 아닌 일시적인 이상 현상이라고 주장한다."},
    {"situation": "기술 문화 및 디지털 트렌드", "en": "Many social media trends are entirely transient, disappearing from public consciousness within weeks.", "ko": "많은 소셜 미디어 트렌드는 완전히 일시적이며, 몇 주 내에 대중의 의식에서 사라진다."},
    {"situation": "심리학 및 기분 변화 연구", "en": "Transient feelings of anxiety before a presentation are normal and should not be confused with a clinical disorder.", "ko": "발표 전의 일시적인 불안감은 정상적이며 임상 장애와 혼동되어서는 안 된다."},
    {"situation": "부동산 및 임시 거주", "en": "The city's high housing costs have created a large population of transient renters who move frequently between districts.", "ko": "도시의 높은 주거 비용은 지역 간을 자주 이동하는 대규모 일시적 임차인 집단을 만들어냈다."},
    {"situation": "시장 변동성 및 투자자 반응", "en": "Markets treated the political uncertainty as transient, recovering quickly once the election result was announced.", "ko": "시장은 정치적 불확실성을 일시적인 것으로 취급하여 선거 결과가 발표되자마자 빠르게 회복했다."}
]

R["unilateral"] = [
    {"situation": "국제법 및 국가 행위", "en": "The unilateral withdrawal from the trade agreement surprised partner nations and triggered retaliatory tariffs.", "ko": "무역 협정에서의 일방적인 탈퇴는 파트너 국가들을 놀라게 했고 보복 관세를 촉발했다."},
    {"situation": "고용법 및 계약 변경", "en": "An employer cannot make a unilateral change to the terms of an employee's contract without their consent.", "ko": "고용주는 직원의 동의 없이 계약 조건을 일방적으로 변경할 수 없다."},
    {"situation": "군사 행동 및 UN 승인", "en": "Critics argued that the unilateral military intervention violated international law by bypassing UN authorisation.", "ko": "비평가들은 일방적인 군사 개입이 유엔 승인을 우회함으로써 국제법을 위반했다고 주장했다."},
    {"situation": "무역 정책 및 관세 조치", "en": "A unilateral increase in import tariffs can escalate into a full trade war if trading partners retaliate.", "ko": "수입 관세의 일방적인 인상은 무역 파트너들이 보복할 경우 전면적인 무역 전쟁으로 확대될 수 있다."},
    {"situation": "외교 협상 및 합의 파기", "en": "The government was accused of making unilateral decisions that undermined the multilateral negotiating framework.", "ko": "정부는 다자간 협상 틀을 훼손하는 일방적인 결정을 내렸다는 비난을 받았다."},
    {"situation": "기업 거버넌스 및 이사회 결정", "en": "The CEO's unilateral decision to cancel the acquisition without board approval triggered a governance crisis.", "ko": "이사회 승인 없이 인수를 취소한 CEO의 일방적인 결정이 거버넌스 위기를 촉발했다."},
    {"situation": "환경 정책 및 국제 협력", "en": "Unilateral environmental measures can be effective domestically but risk disadvantaging domestic industries against foreign competitors.", "ko": "일방적인 환경 조치는 국내적으로 효과적일 수 있지만 외국 경쟁자들에 대해 국내 산업을 불리하게 만들 위험이 있다."},
    {"situation": "분쟁 해결 및 중재 조항", "en": "The arbitration clause prevented either party from taking unilateral legal action in the national courts.", "ko": "중재 조항은 어느 당사자도 국내 법원에서 일방적인 법적 조치를 취하는 것을 방지했다."},
    {"situation": "디지털 플랫폼 및 이용 약관 변경", "en": "The platform was criticised for making unilateral changes to its terms of service without notifying users in advance.", "ko": "그 플랫폼은 사용자에게 사전 통지 없이 서비스 이용 약관을 일방적으로 변경했다는 비판을 받았다."},
    {"situation": "핵 비확산 및 군비 통제", "en": "Unilateral disarmament is rarely considered a credible strategy in regions with unresolved territorial disputes.", "ko": "일방적인 군비 축소는 미해결 영토 분쟁이 있는 지역에서 신뢰할 수 있는 전략으로 거의 여겨지지 않는다."}
]

R["unprecedented"] = [
    {"situation": "경제 위기 및 정책 대응", "en": "Governments launched unprecedented stimulus packages in response to the economic shock caused by the pandemic.", "ko": "정부들은 팬데믹이 초래한 경제적 충격에 대응하여 전례 없는 경기 부양 패키지를 출시했다."},
    {"situation": "기후 변화 및 극단적 기상 현상", "en": "The region experienced an unprecedented drought lasting three consecutive years, devastating agricultural output.", "ko": "그 지역은 3년 연속 지속된 전례 없는 가뭄을 경험하여 농업 생산량에 막대한 피해를 입혔다."},
    {"situation": "기술 발전 및 사회 변화", "en": "The internet enabled an unprecedented exchange of information across borders, transforming global communication.", "ko": "인터넷은 국경을 초월한 전례 없는 정보 교환을 가능하게 하여 글로벌 통신을 변화시켰다."},
    {"situation": "법률 및 역사적 판결", "en": "The court issued an unprecedented ruling that recognised the rights of future generations in environmental law.", "ko": "법원은 환경법에서 미래 세대의 권리를 인정하는 전례 없는 판결을 내렸다."},
    {"situation": "국제 외교 및 정상 회담", "en": "The two leaders held an unprecedented joint press conference, signalling a historic shift in bilateral relations.", "ko": "두 지도자는 양자 관계의 역사적 전환을 신호하는 전례 없는 공동 기자 회견을 열었다."},
    {"situation": "과학 발견 및 의학 돌파구", "en": "The speed at which COVID-19 vaccines were developed was unprecedented in the history of vaccinology.", "ko": "코로나-19 백신이 개발된 속도는 예방 접종 과학 역사에서 전례가 없었다."},
    {"situation": "기업 성장 및 시장 가치", "en": "The technology company achieved an unprecedented valuation of one trillion dollars within just twelve years of founding.", "ko": "그 기술 회사는 설립 후 불과 12년 만에 전례 없는 1조 달러의 기업 가치를 달성했다."},
    {"situation": "사회 운동 및 집단 행동", "en": "The protest drew an unprecedented crowd, with organisers claiming participation exceeded one million people.", "ko": "그 시위는 전례 없는 군중을 끌어모았으며, 주최측은 참가자가 100만 명을 초과했다고 주장했다."},
    {"situation": "공중 보건 및 팬데믹 대응", "en": "The pandemic placed unprecedented demands on intensive care units and healthcare workers worldwide.", "ko": "팬데믹은 전 세계 중환자실과 의료 종사자들에게 전례 없는 부담을 안겨주었다."},
    {"situation": "예술 문화 및 역사적 기록", "en": "The auction achieved an unprecedented price for a work by a living artist, shattering all previous records.", "ko": "그 경매는 생존 예술가의 작품에 대한 전례 없는 가격을 달성하며 이전의 모든 기록을 깼다."}
]

R["zealous"] = [
    {"situation": "법정 변론 및 변호사 의무", "en": "A defence lawyer is obliged to provide zealous representation for the client, regardless of personal views on the case.", "ko": "변호인은 사건에 대한 개인적인 견해에 관계없이 의뢰인을 위해 열성적인 변호를 제공할 의무가 있다."},
    {"situation": "사회 운동 및 시민 참여", "en": "Zealous campaigners pressured the government to introduce stricter controls on single-use plastic packaging.", "ko": "열성적인 운동가들은 정부에 일회용 플라스틱 포장에 대한 더 엄격한 규제를 도입하도록 압박했다."},
    {"situation": "종교 및 신앙 생활", "en": "Her zealous devotion to charitable work inspired many in the local community to volunteer their time.", "ko": "자선 활동에 대한 그녀의 열성적인 헌신은 지역 사회의 많은 사람들이 시간을 자원봉사하도록 영감을 주었다."},
    {"situation": "교육 및 교직 열정", "en": "The teacher's zealous commitment to her students' progress was evident in the extra sessions she offered after school.", "ko": "학생들의 발전에 대한 교사의 열성적인 헌신은 방과 후 제공한 추가 수업에서 분명히 드러났다."},
    {"situation": "규제 집행 및 공무원 과잉 집행", "en": "Critics accused the regulator of being zealous to the point of stifling innovation in the emerging technology sector.", "ko": "비평가들은 규제 당국이 신흥 기술 부문의 혁신을 억압하는 수준으로 지나치게 열성적이라고 비난했다."},
    {"situation": "스포츠 팬덤 및 경기 응원", "en": "The stadium was filled with zealous supporters who had travelled from across the country to cheer their team.", "ko": "경기장은 팀을 응원하기 위해 전국 각지에서 온 열성적인 지지자들로 가득 찼다."},
    {"situation": "세금 조사 및 강제 집행", "en": "Tax authorities conducted a zealous investigation into offshore structures that had reduced the company's domestic tax bill.", "ko": "세무 당국은 회사의 국내 세금 청구서를 줄인 역외 구조에 대한 열성적인 조사를 실시했다."},
    {"situation": "국제 개발 및 원조 단체 활동", "en": "Zealous non-governmental workers sometimes risk cultural insensitivity by imposing external frameworks on local communities.", "ko": "열성적인 비정부 기구 활동가들은 때때로 외부 틀을 지역 사회에 강요하여 문화적 무감각의 위험을 무릅쓴다."},
    {"situation": "직업 윤리 및 과도한 열정", "en": "While professional dedication is valued, overly zealous conduct can breach ethical boundaries in sensitive negotiations.", "ko": "직업적 헌신이 가치 있는 것으로 여겨지지만, 지나치게 열성적인 행동은 민감한 협상에서 윤리적 경계를 침범할 수 있다."},
    {"situation": "정치 활동 및 이념 추구", "en": "Zealous political activists can energise a movement but may also alienate moderate voters whose support is needed for electoral success.", "ko": "열성적인 정치 활동가들은 운동에 활력을 불어넣을 수 있지만 선거 성공에 필요한 지지가 필요한 온건한 유권자들을 소외시킬 수도 있다."}
]

count = 0
for w in data7['words']:
    if w['word'] in R:
        w['examples'] = R[w['word']]
        count += 1
print(f"Updated {count} words")
with open('D:/MakingApps/Youtube/Hellowords/data/IELTS/ielts_7.json', 'w', encoding='utf-8') as f:
    json.dump(data7, f, ensure_ascii=False, indent=2)
print("Saved ielts_7.json batch 9")
