
class Vector2:
    '''A class representing a two-dimensional vector with coordinates x and y.'''
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    def __mul__(self, value):
        if isinstance(value, Vector2):
            return self.dot(value)
        return Vector2(self.x * value, self.y * value)
    __rmul__ = __mul__
    def __truediv__(self, value):
        return Vector2(self.x / value, self.y * value)
    def __floordiv__(self, value):
        return Vector2(self.x // value, self.y // value)

    def dot(self, other):
        '''Returns the dot product of two Vector2 instances. Can also be accessed with the syntax a * b.'''
        return self.x * other.x + self.y * other.y

    def __iter__(self):
        return iter((self.x, self.y))
    def __str__(self):
        return str((self.x, self.y))