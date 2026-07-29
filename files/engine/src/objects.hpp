// Demetre Seturidze
// Chess
// Objects

#ifndef OBJECTS
#define OBJECTS

#include"moves.hpp"

using namespace moves;

namespace objects{
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


    enum Status : char {
        UNBEGUN = '0', ONGOING, PROMOTING, CHECKMATE, STALEMATE, TIMEOUT, DRAW, ABANDONMENT
    };

    template<index_t n>
    using Board = Grid<sptr<Piece<n>>, n>;

}
#endif
