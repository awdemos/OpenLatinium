pub use lat_macro::lat;

/// Trait for OpenLatinum's `+` operator, supporting both integer and string addition.
pub trait LatAdd<Rhs = Self> {
    type Output;
    fn lat_add(self, rhs: Rhs) -> Self::Output;
}

impl LatAdd for i32 {
    type Output = i32;
    fn lat_add(self, rhs: i32) -> i32 {
        self + rhs
    }
}

impl LatAdd for i64 {
    type Output = i64;
    fn lat_add(self, rhs: i64) -> i64 {
        self + rhs
    }
}

impl LatAdd<&str> for String {
    type Output = String;
    fn lat_add(self, rhs: &str) -> String {
        self + rhs
    }
}

impl LatAdd<String> for String {
    type Output = String;
    fn lat_add(self, rhs: String) -> String {
        self + &rhs
    }
}

impl LatAdd<String> for &str {
    type Output = String;
    fn lat_add(self, rhs: String) -> String {
        self.to_string() + &rhs
    }
}

impl LatAdd<&str> for &str {
    type Output = String;
    fn lat_add(self, rhs: &str) -> String {
        self.to_string() + rhs
    }
}
