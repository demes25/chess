// Demetre Seturidze
// Chess
// Tuples

#include"logic.hpp"

const char* indent = "  ";
// A standard numerical Tuple object of size n.
// the template argument mathtype must have addition, subtraction, division, and multiplication defined.
template <typename T, index_t n>
struct structs::Tuple{
    Tuple() {}

    Tuple(const T& t) {
        this -> fill(t);
    }

    Tuple(const T* arr) {
        for(index_t i = 0; i < n; i++){
            tup[i] = arr[i];
        }
    }  

    template<typename... Args>
    requires (sizeof...(Args) == n && (std::convertible_to<Args, T> && ...))
    Tuple(Args&&... args) : tup{static_cast<T>(args)...} {}

    Tuple(const Tuple&) = default;
    Tuple(Tuple&&) = default;

    ~Tuple() = default;

    void fill(const T& t) {
        for (index_t i = 0; i < n; i++){
            this -> tup[i] = t;
        }
    }

    T& operator[](index_t i) {
        return this -> tup[i];
    }

    const T& operator[](index_t i) const {
        return this -> tup[i];
    }

    bool operator==(const Tuple& v) const {
        for(index_t i = 0; i < n; i++){
            if (this -> tup[i] != v[i]){
                return false;
            }
        }

        return true;
    }

    bool operator!=(const Tuple& v) const {
        for(index_t i = 0; i < n; i++){
            if (this -> tup[i] != v[i]){
                return true;
            }
        }

        return false;
    }

    Tuple operator+(const Tuple& v) const {
        Tuple result;

        for(index_t i = 0; i < n; i++){
            result.tup[i] = this -> tup[i] + v.tup[i];
        }

        return result;
    }

    Tuple operator-(const Tuple& v) const {
        Tuple result;

        for(index_t i = 0; i < n; i++){
            result.tup[i] = this -> tup[i] - v.tup[i];
        }

        return result;
    }

    Tuple operator+() const {
        return Tuple(*this);
    }

    Tuple operator-() const {
        Tuple result;

        for(index_t i = 0; i < n; i++){
            result.tup[i] = -this -> tup[i];
        }

        return result;
    }

    Tuple operator*(const T& a) const {
        Tuple result;

        for(index_t i = 0; i < n; i++){
            result.tup[i] = (this -> tup[i])*a;
        }

        return result;
    }

    Tuple operator/(const T& a) const {
        Tuple result;

        for(index_t i = 0; i < n; i++){
            result.tup[i] = (this -> tup[i])/a;
        }

        return result;
    }

    friend Tuple operator*(const Tuple& v, const T& a) {
        Tuple result;

        for(index_t i = 0; i < n; i++){
            result.tup[i] = a*(v.tup[i]);
        }

        return result; 
    }


    // if this is a scaling of unit, returns the relevant scalar. otherwise, returns 0.
    T operator|(const Tuple& unit) const {
        T result(0);

        for (index_t i = 0; i < n; i++){
            if (unit[i] == 0) {
                if (this -> tup[i] != 0){
                    return T(0);
                } else {
                    continue;
                }
            } else {
                T scale = (this -> tup[i]/unit[i]);

                if (result != 0 && result != scale){
                    return T(0);
                } else {
                    result = scale;
                }
            }
        }

        return result;
    }


    friend std::ostream& operator<<(std::ostream& os, const Tuple& v){
        os << '[';
        
        index_t last = n-1;
        for(index_t i = 0; i < last; i++){
            os << v.tup[i] << ", ";
        }
        os << v.tup[last] << "]";

        return os;
    }

    protected:
        T tup[n];
};


template<typename T, index_t n>
struct structs::Grid{
    template<typename... Args>
    requires (sizeof...(Args) == n && (std::convertible_to<Args, index_t> && ...)) 
    Grid(Args&&... k) : Grid(Index<n>(k...)) {}

    Grid(Index<n>&& sizes) : shape(sizes), capacity(1){
        for (index_t i = 0; i < n; i++){
            if (sizes[i] == 0){
                throw std::invalid_argument("Axis of size 0.");
            } else {
                this -> capacity *= sizes[i];
            }
        }

        
        this -> arr = std::make_unique<T[]>(this -> capacity);
    }

    Grid(const Index<n>& sizes) : shape(), capacity(1){
        for (index_t i = 0; i < n; i++){
            if (sizes[i] == 0){
                throw std::invalid_argument("Axis of size 0.");
            } else {
                this -> shape[i] = sizes[i];
                this -> capacity *= sizes[i];
            }
        }

        
        this -> arr = std::make_unique<T[]>(this -> capacity);
    }

    Grid(const Grid&) = default;
    Grid(Grid&&) = default;

    ~Grid() = default;


    template<typename... Args>
    requires (sizeof...(Args) == n && (std::convertible_to<Args, index_t> && ...)) 
    T& operator()(Args&&... k) {
        return this -> operator[](Index<n>(k...));
    }

