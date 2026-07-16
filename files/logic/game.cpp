// Demetre Seturidze
// Chess
// Instances

#include"logic.hpp"

using namespace structs;

template <index_t n>
struct game::Piece{
    const std::string name;
    const index_t index;
    mutable Index<n> position;

    const std::shared_ptr<moves::Figure<n>> figure;
    mutable std::shared_ptr<Instance> board;

    const index_t player_index;

    const std::shared_ptr<index_t[]> promotion_list;
    const index_t num_promotions;

    const index_t promotion_axis;

    mutable bool dead;

    mutable bool has_moved;
    mutable bool just_opened;

    Piece(const std::string& name, index_t index, Tuple<index_t, n>&& position, std::shared_ptr<moves::Figure<n>> figure, std::shared_ptr<Instance> board, index_t player_index, std::shared_ptr<index_t[]> promotion_list, index_t num_promotions, index_t promotion_axis, bool dead, bool has_moved, bool just_opened) : name(name), index(index), position(position), figure(figure), board(board), player_index(player_index), promotion_list(promotion_list), num_promotions(num_promotions), promotion_axis(promotion_axis), dead(dead), has_moved(has_moved), just_opened(just_opened){}

    Piece(const Piece&) = default;
    Piece(Piece&&) = default;

    ~Piece() = default;

    Piece& operator=(const Piece&) = default;
    Piece&& operator=(Piece&&) = default;

    bool operator<(const Piece& p) const {
        return this -> figure -> value < p.figure.value;
    }

    bool sees(const Index<n>& target) const {
        if (this -> dead) {
            return false;
        }

        if (!this -> has_moved){
            index_t num_openers = this -> figure -> num_openers;
            std::shared_ptr<moves::Move[]> opener_list = this -> figure -> opener_list;

            for (index_t i = 0; i < num_openers; i++){
                if (opener_list[i].sees(*(this -> board), this -> position, target, this -> player_index)){
                    return true;
                }
            }

            if (this -> figure -> open_exclusive){
                return false;
            }
        }

        index_t num_moves = this -> figure -> num_moves;
        std::shared_ptr<moves::Move[]> move_list = this -> figure -> move_list;

        for (index_t i = 0; i < num_moves; i++){
            if (move_list[i].sees(*(this -> board), this -> position, target, this -> player_index)){
                return true;
            }
        }

        return false;
    }

    const moves::Move* which_sees(const Index<n>& target) const {
        if (this -> dead) {
            return nullptr;
        }

        if (!this -> has_moved){
            index_t num_openers = this -> figure -> num_openers;
            std::shared_ptr<moves::Move[]> opener_list = this -> figure -> opener_list;

            for (index_t i = 0; i < num_openers; i++){
                if (opener_list[i].sees(*(this -> board), this -> position, target, this -> player_index)){
                    return &opener_list[i];
                }
            }

            if (this -> figure -> open_exclusive){
                return nullptr;
            }
        }

        index_t num_moves = this -> figure -> num_moves;
        std::shared_ptr<moves::Move[]> move_list = this -> figure -> move_list;

        for (index_t i = 0; i < num_moves; i++){
            if (move_list[i].sees(*(this -> board), this -> position, target, this -> player_index)){
                return &move_list[i];
            }
        }

        return nullptr;
    }
};


template<index_t n>
struct game::Player{
    const index_t index;

    value_t material;

    std::set<Piece> pawns;
    std::set<Piece> pieces;
    std::set<Piece> monarchs;

    Player(index_t index, value_t material, std::set<Piece>&& pawns, std::set<Piece>&& pieces, std::set<Piece>&& monarchs) : index(index), material(material), pawns(pawns), pieces(pieces), monarchs(monarchs), {}
    
    bool army_sees(const Index<n>& target) const {
        for (const Piece& piece : this -> pieces){
            if (piece.sees(target)){
                return true;
            }
        }

        for (const Piece& pawn : this -> pawns){
            if (pawn.sees(target)){
                return true;
            }
        }

        return false;
    }

    bool monarchs_see(const Index<n>& target) const {
        for (const Piece& monarch : this -> monarchs){
            if (monarch.sees(target)){
                return true;
            }
        }

        return false;
    }
};


template <index_t n, index_t p>
struct game::Instance{
    Grid<Piece*, n> board;
    Tuple<Player, p> players;
    
    Tuple<Action<n>, p> round;
    index_t turn;

    std::vector<Tuple<Action<n>, p>> history;


    Instance(Grid<Piece*, n>&& board, Tuple<Player, p>&& players) : board(board), turn(0), players(players), history() {}

    Instance(const Instance&) = default;
    Instance(Instance&&) = default;
    
    ~Instance() = default;


    json execute(const Index<n>& start, const Index<n>& end) const {
        try{
            this -> move(start, end);
        } catch(const std::exception& e){
            return {
                {"label", "error"},
                {"content", e.what()}
            }
        }
        if (this -> post_move_and_vet()){
            json r = std::move(this -> move_json);
            this -> move_json = nullptr;
            return r;
        } else {
            return nullptr;
        }
    }


    json serialize() const {
        json _board = this -> tuple_to_json(this -> board.get_shape());
        json _history = this -> history_to_json(this -> history);
        json _round = this -> round_to_json(this -> round);
        json _players = this -> players_to_json(this -> players);

        return {
            {"board", _board},
            {"players", _players},
            {"round", _round},
            {"turn", this -> turn},
            {"history", _history}
        }
    }


