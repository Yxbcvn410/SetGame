import random

from SetCard import Card, CardColor, CardFill, CardShape


def check_set(c1: Card, c2: Card, c3: Card):
    return (c1.Color == c2.Color == c3.Color or c1.Color != c2.Color != c3.Color != c1.Color) and \
           (c1.Fill == c2.Fill == c3.Fill or c1.Fill != c2.Fill != c3.Fill != c1.Fill) and \
           (c1.Shape == c2.Shape == c3.Shape or c1.Shape != c2.Shape != c3.Shape != c1.Shape) and \
           (c1.Count == c2.Count == c3.Count or c1.Count != c2.Count != c3.Count != c1.Count) and \
           (c1 != c2)


def find_set(collection):
    le = len(collection)
    for i in range(le):
        for j in range(i):
            for k in range(j):
                if check_set(collection[i], collection[j], collection[k]):
                    return [i, j, k]
    return None


class GameField:
    def __init__(self):
        self.on_table = []
        self.found_sets = []
        self.deck = [Card(sh, f, col, ct) for ct in range(1, 4) for col in CardColor for f in CardFill for sh in
                     CardShape]
        self.shuffle()

    def shuffle(self):
        self.deck.extend(self.found_sets)
        self.deck.extend(self.on_table)
        self.on_table.clear()
        self.found_sets.clear()
        random.shuffle(self.deck)
        self.on_table.extend(self.deck[:12])
        del self.deck[:12]
        while find_set(self.on_table) is None:
            self.on_table.extend(self.deck[:3])
            del self.deck[:3]

    def check_set(self, i, j, k):
        return check_set(self.on_table[i], self.on_table[j], self.on_table[k])

    def find_set(self):
        return find_set(self.on_table)

    def take_set(self, i, j, k):
        for idx in (i, j, k):
            self.found_sets.append(self.on_table[idx])
        without = [self.on_table[o] for o in range(len(self.on_table)) if o not in (i, j, k)]
        if len(self.on_table) >= 15 and find_set(without) is not None or len(self.deck) == 0:
            for idx in (i, j, k):
                self.on_table[idx] = None
            self.on_table[:] = [card for card in self.on_table if card is not None]
            return
        self.on_table[i], self.on_table[j], self.on_table[k] = self.deck[:3]
        del self.deck[:3]
        while len(self.deck) != 0 and self.find_set() is None:
            self.on_table.extend(self.deck[:3])
            del self.deck[:3]

    def flip_found(self):
        random.shuffle(self.found_sets)
        self.deck.extend(self.found_sets)
        del self.found_sets[:]
        while len(self.deck) != 0 and self.find_set() is None:
            self.on_table.extend(self.deck[:3])
            del self.deck[:3]

    def __len__(self):
        return len(self.on_table)

    def size(self):
        return 3, len(self.on_table) // 3

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.on_table[item]
        if isinstance(item, tuple):
            i, j = item
            return self.on_table[i + (j - 1) * 3]
        raise TypeError()
