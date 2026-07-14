// Demetre Seturidze
// Chess
// Moves

#include"logic.hpp"

template<index_t n>
struct moves::Move{
    ~Move() {
        if (this -> directions != nullptr){
            delete[] (this -> directions);
            this -> directions = nullptr;
        }
    }

    private:
        structs::Vector<n>* directions;
        structs::Vector<n>* capture_displacement;
        
        size_t num_directions;
        bool captures;
        bool moves;
        
        Move(structs::Vector<n>* directions, size_t num_directions, bool captures, bool moves, structs::Vector<n>&& capture_displacement) : directions(directions), num_directions(num_directions), captures(captures), moves(moves), capture_displacement(capture_displacement) {}
};

