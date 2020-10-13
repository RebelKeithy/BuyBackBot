from bisect import bisect


class OCRChar:
    def __init__(self, char, width, certainty, position):
        self.char = char
        self.width = width
        self.certainty = certainty
        self.position = position

    def __str__(self):
        return f'"{self.char}", {self.position}, {self.certainty}'


class OCRText:
    def __init__(self):
        self.chars = []

    def add_char(self, char):
        self.chars.append(char)
        self.chars.sort(key=lambda x: x.position)

    def remove_overlapping(self):
        overlapping = self._get_overlapping()
        while overlapping:
            weakest = min((self.chars[i].certainty, i) for i in overlapping)[1]
            print(f"Removing: {self.chars[weakest]}")
            del self.chars[weakest]
            self.debug_print()
            overlapping = self._get_overlapping()

    def _get_overlapping(self):
        ALLOWED_OVERLAP = 1
        overlapping = set()
        for i, char in enumerate(self.chars[:-1]):
            if char.position + char.width > self.chars[i+1].position + ALLOWED_OVERLAP:
                overlapping.add(i)
                overlapping.add(i+1)
        return overlapping

    def debug_print(self):
        print(', '.join([f'({c})' for c in self.chars]))

    def __str__(self):
        return ''.join(c.char for c in self.chars)