    private:

        json move_json;

        json move(const Index<n>& start, const Index<n>& end) const {
            Piece* piece = this -> board[start];

            if (piece == nullptr) {
                throw std::runtime_error("empty");
            } 

            const moves::Move* move = piece -> which_sees(end);

            if (move == nullptr){
                throw std::runtime_error("illegal");
            } else {
                Piece* target_piece = this -> board[end + piece -> capture_displacement];

                if (target_piece != nullptr){
                    target_piece -> dead = true;
                }

                piece -> position = end;
                this -> board[start] = nullptr;
                this -> board[end] = piece;

                if (this -> in_check(piece -> player_index)) {
                    piece -> position = start;
                    this -> board[start] = piece;
                    this -> board[end] = target_piece;

                    if (target_piece != nullptr){
                        target_piece -> dead = false;
                    }

                    throw std::runtime_error("check");
                } else {
                    this -> history.emplace_back(start, end);
                    
                    if (target_piece == nullptr){
                        json die = nullptr;
                    } else {
                        json die = this -> tuple_to_json(target_piece -> position); 
                    }

                    this -> move_json = {
                        {"label", "move"},
                        {"action", this -> action_to_json(this -> history.back())},
                        {"die", die},
                    };
                }
            }
        }

        bool post_move_and_vet() const {}



        bool in_check(index_t player_index) const {
            const Player<n>& player = this -> players[player_index];

            if (player -> monarchs.size() == 1){
                const Piece& king = player -> monarchs[0];

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

        json tuple_to_json(const Tuple<index_t, n>& i) const{
            json j = json::array();

            for (index_t k; k < n; k++){
                j.push_back(i[k]);
            }

            return j;
        }

        Tuple<index_t, n> tuple_from_json(const json& j) const {
            Tuple<index_t, n> temp;

            for (index_t k; k < n; k++){
                temp[k] = j[k];
            }

            return temp;
        }

        Index<n> index_from_json(const json& j) const{
            Tuple<index_t, n> temp;

            for (index_t k; k < n; k++){
                temp[k] = j[k];
            }

            return Index<n>(*this, std::move(temp));
        }

        json action_to_json(const Action<n>& a) const {
            json j = json::array();
            j.push_back(this -> tuple_to_json(a[0]));
            j.push_back(this -> tuple_to_json(a[1]));
            return j;
        }

        Action<n> action_from_json(const json& j) const {
            return Action<n>(
                this -> index_from_json(j[0]),
                this -> index_from_json(j[1])
            )
        }


        json round_to_json(const Tuple<Action<n>, p>& r) const{
            json j = json::array();

            for (index_t k; k < n; k++){
                j.push_back(std::move(this -> action_to_json(r[k])));
            }

            return j;
        }

        Tuple<Action<n>, p> round_from_json(const json& j) const{
            
            Tuple<Action<n>, p> r;

            for (index_t k; k < j.size(); k++){
                r[k] = std::move(this -> action_from_json(j[k]));
            }

            return r;
        }


        json history_to_json(const std::vector<Tuple<Action<n>, p>>& h) const{
            json j = json::array();

            for (index_t k; k < h.size(); k++){
                j.push_back(std::move(this -> round_to_json(h[k])));
            }

            return j;
        }

        std::vector<Tuple<Action<n>, p>> history_from_json(const json& j) const{
            
            std::vector<Tuple<Action<n>, p>> h;

            for (index_t k; k < j.size(); k++){
                h.push_back(std::move(this -> round_from_json(j[k])));
            }

            return h;
        }


        //TODO: fix the promotion_list paradigm.
        json piece_to_json(const Piece<n>& pi) const {
            json promotion_list = json::array();
            for (index_t i = 0; i < pi.num_promotions; i++){
                promotion_list.push_back(pi.promotion_list[i]); 
            }

            return {
                {"name", pi.name},
                {"index", pi.index},
                {"position", this -> tuple_to_json(pi.position)},
                {"figure", figure -> name},
                {"player_index", pi.player_index},
                {"promotion_list", std::move(promotion_list)},
                {"num_promotions", pi.num_promotions},
                {"dead", pi.dead},
                {"has_moved", pi.has_moved},
                {"just_opened", pi.just_opened}
            };
        }

        Piece piece_from_json(const json& j, std::shared_ptr<Instance> board_ptr) const {
            index_t num_promotions = j["num_promotions"];
            const json& json_promotion_list = j["promotion_list"];

            std::shared_ptr<index_t[]> promotion_list = std::make_shared<index_t[]>(num_promotions);

            for (index_t i = 0; i < num_promotions; i++){
                promotion_list[i] = json_promotion_list[i]; 
            }

            return Piece<n>(
                j["name"], 
                j["index"], 
                this -> index_from_json(j["position"]),
                moves::Figure::resolve(j["figure"]),
                board_ptr,
                j["player_index"],
                promotion_list,
                num_promotions,
                j["promotion_axis"],
                j["dead"],
                j["has_moved"],
                j["just_opened"]
            );
        }


        json player_to_json(const Player<n>& pl) const {
            json pieces = json::array();
            json pawns = json::array();
            json monarchs = json::array();

            for (const Piece& piece : pl.pieces){
                pieces.push_back(this -> piece_to_json(piece));
            }

            for (const Piece& pawn : pl.pawns){
                pawns.push_back(this -> piece_to_json(pawn));
            }

            for (const Piece& monarch : pl.monarchs){
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

