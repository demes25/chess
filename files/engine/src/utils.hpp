// Demetre Seturidze
// Chess
// Moves

#ifndef UTILS
#define UTILS

#include"structs.hpp"

using namespace structs;

namespace utils {
    template <index_t n>
    using Action = Tuple<Tup<n>, 2>;

    template<index_t n>
    using RequestContent = std::variant<std::string, index_t, Action<n>>;
    
    template<index_t n>
    struct Request {
        std::string label;
        std::optional<RequestContent<n>> content = std::nullopt;
    };

    template<index_t p>
    using ResponseContent = std::variant<std::string, Tuple<double, p>>;

    template<index_t p>
    struct Response {
        std::string label;
        std::optional<ResponseContent<p>> content = std::nullopt;  
    };

    template <index_t n, index_t p>
    struct Event {
        std::vector<Action<n>> actions;

        std::optional<Tuple<double, p>> times = std::nullopt;
        std::optional<double> duration = std::nullopt;
        std::optional<std::vector<index_t>> checks = std::nullopt;

        std::optional<Tup<n>> die = std::nullopt;
        std::optional<index_t> promote = std::nullopt;
        std::optional<std::string> end = std::nullopt;
    };

    template <index_t n, index_t p>
    void to_json(json& j, const Event<n, p>& e){
        j = {
            {"actions", e.actions},
            {"times", e.times},
            {"duration", e.duration},
            {"checks", e.checks},
            {"die", e.die},
            {"promote", e.promote},
            {"end", e.end}
        };
    }

    template<index_t n, index_t p>
    void from_json(const json& j, Event<n, p>& e){

        e = Event<n, p>{
            j.at("actions").get<std::vector<Action<n>>>(),
            j.value("times", json(nullptr)).get<std::optional<Tuple<double, p>>>(),
            j.value("duration", json(nullptr)).get<std::optional<double>>(),
            j.value("checks", json(nullptr)).get<std::optional<std::vector<index_t>>>(),
            j.value("die", json(nullptr)).get<std::optional<Tup<n>>>(),
            j.value("promote", json(nullptr)).get<std::optional<index_t>>(),
            j.value("end", json(nullptr)).get<std::optional<std::string>>()
        };
    }

    template <index_t n, index_t p>
    using Reaction = std::variant<Event<n, p>, Response<p>>;
}

#endif 