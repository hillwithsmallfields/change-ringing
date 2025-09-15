#!/usr/bin/env python3

SQUARE_DOWN="""
  <g transform="translate(%d %d)">
    <rect width="64" height="64" x="0" y="0" fill="lightgrey"/>
    <path d="M 16 0 L 0 16
             M 32 0 L 0 32
             M 48 0 L 0 48
             M 64 0 L 0 64
             M 16 64 L 64 16
             M 32 64 L 64 32
             M 64 48 L 48 64" stroke="grey" stroke-width="1"/>
  </g>
"""

SQUARE_UP="""
  <g transform="translate(%d %d)">
    <rect width="64" height="64" x="0" y="0" fill="grey"/>
    <path d="M 48 0 L 64 16
             M 32 0 L 64 32
             M 16 0 L 64 48
             M 0 0 L 64 64
             M 0 16 L 48 64
             M 0 32 L 32 64
             M 0 48 L 16 64" stroke="lightgrey" stroke-width="1"/>
  </g>
"""

SIZE=64

class Bell:

    def __init__(self, start, horizontal=False, colour="blue"):
        self.horizontal = horizontal
        self.x = 0 if horizontal else start-1
        self.y = start-1 if horizontal else 0
        self.line = [(self.x, self.y)]
        self.colour = colour

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
                + '''" stroke="%s" stroke-width="7" fill="none" transform="translate(%d %d)"/>''' % (self.colour, SIZE / 2, SIZE / 2))

def svg(width, height, text):
    return ("""<svg width="%d" height="%d" xmlns="http://www.w3.org/2000/svg">\n""" % (width * SIZE, height * SIZE)
            + text
            + """</svg>""")

def checker(width, height):
    return "".join((SQUARE_UP if x%2 == y%2 else SQUARE_DOWN) % (x * SIZE, y * SIZE)
                   for x in range(width)
                   for y in range(height))

def diagram(filename, width, height, contents):
    with open(filename, 'w') as output:
        output.write(contents)

def two_bells_hunting(width):
    return svg(width, width*2,
               (checker(width, width*2)
                + Bell(1, colour="red").up(width-1).place().down(width-1).render()
                + Bell(2).down().place().up(width-1).place().down(width-3).render()))

if __name__ == "__main__":
    diagram("hunt.svg", 6, 12, two_bells_hunting(6))
    diagram("place-same-direction.svg", 6, 6,
            svg(6, 7,
                (checker(6, 7)
                 + Bell(1).up(3).place().up(2).render())))
    diagram("point.svg", 6, 6,
            svg(6, 7,
                (checker(6, 7)
                 + Bell(1).up(3).down(3).render())))
    diagram("just-places.svg", 8, 4,
            svg(8, 4,
                (checker(8, 4)
                 + Bell(1, horizontal=True).down(2).place().up().place().down(2).render())))
