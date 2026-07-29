// Demetre Seturidze
// Chess
// Engines

#ifndef ENGINES
#define ENGINES

#include"objects.hpp"

using namespace objects;
using namespace moves;

// RIGHT NOW: winning and losing is very much defined for a 2-player chess game. as such, determining who wins and who loses 
// is not in the current form generalizable to higher numbers of players. KEEP THAT IN MIND.

namespace engines {

    template <index_t n, index_t p>
    struct Engine{
        static json game_sets;

        Engine(
            const Tup<n>& shape,
            Tuple<Player<n>, p>&& players,
            double time
        ) : board(shape), 
            players(std::forward<Tuple<Player<n>, n>>(players)), 
            times(duration(time)), 
            turn(0), 
            turn_start_time{},
            history(), 
            status(UNBEGUN), 
            promoting(nullptr),
            victor()
        {
            this -> set();

            this -> history.emplace_back();
            this -> round = &(this -> history.back());
        }

        Engine(Engine&&) = default;
        Engine& operator=(Engine&&) = default;
        ~Engine() = default;

        sptr<Piece<n>>& operator[](const Index<n>& i) {
            return this -> board[i];
        }

        const sptr<Piece<n>>& operator[](const Index<n>& i) const {
            return this -> board[i];
        }

        bool is_on() const {
            return (this -> status <= PROMOTING);
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
        

        void declare_timeout() {
            this -> status = TIMEOUT;
            this -> victor = (this -> turn + 1) % p;
        }

        void declare_draw() {
            this -> status = DRAW;
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


        
        friend std::ostream& operator<<(std::ostream& os, const Engine<n, p>& inst) {
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

            std::optional<index_t> victor;

            Engine(
                Board<n>&& board,
                Tuple<Player<n>, p>&& players,
                Tuple<duration, p>&& times,
                
                std::vector<Tuple<Action<n>, p>>&& history,
                index_t turn,
                timestamp turn_start_time,

                Status status,
                sptr<Piece<n>> promoting,
                std::optional<index_t> victor
            ) : board(std::forward<Board<n>>(board)), 
                players(std::forward<Tuple<Player<n>, n>>(players)), 
                times(std::forward<Tuple<duration, p>>(times)), 
                turn(turn), 
                turn_start_time(turn_start_time),
                history(std::forward<std::vector<Tuple<Action<n>, p>>>(history)), 
                status(status), 
                promoting(promoting),
                victor(victor)
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
                        this -> victor = (this -> turn + p - 1) % p;
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

    template <index_t n, index_t p>
    json Engine<n, p>::game_sets = json::object();

    template <index_t n, index_t p>
    struct EvaluableEngine : public Engine<n, p> {
        using Engine<n, p>::Engine;

        EvaluableEngine(EvaluableEngine&&) = default;
        EvaluableEngine& operator=(EvaluableEngine&&) = default;
        ~EvaluableEngine() = default;

        //TODO: write

        private:
            double check_value;
            double threat_weight;

            double move_eval();
        
    };


    template <index_t n, index_t p>
    struct SerializableEngine : public Engine<n, p>{
        using Engine<n, p>::Engine;

        SerializableEngine(SerializableEngine&&) = default;
        SerializableEngine& operator=(SerializableEngine&&) = default;
        ~SerializableEngine() = default;

        static SerializableEngine instantiate(const std::string& set_name, double timer) {
            json setup = Engine<n, p>::game_sets.at(set_name);

            json times_arr = json::array();

            for (index_t i = 0; i < p; i++){
                times_arr.push_back(timer);
            }

            setup["times"] = times_arr;

            return SerializableEngine::deserialize(setup);
        }

        virtual void resolve_promotion(index_t i) {
            if (this -> status != PROMOTING) {
                this -> status_error();
            }

            this -> raw_promote(i);
            this -> move_event -> promote = i;

            this -> post_move();
        }


        // EXTERNAL SERIALIZATION

        // the following map to python Serializable objects (see netlib)
        // defined in AV.
        Reaction<n, p> execute(const Index<n>& start, const Index<n>& end) {
            try {
                this -> move(start, end);
                
                if (this -> status != PROMOTING) {
                    return *(this -> drain_event());
                } else {
                    return Response<p>{"promote"};
                }

            } catch(const std::exception& e){
                this -> move_event = std::nullopt;
                return Error{"InGame",  e.what()};
            }
        }

        Reaction<n, p> promote(index_t i) {
            try {
                this -> resolve_promotion(i);
                return *(this -> drain_event());
            } catch (const std::exception& e) {
                return Error{"InGame",  e.what()};
            }
        }
        

        // EXPOSED SERIALIZATION

        // the following are exposed to python
        Reaction<n, p> process(const Request<n>& a) {
            if (a.label == "action"){
                const Action<n>& c = std::get<Action<n>>(*(a.content));
                Index<n> start = this -> as_index(c[0]);
                Index<n> end = this -> as_index(c[1]);
                return this -> execute(start, end);
            } else if (a.label == "promotion") {
                index_t i = std::get<index_t>(*(a.content));
                return this -> promote(i);
            } else if (a.label == "times") {
                return this -> get_times();
            } else {
                return Error{"InGame", "invalid request"};
            }
        }

        Response<p> get_times() const {
            Tuple<double, p> times;

            for (index_t i = 0; i < p; i++){
                if (i == this -> turn && this -> status > UNBEGUN && this -> status < CHECKMATE){
                    duration elapsed_time = std::chrono::duration_cast<duration>(timer::now() - this -> turn_start_time);
                    times[i] = (this -> times[i] - elapsed_time).count();
                } else {
                    times[i] = this -> times[i].count();
                }
            }

            return {"times", times};
        }


        json layout() const {
            json k = json::array();

            for (index_t i = 0; i < p; i++){
                const Player<n>& player = this -> players[i];

                json arr = json::array();

                for (const sptr<Piece<n>>& piece : player.pieces) {
                    if (!(piece -> dead || piece -> promoted)){
                        arr.push_back({
                            {"name", piece -> figure -> name},
                            {"position", piece -> position},
                            {"promotion_list", piece -> promotion_list},
                            {"player_index", i},
                            {"__type__", "Piece"}
                        });
                    }
                }

                for (const sptr<Piece<n>>& piece : player.monarchs) {
                    if (!(piece -> dead || piece -> promoted)){
                        arr.push_back({
                            {"name", piece -> figure -> name},
                            {"position", piece -> position},
                            {"promotion_list", piece -> promotion_list},
                            {"player_index", i},
                            {"__type__", "Piece"}
                        });
                    }
                }

                k.push_back(arr);
            }

            return {
                {"dims", this -> board.get_shape()},
                {"armies", k},
                {"__type__", "Board"}
            };
        }

        

        std::string layout_str() const {
            return this -> layout().dump();
        }

        std::string to_str() const {
            std::ostringstream oss;
            oss << (*this);
            return oss.str();
        }


        // INTERNAL SERIALIZATION 

        json serialize() const {
            json promoting;

            if (this -> promoting == nullptr){
                promoting = nullptr;
            } else {
                promoting = this -> promoting -> position;
            }  

            duration t = this -> turn_start_time.time_since_epoch();

            return {
                {"board", this -> board.get_shape()},
                {"players", SerializableEngine::players_to_json(this -> players)},
                {"times", this -> serialize_static_times()},
                {"turn_start_time", t.count()},

                {"turn", this -> turn},
                {"history", this -> history},

                {"status", (char)this -> status},
                {"promoting", promoting},

                {"victor", this -> victor},

                {"move_event", this -> move_event}
            };
        }

        static SerializableEngine deserialize(const json& j) {
            Board<n> board(j.at("board").get<Tup<n>>());
            Tuple<Player<n>, p> players = SerializableEngine::players_from_json(j.at("players"), board);

            Tuple<duration, p> times;

            json json_times = j.at("times");

            for (index_t i = 0; i < p; i++){
                times[i] = duration(json_times.at(i).get<double>());
            }

            json j_start_time = j.value("turn_start_time", json(nullptr));
            timestamp turn_start_time;

            if (j_start_time.is_null()){
                turn_start_time = timestamp(timer::duration(0));
            } else {
                turn_start_time = timestamp(std::chrono::duration_cast<timer::duration>(duration{j.at("turn_start_time").get<double>()}));
            }
            SerializableEngine result(
                std::move(board), 
                std::move(players), 
                std::move(times),
                
                j.value("history", json::array()).get<std::vector<Tuple<Action<n>, p>>>(),
                j.value("turn", json(0)).get<index_t>(),
                turn_start_time,

                j.value("status", json(UNBEGUN)).get<Status>(),
                nullptr,
                j.value("victor", json(nullptr)).get<std::optional<index_t>>()
            );

            const json& promoting = j.value("promoting", json(nullptr));

            if (!promoting.is_null()){
                result.promoting = result.board[Index<n>(promoting.get<Tup<n>>(), board)];
            }
            
            return result;
        }


        std::string embed() const {
            return this -> serialize().dump();
        }

        static SerializableEngine disembed(const std::string& jstr) {
            return SerializableEngine::deserialize(json::parse(jstr));
        }

        
        protected:
            std::optional<Event<n, p>> move_event;

            virtual void make_move(const Index<n>& start, const Index<n>& end) {
                if (this -> status > ONGOING) {
                    this -> status_error();
                }

                sptr<Piece<n>> piece = this -> board[start];
                sptr<Move<n>> move_ptr = this -> validate_and_get_move(piece, end);
                const sptr<Piece<n>> target_piece = this -> adjust_board_and_get_target(piece, move_ptr.get(), start, end);
                
                this -> set_current_action(start, end);

                bool auto_promote = this -> update_promoting(piece);

                this -> move_event = Event<n, p>{std::vector<Action<n>>()};
                this -> move_event -> actions.push_back(Action<n>(start, end));


                if (move_ptr -> type_str() == "Castle"){
                    //TODO: LOTS of recalculating scaling with castles. not too big a deal but try to optimize at some point.
                    Vector<n> direction = move_ptr -> operator[](0);

                    arith_t scaling = (end - start) | direction;
                    Index<n> partner_start = target_piece -> position;

                    index_t axis = direction.first_nonzero();

                    if(scaling < 0){
                        partner_start.zero_out(axis);
                    } else {
                        partner_start.max_out(axis);
                    }

                    this -> move_event -> actions.push_back(Action<n>(partner_start, target_piece -> position));

                } else if (target_piece != nullptr){
                    this -> move_event -> die = target_piece -> position;
                }

                if (auto_promote){
                    this -> move_event -> promote = 0;
                }

            }

            virtual void post_move() {
                this -> move_event -> checks = this -> get_checks_except(this -> turn);
                    
                duration time_dif = this -> advance_turn();

                bool next_in_check = false;

                for (const index_t & check : *(this -> move_event -> checks)){
                    if (check == this -> turn){
                        next_in_check = true;
                        break;
                    }
                }

                this -> update_game_status(next_in_check);

                this -> move_event -> times = Tuple<double, p>();

                for (index_t i = 0; i < p; i++){
                    this -> move_event -> times -> operator[](i) = this -> times[i].count();
                }
                
                this -> move_event -> duration = time_dif.count();

                if (this -> status == CHECKMATE){
                    this -> move_event -> end = "checkmate";
                } else if (this -> status == STALEMATE){
                    this -> move_event -> end = "stalemate";
                }
            }


            std::optional<Event<n, p>> drain_event() {
                return std::exchange(this -> move_event, std::nullopt);
            }

            json serialize_static_times() const {
            json times = json::array();

            for (index_t i = 0; i < p; i++){
                if (i == this -> turn && this -> status > UNBEGUN){
                    duration elapsed_time = std::chrono::duration_cast<duration>(timer::now() - this -> turn_start_time);
                    times.push_back(
                        (this -> times[i] - elapsed_time).count()
                    );
                } else {
                    times.push_back(this -> times[i].count());
                }
            }

            return times;
        }


            static json piece_to_json(const sptr<Piece<n>>& pi) {
                return {
                    {"position", pi -> position},
                    {"figure", pi -> figure -> key},
                    {"player_index", pi -> player_index},
                    {"promotion_list", pi -> promotion_list},
                    {"promotion_axis", pi -> promotion_axis},
                    {"promotion_index", pi -> promotion_index},
                    {"promoted", pi -> promoted},
                    {"dead", pi -> dead},
                    {"has_moved", pi -> has_moved},
                    {"just_opened", pi -> just_opened}
                };
            }

            static sptr<Piece<n>> piece_from_json(const json& j, const Board<n>& board, index_t player_index) {
                return std::make_shared<Piece<n>>(
                    Index<n>(std::move(j.at("position").get<Tup<n>>()), board),
                    Figure<n>::resolve(j.at("figure").get<std::string>()),
                    j.value("player_index", json(player_index)).get<index_t>(),

                    j.value("promotion_list", json::array()).get<std::vector<std::string>>(),
                    j.value("promotion_axis", json(0)).get<index_t>(),
                    j.value("promotion_index", json(0)).get<index_t>(),
                    
                    j.value("promoted", json(false)).get<bool>(),
                    j.value("dead", json(false)).get<bool>(),
                    j.value("has_moved", json(false)).get<bool>(),
                    j.value("just_opened", json(false)).get<bool>()
                );
            }


            static json player_to_json(const Player<n>& pl) {
                json pieces = json::array();
                json monarchs = json::array();
                json just_opened = json::array();

                for (const sptr<Piece<n>>& piece : pl.pieces){
                    pieces.push_back(SerializableEngine::piece_to_json(piece));
                }

                for (const sptr<Piece<n>>& monarch : pl.monarchs){
                    monarchs.push_back(SerializableEngine::piece_to_json(monarch));
                }

                return {
                    {"index", pl.index},
                    {"material", pl.material},
                    {"pieces", pieces},
                    {"monarchs", monarchs}
                };
            }

            static Player<n> player_from_json(const json& j, const Board<n>& board, index_t index) {
                std::vector<sptr<Piece<n>>> pieces;
                std::vector<sptr<Piece<n>>> monarchs;
                std::vector<sptr<Piece<n>>> just_opened;

                const json& jpieces = j.at("pieces");
                const json& jmonarchs = j.at("monarchs");

                for (const json& piece : jpieces){
                    pieces.push_back(SerializableEngine::piece_from_json(piece, board, index));
                    if (pieces.back() -> just_opened){
                        just_opened.push_back(pieces.back());
                    }
                }

                for (const json& monarch : jmonarchs){
                    monarchs.push_back(SerializableEngine::piece_from_json(monarch, board, index));
                    if (monarchs.back() -> just_opened){
                        just_opened.push_back(monarchs.back());
                    }
                }

                return Player<n>(
                    j.value("index", json(index)).get<index_t>(),
                    j.at("material").get<value_t>(),
                    std::move(pieces),
                    std::move(monarchs),
                    std::move(just_opened)
                );
            }


            static json players_to_json(const Tuple<Player<n>, p>& ps){
                json j = json::array();

                for (index_t k = 0; k < p; k++){
                    j.push_back(SerializableEngine::player_to_json(ps[k]));
                }

                return j;
            }

            static Tuple<Player<n>, p> players_from_json(const json& j, const Board<n>& board) {
                
                Tuple<Player<n>, p> ps;

                for (index_t k = 0; k < p; k++){
                    ps[k] = SerializableEngine::player_from_json(j[k], board, k);
                }

                return ps;
            }
        
    };
}

#endif 