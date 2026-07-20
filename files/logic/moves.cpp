// Demetre Seturidze
// Chess
// Moves

#ifndef MOVES
#define MOVES

#include"logic.hpp"

using namespace structs;

template<index_t n>
struct moves::Move{
    const std::vector<Vector<n>> directions;
    const Vector<n> relative_capture;
    
    const bool captures;
    const bool moves;

    Move(Move&&) = default;

    ~Move() = default;

    Move(std::vector<Vector<n>>&& directions, bool captures, bool moves, Vector<n>&& relative_capture) : directions(std::forward<std::vector<Vector<n>>>(directions)),  captures(captures), moves(moves), relative_capture(relative_capture) {}

    Move(std::vector<Vector<n>>&& directions, bool captures, bool moves) : directions(std::forward<std::vector<Vector<n>>>(directions)),  captures(captures), moves(moves), relative_capture(0) {}

    template<index_t k>
    Move(Tuple<Vector<n>, k>&& directions, bool captures, bool moves, Vector<n>&& relative_capture) : directions(directions.into_vector()), captures(captures), moves(moves), relative_capture(relative_capture) {}
    
    template<index_t k>
    Move(Tuple<Vector<n>, k>&& directions, bool captures, bool moves) : directions(directions.into_vector()), captures(captures), moves(moves), relative_capture(0) {}


    Move& operator=(Move&&) = default;

    const Vector<n>& operator[](index_t i) const {
        return this -> directions[i];
    }

    virtual bool sees(const game::Board<n>& board, const Index<n>& position, const Index<n>& target, index_t player_index) const {
        return (
            this -> valid_occupancy(board, target, player_index) && this -> valid_square(board, position, target)
        );
    }

    virtual void populate(MoveMap<n>& map, const game::Board<n>& board, const Index<n>& position, index_t player_index) const {
        for (const Vector<n>& v : this -> directions){
            Index<n> target = position + v;
            
            if (target.is_valid() && this -> valid_occupancy(board, target, player_index)){
                const Move<n>*& b = map[target];

                if (b == nullptr){
                    b = this;
                } else if (b != this) {
                    throw std::runtime_error("target reachable by multiple moves -- ambiguous");
                }
            }
        }
    }

    
    // SERIALIZATION

    Move(const json& j) : 
        directions(j.at("directions").get<std::vector<Vector<n>>>()),
        captures(j.at("captures").get<bool>()),
        moves(j.at("moves").get<bool>()),
        relative_capture(j.at("relative_capture").get<Vector<n>>()) {}

    virtual json serialize() const {
        return {
            {"directions", this -> directions},
            {"captures", this -> captures},
            {"moves", this -> moves},
            {"relative_capture", this -> relative_capture}
        };
    }


    protected:
        virtual bool valid_occupancy(const game::Board<n>& board, const Index<n>& target, index_t player_index) const {
            const sptr<game::Piece<n>>& piece_at = board[target];
            const sptr<game::Piece<n>>& takes_at = board[target + this -> relative_capture];

            if (piece_at == nullptr && takes_at == nullptr) return this -> moves;

            else if (this -> captures && takes_at != nullptr) {
                if (piece_at == takes_at || piece_at == nullptr) {
                    return takes_at -> player_index != player_index;
                } 
            }

            return false;
        }

        virtual bool valid_square(const game::Board<n>& board, const Index<n>& position, const Index<n>& target) const {
            if (position == target){
                return false;
            }

            Vector<n> vector = target-position;

            for (const Vector<n>& v : this -> directions){
                if (v == vector){
                    return true;
                }
            }

            return false;
        }
};

template<index_t n>
struct moves::Span : public Move<n>{
    const arith_t min_steps;
    const arith_t max_steps;

    const arith_t min_obstacles;
    const arith_t max_obstacles;

