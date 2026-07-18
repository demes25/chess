// Demetre Seturidze
// Chess
// Game

#ifndef GAME
#define GAME

#include"logic.hpp"

using namespace structs;
using namespace moves;

template <index_t n>
struct game::Piece{
    mutable Index<n> position;

    const std::shared_ptr<Figure<n>> figure;

    const index_t player_index;

    const std::vector<std::string> promotion_list;
    const index_t promotion_axis;
    const index_t promotion_index;
    mutable bool promoted;

    mutable bool dead;

    mutable bool has_moved;
    mutable bool just_opened;

    Piece(
        Tup<n>&& position, 
        std::shared_ptr<Figure<n>> figure, 
        index_t player_index, 
        std::vector<std::string>&& promotion_list, 
        index_t promotion_axis, 
        index_t promotion_index, 
        bool promoted, 
        bool dead, 
        bool has_moved, 
        bool just_opened
    ) : position(std::forward<Tup<n>>(position)), 
        figure(figure), 
        player_index(player_index), 
        promotion_list(std::forward<std::vector<std::string>>(promotion_list)), 
        promotion_axis(promotion_axis), 
        promotion_index(promotion_index), 
        promoted(promoted), 
        dead(dead), 
        has_moved(has_moved), 
        just_opened(just_opened){}
    
    Piece(
        Tup<n>&& position, 
        std::shared_ptr<Figure<n>> figure, 
        index_t player_index, 
        bool dead, 
        bool has_moved, 
        bool just_opened
    ) : position(std::forward<Tup<n>>(position)), 
        figure(figure), 
        player_index(player_index), 
        promotion_list(), 
        promotion_axis(0), 
        promotion_index(0), 
        promoted(false), 
        dead(dead), 
        has_moved(has_moved), 
        just_opened(just_opened){}
    
    Piece(Piece&&) = default;
    Piece(const Piece&) = default;

    ~Piece() = default;

    bool sees(const Grid<Piece<n>*, n>& board, const Index<n>& target) const {
        if (this -> dead || this -> promoted) {
            return false;
        }

        if (!this -> has_moved){
            if (this -> figure -> which_opener(board, this -> position, target, this -> player_index) != nullptr){
                return true;
            } else if (this -> figure -> open_exclusive){
                return false;
            }
        }

        return (this -> figure -> which_move(board, this -> position, target, this -> player_index) != nullptr);
    }

    const Move<n>* which_sees(const Grid<Piece<n>*, n>& board, const Index<n>& target) const {
        if (this -> dead || this -> promoted) {
            return nullptr;
        }

        if (!this -> has_moved){
            const Move<n>* opener = this -> figure -> which_opener(board, this -> position, target, this -> player_index);
            if (opener != nullptr) {
                return opener;
            } else if (this -> figure -> open_exclusive){
                return nullptr;
            }
        }

        return this -> figure -> which_move(board, this -> position, target, this -> player_index);
    }

    Piece<n> promoted_piece(index_t i) {
        this -> promoted = true;

        const std::string& promotion_fig = this -> promotion_list[i];

        return Piece<n>(
            this -> position,
            Figure<n>::resolve(promotion_fig),
            this -> player_index, 
            false,
            false, 
            false
        );
    }
};

template<index_t n>
struct game::Player{
    const index_t index;

    value_t material;

    std::vector<Piece<n>> pieces;
    std::vector<Piece<n>> monarchs;

    Player(
        index_t index, 
        value_t material, 
        std::vector<Piece<n>>&& pieces, 
        std::vector<Piece<n>>&& monarchs
    ) : index(index), 
        material(material), 
        pieces(std::forward<std::vector<Piece<n>>>(pieces)), 
        monarchs(std::forward<std::vector<Piece<n>>>(monarchs)) {}
    
    bool pieces_see(const Index<n>& target) const {
        for (const Piece<n>& piece : this -> pieces){
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
        return this -> monarchs_see(target) || this -> pieces_see(target);
    }




    std::vector<Piece<n>*> which_pieces_see(const Index<n>& target) const {
        std::vector<Piece<n>*> result;

        for (Piece<n>& piece : this -> pieces){
            if (piece.sees(target)){
                result.push_back(&piece);
            }
        }

        return result;
    }

    std::vector<Piece<n>*> which_monarchs_see(const Index<n>& target) const {
        std::vector<Piece<n>*> result;

        for (Piece<n>& monarch : this -> monarchs){
            if (monarch.sees(target)){
                result.push_back(&monarch);
            }
        }

        return result;
    }

    std::vector<Piece<n>*> which_see(const Index<n>& target) const {
        std::vector<Piece<n>*> result;

        for (Piece<n>& piece : this -> pieces){
            if (piece.sees(target)){
                result.push_back(&piece);
            }
        }

        for (Piece<n>& monarch : this -> monarchs){
            if (monarch.sees(target)){
                result.push_back(&monarch);
            }
        }

        return result;
    }



    index_t how_many_pieces_see(const Index<n>& target) const {
        index_t n = 0;

        for (const Piece<n>& piece : this -> pieces){
            if (piece.sees(target)){
                n++;
            }
        }

        return n;
    }

    index_t how_many_monarchs_see(const Index<n>& target) const {
        index_t n = 0;

        for (const Piece<n>& monarch : this -> monarchs){
            if (monarch.sees(target)){
                n++;
            }
        }

        return n;
    }

    index_t how_many_see(const Index<n>& target) const {
        return this -> how_many_pieces_see(target) + this -> how_many_monarchs_see(target);
    }
};

template <index_t n, index_t p>
struct game::Instance{
    Instance(
        Grid<Piece<n>*, n>&& board, 
        Tuple<Player<n>, p>&& players, 
        duration time
    ) : board(std::forward<Grid<Piece<n>*, n>>(board)), 
        players(std::forward<Tuple<Player<n>, n>>(players)),
        times(time),
        turn(0), 
        promoting(nullptr){} 

