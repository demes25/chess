// Demetre Seturidze
// Chess
// Logic

#ifndef BASE
#define BASE 

#include<cstddef>
#include<concepts>
#include<iostream>
#include<memory>
#include<stdexcept>
#include<set>
#include<chrono>
#include<unordered_map>
#include<vector>
#include<functional>
#include<utility>
#include<type_traits>
#include"json.hpp"

using index_t = unsigned short;
using arith_t = signed short;
using value_t = double;
using json = nlohmann::json;

using timer = std::chrono::system_clock;
using duration = std::chrono::duration<double>;
using timestamp = timer::time_point;

template <typename T>
using sptr = std::shared_ptr<T>;

template <typename T>
using uptr = std::unique_ptr<T>;

const char* indent = "  ";

#endif 