    Span(std::vector<Vector<n>>&& directions, bool captures, bool moves) : Move<n>(std::forward<std::vector<Vector<n>>>(directions), captures, moves), min_steps(1), max_steps(-1), min_obstacles(0), max_obstacles(0) {}

    Span(
        std::vector<Vector<n>>&& directions, 
        bool captures, 
        bool moves, 
        arith_t min_steps, 
        arith_t max_steps, 
        arith_t min_obstacles, 
        arith_t max_obstacles
    ) : Move<n>(std::forward<std::vector<Vector<n>>>(directions), captures, moves), 
        min_steps(min_steps), 
        max_steps(max_steps), 
        min_obstacles(min_obstacles), 
        max_obstacles(max_obstacles) {}

    template<index_t k>
    Span(Tuple<Vector<n>, k>&& directions, bool captures, bool moves) : Move<n>(directions.into_vector(), captures, moves), min_steps(1), max_steps(-1), min_obstacles(0), max_obstacles(0) {}

    template<index_t k>
    Span(
        Tuple<Vector<n>, k>&& directions, 
        bool captures, 
        bool moves, 
        arith_t min_steps, 
        arith_t max_steps, 
        arith_t min_obstacles, 
        arith_t max_obstacles
    ) : Move<n>(directions.into_vector(), captures, moves), 
        min_steps(min_steps), 
        max_steps(max_steps), 
        min_obstacles(min_obstacles), 
        max_obstacles(max_obstacles) {}

    
    virtual void populate(MoveMap<n>& map, const game::Board<n>& board, const Index<n>& position, index_t player_index) const {
        for (const Vector<n>& di : this -> directions){
            this -> positive_span(map, board, position, player_index, di);
            this -> positive_span(map, board, position, player_index, -di);
        }
    }

    // SERIALIZATION

    Span(const json& j) : 
        Move<n>(j),
        min_steps(j.at("min_steps").get<arith_t>()),
        max_steps(j.at("max_steps").get<arith_t>()),
        min_obstacles(j.at("min_obstacles").get<arith_t>()),
        max_obstacles(j.at("max_obstacles").get<arith_t>()) {}


    json serialize() const override {
        json result = Move<n>::serialize();

        result["min_steps"] = this -> min_steps;
        result["max_steps"] = this -> max_steps;
        result["min_obstacles"] = this -> min_obstacles;
        result["max_obstacles"] = this -> max_obstacles;

        return result;
    }


    protected:
        bool valid_square(const game::Board<n>& board, const Index<n>& position, const Index<n>& target) const override {
            if (position == target){
                return false;
            }

            Vector<n> vector = target-position;

            for (const Vector<n>& v : this -> directions){
                arith_t scaling = vector | v;
                
                if (scaling == 0){
                    continue;
                }

                arith_t num_steps = (scaling < 0) ? -scaling : scaling;

                if (num_steps < this -> min_steps || (this -> max_steps > 0 && num_steps > this -> max_steps)){
                    return false;
                }
                
                arith_t num_obstacles(0);

                if (scaling < 0) {
                    for (Index<n> i(position - v); i != target; i -= v) {
                        if (board[i] != nullptr) {
                            num_obstacles++;
                        }

                        if (num_obstacles > this -> max_obstacles){
                            return false;
                        }
                    }
                } else {
                    for (Index<n> i(position + v); i != target; i += v) {
                        if (board[i] != nullptr) {
                            num_obstacles++;
                        }

                        if (num_obstacles > this -> max_obstacles){
                            return false;
                        }
                    }
                }

                if (num_obstacles >= this -> min_obstacles && num_obstacles <= this -> max_obstacles){
                    return true;
                }

                return false;
            }

            return false;
        }

