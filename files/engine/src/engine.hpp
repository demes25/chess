// Demetre Seturidze
// Chess
// Engine


#ifndef ENGINE
#define ENGINE

#include"game.hpp"

using namespace structs;
using namespace game;
using namespace moves;

template <index_t n, index_t p>
struct SerializableInstance : public Instance<n, p>{
    using Instance<n, p>::Instance;

    SerializableInstance(SerializableInstance&&) = default;
    SerializableInstance& operator=(SerializableInstance&&) = default;
    ~SerializableInstance() = default;

    // EXTERNAL SERIALIZATION

    // the following map to python Serializable objects (see netlib)
    // defined in AV.
    json execute(const Index<n>& start, const Index<n>& end) {
        try {
            this -> move(start, end);
            
            if (this -> status != PROMOTING) {
                return this -> drain_json();
            } else {
                return {
                    {"__type__", "Response"},
                    {"label", "promote"}
                };
            }

        } catch(const std::exception& e){
            this -> move_json = nullptr;
            return {
                {"__type__", "Response"},
                {"label", "error"},
                {"content", e.what()}
            };
        }
    }

    json promote(index_t i) {
        try {
            this -> resolve_promotion(i);
            return this -> drain_json();
        } catch (const std::exception& e) {
            return {
                {"__type__", "Response"},
                {"label", "error"},
                {"content", e.what()}
            };
        }
    }
    

    // EXPOSED SERIALIZATION

    // the following are exposed to python
    json process(const json& a) {
        if (a["__type__"] == "Action"){
            Index<n> start = this -> as_index(a["start"]);
            Index<n> end = this -> as_index(a["end"]);
            return this -> execute(start, end);
        } else if (a["__type__"] == "Promotion") {
            return this -> promote(a["index"]);
        } else {
            throw std::invalid_argument("Invalid json.");
        }
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

    json serialize_times() const {
        json times = json::array();

        for (index_t i = 0; i < p; i++){
            if (i == this -> turn && this -> status > UNBEGUN){
                duration elapsed_time = std::chrono::duration_cast<duration>(timer::now() - this -> turn_start_time);
                times.push_back(
                    (this -> times[i] - elapsed_time).count()
                );
            }
            times.push_back(this -> times[i].count());
        }

        return times;
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
            {"players", SerializableInstance::players_to_json(this -> players)},
            {"times", this -> serialize_times()},
            {"turn_start_time", t.count()},

            {"turn", this -> turn},
            {"history", this -> history},

            {"status", (char)this -> status},
            {"promoting", promoting},

            {"move_json", this -> move_json},
        };
    }

    static SerializableInstance deserialize(const json& j) {
        Board<n> board(j.at("board").get<Tup<n>>());
        Tuple<Player<n>, p> players = SerializableInstance::players_from_json(j.at("players"), board);

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
        SerializableInstance result(
            std::move(board), 
            std::move(players), 
            std::move(times),
            
            j.value("history", json::array()).get<std::vector<Tuple<Action<n>, p>>>(),
            j.value("turn", json(0)).get<index_t>(),
            turn_start_time,

            j.value("status", json(UNBEGUN)).get<Status>(),
            nullptr
        );

        const json& promoting = j.value("promoting", json(nullptr));

        if (!promoting.is_null()){
            result.promoting = result.board[Index<n>(promoting.get<Tup<n>>(), board)];
        }
        
        return result;
    }

    protected:
        json move_json;


        virtual void resolve_promotion(index_t i) {
            if (this -> status != PROMOTING) {
                this -> status_error();
            }

            this -> raw_promote(i);
            this -> move_json["promote"] = i;

            this -> post_move();
        }

        virtual void make_move(const Index<n>& start, const Index<n>& end) {
            if (this -> status > ONGOING) {
                this -> status_error();
            }

            sptr<Piece<n>> piece = this -> board[start];
            sptr<Move<n>> move = this -> validate_and_get_move(piece, end);
            const sptr<Piece<n>> target_piece = this -> adjust_board_and_get_target(piece, move, start, end);
            
            this -> set_current_action(start, end);

            bool auto_promote = this -> update_promoting(piece);

            this->move_json = json::object();
            
            this -> move_json["__type__"] = "Event";
            this -> move_json["action"] = {
                {"__type__", "Action"},
                {"start", start},
                {"end", end}
            };
            
            if (target_piece != nullptr){
                this -> move_json["die"] = target_piece -> position;
            }
            if (auto_promote){
                this -> move_json["promote"] = 0;
            }

        }

