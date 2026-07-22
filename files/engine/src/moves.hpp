// Demetre Seturidze
// Chess
// Moves

#ifndef MOVES
#define MOVES

#include"structs.hpp"

using namespace structs;

namespace game {
    template<index_t n>
    struct Piece;

    template<index_t n>
    using Board = Grid<sptr<Piece<n>>, n>;
}

namespace moves {
    template<index_t n>
    struct Move;
    
    template<index_t n>
    using MoveMap = PointerMap<const Move<n>, n>;

    template<index_t n>
    struct Move{
        const std::vector<Vector<n>> directions;
        const Vector<n> relative_capture;
        
        const bool captures;
        const bool moves;
        const bool only_opens;
        
        ~Move() = default;

        Move(std::vector<Vector<n>>&& directions, bool captures = true, bool moves = true, bool only_opens=false, Vector<n>&& relative_capture = Vector<n>(0)) : directions(std::forward<std::vector<Vector<n>>>(directions)),  captures(captures), moves(moves), only_opens(only_opens), relative_capture(std::forward<Vector<n>>(relative_capture)) {}

        template<index_t k>
        Move(Tuple<Vector<n>, k>&& directions, bool captures = true, bool moves = true, bool only_opens=false, Vector<n>&& relative_capture = Vector<n>(0)) : directions(std::move(directions).into_vector()), captures(captures), moves(moves), only_opens(only_opens), relative_capture(std::forward<Vector<n>>(relative_capture)) {}
       

        const Vector<n>& operator[](index_t i) const {
            return this -> directions[i];
        }

