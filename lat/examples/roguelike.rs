use lat::lat;

lat! { r##"
// ---------- CONSTANTS ----------
MAP_W: integer = 12
MAP_H: integer = 8
MAP_SIZE: integer = 96

TILE_FLOOR: integer = 0
TILE_WALL: integer = 1
TILE_PLAYER: integer = 2
TILE_GOBLIN: integer = 3
TILE_POTION: integer = 4
TILE_STAIRS: integer = 5

// ---------- GLOBAL STATE ----------
map: vec<integer>[96]

// Player
px: integer
py: integer
php: integer
pxp: integer

// Monsters (max 3)
mx: vec<integer>[3]
my: vec<integer>[3]
mhp: vec<integer>[3]
malive: vec<integer>[3]
mcount: integer

// Items (max 3)
ix: vec<integer>[3]
iy: vec<integer>[3]
ialive: vec<integer>[3]
icount: integer

// Game state
gturn: integer
gover: integer
gwon: integer

// Random
rseed: integer = 12345

// ---------- RANDOM ----------
munus rand() -> integer {
    rseed = (rseed * 1103515245 + 12345) % 2147483648
    si rseed < 0 { rseed = rseed + 2147483648 }
    reditus rseed
}

munus rrange(lo: integer, hi: integer) -> integer {
    reditus lo + (rand() % (hi - lo + 1))
}

// ---------- MAP ----------
munus midx(x: integer, y: integer) -> integer {
    reditus y * MAP_W + x
}

munus init_map() {
    i: integer
    enim(i = 0; i < MAP_SIZE; i = i + 1) {
        map[i] = TILE_WALL
    }
}

munus carve(rx: integer, ry: integer, rw: integer, rh: integer) {
    y: integer
    x: integer
    enim(y = ry; y < ry + rh; y = y + 1) {
        enim(x = rx; x < rx + rw; x = x + 1) {
            si x > 0 et x < MAP_W - 1 et y > 0 et y < MAP_H - 1 {
                map[midx(x, y)] = TILE_FLOOR
            }
        }
    }
}

munus hcorr(x1: integer, x2: integer, y: integer) {
    i: integer
    si x1 < x2 {
        enim(i = x1; i <= x2; i = i + 1) {
            map[midx(i, y)] = TILE_FLOOR
        }
    } aliter {
        enim(i = x2; i <= x1; i = i + 1) {
            map[midx(i, y)] = TILE_FLOOR
        }
    }
}

munus vcorr(y1: integer, y2: integer, x: integer) {
    i: integer
    si y1 < y2 {
        enim(i = y1; i <= y2; i = i + 1) {
            map[midx(x, i)] = TILE_FLOOR
        }
    } aliter {
        enim(i = y2; i <= y1; i = i + 1) {
            map[midx(x, i)] = TILE_FLOOR
        }
    }
}

// ---------- RENDER ----------
munus tchar(t: integer) -> filum {
    si t == TILE_WALL { reditus "#" }
    si t == TILE_FLOOR { reditus "." }
    si t == TILE_PLAYER { reditus "@" }
    si t == TILE_GOBLIN { reditus "g" }
    si t == TILE_POTION { reditus "!" }
    si t == TILE_STAIRS { reditus ">" }
    reditus "?"
}

munus draw() {
    y: integer
    x: integer
    t: integer
    enim(y = 0; y < MAP_H; y = y + 1) {
        row: filum = ""
        enim(x = 0; x < MAP_W; x = x + 1) {
            t = map[midx(x, y)]
            si x == px et y == py {
                row = row + "@"
            } aliter {
                row = row + tchar(t)
            }
        }
        imprimo(row)
    }
    imprimo("HP: ")
    imprimo(php)
    imprimo(" | Turn: ")
    imprimo(gturn)
    imprimo("n/s/e/w=move, q=quit")
}

// ---------- ENTITIES ----------
munus spawn_monsters() {
    i: integer
    mcount = 0
    enim(i = 0; i < 3; i = i + 1) {
        x: integer = rrange(2, MAP_W - 3)
        y: integer = rrange(2, MAP_H - 3)
        si map[midx(x, y)] == TILE_FLOOR {
            mx[i] = x
            my[i] = y
            mhp[i] = 2
            malive[i] = 1
            mcount = mcount + 1
        }
    }
}

munus spawn_items() {
    i: integer
    icount = 0
    enim(i = 0; i < 3; i = i + 1) {
        x: integer = rrange(2, MAP_W - 3)
        y: integer = rrange(2, MAP_H - 3)
        si map[midx(x, y)] == TILE_FLOOR {
            ix[i] = x
            iy[i] = y
            ialive[i] = 1
            icount = icount + 1
        }
    }
}

munus place_stairs() {
    x: integer = rrange(2, MAP_W - 3)
    y: integer = rrange(2, MAP_H - 3)
    si map[midx(x, y)] == TILE_FLOOR {
        map[midx(x, y)] = TILE_STAIRS
    }
}

// ---------- MOVEMENT ----------
munus is_walkable(x: integer, y: integer) -> integer {
    si x < 0 aut x >= MAP_W aut y < 0 aut y >= MAP_H {
        reditus 0
    }
    si map[midx(x, y)] == TILE_WALL {
        reditus 0
    }
    reditus 1
}

munus move_player(dx: integer, dy: integer) {
    nx: integer = px + dx
    ny: integer = py + dy
    si is_walkable(nx, ny) == 0 {
        reditus
    }
    px = nx
    py = ny

    // Check stairs
    si map[midx(px, py)] == TILE_STAIRS {
        imprimo("You found the stairs! You win!")
        gturn = gturn + 1
        gwon = 1
        gover = 1
        reditus
    }

    // Check items
    i: integer
    enim(i = 0; i < 3; i = i + 1) {
        si ialive[i] == 1 et ix[i] == px et iy[i] == py {
            php = php + 5
            ialive[i] = 0
            imprimo("Potion! HP +5")
        }
    }

    // Check monsters
    enim(i = 0; i < 3; i = i + 1) {
        si malive[i] == 1 et mx[i] == px et my[i] == py {
            imprimo("Combat!")
            mhp[i] = mhp[i] - 1
            si mhp[i] <= 0 {
                malive[i] = 0
                pxp = pxp + 10
                imprimo("Monster defeated! XP +10")
            } aliter {
                php = php - 1
                imprimo("You hit, monster hits back! HP -1")
            }
            si php <= 0 {
                imprimo("You died!")
                gover = 1
            }
        }
    }

    gturn = gturn + 1
}

munus move_monsters() {
    i: integer
    enim(i = 0; i < 3; i = i + 1) {
        si malive[i] == 1 {
            dx: integer = 0
            dy: integer = 0
            si mx[i] < px { dx = 1 }
            si mx[i] > px { dx = -1 }
            si my[i] < py { dy = 1 }
            si my[i] > py { dy = -1 }

            nx: integer = mx[i] + dx
            ny: integer = my[i] + dy
            si is_walkable(nx, ny) == 1 {
                mx[i] = nx
                my[i] = ny
            }

            si mx[i] == px et my[i] == py {
                imprimo("Monster attacks!")
                php = php - 1
                si php <= 0 {
                    imprimo("You died!")
                    gover = 1
                }
            }
        }
    }
}

// ---------- GAME LOOP ----------
munus process_input() -> integer {
    cmd: filum = legeres()
    si cmd == "n" {
        move_player(0, -1)
        reditus 2
    }
    si cmd == "s" {
        move_player(0, 1)
        reditus 2
    }
    si cmd == "e" {
        move_player(1, 0)
        reditus 2
    }
    si cmd == "w" {
        move_player(-1, 0)
        reditus 2
    }
    si cmd == "q" {
        imprimo("Goodbye!")
        reditus 1
    }
    reditus 0
}

// ---------- MAIN ----------
munus main() {
    init_map()

    // 3 rooms
    carve(2, 2, 4, 3)
    carve(8, 2, 3, 3)
    carve(5, 5, 4, 2)

    // Corridors
    hcorr(5, 8, 3)
    vcorr(4, 5, 6)

    // Player start
    px = 3
    py = 3
    php = 10
    pxp = 0

    spawn_monsters()
    spawn_items()
    place_stairs()

    gturn = 0
    gover = 0
    gwon = 0

    imprimo("=== LATINIUM ROGUELIKE ===")
    imprimo("Find the stairs (>). Avoid goblins (g).")
    imprimo("Potions (!) heal you.")
    imprimo("")

    dum gover == 0 {
        draw()
        action: integer = process_input()
        si action == 1 {
            confractus
        }
        si action == 2 et gover == 0 {
            move_monsters()
        }
        imprimo("")
    }

    si gwon == 1 {
        imprimo("Victory! Turns: ")
        imprimo(gturn)
    }
}
"## }
