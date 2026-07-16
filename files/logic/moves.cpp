// Demetre Seturidze
// Chess
// Moves

#include"logic.hpp"

using namespace structs;

template<index_t n>
struct moves::Move{
    const std::unique_ptr<Vector<n>[]> directions;
    const Vector<n> capture_displacement;
    
    const size_t num_directions;
    const bool captures;
    const bool moves;

    Move(const Move&) = default;
    Move(Move&&) = default;

    ~Move() = default;

    Move& operator=(const Move&) = default;
    Move& operator=(Move&&) = default;

    const Vector<n>& operator[](index_t i) const {
        return this -> directions[i];
    }

    bool sees(const game::Instance& board, const Index<n>& position, const Index<n>& target, index_t player_index) const {
        return (
            this -> valid_occupancy(board, target, player_index) && this -> valid_square(board, position, target);
        )
    }

    
    protected:
        template<size_t k>
        Move(Tuple<Vector<n>, k> directions, bool captures, bool moves, Vector<n>&& capture_displacement) : directions(std::make_unique<Vector<n>[]>(k)), num_directions(k), captures(captures), moves(moves), capture_displacement(capture_displacement) {
            for (index_t i = 0; i < k; i++){
                this -> directions[i] = std::move(moves[i]);
            } 
        }

        template<size_t k>
        Move(Tuple<Vector<n>, k> directions, bool captures, bool moves) : directions(std::make_unique<Vector<n>[]>(k)), num_directions(k), captures(captures), moves(moves), capture_displacement(0) {
            for (index_t i = 0; i < k; i++){
                this -> directions[i] = std::move(moves[i]);
            } 
        }

        
        Move(Vector<n>* directions, size_t num_directions, bool captures, bool moves, Vector<n>&& capture_displacement) : directions(directions), num_directions(num_directions), captures(captures), moves(moves), capture_displacement(capture_displacement) {}

        virtual bool valid_occupancy(const game::Instance& board, const Index<n>& target, index_t player_index) const {
            std::shared_ptr<game::Piece> piece_at = board.map[target];
            std::shared_ptr<game::Piece> takes_at = board.map[target + this -> capture_displacement]

            if (piece_at == nullptr && takes_at == nullptr) return this -> moves;

            else if (this -> captures && takes_at != nullptr) {
                if (piece_at == takes_at || piece_at == nullptr) {
                    return takes_at -> player_index != player_index;
                }
            }

            else return false;
        }

        virtual bool valid_square(const game::Instance& board, const Index<n>& position, const Index<n>& target) const = 0;
};


template<index_t n>
struct moves::Figure {
    using MoveListPtr = std::shared_ptr<Move[]>;

    const std::string name;
    const value_t value;

    const MoveListPtr move_list;
    const MoveListPtr opener_list;

    const size_t num_moves;
    const size_t num_openers;

    const bool open_exclusive;

    static std::shared_ptr<Figure> define(const char* name, value_t value, const MoveListPtr& moves, size_t num_moves, const MoveListPtr& openers, size_t num_openers, bool open_exclusive){
        std::shared_ptr<Figure> result = std::make_shared<Figure>(name, value, moves, num_moves, openers, num_openers, open_exclusive);
        Figure::instances[name] = result;
        return result;
    }

    static std::shared_ptr<Figure> define(const std::string& name, value_t value, const MoveListPtr& moves, size_t num_moves, const MoveListPtr& openers, size_t num_openers, bool open_exclusive){
        std::shared_ptr<Figure> result = std::make_shared<Figure>(name, value, moves, num_moves, openers, num_openers, open_exclusive);
        Figure::instances[name] = result;
        return result;
    }

    static std::shared_ptr<Figure> resolve(const std::string& name) {
        return Figure::instances[name];
    }

    private:
        Figure(const std::string& name, value_t value, const MoveListPtr& moves, size_t num_moves, const MoveListPtr& openers, size_t num_openers, bool open_exclusive) : name(name), value(value), move_list(moves), num_moves(num_moves), opener_list(openers), num_openers(num_openers), open_exclusive(open_exclusive) {}
    
        static std::unordered_map<std::string, std::shared_ptr<Figure>> instances; 
};