        virtual std::string type_str() const {
            return "Move";
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
            captures(j.value("captures", json(true)).get<bool>()),
            moves(j.value("moves", json(true)).get<bool>()),
            only_opens(j.value("only_opens", json(false)).get<bool>()),
            relative_capture(j.value("relative_capture", json(Vector<n>(0))).get<Vector<n>>()) {}

        virtual json serialize() const {
            return {
                {"directions", this -> directions},
                {"captures", this -> captures},
                {"moves", this -> moves},
                {"only_opens", this -> only_opens},
                {"relative_capture", this -> relative_capture},
                {"__move__", this -> type_str()}
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

    template <index_t n>
    struct EnPassant : public Move<n> {
        const std::string target_name;

        EnPassant(std::vector<Vector<n>>&& directions, Vector<n>&& relative_capture, const std::string& target_name = "Pawn") : Move<n>(std::forward<std::vector<Vector<n>>>(directions), true, false, false, std::forward<Vector<n>>(relative_capture)), target_name(target_name) {}

        template<index_t k>
        EnPassant(Tuple<Vector<n>, k>&& directions, Vector<n>&& relative_capture, const std::string& target_name = "Pawn") : Move<n>(std::forward<std::vector<Vector<n>>>(directions), true, false, false, std::forward<Vector<n>>(relative_capture)), target_name(target_name) {}
        
        virtual std::string type_str() const {
            return "EnPassant";
        }

        // SERIALIZATION

        EnPassant(const json& j) : 
            EnPassant(j.at("directions").get<std::vector<Vector<n>>>(),
                      j.at("relative_capture").get<Vector<n>>(),
                      j.value("target_name", json("Pawn")).get<std::string>()) {}

        virtual json serialize() const {
            return {
                {"directions", this -> directions},
                {"relative_capture", this -> relative_capture},
                {"target_name", this -> target_name},
                {"__move__", this -> type_str()}
            };
        }


        protected:
            virtual bool valid_occupancy(const game::Board<n>& board, const Index<n>& target, index_t player_index) const {
                const sptr<game::Piece<n>>& piece_at = board[target];
                const sptr<game::Piece<n>>& takes_at = board[target + this -> relative_capture];

                if (piece_at != nullptr || takes_at == nullptr || takes_at -> player_index == player_index){
                    return false;
                } else if (takes_at -> figure -> name == this -> target_name && takes_at -> just_opened){
                    return true;
                }

                return false;
            }
    };

    template<index_t n>
    struct Span : public Move<n>{
        const arith_t min_steps;
        const arith_t max_steps;

        const arith_t min_obstacles;
        const arith_t max_obstacles;

        Span(
            std::vector<Vector<n>>&& directions, 
            bool captures = true, 
            bool moves = true, 
            arith_t min_steps = 1, 
            arith_t max_steps = -1, 
            arith_t min_obstacles = 0, 
            arith_t max_obstacles = 0
        ) : Move<n>(std::forward<std::vector<Vector<n>>>(directions), captures, moves), 
            min_steps(min_steps), 
            max_steps(max_steps), 
            min_obstacles(min_obstacles), 
            max_obstacles(max_obstacles) {}

        template<index_t k>
        Span(
            Tuple<Vector<n>, k>&& directions, 
            bool captures = true, 
            bool moves = true, 
            arith_t min_steps = 1, 
            arith_t max_steps = -1, 
            arith_t min_obstacles = 0, 
            arith_t max_obstacles = 0
        ) : Move<n>(std::move(directions).into_vector(), captures, moves), 
            min_steps(min_steps), 
            max_steps(max_steps), 
            min_obstacles(min_obstacles), 
            max_obstacles(max_obstacles) {}

        
        virtual std::string type_str() const {
            return "Span";
        }

        virtual void populate(MoveMap<n>& map, const game::Board<n>& board, const Index<n>& position, index_t player_index) const {
            for (const Vector<n>& di : this -> directions){
                this -> positive_span(map, board, position, player_index, di);
                this -> positive_span(map, board, position, player_index, -di);
            }
        }

        // SERIALIZATION

        Span(const json& j) : 
            Move<n>(j),
            min_steps(j.value("min_steps", json(1)).get<arith_t>()),
            max_steps(j.value("max_steps", json(-1)).get<arith_t>()),
            min_obstacles(j.value("min_obstacles", json(0)).get<arith_t>()),
            max_obstacles(j.value("max_obstacles", json(0)).get<arith_t>()) {}


        json serialize() const override {
            return {
                {"directions", this -> directions},
                {"captures", this -> captures},
                {"moves", this -> moves},
                {"min_steps", this -> min_steps},
                {"max_steps", this -> max_steps},
                {"min_obstacles", this -> min_obstacles},
                {"max_obstacles", this -> max_obstacles},
                {"__move__", this -> type_str()}
            };
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

                    Vector<n> di = (scaling < 0) ? -v : v;
                
                    for (Index<n> i(position + di); i != target; i += di) {
                        if (board[i] != nullptr) {
                            num_obstacles++;
                        }

                        if (num_obstacles > this -> max_obstacles){
                            return false;
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
    struct Castle : public Move<n> {

        Castle(
            index_t axis = 0,
            index_t min_steps = 2,
            index_t max_steps = 2,
            std::string&& partner_key = "Rook"
        ) : Move<n>(std::vector<Vector<n>>{Vector<n>::one_hot(axis)}, false, true, true), axis(axis), min_steps(min_steps), max_steps(max_steps), partner_key(partner_key) {}

        virtual std::string type_str() const {
            return "Castle";
        }

        virtual bool sees(const game::Board<n>& board, const Index<n>& position, const Index<n>& target, index_t player_index) const {
            Vector<n> vec(target - position);

            arith_t scaling = vec | this -> directions[0];

            if (scaling == 0){
                return false;
            }

            arith_t num_steps = (scaling < 0) ? -scaling : scaling;

            if (num_steps < this -> min_steps || num_steps > this -> max_steps){
                return false;
            }
            
            Vector<n> di = (scaling < 0) ? -(this -> directions[0]) : (this -> directions[0]);

            for (Index<n> i(position + di); i.is_valid(); i += di) {
                if (board[i] != nullptr) {
                    if (i.is_at_bounds(this -> axis) &&
                        board[i] -> player_index == player_index &&
                        board[i] -> figure -> key == this -> partner_key && 
                        !(board[i] -> has_moved)){
                            return true;
                        }
                    
                        return false;
                }
            }

            return false;
        }


        virtual void populate(MoveMap<n>& map, const game::Board<n>& board, const Index<n>& position, index_t player_index) const {
            this -> populate_helper(
                map, board, position, player_index, this -> directions[0]
            );
            this -> populate_helper(
                map, board, position, player_index, -(this -> directions[0])
            );
        }

        
        // SERIALIZATION

        Castle(const json& j) : 
            Castle(
                j.value("axis", json(0)).get<index_t>(),
                j.value("min_steps", json(2)).get<index_t>(),
                j.value("max_steps", json(2)).get<index_t>(),
                j.value("partner_key", json("Rook")).get<std::string>()
            ) {}

        virtual json serialize() const {
            return {
                {"axis", this -> axis},
                {"min_steps", this -> min_steps},
                {"max_steps", this -> max_steps},
                {"partner_key", this -> partner_key},
                {"__move__", this -> type_str()}
            };
        }
        
        private:
            index_t axis;
            index_t min_steps;
            index_t max_steps;
            std::string partner_key;


            void populate_helper(MoveMap<n>& map, const game::Board<n>& board, const Index<n>& position, index_t player_index, const Vector<n>& forward) const {
                bool _seen = false;
                
                for (Index<n> i(position + forward); i.is_valid(); i+= forward){
                    if (board[i] != nullptr){
                        if (i.is_at_bounds(axis) &&
                            board[i] -> player_index == player_index &&
                            board[i] -> figure -> key == this -> partner_key && 
                            !(board[i] -> has_moved)){
                            _seen = true;
                            }

                        break;
                    }
                }

                if (_seen){
                    Index<n> s = position + (this -> min_steps) * forward;
                    
                    for (index_t i = 0; i <= this -> max_steps - this -> min_steps; i++){
                        map[s] = this;
                        s += forward;
                    }
                }
            }
    };

    template<index_t n>
    struct Figure {
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
            std::string __move__ = m.at("__move__");

            if (__move__ == "Span"){
                return std::make_shared<Span<n>>(m);
            } else if (__move__ == "Castle"){
                return std::make_shared<Castle<n>>(m);
            } else if (__move__ == "EnPassant"){
                return std::make_shared<EnPassant<n>>(m);
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
                j.value("open_exclusive", json(false)).get<bool>()
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
    std::unordered_map<std::string, sptr<Figure<n>>>
    Figure<n>::instances{};
}

#endif
