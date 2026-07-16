// Demetre Seturidze
// Chess
// Instances

#include"logic.hpp"

using namespace structs;

template <index_t n>
struct game::Piece{
    mutable Index<n> position;

    const std::shared_ptr<moves::Figure<n>> figure;
    mutable std::shared_ptr<Instance> instance;

    const index_t player_index;

    const std::vector<std::string> promotion_list;
    const index_t promotion_axis;
    const index_t promotion_index;
    mutable bool promoted;

    mutable bool dead;

    mutable bool has_moved;
    mutable bool just_opened;

    Piece(Tuple<index_t, n>&& position, std::shared_ptr<moves::Figure<n>> figure, std::shared_ptr<Instance> instance, index_t player_index, std::vector<std::string>&& promotion_list, index_t promotion_axis, index_t promotion_index, bool promoted, bool dead, bool has_moved, bool just_opened) : position(position), figure(figure), instance(instance), player_index(player_index), promotion_list(promotion_list), promotion_axis(promotion_axis), promotion_index(promotion_index), promoted(promoted), dead(dead), has_moved(has_moved), just_opened(just_opened){}
    Piece(Tuple<index_t, n>&& position, std::shared_ptr<moves::Figure<n>> figure, std::shared_ptr<Instance> instance, index_t player_index, bool dead, bool has_moved, bool just_opened) : position(position), figure(figure), instance(instance), player_index(player_index), promotion_list(), promotion_axis(0), promotion_index(0), promoted(false), dead(dead), has_moved(has_moved), just_opened(just_opened){}
    
    Piece(Piece&&) = default;

    ~Piece() = default;
    Piece&& operator=(Piece&&) = default;

    bool operator<(const Piece& p) const {
        return this -> figure -> value < p.figure.value;
    }

    bool sees(const Index<n>& target) const {
        if (this -> dead || this -> promoted) {
            return false;
        }

        if (!this -> has_moved){
            index_t num_openers = this -> figure -> num_openers;
            const std::vector<moves::Move<n>>& opener_list = this -> figure -> opener_list;

            for (const moves::Move<n>& opener : opener_list){
                if (opener.sees(*(this -> instance), this -> position, target, this -> player_index)){
                    return true;
                }
            }

            if (this -> figure -> open_exclusive){
                return false;
            }
        }

        const std::vector<moves::Move<n>>& move_list = this -> figure -> move_list;

        for (const moves::Move<n>& move : move_list){
            if (move.sees(*(this -> instance), this -> position, target, this -> player_index)){
                return true;
            }
        }

        return false;
    }

    const moves::Move<n>* which_sees(const Index<n>& target) const {
        if (this -> dead || this -> promoted) {
            return nullptr;
        }

        if (!this -> has_moved){
            index_t num_openers = this -> figure -> num_openers;
            const std::vector<moves::Move<n>>& opener_list = this -> figure -> opener_list;

            for (const moves::Move<n>& opener : opener_list){
                if (opener.sees(*(this -> instance), this -> position, target, this -> player_index)){
                    return &opener;
                }
            }

            if (this -> figure -> open_exclusive){
                return nullptr;
            }
        }

        const std::vector<moves::Move<n>>& move_list = this -> figure -> move_list;

        for (const moves::Move<n>& move : move_list){
            if (move.sees(*(this -> instance), this -> position, target, this -> player_index)){
                return &move;
            }
        }

        return nullptr;
    }


    void die() {
        this -> dead = true;
        this -> instance[this -> position] = nullptr;
    }
    
    void undie() {
        this -> dead = false;
        this -> instance[this -> position] = this;
    }

    void appear() {
        if (!(this -> dead || this -> promoted)){
            this -> instance[this -> position] = this;
        }
    }


    void promote(index_t i) {
        this -> promoted = true;

        const std::string& promotion_fig = this -> promotion_list[i];

        Piece<n> new_piece = Piece<n>(
            this -> position,
            moves::Figure<n>::resolve(promotion_fig),
            this -> instance,
            this -> player_index, 
            false,
            false, 
            false
        )

        this -> instance -> add_piece(this -> player_index, std::move(new_piece));
    }
};


template<index_t n>
struct game::Player{
    const index_t index;

    value_t material;

    std::vector<Piece<n>> pieces;
    std::vector<Piece<n>> monarchs;

    Player(index_t index, value_t material, std::vector<Piece<n>>&& pieces, std::vector<Piece<n>>&& monarchs) : index(index), material(material), pieces(pieces), monarchs(monarchs), {}
    
    bool army_sees(const Index<n>& target) const {
        for (Piece<n>& piece : this -> pieces){
            if (piece.sees(target)){
                return true;
            }
        }

        return false;
    }

