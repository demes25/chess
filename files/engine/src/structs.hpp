// Demetre Seturidze
// Chess
// Structs

#ifndef STRUCTS
#define STRUCTS

#include"base.hpp"

namespace structs {
    // A standard Tuple object of fixed size n.
    template <typename T, index_t n>
    struct Tuple{
        Tuple() {}

        Tuple(const T& t) {
            this -> fill(t);
        }

        template<typename... Args>
        requires (sizeof...(Args) == n && (std::convertible_to<Args, T> && ...))
        Tuple(Args&&... args) : tup{static_cast<T>(std::forward<Args>(args))...} {}

        Tuple(const Tuple&) = default;
        Tuple(Tuple&&) noexcept = default;

        ~Tuple() = default;

        Tuple& operator=(const Tuple&) = default;
        Tuple& operator=(Tuple&&) noexcept = default;

        void fill(const T& t) {
            for (index_t i = 0; i < n; ++i){
                this -> at(i) = t;
            }
        }

        T& operator[](index_t i) {
            return this -> at(i);
        }

        const T& operator[](index_t i) const {
            return this -> at(i);
        }

        bool operator==(const Tuple& v) const {
            for(index_t i = 0; i < n; ++i){
                if (this -> at(i) != v.at(i)){
                    return false;
                }
            }

            return true;
        }

        bool operator!=(const Tuple& v) const {
            for(index_t i = 0; i < n; ++i){
                if (this -> at(i) != v.at(i)){
                    return true;
                }
            }

            return false;
        }

        friend std::ostream& operator<<(std::ostream& os, const Tuple& v){
            os << '[';
            
            index_t last = n-1;
            for(index_t i = 0; i < last; ++i){
                os << v.at(i) << ", ";
            }
            os << v[last] << "]";

            return os;
        }

        std::vector<T> to_vector() const {
            std::vector<T> result;
            result.reserve(n);
            for (index_t i = 0; i < n; i++){
                result.push_back(this -> at(i));
            }
            return result;
        }

        std::vector<T> into_vector() {
            std::vector<T> result;
            result.reserve(n);
            for (index_t i = 0; i < n; i++){
                result.push_back(std::move(this -> at(i)));
            }
            return result;
        }

        protected:
            T tup[n];

            T& at(index_t i) {
                return this -> tup[i];
            }

            const T& at(index_t i) const{
                return this -> tup[i];
            }
    };

    template <typename T, index_t n>
    requires requires(json& j, const T& value) {
        json(value);
    }
    void to_json(json& j, const Tuple<T, n>& v){
        for (index_t i = 0; i < n; i++){
            j.push_back(v[i]);
        }
    }

    template <typename T, index_t n>
    requires requires(json& j, const T& value) {
        json(value);
    }
    void from_json(const json& j, Tuple<T, n>& v){
        for (index_t i = 0; i < n; i++){
            v[i] = j[i];
        }
    }

    template<index_t n>
    using Tup = Tuple<index_t, n>;

    template<index_t n>
    struct Index;

    // A Grid of rank n.
    // For shape S = [s1, s2, ..., sn], stores a contiguous array of size prod(S). (*)
    //
    // Elements may be retrieved by:
    //   - Indexing using a Tup<n>, in which case the array is "collapsed" under-the-hood into a single integral type object according to (*) which then is used to access the element.
    //   - Using the () operator with n integer arguments i.e. b(1, 3, 481, 23, ...), in which case the variadic arguments are collected into a Tuple, whereafter the same procedure is followed as above.
    //   - Directly indexing using a single integral type object which is taken to be the same as the "collapsed" index noted above.
    template<typename T, index_t n>
    struct Grid{
        template<typename... Args>
        requires (sizeof...(Args) == n && (std::convertible_to<Args, index_t> && ...)) 
        Grid(Args&&... k) : Grid(Tup<n>(std::move(k)...)) {}

        Grid(Tup<n>&& shape) : shape(std::make_shared<Tup<n>>(std::move(shape))), sizes(std::make_shared<Tup<n>>(0)), capacity(1){
            index_t i;

            for (i = 0; i < n; ++i){
                index_t d = this -> axis_shape(i);
                if (d == 0){
                    throw std::invalid_argument("Axis of size 0.");
                } else {
                    this -> capacity *= d;
                }
            }

            --i;
            this -> sizes -> operator[](i) = 1;

            while(i > 0){
                --i;
                this -> sizes -> operator[](i) = this -> axis_size(i+1)*this -> axis_shape(i+1); 
            }

            this -> arr = std::make_unique<T[]>(this -> capacity);
        }

