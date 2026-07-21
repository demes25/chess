// Demetre Seturidze
// Chess 
// Bindings

#include<pybind11/pybind11.h>

#include"engine.hpp"
#include<fstream>

namespace py = pybind11;

template<index_t n, index_t p>
void bind(py::module_& m, const char* name)
{
    using T = Engine<n, p>;
    
    py::class_<T>(m, name)
        .def(py::init<std::string>(), py::arg("j_str"))
        
        .def("begin", &T::begin)
        .def("layout", &T::layout)
        .def("times", &T::times)
        .def("process", &T::process, py::arg("j_str"))
        .def("is_on", &T::is_on)
        .def("save", &T::save)
        .def("load", &T::load, py::arg("j_str"))
        .def("__str__", &T::to_str);
}

template<index_t n>
void load_figures(std::string figure_path){
    std::fstream file(figure_path);
    json j;
    file >> j;
    moves::Figure<n>::load(j);
}

PYBIND11_MODULE(engine, m)
{  
    m.def("load_figures", load_figures<2>);
    bind<2, 2>(m, "Engine");
}