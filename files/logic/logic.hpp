// Demetre Seturidze
// Chess
// Logic

#include<cstddef>
#include<concepts>
#include<iostream>
#include<memory>
#include<stdexcept>

typedef unsigned short index_t;
typedef unsigned long size_t;

namespace structs {
    template<typename T, index_t n>
    struct Tuple;

    template<index_t n> 
    using Index = Tuple<index_t, n>;

    template<index_t n>
    using Vector = Tuple<index_t, n>;


    template <typename T, index_t n>
    struct Grid;

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
    struct Board;
}