        Grid(const Tup<n>& shape) : shape(std::make_shared<Tup<n>>(shape)), sizes(std::make_shared<Tup<n>>(0)), capacity(1){
            index_t i;

            for (i = 0; i < n; ++i){
                if (shape[i] == 0){
                    throw std::invalid_argument("Axis of size 0.");
                } else {
                    this -> shape -> operator[](i) = shape[i];
                    this -> capacity *= shape[i];
                }
            }

            --i;
            this -> sizes -> operator[](i) = 1;

            while(i > 0){
                --i;
                this -> sizes -> operator[](i) = this -> axis_size(i+1)*this -> axis_shape(i+1); 
            }

            
            this -> arr = std::make_unique<T[]>(this -> capacity);
        }

        Grid(const Grid&) = default;
        Grid(Grid&&) noexcept = default;

        Grid& operator=(const Grid&) = default;
        Grid& operator=(Grid&&) noexcept = default;
        
        ~Grid() = default;

        

        void fill(const T& f) {
            for (index_t i = 0; i < this -> capacity; ++i){
                this -> at(i) = f;
            }
        }

        template<typename... Args>
        requires (sizeof...(Args) == n && (std::convertible_to<Args, index_t> && ...)) 
        T& operator()(Args&&... k) {
            return this -> operator[](Tup<n>(std::move(k)...));
        }

        template<typename... Args>
        requires (sizeof...(Args) == n && (std::convertible_to<Args, index_t> && ...)) 
        const T& operator()(Args&&... k) const{
            return this -> operator[](Tup<n>(std::move(k)...));
        }

        T& operator[](index_t i) {
            return this -> at(i);
        }

        const T& operator[](index_t i) const{
            return this -> at(i);
        }

        T& operator[](const Index<n>& index) {
            if (!index.is_valid()){
                throw std::out_of_range("Index out of bounds.");
            }
            return this -> at((index_t)index);
        }

        const T& operator[](const Index<n>& index) const {
            if (!index.is_valid()){
                throw std::out_of_range("Index out of bounds.");
            }
            return this -> at((index_t)index);
        }

        T& operator[](const Tup<n>& index){
            index_t i = this -> collapse(index);
            return this -> at(i);
        }

        const T& operator[](const Tup<n>& index) const {
            index_t i = this -> collapse(index);
            return this -> at(i);
        }

        bool operator==(const Grid& g) const {
            if (this -> shape != g.shape){
                throw std::invalid_argument("Shape mismatch.");
            }

            for (index_t i = 0; i < this -> capacity; ++i){
                if (this -> at(i) != g.at(i)){
                    return false;
                }
            }

            return true;
        }

        bool operator!=(const Grid& g) const {
            if (this -> shape != g.shape){
                throw std::invalid_argument("Shape mismatch.");
            }

            for (index_t i = 0; i < this -> capacity; ++i){
                if (this -> at(i) != g.at(i)){
                    return true;
                }
            }

            return false;
        }


        // ACCESSORS
        
        index_t axis_shape(index_t i) const {
            return this -> shape -> operator[](i);
        }

        index_t axis_size(index_t i) const {
            return this -> sizes -> operator[](i);
        }


        const sptr<Tup<n>>& shape_ptr() const {
            return this -> shape;
        }

        const sptr<Tup<n>>& sizes_ptr() const {
            return this -> sizes;
        }


        const Tup<n>& get_shape() const {
            return *(this -> shape);
        }

        const Tup<n>& get_sizes() const {
            return *(this -> sizes);
        }

        
        index_t get_capacity() const {
            return this -> capacity;
        }
        

        friend std::ostream& operator<<(std::ostream& os, const Grid& g) {
            index_t index = 0;
            return g.print_help(os, 0, index);
        }

        protected:
            sptr<Tup<n>> shape;
            sptr<Tup<n>> sizes;

            index_t capacity;
            std::unique_ptr<T[]> arr;

            T& at(index_t index){
                return this -> arr[index];
            }
            
            const T& at(index_t index) const{
                return this -> arr[index];
            }

