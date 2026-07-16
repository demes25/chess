// Demetre Seturidze
// Chess
// Instances

#include"logic.hpp"

using namespace structs;

template <index_t n>
struct game::Piece{
    mutable Index<n> position;

    const std::shared_ptr<moves::Figure<n>> figure;

    const index_t player_index;

    const std::vector<std::string> promotion_list;
    const index_t promotion_axis;
    const index_t promotion_index;
    mutable bool promoted;

    mutable bool dead;

    mutable bool has_moved;
    mutable bool just_opened;

    Piece(Tuple<index_t, n>&& position, std::shared_ptr<moves::Figure<n>> figure, index_t player_index, std::vector<std::string>&& promotion_list, index_t promotion_axis, index_t promotion_index, bool promoted, bool dead, bool has_moved, bool just_opened) : position(position), figure(figure), player_index(player_index), promotion_list(promotion_list), promotion_axis(promotion_axis), promotion_index(promotion_index), promoted(promoted), dead(dead), has_moved(has_moved), just_opened(just_opened){}
    Piece(Tuple<index_t, n>&& position, std::shared_ptr<moves::Figure<n>> figure, index_t player_index, bool dead, bool has_moved, bool just_opened) : position(position), figure(figure), player_index(player_index), promotion_list(), promotion_axis(0), promotion_index(0), promoted(false), dead(dead), has_moved(has_moved), just_opened(just_opened){}
    
    Piece(Piece&&) = default;

    ~Piece() = default;
    Piece&& operator=(Piece&&) = default;

    bool sees(const Grid<Piece<n>*, n>& board, const Index<n>& target) const {
        if (this -> dead || this -> promoted) {
            return false;
        }

        if (!this -> has_moved){
            index_t num_openers = this -> figure -> num_openers;
            const std::vector<moves::Move<n>>& opener_list = this -> figure -> opener_list;

            for (const moves::Move<n>& opener : opener_list){
                if (opener.sees(board, this -> position, target, this -> player_index)){
                    return true;
                }
            }

            if (this -> figure -> open_exclusive){
                return false;
            }
        }

        const std::vector<moves::Move<n>>& move_list = this -> figure -> move_list;

        for (const moves::Move<n>& move : move_list){
            if (move.sees(board, this -> position, target, this -> player_index)){
                return true;
            }
        }

        return false;
    }

    const moves::Move<n>* which_sees(const Grid<Piece<n>*, n>& board, const Index<n>& target) const {
        if (this -> dead || this -> promoted) {
            return nullptr;
        }

        if (!this -> has_moved){
            index_t num_openers = this -> figure -> num_openers;
            const std::vector<moves::Move<n>>& opener_list = this -> figure -> opener_list;

            for (const moves::Move<n>& opener : opener_list){
                if (opener.sees(board, this -> position, target, this -> player_index)){
                    return &opener;
                }
            }

            if (this -> figure -> open_exclusive){
                return nullptr;
            }
        }

        const std::vector<moves::Move<n>>& move_list = this -> figure -> move_list;

        for (const moves::Move<n>& move : move_list){
            if (move.sees(board, this -> position, target, this -> player_index)){
                return &move;
            }
        }

        return nullptr;
    }

    Piece<n> promote(index_t i) {
        this -> promoted = true;

        const std::string& promotion_fig = this -> promotion_list[i];

        return Piece<n>(
            this -> position,
            moves::Figure<n>::resolve(promotion_fig),
            this -> player_index, 
            false,
            false, 
            false
        )
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

    // MANIPULATORS

    Piece<n>* add(Piece<n>&& piece){
        std::vector<Piece<n>>& pieces = this -> players[piece.player_index].pieces;

        pieces.push_back(piece);
        Piece<n>* result = &pieces.back();

        this -> show(result);

        return result;
    }

    Piece<n>* add_monarch(Piece<n>&& monarch){
        std::vector<Piece<n>>& monarchs = this -> players[piece.player_index].monarchs;

        monarchs.push_back(monarch);
        Piece<n>* result = &monarchs.back();

        this -> show(result);

        return result;
    }

    void show(Piece<n>* piece) {
        if (piece != nullptr && !piece -> dead && !piece -> promoted){
            this -> board[piece -> position] = piece;
        }
    }

    void kill(Piece<n>* p) {
        if (piece != nullptr && !piece -> dead && !piece -> promoted){
            piece -> dead = true;
            this -> board[piece -> position] = nullptr;
        }
    }

    void unkill(Piece<n>* piece) {
        if (piece != nullptr && piece -> dead && !piece -> promoted){
            piece -> dead = false;
            this -> board[piece -> position] = piece;
        }
    }

    void promote(index_t promotion_index) {
        if (promoting != nullptr) {
            promoting -> promoted = true;
            this -> add(promoting -> promote(promotion_index));
            promoting = nullptr;
        }
    }


    // COMMANDS

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


    // SERIALIZATION

    json serialize() const {
        json promoting;

        if (this -> promoting == nullptr){
            promoting = nullptr;
        } else {
            promoting = this -> promoting -> position;
        }

        return {
            {"board", this -> board.get_shape()},
            {"players", Instance::players_to_json(this -> players)},
            {"times", this -> times},

            {"round", this -> round},
            {"turn", this -> turn},
            {"history", this -> history},

            {"status", (char)this -> status},
            {"promoting", promoting},

            {"move_json", this -> move_json},
        }
    }

    static Instance deserialize(const json& j) {
        Grid<Piece<n>*, n> board(j.at("board").get<Tuple<index_t, n>>());
        Tuple<Player<n>, p> players = Instance::players_to_json(j.at("players"), board);


        Instance result(
            std::move(board), 
            std::move(players), 
            j.at("times").get<Tuple<double, p>>(),
            j.at("round").get<Tuple<Action<n>, p>>(),
            j.at("turn").get<index_t>(),
            j.at("history").get<std::vector<Tuple<Action<n>, p>>>(),
            j.at("status").get<Status>(),
            nullptr,
            j.at("move_json")
        );

        for (index_t i = 0; i < p; i++){
            for (Piece& piece : players[i].pieces){
                result.show(&piece);
            }

            for (Piece& monarch : players[i].monarchs){
                result.show(&monarch);
            }
        }

        json& promoting = j.at("promoting");

        if (!promoting.is_null()){
            result.promoting = result.board[Index<n>(promoting.get<Tuple<index_t, n>>(), board)]
        }
        
        return result;
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

                this -> kill(target_piece);

                piece -> position = end;
                this -> board[start] = nullptr;
                this -> board[end] = piece;

                if (this -> in_check(this -> turn)) {
                    piece -> position = start;
                    this -> board[start] = piece;
                    this -> board[end] = end_piece;

                    this -> unkill(target_piece);

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


        static json piece_to_json(const Piece<n>& pi) const {
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

        static Piece<n> piece_from_json(const json& j, const Grid<Piece<n>*, n>& board) const {
            return Piece<n>(
                Index<n>(std::move(j.at("position").get<Tuple<index_t, n>>()), board),
                moves::Figure::resolve(j.at("figure").get<std::string>()),

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
