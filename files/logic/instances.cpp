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

    /*
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
            //{"times", this -> times},

            {"turn", this -> turn},
            {"history", this -> history},

            {"status", (char)this -> status},
            {"promoting", promoting},

            {"move_json", this -> move_json},
        };
    }

    static Instance deserialize(const json& j) {
        Grid<Piece<n>*, n> board(j.at("board").get<Tup<n>>());
        Tuple<Player<n>, p> players = Instance::players_to_json(j.at("players"), board);


        Instance result(
            std::move(board), 
            std::move(players), 
            //j.at("times").get<Tuple<duration, p>>(),
            j.at("turn").get<index_t>(),
            j.at("history").get<std::vector<Tuple<Action<n>, p>>>(),
            j.at("status").get<Status>(),
            nullptr,
            j.at("move_json")
        );

        for (index_t i = 0; i < p; i++){
            for (Piece<n>& piece : players[i].pieces){
                result.show(&piece);
            }

            for (Piece<n>& monarch : players[i].monarchs){
                result.show(&monarch);
            }
        }

        json& promoting = j.at("promoting");

        if (!promoting.is_null()){
            result.promoting = result.board[Index<n>(promoting.get<Tup<n>>(), board)];
        }
        
        return result;
    }
    */

    private:
        json move_json;


        virtual void resolve_promotion(index_t i) {
            if (this -> status != PROMOTING) {
                throw std::runtime_error(std::string("status ") + std::string((char)(this -> status)));
            }

            this -> raw_promote(i);
            this -> move_json["promote"] = i;

            this -> post_move();
        }

        virtual void make_move(const Index<n>& start, const Index<n>& end) {
            if (this -> status > ONGOING) {
                throw std::runtime_error(std::string("status ") + std::string((char)(this -> status)));
            }

            Piece<n>* piece = this -> board[start];
            const Move<n>* move = this -> validate_and_get_move(piece, end);
            const Piece<n>* target_piece = this -> adjust_board_and_get_target(piece, move, start, end);
            
            Action<n> action(start, end);

            this -> round[this -> turn] = action;

            bool auto_promote = this -> update_promoting(piece);

            this -> move_json = {
                {"label", "move"},
                {"action", action}
            };
            
            if (target_piece) != nullptr{
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

            this -> move_json["times"] = this -> times;
            this -> move_json["duration"] = time_dif;

            if (this -> status == CHECKMATE){
                this -> move_json["end"] = "checkmate";
            } else if (this -> status == STALEMATE){
                this -> move_json["end"] = "stalemate";
            }
        }

        

        json drain_json() {
            json r = std::move(this -> move_json);
            this -> move_json = nullptr;
            return r;
        }

        /*

        static json piece_to_json(const Piece<n>& pi) {
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

        static Piece<n> piece_from_json(const json& j, const Grid<Piece<n>*, n>& board) {
            return Piece<n>(
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
            };
        }

        Player<n> player_from_json(const json& j) const {
            std::vector<Piece<n>> pieces;
            std::vector<Piece<n>> pawns;
            std::vector<Piece<n>> monarchs;

            const json& jpieces = j["pieces"];
            const json& jpawns = j["pawns"];
            const json& jmonarchs = j["monarchs"];

            for (const auto& piece : jpieces){
                pieces.push_back(this -> piece_from_json(piece));
            }

            for (const auto& pawn : jpawns){
                pawns.push_back(this -> piece_from_json(pawn));
            }

            for (const auto& monarch : jmonarchs){
                monarchs.push_back(this -> piece_from_json(monarch));
            }

            return Player<n>(
                j["index"],
                j["material"],
                std::move(pawns),
                std::move(pieces),
                std::move(monarchs)
            );
        }


        json players_to_json(const Tuple<Player<n>, p>& ps) const{
            json j = json::array();

            for (index_t k; k < p; k++){
                j.push_back(this -> player_to_json(ps[k]));
            }

            return j;
        }

        Tuple<Player<n>, p> players_from_json(const json& j) const{
            
            Tuple<Player<n>, p> ps;

            for (index_t k; k < p; k++){
                ps[k] = this -> player_from_json(j[k]);
            }

            return ps;
        }
        */

};

#endif