            std::ostream& print_help(std::ostream& os, index_t axis, index_t& index) const {
                if (axis == n-1){
                    for (index_t k = 0; k < axis; ++k){
                        os << indent;
                    }
                    os << '[';
            
                    index_t last = this -> axis_shape(axis) - 1;
                    for(index_t i = 0; i < last; ++i){
                        os << this -> at(index++) << ", ";
                    }
                    os << this -> at(index++) << "]";
                } else {
                    for (index_t k = 0; k < axis; ++k){
                        os << indent;
                    }
                    os << '[' << std::endl;

                    index_t last = this -> axis_shape(axis) - 1;
                    for(index_t i = 0; i < last; ++i){
                        this -> print_help(os, axis+1, index);
                        os << ',' << std::endl;
                    }

                    this -> print_help(os, axis+1, index);
                    os << std::endl;
                    for (index_t k = 0; k < axis; ++k){
                        os << indent;
                    }
                    os << ']';
                }

                return os;
            }

        private:
            index_t collapse(const Tup<n>& index) const{
                index_t i = 0;

                for (index_t j = 0; j < n; ++j){
                    if (index[j] >= this -> axis_shape(j)){
                        throw std::out_of_range("Index out of bounds.");
                    } else {
                        i += (this -> axis_size(j)*index[j]); 
                    }
                }

                return i;
            }
    };

     // A Tuple<arith_t, n> with mathematical operations defined.
    template<index_t n>
    struct Vector : public Tuple<arith_t, n> {
        using Tuple<arith_t, n>::Tuple;

        Vector(Vector&&) noexcept = default;
        Vector(const Vector&) = default;

        ~Vector() = default;

        Vector& operator=(const Vector&) = default;
        Vector& operator=(Vector&&) noexcept = default;

        Vector operator+(const Vector& v) const {
            Vector result;

            for(index_t i = 0; i < n; ++i){
                result[i] = this -> at(i) + v.at(i);
            }

            return result;
        }

        Vector& operator+=(const Vector& v) {

            for(index_t i = 0; i < n; ++i){
                this -> at(i) += v.at(i);
            }

            return *this;
        }

        Vector operator-(const Vector& v) const {
            Vector result;

            for(index_t i = 0; i < n; ++i){
                result[i] = this -> at(i) - v.at(i);
            }

            return result;
        }

        Vector& operator-=(const Vector& v) {

            for(index_t i = 0; i < n; ++i){
                this -> at(i) -= v.at(i);
            }

            return *this;
        }

        Vector operator+() const {
            return Vector(*this);
        }

        Vector operator-() const {
            Vector result;

            for(index_t i = 0; i < n; ++i){
                result[i] = -this -> at(i);
            }

            return result;
        }

        Vector operator*(arith_t a) const {
            Vector result;

            for(index_t i = 0; i < n; ++i){
                result[i] = (this -> at(i))*a;
            }

            return result;
        }

        Vector& operator*=(arith_t a) {

            for(index_t i = 0; i < n; ++i){
                this -> at(i) *= a;
            }

            return *this;
        }

        Vector operator/(arith_t a) const {
            Vector result;

            for(index_t i = 0; i < n; ++i){
                result[i] = (this -> at(i))/a;
            }

            return result;
        }

        Vector& operator/=(arith_t a) {

            for(index_t i = 0; i < n; ++i){
                this -> at(i) /= a;
            }

            return *this;
        }

        friend Vector operator*(arith_t a, const Vector& v) {
            Vector result;

            for(index_t i = 0; i < n; ++i){
                result[i] = a*v.at(i);
            }

            return result; 
        }


        // if this is a scaling of unit, returns the relevant scalar. otherwise, returns 0.
        arith_t operator|(const Vector& unit) const {
            arith_t result = 0;

            for (index_t i = 0; i < n; ++i){
                if (unit[i] == 0) {
                    if (this -> at(i) != 0){
                        return 0;
                    } else {
                        continue;
                    }
                } else {
                    arith_t scale = (this -> at(i)/unit[i]);

                    if (result != 0 && result != scale){
                        return 0;
                    } else {
                        result = scale;
                    }
                }
            }

            return result;
        }
    };

    template <index_t n>
    void to_json(json& j, const Vector<n>& v){
        for (index_t i = 0; i < n; i++){
            j.push_back(v[i]);
        }
    }