    Instance(Instance&&) = default;
    Instance& operator=(Instance&&) = default;
    ~Instance() = default;

    Piece<n>*& operator[](const Index<n>& i) {
        return this -> board[i];
    }

    const Piece<n>*& operator[](const Index<n>& i) const {
        return this -> board[i];
    }

    protected:
        Grid<Piece<n>*, n> board;
        Tuple<Player<n>, p> players;
        Tuple<duration, p> times;

        std::vector<Tuple<Action<n>, p>> history;
        Tuple<Action<n>>& round;

        index_t turn;
        timestamp turn_start_time;

        Status status;
        Piece<n>* promoting;

        Instance(
            Grid<Piece<n>*, n>&& board,
            Tuple<Player<n>, p>&& players,
            Tuple<duration, p>&& times,
            
            std::vector<Tuple<Action<n>, p>>&& history,
            index_t turn,
            timestamp turn_start_time,

            Status status,
            Piece<n>* promoting,
        ) : board(std::forward<Grid<Piece<n>*, n>>(board)), 
            players(std::forward<Tuple<Player<n>, n>>(players)), 
            times(std::forward<Tuple<duration, p>>(times)), 
            turn(turn), 
            turn_start_time(turn_start_time),
            history(std::forward<Tuple<Action<n>, p>>(history)), 
            status(status), 
            promoting(promoting) {
                
            if (this -> history.size() == 0){
                this -> history.push_back(Tuple<Action<n>, p>());
            }
            this -> round = this -> history.back();
        }


        
        // shows the piece on the board.
        void show(Piece<n>* piece) {
            if (piece != nullptr && !piece -> dead && !piece -> promoted){
                this -> board[piece -> position] = piece;
            }
        }
        
        // adds the given piece to the board.
        // if the position is occupied, raises error.
        // adds the piece to the corresponding player and shows it on the board.
        Piece<n>* add(Piece<n>&& piece){
            if (this -> board[piece.position] != nullptr){
                throw std::runtime_error("occupied");
            }

            std::vector<Piece<n>>& pieces = this -> players[piece.player_index].pieces;

            pieces.push_back(std::forward<Piece<n>>(piece));
            Piece<n>* result = &pieces.back();

            this -> show(result);

            return result;
        }

        // adds the given monarch to the board.
        // if the position is occupied, raises error.
        // adds the monarch to the corresponding player and shows it on the board.
        Piece<n>* add_monarch(Piece<n>&& monarch){
            if (this -> board[piece.position] != nullptr){
                throw std::runtime_error("occupied");
            }

            std::vector<Piece<n>>& monarchs = this -> players[monarch.player_index].monarchs;

            monarchs.push_back(std::forward<Piece<n>>(monarch));
            Piece<n>* result = &monarchs.back();

            this -> show(result);

            return result;
        }

        // sets piece -> dead to true and hides the piece from the board.
        void kill(Piece<n>* piece) {
            if (piece != nullptr && !piece -> dead && !piece -> promoted){
                piece -> dead = true;
                this -> board[piece -> position] = nullptr;
            }
        }

        // sets piece -> dead to false and shows the piece on the board.
        void unkill(Piece<n>* piece) {
            if (piece != nullptr && piece -> dead && !piece -> promoted){
                piece -> dead = false;
                this -> board[piece -> position] = piece;
            }
        }

        // if promoting is nullptr, raises error.
        // otherwise, sets promoting -> promoted = true, and calls .add on the promoted piece
        void raw_promote(index_t promotion_index) {
            if (promoting != nullptr) {
                promoting -> promoted = true;
                this -> add(promoting -> promoted_piece(promotion_index));
                promoting = nullptr;
            } else {
                throw std::runtime_error("no promoting");
            }
        }




        
        void move(const Index<n>& start, const Index<n>& end) {
            this -> make_move();

            if (this -> status != PROMOTING) {
                this -> post_move();
            }
        }
        
        virtual void resolve_promotion(index_t i) {
            if (this -> status != PROMOTING) {
                throw std::runtime_error(std::string("status ") + std::string((char)(this -> status)));
            }

            this -> raw_promote(i);
            this -> post_move();
        }

