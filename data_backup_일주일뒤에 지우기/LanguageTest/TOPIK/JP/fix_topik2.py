import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('D:/MakingApps/Youtube/Hellowords/data/TOPIK/JP/topik_2.json', 'r', encoding='utf-8') as f:
    data2 = json.load(f)

fix_count = 0

for word in data2['words']:
    wid = word['id']
    w = word['word']

    # ── MEANING FIXES ──────────────────────────────────────

    # 냄새: 臭い is too negative - it means any smell; 中立的なにおい
    if w == '냄새' and word['meaning'] == '臭い':
        word['meaning'] = 'におい'; fix_count += 1

    # 너: informal 'you' -> きみ is more natural than あなた for this informal word
    if w == '너' and word['meaning'] == 'あなた':
        word['meaning'] = 'きみ/あなた'; fix_count += 1

    # 녹색: グリーン is English loan; 緑色 is standard Japanese
    if w == '녹색' and word['meaning'] == 'グリーン':
        word['meaning'] = '緑色'; fix_count += 1

    # 늘다: 伸びる is wrong; 늘다 = to increase/improve
    if w == '늘다' and word['meaning'] == '伸びる':
        word['meaning'] = '増える/上達する'; fix_count += 1

    # 몸살: 身体 is completely wrong - 몸살 = body aches/fatigue illness
    if w == '몸살' and word['meaning'] == '身体':
        word['meaning'] = '体のだるさ（体が痛くなる疲れ型の風邪）'; fix_count += 1

    # 무: 無 is wrong - 무 = 大根 (white radish) in Korean cooking context
    if w == '무' and word['meaning'] == '無':
        word['meaning'] = '大根'; fix_count += 1

    # 무궁화: ムグンファ should be ムクゲ (Japanese name for hibiscus syriacus)
    if w == '무궁화' and word['meaning'] == 'ムグンファ':
        word['meaning'] = 'ムクゲ（韓国の国花）'; fix_count += 1

    # 물어보다: 頼むより is completely wrong - 물어보다 = to ask/inquire
    if w == '물어보다' and '頼む' in word['meaning']:
        word['meaning'] = '聞く/尋ねる'; fix_count += 1

    # 미술: アート is English loan; 美術 is standard Japanese
    if w == '미술' and word['meaning'] == 'アート':
        word['meaning'] = '美術'; fix_count += 1

    # 미안하다: すみません is too light for this apology word
    # 미안하다 = ごめんなさい (sorry, apology)
    if w == '미안하다' and word['meaning'] == 'すみません':
        word['meaning'] = 'ごめんなさい'; fix_count += 1

    # 미안합니다: formal apology
    if w == '미안합니다' and word['meaning'] == 'すみません':
        word['meaning'] = '申し訳ありません'; fix_count += 1

    # 미터: メーター is wrong (that's a meter/gauge reading) - 미터 = メートル
    if w == '미터' and word['meaning'] == 'メーター':
        word['meaning'] = 'メートル'; fix_count += 1

    # ── EXAMPLE FIXES ──────────────────────────────────────
    for ex in word['examples']:
        ko = ex['ko']
        jp = ex['jp']
        new_jp = jp

        # 1. マート -> スーパー
        if 'マート' in new_jp and 'スマート' not in new_jp:
            new_jp = new_jp.replace('マート', 'スーパー')

        # 2. 薬を食べ -> 薬を飲む
        new_jp = new_jp.replace('薬を食べた。', '薬を飲んだ。')
        new_jp = new_jp.replace('薬を食べました', '薬を飲みました')
        new_jp = new_jp.replace('薬を食べるのが好きです', '薬を飲むのが良いです')
        if re.search(r'약을 먹', ko) and '食べ' in new_jp:
            new_jp = re.sub(r'薬を食べ', '薬を飲', new_jp)

        # 3. 雪が来 -> 雪が降る
        new_jp = new_jp.replace('雪がたくさん来ました', '雪がたくさん降りました')
        new_jp = new_jp.replace('雪がたくさん来て', '雪がたくさん降って')
        new_jp = new_jp.replace('雪が来て', '雪が降って')
        new_jp = new_jp.replace('雪が来ると', '雪が降ると')

        # 4. 電話が来 -> 電話がかかってきた
        new_jp = new_jp.replace('電話が来ました', '電話がかかってきました')

        # 5. 医師先生 -> お医者さん
        new_jp = re.sub(r'医師先生が', 'お医者さんが', new_jp)
        new_jp = re.sub(r'医師先生、', '先生、', new_jp)

        # 6. 応急室 -> 救急室
        new_jp = new_jp.replace('応急室', '救急室')

        # 7. 너 examples: あなた -> きみ in casual contexts (friend/peer dialogue)
        if w == '너':
            # Keep あなた for formal sounding questions, use きみ for clearly casual
            new_jp = new_jp.replace('あなたは今どこにいますか？', 'きみは今どこにいるの？')
            new_jp = new_jp.replace('あなたのおかげで問題が解決しました。', 'きみのおかげで問題が解決したよ。')
            new_jp = new_jp.replace('今日は顔色が悪そうだよ。', '今日は顔色悪そうだよ。')
            new_jp = new_jp.replace('もう少し自信を持たなきゃ。', 'もっと自信を持ちなよ。')
            new_jp = new_jp.replace('あなたも一緒に行きますか？', 'きみも一緒に行く？')
            new_jp = new_jp.replace('あなたはどんな食べ物が好きですか？', 'きみはどんな食べ物が好き？')
            new_jp = new_jp.replace('明日の時間はありますか？', '明日時間ある？')
            new_jp = new_jp.replace('一時間待ってたよ', '1時間も待ってたよ')

        # 8. 누가 examples: awkward translations
        if w == '누가':
            new_jp = new_jp.replace('誰が食べ物をもたらしますか？', '誰が食べ物を持ってきますか？')
            new_jp = new_jp.replace('誰がこの宿題を助けることができますか？', '誰かこの宿題を手伝ってくれますか？')
            new_jp = new_jp.replace('誰が私のカップを破ったのですか？', '誰が私のカップを割ったのですか？')
            new_jp = new_jp.replace('誰が財布を失ったのですか？', '誰が財布をなくしたのですか？')

        # 9. 누구 examples: unnatural translations
        if w == '누구':
            new_jp = new_jp.replace('そこに誰ですか？', 'どちら様ですか？')
            new_jp = new_jp.replace('この本を誰に与えますか？', 'この本は誰にあげますか？')
            new_jp = new_jp.replace('誰をチーム長に選びますか？', '誰をリーダーに選びますか？')

        # 10. 누나 examples
        if w == '누나':
            new_jp = new_jp.replace('今日は姉のように買い物に行きます。', '今日は姉と一緒に買い物に行きます。')
            new_jp = new_jp.replace('姉がテストをよく見てほしいです。', '姉がテストでいい点を取ってほしいです。')
            new_jp = new_jp.replace('姉がソウルによく知って道を教えてくれました。', '姉がソウルのことをよく知っていて道を教えてくれました。')
            new_jp = new_jp.replace('姉、宿題を助けてください。', '姉ちゃん、宿題を手伝って。')

        # 11. 눕다 examples
        if w == '눕다':
            new_jp = new_jp.replace('医者が検査するために横になったと言いました。', '医者が検査のために横になるよう言いました。')
            new_jp = new_jp.replace('ベッドに横になって本を読んでください。', 'ベッドに横になって本を読んでいます。')
            new_jp = new_jp.replace('ヨガの最後の動作は静かに横たわっています。', 'ヨガの最後のポーズは静かに横になることです。')

        # 12. 눈싸움: 목을 束ねました -> 雪玉を作りました
        if w == '눈싸움':
            new_jp = new_jp.replace('雪合戦をしようと目を束ねました。', '雪合戦をしようと雪玉を作りました。')
            new_jp = new_jp.replace('雪が来たから雪合戦するの？', '雪が降ったから雪合戦しようか？')
            new_jp = new_jp.replace('雪合戦チームを分けて遊んだ。', '雪合戦のチームを分けて遊びました。')

        # 13. 눈사람 examples
        if w == '눈사람':
            new_jp = new_jp.replace('雪がたくさん来て雪だるまを作りました。', '雪がたくさん降ったので雪だるまを作りました。')
            new_jp = new_jp.replace('私たちが作った雪だるまの名前は何ですか？', '私たちが作った雪だるまの名前、何にしようか？')

        # 14. 눈 (topik_2 word) snow/eye confusion
        if w == '눈':
            new_jp = new_jp.replace('今朝は雪がたくさん来ました。', '今朝は雪がたくさん降りました。')
            new_jp = new_jp.replace('雪が来ると、滑りやすいので注意してください。', '雪が降ると滑りやすいので注意してください。')

        # 15. 높다 examples
        if w == '높다':
            new_jp = new_jp.replace('今回の試験で高いスコアを受けました。', '今回のテストで高い点数を取りました。')
            new_jp = new_jp.replace('音楽音が高すぎて耳が痛い', '音楽の音が大きすぎて耳が痛いです。')
            new_jp = new_jp.replace('この山は高くて上がりにくいです。', 'この山は高くて登るのが大変です。')

        # 16. 놓다 examples
        if w == '놓다':
            new_jp = new_jp.replace('バッグを机の上に置きます。', 'バッグを机の上に置いてください。')

        # 17. 몸살 examples: 体の肉 is completely wrong (mistranslation of 몸살)
        if w == '몸살':
            new_jp = new_jp.replace('体の肉で数日間家で休んだら良かったです。', '体のだるさで数日間家で休んだら良くなりました。')
            new_jp = new_jp.replace('体の肉には暖かいお茶を飲んで薬を食べるのが好きです。', 'だるさには温かいお茶を飲んで薬を飲むのがいいです。')

        # 18. 많이: 今日は雪がたくさん来ました -> 降りました
        if w == '많이':
            new_jp = new_jp.replace('今日は雪がたくさん来ました。', '今日は雪がたくさん降りました。')

        # 19. 돌아오다: マート + 電話が来
        if w == '돌아오다':
            new_jp = new_jp.replace('マートから戻るとすぐに電話が来ました。', 'スーパーから帰ったらすぐに電話がかかってきました。')

        # 20. 매주: 章を見ています -> 買い物をしています
        if w == '매주':
            new_jp = new_jp.replace('毎週日曜日にマートに行って章を見ています。', '毎週日曜日にスーパーに行って買い物をしています。')

        # 21. 머리: 薬を食べました -> 飲みました
        if w == '머리':
            new_jp = new_jp.replace('頭が痛くて薬を食べました。', '頭が痛くて薬を飲みました。')

        # 22. 목: 医師先生が首を見て -> お医者さんが喉を診て
        if w == '목':
            new_jp = new_jp.replace('医師先生が首を見て薬を処方してくれました。', 'お医者さんが喉を診て薬を処方してくれました。')

        # 23. 몸살: 따라서 약을 먹었다 -> 従って薬を飲んだ
        if w == '따라서' or w == '따르다':
            new_jp = new_jp.replace('医師の指示に従って薬を食べた。', '医師の指示に従って薬を飲みました。')

        # 24. General: 薬を食べ anywhere
        if '약을 먹' in ko or '약을 먹었' in ko:
            new_jp = new_jp.replace('薬を食べて', '薬を飲んで')
            new_jp = new_jp.replace('薬を食べる', '薬を飲む')
            new_jp = new_jp.replace('薬を食べ', '薬を飲')

        # 25. 넘어지다: 倒れる -> 転ぶ
        if w == '넘어지다':
            new_jp = new_jp.replace('倒れました', '転びました')
            new_jp = new_jp.replace('倒れて', '転んで')
            new_jp = new_jp.replace('倒れた', '転んだ')
            new_jp = new_jp.replace('倒れる', '転ぶ')
            # 子供が階段から倒れて -> 転んで
            new_jp = new_jp.replace('子供が階段から倒れて膝を傷つけました', '子供が階段で転んで膝を痛めました')
            # 途中でおばあちゃんが倒れて -> つまずいて
            new_jp = new_jp.replace('途中でおばあちゃんが倒れて助けました', '道でおばあさんが転んだので助けてあげました')

        # 26. 느리다 examples:
        if w == '느리다':
            new_jp = new_jp.replace('おばあちゃんは歩くのが遅いので、助けてください。', 'おばあちゃんは歩くのが遅いので手伝ってあげます。')
            new_jp = new_jp.replace('反応が遅いとゲームでやりやすいです。', '反応が遅いとゲームで負けやすいです。')

        # 27. 느낌 examples
        if w == '느낌':
            new_jp = new_jp.replace('初めて会った時はいい感じをいただきました。', '初めて会ったとき、いい印象を受けました。')

        # 28. 늘다 examples
        if w == '늘다':
            new_jp = new_jp.replace('新しいことは最初に遅くなるしかありません。', '新しいことは最初は遅くて当然です。')
            new_jp = new_jp.replace('毎日練習するので韓国語の実力がたくさん増えました。', '毎日練習したので韓国語の実力がとても伸びました。')

        # 29. 늘 examples
        if w == '늘':
            new_jp = new_jp.replace('両親がいつも健康になりたいです。', '両親にはいつも健康でいてほしいです。')
            new_jp = new_jp.replace('いつも幸せです。', 'いつもお幸せに。')

        # 30. 노래방 examples - ノレバン（カラオケ）redundant
        if w == '노래방':
            new_jp = new_jp.replace('初めて韓国のノレバン（カラオケ）に行ってみたのですが、本当に楽しかったです。',
                                     '初めて韓国のカラオケ（ノレバン）に行ってみましたが、本当に楽しかったです。')

        # 31. 뉴스 examples: ニュースでニュースを
        if w == '뉴스':
            new_jp = new_jp.replace('今日のニュースで大きな事故のニュースを聞きました。', '今日のニュースで大きな事故があったと聞きました。')

        # 32. 내일: 明日の試験があり、今夜勉強しなければなりません
        # -> 明日試験があるので、今夜勉強しなければなりません
        if w == '내일':
            new_jp = new_jp.replace('明日の試験があり、今夜勉強しなければなりません。', '明日試験があるので、今夜勉強しなければなりません。')
            new_jp = new_jp.replace('明日までにこのレポートを送信する必要があります。', '明日までにこのレポートを提出する必要があります。')

        # 33. 냄비: 味噌チゲを鍋に煮込んだ。 -> 煮込みました
        if w == '냄비':
            new_jp = new_jp.replace('味噌チゲを鍋に煮込んだ。', '味噌チゲを鍋で煮込みました。')
            new_jp = new_jp.replace('コーヒーに砂糖を2杯入れた。', 'コーヒーに砂糖を2さじ入れました。')
            new_jp = new_jp.replace('新しい鍋を一つ買うべきです。', '新しい鍋を一つ買わなければなりません。')

        # 34. 넘다 examples - naturalness
        if w == '넘다':
            new_jp = new_jp.replace('もう深夜が過ぎました。', 'もう真夜中を過ぎました。')
            new_jp = new_jp.replace('この商品は販売量が万個を超えました。', 'この商品は1万個以上売れました。')

        # 35. 녹차: マートで買いました -> スーパーで (already done by general rule above)

        # 36. 달걀: マートで卵一枚を買いました -> one pack/egg
        if w == '달걀':
            new_jp = new_jp.replace('マートで卵一枚を買いました。', 'スーパーで卵を一パック買いました。')

        # 37. 닭고기: チキンパック -> 鶏肉
        if w == '닭고기':
            new_jp = new_jp.replace('マートでチキンパックを買ってきました。', 'スーパーで鶏肉を買ってきました。')

        # 38. 동네: 近所にマート、病院、学校があります -> スーパー
        # (already handled by general マート rule)

        # 39. 마늘: カンニンニク -> ニンニク
        if w == '마늘':
            new_jp = new_jp.replace('マートでカンニンニクを買いました。', 'スーパーでにんにくを買いました。')

        # 40. 로션: マートで体に塗るローション -> スーパーで (done)

        # 41. 다녀오다: マートに行きます -> スーパーに行きます (done)

        # 42. 높은 점수를 받았어요 score
        if w == '높다':
            new_jp = new_jp.replace('今回の試験で高いスコアを受けました。', '今回のテストで高い点数を取りました。')

        # 43. 누구에게 줄 거예요 -> あげますか
        if w == '누구':
            new_jp = new_jp.replace('この本を誰にあげますか？', 'この本は誰にあげますか？')

        # 44. 超人種 -> インターホン (초인종 = doorbell/intercom)
        new_jp = new_jp.replace('超人種を押したが誰も出てこなかった。', 'インターホンを押したのに誰も出てこなかった。')

        # 45. 긴급버튼 -> 緊急ボタンを押すと役に立ちます -> 助けが来ます
        new_jp = new_jp.replace('緊急ボタンを押すと役に立ちます。', '緊急ボタンを押すと助けが来ます。')

        # 46. 공원が広くて散歩するのが好きです -> 散歩しやすいです
        if w == '넓다':
            new_jp = new_jp.replace('公園が広くて散歩するのが好きです。', '公園が広くて散歩しやすいです。')
            new_jp = new_jp.replace('出退勤時間には車がゆっくり行きます。', '通勤・退勤時間は車がゆっくりしか進みません。')

        # 47. 도와드렸어요 -> 도와드렸어요 correct but jp translation
        if w == '넘어지다':
            new_jp = new_jp.replace('道でおばあさんが転んだので助けてあげました。', '道でおばあさんが転んでいたので助けてあげました。')

        if new_jp != jp:
            ex['jp'] = new_jp
            fix_count += 1

# Also fix meaning for 몸살 examples that don't reference the correct meaning
for word in data2['words']:
    if word['word'] == '몸살':
        for ex in word['examples']:
            new_jp = ex['jp']
            old_jp = new_jp
            new_jp = new_jp.replace('体の肉', '体のだるさ')
            new_jp = new_jp.replace('薬を食べるのが好きです', '薬を飲むのがいいです')
            if new_jp != old_jp:
                ex['jp'] = new_jp
                fix_count += 1

print(f'Total fixes applied to topik_2: {fix_count}')

with open('D:/MakingApps/Youtube/Hellowords/data/TOPIK/JP/topik_2.json', 'w', encoding='utf-8') as f:
    json.dump(data2, f, ensure_ascii=False, indent=2)

print('topik_2.json saved successfully.')
