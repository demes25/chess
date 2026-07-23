// Demetre Seturidze
// Chess
// Engine


#ifndef ENGINE
#define ENGINE

#include"instances.hpp"

template <index_t n, index_t p>
struct Engine {

    static json sets;

    Engine(const std::string& j_str) : setup(json::parse(j_str)) {}

    Engine(const std::string& name, double timer) : setup(Engine::sets[name]) {
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
            if (j["content"] == "reset"){
                return this -> begin();
            } else if (j["content"] == "quit"){
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

    const uptr<SerializableInstance<n, p>>& unwrap() const {
        return this -> instance;
    }
    // STATIC LOADING/DEFINITIONS

    private:
        json setup;
        uptr<SerializableInstance<n, p>> instance;
};

template<index_t n, index_t p>
json Engine<n, p>::sets = nullptr;

#endif