    template <index_t n>
    void from_json(const json& j, Vector<n>& v){
        for (index_t i = 0; i < n; i++){
            v[i] = j[i];
        }
    }
    

    // A Tup<n> used to index Grid objects.
    //
    // equipped with operators:
    //   - ++Index / --Index : increments/decrements by 1, automatically rolls over
    //   - Index += Vector / Index -= Vector : assign-adds/assign-subtracts a vector, does not roll over.
    //   - Index + Vector / Index - Vector : assign-adds/assign-subtracts vector to a copy, returns the copy.
    //   - Index - Index : returns the Vector difference between two indices.
    //
    // stores a collapsed index that it can used to directly key grids.
    // stores a reference to the shape of the grid and checks updates validity upon every increment/decrement.
    // (throws error if incrementing/decrementing invalid indices).
    template<index_t n>
    struct Index : public Tup<n>{

        Index() : Tup<n>(), limits(), sizes(), collapsed(0), valid(false) {}

        Index(Tup<n>&& value, const sptr<Tup<n>>& limits, const sptr<Tup<n>>& sizes) : Tup<n>(std::move(value)), limits(limits), sizes(sizes), collapsed(0), valid(true) {
            try {
                this -> collapsed = this -> collapse();
            } catch(...) {
                this -> valid = false;
            }
        }
        
        template<typename T>
        Index(const Grid<T, n>& grid) : Tup<n>(0), limits(grid.shape_ptr()), sizes(grid.sizes_ptr()), collapsed(0), valid(true) {}
        
        template<typename T>
        Index(Tup<n>&& value, const Grid<T, n>& grid) : Index(std::move(value), grid.shape_ptr(), grid.sizes_ptr()) {}


        
        template<typename T>
        static Index begin(const Grid<T, n>& grid) {
            return Index(grid);
        }

        template<typename T>
        static Index end(const Grid<T, n>& grid) {
            Index result(grid);
            result.set_end();
            return result;
        }

        Index(const Index&) = default;
        Index(Index&&) noexcept = default;

        Index& operator=(const Index&) = default;
        Index& operator=(Index&&) noexcept = default;

        ~Index() = default;

        Index& set(const Tup<n>& value) {
            this -> valid = true;

            try {
                this -> collapsed = this -> collapse(value);
            } catch(...) {
                this -> valid = false;
            }

            Tup<n>::operator=(value);
            return *this;
        }

        Index& set(Tup<n>&& value) {
            this -> valid = true;

            Tup<n>::operator=(std::move(value));

            try {
                this -> collapsed = this -> collapse();
            } catch(...) {
                this -> valid = false;
            }

            return *this;
        }

        Index& set_begin() {
            this -> valid = true;
            this -> fill(0);

            this -> collapsed = 0;

            return *this;
        }

        Index& set_end() {
            this -> valid = true;
            this -> collapsed = 0;

            for (index_t i = 0; i < n; ++i){
                index_t lim = this ->  axis_limit(i);
                this -> at(i) = lim - 1;
            }

            this -> collapsed = this -> collapse();

            return *this;
        }

        index_t operator[](index_t i) const{
            return this -> at(i);
        }


        Index& operator++() {
            if (!this -> valid){
                throw std::out_of_range("Incrementing invalid index.");
            }

            index_t axis = n-1;
            ++(this -> at(axis));

            if (this -> at(axis) >= this -> axis_limit(axis)) {
                if (axis == 0) {
                    this -> valid = false;
                    return *this;
                } else while(true) {
                    --axis;

                    this -> at(axis+1) = 0;

                    ++(this -> at(axis));
                    
                    if (this -> at(axis) < this -> axis_limit(axis)){
                        break;
                    } else if (axis==0){
                        this -> valid = false;
                        return *this;
                    }
                }
            }  
            
            ++(this -> collapsed);

            return *this;
        }

        Index& operator--() {
            if (!this -> valid){
                throw std::out_of_range("Decrementing invalid index.");
            }

            if (this -> at(n-1) == 0){
                index_t axis = n-2;
                while (true) {
                    this -> at(axis+1) = this -> axis_limit(axis+1)-1;

                    if (this -> at(axis) > 0) {
                        --(this -> at(axis));
                        break;
                    } else if (axis == 0) {
                        this -> valid = false;
                        return *this;
                    }

                    --axis;
                }
            } else {
                --(this -> at(n-1));
            }
            
            --(this -> collapsed);

            return *this;
        }

