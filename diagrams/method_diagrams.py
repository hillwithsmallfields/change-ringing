#!/usr/bin/env python3

import os

SIZE = 16
SPACING = SIZE/4

POSITIONS = {
    'p1': SPACING * 1,
    'p2': SPACING * 2,
    'p3': SPACING * 3,
    'p4': SPACING * 4,
}

SQUARE_DOWN='''
  <g transform="translate(%%d %%d)">
    <rect width="%(p4)d" height="%(p4)d" x="0" y="0" fill="lightgrey"/>
    <path d="M %(p1)d 0 L 0 %(p1)d
             M %(p2)d 0 L 0 %(p2)d
             M %(p3)d 0 L 0 %(p3)d
             M %(p4)d 0 L 0 %(p4)d
             M %(p1)d %(p4)d L %(p4)d %(p1)d
             M %(p2)d %(p4)d L %(p4)d %(p2)d
             M %(p4)d %(p3)d L %(p3)d %(p4)d" stroke="grey" stroke-width="1"/>
  </g>
''' % POSITIONS

SQUARE_UP='''
  <g transform="translate(%%d %%d)">
    <rect width="%(p4)d" height="%(p4)d" x="0" y="0" fill="grey"/>
    <path d="M %(p3)d 0 L %(p4)d %(p1)d
             M %(p2)d 0 L %(p4)d %(p2)d
             M %(p1)d 0 L %(p4)d %(p3)d
             M 0 0 L %(p4)d %(p4)d
             M 0 %(p1)d L %(p3)d %(p4)d
             M 0 %(p2)d L %(p2)d %(p4)d
             M 0 %(p3)d L %(p1)d %(p4)d" stroke="lightgrey" stroke-width="1"/>
  </g>
''' % POSITIONS

class Bell:

    def __init__(self, start, horizontal=False, colour="blue"):
        self.horizontal = horizontal
        self.x = 0 if horizontal else start-1
        self.y = start-1 if horizontal else 0
        self.line = [(self.x, self.y)]
        self.colour = colour

    def place_min(self):
        return min(x if self.horizontal else y for x, y in self.line)

    def place_max(self):
        return max(y if self.horizontal else x for x, y in self.line)

    def down(self, n=1):
        if self.horizontal:
            self.y += n
            self.x += n
        else:
            self.x -= n
            self.y += n
        self.line.append((self.x, self.y))
        return self

    def place(self, n=1):
        if self.horizontal:
            self.x += n
        else:
            self.y += n
        self.line.append((self.x, self.y))
        return self

    def up(self, n=1):
        if self.horizontal:
            self.y -= n
            self.x += n
        else:
            self.x += n
            self.y += n
        self.line.append((self.x, self.y))
        return self

    def render(self):
        return ('''<path d="M %d %d ''' % (self.line[0][0] * SIZE, self.line[0][1] * SIZE)
                + ' '.join("L %d %d" % (p[0] * SIZE, p[1] * SIZE) for p in self.line[1:])
                + '''" stroke="%s" stroke-width="3" fill="none" transform="translate(%d %d)"/>''' % (self.colour, SIZE / 2, SIZE / 2))

def svg(width, height, text):
    return ("""<svg width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">\n""" % (width * SIZE, height * SIZE)
            + text
            + """</svg>""")

def checker(width, height):
    return "".join((SQUARE_UP if x%2 == y%2 else SQUARE_DOWN) % (x * SIZE, y * SIZE)
                   for x in range(width)
                   for y in range(height))

def from_moves(start, moves, **kwargs):
    bell = Bell(start, **kwargs)
    for move in moves:
        match move:
            case '\\' | 'u' | '+': bell = bell.up()
            case '/' | 'd' | '-': bell = bell.down()
            case '|' | 'p' | '=': bell = bell.place()
    rows = len(moves) + 1
    columns = bell.place_max()
    print(rows, "rows, and", columns, "columns")
    return svg(rows, columns,
               (checker(rows, columns)
                + bell.render()))

def diagram(filename, contents):
    full_name = os.path.join("/tmp/diagrams", filename)
    os.makedirs(os.path.dirname(full_name), exist_ok=True)
    print("writing", full_name)
    with open(full_name, 'w') as output:
        output.write(contents)

def two_bells_hunting(width):
    return svg(width, width*2,
               (checker(width, width*2)
                + Bell(1, colour="red").up(width-1).place().down(width-1).render()
                + Bell(2).down().place().up(width-1).place().down(width-3).render()))

if __name__ == "__main__":
    diagram("hunt.svg", two_bells_hunting(6))
    diagram("place-same-direction.svg",
            svg(6, 7,
                (checker(6, 7)
                 + Bell(1).up(3).place().up(2).render())))
    diagram("point.svg",
            svg(6, 7,
                (checker(6, 7)
                 + Bell(1).up(3).down(3).render())))
    diagram("just-places.svg",
            svg(8, 4,
                (checker(8, 4)
                 + Bell(1, horizontal=True).down(2).place().up().place().down(2).render())))
    diagram("place-dodge-place.svg",
            from_moves(1, "++=-+-=++", horizontal=True))