        virtual void positive_span(MoveMap<n>& map, const game::Board<n>& board, const Index<n>& position, index_t player_index, const Vector<n>& v) const {
            arith_t steps(1);
            arith_t obstacles(0);

            for (Index<n> i(position+v); i.is_valid(); i += v){
                if (obstacles >= this -> min_obstacles && steps >= this -> min_steps){
                    if (this -> valid_occupancy(board, i, player_index)){
                        const Move<n>*& b = map[i];

                        if (b == nullptr){
                            b = this;
                        } else if (b != this) {
                            throw std::runtime_error("target reachable by multiple moves -- ambiguous");
                        }   
                    }
                }

                steps++;

                if (this -> max_steps > 0 && steps > this -> max_steps){
                    break;
                }

                if (board[i] != nullptr){
                    obstacles ++;
                }

                if (obstacles > this -> max_obstacles){
                    break;
                }
            }
        }


};

template<index_t n>
struct moves::Figure {
    const std::string name;
    const std::string key;
    const value_t value;

    const std::vector<sptr<Move<n>>> move_list;
    const std::vector<sptr<Move<n>>> opener_list;

    const bool open_exclusive;

    static sptr<Figure> define(const std::string& name, const std::string& key, value_t value, std::vector<sptr<Move<n>>>&& move_list, std::vector<sptr<Move<n>>>&& opener_list, bool open_exclusive){
        sptr<Figure> result = std::make_shared<Figure>(name, key, value, std::forward<std::vector<sptr<Move<n>>>>(move_list), std::forward<std::vector<sptr<Move<n>>>>(opener_list), open_exclusive);
        Figure::instances[key] = result;
        return result;
    }

    template<index_t i, index_t j>
    static sptr<Figure> define(const std::string& name, const std::string& key, value_t value, Tuple<Move<n>, i>&& move_list, Tuple<Move<n>, j>&& opener_list, bool open_exclusive){
        return Figure::define(name, key, value, move_list.into_vector(), opener_list.into_vector(), open_exclusive);
    }

    static sptr<Figure> resolve(const std::string& key) {
        return Figure::instances[key];
    }


    sptr<Move<n>> which_opener(const game::Board<n>& board, const Index<n>& position, const Index<n>& target, index_t player_index) const {
        for (const sptr<Move<n>>& m : this -> opener_list){
            if (m -> sees(board, position, target, player_index)){
                return m;
            }
        }

        return nullptr;
    }

    virtual void populate_openers(MoveMap<n>& map, const game::Board<n>& board, const Index<n>& position, index_t player_index) const {
        for (const sptr<Move<n>>& m : this -> opener_list){
            m -> populate(map, board, position, player_index);
        }
    }

    sptr<Move<n>> which_move(const game::Board<n>& board, const Index<n>& position, const Index<n>& target, index_t player_index) const {
        for (const sptr<Move<n>>& m : this -> move_list){
            if (m -> sees(board, position, target, player_index)){
                return m;
            }
        }

        return nullptr;
    }

    virtual void populate_moves(MoveMap<n>& map, const game::Board<n>& board, const Index<n>& position, index_t player_index) const {
        for (const sptr<Move<n>>& m : this -> move_list){
            m -> populate(map, board, position, player_index);
        }
    }


    // SERIALIZATION

    static sptr<Move<n>> deserialize(const json& m) {
        if (m.contains("min_steps")){
            return std::make_shared<Span<n>>(m);
        } else {
            return std::make_shared<Move<n>>(m);
        }
    }

    static sptr<Figure> define(const json& j){
        std::vector<sptr<Move<n>>> move_list;

        for (const json& m : j.at("move_list")){
            move_list.push_back(deserialize(m));
        }

        std::vector<sptr<Move<n>>> opener_list;
        for (const json& o : j.at("opener_list")){
            opener_list.push_back(deserialize(o));
        }

        return Figure::define(
            j.at("name").get<std::string>(),
            j.at("key").get<std::string>(),
            j.at("value").get<value_t>(),
            std::move(move_list),
            std::move(opener_list),
            j.at("open_exclusive").get<bool>()
        );
    }

    static void load(const json& j) {
        for (const json& m : j){
            Figure::define(m);
        }
    }