        virtual void post_move() {
            std::vector<index_t> checks = this -> get_checks();
                
            duration time_dif = this -> advance_turn();

            bool next_in_check = false;

            for (const index_t & check : checks){
                if (check == this -> turn){
                    next_in_check = true;
                    break;
                }
            }

            this -> update_game_status(next_in_check);

            json json_times = json::array();

            for (index_t i = 0; i < p; i++){
                json_times.push_back(this -> times[i].count());
            }

            this -> move_json["times"] = json_times;
            this -> move_json["duration"] = time_dif.count();

            if (this -> status == CHECKMATE){
                this -> move_json["end"] = "checkmate";
            } else if (this -> status == STALEMATE){
                this -> move_json["end"] = "stalemate";
            }
        }

        

        json drain_json() {
            return std::exchange(this->move_json, nullptr);
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

            for (const sptr<Piece<n>>& piece : pl.pieces){
                pieces.push_back(SerializableInstance::piece_to_json(piece));
            }

            for (const sptr<Piece<n>>& monarch : pl.monarchs){
                monarchs.push_back(SerializableInstance::piece_to_json(monarch));
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

            const json& jpieces = j.at("pieces");
            const json& jmonarchs = j.at("monarchs");

            for (const json& piece : jpieces){
                pieces.push_back(SerializableInstance::piece_from_json(piece, board, index));
            }

            for (const json& monarch : jmonarchs){
                monarchs.push_back(SerializableInstance::piece_from_json(monarch, board, index));
            }

            return Player<n>(
                j.value("index", json(index)).get<index_t>(),
                j.at("material").get<value_t>(),
                std::move(pieces),
                std::move(monarchs)
            );
        }


        static json players_to_json(const Tuple<Player<n>, p>& ps){
            json j = json::array();

            for (index_t k = 0; k < p; k++){
                j.push_back(SerializableInstance::player_to_json(ps[k]));
            }

            return j;
        }

        static Tuple<Player<n>, p> players_from_json(const json& j, const Board<n>& board) {
            
            Tuple<Player<n>, p> ps;

            for (index_t k = 0; k < p; k++){
                ps[k] = SerializableInstance::player_from_json(j[k], board, k);
            }

            return ps;
        }
    
};


template <index_t n, index_t p>
struct Engine {

    Engine(const std::string& j_str) : setup(json::parse(j_str)) {}

    Engine(const std::string& name, double timer) : setup(json::parse(Engine::sets[name])) {
        json times = json::array();
        for (index_t i = 0; i < p; i++){
            times.push_back(timer);
        }

        setup["times"] = times;
    }


    std::string begin() {
        SerializableInstance<n, p> inst = SerializableInstance<n, p>::deserialize(this -> setup);
        this -> instance = std::make_unique<SerializableInstance<n, p>>(std::move(inst));
        return this -> layout();
    }

    std::string layout() const{
        return this -> instance -> layout().dump();
    }

    std::string times() const {
        return json({
            {"label", "times"},
            {"content", this -> instance -> serialize_times()},
            {"__type__", "Response"}
        }).dump();
    }

    std::string process(const std::string& j_str){
        json j = json::parse(j_str);
        
        if (j["__type__"] == "Request"){
            if (j["label"] == "reset"){
                return this -> begin();
            } else if (j["label"] == "quit"){
                // TODO
            }
        } 

        json result = this -> instance -> process(j);
        return result.dump();
    }

    bool is_on() const {
        return !(this -> instance == nullptr || this -> instance -> is_over());
    }


    std::string save() const {
        return this -> instance -> serialize().dump();
    }

    std::string load(const std::string& j_str) {
        json setup = json::parse(j_str);
        SerializableInstance<n, p> inst = SerializableInstance<n, p>::deserialize(setup);
        this -> instance = std::make_unique<SerializableInstance<n, p>>(std::move(inst));
        return this -> layout();
    }


    std::string to_str() const {
        std::ostringstream oss;
        oss << *(this -> instance);
        return oss.str();
    }

    // STATIC LOADING/DEFINITIONS

    private:
        json setup;
        uptr<SerializableInstance<n, p>> instance;

        static std::unordered_map<std::string, std::string> sets;
};

#endif
