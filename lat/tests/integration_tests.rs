use lat::lat;

#[test]
fn test_hello_world() {
    lat! { r#"
        munus main() {
            imprimo("Hello, World!")
        }
    "# }
}

#[test]
fn test_variables_and_arithmetic() {
    lat! { r#"
        munus main() {
            x: integer = 10
            y: integer = 20
            z: integer = x + y
            imprimo(z)
        }
    "# }
}

#[test]
fn test_if_statement() {
    lat! { r#"
        munus main() {
            x: integer = 5
            si x > 3 {
                imprimo(1)
            } aliter {
                imprimo(0)
            }
        }
    "# }
}

#[test]
fn test_while_loop() {
    lat! { r#"
        munus main() {
            i: integer = 0
            dum i < 3 {
                imprimo(i)
                i = i + 1
            }
        }
    "# }
}

#[test]
fn test_function_call() {
    lat! { r#"
        munus add(a: integer, b: integer) -> integer {
            reditus a + b
        }

        munus main() {
            result: integer = add(3, 4)
            imprimo(result)
        }
    "# }
}

#[test]
fn test_string_concat() {
    lat! { r#"
        munus main() {
            greeting: filum = "Hello, "
            name: filum = "World"
            message: filum = greeting + name
            imprimo(message)
        }
    "# }
}

#[test]
fn test_match_statement() {
    lat! { r#"
        munus main() {
            x: integer = 2
            par (x) {
                1 => { imprimo(1) }
                2 => { imprimo(2) }
                3 => { imprimo(3) }
                _ => { imprimo(0) }
            }
        }
    "# }
}

#[test]
fn test_arrays() {
    lat! { r#"
        munus main() {
            arr: vec<integer> = [10, 20, 30]
            imprimo(arr[0])
            imprimo(arr[1])
            imprimo(arr[2])
        }
    "# }
}

#[test]
fn test_read_string() {
    lat! { r#"
        munus main() {
            x: filum = legeres()
            imprimo(x)
        }
    "# }
}
