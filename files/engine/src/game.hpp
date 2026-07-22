// Demetre Seturidze
// Chess
// Game

#ifndef GAME
#define GAME

#include"moves.hpp"

using namespace structs;
using namespace moves;

namespace game{
    template <index_t n>
    struct Piece{
        mutable Index<n> position;

        const sptr<Figure<n>> figure;

        const index_t player_index;

        const std::vector<std::string> promotion_list;
        const index_t promotion_axis;
        const index_t promotion_index;
        mutable bool promoted;

        mutable bool dead;

        mutable bool has_moved;
        mutable bool just_opened; // JUST_OPENED marks a piece that played its first move in the current round, and the first move was marked "ONLY_OPENS".

        Piece(
            Index<n>&& position, 
            sptr<Figure<n>> figure, 
            index_t player_index, 
            std::vector<std::string>&& promotion_list, 
            index_t promotion_axis, 
            index_t promotion_index, 
            bool promoted, 
            bool dead, 
            bool has_moved, 
            bool just_opened
        ) : position(std::forward<Index<n>>(position)), 
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
            Index<n>&& position, 
            sptr<Figure<n>> figure, 
            index_t player_index, 
            bool dead, 
            bool has_moved, 
            bool just_opened
        ) : position(std::forward<Index<n>>(position)), 
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

        bool sees(const Board<n>& board, const Index<n>& square) const {
            if (this -> dead || this -> promoted) {
                return false;
            }

            if (!this -> has_moved){
                if (this -> figure -> which_opener(board, this -> position, square, this -> player_index) != nullptr){
                    return true;
                } else if (this -> figure -> open_exclusive){
                    return false;
                }
            }

            return (this -> figure -> which_move(board, this -> position, square, this -> player_index) != nullptr);
        }

        sptr<Move<n>> which_sees(const Board<n>& board, const Index<n>& square) const {
            if (this -> dead || this -> promoted) {
                return nullptr;
            }

            if (!this -> has_moved){
                sptr<Move<n>> opener = this -> figure -> which_opener(board, this -> position, square, this -> player_index);
                if (opener != nullptr) {
                    return opener;
                } else if (this -> figure -> open_exclusive){
                    return nullptr;
                }
            }

            return this -> figure -> which_move(board, this -> position, square, this -> player_index);
        }

        virtual void populate(MoveMap<n>& map, const Board<n>& board) const {
            if (this -> dead || this -> promoted) {
                return;
            }

            if (!this -> has_moved){
                this -> figure -> populate_openers(map, board, this -> position, this -> player_index);

                if (this -> figure -> open_exclusive){
                    return;
                }
            }

            this -> figure -> populate_moves(map, board, this -> position, this -> player_index);
        }