    bool monarchs_see(const Index<n>& target) const {
        for (Piece<n>& monarch : this -> monarchs){
            if (monarch.sees(target)){
                return true;
            }
        }

        return false;
    }

    bool sees(const Index<n>& target) const {
        return this -> monarchs_see(target) || this -> army_sees(target);
    }
};


template <index_t n, index_t p>
struct game::Instance{
    Instance(Grid<Piece<n>*, n>&& board, Tuple<Player, p>&& players, double time) : board(board), turn(0), times(time), players(players), promoting(nullptr){} 

    Instance(Instance&&) = default;
    Instance& operator=(Instance&&) = default;
    ~Instance() = default;

    Piece<n>*& operator[](const Index<n>& i) {
        return this -> board[i];
    }

    const Piece<n>*& operator[](const Index<n>& i) const {
        return this -> board[i];
    }

    json execute(const Index<n>& start, const Index<n>& end) const {
        if (this -> status > ONGOING){
            return {
                {"label", "error"},
                {"content", std::string("status ") + std::string((char)(this -> status))}
            }
        }

        try{
            if (this -> move(start, end)){
                json r = std::move(this -> move_json);
                this -> move_json = nullptr;
                return r;
            } else {
                return nullptr;
            }
        } catch(const std::exception& e){
            return {
                {"label", "error"},
                {"content", e.what()}
            }
        }
    }


    json serialize() const {
        return {
            {"board", this -> board.get_shape()},
            {"players", this -> history},
            {"round", this -> round},
            {"turn", this -> turn},
            {"history", this -> players_to_json(this -> players)}
        }
    }

    void add_piece(index_t player_index, Piece<n>&& piece) {
        std::vector<Piece<n>>& pieces = this -> players[player_index].pieces;

        pieces.push_back(piece);
        Piece<n>* p = pieces.back();

        p -> appear();
    }


    private:
        Grid<Piece<n>*, n> board;
        Tuple<Player<n>, p> players;
        Tuple<double, p> times;
        
        Tuple<Action<n>, p> round;
        index_t turn;

        std::vector<Tuple<Action<n>, p>> history;

        Status status;
        Piece<n>* promoting;

        json move_json;

        Instance(
            Grid<Piece<n>*, n>&& board,
            Tuple<Player<n>, p>&& players,
            Tuple<double, p>&& times,
            
            Tuple<Action<n>, p>&& round,
            index_t turn,

            std::vector<Tuple<Action<n>, p>>&& history,

            Status status,
            Piece<n>* promoting,

            json&& move_json
        ) : board(board), players(players), times(times), round(round), turn(turn), history(history), status(status), promoting(promoting), move_json(move_json) {}


        bool move(const Index<n>& start, const Index<n>& end) {
            Piece<n>* piece = this -> board[start];

            if (piece == nullptr) {
                throw std::runtime_error("empty");
            } else if (piece -> player_index != this -> turn){
                throw std::runtime_error("turn");
            } if (piece -> dead || piece -> promoted) {
                throw std::runtime_error("panic");
            }

            const moves::Move<n>* move = piece -> which_sees(end);

            if (move == nullptr){
                throw std::runtime_error("illegal");
            } else {
                Piece<n>* target_piece = this -> board[end + piece -> capture_displacement];
                Piece<n>* end_piece = this -> board[end];

                if (target_piece != nullptr){
                    target_piece -> die();
                }

                piece -> position = end;
                this -> board[start] = nullptr;
                this -> board[end] = piece;

                if (this -> in_check(this -> turn)) {
                    piece -> position = start;
                    this -> board[start] = piece;
                    this -> board[end] = end_piece;

                    if (target_piece != nullptr){
                        target_piece -> undie()
                    }

                    throw std::runtime_error("check");
                } else {
                    this -> history.emplace_back(start, end);
                    
                    this -> move_json = {
                        {"label", "move"},
                        {"action", this -> action_to_json(this -> history.back())}
                    };

                    if (target_piece != nullptr){
                        this -> move_json["die"] = this -> tuple_to_json(target_piece -> position); 
                    }

                    std::vector<index_t> checks;

                    for (index_t i = 0; i < p; i++){
                        if (i != this -> turn && this -> in_check(i)){
                            checks.push_back(i);
                        }
                    }

                    if (checks.size() > 0){
                        this -> move_json["checks"] = std::move(checks);
                    }
                    

                    if (piece -> promotion_list.size() == 0){
                        return true;
                    } else {
                        if (piece -> position[piece -> promotion_axis] == piece -> promotion_index){
                            if (piece -> promotion_list.size() == 1){
                                piece -> promote(0);
                                this -> move_json["promote"] = 0;
                                return true;
                            } else {
                                this -> promoting = piece;
                                this -> status = PROMOTING;
                                return false;
                            }
                        } else {
                            return true;
                        }
                    }
                }
            }
        }

