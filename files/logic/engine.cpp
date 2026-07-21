// Demetre Seturidze
// Chess
// Python wrapper

//#include<pybind11/pybind11.h>
#include"logic.hpp"
#include"structs.cpp"
#include"moves.cpp"
#include"game.cpp"
#include"instances.cpp"

//namespace py = pybind11;


template<index_t n, index_t p>
std::string py_process(game::SerializableInstance<n, p>& si, const std::string& j){
    json input = json::parse(j);
    json result = si.process(input);
    return result.dump();
}

template<index_t n, index_t p>
std::string py_layout(const game::SerializableInstance<n, p>& si, index_t i){
    json result = si.layout(i);
    return result.dump();
}


/*
PYBIND11_MODULE(mycpp, m) {
    py::class_<game::SerializableInstance>(m, "Engine")
        .def(py::init<int, int>())
        .def_readwrite("x", &Point::x)
        .def_readwrite("y", &Point::y)
        .def("repr", &Point::repr);
}
*/