    json serialize() {
        json move_arr = json::array();
        for (const sptr<Move<n>>& m : this -> move_list){
            move_arr.push_back(m -> serialize());
        }

        json opener_arr = json::array();
        for (const sptr<Move<n>>& o : this -> opener_list){
            opener_arr.push_back(o -> serialize());
        }

        return {
            {"name", this -> name},
            {"key", this -> key},
            {"value", this -> value},
            {"move_list", move_arr},
            {"opener_list", opener_arr},
            {"open_exclusive", this -> open_exclusive}
        };
    }

    static json save() {
        json j;

        for (auto f : Figure::instances){
            j[f -> key] = f -> serialize();
        }

        return j;
    }

    Figure(const std::string& name, const std::string& key, value_t value, std::vector<sptr<Move<n>>>&& move_list, std::vector<sptr<Move<n>>>&& opener_list, bool open_exclusive) : name(name), key(key), value(value), move_list(std::forward<std::vector<sptr<Move<n>>>>(move_list)), opener_list(std::forward<std::vector<sptr<Move<n>>>>(opener_list)), open_exclusive(open_exclusive) {}


    private:
        static std::unordered_map<std::string, sptr<Figure>> instances; 
};

template<index_t n>
std::unordered_map<std::string, sptr<moves::Figure<n>>>
moves::Figure<n>::instances{};

#endif


#ifdef MOVE_TEST

#include"structs.cpp"
#include"game.cpp"
int main() {
    using namespace moves;
    using namespace structs;

    Move<2> perimeter(
        Tuple<Vector<2>, 8>(
            Vector<2>(1, 0),
            Vector<2>(0, 1),
            Vector<2>(1, 1),
            Vector<2>(-1, 0),
            Vector<2>(0, -1),
            Vector<2>(-1, -1),
            Vector<2>(1, -1),
            Vector<2>(-1, 1)
        ),
        true,
        true
    );

    Grid<game::Piece<2>*, 2> board(8, 8);
    board.fill(nullptr); 

    std::cout << board << std::endl;

    MoveMap<2> mm(8, 8);
    mm.fill(nullptr);

    Index<2> start(Tup<2>(2, 2), board);
    Index<2> end(Tup<2>(2, 4), board);

    perimeter.populate(mm, board, start, 0);

    std::cout << mm.to_bitmap() << std::endl;
}

#endif 

#ifdef SPAN_TEST

#include"structs.cpp"
#include"game.cpp"

int main() {
    using namespace moves;
    using namespace structs;

    Span<2> span(
        Tuple<Vector<2>, 4>(
            Vector<2>(1, 0),
            Vector<2>(0, 1),
            Vector<2>(1, 1),
            Vector<2>(1, -1)
        ),
        true,
        true
    );

    Grid<game::Piece<2>*, 2> board(8, 8);
    board.fill(nullptr); 

    MoveMap<2> mm(8, 8);
    BitMap<2> nn(8, 8);

    mm.fill(nullptr);
    nn.fill(false);

    Index<2> start(Tup<2>(2, 2), board);
    Index<2> end(Tup<2>(2, 4), board);

    span.populate(mm, board, start, 0);

    for (Index<2> i(nn); i.is_valid(); ++i){
        if (span.sees(board, start, i, 0)){
            nn[i] = true;
        }
    }

    std::cout << mm.to_bitmap() << std::endl;
    std::cout << nn << std::endl;

    std::cout << (mm.to_bitmap() == nn) << std::endl;
}


#endif

#ifdef FIGURE_TEST

#include"structs.cpp"
#include"game.cpp"
#include<fstream>

int main(){
    json j;

    std::ifstream file("figures.json");
    if (!file) {
        throw std::runtime_error("Could not open config.json");
    }

    file >> j;

    sptr<Figure<2>> ptr;

    for (const json& m : j){
        sptr<Figure<2>> ptr = Figure<2>::define(m);
    }

    ptr;


}
#endif 