        Index& operator+=(const Vector<n>& v) {
            if (!this -> valid){
                throw std::out_of_range("Incrementing invalid index.");
            }

            for(index_t i = 0; i < n; ++i){
                arith_t temp = (arith_t) this -> at(i) + v[i];

                if (temp < 0 || temp >= this -> axis_limit(i)){
                    this -> valid = false;
                    return *this;
                }

                this -> at(i) = (index_t)temp;
            }

            this -> collapsed = (index_t)((arith_t)(this -> collapsed) + this -> collapse(v));
            return *this;
        }

        Index& operator-=(const Vector<n>& v) {
            if (!this -> valid){
                throw std::out_of_range("Decrementing invalid index.");
            }

            for(index_t i = 0; i < n; ++i){
                arith_t temp = (arith_t)(this -> at(i)) -  v[i];

                if (temp < 0 || temp >= this -> axis_limit(i)){
                    this -> valid = false;
                    return *this;
                }

                this -> at(i) = (index_t)temp;
            }

            this -> collapsed = (index_t)((arith_t)(this -> collapsed) - this -> collapse(v));;
            return *this;
        }


        Index operator+(const Vector<n>& v) const {
            Index result(*this);
            result += v;
            return result;
        }

        Index operator-(const Vector<n>& v) const {
            Index result(*this);
            result -= v;
            return result;
        }


        Vector<n> operator-(const Index& v) const {
            if (!this -> valid || !v.valid){
                throw std::out_of_range("Invalid index.");
            }

            Vector<n> result;

            for (index_t i = 0; i < n; i++){
                result[i] = ((arith_t)(this -> at(i)) - (arith_t)(v.at(i)));
            }

            return result;
        }


        operator index_t() const {
            return this -> collapsed;
        }

        bool is_valid() const {
            return this -> valid;
        }

        private:
            index_t collapsed;
            bool valid;

            sptr<Tup<n>> limits;
            sptr<Tup<n>> sizes;

            index_t axis_limit(index_t i) const {
                return this -> limits -> operator[](i);
            }

            index_t axis_size(index_t i) const {
                return this -> sizes -> operator[](i);
            }


            index_t collapse() const {
                if (!this -> valid){
                    throw std::out_of_range("Index out of bounds.");
                }

                index_t i = 0;

                for (index_t j = 0; j < n; ++j){
                    i += (this -> axis_size(j)*this -> at(j)); 
                }

                return i;
            }

            index_t collapse(const Tup<n>& index) const{
                index_t i = 0;

                for (index_t j = 0; j < n; ++j){
                    if (index[j] >= this -> axis_limit(j)){
                        throw std::out_of_range("Index out of bounds.");
                    } else {
                        i += (this -> axis_size(j)*index[j]); 
                    }
                }

                return i;
            }

            arith_t collapse(const Tuple<arith_t, n>& vector) const{
                arith_t i = 0;

                for (index_t j = 0; j < n; ++j){
                    i += (this -> axis_size(j)*vector[j]);
                }

                return i;
            }
    };


    // A BitMap of rank n.
    // Works identically to Grid<bool, n> but has boolean operators & | ^ ! defined.
    template <index_t n>
    struct BitMap : public Grid<bool, n>{
        using Grid<bool, n>::Grid;

        BitMap(BitMap&&) = default;
        BitMap(const BitMap&) = default;

        ~BitMap() = default;
        
        BitMap& operator=(const BitMap&) = default;
        BitMap& operator=(BitMap&&) = default;


        bool all() const {
            for (index_t i = 0; i < this -> capacity; i++){
                if (!this -> at(i)){
                    return false;
                }
            }
            return true;
        }

        bool none() const {
            for (index_t i = 0; i < this -> capacity; i++){
                if (this -> at(i)){
                    return false;
                }
            }
            return true;
        }

        bool any() const {
            for (index_t i = 0; i < this -> capacity; i++){
                if (this -> at(i)){
                    return true;
                }
            }
            return false;
        }



        BitMap operator&(const BitMap& b) const {
            if (this -> shape != b.shape){
                throw std::invalid_argument("Shape mismatch.");
            }

            BitMap r(this -> shape);
            
            for (index_t i = 0; i < this -> capacity; ++i){
                r.at(i) = (this -> at(i) && b.at(i));
            }

            return r;
        }

