// Demetre Seturidze
// Chess
// Moves

#include"logic.hpp"

using namespace structs;

template<index_t n>
struct moves::Move{
    const std::vector<Vector<n>> directions;
    const Vector<n> capture_displacement;
    
    const bool captures;
    const bool moves;

    Move(Move&&) = default;

    Move(std::vector<Vector<n>>&& directions, bool captures, bool moves, Vector<n>&& capture_displacement) : directions(directions),  captures(captures), moves(moves), capture_displacement(capture_displacement) {}

    template<size_t k>
    Move(const Tuple<Vector<n>, k>& directions, bool captures, bool moves, Vector<n>&& capture_displacement) : directions(), captures(captures), moves(moves), capture_displacement(capture_displacement) {
        for (index_t i = 0; i < k; i++){
            this -> directions.push_back(std::move(directions[i]));
        } 
    }

    ~Move() = default;

    Move& operator=(Move&&) = default;

    const Vector<n>& operator[](index_t i) const {
        return this -> directions[i];
    }

    bool sees(const game::Instance& instance, const Index<n>& position, const Index<n>& target, index_t player_index) const {
        return (
            this -> valid_occupancy(instance, target, player_index) && this -> valid_square(instance, position, target);
        )
    }

    
    protected:
        virtual bool valid_occupancy(const game::Instance& instance, const Index<n>& target, index_t player_index) const {
            const game::Piece* piece_at = instance[target];
            const game::Piece* takes_at = instance[target + this -> capture_displacement]

            if (piece_at == nullptr && takes_at == nullptr) return this -> moves;

            else if (this -> captures && takes_at != nullptr) {
                if (piece_at == takes_at || piece_at == nullptr) {
                    return takes_at -> player_index != player_index;
                }
            }

            else return false;
        }

        virtual bool valid_square(const game::Instance& instance, const Index<n>& position, const Index<n>& target) const = 0;
};


template<index_t n>
struct moves::Figure {
    const std::string name;
    const std::string key;
    const value_t value;

    const std::vector<moves::Move<n>> move_list;
    const std::vector<moves::Move<n>> opener_list;

    const bool open_exclusive;

    static std::shared_ptr<Figure> define(const std::string& name, const std::string& key, value_t value, std::vector<moves::Move<n>>&& move_list, std::vector<moves::Move<n>>&& opener_list, bool open_exclusive){
        std::shared_ptr<Figure> result = std::make_shared<Figure>(name, key, value, move_list, opener_list, open_exclusive);
        Figure::instances[key] = result;
        return result;
    }

    template<index_t i, index_t j>
    static std::shared_ptr<Figure> define(const std::string& name, const std::string& key, value_t value, const Tuple<moves::Move<n>, i>& move_list, const Tuple<moves::Move<n>, k>& opener_list, bool open_exclusive){
        std::vector<moves::Move<n>> temp_moves;
        std::vector<moves::Move<n>> temp_openers;

        for (index_t _i = 0; _i < i; ++_i){
            temp_moves.push_back(std::move(move_list[_i]));
        }

        for (index_t _j = 0; _j <j; ++_j){
            temp_openers.push_back(std::move(opener_list[_j]));
        }

        return Figure::define(name, key, value, std::move(temp_moves), std::move(temp_openers), open_exclusive)
    }

    static std::shared_ptr<Figure> resolve(const std::string& key) {
        return Figure::instances[key];
    }

    private:
        Figure(const std::string& name, const std::string& key, value_t value, std::vector<moves::Move>&& move_list, std::vector<moves::Move>&& opener_list, bool open_exclusive) : name(name), key(key), value(value), move_list(move_list), opener_list(opener_list), open_exclusive(open_exclusive) {}

        static std::unordered_map<std::string, std::shared_ptr<Figure>> instances; 
};




