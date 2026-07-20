// Demetre Seturidze
// Chess
// Logic

#ifndef LOGIC
#define LOGIC 

#include<cstddef>
#include<concepts>
#include<iostream>
#include<memory>
#include<stdexcept>
#include<set>
#include<chrono>
#include<unordered_map>
#include<vector>
#include"json.hpp"

using index_t = unsigned short;
using arith_t = signed short;
using value_t = double;
using json = nlohmann::json;

using timer = std::chrono::system_clock;
using duration = std::chrono::duration<double>;
using timestamp = timer::time_point;

template <typename T>
using sptr = std::shared_ptr<T>;

template <typename T>
using uptr = std::unique_ptr<T>;

const char* indent = "  ";

namespace structs {
    template<typename T, index_t n>
    struct Tuple;
    
    template<typename T, index_t n>
    void to_json(json& j, const structs::Tuple<T, n>& v);

    template<typename T, index_t n>
    void from_json(const json& j, structs::Tuple<T, n>& v);


    template<index_t n>
    using Tup = Tuple<index_t, n>;
 
    template <typename T, index_t n>
    struct Grid;

    template<index_t n>
    struct Vector;
    
    template<index_t n>
    void to_json(json& j, const structs::Vector<n>& v);

    template<index_t n>
    void from_json(const json& j, structs::Vector<n>& v);



    template<index_t n>
    struct Index;

    template <index_t n>
    struct BitMap;

    template <typename T, index_t n>
    struct PointerMap;
}

namespace moves {
    using namespace structs; 

    template<index_t n>
    struct Move;

    template<index_t n>
    using MoveMap = PointerMap<const Move<n>, n>;

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

    enum Status : char {
        UNBEGUN = '0', ONGOING, PROMOTING, CHECKMATE, STALEMATE, TIMEOUT, DRAW
    };

    template<index_t n>
    using Board = structs::Grid<std::shared_ptr<Piece<n>>, n>;

    template<index_t n, index_t p>
    struct Instance;

    template<index_t n, index_t p>
    struct SerializableInstance;

    template<index_t n, index_t p>
    void to_json(json& j, const game::SerializableInstance<n, p>& g);

    template<index_t n, index_t p>
    void from_json(json& j, game::SerializableInstance<n, p>& g);


    template<index_t n, index_t p>
    struct Set;
}




#endif