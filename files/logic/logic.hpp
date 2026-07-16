// Demetre Seturidze
// Chess
// Logic

#include<cstddef>
#include<concepts>
#include<iostream>
#include<memory>
#include<stdexcept>
#include<set>
#include<unordered_map>
#include<vector>
#include"json.hpp"

typedef unsigned short index_t;
typedef signed short arith_t;
typedef float value_t;
using json = nlohmann::json;

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
    struct Span;

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
    using Action = structs::Tuple<structs::Index<n>, 2>;

    template<index_t n, index_t p>
    struct Instance;

    template<index_t n, index_t p>
    struct Set;
}

template<typename T, index_t n>
void to_json(json& j, const structs::Tuple<T, n>& v);

template<typename T, index_t n>
void from_json(const json& j, structs::Tuple<T, n>& v);


/*
template<index_t n>
void to_json(json& j, const moves::Move<n>& m);

template<index_t n>
void from_json(const json& j, moves::Move<n>& m);


template<index_t n>
void to_json(json& j, const moves::Figure<n>& f);

template<index_t n>
void from_json(const json& j, moves::Figure<n>& f);
*/

template<index_t n, index_t p>
void to_json(json& j, const game::Instance<n, p>& g);

template<index_t n, index_t p>
void from_json(json& j, game::Instance<n, p>& g);