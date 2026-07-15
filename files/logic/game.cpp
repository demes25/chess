// Demetre Seturidze
// Chess
// Game

#include"logic.hpp"
#include"moves.cpp"

using namespace structs;

template <index_t n>
struct game::Piece{
    const char* name;
    const index_t index;
    mutable Index<n> position;

    const std::shared_ptr<moves::Figure<n>> figure;
    mutable std::shared_ptr<game::Board> board;

    const index_t player_index;

    const std::shared_ptr<index_t[]> promotion_list;
    const index_t promotion_axis;

    mutable bool dead;

    mutable bool has_moved;
    mutable bool just_opened;

    Piece(const char* name, index_t index, Tuple<index_t, n>&& position, std::shared_ptr<moves::Figure<n>> figure, index_t player_index, std::shared_ptr<index_t[]> promotion_list, index_t promotion_axis) : name(name), index(index), position(position), figure(figure), player_index(player_index), promotion_list(promotion_list), promotion_axis(promotion_axis){}
    
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

    std::set<game::Piece> pawns;
    std::set<game::Piece> pieces;
    std::set<game::Piece> monarchs;

    Player(index_t index, std::set<game::Piece>&& pawns, std::set<game::Piece>&& pieces, std::unique_ptr<game::Piece>&& monarchs) : index(index), pawns(pawns), pieces(pieces), monarchs(monarchs) {}
    
    bool army_sees(const Index<n>& target) const {
        for (game::Piece& piece : this -> pieces){
            if (piece.sees(target)){
                return true;
            }
        }

        for (const game::Piece& pawn : this -> pawns){
            if (pawn.sees(target)){
                return true;
            }
        }

        return false;
    }

    bool monarchs_see(const Index<n>& target) const {
        for (const game::Piece& monarch : this -> monarchs){
            if (monarch.sees(target)){
                return true;
            }
        }

        return false;
    }
};


template <index_t n, index_t p>
struct game::Game{
    structs::Grid<std::shared_ptr<game::Piece>, n> board;
    structs::Tuple<std::shared_ptr<game::Player>, p> players;
    index_t turn;

    std::vector<MoveRecord> history;


    Game(structs::Grid<std::shared_ptr<game::Piece>, n>&& board, structs::Tuple<std::shared_ptr<game::Player>, p>&& players) : board(board), turn(0), players(players), history() {}

    Game(const Game&) = default;
    Game(Game&&) = default;
    
    ~Game() = default;



    bool move(const Index<n>& start, const Index<n>& end) const {
        std::shared_ptr<game::Piece> piece = this -> board[start];

        if (piece == nullptr) {
            return false;
        } 

        const moves::Move* move = piece -> which_sees(end);

        if (move == nullptr){
            return false;
        } else {
            std::shared_ptr<game::Piece> target_piece = this -> board[end + piece -> capture_displacement];

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

                return false;
            } else {
                this -> history.emplace_back(start, end);
                return true;
            }
        }
    }


    bool in_check(index_t player_index) const {
        std::shared_ptr<game::Player> player = this -> players[player_index];

        if (player -> monarchs.size() == 1){
            const game::Piece& king = player -> monarchs[0];

            for (index_t i = 0; i < p; i++){
                if (i != player_index){
                    std::shared_ptr<game::Player> opponent = this -> players[i];
                    if (opponent -> army_sees(king.position)){
                        return true;
                    }
                }
            }
        }

        return false;
    }

    private:


        
};

