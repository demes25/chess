// Demetre Seturidze
// Chess
// Instances


#ifndef INSTANCES
#define INSTANCES

#include"logic.hpp"
#include"game.cpp"

template <index_t n, index_t p>
struct game::SerializableInstance : public Instance<n, p>{
    using Instance<n, p>::Instance;

    SerializableInstance(SerializableInstance&&) = default;
    SerializableInstance& operator=(SerializableInstance&&) = default;
    ~SerializableInstance() = default;

    // COMMANDS

    json execute(const Index<n>& start, const Index<n>& end) {
        try {
            this -> move(start, end);
            
            if (this -> status != PROMOTING) {
                return this -> drain_json();
            } else {
                return nullptr;
            }

        } catch(const std::exception& e){
            this -> move_json = nullptr;
            return {
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
                {"label", "error"},
                {"content", e.what()}
            };
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

        json times = json::array();

        for (index_t i = 0; i < p; i++){
            times.push_back(this -> times[i].count());
        }

        duration t = this -> turn_start_time.time_since_epoch();

        return {
            {"board", this -> board.get_shape()},
            {"players", SerializableInstance::player_to_json(this -> players)},
            {"times", times},
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

        timestamp turn_start_time(std::chrono::duration_cast<timer::duration>(duration{j.at("turn_start_time").get<double>()}));

        SerializableInstance result(
            std::move(board), 
            std::move(players), 
            std::move(times),
            
            j.at("history").get<std::vector<Tuple<Action<n>, p>>>(),
            j.at("turn").get<index_t>(),
            turn_start_time,

            j.at("status").get<Status>(),
            nullptr
        );

        const json& promoting = j.at("promoting");

        if (!promoting.is_null()){
            result.promoting = result.board[Index<n>(promoting.get<Tup<n>>(), board)];
        }
        
        return result;
    }

    private:
        json move_json;


        virtual void resolve_promotion(index_t i) {
            this -> assert_status();

            this -> raw_promote(i);
            this -> move_json["promote"] = i;

            this -> post_move();
        }

        virtual void make_move(const Index<n>& start, const Index<n>& end) {
            this -> assert_status();

            std::shared_ptr<Piece<n>> piece = this -> board[start];
            const Move<n>* move = this -> validate_and_get_move(piece, end);
            const std::shared_ptr<Piece<n>> target_piece = this -> adjust_board_and_get_target(piece, move, start, end);
            
            Action<n> action(start, end);

            this -> round[this -> turn] = action;

            bool auto_promote = this -> update_promoting(piece);

            this -> move_json = json::object();
            
            this -> move_json["label"] = "move";
            this -> move_json["action"] = "action";
            
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
            json r = std::move(this -> move_json);
            this -> move_json.clear();
            return r;
        }


        static json piece_to_json(const std::shared_ptr<Piece<n>>& pi) {
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

        static std::shared_ptr<Piece<n>> piece_from_json(const json& j, const Board<n>& board) {
            return std::make_shared<Piece<n>>(
                Index<n>(std::move(j.at("position").get<Tup<n>>()), board),
                Figure<n>::resolve(j.at("figure").get<std::string>()),

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


        static json player_to_json(const Player<n>& pl) {
            json pieces = json::array();
            json monarchs = json::array();

            for (const std::shared_ptr<Piece<n>>& piece : pl.pieces){
                pieces.push_back(SerializableInstance::piece_to_json(piece));
            }

            for (const std::shared_ptr<Piece<n>>& monarch : pl.monarchs){
                monarchs.push_back(SerializableInstance::piece_to_json(monarch));
            }

            return {
                {"index", pl.index},
                {"material", pl.material},
                {"pieces", pieces},
                {"monarchs", monarchs}
            };
        }

        static Player<n> player_from_json(const json& j, const Board<n>& board) {
            std::vector<std::shared_ptr<Piece<n>>> pieces;
            std::vector<std::shared_ptr<Piece<n>>> monarchs;

            const json& jpieces = j.at("pieces");
            const json& jmonarchs = j.at("monarchs");

            for (const json& piece : jpieces){
                pieces.push_back(SerializableInstance::piece_from_json(piece, board));
            }

            for (const json& monarch : jmonarchs){
                monarchs.push_back(SerializableInstance::piece_from_json(monarch, board));
            }

            return Player<n>(
                j.at("index").get<index_t>(),
                j.at("material").get<value_t>(),
                std::move(pieces),
                std::move(monarchs)
            );
        }


        static json players_to_json(const Tuple<Player<n>, p>& ps){
            json j = json::array();

            for (index_t k; k < p; k++){
                j.push_back(SerializableInstance::player_to_json(ps[k]));
            }

            return j;
        }

        static Tuple<Player<n>, p> players_from_json(const json& j, const Board<n>& board) {
            
            Tuple<Player<n>, p> ps;

            for (index_t k; k < p; k++){
                ps[k] = SerializableInstance::player_from_json(j[k], board);
            }

            return ps;
        }
    
};

#endif


#define INSTANCE_TEST

#ifdef INSTANCE_TEST
    
#include"structs.cpp"
#include"moves.cpp"
#include<fstream>

using namespace game;

int main(){
    json j;
    json k;

    std::ifstream file("figures.json");

    file >> k;
    Figure<2>::load(k);


    file = std::ifstream("game.json");
    if (!file) {
        throw std::runtime_error("Could not open game.json");
    }

    file >> j;

    SerializableInstance<2, 2> g = SerializableInstance<2, 2>::deserialize(j);

    std::cout << g << std::endl;

    while (!g.is_over()) {
        std::string k;
        std::cin >> k;

        Index<2> start = g.as_index(Tup<2>(k[0] - 'a', k[1] - '1'));
        Index<2> end = g.as_index(Tup<2>(k[2]-'a', k[3] - '1'));

        std::cout << g.execute(start, end) << std::endl;
        std::cout << g << std::endl;
    }
}
#endif 