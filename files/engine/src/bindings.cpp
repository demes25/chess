// Demetre Seturidze
// Chess 
// Bindings

#include<pybind11/pybind11.h>
#include<pybind11/stl.h>

#include"engines.hpp"
#include<fstream>

namespace py = pybind11;

namespace pybind11::detail {
    template <typename T, index_t n>
    struct type_caster<Tuple<T, n>> {
    public:
        using tuple_type = Tuple<T, n>;

        PYBIND11_TYPE_CASTER(tuple_type, _("CTuple"));

        bool load(handle src, bool) {
            if (!py::isinstance<py::sequence>(src))
                return false;

            auto seq = py::reinterpret_borrow<py::sequence>(src);

            if (py::len(seq) != n)
                return false;

            for (index_t i = 0; i < n; i++){
                value[i] = seq[i].cast<T>();
            }

            return true;
        }

        static handle cast(const tuple_type& v,
                   return_value_policy,
                   handle)
        {
            py::tuple t(n);

            for (index_t i = 0; i < n; ++i)
                t[i] = py::cast(v[i]);

            return t.release();
        }
    };
}

template<index_t n>
void load_figures(std::string figure_path){
    std::fstream file(figure_path);
    json j;
    file >> j;
    moves::Figure<n>::load(j);
}

template<index_t n, index_t p>
void load_sets(std::string set_path){
    std::fstream file(set_path);
    json j;
    file >> j;
    engines::Engine<n, p>::game_sets = j;
}


template<index_t n, index_t p>
void bind(py::module_& m, const char* req_name = "Request", const char* resp_name = "Response", const char* event_name = "Event", const char* err_name = "Error", const char* eng_name = "Engine")
{   
    using Rq = Request<n>;
    using Rp = Response<p>;
    using Ev = Event<n, p>;
    using Er = Error;

    py::class_<Rq>(m, req_name)
        .def(py::init([](
                            std::string label,
                            std::optional<RequestContent<n>> content
                        ) -> Rq {
                            return Request<n>{
                                std::move(label), std::move(content)
                            };
                        }), py::arg("label"), py::arg("content") = py::none()) 
        .def_readwrite("label", &Rq::label)
        .def_readwrite("content", &Rq::content);
    
    py::class_<Rp>(m, resp_name)
        .def(py::init([](
                            std::string label,
                            std::optional<ResponseContent<p>> content
                        ) -> Rp {
                            return Response<p>{
                                std::move(label), std::move(content)
                            };
                        }

                    ), py::arg("label"), py::arg("content") = py::none())
        .def_readwrite("label", &Rp::label)
        .def_readwrite("content", &Rp::content);
    
    py::class_<Ev>(m, event_name)
        .def(py::init([](
                            std::vector<Action<n>> actions, 
                            std::optional<Tuple<double, p>> times,
                            std::optional<double> duration,
                            std::optional<std::vector<index_t>> checks,
                            std::optional<Tup<n>> die,
                            std::optional<index_t> promote,
                            std::optional<std::string> end
                        ) -> Ev {
                            return Event<n, p>{
                                std::move(actions), std::move(times), std::move(duration), std::move(checks), std::move(die), std::move(promote), std::move(end)
                            };
                        }
                    ),
            py::arg("actions"),
            py::arg("times") = py::none(),
            py::arg("duration") = py::none(),
            py::arg("checks") = py::none(),
            py::arg("die") = py::none(),
            py::arg("promote") = py::none(),
            py::arg("end") = py::none()        
        )
        .def_readwrite("actions", &Ev::actions)
        .def_readwrite("times", &Ev::times)
        .def_readwrite("duration", &Ev::duration)
        .def_readwrite("checks", &Ev::checks)
        .def_readwrite("die", &Ev::die)
        .def_readwrite("promote", &Ev::promote)
        .def_readwrite("end", &Ev::end);

    py::class_<Er>(m, err_name)
        .def(py::init([](
                            std::string label,
                            std::optional<std::string> content
                        ) -> Er {
                            return Error{
                                std::move(label), std::move(content)
                            };
                        }

                    ), py::arg("label"), py::arg("content") = py::none())
        .def_readwrite("label", &Er::label)
        .def_readwrite("content", &Er::content);

    using Eng = engines::SerializableEngine<n, p>;
    
    py::class_<Eng>(m, eng_name)
        .def(py::init([](std::string set_name, double timer) -> Eng {
            return Eng::instantiate(set_name, timer);
        }), py::arg("set_name"), py::arg("timer"))
        
        .def("layout", &Eng::layout_str)
        .def("times", &Eng::get_times)
        .def("process", &Eng::process, py::arg("request"))
        .def("is_on", &Eng::is_on)
        .def("embed", &Eng::embed)
        .def_static("disembed", &Eng::disembed, py::arg("jstr"))
        .def("__str__", &Eng::to_str);
    
    m.def("load_figures", load_figures<n>, py::arg("filepath"));
    m.def("load_sets", load_sets<n, p>, py::arg("filepath"));
}

PYBIND11_MODULE(internals, m)
{  
    bind<2, 2>(m);
}