        // TODO: instead of true/false, make promoted hold a pointer to the piece it promoted to.
        sptr<Piece<n>> promoted_piece(index_t i) {
            this -> promoted = true;

            const std::string& promotion_fig = this -> promotion_list[i];

            return std::make_shared<Piece<n>>(
                Index<n>(this -> position),
                Figure<n>::resolve(promotion_fig),
                this -> player_index, 
                false,
                false, 
                false
            );
        }
    };

    template<index_t n>
    struct Player{
        index_t index;

        value_t material;

        std::vector<sptr<Piece<n>>> pieces;
        std::vector<sptr<Piece<n>>> monarchs;

        std::vector<sptr<Piece<n>>> just_opened; // a list of pieces that were JUST_OPENED

        Player(
            index_t index, 
            value_t material, 
            std::vector<sptr<Piece<n>>>&& pieces, 
            std::vector<sptr<Piece<n>>>&& monarchs,
            std::vector<sptr<Piece<n>>>&& just_opened = std::move(std::vector<sptr<Piece<n>>>())
        ) : index(index), 
            material(material), 
            pieces(std::forward<std::vector<sptr<Piece<n>>>>(pieces)), 
            monarchs(std::forward<std::vector<sptr<Piece<n>>>>(monarchs)),
            just_opened(std::forward<std::vector<sptr<Piece<n>>>>(just_opened)) {}

        Player() : index(0), material(0), pieces(), monarchs() {}

        Player(Player&&) = default;
        Player(const Player&) = default;
        

        Player& operator=(Player&&) = default;
        Player& operator=(const Player&) = default;

        // PREPS FOR THE NEXT TURN
        // i.e. all pieces that JUST_OPENED in the last turn will have JUST_OPENED set to false
        void drain_last_opened() {
            if (!this -> just_opened.empty()){
                for (sptr<Piece<n>>& piece : this -> just_opened){
                    piece -> just_opened = false;
                }

                this -> just_opened = std::vector<sptr<Piece<n>>>();
            }
        }

        bool pieces_see(const Board<n>& board, const Index<n>& square) const {
            for (const sptr<Piece<n>>& piece : this -> pieces){
                if (piece -> sees(board, square)){
                    return true;
                }
            }

            return false;
        }

        bool monarchs_see(const Board<n>& board, const Index<n>& square) const {
            for (const sptr<Piece<n>>& monarch : this -> monarchs){
                if (monarch -> sees(board, square)){
                    return true;
                }
            }

            return false;
        }

        bool sees(const Board<n>& board, const Index<n>& square) const {
            return this -> monarchs_see(board, square) || this -> pieces_see(board, square);
        }




        std::vector<sptr<Piece<n>>> which_pieces_see(const Board<n>& board, const Index<n>& square) const {
            std::vector<sptr<Piece<n>>> result;

            for (const sptr<Piece<n>>& piece : this -> pieces){
                if (piece -> sees(board, square)){
                    result.push_back(&piece);
                }
            }

            return result;
        }

        std::vector<sptr<Piece<n>>> which_monarchs_see(const Board<n>& board, const Index<n>& square) const {
            std::vector<sptr<Piece<n>>> result;

            for (const sptr<Piece<n>>& monarch : this -> monarchs){
                if (monarch -> sees(board, square)){
                    result.push_back(&monarch);
                }
            }

            return result;
        }

        std::vector<sptr<Piece<n>>> which_see(const Board<n>& board, const Index<n>& square) const {
            std::vector<sptr<Piece<n>>> result;

            for (const sptr<Piece<n>>& piece : this -> pieces){
                if (piece -> sees(board, square)){
                    result.push_back(&piece);
                }
            }

            for (const sptr<Piece<n>>& monarch : this -> monarchs){
                if (monarch -> sees(board, square)){
                    result.push_back(&monarch);
                }
            }

            return result;
        }



        index_t how_many_pieces_see(const Board<n>& board, const Index<n>& square) const {
            index_t N = 0;

            for (const sptr<Piece<n>>& piece : this -> pieces){
                if (piece -> sees(board, square)){
                    N++;
                }
            }

            return N;
        }

        index_t how_many_monarchs_see(const Board<n>& board, const Index<n>& square) const {
            index_t N = 0;

            for (const sptr<Piece<n>>& monarch : this -> monarchs){
                if (monarch -> sees(board, square)){
                    N++;
                }
            }

            return N;
        }

        index_t how_many_see(const Board<n>& board, const Index<n>& square) const {
            return this -> how_many_pieces_see(board, square) + this -> how_many_monarchs_see(board, square);
        }
    };

    template<index_t n>
    using Action = Tuple<Index<n>, 2>;

    enum Status : char {
        UNBEGUN = '0', ONGOING, PROMOTING, CHECKMATE, STALEMATE, TIMEOUT, DRAW
    };

    template<index_t n>
    using Board = Grid<sptr<Piece<n>>, n>;

    template <index_t n, index_t p>
    struct Instance{
        Instance(
            const Tup<n>& shape,
            Tuple<Player<n>, p>&& players,
            double time
        ) : board(shape), 
            players(std::forward<Tuple<Player<n>, n>>(players)), 
            times(duration(time)), 
            turn(0), 
            turn_start_time(0),
            history(), 
            status(UNBEGUN), 
            promoting(nullptr) 
        {
            this -> set();

            this -> history.emplace_back();
            this -> round = &(this -> history.back());
        }

        Instance(Instance&&) = default;
        Instance& operator=(Instance&&) = default;
        ~Instance() = default;

        sptr<Piece<n>>& operator[](const Index<n>& i) {
            return this -> board[i];
        }

        const sptr<Piece<n>>& operator[](const Index<n>& i) const {
            return this -> board[i];
        }

        bool is_over() const {
            return (this -> status > PROMOTING);
        }

        
        Index<n> as_index(const Tup<n>& t) const {
            return Index<n>(t, this -> board);
        }

        Index<n> as_index(Tup<n>&& t) const {
            return Index<n>(std::move(t), this -> board);
        }

        // returns true if any OTHER players see the given square
        bool is_unsafe_for(const Index<n>& square, index_t player_index) const {
            for (index_t i = 0; i < p; i++){
                if (i != player_index){
                    const Player<n>& opponent = this -> players[i];
                    if (opponent.pieces_see(this -> board, square)){
                        return true;
                    }
                }
            }
            return false;
        }

        // returns true if the given player has only one monarch, and it is "seen" by any of the other players' pieces.
        bool in_check(index_t player_index) const {
            const Player<n>& player = this -> players[player_index];

            if (player.monarchs.size() == 1){
                const sptr<Piece<n>>& king = player.monarchs[0];

                if (this -> is_unsafe_for(king -> position, player_index)){
                    return true;
                }
            }

            return false;
        }

        // returns a std::vector containing the indices of all the players that are currently in check.
        std::vector<index_t> get_checks() const {
            std::vector<index_t> checks;

            for (index_t i = 0; i < p; i++){
                if (this -> in_check(i)){
                    checks.push_back(i);
                }
            }

            return checks;
        }

        // returns a std::vector containing the indices of all the players that are currently in check.
        std::vector<index_t> get_checks_except(index_t j) const {
            std::vector<index_t> checks;

            for (index_t i = 0; i < p; i++){
                if (i != j && this -> in_check(i)){
                    checks.push_back(i);
                }
            }

            return checks;
        }


        // returns a BitMap containing all the **legal** moves that the piece at the given index can make.
        // i.e., enforces checks
        MoveMap<n> legal_moves(const sptr<Piece<n>>& piece) {
            if (piece == nullptr){
                throw std::runtime_error("empty");
            }

            MoveMap<n> result(this -> board.get_shape());

            piece -> populate(result, this -> board);

            for (Index<n> j(result); j.is_valid(); ++j){
                const Move<n>* sp = result[j];        
                if (sp != nullptr){
                    if (sp -> type_str() == "Castle"){
                        Vector<n> displacement = j - (piece -> position);
                        Vector<n> unit = sp -> operator[](0);

                        arith_t scaling = displacement | unit;

                        Vector<n> direction = (scaling < 0) ? -unit : unit;
                        index_t lim = (scaling < 0) ? -scaling : scaling;
                        
                        Index<n> tracker = piece -> position;

                        for (index_t t = 0; t <= lim; t++){
                            if (this -> is_unsafe_for(tracker, piece -> player_index)){
                                result[j] = nullptr;
                                break;
                            }

                            tracker += direction;
                        }

                    } else if (this -> walks_into_check(piece, j, sp)){
                        result[j] = nullptr;
                    }
                }
            }

            return result;
        }
        

        void move(const Index<n>& start, const Index<n>& end) {
            this -> make_move(start, end);

            if (this -> status != PROMOTING) {
                this -> post_move();
            }
        }
        
        virtual void resolve_promotion(index_t i) {
            if (this -> status != PROMOTING) {
                this -> status_error();
            }

            this -> raw_promote(i);
            this -> post_move();
        }


        // NEEDS WORK!!
        // needs to adjust for castles !!
        template<typename F, typename... Args>
        decltype(auto) if_move(sptr<Piece<n>> piece, const Index<n>& end, const Move<n>* move_ptr, F&& func, Args&&... args) {
            Index<n> start_pos = piece -> position;
            Index<n> end_pos = end;
            Index<n> take_pos = end + move_ptr -> relative_capture;

            sptr<Piece<n>> target = this -> board[take_pos];
            
            bool move_status = piece -> has_moved;
            bool open_status = piece -> just_opened;

            this -> raw_move(piece, end_pos, target);
            this -> abide(piece, move_ptr);

            using Result = std::invoke_result_t<F&&, Args&&...>;

            if constexpr (std::is_void_v<Result>) {
                std::invoke(std::forward<F>(func),
                            std::forward<Args>(args)...);
                
                this -> raw_unmove(piece, start_pos, target);
                piece -> has_moved = move_status;
                piece -> just_opened = open_status;

            } else {
                Result result =
                    std::invoke(std::forward<F>(func),
                                std::forward<Args>(args)...);
                
                this -> raw_unmove(piece, start_pos, target);
                piece -> has_moved = move_status;
                piece -> just_opened = open_status;

                return result;
            }
        }


        
        friend std::ostream& operator<<(std::ostream& os, const Instance<n, p>& inst) {
            index_t index = 0;
            return inst.print_help(os, 0, index);
        }

        const Board<n>& look() const {
            return this -> board;
        }

        protected:
            Board<n> board;
            Tuple<Player<n>, p> players;
            Tuple<duration, p> times;

            std::vector<Tuple<Action<n>, p>> history;
            Tuple<Action<n>, p>* round;

            index_t turn;
            timestamp turn_start_time;

            Status status;
            sptr<Piece<n>> promoting;

            Instance(
                Board<n>&& board,
                Tuple<Player<n>, p>&& players,
                Tuple<duration, p>&& times,
                
                std::vector<Tuple<Action<n>, p>>&& history,
                index_t turn,
                timestamp turn_start_time,

                Status status,
                sptr<Piece<n>> promoting
            ) : board(std::forward<Board<n>>(board)), 
                players(std::forward<Tuple<Player<n>, n>>(players)), 
                times(std::forward<Tuple<duration, p>>(times)), 
                turn(turn), 
                turn_start_time(turn_start_time),
                history(std::forward<std::vector<Tuple<Action<n>, p>>>(history)), 
                status(status), 
                promoting(promoting) 
            {
                this -> set();

                if (this -> history.size() == 0){
                    this -> history.push_back(Tuple<Action<n>, p>());
                }
                this -> round = &(this -> history.back());
            }

            // empties the board and calls .show on all players
            void set() {
                this -> board.fill(nullptr);
                
                for (index_t i = 0; i < p; i++){
                    this -> show(this -> players[i]);
                }
            }
            
            // shows the piece on the board.
            void show(const sptr<Piece<n>>& piece) {
                if (piece != nullptr && !piece -> dead && !piece -> promoted){
                    this -> board[piece -> position] = piece;
                }
            }

            // shows the piece on the board.
            void show(Piece<n>& piece) {
                if (!(piece.dead || piece.promoted)){
                    this -> board[piece.position] = &piece;
                }
            }

            // shows all of this player's pieces on the board.
            void show(Player<n>& player) {
                for (const sptr<Piece<n>>& piece : player.pieces){
                    this -> show(piece);
                }
                
                for (const sptr<Piece<n>>& monarch : player.monarchs){
                    this -> show(monarch);
                }
            }
            
            // adds the given piece to the board.
            // if the position is occupied, raises error.
            // adds the piece to the corresponding player and shows it on the board.
            sptr<Piece<n>> add(sptr<Piece<n>> piece){
                if (this -> board[piece -> position] != nullptr){
                    throw std::runtime_error("occupied");
                }

                this -> players[piece -> player_index].pieces.push_back(piece);
                this -> show(piece);

                return piece;
            }

            // adds the given piece to the board.
            // if the position is occupied, overwrites.
            // adds the piece to the corresponding player and shows it on the board.
            sptr<Piece<n>> overwrite(sptr<Piece<n>> piece){
                this -> players[piece -> player_index].pieces.push_back(piece);
                this -> show(piece);

                return piece;
            }

            // adds the given monarch to the board.
            // if the position is occupied, raises error.
            // adds the monarch to the corresponding player and shows it on the board.
            sptr<Piece<n>> add_monarch(sptr<Piece<n>> monarch){
                if (this -> board[monarch -> position] != nullptr){
                    throw std::runtime_error("occupied");
                }

                this -> players[monarch -> player_index].monarchs.push_back(monarch);
                this -> show(monarch);

                return monarch;
            }

            // adds the given monarch to the board.
            // if the position is overwrites.
            // adds the monarch to the corresponding player and shows it on the board.
            sptr<Piece<n>> overwrite_monarch(sptr<Piece<n>> monarch){
                this -> players[monarch -> player_index].monarchs.push_back(monarch);
                this -> show(monarch);

                return monarch;
            }

            // sets piece -> dead to true and hides the piece from the board.
            void kill(sptr<Piece<n>> piece) {
                if (piece != nullptr && !piece -> dead && !piece -> promoted){
                    piece -> dead = true;
                    this -> board[piece -> position] = nullptr;
                }
            }

            // sets piece -> dead to false and shows the piece on the board.
            void unkill(sptr<Piece<n>> piece) {
                if (piece != nullptr && piece -> dead && !piece -> promoted){
                    piece -> dead = false;
                    this -> board[piece -> position] = piece;
                }
            }

            void raw_move(sptr<Piece<n>> piece, const Index<n>& end, sptr<Piece<n>> target = nullptr) {
                this -> board[piece -> position] = nullptr;
                this -> kill(target);
                piece -> position = end;
                this -> board[end] = piece;
            }

            void raw_unmove(sptr<Piece<n>> piece, const Index<n>& start, sptr<Piece<n>> target = nullptr) {
                this -> board[piece -> position] = nullptr;
                this -> unkill(target);
                piece -> position = start;
                this -> board[start] = piece;
            }

            // if promoting is nullptr, raises error.
            // otherwise, sets promoting -> promoted = true, and calls .add on the promoted piece
            void raw_promote(index_t promotion_index) {
                if (promoting != nullptr) {
                    this -> overwrite(promoting -> promoted_piece(promotion_index));
                    promoting = nullptr;
                } else {
                    throw std::runtime_error("no promoting");
                }
            }


            // returns true if the given move walks into check.
            // TODO: this needs to be done better. what if at_i does not take at_j???
            bool walks_into_check(sptr<Piece<n>> piece, const Index<n>& end, const Move<n>* move_ptr) {
                return this -> if_move(
                    piece, 
                    end, 
                    move_ptr, 
                    [this](index_t i) {
                        return in_check(i);
                    },
                    piece -> player_index
                );
            }
            

            // updates the internal flags of the given piece depending on the move
            void abide(const sptr<Piece<n>>& piece, const Move<n>* move_ptr) {
                if (!piece -> has_moved){
                    piece -> has_moved = true;
                    if (move_ptr -> only_opens) {
                        piece -> just_opened = move_ptr -> only_opens;
                        this -> players[piece -> player_index].just_opened.push_back(piece);
                    }
                } 
            }



            void status_error() const {
                std::string status{(char)(this -> status)};
                std::string error_str("status ");
                error_str += status;

                throw std::runtime_error(error_str);
            }
    
            virtual void make_move(const Index<n>& start, const Index<n>& end) {
                if (this -> status > ONGOING) {
                    this -> status_error();
                }

                sptr<Piece<n>> piece = this -> board[start];
                sptr<Move<n>> move_ptr = this -> validate_and_get_move(piece, end);
                const sptr<Piece<n>> target_piece = this -> adjust_board_and_get_target(piece, move_ptr.get(), start, end);

                this -> set_current_action(start, end);

                this -> update_promoting(piece);
            }

            virtual void post_move() {
                std::vector<index_t> checks = this -> get_checks_except(this -> turn);
                
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

            void set_current_action(const Index<n>& start, const Index<n>& end) {
                this -> round -> operator[](this -> turn) = Action<n>(start, end);
            }

            // if (piece, end) represent an illegal move, raises error.
            // otherwise, returns a pointer to the Move object corresponding to the given move.
            sptr<Move<n>> validate_and_get_move(const sptr<Piece<n>> piece, const Index<n>& end) const {
                if (piece == nullptr) {
                    throw std::runtime_error("empty");
                } else if (piece -> player_index != this -> turn){
                    throw std::runtime_error("turn");
                } if (piece -> dead || piece -> promoted) {
                    throw std::runtime_error("panic");
                }

                sptr<Move<n>> move_ptr = piece -> which_sees(this -> board, end);

                if (move_ptr == nullptr){
                    throw std::runtime_error("illegal");
                }
                
                return move_ptr;
            }

            // updates the board according to the given piece and move.
            // i.e. -- captures any pieces that need to be captured, updates positions, etc...
            // if the given move "walks into" check, undoes everything and raises error.
            // otherwise, returns a pointer to the piece, if any, that was captured.
            //
            // IF the given move is a castle, then checks for castle validity (i.e. not to castle through check) and returns the partner piece (i.e. the rook)
            sptr<Piece<n>> adjust_board_and_get_target(sptr<Piece<n>> piece, const Move<n>* move_ptr, const Index<n>& start, const Index<n>& end) {
                if (move_ptr -> type_str() == "Castle"){
                    Vector<n> displacement = end - start;
                    Vector<n> unit = move_ptr -> operator[](0);

                    index_t axis = unit.first_nonzero();

                    arith_t scaling = displacement | unit;

                    Vector<n> direction = (scaling < 0) ? -unit : unit;
                    index_t lim = (scaling < 0) ? -scaling : scaling;
                    
                    Index<n> tracker = start;

                    for (index_t t = 0; t <= lim; t++){
                        if (this -> is_unsafe_for(tracker, piece -> player_index)){
                            throw std::runtime_error("check");
                        }

                        tracker += direction;
                    }

                    // WE HAVE TO ACCESS THE ROOK
                    Index<n> partner_index = start;
                    if (scaling < 0){
                        partner_index.zero_out(axis);
                    } else {
                        partner_index.max_out(axis);
                    }


                    this -> raw_move(piece, end);
                    this -> abide(piece, move_ptr);
                
                    Index<n> partner_end = end-direction;
                    sptr<Piece<n>> partner = this -> board[partner_index];
                    
                    this -> raw_move(partner, partner_end);
                    this -> abide(partner, move_ptr);

                    return partner;
                } else {
                    sptr<Piece<n>> target_piece = this -> board[end + move_ptr -> relative_capture];

                    this -> raw_move(piece, end, target_piece);

                    if (this -> in_check(this -> turn)) {
                        this -> raw_unmove(piece, start, target_piece);
                        throw std::runtime_error("check");
                    }

                    this -> abide(piece, move_ptr);

                    return target_piece;
                }
            }

            // if the piece is not on its promotion square, returns false.
            // if the piece is on its promotion square, then:
            //    -  if the piece can only promote to one thing, automatically promotes and returns true.
            //    -  otherwise, caches the unfinished promotion, sets status to PROMOTING and returns false
            bool update_promoting(sptr<Piece<n>> piece) {
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
            
            // updates the times, places the given action in history and calls .next_turn.
            // returns the duration of the move.
            duration advance_turn(){
                timestamp turn_end_time = timer::now();

                duration time_dif;

                if (this -> status == UNBEGUN){
                    this -> status = ONGOING;
                    this -> turn_start_time = turn_end_time;
                    time_dif = duration(0);
                } 

                else {
                    time_dif = turn_end_time - this -> turn_start_time;
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
                    this -> round = nullptr;
                    this -> history.emplace_back();
                    this -> round = &(this -> history.back());
                }

                this -> players[this -> turn].drain_last_opened();
            }

            // if the next player is in check and has no legal moves, sets status to CHECKMATE
            // if the next player is not in check but has no legal moves, sets status to STALEMATE
            // otherwise sets the status to ONGOING.
            void update_game_status(bool next_in_check) {

                bool has_legal_moves = false;

                const Player<n>& player = this -> players[this -> turn];
                
                for (const sptr<Piece<n>>& monarch : player.monarchs){
                    if (this -> legal_moves(monarch).any()){
                        has_legal_moves = true;
                        break;
                    }
                }

                for (const sptr<Piece<n>>& piece : player.pieces) {
                    if (this -> legal_moves(piece).any()){
                        has_legal_moves = true;
                        break;
                    }
                }

                if (!has_legal_moves){
                    if (next_in_check){
                        this -> status = CHECKMATE;
                    } else {
                        this -> status = STALEMATE;
                    }
                } else {
                    this -> status = ONGOING;
                }
            }



            std::ostream& print_help(std::ostream& os, index_t axis, index_t& index) const {
                if (axis == n-1){
                    for (index_t k = 0; k < axis; ++k){
                        os << indent;
                    }
                    os << '[';
            
                    index_t last = this -> board.get_shape()[axis] - 1;
                    for(index_t i = 0; i < last; ++i){
                        const sptr<Piece<n>> a = this -> board[index++];

                        if (a == nullptr){
                            os << '.' << '\t';
                        } else {
                            os << a -> figure -> name[0] << (a -> player_index == 0 ? 'w' : 'b') << '\t';
                        }
                    }

                    const sptr<Piece<n>> a = this -> board[index++];

                    if (a == nullptr){
                        os << '.' << ']';
                    } else {
                        os << a -> figure -> name[0] << (a -> player_index == 0 ? 'w' : 'b') << ']';
                    }

                } else {
                    for (index_t k = 0; k < axis; ++k){
                        os << indent;
                    }
                    os << '[' << std::endl;

                    index_t last = this -> board.get_shape()[axis] - 1;
                    for(index_t i = 0; i < last; ++i){
                        this -> print_help(os, axis+1, index);
                        os << ',' << std::endl;
                    }

                    this -> print_help(os, axis+1, index);
                    os << std::endl;
                    for (index_t k = 0; k < axis; ++k){
                        os << indent;
                    }
                    os << ']';
                }

                return os;
            }

    };
}
#endif