        virtual void make_move(const Index<n>& start, const Index<n>& end) {
            if (this -> status > ONGOING) {
                throw std::runtime_error(std::string("status ") + std::string((char)(this -> status)));
            }

            Piece<n>* piece = this -> board[start];
            const Move<n>* move = this -> validate_and_get_move(piece, end);
            const Piece<n>* target_piece = this -> adjust_board_and_get_target(piece, move, start, end);

            this -> round[this -> turn] = Action<n>(start, end);
            
            this -> update_promoting(piece);
        }

        virtual void post_move() {
            std::vector<index_t> checks = this -> get_checks();
            
            this -> advance_turn();

            bool next_in_check = false;

            for (const index_t & check : checks){
                if (check == this -> turn){
                    next_in_check = true;
                    break;
                }
            }

            this -> update_game_status(next_in_check);
        }

        
        
        // if (piece, end) represent an illegal move, raises error.
        // otherwise, returns a pointer to the Move object corresponding to the given move.
        const Move<n>* validate_and_get_move(const Piece<n>* piece, const Index<n>& end) const {
            if (piece == nullptr) {
                throw std::runtime_error("empty");
            } else if (piece -> player_index != this -> turn){
                throw std::runtime_error("turn");
            } if (piece -> dead || piece -> promoted) {
                throw std::runtime_error("panic");
            }

            const Move<n>* move = piece -> which_sees(end);

            if (move == nullptr){
                throw std::runtime_error("illegal");
            }
            
            return move;
        }

        // updates the board according to the given piece and move.
        // i.e. -- captures any pieces that need to be captured, updates positions, etc...
        // if the given move "walks into" check, undoes everything and raises error.
        // otherwise, returns a pointer to the piece, if any, that was captured.
        const Piece<n>* adjust_board_and_get_target(Piece<n>* piece, const Move<n>* move, const Index<n>& start, const Index<n>& end) {
            Piece<n>* target_piece = this -> board[end + move -> relative_capture];
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
            }

            return target_piece;
        }

        // returns true if the given player has only one monarch, and it is "seen" by any of the other players' pieces.
        bool in_check(index_t player_index) const {
            const Player<n>& player = this -> players[player_index];

            if (player -> monarchs.size() == 1){
                const Piece<n>& king = player -> monarchs[0];

                for (index_t i = 0; i < p; i++){
                    if (i != player_index){
                        const Player<n>& opponent = this -> players[i];
                        if (opponent.pieces_see(king.position)){
                            return true;
                        }
                    }
                }
            }

            return false;
        }


        // if the piece is not on its promotion square, returns false.
        // if the piece is on its promotion square, then:
        //    -  if the piece can only promote to one thing, automatically promotes and returns true.
        //    -  otherwise, caches the unfinished promotion, sets status to PROMOTING and returns false
        bool update_promoting(Piece<n>* piece) {
            if (piece -> promotion_list.size() != 0 && piece -> position[piece -> promotion_axis] == piece -> promotion_index){
                if (piece -> promotion_list.size() == 1){
                    this -> raw_promote(0);
                    return true;
                } else {
                    this -> promoting = piece;
                    this -> status = PROMOTING;
                }
            }
            return false;
        }
        
        // returns a std::vector containing the indices of all the players that are currently in check.
        std::vector<index_t> get_checks() {
            std::vector<index_t> checks;

            for (index_t i = 0; i < p; i++){
                if (i != this -> turn && this -> in_check(i)){
                    checks.push_back(i);
                }
            }

            return std::move(checks);
        }

        // updates the times, places the given action in history and calls .next_turn.
        // returns the duration of the move.
        duration advance_turn(const Index<n>& start, const Index<n>& end){
            timestamp turn_end_time = clock::now();

            duration time_dif;

            if (this -> status == UNBEGUN){
                this -> status = ONGOING;
                this -> turn_start_time = turn_end_time;
                time_dif = duration(0);
            } 

            else if (this -> status == ONGOING) {
                duration time_dif = turn_end_time - this -> turn_start_time;
                this -> times[this -> turn] -= time_dif;
            }
            
            this -> next_turn();
            this -> turn_start_time = turn_end_time;

            return time_dif;
        }

        // registers the given action to the history and 
        void next_turn() {
            this -> turn = (this -> turn + 1) % p;
            
            if (this -> turn == 0){
                this -> history.push_back(Tuple<Action<n>, p>());
                this -> round = this -> history.back();
            }
        }

        // if the next player is in check and has no legal moves, sets status to CHECKMATE
        // if the next player is not in check but has no legal moves, sets status to STALEMATE
        // otherwise sets the status to ONGOING.
        void update_game_status(bool next_in_check) {
            if (this -> no_legal_moves()){
                if (next_in_check){
                    this -> status = CHECKMATE;
                } else {
                    this -> status = STALEMATE;
                }
            } else {
                this - > status = ONGOING;
            }
        }

        bool no_legal_moves();

};

#endif