    template<typename... Args>
    requires (sizeof...(Args) == n && (std::convertible_to<Args, index_t> && ...)) 
    const T& operator()(Args&&... k) const{
        return this -> operator[](Index<n>(k...));
    }

    T& operator[](index_t i) {
        return this -> arr[i];
    }

    const T& operator[](index_t i) const{
        return this -> arr[i];
    }

    T& operator[](const Index<n>& index){
        index_t i = 0;

        for (index_t j = 1; j < n; j++){
            if (index[j-1] >= this -> shape[j-1]){
                throw std::out_of_range("Index out of bounds.");
            } else {
                i += (this -> shape[j]*index[j-1]); 
            }
        }
        
        if (index[n-1] >= this -> shape[n-1]){
            throw std::out_of_range("Index out of bounds.");
        } else {
            i += index[n-1]; 
        }

        return this -> arr[i];
    }

    const T& operator[](const Index<n>& index) const {
        index_t i = 0;

        for (index_t j = 1; j < n; j++){
            if (index[j-1] >= this -> shape[j-1]){
                throw std::out_of_range("Index out of bounds.");
            } else {
                i += (this -> shape[j]*index[j-1]); 
            }
        }
        
        if (index[n-1] >= this -> shape[n-1]){
            throw std::out_of_range("Index out of bounds.");
        } else {
            i += index[n-1]; 
        }

        return this -> arr[i];
    }

    bool equals(const Grid& g) const {
        if (this -> shape != g.shape){
            throw std::invalid_argument("Shape mismatch.");
        }

        for (index_t i = 0; i < this -> capacity; i++){
            if (this -> arr[i] != g.arr[i]){
                return false;
            }
        }

        return true;
    }

    friend std::ostream& operator<<(std::ostream& os, const Grid& g) {
        index_t index = 0;
        return g.print_help(os, 0, index);
    }

    protected:
        Index<n> shape;
        index_t capacity;
        std::unique_ptr<T[]> arr;

        std::ostream& print_help(std::ostream& os, index_t axis, index_t& index) const {
            if (axis == n-1){
                for (index_t k = 0; k < axis; k++){
                    os << indent;
                }
                os << '[';
        
                index_t last = this -> shape[axis] - 1;
                for(index_t i = 0; i < last; i++){
                    os << this -> arr[index++] << ", ";
                }
                os << this -> arr[index++] << "]";
            } else {
                for (index_t k = 0; k < axis; k++){
                    os << indent;
                }
                os << '[' << std::endl;

                index_t last = this -> shape[axis] - 1;
                for(index_t i = 0; i < last; i++){
                    this -> print_help(os, axis+1, index);
                    os << ',' << std::endl;
                }

                this -> print_help(os, axis+1, index);
                os << std::endl;
                for (index_t k = 0; k < axis; k++){
                    os << indent;
                }
                os << ']';
            }

            return os;
        }
};

template <index_t n>
struct structs::BitMap : public Grid<bool, n>{
    using Grid<bool, n>::Grid;

    BitMap operator&(const BitMap& b) const {
        if (this -> shape != b.shape){
            throw std::invalid_argument("Shape mismatch.");
        }

        BitMap r(this -> shape);
        
        for (index_t i = 0; i < this -> capacity; i++){
            r.arr[i] = (this -> arr[i] && b.arr[i]);
        }

        return r;
    }

    BitMap operator|(const BitMap& b) const {
        if (this -> shape != b.shape){
            throw std::invalid_argument("Shape mismatch.");
        }

        BitMap r(this -> shape);
        
        for (index_t i = 0; i < this -> capacity; i++){
            r.arr[i] = (this -> arr[i] || b.arr[i]);
        }

        return r;
    }

    BitMap operator^(const BitMap& b) const {
        if (this -> shape != b.shape){
            throw std::invalid_argument("Shape mismatch.");
        }

        BitMap r(this -> shape);
        
        for (index_t i = 0; i < this -> capacity; i++){
            r.arr[i] = (this -> arr[i] ^ b.arr[i]);
        }

        return r;
    }

    BitMap operator!() const {
        BitMap r(this -> shape);
        
        for (index_t i = 0; i < this -> capacity; i++){
            r.arr[i] = !(this -> arr[i]);
        }

        return r;
    }

    BitMap operator==(const BitMap& b) const {
        if (this -> shape != b.shape){
            throw std::invalid_argument("Shape mismatch.");
        }

        BitMap r(this -> shape);
        
        for (index_t i = 0; i < this -> capacity; i++){
            r.arr[i] = (this -> arr[i] == b.arr[i]);
        }

        return r;
    }

    BitMap operator!=(const BitMap& b) const {
        if (this -> shape != b.shape){
            throw std::invalid_argument("Shape mismatch.");
        }

        BitMap r(this -> shape);
        
        for (index_t i = 0; i < this -> capacity; i++){
            r.arr[i] = (this -> arr[i] != b.arr[i]);
        }

        return r;
    }
    
};


int main() {
    structs::Grid<int, 3> r(3, 3, 3);

    for (index_t i = 0; i < 27; i++){
        r[i] = i;
    }

    std::cout << r << std::endl;
}