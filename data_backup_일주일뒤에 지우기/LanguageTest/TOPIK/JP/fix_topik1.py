import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('D:/MakingApps/Youtube/Hellowords/data/TOPIK/JP/topik_1.json', 'r', encoding='utf-8') as f:
    data1 = json.load(f)

fix_count = 0

for word in data1['words']:
    wid = word['id']
    w = word['word']

    # ── MEANING FIXES ──────────────────────────────────────

    if w == '간단하다' and word['meaning'] == '簡単':
        word['meaning'] = '簡単だ'; fix_count += 1

    if w == '갈아타다' and word['meaning'] == '乗り換え':
        word['meaning'] = '乗り換える'; fix_count += 1

    # 감다 in all examples = close eyes (눈을 감다), not 巻く
    if w == '감다' and word['meaning'] == '巻く':
        word['meaning'] = '（目を）閉じる'; fix_count += 1

    if w == '감사' and word['pos'] == '명사' and word['meaning'] == 'ありがとう':
        word['meaning'] = '感謝'; fix_count += 1

    if w == '감사드립니다' and word['meaning'] == 'ありがとう':
        word['meaning'] = 'ありがとうございます'; fix_count += 1

    if w == '감사하다' and word['meaning'] == 'ありがとう':
        word['meaning'] = '感謝する'; fix_count += 1

    if w == '감사합니다' and word['meaning'] == 'ありがとう':
        word['meaning'] = 'ありがとうございます'; fix_count += 1

    # 감자탕 = pork bone & potato soup, not ジャガイモ
    if w == '감자탕' and word['meaning'] == 'ジャガイモ':
        word['meaning'] = 'カムジャタン（豚骨じゃがいも鍋）'; fix_count += 1

    if w == '값' and word['meaning'] == '値':
        word['meaning'] = '値段'; fix_count += 1

    # ── EXAMPLE FIXES ──────────────────────────────────────
    for ex in word['examples']:
        ko = ex['ko']
        jp = ex['jp']
        new_jp = jp

        # 1. マート -> スーパー (Korean 마트 = supermarket, not loanword マート in JP)
        if 'マート' in new_jp and 'スマート' not in new_jp:
            new_jp = new_jp.replace('マート', 'スーパー')

        # 2. 薬を食べ -> 薬を飲む (medicine is 飲む in Japanese)
        new_jp = new_jp.replace('薬を食べています', '薬を飲んでいます')
        new_jp = new_jp.replace('薬を食べたら少し良くなりました', '薬を飲んだら少し良くなりました')
        new_jp = new_jp.replace('薬を食べてもいいわけではありません', '薬を飲んでもなかなか治りません')
        new_jp = new_jp.replace('薬を食べたら眠くなります', '薬を飲むと眠くなります')
        new_jp = new_jp.replace('薬を食べたら咳が止まりました', '薬を飲んだら咳が止まりました')
        new_jp = new_jp.replace('薬を食べて今週', '薬を飲んで今は禁酒しています')
        new_jp = new_jp.replace('薬を食べて咳が良くなりました', '薬を飲んで咳が良くなりました')
        new_jp = new_jp.replace('風邪薬は1日3回食べる必要があります', '風邪薬は1日3回飲む必要があります')
        new_jp = new_jp.replace('風邪薬を食べたら少し良くなりました', '風邪薬を飲んだら少し良くなりました')

        # 3. 電話が来ました -> 電話がかかってきました
        new_jp = new_jp.replace('電話が来ました', '電話がかかってきました')
        new_jp = new_jp.replace('電話が来て', '電話がかかってきて')

        # 4. 雪が来 -> 雪が降る
        new_jp = new_jp.replace('雪がたくさん来ました', '雪がたくさん降りました')
        new_jp = new_jp.replace('雪がたくさん来ます', '雪がたくさん降ります')
        new_jp = new_jp.replace('雪が来たら', '雪が降ったら')
        new_jp = new_jp.replace('雪が来て', '雪が降って')
        new_jp = new_jp.replace('雪が来ると', '雪が降ると')

        # 5. 雨が来 -> 雨が降る
        new_jp = new_jp.replace('雨がよく来ます', '雨がよく降ります')
        new_jp = new_jp.replace('雨が来ます', '雨が降ります')
        new_jp = new_jp.replace('雨が来て', '雨が降って')

        # 6. 医師先生 -> お医者さん / 先生
        new_jp = new_jp.replace('医師先生が胸を確認しました', 'お医者さんが胸を診てくれました')
        new_jp = new_jp.replace('医師先生が風邪と言いました', 'お医者さんが風邪だと言いました')
        new_jp = new_jp.replace('医師先生が感기약을 처방해 주셨어요', 'お医者さんが風邪薬を処方してくれました')
        new_jp = new_jp.replace('医師先生が風邪薬を処方してくれました', 'お医者さんが風邪薬を処方してくれました')
        new_jp = new_jp.replace('医師先生が腕に注射しました', 'お医者さんが腕に注射しました')
        new_jp = new_jp.replace('医師先生が毎朝体温をとります', '看護師が毎朝体温を測ります')
        new_jp = re.sub(r'医師先生が', 'お医者さんが', new_jp)
        new_jp = re.sub(r'医師先生、', '先生、', new_jp)

        # 7. 応急室 -> 救急室
        new_jp = new_jp.replace('応急室', '救急室')

        # 8. ハーブに醤油とごま油 (나물 = Korean vegetable side dish, not herb)
        new_jp = new_jp.replace('ハーブに醤油とごま油を入れました', 'ナムルに醤油とごま油を加えました')

        # 9. 감자탕 examples completely wrong - all replaced
        if w == '감자탕':
            new_jp = new_jp.replace('今夜はジャガイモを食べました', '今夜はカムジャタンを食べました')
            new_jp = new_jp.replace('ジャガイモは豚骨とジャガイモで煮込んだ汁です', 'カムジャタンは豚骨とじゃがいもで煮込んだ澄んだスープです')
            new_jp = new_jp.replace('寒い日にはジャガイモが最高です', '寒い日にはカムジャタンが最高です')
            new_jp = new_jp.replace('友達と一緒にジャガイモの家に行きました', '友達と一緒にカムジャタン屋さんに行きました')
            new_jp = new_jp.replace('夜食でじゃがいもをさせて食べました', '夜食にカムジャタンをデリバリーして食べました')
            new_jp = new_jp.replace('このジャガイモはスープが濃くて美味しいです', 'このカムジャタンはスープが濃くて美味しいです')
            new_jp = new_jp.replace('配達でジャガイモを注文しました', '配達でカムジャタンを注文しました')
            new_jp = new_jp.replace('じゃがいもは酒のおつまみとしてもいいです', 'カムジャタンはお酒のおつまみにもぴったりです')
            new_jp = new_jp.replace('初めてジャガイモを食べてみました', '初めてカムジャタンを食べてみました')
            new_jp = new_jp.replace('じゃがいもを包んで家に帰りました', 'カムジャタンを包んで家に帰りました')

        # 10. 감(柿) examples - nonsensical translations
        if w == '감':
            new_jp = new_jp.replace('熟した感覚を食べました', '熟した柿を食べました')
            new_jp = new_jp.replace('柿を乾かすと岬になります', '柿を乾かすと干し柿になります')
            new_jp = new_jp.replace('軒下に柿が渋い走っています', '軒下に柿がたわわに実っています')
            new_jp = new_jp.replace('しっかりとした感覚より渋い感があります', '固い柿より柔らかい柿の方が甘いです')
            new_jp = new_jp.replace('おばあちゃんの家庭に柿の木があります', 'おばあちゃんの家の庭に柿の木があります')
            new_jp = new_jp.replace('お店で柿の袋を買いました', 'お店で柿をひと袋買いました')

        # 11. 갑자기 - 急にいい思いがしました -> いいアイデアが浮かびました
        new_jp = new_jp.replace('急にいい思いがしました', '急にいいアイデアが浮かびました')

        # 12. 강아지 (子犬): first example uses 犬 not 子犬
        if w == '강아지' and '私の家に犬が一匹います' in new_jp:
            new_jp = new_jp.replace('私の家に犬が一匹います', '私の家に子犬が一匹います')

        # 13. 子犬が痛くて -> 具合が悪くて
        new_jp = new_jp.replace('子犬が痛くて動物病院に行きました', '子犬の具合が悪くて動物病院に行きました')

        # 14. 会社に近いカフェに来ています -> 来てください
        new_jp = new_jp.replace('私たちの会社に近いカフェに来ています', '会社の近くのカフェに来てください')

        # 15. Register fixes: plain form -> ます form (TOPIK1 should use polite forms)
        new_jp = new_jp.replace('部屋の真ん中にベッドを置いた。', '部屋の真ん中にベッドを置きました。')
        new_jp = new_jp.replace('はさみで紙を切った。', 'はさみで紙を切りました。')
        new_jp = new_jp.replace('はさみで肉を切る。', 'はさみで肉を切ります。')
        new_jp = new_jp.replace('美容師がはさみで髪を切った。', '美容師がはさみで髪を切りました。')
        new_jp = new_jp.replace('ギフト包装紙はさみで切った。', 'プレゼントの包装紙をはさみで切りました。')
        new_jp = new_jp.replace('バッグが重すぎる。', 'バッグが重すぎます。')
        new_jp = new_jp.replace('川の横でピクニックを楽しんだ。', '川のそばでピクニックを楽しみました。')
        new_jp = new_jp.replace('子犬とボールで遊んだ。', '子犬とボールで遊びました。')
        new_jp = new_jp.replace('春には黄色のクレヨンを使用しました。', '太陽を描くときに黄色のクレヨンを使いました。')

        # 16. 今日店に行ってミルクを買うよ -> 牛乳を買います
        new_jp = new_jp.replace('今日店に行ってミルクを買うよ。', '今日お店に行って牛乳を買います。')

        # 17. 価格 over-usage -> more natural expressions
        new_jp = new_jp.replace('コーヒーの価格はいくらですか？', 'コーヒーはいくらですか？')
        new_jp = new_jp.replace('このバッグの価格はいくらですか？', 'このバッグはいくらですか？')

        # 18. 불이 꺼졌어요 = 電気が消えました (not 火)
        if '갑자기 불이 꺼졌어요' in ko and '突然火が消えました' in new_jp:
            new_jp = new_jp.replace('突然火が消えました', '突然電気が消えました')

        # 19. 값 examples
        new_jp = new_jp.replace('物価を現金で出しました', '代金を現金で支払いました')
        new_jp = new_jp.replace('セール時に物価がたくさん下がります', 'セールのとき商品の値段がかなり下がります')
        new_jp = new_jp.replace('値を削ってもらいました', '値引きをお願いしました')
        new_jp = new_jp.replace('価格表に値が書いてあります', '値札に値段が書いてあります')

        # 20. 감사드립니다 examples - the word is formal honorific, examples need to match
        if w == '감사드립니다':
            new_jp = new_jp.replace('お助けいただきありがとうございます。', 'お助けいただきありがとうございます。')
            if '助けてくれてありがとう。' in new_jp:
                new_jp = new_jp.replace('助けてくれてありがとう。', 'お助けいただきありがとうございます。')
            if '先生、教えてくれてありがとう。' in new_jp:
                new_jp = new_jp.replace('先生、教えてくれてありがとう。', '先生、ご指導ありがとうございます。')
            if 'よく聞いてくれてありがとう。' in new_jp:
                new_jp = new_jp.replace('よく聞いてくれてありがとう。', 'ご清聴ありがとうございます。')
            if 'このように来てくれてありがとう。' in new_jp:
                new_jp = new_jp.replace('このように来てくれてありがとう。', 'お越しいただきありがとうございます。')
            if 'いつも助けてくれてありがとう。' in new_jp:
                new_jp = new_jp.replace('いつも助けてくれてありがとう。', 'いつもお力添えありがとうございます。')
            if '今日一緒にいただきありがとうございます。' in new_jp:
                new_jp = new_jp.replace('今日一緒にいただきありがとうございます。', '本日ご参加いただきありがとうございます。')

        # 21. 감사합니다 examples - polite forms
        if w == '감사합니다':
            if '助けてくれてありがとう。' in new_jp:
                new_jp = new_jp.replace('助けてくれてありがとう。', '助けていただきありがとうございます。')
            if '褒めてくれてありがとう。' in new_jp:
                new_jp = new_jp.replace('褒めてくれてありがとう。', 'お褒めいただきありがとうございます。')
            if '食べ物を持ってくれてありがとう。' in new_jp:
                new_jp = new_jp.replace('食べ物を持ってくれてありがとう。', '食べ物を持ってきてくれてありがとうございます。')
            if 'バスで降りてくれてありがとうと言いました' in new_jp:
                new_jp = new_jp.replace('バスで降りてくれてありがとうと言いました', 'バスを降りながら「ありがとうございます」と言いました')

        # 22. ありがとうカードを送りました -> 感謝カードを送りました
        new_jp = new_jp.replace('ありがとうカードを送りました', '感謝カードを送りました')

        # 23. 荷物を聞いてくれてありがとう -> 持って
        new_jp = new_jp.replace('荷物を聞いてくれてありがとう', '荷物を持ってくれてありがとう')

        # 24. 子犬をなでてくれました -> なでてあげました (subject is me)
        new_jp = new_jp.replace('子犬をなでてくれました。', '子犬をなでてあげました。')

        # 25. 時々頭痛が発生します -> 起きます
        new_jp = new_jp.replace('時々頭痛が発生します', '時々頭痛が起きます')

        # 26. ここで地下鉄駅は近いですか？ -> ここから
        new_jp = new_jp.replace('ここで地下鉄駅は近いですか？', 'ここから地下鉄駅は近いですか？')

        # 27. 家に帰ると、子犬が歓迎してくれます -> 喜んで迎えてくれます
        new_jp = new_jp.replace('家に帰ると、子犬が歓迎してくれます', '家に帰ると、子犬が喜んで迎えてくれます')

        # 28. 子供に風邪薬を与えました -> 飲ませました
        new_jp = new_jp.replace('子供に風邪薬を与えました', '子供に風邪薬を飲ませました')

        # 29. 風邪をひいた友人に風邪薬を与えました -> あげました
        new_jp = new_jp.replace('風邪をひいた友人に風邪薬を与えました', '風邪をひいた友人に風邪薬をあげました')

        # 30. 川沿いの自転車に乗りました -> 川沿いを自転車で走りました
        new_jp = new_jp.replace('川沿いの自転車に乗りました', '川沿いを自転車で走りました')

        # 31. 黄色いバッグが目立つ。 -> ます form
        new_jp = new_jp.replace('黄色いバッグが目立つ。', '黄色いバッグはよく目立ちます。')

        # 32. チョコレートは茶色です。 -> already natural, keep

        # 33. 이 감자탕은 국물이 진하고 -> 'カムジャタンの水は長く沸騰しなければおいしいです' is wrong
        if w == '갈비탕':
            new_jp = new_jp.replace('カルビタンは長く沸騰しなければおいしいです', 'カルビタンは長く煮込むほど美味しくなります')
            new_jp = new_jp.replace('チュソクにはカルビタンを煮込んだ。', 'チュソクにはカルビタンを煮込みました。')
            new_jp = new_jp.replace('配達でカルビタンをさせて食べました', '配達でカルビタンを注文して食べました')

        # 34. 冬に雪がたくさん来ます -> 降ります
        new_jp = new_jp.replace('冬に雪がたくさん来ます', '冬は雪がたくさん降ります')

        if new_jp != jp:
            ex['jp'] = new_jp
            fix_count += 1

print(f'Total fixes applied to topik_1: {fix_count}')

with open('D:/MakingApps/Youtube/Hellowords/data/TOPIK/JP/topik_1.json', 'w', encoding='utf-8') as f:
    json.dump(data1, f, ensure_ascii=False, indent=2)

print('topik_1.json saved successfully.')