        /*
            # update process after a move has been completed.
    # checks for checks, registers the necessary sounds, updates history
    def _post_move_update(self, event : Event, update_time=True):
        if update_time:
            if self.status == Status.UNBEGUN:
                self.status = Status.ONGOING
                self.turn_start_time = turn_end_time = time.time()
            elif self.status == Status.ONGOING and update_time:
                turn_end_time = time.time()
                time_dif = turn_end_time - self.turn_start_time
                self.times[self.turn] -= time_dif
            
            event.action.times = self.times.copy()
            event.action.start_time = self.turn_start_time
            event.action.end_time = turn_end_time
            
            self.turn_start_time = turn_end_time    
        
        self._next_turn()

        check = self.update_checks()
        if check:
            event.sounds.append('check')

            if 'move' in event.sounds:
                event.sounds.remove('move')
        
        # if the player is out of legal moves, the game ends
        if not self.has_legal_moves(self.players[self.turn]):
            event.sounds.append('end')
            self.status = Status.CHECKMATE if check else Status.STALEMATE

        # registers the move in the game history
        self.history[-1].append(event.action)
        return event

        }
    */


        bool in_check(index_t player_index) const {
            const Player<n>& player = this -> players[player_index];

            if (player -> monarchs.size() == 1){
                const Piece<n>& king = player -> monarchs[0];

                for (index_t i = 0; i < p; i++){
                    if (i != player_index){
                        const Player<n>& opponent = this -> players[i];
                        if (opponent.army_sees(king.position)){
                            return true;
                        }
                    }
                }
            }

            return false;
        }



        json piece_to_json(const Piece<n>& pi) const {
            return {
                {"position", pi.position},
                {"figure", pi.figure -> key},
                {"player_index", pi.player_index},
                {"promotion_list", pi.promotion_list},
                {"promotion_axis", pi.promotion_axis},
                {"promotion_index", pi.promotion_index},
                {"promoted", pi.promoted},
                {"dead", pi.dead},
                {"has_moved", pi.has_moved},
                {"just_opened", pi.just_opened}
            };
        }

        Piece<n> piece_from_json(const json& j, std::shared_ptr<Instance> instance_ptr) const {
            return Piece<n>(
                Index<n>(std::move(j.at("position").get<Tuple<index_t, n>>()), *this),
                moves::Figure::resolve(j.at("figure").get<std::string>()),

                instance_ptr,

                j.at("player_index").get<index_t>(),
                j.at("promotion_list").get<std::vector<std::string>>(),
                j.at("promotion_axis").get<index_t>(),
                j.at("promotion_index").get<index_t>(),
                
                j.at("promoted").get<bool>(),
                j.at("dead").get<bool>(),
                j.at("has_moved").get<bool>(),
                j.at("just_opened").get<bool>()
            );
        }


        json player_to_json(const Player<n>& pl) const {
            json pieces = json::array();
            json pawns = json::array();
            json monarchs = json::array();

            for (const Piece<n>& piece : pl.pieces){
                pieces.push_back(this -> piece_to_json(piece));
            }

            for (const Piece<n>& pawn : pl.pawns){
                pawns.push_back(this -> piece_to_json(pawn));
            }

            for (const Piece<n>& monarch : pl.monarchs){
                monarchs.push_back(this -> piece_to_json(monarch));
            }

            return {
                {"index", pl.index},
                {"material", pl.material},
                {"pawns", pawns},
                {"pieces", pieces},
                {"monarchs", monarchs}
            }
        }

        Player<n> player_from_json(const json& j) const {
            std::set<Piece<n>> pieces;
            std::set<Piece<n>> pawns;
            std::set<Piece<n>> monarchs;

            const json& jpieces = j["pieces"];
            const json& jpawns = j["pawns"];
            const json& jmonarchs = j["monarchs"];

            for (const auto& piece : jpieces){
                pieces.insert(std::move(this -> piece_from_json(piece)));
            }

            for (const auto& pawn : jpawns){
                pawns.insert(std::move(this -> piece_from_json(pawn)));
            }

            for (const auto& monarch : jmonarchs){
                monarchs.insert(std::move(this -> piece_from_json(monarch)));
            }

            return Player<n>(
                j["index"],
                j["material"],
                std::move(pawns),
                std::move(pieces),
                std::move(monarchs)
            ) 
        }


        json players_to_json(const Tuple<Player<n>, p>& ps) const{
            json j = json::array();

            for (index_t k; k < p; k++){
                j.push_back(std::move(this -> player_to_json(ps[k])));
            }

            return j;
        }

        Tuple<Player<n>, p> players_from_json(const json& j) const{
            
            Tuple<Player<n>, p> ps;

            for (index_t k; k < p; k++){
                ps[k] = std::move(this -> player_from_json(j[k]));
            }

            return ps;
        }

};
