from rank_bm25 import BM25Plus
from Levenshtein import jaro_winkler as similarity


def search(query):
    query = query.split(" ")
    subquery = []
    subquery += query
    query.clear()

    for item in subquery:
        query.append(item.replace('\n', ''))

    common = 0
    counter = 0

    for item in query:
        for word in corpus:
            if item in exceptions:
                return False
            if len(item) < 2:
                continue
            if item.lower().find(word) != -1:
                return True
                #counter += 1
            if similarity(item, word) > 0.8:
                common += similarity(item, word)
            #counter += 1

    bm25 = BM25Plus(curses)
    if (" ".join(bm25.get_top_n(query, curses, n=1)[0])) != 'заглушка':
        common += 1

    common /= 10      #среднее требует доработки
    if common > 0.2:
        return True
    if (common > 0.08) and (common < 0.2):
        return True
    if common < 0.08:
        return False

corpus = [
    "блять", "сука", "пиздец", "уебок", "тварь", "хуй", "пизда", "ебать", "ёбанный", "гомик",
    "блядь", "говно", "мудак", "пидор", "ебля", "ёб", "ебало", "жопа", "ебля",
    "ахуеть", "охуеть", "гандон", "гондон", "падла", "падалюка", "дерьмо", "залупа"]

curses = ['сын собаки', 'от тебя воняет', 'мразь', 'заглушка']
curses = [doc.split(" ") for doc in curses]

exceptions = ['за баллы', 'гандольер']

query = '''
Вы знаете, ваш этот Максим, тот еще сын ебливой собаки, но признаться честно, другого выбора у нас нет
'''

'''
Вы знаете, ваш этот Максим, тот еще сын ебливой собаки, но признаться честно, другого выбора у нас нет
яркое солнышко светило в окно ивана, пронизывая тонкую тюль своими яркими желтыми лучами
Автор пидор
'''