        BitMap& operator&=(const BitMap& b) {
            if (this -> shape != b.shape){
                throw std::invalid_argument("Shape mismatch.");
            }
            
            for (index_t i = 0; i < this -> capacity; ++i){
                this -> at(i) = (this -> at(i) && b.at(i));
            }

            return *this;
        }

        BitMap operator|(const BitMap& b) const {
            if (this -> shape != b.shape){
                throw std::invalid_argument("Shape mismatch.");
            }

            BitMap r(this -> shape);
            
            for (index_t i = 0; i < this -> capacity; ++i){
                r.at(i) = (this -> at(i) || b.at(i));
            }

            return r;
        }

        BitMap& operator|=(const BitMap& b) {
            if (this -> shape != b.shape){
                throw std::invalid_argument("Shape mismatch.");
            }
            
            for (index_t i = 0; i < this -> capacity; ++i){
                this -> at(i) = (this -> at(i) || b.at(i));
            }

            return *this;
        }


        BitMap operator^(const BitMap& b) const {
            if (this -> shape != b.shape){
                throw std::invalid_argument("Shape mismatch.");
            }

            BitMap r(this -> shape);
            
            for (index_t i = 0; i < this -> capacity; ++i){
                r.at(i) = (this -> at(i) != b.at(i));
            }

            return r;
        }

        BitMap& operator^=(const BitMap& b) {
            if (this -> shape != b.shape){
                throw std::invalid_argument("Shape mismatch.");
            }
            
            for (index_t i = 0; i < this -> capacity; ++i){
                this -> at(i) = (this -> at(i) != b.at(i));
            }

            return *this;
        }


        BitMap operator!() const {
            BitMap r(this -> shape);
            
            for (index_t i = 0; i < this -> capacity; ++i){
                r.at(i) = !(this -> at(i));
            }

            return r;
        }
        
    };


    template <typename T, index_t n>
    struct PointerMap : public Grid<T*, n>{
        using Grid<T*, n>::Grid;

        template<typename... Args>
        requires (sizeof...(Args) == n && (std::convertible_to<Args, index_t> && ...)) 
        PointerMap(Args&&... k) : Grid<T*, n>(Tup<n>(std::move(k)...)) {
            this -> fill(nullptr);
        }

        PointerMap(Tup<n>&& shape) : Grid<T*, n>(std::forward<Tup<n>>(shape)) {
            this -> fill(nullptr);
        }

        PointerMap(const Tup<n>& shape) : Grid<T*, n>(shape) {
            this -> fill(nullptr);
        }

        PointerMap(PointerMap&&) = default;
        PointerMap(const PointerMap&) = default;

        ~PointerMap() = default;
        
        PointerMap& operator=(const PointerMap&) = default;
        PointerMap& operator=(PointerMap&&) = default;

        bool all() const {
            for (index_t i = 0; i < this -> capacity; i++){
                if (this -> at(i) == nullptr){
                    return false;
                }
            }
            return true;
        }

        bool none() const {
            for (index_t i = 0; i < this -> capacity; i++){
                if (this -> at(i) != nullptr){
                    return false;
                }
            }
            return true;
        }

        bool any() const {
            for (index_t i = 0; i < this -> capacity; i++){
                if (this -> at(i) != nullptr){
                    return true;
                }
            }
            return false;
        }


        BitMap<n> to_bitmap() const {
            BitMap<n> b(this -> get_shape());
            b.fill(false);

            for (index_t i = 0; i < this -> capacity; i++){
                b[i] = (this -> at(i) != nullptr);
            }

            return b;
        }

        PointerMap operator&(const BitMap<n>& b) const {
            if (this -> shape != b.get_shape()) {
                throw std::invalid_argument("Shape mismatch.");
            }

            PointerMap p(this -> shape);

            for (index_t i = 0; i < this -> capacity; i++){
                if (b[i] == 0) {
                    p.at(i) = nullptr;
                } else {
                    p.at(i) = this -> at(i); 
                }
            }

            return p;
        }

        PointerMap& operator&=(const BitMap<n>& b) {
            if (this -> shape != b.get_shape()) {
                throw std::invalid_argument("Shape mismatch.");
            }

            for (index_t i = 0; i < this -> capacity; i++){
                if (b[i] == 0) {
                    this -> at(i) = nullptr;
                } 
            }

            return &this;
        }
        
    };

}
    

#endif 