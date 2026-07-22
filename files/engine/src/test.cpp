// Demetre Seturidze
// Chess
// Test

#include"engine.hpp"
#include<fstream>

json follow(Engine<2, 2>& e, const std::string& s) {
    if (s == "reset"){
        json request = {
            {"__type__", "Request"},
            {"label", "reset"}
        };

        json response = json::parse(
            e.process(request.dump())
        );

        return response;
    }
    
    json action = {
        {"start", {s[0] - 'a', s[1] - '1'}},
        {"end", {s[2] - 'a', s[3] - '1'}},
        {"__type__", "Action"}
    };

    std::string a = action.dump();

    json result = json::parse(
        e.process(a)
    );

    if (result["__type__"] == "Response" && result["label"] == "promote"){
        index_t i;
        std::cin >> i;

        json response = {
            {"__type__", "Promotion"},
            {"index", i}
        };

        result = json::parse(e.process(
            response.dump()
        ));
    }

    return result;
}

int main() {
    json j;

    std::fstream f("../figures.json");
    f >> j;

    moves::Figure<2>::load(j);

    j = json::object();
    f = std::fstream("../game.json");

    f >> j;

    Engine<2, 2> e(j.dump());

    std::vector<std::string> premoves = {
        //"d2d4", "a7a5", "d4d5", "a5a4", "d5d6", "a4a3", "d6e7", "a3b2"
        "d2d4", "e7e5", "d4e5", "d7d6"//, "e5d6", "d8e7", "d6e7", "c7c6"
        //"e2e4", "d7d5", "e4d5", "e7e6", "d5e6", "f7f5", "e6e7", "d8e7"
        //"e2e4", "e7e5", "f1e2", "f8e7", "g1f3", "g8f6"
        //"e2e4", "e7e5", "f1d3", "f8c5", "g1h3", "g8f6", "f2f3"

    };


    std::cout << e.begin() << std::endl;

    for (const std::string& s : premoves){
        follow(e, s);
        std::cout << e.to_str() << std::endl;
        //MoveMap<2> map(e.unwrap() -> look().get_shape());
        //e.unwrap() -> look()[Tup<2>(4, 0)] -> populate(map, e.unwrap() -> look());
        //std::cout << map.to_bitmap() << std::endl;
    }

    while (e.is_on()) {
        std::string s;
        std::cin >> s;

        
        json result = follow(e, s);  
        std::cout << result << std::endl;
        

        std::cout << e.to_str() << std::endl;
        //MoveMap<2> map(e.unwrap() -> look().get_shape());
        //e.unwrap() -> look()[Tup<2>(4, 0)] -> populate(map, e.unwrap() -> look());
        //std::cout << map.to_bitmap() << std::endl;
    }
}

