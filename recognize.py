from Levenshtein import jaro_winkler as similarity


def search(query):
    query = query.split(" ")
    subquery = []
    subquery += query
    query.clear()

    for item in subquery:
        query.append(item.replace('\n', ''))

    for item in query:
        for word in corpus:
            if item in exceptions:
                return False
            if len(item) < 2:
                continue
            if item.lower().find(word) != -1:
                return True
            if similarity(item, word) > 0.85:
                return True


corpus = [
    "блять", "сука", "пиздец", "уебок", "тварь", "хуй", "пизда", "ебать", "ёбанный", "гомик",
    "блядь", "говно", "мудак", "пидор", "ебля", "ёб", "ебало", "жопа", "ебля",
    "ахуеть", "охуеть", "гандон", "гондон", "падла", "падалюка", "дерьмо", "залупа", "xyй", "huy"]


exceptions = ['баллы', 'гандольер', 'матеша', 'Баллы']

