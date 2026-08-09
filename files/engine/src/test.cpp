// Demetre Seturidze
// Chess
// Test

#include"engines.hpp"
#include<fstream>

template<index_t n, index_t p>
using Engine = engines::SerializableEngine<n, p>;

Reaction<2, 2> follow(Engine<2, 2>& e, const std::string& s) {
    if (s == "reset"){
        return e.process(
            Request<2>{"reset"}
        );
    }

    Reaction<2, 2> response = e.process(
        Request<2>{"action", std::optional{Action<2>(Tup<2>(s[0]-'a', s[1]-'1'), Tup<2>(s[2]-'a', s[3]-'1'))}}
    );

    if (std::holds_alternative<Response<2>>(response) && std::get<Response<2>>(response).label == "promote"){
        index_t i;
        std::cin >> i;

        response = e.process(
            Request<2>{"promote", i}
        );
    }

    return response;
}

int main() {
    json j;

    std::fstream f("../figures.json");
    f >> j;

    moves::Figure<2>::load(j);

    j = json::object();
    f = std::fstream("../sets.json");

    f >> j;

    engines::Engine<2, 2>::game_sets = j;

    Engine<2, 2> e = Engine<2, 2>::instantiate("Chess", 600.0);

    std::vector<std::string> premoves = {
        //"d2d4", "a7a5", "d4d5", "a5a4", "d5d6", "a4a3", "d6e7", "a3b2"
        //"d2d4", "e7e5", "d4e5", "d7d6", "e5d6", "d8e7", "d6e7", "c7c6"
        //"e2e4", "d7d5", "e4d5", "e7e6", "d5e6", "f7f5", "e6e7", "d8e7"
        //"e2e4", "e7e5", "f1e2", "f8e7", "g1f3", "g8f6"
        //"e2e4", "e7e5", "f1d3", "f8c5", "g1h3", "g8f6", "f2f3" // CASTLE
        "e2e3", "a7a6", "d1f3", "b7b6", "f1c4", "c7c6" // SCHOLAR

    };


    std::cout << e.layout() << std::endl;

    for (const std::string& s : premoves){
        follow(e, s);
        std::cout << e.to_str() << std::endl;
        MoveMap<2> map(e.look().get_shape());
        e.look()[Tup<2>(4, 0)] -> populate(map, e.look());
        std::cout << map.to_bitmap() << std::endl;
    }

    while (e.is_on()) {
        std::string s;
        std::cin >> s;

        
        Reaction<2, 2> result = follow(e, s);  
        //std::cout << std::visit(result) << std::endl;
        

        std::cout << e.to_str() << std::endl;
        MoveMap<2> map(e.look().get_shape());
        e.look()[Tup<2>(4, 0)] -> populate(map, e.look());
        std::cout << map.to_bitmap() << std::endl;
    }
}

