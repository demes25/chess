// Demetre Seturidze
// Chess
// Logic

#include<cstddef>
#include<concepts>
#include<iostream>
#include<memory>
#include<stdexcept>
#include<set>
#include<vector>

typedef unsigned short index_t;
typedef signed short arith_t;
typedef float value_t;

namespace structs {
    template<typename T, index_t n>
    struct Tuple;

    template <typename T, index_t n>
    struct Grid;

    template<index_t n>
    struct Index;

    template<index_t n>
    struct Vector;


    template <index_t n>
    struct BitMap;
}

namespace moves {
    template<index_t n>
    struct Move;
    
    template<index_t n>
    struct Discrete;

    template<index_t n>
    struct Leap;

    template<index_t n>
    struct Spanning;

    template<index_t n>
    struct Compound;

    template<index_t n>
    struct Castle;  

    template<index_t n>
    struct Figure;
}

namespace game {
    template<index_t n>
    struct Piece;

    template<index_t n>
    struct Player;

    template<index_t n>
    using MoveRecord = structs::Tuple<structs::Index<n>, 2>;

    template<index_t n, index_t p>
    struct Game;

    template<index_t n, index_t p>
    struct Set;
}